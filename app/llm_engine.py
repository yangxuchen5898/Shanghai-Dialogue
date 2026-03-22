from typing import List, Dict
from openai import OpenAI


class QwenLLM:
    """
    千问大模型封装（OpenAI兼容接口）
    - system 中约束“50字以内”
    - user 中放 ASR 文本
    """
    def __init__(self, api_key: str, model: str, base_url: str, timeout: int = 30) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.timeout = timeout

        if not self.api_key:
            raise ValueError("QWEN_API_KEY 未配置")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout,
        )

    def _build_messages(self, user_text: str) -> List[Dict[str, str]]:
        return [
            {
                "role": "system",
                "content": "你是一个中文语音助手。回答简短一些，保持50字以内。",
            },
            {
                "role": "user",
                "content": user_text,
            },
        ]

    def llm_inference(self, text: str) -> str:
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=self._build_messages(text),
                temperature=0.7,
            )
            reply = resp.choices[0].message.content or ""
            return reply.strip()
        except Exception as e:
            raise RuntimeError(f"LLM 调用失败: {e}")
