# 双通道日报选题 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 每天选 4 条成熟项目和 2 条新兴项目，并在 30 天冷却期内不重复推送。

**Architecture:** 扩展状态记录推送日期与历史 Star；选择器在同一候选集合中先保留成熟池，再用新兴评分填充新兴池，并共享 URL 排除集合。

**Tech Stack:** Python 3.12、pytest。

## Global Constraints

- 成熟池 4 条，新兴池 2 条，总数最多 6 条。
- 所有推送 URL 冷却 30 天；候选不足时少发。
- 新兴项目创建不超过 90 天，按 24 小时 Star 增量、创建时间和近期更新评分。

### Task 1: 可追溯的推送历史

**Files:** Modify `agent_notice/state.py`; test `tests/test_state.py`.

- [ ] Write failing test asserting a project pushed 29 days ago is excluded and one pushed 31 days ago is eligible.
- [ ] Run `python -m pytest tests/test_state.py -q` and observe failure.
- [ ] Store `last_sent` and prior Star score; implement `is_in_cooldown(item, today, state) -> bool` with a 30-day boundary.
- [ ] Run `python -m pytest tests/test_state.py -q`, expect PASS, then commit `feat: track digest cooldown history`.

### Task 2: 4+2 dual-channel selector

**Files:** Modify `agent_notice/filtering.py`; test `tests/test_filtering.py`.

- [ ] Write failing test with four eligible mature items, three eligible emerging items and one shared URL; assert exactly 4 mature then 2 emerging and all URLs unique.
- [ ] Run `python -m pytest tests/test_filtering.py -q` and observe failure.
- [ ] Implement `select_daily_items(items, now, state) -> list[Item]`: mature ranking preserves existing category/quality rules; emerging candidates require age <=90 days, score by Star delta, age and update timestamp; exclude cooldown URLs before either selection.
- [ ] Run full suite and commit `feat: select mature and emerging digest projects`.

### Task 3: Daily app integration

**Files:** Modify `agent_notice/app.py`; test `tests/test_app_chinese.py`.

- [ ] Write failing integration test asserting `run_daily` passes six dual-channel items to the renderer and records their send dates only after successful mail delivery.
- [ ] Run targeted test and observe failure.
- [ ] Replace existing single-pool selection with `select_daily_items`; pass state and current day, then record successful items.
- [ ] Run `python -m pytest -q`, expect PASS, and commit `feat: deliver diversified nonrepeating digest`.

## Plan Self-Review

The three tasks cover cooldown, scoring, pool quotas, cross-pool de-duplication, delivery-state ordering and full offline tests.
