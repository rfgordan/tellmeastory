from ..stage import Context

SYSTEM_SIMPLE = "You are a skilled novelist. Write vivid, compelling prose."

SYSTEM = (
    "You are a skilled novelist. You should try your best to write a good novel. "
    "This means prose that is effective at evoking in the reader the desired response. "
    "Good novels understand the conventions and expectations that readers have for a genre, "
    "but they often meet those expectations in surprising and creative ways. "
    "Likewise, a unique and original voice is often a hallmark of good writing. "
    "You should try to avoid cliches and trite turns of phrase, unless you strongly believe "
    "the prompt implies that the user wants such prose. "
    "If you have time to think, use it to develop an interesting plan for the structure and texture of the novel."
)


def user_message(ctx: Context) -> str:
    outline = ctx.data.get("outline")
    if outline:
        return (
            f"Write the first 10 pages of a novel based on this concept:\n\n{ctx.prompt}"
            f"\n\nOutline:\n{outline}"
        )
    return f"Write the first 10 pages of a novel based on this concept:\n\n{ctx.prompt}"
