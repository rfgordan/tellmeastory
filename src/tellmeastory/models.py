from dataclasses import dataclass


@dataclass(frozen=True)
class ModelInfo:
    provider: str  # "anthropic" | "openai"
    model_id: str


MODELS: dict[str, ModelInfo] = {
    "sonnet4_6": ModelInfo("anthropic", "claude-sonnet-4-6"),
    "opus4_6":   ModelInfo("anthropic", "claude-opus-4-6"),
    "gpt4_1":    ModelInfo("openai",    "gpt-4.1"),
    "gpt5_4":    ModelInfo("openai",    "gpt-5.4"),
}

DEFAULT_MODEL = "sonnet4_6"
