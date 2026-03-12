from collections.abc import Iterator

from openai import OpenAI

from ..models import MODELS
from ..prompts.writer import SYSTEM, user_message
from ..stage import Context, Stage

MAX_TOKENS = 4096


class OpenAIWriterStage(Stage):
    def __init__(self, client: OpenAI, model: str) -> None:
        self.client = client
        self.model = MODELS[model].model_id

    def run(self, ctx: Context) -> Context:
        full_text = "".join(self.stream(ctx))
        ctx.data["draft"] = full_text
        return ctx

    def stream(self, ctx: Context) -> Iterator[str]:
        full_text: list[str] = []
        ctx.data["final_prompt"] = user_message(ctx)
        ctx.data["model"] = self.model
        ctx.data["thinking_budget"] = None

        stream = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": ctx.data["final_prompt"]},
            ],
            max_completion_tokens=MAX_TOKENS,
            stream=True,
            stream_options={"include_usage": True},
        )
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                text = chunk.choices[0].delta.content
                full_text.append(text)
                yield text
            if chunk.usage:
                ctx.data["input_tokens"] = chunk.usage.prompt_tokens
                ctx.data["output_tokens"] = chunk.usage.completion_tokens
        ctx.data["draft"] = "".join(full_text)
