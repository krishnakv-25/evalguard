"""Guard registry and factory for EvalGuard."""

from typing import Any, Dict, Type
from evalguard.guards.base import BaseGuard
from evalguard.guards.pii import PiiGuard
from evalguard.guards.injection import InjectionGuard
from evalguard.guards.format_guard import JsonSchemaGuard, RegexGuard
from evalguard.guards.toxicity import ToxicityGuard
from evalguard.guards.faithfulness import FaithfulnessGuard
from evalguard.guards.performance import PerformanceGuard
from evalguard.guards.judge import JudgeGuard

GUARD_REGISTRY: Dict[str, Type[BaseGuard]] = {
    "pii": PiiGuard,
    "piiguard": PiiGuard,
    "injection": InjectionGuard,
    "injectionguard": InjectionGuard,
    "jailbreak": InjectionGuard,
    "json_schema": JsonSchemaGuard,
    "jsonschemaguard": JsonSchemaGuard,
    "regex": RegexGuard,
    "regexguard": RegexGuard,
    "toxicity": ToxicityGuard,
    "toxicityguard": ToxicityGuard,
    "faithfulness": FaithfulnessGuard,
    "faithfulnessguard": FaithfulnessGuard,
    "groundedness": FaithfulnessGuard,
    "performance": PerformanceGuard,
    "performanceguard": PerformanceGuard,
    "sla": PerformanceGuard,
    "judge": JudgeGuard,
    "judgeguard": JudgeGuard,
}


def create_guard(guard_spec: Dict[str, Any]) -> BaseGuard:
    """Instantiates a guard from a declarative configuration dictionary."""
    name = guard_spec.get("name") or guard_spec.get("type", "")
    key = name.lower().replace("-", "_").replace(" ", "")

    guard_cls = GUARD_REGISTRY.get(key)
    if not guard_cls:
        raise ValueError(f"Unknown guard type '{name}'. Available guards: {list(GUARD_REGISTRY.keys())}")

    config = guard_spec.get("config", {})
    # Also pass top-level spec keys as fallback config
    merged_config = {**guard_spec, **config}
    return guard_cls(merged_config)


__all__ = [
    "BaseGuard",
    "PiiGuard",
    "InjectionGuard",
    "JsonSchemaGuard",
    "RegexGuard",
    "ToxicityGuard",
    "FaithfulnessGuard",
    "PerformanceGuard",
    "JudgeGuard",
    "create_guard",
    "GUARD_REGISTRY",
]
