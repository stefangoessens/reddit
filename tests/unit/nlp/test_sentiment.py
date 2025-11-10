from datetime import datetime

from common.models import MentionEvent
from nlp.pipeline import SentimentAnnotator


def make_mention(span_text: str) -> MentionEvent:
    return MentionEvent(
        ts_utc=datetime(2024, 1, 1, 0, 0, 0),
        subreddit="wallstreetbets",
        reddit_id="t1",
        author="u/test",
        ticker="PLTR",
        confidence=1.0,
        upvotes=1,
        span_text=span_text,
    )


def test_bullish_span_sets_positive_label() -> None:
    annotator = SentimentAnnotator()
    mention = make_mention("PLTR calls are moon bound")
    annotated = annotator.annotate([mention])[0]
    assert annotated.sentiment_label == 1
    assert annotated.has_options_intent is True
    assert annotated.option_side == 1


def test_bearish_span_sets_negative_label() -> None:
    annotator = SentimentAnnotator()
    mention = make_mention("AMC puts looking rough short it")
    annotated = annotator.annotate([mention])[0]
    assert annotated.sentiment_label == -1
    assert annotated.has_options_intent is True
    assert annotated.option_side == -1


def test_neutral_span_stays_zero() -> None:
    annotator = SentimentAnnotator()
    mention = make_mention("Discussing PLTR fundamentals")
    annotated = annotator.annotate([mention])[0]
    assert annotated.sentiment_label == 0
    assert annotated.has_options_intent is False
