# Task 2 Report: Filter, Deduplicate, and Rank Agent Content

## Test commands and results

- `python -m pytest tests/test_filtering.py` (RED): failed during collection with `ModuleNotFoundError: No module named 'agent_notice.filtering'`, confirming the requested module was absent.
- `python -m pytest tests/test_filtering.py` (GREEN): 5 passed.
- `python -m pytest`: 7 passed.
- `git diff --check`: passed with no whitespace errors.

## Files

- `agent_notice/filtering.py`: selects recent relevant items, ranks categories and scores, removes duplicate keys, and applies the limit.
- `tests/test_filtering.py`: tests empty input, title relevance, duplicate removal with GitHub priority, limiting, and the 24-hour stale-data policy.

## Commit

- `feat: filter and rank agent content` (includes this report)

## Self-review

- Confirmed filtering accepts any `Iterable[Item]`, evaluates title and summary case-insensitively, and retains items published within the inclusive 24-hour report window.
- Confirmed ranking is GitHub, research, official; then descending score; then newest publication time. Deduplication uses the normalized `Item.key` and occurs after ranking so the best-ranked duplicate is retained.
- No unrelated files were changed.
