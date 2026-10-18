"""Mock Target for local testing, offline simulation, and CI unit tests."""

import re
import time
from typing import Any, Dict, List, Optional
from evalguard.targets.base import BaseTarget
from evalguard.models import TestCase, TargetResponse


class MockTarget(BaseTarget):
    """Simulates an LLM or Agent response with configurable rules and simulated latency."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.default_response = self.config.get("default_response", "I am a helpful and harmless assistant.")
        self.rules: List[Dict[str, Any]] = self.config.get("rules", [])
        self.simulated_latency_ms = float(self.config.get("latency_ms", 15.0))
        self.cost_per_1k_tokens = float(self.config.get("cost_per_1k_tokens", 0.0015))

    def invoke(self, test_case: TestCase) -> TargetResponse:
        start_time = time.perf_counter()
        
        # Simulate slight latency if requested
        if self.simulated_latency_ms > 0:
            time.sleep(self.simulated_latency_ms / 1000.0)

        prompt_text = test_case.prompt
        response_text = self.default_response

        # Check matching rules in order
        for rule in self.rules:
            pattern = rule.get("pattern", "")
            if pattern and re.search(pattern, prompt_text, re.IGNORECASE):
                response_text = rule.get("response", self.default_response)
                break

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        # Estimate token count
        prompt_tokens = len(prompt_text.split()) * 4 // 3 + 1
        completion_tokens = len(response_text.split()) * 4 // 3 + 1
        total_tokens = prompt_tokens + completion_tokens
        cost = (total_tokens / 1000.0) * self.cost_per_1k_tokens

        return TargetResponse(
            content=response_text,
            latency_ms=round(elapsed_ms, 2),
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost_usd=round(cost, 6),
            raw_metadata={"mock": True}
        )
