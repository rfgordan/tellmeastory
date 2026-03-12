from collections.abc import Iterator

from anthropic import Anthropic

from .stage import Context, Stage
from .stages.writer import WriterStage


class Pipeline:
    def __init__(self, stages: list[Stage], client: Anthropic) -> None:
        self.stages = stages
        self.client = client
        self.last_ctx: Context | None = None

    def run(self, prompt: str) -> Context:
        ctx = Context(prompt=prompt)
        for stage in self.stages:
            ctx = stage.run(ctx)
        self.last_ctx = ctx
        return ctx

    def stream(self, prompt: str) -> Iterator[str]:
        ctx = Context(prompt=prompt)
        # Run all stages except the last without streaming
        for stage in self.stages[:-1]:
            ctx = stage.run(ctx)
        # Stream the last stage
        last = self.stages[-1]
        if isinstance(last, WriterStage):
            yield from last.stream(ctx)
        else:
            ctx = last.run(ctx)
            draft = ctx.data.get("draft", "")
            if draft:
                yield draft
        self.last_ctx = ctx
