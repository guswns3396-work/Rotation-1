"""A tiny named registry. Each extensible layer (outcomes, contrasts, estimators, learners, covariates) owns one.

Adding a feature means writing one function and decorating it:

    from ihs_causal.estimators import ESTIMATORS

    @ESTIMATORS.register("my_estimator")
    def my_estimator(frame, spec): ...

and then naming it in a configuration file.
"""
from __future__ import annotations

from typing import Callable, Dict, List


class Registry:
    def __init__(self, kind: str):
        self.kind = kind
        self._items: Dict[str, Callable] = {}

    def register(self, name: str) -> Callable[[Callable], Callable]:
        def deco(fn: Callable) -> Callable:
            if name in self._items:
                raise ValueError(f"{self.kind} '{name}' is already registered")
            self._items[name] = fn
            return fn
        return deco

    def get(self, name: str) -> Callable:
        try:
            return self._items[name]
        except KeyError:
            known = ", ".join(sorted(self._items)) or "none"
            raise KeyError(f"unknown {self.kind} '{name}'; registered: {known}") from None

    def names(self) -> List[str]:
        return sorted(self._items)

    def __contains__(self, name: str) -> bool:
        return name in self._items
