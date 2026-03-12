import sys

from anthropic import Anthropic

from ..prompts.outliner import SYSTEM, user_message
from ..stage import Context, Stage
from .writer import MODELS, DEFAULT_MODEL

MAX_TOKENS = 2048


class OutlinerStage(Stage):
    def __init__(self, client: Anthropic, model: str = DEFAULT_MODEL) -> None:
        self.client = client
        self.model = MODELS[model]

    def run(self, ctx: Context) -> Context:
        print("Generating outline...", file=sys.stderr)
        response = self.client.messages.create(
            model=self.model,
            max_tokens=MAX_TOKENS,
            system=SYSTEM,
            messages=[{"role": "user", "content": user_message(ctx)}],
        )
        ctx.data["outline"] = response.content[0].text
        ctx.data["outline_input_tokens"] = response.usage.input_tokens
        ctx.data["outline_output_tokens"] = response.usage.output_tokens
        print("Writing story...\n", file=sys.stderr)
        return ctx
