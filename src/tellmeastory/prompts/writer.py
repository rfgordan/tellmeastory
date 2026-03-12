from ..stage import Context

SYSTEM = "You are a skilled novelist. Write vivid, compelling prose."


def user_message(ctx: Context) -> str:
    outline = ctx.data.get("outline")
    if outline:
        return (
            f"Write the first 10 pages of a novel based on this concept:\n\n{ctx.prompt}"
            f"\n\nOutline:\n{outline}"
        )
    return f"Write the first 10 pages of a novel based on this concept:\n\n{ctx.prompt}"
