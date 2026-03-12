from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Context:
    prompt: str
    data: dict[str, Any] = field(default_factory=dict)


class Stage(ABC):
    @abstractmethod
    def run(self, ctx: Context) -> Context: ...
