"""Target registry and factory for EvalGuard."""

from typing import Any, Dict, Type
from evalguard.targets.base import BaseTarget
from evalguard.targets.mock_target import MockTarget
from evalguard.targets.http_target import HttpTarget
from evalguard.targets.python_target import PythonTarget

TARGET_REGISTRY: Dict[str, Type[BaseTarget]] = {
    "mock": MockTarget,
    "mocktarget": MockTarget,
    "http": HttpTarget,
    "httptarget": HttpTarget,
    "rest": HttpTarget,
    "openai": HttpTarget,
    "python": PythonTarget,
    "pythontarget": PythonTarget,
}


def create_target(target_config: Dict[str, Any]) -> BaseTarget:
    """Instantiates a target runner from configuration."""
    target_type = target_config.get("type", "mock").lower()
    target_cls = TARGET_REGISTRY.get(target_type)
    if not target_cls:
        raise ValueError(f"Unknown target type '{target_type}'. Available types: {list(TARGET_REGISTRY.keys())}")
    return target_cls(target_config)


__all__ = [
    "BaseTarget",
    "MockTarget",
    "HttpTarget",
    "PythonTarget",
    "create_target",
    "TARGET_REGISTRY",
]
