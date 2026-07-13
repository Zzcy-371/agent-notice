# Agent Notice

GitHub Actions 每日收集 Agent 技术动态、生成 Markdown 报告并通过 QQ 邮箱发送；周日生成周报。

## 配置

在 GitHub 仓库 Settings → Secrets and variables → Actions 添加：QQ_SMTP_USER、QQ_SMTP_AUTH_CODE、EMAIL_TO 和 GITHUB_TOKEN。QQ_SMTP_AUTH_CODE 是 QQ 邮箱“账户/POP3/SMTP”中生成的授权码，绝不能提交到仓库。

推送后在 Actions 中手动运行 Daily agent notice 测试邮件与报告。日报在 reports/daily/，周报在 reports/weekly/。定时任务分别为北京时间每天 08:30 和周日 09:00。
