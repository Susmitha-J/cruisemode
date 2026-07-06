from __future__ import annotations

"""
BaseAgent — abstract base class for all CruiseMode agents.

Every agent in the system extends BaseAgent and implements the `run()` method.
Agents receive a shared workflow state dict, operate on it, and return it.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any


class BaseAgent(ABC):
    """
    Abstract base class for CruiseMode agents.

    Each agent:
    - Has a name and description
    - Receives the shared workflow state dictionary
    - Performs its task and updates the state
    - Returns the updated state
    """

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.logger = logging.getLogger(f"cruisemode.agent.{name}")

    @abstractmethod
    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        """
        Execute the agent's task.

        Args:
            state: Shared workflow state dictionary.

        Returns:
            Updated workflow state dictionary.
        """
        ...

    def log(self, message: str, level: str = "info"):
        """Convenience logging with agent name prefix."""
        getattr(self.logger, level)(f"[{self.name}] {message}")

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}')>"
