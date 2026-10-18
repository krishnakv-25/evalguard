"""Abstract base class for model and agent targets."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from evalguard.models import TestCase, TargetResponse


class BaseTarget(ABC):
    """Abstract interface for all model endpoints, agent runtimes, and mock services."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    @abstractmethod
    def invoke(self, test_case: TestCase) -> TargetResponse:
        """Executes a test case against the target system and returns a standardized response.

        Args:
            test_case: The test case containing prompt, system prompt, context, variables.

        Returns:
            TargetResponse containing content, token usage, latency, and metadata.
        """
        pass
