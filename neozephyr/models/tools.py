from __future__ import annotations

from collections.abc import Callable
from typing import Any


class ToolRegistry:
    def __init__(
        self,
        tools: list[tuple[dict[str, Any], Callable[..., Any]]],
    ):
        self._definitions: dict[str, dict[str, Any]] = {}
        self._functions: dict[str, Callable[..., Any]] = {}

        for definition, function in tools:
            name = definition["function"]["name"]

            self._definitions[name] = definition
            self._functions[name] = function

    def names(self) -> list[str]:
        return list(self._definitions.keys())

    def definitions(self) -> list[dict[str, Any]]:
        return list(self._definitions.values())

    def definition(self, name: str) -> dict[str, Any]:
        return self._definitions[name]

    def function(self, name: str) -> Callable[..., Any]:
        return self._functions[name]

    def exists(self, name: str) -> bool:
        return name in self._definitions

    def execute(self, name: str, **kwargs):
        if not self.exists(name):
            raise PermissionError(
                f"Tool '{name}' is not available."
            )

        return self._functions[name](**kwargs)

    def subset(self, names: list[str]) -> "ToolRegistry":
        return ToolRegistry(
            [
                (self._definitions[name], self._functions[name])
                for name in names
            ]
        )