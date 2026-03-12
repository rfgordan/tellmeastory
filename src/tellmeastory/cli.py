import os
import sys

from anthropic import Anthropic
from dotenv import load_dotenv

from .pipeline import Pipeline
from .stages.writer import DEFAULT_MODEL, MODELS, WriterStage

load_dotenv()

USAGE = (
    "Usage: tellmeastory [--model sonnet|opus] \"<story concept>\"\n"
    "       echo \"<story concept>\" | tellmeastory [--model sonnet|opus]\n"
    f"Models: {', '.join(MODELS)} (default: {DEFAULT_MODEL})"
)


def main() -> None:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY is not set. Add it to your .env file or environment.", file=sys.stderr)
        sys.exit(1)

    args = sys.argv[1:]
    model = DEFAULT_MODEL

    # Parse --model / -m
    i = 0
    prompt_parts: list[str] = []
    while i < len(args):
        if args[i] in ("--model", "-m"):
            if i + 1 >= len(args):
                print(f"Error: {args[i]} requires a value (sonnet or opus).", file=sys.stderr)
                sys.exit(1)
            model = args[i + 1]
            if model not in MODELS:
                print(f"Error: unknown model '{model}'. Choose from: {', '.join(MODELS)}", file=sys.stderr)
                sys.exit(1)
            i += 2
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
