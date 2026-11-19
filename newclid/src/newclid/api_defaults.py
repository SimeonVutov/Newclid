"""Interface for the defaults of the API given installed plugins."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Sequence

if TYPE_CHECKING:
    from newclid.api import DeductiveAgent, Deductor, RuleMatcher
    from newclid.proof_state import ProofState
    from newclid.rule import Rule


class APIDefault(ABC):
    @abstractmethod
    def default_rule_matcher(self) -> RuleMatcher:
        """Return the default rule matcher for the API."""

    @abstractmethod
    def default_deductors(self) -> list[Deductor]:
        """Return the default deductors for the API."""

    @abstractmethod
    def default_deductive_agent(self) -> DeductiveAgent:
        """Return the default deductive agent for the API."""

    @abstractmethod
    def callback(self, proof_state: ProofState, rules: Sequence[Rule]) -> None:
        """Configure the backend for the proof state and selected rules."""
