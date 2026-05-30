"""一个极简的 OpenAI 兼容 Chat 客户端。

故意只用 requests，不绑定 openai SDK —— 这样任何兼容 OpenAI 接口的服务都能用：
OpenAI、DeepSeek、Moonshot(Kimi)、智谱、本地 Ollama / vLLM 等，只要改 base_url。

通过环境变量配置：
    ASKCSV_API_KEY     必填，API key（本地 Ollama 可随便填）
    ASKCSV_BASE_URL    选填，默认 https://api.openai.com/v1
    ASKCSV_MODEL       选填，默认 gpt-4o-mini
"""

from __future__ import annotations

import json
import os
from typing import Any

import requests

DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_MODEL = "gpt-4o-mini"


class LLMError(RuntimeError):
    """LLM 调用失败时抛出，CLI 会捕获并友好提示。"""


class LLMClient:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout: int = 60,
    ) -> None:
        self.api_key = api_key or os.getenv("ASKCSV_API_KEY", "")
        self.base_url = (base_url or os.getenv("ASKCSV_BASE_URL", DEFAULT_BASE_URL)).rstrip("/")
        self.model = model or os.getenv("ASKCSV_MODEL", DEFAULT_MODEL)
        self.timeout = timeout
        if not self.api_key:
            raise LLMError(
                "未配置 API key。请设置环境变量 ASKCSV_API_KEY"
                "（本地 Ollama 可随便填一个值）。"
            )

    def chat(self, messages: list[dict[str, str]], temperature: float = 0.0) -> str:
        """发送一轮对话，返回 assistant 的文本内容。"""
        url = f"{self.base_url}/chat/completions"
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
        except requests.RequestException as exc:  # 网络层错误
            raise LLMError(f"请求失败：{exc}") from exc

        if resp.status_code != 200:
            raise LLMError(f"接口返回 {resp.status_code}：{resp.text[:300]}")

        try:
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except (json.JSONDecodeError, KeyError, IndexError) as exc:
            raise LLMError(f"无法解析接口返回：{resp.text[:300]}") from exc
