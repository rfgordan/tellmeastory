import sys

from openai import OpenAI

from ..models import MODELS
from ..prompts.outliner import SYSTEM, user_message
from ..stage import Context, Stage

MAX_TOKENS = 2048


class OpenAIOutlinerStage(Stage):
    def __init__(self, client: OpenAI, model: str) -> None:
        self.client = client
        self.model = MODELS[model].model_id

    def run(self, ctx: Context) -> Context:
        print("Generating outline...", file=sys.stderr)
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": user_message(ctx)},
            ],
            max_completion_tokens=MAX_TOKENS,
        )
        ctx.data["outline"] = response.choices[0].message.content
        ctx.data["outline_input_tokens"] = response.usage.prompt_tokens
        ctx.data["outline_output_tokens"] = response.usage.completion_tokens
        print("Writing story...\n", file=sys.stderr)
        return ctx
