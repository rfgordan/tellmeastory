import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

from .pipeline import Pipeline
from .prompts.writer import SYSTEM
from .stages.writer import DEFAULT_MODEL, MODELS, WriterStage

load_dotenv()

USAGE = (
    "Usage: tellmeastory [--model sonnet4_6|opus4_6] [--save] \"<story concept>\"\n"
    "       echo \"<story concept>\" | tellmeastory [--model sonnet4_6|opus4_6] [--save]\n"
    f"Models: {', '.join(MODELS)} (default: {DEFAULT_MODEL})"
)


def _slugify(text: str, max_words: int = 6) -> str:
    words = text.lower().split()[:max_words]
    slug = "-".join(re.sub(r"[^a-z0-9]+", "", w) for w in words)
    return slug.strip("-") or "story"


def _save_story(output_root: Path, prompt: str, model_alias: str, ctx_data: dict) -> Path:
    slug = _slugify(prompt)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    story_dir = output_root / f"{slug}-{ts}"
    story_dir.mkdir(parents=True, exist_ok=True)

    draft = ctx_data.get("draft", "")
    word_count = len(draft.split())

    (story_dir / "story.txt").write_text(draft, encoding="utf-8")

    final_prompt = ctx_data.get("final_prompt", "")
    # Indent multi-line values for YAML block scalar
    def block(s: str) -> str:
        return "|\n" + "\n".join("  " + line for line in s.splitlines())

    card_lines = [
        f"timestamp: {datetime.now(timezone.utc).isoformat()}",
        f"model: {ctx_data.get('model', '')}",
        f"model_alias: {model_alias}",
        f"word_count: {word_count}",
        f"input_tokens: {ctx_data.get('input_tokens', 'N/A')}",
        f"output_tokens: {ctx_data.get('output_tokens', 'N/A')}",
        f"user_prompt: {block(prompt)}",
        f"system_prompt: {block(SYSTEM)}",
        f"final_prompt: {block(final_prompt)}",
    ]
    (story_dir / "story-card.yaml").write_text("\n".join(card_lines) + "\n", encoding="utf-8")

    return story_dir


def main() -> None:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY is not set. Add it to your .env file or environment.", file=sys.stderr)
        sys.exit(1)

    args = sys.argv[1:]
    model = DEFAULT_MODEL
    save = False

    i = 0
    prompt_parts: list[str] = []
    while i < len(args):
        if args[i] in ("--model", "-m"):
            if i + 1 >= len(args):
                print(f"Error: {args[i]} requires a value ({' or '.join(MODELS)}).", file=sys.stderr)
                sys.exit(1)
            model = args[i + 1]
            if model not in MODELS:
                print(f"Error: unknown model '{model}'. Choose from: {', '.join(MODELS)}", file=sys.stderr)
                sys.exit(1)
            i += 2
        elif args[i] in ("--save", "-s"):
            save = True
            i += 1
        else:
            prompt_parts.append(args[i])
            i += 1

    if prompt_parts:
        prompt = " ".join(prompt_parts).strip()
    elif not sys.stdin.isatty():
        prompt = sys.stdin.read().strip()
    else:
        prompt = ""

    if not prompt:
        print(USAGE, file=sys.stderr)
        sys.exit(1)

    client = Anthropic(api_key=api_key)
    pipeline = Pipeline([WriterStage(client, model)], client)

    print("Generating your story...\n", file=sys.stderr)
    for chunk in pipeline.stream(prompt):
        print(chunk, end="", flush=True)
    print()  # final newline

    if save and pipeline.last_ctx is not None:
        output_root = Path.cwd() / "output"
        story_dir = _save_story(output_root, prompt, model, pipeline.last_ctx.data)
        print(f"\nSaved to {story_dir}/", file=sys.stderr)
