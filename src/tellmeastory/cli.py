import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from .models import DEFAULT_MODEL, MODELS
from .pipeline import Pipeline
from .prompts.writer import SYSTEM
from .stages.outliner import OutlinerStage
from .stages.openai_outliner import OpenAIOutlinerStage
from .stages.openai_writer import OpenAIWriterStage
from .stages.writer import DEFAULT_THINKING_BUDGET, WriterStage

load_dotenv()

USAGE = (
    "Usage: tellmeastory [--model MODEL] [--outline] [--thinking [N]] [--save] \"<story concept>\"\n"
    "       echo \"<story concept>\" | tellmeastory [options]\n"
    f"Models: {', '.join(MODELS)} (default: {DEFAULT_MODEL})\n"
    "--outline   generate a structural outline before writing\n"
    f"--thinking  Anthropic only — extended thinking, optional token budget (default: {DEFAULT_THINKING_BUDGET})"
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

    outline_text = ctx_data.get("outline")
    if outline_text:
        (story_dir / "outline.txt").write_text(outline_text, encoding="utf-8")

    final_prompt = ctx_data.get("final_prompt", "")

    def block(s: str) -> str:
        return "|\n" + "\n".join("  " + line for line in s.splitlines())

    card_lines = [
        f"timestamp: {datetime.now(timezone.utc).isoformat()}",
        f"model: {ctx_data.get('model', '')}",
        f"model_alias: {model_alias}",
        f"word_count: {word_count}",
        f"thinking_budget: {ctx_data.get('thinking_budget') or 'null'}",
        f"outline_generated: {'true' if ctx_data.get('outline') else 'false'}",
        f"outline_input_tokens: {ctx_data.get('outline_input_tokens', 'N/A')}",
        f"outline_output_tokens: {ctx_data.get('outline_output_tokens', 'N/A')}",
        f"input_tokens: {ctx_data.get('input_tokens', 'N/A')}",
        f"output_tokens: {ctx_data.get('output_tokens', 'N/A')}",
        f"user_prompt: {block(prompt)}",
        f"system_prompt: {block(SYSTEM)}",
        f"final_prompt: {block(final_prompt)}",
    ]
    (story_dir / "story-card.yaml").write_text("\n".join(card_lines) + "\n", encoding="utf-8")

    return story_dir


def main() -> None:
    args = sys.argv[1:]
    model = DEFAULT_MODEL
    save = False
    outline = False
    thinking_budget: int | None = None

    i = 0
    prompt_parts: list[str] = []
    while i < len(args):
        if args[i] in ("--model", "-m"):
            if i + 1 >= len(args):
                print(f"Error: {args[i]} requires a value.", file=sys.stderr)
                sys.exit(1)
            model = args[i + 1]
            if model not in MODELS:
                print(f"Error: unknown model '{model}'. Choose from: {', '.join(MODELS)}", file=sys.stderr)
                sys.exit(1)
            i += 2
        elif args[i] in ("--thinking", "-t"):
            if i + 1 < len(args) and args[i + 1].isdigit():
                thinking_budget = int(args[i + 1])
                i += 2
            else:
                thinking_budget = DEFAULT_THINKING_BUDGET
                i += 1
        elif args[i] in ("--outline", "-o"):
            outline = True
            i += 1
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

    provider = MODELS[model].provider

    if provider == "anthropic":
        from anthropic import Anthropic
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            print("Error: ANTHROPIC_API_KEY is not set.", file=sys.stderr)
            sys.exit(1)
        client = Anthropic(api_key=api_key)
        writer = WriterStage(client, model, thinking_budget)
        outliner = OutlinerStage(client, model) if outline else None
    else:
        from openai import OpenAI
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            print("Error: OPENAI_API_KEY is not set.", file=sys.stderr)
            sys.exit(1)
        if thinking_budget is not None:
            print("Note: --thinking is only supported for Anthropic models, ignoring.", file=sys.stderr)
        client = OpenAI(api_key=api_key)
        writer = OpenAIWriterStage(client, model)
        outliner = OpenAIOutlinerStage(client, model) if outline else None

    stages = ([outliner] if outliner else []) + [writer]
    pipeline = Pipeline(stages)

    if not outline:
        status = "Generating your story"
        if thinking_budget is not None and provider == "anthropic":
            status += f" (thinking budget: {thinking_budget} tokens)"
        print(f"{status}...\n", file=sys.stderr)

    for chunk in pipeline.stream(prompt):
        print(chunk, end="", flush=True)
    print()

    if save and pipeline.last_ctx is not None:
        output_root = Path.cwd() / "output"
        story_dir = _save_story(output_root, prompt, model, pipeline.last_ctx.data)
        print(f"\nSaved to {story_dir}/", file=sys.stderr)
