from datetime import datetime

from common.models import RedditItem
from nlp.pipeline import MentionExtractor

DEFAULT_TICKERS = {"PLTR", "AAPL", "AMC", "A"}
STOPLIST = {"A", "IT", "ON", "ALL", "ARE", "FOR", "GO", "BE"}
ALIAS_MAP = {"palantir": "PLTR"}


def make_item(body: str) -> RedditItem:
    return RedditItem(
        id="t1",
        kind="comment",
        subreddit="wallstreetbets",
        author="u/test",
        body=body,
        created_utc=datetime(2024, 1, 1, 0, 0, 0),
        score=10,
        permalink="https://reddit.com/t1",
    )


def test_cashtag_mentions_are_emitted() -> None:
    extractor = MentionExtractor(DEFAULT_TICKERS, STOPLIST, alias_map=ALIAS_MAP)
    result = extractor.extract(make_item("$PLTR to the moon"))
    assert [m.ticker for m in result.mentions] == ["PLTR"]
    assert result.mentions[0].span_text is not None


def test_stoplist_without_context_is_ignored() -> None:
    extractor = MentionExtractor(DEFAULT_TICKERS, STOPLIST, alias_map=ALIAS_MAP)
    result = extractor.extract(make_item("A is awesome"))
    assert not result.mentions


def test_stoplist_with_finance_context_is_allowed() -> None:
    extractor = MentionExtractor(DEFAULT_TICKERS, STOPLIST, alias_map=ALIAS_MAP)
    result = extractor.extract(make_item("A calls are printing"))
    assert [m.ticker for m in result.mentions] == ["A"]


def test_alias_map_converts_company_names() -> None:
    extractor = MentionExtractor(DEFAULT_TICKERS, STOPLIST, alias_map=ALIAS_MAP)
    result = extractor.extract(make_item("Palantir is ripping"))
    tickers = [m.ticker for m in result.mentions]
    assert tickers == ["PLTR"]
