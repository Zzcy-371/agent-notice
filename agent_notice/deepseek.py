import json
from dataclasses import dataclass
from collections.abc import Callable

from agent_notice.models import Item


@dataclass(frozen=True)
class ChineseBrief:
    title: str
    bullets: tuple[str, str, str]


class DeepSeekClient:
    def __init__(self, api_key: str, post_json: Callable) -> None:
        self._api_key, self._post_json = api_key, post_json

    def brief(self, item: Item) -> ChineseBrief:
        prompt = f"基于以下事实用中文生成 JSON，保留 MCP、RAG、tool calling、multi-agent 等术语。仅返回 title 和恰好三个 bullets：\n标题:{item.title}\n描述:{item.summary}"
        body = {"model": "deepseek-v4-flash", "thinking": {"type": "disabled"}, "response_format": {"type": "json_object"}, "messages": [{"role": "user", "content": prompt}]}
        response = self._post_json("https://api.deepseek.com/chat/completions", body, {"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"})
        data = json.loads(response["choices"][0]["message"]["content"])
        bullets = tuple(data["bullets"])
        if not isinstance(data.get("title"), str) or len(bullets) != 3 or not all(isinstance(x, str) and x.strip() for x in bullets):
            raise ValueError("Invalid DeepSeek brief")
        return ChineseBrief(data["title"], bullets)


def fallback_brief(item: Item) -> ChineseBrief:
    return ChineseBrief(item.title, ("项目定位：Agent 开发相关开源项目。", f"核心信息：{item.summary or '请查看原始链接。'}", "工程价值：可作为 Agent 技术选型与实践参考。"))
