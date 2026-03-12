from collections.abc import Iterator

from anthropic import Anthropic

from ..prompts.writer import SYSTEM, user_message
from ..stage import Context, Stage

MODELS = {
    "sonnet4_6": "claude-sonnet-4-6",
    "opus4_6": "claude-opus-4-6",
}
DEFAULT_MODEL = "sonnet4_6"
MAX_TOKENS = 4096


class WriterStage(Stage):
    def __init__(self, client: Anthropic, model: str = DEFAULT_MODEL) -> None:
        self.client = client
        self.model = MODELS[model]

    def run(self, ctx: Context) -> Context:
        full_text = "".join(self.stream(ctx))
        ctx.data["draft"] = full_text
        return ctx

    def stream(self, ctx: Context) -> Iterator[str]:
        full_text: list[str] = []
        ctx.data["final_prompt"] = user_message(ctx)
        ctx.data["model"] = self.model
        with self.client.messages.stream(
            model=self.model,
            max_tokens=MAX_TOKENS,
            system=SYSTEM,
            messages=[{"role": "user", "content": ctx.data["final_prompt"]}],
        ) as stream:
            for text in stream.text_stream:
                full_text.append(text)
                yield text
            usage = stream.get_final_message().usage
            ctx.data["input_tokens"] = usage.input_tokens
            ctx.data["output_tokens"] = usage.output_tokens
        ctx.data["draft"] = "".join(full_text)
