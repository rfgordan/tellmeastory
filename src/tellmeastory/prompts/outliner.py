from ..stage import Context

SYSTEM = (
    "You are a skilled novelist and story architect. "
    "Create clear, useful outlines that give a writer strong structural direction "
    "while leaving room for discovery."
)


def user_message(ctx: Context) -> str:
    return (
        f"Create a detailed outline for a novel based on this concept:\n\n{ctx.prompt}\n\n"
        "Include: overall structure and arc, a chapter-by-chapter breakdown for the first act, "
        "key characters and their roles, tone and voice notes, and thematic elements to develop."
    )
