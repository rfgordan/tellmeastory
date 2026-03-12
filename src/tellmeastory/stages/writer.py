from collections.abc import Iterator

from anthropic import Anthropic

from ..models import MODELS, DEFAULT_MODEL
from ..prompts.writer import SYSTEM, user_message
from ..stage import Context, Stage

DEFAULT_THINKING_BUDGET = 5000
MAX_OUTPUT_TOKENS = 4096


class WriterStage(Stage):
    def __init__(self, client: Anthropic, model: str = DEFAULT_MODEL, thinking_budget: int | None = None) -> None:
        self.client = client
        self.model = MODELS[model].model_id
        self.thinking_budget = thinking_budget

    def run(self, ctx: Context) -> Context:
        full_text = "".join(self.stream(ctx))
        ctx.data["draft"] = full_text
        return ctx

    def stream(self, ctx: Context) -> Iterator[str]:
        full_text: list[str] = []
        ctx.data["final_prompt"] = user_message(ctx)
        ctx.data["model"] = self.model
        ctx.data["thinking_budget"] = self.thinking_budget

        extra: dict = {}
        max_tokens = MAX_OUTPUT_TOKENS
        if self.thinking_budget is not None:
            extra["thinking"] = {"type": "enabled", "budget_tokens": self.thinking_budget}
            max_tokens += self.thinking_budget

        with self.client.messages.stream(
            model=self.model,
            max_tokens=max_tokens,
            system=SYSTEM,
            messages=[{"role": "user", "content": ctx.data["final_prompt"]}],
            **extra,
        ) as stream:
            for text in stream.text_stream:
                full_text.append(text)
                yield text
            usage = stream.get_final_message().usage
            ctx.data["input_tokens"] = usage.input_tokens
            ctx.data["output_tokens"] = usage.output_tokens
        ctx.data["draft"] = "".join(full_text)
