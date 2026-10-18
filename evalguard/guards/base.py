"""Base class for all EvalGuard assertions and security guards."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from evalguard.models import TestCase, TargetResponse, GuardResult


class BaseGuard(ABC):
    """Abstract base class that all quality and security guards inherit from."""

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.config = config or {}
        self.severity = self.config.get("severity", "high")  # critical, high, medium, low

    @abstractmethod
    def evaluate(self, test_case: TestCase, response: TargetResponse) -> GuardResult:
        """Evaluates the target response against the guard's rules.

        Args:
            test_case: The test scenario including prompt, context, variables.
            response: The model or agent output with metadata.

        Returns:
            GuardResult containing pass/fail boolean, numeric score, and reasoning.
        """
        pass
