"""Python Target for evaluating in-process Python functions, chains, and agents."""

import importlib
import time
from typing import Any, Callable, Dict, Optional
from evalguard.targets.base import BaseTarget
from evalguard.models import TestCase, TargetResponse


class PythonTarget(BaseTarget):
    """Executes a local Python callable or class directly in process."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.entrypoint: str = self.config.get("entrypoint", "")
        self.func: Optional[Callable] = None
        if self.entrypoint:
            self._load_callable(self.entrypoint)

    def _load_callable(self, entrypoint: str) -> None:
        if ":" not in entrypoint:
            raise ValueError(f"Invalid entrypoint format '{entrypoint}'. Expected 'module.submodule:function_name'")
        module_path, func_name = entrypoint.split(":", 1)
        mod = importlib.import_module(module_path)
        self.func = getattr(mod, func_name)

    def invoke(self, test_case: TestCase) -> TargetResponse:
        if not self.func:
            return TargetResponse(
                content="",
                error="PythonTarget has no callable loaded."
            )

        start_time = time.perf_counter()
        try:
            # Call function with test case object or prompt keyword
            res = self.func(test_case.prompt)
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            content = str(res) if res is not None else ""
            prompt_tokens = len(test_case.prompt.split()) * 4 // 3
            comp_tokens = len(content.split()) * 4 // 3

            return TargetResponse(
                content=content,
                latency_ms=round(elapsed_ms, 2),
                prompt_tokens=prompt_tokens,
                completion_tokens=comp_tokens,
                total_tokens=prompt_tokens + comp_tokens,
                raw_metadata={"python_return": type(res).__name__}
            )
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return TargetResponse(
                content="",
                latency_ms=round(elapsed_ms, 2),
                error=f"Python execution error in {self.entrypoint}: {str(e)}"
            )
