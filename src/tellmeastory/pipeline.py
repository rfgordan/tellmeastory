from collections.abc import Iterator

from .stage import Context, Stage


class Pipeline:
    def __init__(self, stages: list[Stage], client: object = None) -> None:
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
        for stage in self.stages[:-1]:
            ctx = stage.run(ctx)
        last = self.stages[-1]
        if hasattr(last, "stream"):
            yield from last.stream(ctx)
        else:
            ctx = last.run(ctx)
            draft = ctx.data.get("draft", "")
            if draft:
                yield draft
        self.last_ctx = ctx
