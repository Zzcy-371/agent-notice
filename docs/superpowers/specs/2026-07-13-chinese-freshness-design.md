# 中文化与时效性日报设计

## 目标

将日报升级为中文深度技术情报：每日只推送 5–8 条真正新增或实质更新的内容，每条由 DeepSeek V4 Flash 生成 3 条工程导向要点。MCP、RAG、tool calling、multi-agent 等技术术语保持英文。

## 新鲜度与去重

仓库维护 `reports/state.json`，保存 URL、首次/最近推送日期、最近 Star 数和内容指纹。项目仅在首次出现、Star 增量达到配置阈值、或标题/描述指纹变化时再推送。未达到条件的热门项目不进入当天日报；内容不足时少发而不复用旧条目。

## 中文解读

筛选后的条目以 JSON 方式请求 DeepSeek 官方 OpenAI-compatible API：base URL 为 `https://api.deepseek.com`，模型为 `deepseek-v4-flash`，非思考模式。模型对每条返回中文标题和恰好 3 条要点：项目定位、核心技术/架构、对 Agent 开发工程师的价值与适用场景。模型不得虚构未提供的事实，须保留关键技术英文术语。

## 弹性与安全

`DEEPSEEK_API_KEY` 仅作为 GitHub Actions Secret 注入。模型调用失败或返回无效 JSON 时，以中文固定模板、原始描述与链接降级生成；日报仍会发送。API Key 绝不写入报告或日志。

## 报告与测试

报告栏目和邮件正文均为中文。测试覆盖状态读取/更新、首次出现、Star 增量、内容指纹更新、模型 JSON 解析、术语保留和失败降级。日报默认上限 6 条。
