from datetime import UTC, datetime

from agent_notice.deepseek import DeepSeekClient
from agent_notice.models import Category, Item


def test_deepseek_client_parses_three_chinese_bullets():
    item = Item("Agent Kit", "https://example.test", "GitHub", Category.GITHUB, datetime(2026, 7, 13, tzinfo=UTC), "MCP agent framework", 1)
    response = {"choices": [{"message": {"content": '{"title":"Agent Kit","bullets":["项目定位","核心 MCP 架构","适合构建 agent"]}'}}]}
    brief = DeepSeekClient("key", lambda url, body, headers: response).brief(item)
    assert brief.title == "Agent Kit"
    assert brief.bullets == ("项目定位", "核心 MCP 架构", "适合构建 agent")
