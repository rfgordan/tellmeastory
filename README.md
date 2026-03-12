# tellmeastory

A CLI that streams the opening of a novel from a single story concept. Give it a prompt; get prose.

## Setup

```bash
# Install dependencies
uv sync

# Add your API key(s) to .env
cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY and/or OPENAI_API_KEY
```

## Usage

```bash
uv run tellmeastory "A detective finds her own obituary"
echo "concept" | uv run tellmeastory
uv run tellmeastory "concept" > novel.txt
```

## Options

| Flag | Short | Description |
|------|-------|-------------|
| `--model MODEL` | `-m` | Model to use (default: `sonnet4_6`) |
| `--outline` | `-o` | Generate a structural outline before writing |
| `--thinking [N]` | `-t` | Enable extended thinking with optional token budget (Anthropic only, default: 5000) |
| `--save` | `-s` | Save output to `output/<slug>-<timestamp>/` |

## Models

| Alias | Model | Provider |
|-------|-------|----------|
| `sonnet4_6` | claude-sonnet-4-6 | Anthropic |
| `opus4_6` | claude-opus-4-6 | Anthropic |
| `gpt4_1` | gpt-4.1 | OpenAI |
| `gpt5_4` | gpt-5.4 | OpenAI |

## Examples

```bash
# Use Opus with extended thinking and save the result
uv run tellmeastory --model opus4_6 --thinking --save "A lighthouse keeper who can hear the future"

# Generate an outline first, then write
uv run tellmeastory --outline "Twin sisters separated at birth, one raised by wolves"

# Use OpenAI
uv run tellmeastory --model gpt5_4 --outline --save "A city that only exists at night"

# Pipe a concept from a file
cat concept.txt | uv run tellmeastory --model gpt4_1 --save
```

## Output

With `--save`, each run creates a directory under `output/`:

```
output/
└── a-detective-finds-her-own-obituary-20260312-182102/
    ├── story.txt         # the prose
    ├── outline.txt       # if --outline was used
    └── story-card.yaml   # inputs, model, token counts, word count
```

## Architecture

The pipeline is a sequence of stages that pass a shared `Context` object:

```
[OutlinerStage?] → [WriterStage] → stdout
```

Each stage reads from and writes to `ctx.data`, making it straightforward to add new stages (critic, revision, context compression) without restructuring existing ones.
