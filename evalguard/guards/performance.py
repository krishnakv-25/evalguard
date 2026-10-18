"""Performance and SLA Guard for latency, tokens, and cost thresholds."""

from typing import Any, Dict, Optional
from evalguard.guards.base import BaseGuard
from evalguard.models import TestCase, TargetResponse, GuardResult


class PerformanceGuard(BaseGuard):
    """Enforces latency, token limit, and cost SLA thresholds."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("PerformanceGuard", config)
        self.max_latency_ms = float(self.config.get("max_latency_ms", 5000.0))
        self.max_tokens = int(self.config.get("max_tokens", 2048))
        self.max_cost_usd = float(self.config.get("max_cost_usd", 0.05))

    def evaluate(self, test_case: TestCase, response: TargetResponse) -> GuardResult:
        violations = []

        # 1. Latency check
        if response.latency_ms > self.max_latency_ms:
            violations.append(
                f"Latency {response.latency_ms:.1f}ms exceeded limit of {self.max_latency_ms:.1f}ms"
            )

        # 2. Token consumption check
        if response.total_tokens > self.max_tokens:
            violations.append(
                f"Total tokens ({response.total_tokens}) exceeded limit ({self.max_tokens})"
            )

        # 3. Cost budget check
        if response.cost_usd > self.max_cost_usd:
            violations.append(
                f"Cost ${response.cost_usd:.4f} exceeded limit ${self.max_cost_usd:.4f}"
            )

        if violations:
            return GuardResult(
                guard_name=self.name,
                passed=False,
                score=0.0,
                reason="; ".join(violations),
                details={
                    "latency_ms": response.latency_ms,
                    "total_tokens": response.total_tokens,
                    "cost_usd": response.cost_usd,
                    "violations": violations,
                }
            )

        return GuardResult(
            guard_name=self.name,
            passed=True,
            score=1.0,
            reason=f"Performance SLA met ({response.latency_ms:.1f}ms, {response.total_tokens} tokens, ${response.cost_usd:.4f}).",
            details={
                "latency_ms": response.latency_ms,
                "total_tokens": response.total_tokens,
                "cost_usd": response.cost_usd,
            }
        )
