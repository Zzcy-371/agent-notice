# Agent 技术情报推送系统 Implementation Plan

Goal: 构建由 GitHub Actions 每日生成、QQ 邮箱发送 Agent 技术日报，并每周生成趋势周报的 Python 服务。

Architecture: Python CLI 通过可注入来源客户端采集 GitHub 与 RSS 内容，归一化为 Item 后过滤、去重、排序、渲染并投递。GitHub Actions 负责每日、每周和手动调度。

Tech Stack: Python 3.12、urllib、smtplib、feedparser、pytest、PyYAML、GitHub Actions。

## Global Constraints

- 展示顺序固定为 GitHub 热门项目、论文与工程实践、官方更新。
- 不调用付费 LLM API；摘要仅依赖采集到的标题与描述。
- QQ_SMTP_USER、QQ_SMTP_AUTH_CODE、EMAIL_TO、GITHUB_TOKEN 仅通过环境变量或 Secrets 注入。
- 日报写入 reports/daily/YYYY-MM-DD.md，周报写入 reports/weekly/YYYY-Www.md；重复运行覆盖同一路径。
- 每日 cron 为 30 0 * * *；每周 cron 为 0 1 * * 0（均为 UTC）。
- 单个来源失败继续运行；全部来源失败或邮件失败必须以非零状态退出。

## File Structure

agent_notice/models.py: Category、Item、SourceResult
agent_notice/config.py: Secrets 配置
agent_notice/filtering.py: 筛选、去重、排序、限额
agent_notice/sources.py: GitHub REST、RSS 采集
agent_notice/reports.py: Markdown 与邮件摘要
agent_notice/mailer.py: QQ SMTP
agent_notice/app.py: CLI 编排
config/sources.json: RSS 和关键词
tests/: 纯离线单元及集成测试
.github/workflows/: test、daily、weekly 工作流

### Task 1: 建立项目骨架、模型与 Secrets 配置

Files:
- Create: pyproject.toml, .gitignore, agent_notice/__init__.py, agent_notice/models.py, agent_notice/config.py, config/sources.json
- Test: tests/test_models.py, tests/test_config.py

Interfaces:
- Produces: Category, Item, SourceResult; Settings.from_env(environ: Mapping[str, str]) -> Settings.

- [ ] Step 1: Write a failing model test

    def test_item_removes_fragment_from_url():
        item = Item("Title", "https://example.test/a/#part", "GitHub", Category.GITHUB, NOW, "agent tools", 5)
        assert item.url == "https://example.test/a"
        assert item.key == "https://example.test/a"

- [ ] Step 2: Verify red

Run: python -m pytest tests/test_models.py -q
Expected: FAIL because agent_notice.models does not exist.

- [ ] Step 3: Implement the minimum models

    class Category(StrEnum):
        GITHUB = "GitHub projects"; RESEARCH = "Research and engineering"; OFFICIAL = "Official updates"

    @dataclass(frozen=True)
    class Item:
        title: str; url: str; source: str; category: Category
        published_at: datetime; summary: str; score: int
        def __post_init__(self): object.__setattr__(self, "url", normalize_url(self.url))
        @property
        def key(self) -> str: return self.url

    @dataclass(frozen=True)
    class SourceResult:
        source: str; items: tuple[Item, ...]; error: str | None = None

- [ ] Step 4: Add failing config test, implement, and verify green

    def test_settings_requires_qq_authorization_code():
        with pytest.raises(ValueError, match="QQ_SMTP_AUTH_CODE"):
            Settings.from_env({"QQ_SMTP_USER": "a@qq.com", "EMAIL_TO": "b@test.com"})

    @classmethod
    def from_env(cls, env):
        for name in ("QQ_SMTP_USER", "QQ_SMTP_AUTH_CODE", "EMAIL_TO"):
            if not env.get(name): raise ValueError(name)
        return cls(env["QQ_SMTP_USER"], env["QQ_SMTP_AUTH_CODE"], env["EMAIL_TO"], env.get("GITHUB_TOKEN"))

Run: python -m pytest tests/test_models.py tests/test_config.py -q
Expected: PASS.

- [ ] Step 5: Commit

Run: git add pyproject.toml .gitignore agent_notice config tests && git commit -m "feat: add notice models and configuration"

### Task 2: 实现筛选、去重和优先级排序

Files:
- Create: agent_notice/filtering.py
- Test: tests/test_filtering.py

