# 中文化与时效性日报 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 使用 DeepSeek V4 Flash 生成中文 3 要点日报，并以持久状态避免重复推送旧热门项目。

**Architecture:** 新增状态仓储和 DeepSeek 客户端；日报编排先比较历史状态，再仅解读需要推送的条目。报告渲染消费结构化中文解读，失败时使用确定性中文降级文本。

**Tech Stack:** Python 3.12、urllib、DeepSeek OpenAI-compatible API、pytest、GitHub Actions。

## Global Constraints

- 默认日报最多 6 条，GitHub 优先；内容不足时少发。
- 保留 MCP、RAG、tool calling、multi-agent 等英文术语。
- API base URL 为 https://api.deepseek.com，模型为 deepseek-v4-flash，使用非思考模式。
- DEEPSEEK_API_KEY 仅从 GitHub Actions Secret/环境变量读取，绝不写入日志或报告。
- 模型失败时仍生成并发送中文模板日报。

### Task 1: 状态存储与时效筛选

**Files:** Create `agent_notice/state.py`, `tests/test_state.py`; modify `agent_notice/app.py`.

**Interfaces:** `NoticeState.load(path: Path) -> NoticeState`; `should_notify(item: Item, today: date, state: NoticeState, star_delta: int = 100) -> bool`; `record(items: Iterable[Item], today: date) -> None`.

- [ ] **Step 1: Write failing state tests**

```python
def test_existing_item_is_suppressed_without_star_growth(tmp_path, item):
    state = NoticeState.load(tmp_path / "state.json")
    state.record([item], date(2026, 7, 12))
    assert not should_notify(item, date(2026, 7, 13), state)
```

- [ ] **Step 2: Run red test**

Run: `python -m pytest tests/test_state.py -q`
Expected: FAIL because `agent_notice.state` is absent.

- [ ] **Step 3: Implement JSON state and notification policy**

```python
def should_notify(item, today, state, star_delta=100):
    previous = state.entries.get(item.key)
    return previous is None or item.score - previous["score"] >= star_delta or previous["fingerprint"] != fingerprint(item)
```

- [ ] **Step 4: Verify green and commit**

Run: `python -m pytest tests/test_state.py -q`
Expected: PASS for first appearance, Star delta, changed fingerprint and no-change suppression.

Run: `git add agent_notice/state.py agent_notice/app.py tests/test_state.py && git commit -m "feat: suppress stale digest items"`

### Task 2: DeepSeek structured Chinese summaries

**Files:** Create `agent_notice/deepseek.py`, `tests/test_deepseek.py`; modify `agent_notice/models.py`.

**Interfaces:** `ChineseBrief(title: str, bullets: tuple[str, str, str])`; `DeepSeekClient(api_key, post_json).brief(item: Item) -> ChineseBrief`; `fallback_brief(item: Item) -> ChineseBrief`.

- [ ] **Step 1: Write failing JSON parsing test**

```python
def test_client_returns_three_chinese_bullets_from_json(item):
    client = DeepSeekClient("key", lambda url, payload, headers: {"choices": [{"message": {"content": '{"title":"中文","bullets":["定位","MCP 技术","适用场景"]}'}}]})
    assert client.brief(item).bullets == ("定位", "MCP 技术", "适用场景")
```

- [ ] **Step 2: Run red test**

Run: `python -m pytest tests/test_deepseek.py -q`
Expected: FAIL because `DeepSeekClient` is absent.

- [ ] **Step 3: Implement request and strict response validation**

```python
payload = {"model": "deepseek-v4-flash", "thinking": {"type": "disabled"}, "response_format": {"type": "json_object"}, "messages": messages}
```

Require exactly three non-empty bullets. Implement `fallback_brief` with Chinese labels and original English title/description without API usage.

- [ ] **Step 4: Verify green and commit**

Run: `python -m pytest tests/test_deepseek.py -q`
Expected: PASS for JSON success, malformed JSON, wrong bullet count and fallback terminology preservation.

Run: `git add agent_notice/deepseek.py agent_notice/models.py tests/test_deepseek.py && git commit -m "feat: add DeepSeek Chinese briefs"`

### Task 3: 中文报告、Actions Secret 与 end-to-end verification

**Files:** Modify `agent_notice/reports.py`, `agent_notice/app.py`, `.github/workflows/daily.yml`, `README.md`; create `tests/test_app_chinese.py`.

**Interfaces:** Daily renderer consumes `Mapping[str, ChineseBrief]`; app reads `DEEPSEEK_API_KEY` and falls back on client errors.

- [ ] **Step 1: Write failing integration test**

```python
def test_daily_report_uses_chinese_title_and_three_bullets(tmp_path, settings, item):
    path = run_daily(..., briefer=StubBriefer("中文标题", ("定位", "架构", "价值")))
    assert "### 中文标题" in path.read_text()
    assert "- 价值" in path.read_text()
```

- [ ] **Step 2: Run red test**

Run: `python -m pytest tests/test_app_chinese.py -q`
Expected: FAIL before renderer/app integration exists.

- [ ] **Step 3: Implement integration and workflow variable**

```yaml
DEEPSEEK_API_KEY: ${{ secrets.DEEPSEEK_API_KEY }}
```

Add README instructions for creating the Secret without exposing its value.

- [ ] **Step 4: Verify full suite and commit**

Run: `python -m pytest -q`
Expected: PASS with no external DeepSeek or SMTP request.

Run: `git add agent_notice/reports.py agent_notice/app.py .github/workflows/daily.yml README.md tests/test_app_chinese.py && git commit -m "feat: deliver fresh Chinese agent digest"`

## Plan Self-Review

- Tasks 1–3 cover freshness, Chinese summaries, fallback, terminology, Secret wiring and full offline verification.
- All interfaces use concrete names and every behavior starts with a failing test.
