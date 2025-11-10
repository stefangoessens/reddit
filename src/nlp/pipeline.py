"""Ticker extraction + sentiment pipeline skeleton."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

from common.models import MentionEvent, RedditItem


@dataclass
class ExtractionResult:
    """Container for mentions extracted from a single Reddit item."""

    reddit_item: RedditItem
    mentions: Sequence[MentionEvent]


class MentionExtractor:
    """Applies regex/alias rules to identify tickers inside reddit text."""

    _TOKEN_PATTERN = re.compile(r"[A-Za-z$][A-Za-z0-9$']*")

    def __init__(
        self,
        tickers: Iterable[str],
        stoplist: Iterable[str],
        alias_map: Mapping[str, str] | None = None,
        finance_terms: Iterable[str] | None = None,
        context_window: int = 3,
        span_window: int = 12,
    ) -> None:
        self._tickers = {ticker.upper() for ticker in tickers}
        self._stoplist = {word.upper() for word in stoplist}
        self._alias_map = {alias.lower(): symbol.upper() for alias, symbol in (alias_map or {}).items()}
        default_finance = {
            "calls",
            "call",
            "puts",
            "put",
            "option",
            "options",
            "pt",
            "earnings",
            "float",
            "short",
            "long",
            "iv",
            "strike",
            "gamma",
            "delta",
        }
        finance_source = finance_terms or default_finance
        self._finance_terms = {term.lower() for term in finance_source}
        self._context_window = context_window
        self._span_window = span_window

    def extract(self, item: RedditItem) -> ExtractionResult:
        """Return mention events with placeholder confidence/sentiment."""

        tokens = list(self._TOKEN_PATTERN.findall(item.body))
        mentions: list[MentionEvent] = []
        seen: set[str] = set()

        for idx, token in enumerate(tokens):
            alias_symbol = self._alias_map.get(token.lower())
            if alias_symbol and alias_symbol in self._tickers and alias_symbol not in seen:
                mentions.append(
                    self._build_mention(
                        item=item,
                        ticker=alias_symbol,
                        tokens=tokens,
                        idx=idx,
                        confidence=0.65,
                    )
                )
                seen.add(alias_symbol)
                continue

            if not token:
                continue

            if token.startswith("$"):
                symbol = token[1:].upper()
                if self._is_valid_symbol(symbol, seen):
                    mentions.append(
                        self._build_mention(
                            item=item,
                            ticker=symbol,
                            tokens=tokens,
                            idx=idx,
                            confidence=0.95,
                        )
                    )
                    seen.add(symbol)
                continue

            if token.isalpha() and token.isupper() and 1 <= len(token) <= 5:
                symbol = token.upper()
                if not self._is_valid_symbol(symbol, seen):
                    continue
                if symbol in self._stoplist and not self._has_finance_context(tokens, idx):
                    continue
                mentions.append(
                    self._build_mention(
                        item=item,
                        ticker=symbol,
                        tokens=tokens,
                        idx=idx,
                        confidence=0.75,
                    )
                )
                seen.add(symbol)

        return ExtractionResult(reddit_item=item, mentions=mentions)

    def _is_valid_symbol(self, symbol: str, seen: set[str]) -> bool:
        return symbol in self._tickers and symbol not in seen

    def _has_finance_context(self, tokens: Sequence[str], idx: int) -> bool:
        start = max(idx - self._context_window, 0)
        end = min(idx + self._context_window + 1, len(tokens))
        for neighbor in tokens[start:end]:
            if neighbor.lower() in self._finance_terms:
                return True
        return False

    def _build_mention(
        self,
        item: RedditItem,
        ticker: str,
        tokens: Sequence[str],
        idx: int,
        confidence: float,
    ) -> MentionEvent:
        span = self._span(tokens, idx)
        return MentionEvent(
            ts_utc=item.created_utc,
            subreddit=item.subreddit,
            reddit_id=item.id,
            author=item.author,
            ticker=ticker,
            confidence=confidence,
            upvotes=item.score,
            span_text=span,
        )

    def _span(self, tokens: Sequence[str], idx: int) -> str:
        start = max(idx - self._span_window, 0)
        end = min(idx + self._span_window + 1, len(tokens))
        return " ".join(tokens[start:end])


class SentimentAnnotator:
    """Lightweight lexicon-based sentiment approximator with options tilt."""

    _TOKEN_PATTERN = re.compile(r"[A-Za-z']+")
    _POSITIVE = {
        "bull",
        "bullish",
        "green",
        "moon",
        "long",
        "calls",
        "call",
        "callers",
        "rip",
        "squeeze",
    }
    _NEGATIVE = {
        "bear",
        "bearish",
        "red",
        "bag",
        "bags",
        "bagholder",
        "dump",
        "short",
        "shorting",
        "puts",
        "put",
    }
    _OPTIONS_BULL = {"call", "calls", "long", "c"}
    _OPTIONS_BEAR = {"put", "puts", "short", "p"}

    def __init__(self, neutral_threshold: float = 0.15) -> None:
        self._neutral_threshold = neutral_threshold

    def annotate(self, mentions: Sequence[MentionEvent]) -> Sequence[MentionEvent]:
        """Attach sentiment_score/label/confidence to mentions."""

        for mention in mentions:
            tokens = [token.lower() for token in self._TOKEN_PATTERN.findall(mention.span_text or "")]
            score = 0.0
            for token in tokens:
                if token in self._POSITIVE:
                    score += 0.2
                elif token in self._NEGATIVE:
                    score -= 0.2

            options_bias = 0
            if any(token in self._OPTIONS_BULL for token in tokens):
                mention.has_options_intent = True
                mention.option_side = 1
                options_bias += 0.1
            if any(token in self._OPTIONS_BEAR for token in tokens):
                mention.has_options_intent = True
                mention.option_side = -1
                options_bias -= 0.1

            score = max(min(score + options_bias, 0.9), -0.9)
            mention.sentiment_score = score
            if score >= self._neutral_threshold:
                mention.sentiment_label = 1
            elif score <= -self._neutral_threshold:
                mention.sentiment_label = -1
            else:
                mention.sentiment_label = 0
            mention.sentiment_conf = min(abs(score) / 0.3, 1.0)

        return mentions
