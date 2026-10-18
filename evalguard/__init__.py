"""EvalGuard: CI/CD Quality Gate & Automated Red-Teaming for GenAI & LLM Applications."""

__version__ = "0.1.0"

from evalguard.models import (
    TestCase,
    TestResult,
    TestSuiteConfig,
    TestSuiteResult,
    TargetResponse,
    GuardResult,
)
from evalguard.guards import (
    BaseGuard,
    PiiGuard,
    InjectionGuard,
    JsonSchemaGuard,
    RegexGuard,
    ToxicityGuard,
    FaithfulnessGuard,
    PerformanceGuard,
    JudgeGuard,
    create_guard,
)
from evalguard.targets import (
    BaseTarget,
    MockTarget,
    HttpTarget,
    PythonTarget,
    create_target,
)
from evalguard.engine import EvalEngine
from evalguard.fuzzer import RedTeamFuzzer

__all__ = [
    "__version__",
    "TestCase",
    "TestResult",
    "TestSuiteConfig",
    "TestSuiteResult",
    "TargetResponse",
    "GuardResult",
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
    "BaseTarget",
    "MockTarget",
    "HttpTarget",
    "PythonTarget",
    "create_target",
    "EvalEngine",
    "RedTeamFuzzer",
]
