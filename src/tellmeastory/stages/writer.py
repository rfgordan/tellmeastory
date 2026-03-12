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
        with self.client.messages.stream(
            model=self.model,
            max_tokens=MAX_TOKENS,
            system=SYSTEM,
            messages=[{"role": "user", "content": user_message(ctx)}],
        ) as stream:
            for text in stream.text_stream:
                full_text.append(text)
                yield text
        ctx.data["draft"] = "".join(full_text)