Interfaces:
- Produces: select_items(items: Iterable[Item], now: datetime, limit: int = 15) -> list[Item].

- [ ] Step 1: Write a failing behavior test

    def test_select_items_deduplicates_and_prefers_github(items, now):
        selected = select_items(items, now, limit=2)
        assert [item.title for item in selected] == ["Hot agent repo", "Agent paper"]

Fixtures include duplicate URLs, an irrelevant item, GitHub score 20 and research score 99.

- [ ] Step 2: Verify red

Run: python -m pytest tests/test_filtering.py -q
Expected: FAIL because select_items is missing.

- [ ] Step 3: Implement and verify green

    PRIORITY = {Category.GITHUB: 0, Category.RESEARCH: 1, Category.OFFICIAL: 2}
    KEYWORDS = ("agent", "agentic", "multi-agent", "mcp", "tool use", "tool-use")

    def select_items(items, now, limit=15):
        seen, result = set(), []
        for item in sorted(items, key=lambda x: (PRIORITY[x.category], -x.score, -x.published_at.timestamp())):
            if item.key in seen or not any(k in f"{item.title} {item.summary}".lower() for k in KEYWORDS): continue
            seen.add(item.key); result.append(item)
        return result[:limit]

Run: python -m pytest tests/test_filtering.py -q
Expected: PASS, including empty, stale, limit and duplicate cases.

- [ ] Step 4: Commit

Run: git add agent_notice/filtering.py tests/test_filtering.py && git commit -m "feat: filter and rank agent content"

### Task 3: 实现可隔离的 GitHub 和 RSS 采集器

Files:
- Create: agent_notice/sources.py
- Modify: config/sources.json
- Test: tests/test_sources.py

Interfaces:
- Produces: GitHubSource(get_json).fetch(now) -> SourceResult; RssSource(name, category, url, parse_feed).fetch(now) -> SourceResult.

- [ ] Step 1: Write a failing GitHub mapping test

    def test_github_source_maps_repository(now):
        source = GitHubSource(lambda url, headers: {"items": [REPOSITORY_FIXTURE]})
        result = source.fetch(now)
        assert result.items[0].category is Category.GITHUB
        assert result.items[0].url == "https://github.com/a/agent-kit"

- [ ] Step 2: Verify red and implement source isolation

Run: python -m pytest tests/test_sources.py::test_github_source_maps_repository -q
Expected: FAIL because GitHubSource is missing.

    class GitHubSource:
        def __init__(self, get_json): self._get_json = get_json
        def fetch(self, now):
            try:
                payload = self._get_json(GITHUB_SEARCH_URL, {})
                return SourceResult("GitHub", tuple(map_repository(row) for row in payload["items"]))
            except Exception as exc:
                return SourceResult("GitHub", (), str(exc))

- [ ] Step 3: Add an RSS test, implement, verify and commit

    def test_rss_source_maps_entry(now):
        source = RssSource("arXiv", Category.RESEARCH, "https://x.test/rss", lambda _: FEED_FIXTURE)
        assert source.fetch(now).items[0].title == "Agent Planning"

Run: python -m pytest tests/test_sources.py -q
Expected: PASS for GitHub/RSS mapping and errors returned in SourceResult.error.

Run: git add agent_notice/sources.py config/sources.json tests/test_sources.py && git commit -m "feat: collect GitHub and RSS agent news"

### Task 4: 用 TDD 生成日报、周报和邮件正文

Files:
- Create: agent_notice/reports.py
- Test: tests/test_reports.py

Interfaces:
- Produces: render_daily(day, items, failures) -> str; render_weekly(week, reports) -> str; render_email(subject, report) -> str.

- [ ] Step 1: Write failing daily grouping test

    def test_daily_report_groups_categories_in_priority_order(day, items):
        report = render_daily(day, items, ["OpenAI: timeout"])
        assert report.index("## GitHub projects") < report.index("## Research and engineering")
        assert "Source failures: OpenAI: timeout" in report

- [ ] Step 2: Verify red, implement and verify green

Run: python -m pytest tests/test_reports.py -q
Expected: FAIL before implementation; PASS after daily grouping, empty state, source failure and 15-item email-cap cases are implemented.

