from __future__ import annotations

from collections.abc import Callable

from app.ingestion.schemas import IngestionDocument


SourceBuilder = Callable[..., IngestionDocument]


class IngestionRegistry:
    def __init__(self) -> None:
        self._builders: dict[str, SourceBuilder] = {}

    def register(self, name: str, builder: SourceBuilder) -> None:
        if name in self._builders:
            raise ValueError(f"Source already registered: {name}")
        self._builders[name] = builder

    def get(self, name: str) -> SourceBuilder:
        if name not in self._builders:
            raise KeyError(f"Unknown source: {name}")
        return self._builders[name]

    def list_sources(self) -> list[str]:
        return sorted(self._builders.keys())


registry = IngestionRegistry()
