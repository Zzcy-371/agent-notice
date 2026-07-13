# Task 3 Report: GitHub and RSS collectors

## Delivered

- Added `GitHubSource`, using an injected JSON client to search Agent-related repositories and map results to GitHub `Item` values.
- Added `RssSource`, using an injected feed parser to map RSS entries while keeping parser failures isolated.
- Added arXiv AI, Hacker News, and OpenAI RSS source configuration.
- Added offline fixture tests for successful GitHub/RSS collection and per-source failure isolation.

## TDD evidence

`python -m pytest tests/test_sources.py -q` initially failed during collection because `agent_notice.sources` did not exist. After implementing the collectors, the same command passed with 4 tests.

## Verification

`python -m pytest -q` passed: 12 tests.

`python -m json.tool config/sources.json` and `git diff --check` completed successfully.