- [ ] Step 3: Add weekly test, implement, and commit

    def test_weekly_report_indexes_daily_reports():
        report = render_weekly("2026-W28", {date(2026,7,13): "- [Repo](https://x.test)"})
        assert "# Agent 技术周报 · 2026-W28" in report
        assert "https://x.test" in report

Run: python -m pytest tests/test_reports.py -q
Expected: PASS.

Run: git add agent_notice/reports.py tests/test_reports.py && git commit -m "feat: render daily and weekly reports"

### Task 5: 实现 QQ SMTP 和 CLI 编排

Files:
- Create: agent_notice/mailer.py, agent_notice/app.py
- Test: tests/test_mailer.py, tests/test_app.py

Interfaces:
- Produces: send_email(settings, subject, body, smtp_factory) -> None; run_daily(day, sources, settings, output_root, mailer) -> Path; run_weekly(day, settings, output_root, mailer) -> Path.

- [ ] Step 1: Write failing SMTP test

    def test_send_email_uses_qq_ssl_without_exposing_auth_code(settings):
        smtp = FakeSmtp()
        send_email(settings, "subject", "body", lambda host, port: smtp)
        assert smtp.connected_to == ("smtp.qq.com", 465)
        assert settings.smtp_auth_code not in smtp.message

- [ ] Step 2: Verify red, implement, and verify green

Run: python -m pytest tests/test_mailer.py -q
Expected: FAIL before send_email exists; PASS after it logs in through smtp.qq.com:465 and sends an EmailMessage.

- [ ] Step 3: Write failing orchestration test, implement failure contract and commit

    def test_daily_writes_report_if_one_source_fails(tmp_path, settings, day):
        path = run_daily(day, [SuccessfulSource(), FailingSource()], settings, tmp_path, mailer=FakeMailer())
        assert path == tmp_path / "daily" / "2026-07-13.md"
        assert path.exists()

Run: python -m pytest tests/test_app.py -q
Expected: PASS after implementation, including all-source failure, SMTP failure after write, and weekly reading seven daily paths.

Run: git add agent_notice/mailer.py agent_notice/app.py tests/test_mailer.py tests/test_app.py && git commit -m "feat: send QQ email notices"

### Task 6: GitHub Actions、项目文档与最终验证

Files:
- Create: .github/workflows/test.yml, .github/workflows/daily.yml, .github/workflows/weekly.yml, README.md
- Modify: pyproject.toml, .gitignore
- Test: tests/test_workflows.py

Interfaces:
- Consumes: GitHub Secrets QQ_SMTP_USER, QQ_SMTP_AUTH_CODE, EMAIL_TO and GITHUB_TOKEN.
- Produces: 测试 CI、每日和每周可手动触发的任务及提交回仓库的报告。

- [ ] Step 1: Write failing workflow contract test

    def test_daily_workflow_has_cron_and_secret_mapping():
        data = yaml.safe_load(Path(".github/workflows/daily.yml").read_text())
        assert "30 0 * * *" in data[True]["schedule"][0]["cron"]
        assert "QQ_SMTP_AUTH_CODE" in data["jobs"]["notify"]["env"]

Run: python -m pytest tests/test_workflows.py -q
Expected: FAIL with missing workflow file.

- [ ] Step 2: Add workflows and verify green

Daily workflow: workflow_dispatch, Ubuntu, Python 3.12, install project, run daily CLI, contents: write permission, and only commit staged reports. Weekly workflow differs only in cron 0 1 * * 0 and weekly CLI. Test workflow runs python -m pytest -q on push and pull request.

Run: python -m pytest tests/test_workflows.py -q
Expected: PASS.

- [ ] Step 3: Add setup document, full verification and commit

README must give exact Secret names, QQ SMTP authorization-code setup, manual first-run procedure, report paths, and a warning never to commit credentials.

Run: python -m pytest -q
Expected: PASS with no real network or SMTP connection.

Run: git add .github README.md pyproject.toml .gitignore tests/test_workflows.py && git commit -m "ci: schedule agent intelligence reports"

## Plan Self-Review

- Spec coverage: Tasks 1–5 cover collection, normalization, priorities, reports, SMTP, source isolation, error behavior and idempotent report paths. Task 6 supplies schedule, manual trigger, minimal permissions, Secrets setup and CI.
- Placeholder scan: No deferred implementation tasks or undefined interfaces remain.
- Type consistency: All task signatures use the same Item, Category, SourceResult, Settings, reporting, mailer and CLI names.

