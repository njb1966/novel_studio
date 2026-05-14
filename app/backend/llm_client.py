import os
from anthropic import Anthropic


class LLMClient:
    def __init__(self):
        self.client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        self.default_model = "claude-sonnet-4-6"

    def complete(self, system_prompt: str, user_prompt: str, model: str = None) -> str:
        model = model or self.default_model
        message = self.client.messages.create(
            model=model,
            max_tokens=8192,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return message.content[0].text
