"""Data models for EvalGuard test suites, test cases, and evaluation results."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import time


@dataclass
class TargetResponse:
    """Standardized response from any model or agent target."""
    content: str
    latency_ms: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    raw_metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class GuardResult:
    """Result of evaluating a single guard on a target response."""
    guard_name: str
    passed: bool
    score: float  # 0.0 to 1.0
    reason: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestCase:
    """Individual test scenario to be executed by EvalGuard."""
    id: str
    name: str
    prompt: str
    system_prompt: Optional[str] = None
    context: Optional[List[str]] = None
    expected_output: Optional[str] = None
    variables: Dict[str, Any] = field(default_factory=dict)
    guards: List[Dict[str, Any]] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestResult:
    """Aggregated evaluation result for an individual test case."""
    test_case_id: str
    test_case_name: str
    prompt: str
    response: Optional[TargetResponse]
    guard_results: List[GuardResult] = field(default_factory=list)
    passed: bool = True
    overall_score: float = 1.0
    error: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def calculate_status(self) -> None:
        """Computes overall pass/fail status and composite score."""
        if self.error:
            self.passed = False
            self.overall_score = 0.0
            return

        if not self.guard_results:
            self.passed = True
            self.overall_score = 1.0
            return

        self.passed = all(gr.passed for gr in self.guard_results)
        self.overall_score = sum(gr.score for gr in self.guard_results) / len(self.guard_results)


@dataclass
class TestSuiteConfig:
    """Global configuration and thresholds for a test suite."""
    name: str
    description: str = ""
    target: Dict[str, Any] = field(default_factory=dict)
    default_guards: List[Dict[str, Any]] = field(default_factory=list)
    min_overall_score: float = 0.85
    max_critical_failures: int = 0
    concurrency: int = 4
    timeout_seconds: float = 30.0


@dataclass
class TestSuiteResult:
    """Overall result of executing an entire test suite."""
    suite_name: str
    total_cases: int = 0
    passed_cases: int = 0
    failed_cases: int = 0
    error_cases: int = 0
    duration_ms: float = 0.0
    results: List[TestResult] = field(default_factory=list)
    average_score: float = 1.0
    quality_gate_passed: bool = True
    gate_failure_reasons: List[str] = field(default_factory=list)

    def evaluate_quality_gate(self, min_score: float = 0.85, max_failures: int = 0) -> None:
        """Determines if the run passes the CI/CD Quality Gate criteria."""
        self.total_cases = len(self.results)
        self.passed_cases = sum(1 for r in self.results if r.passed and not r.error)
        self.failed_cases = sum(1 for r in self.results if not r.passed and not r.error)
        self.error_cases = sum(1 for r in self.results if r.error is not None)

        if self.results:
            self.average_score = sum(r.overall_score for r in self.results) / len(self.results)
        else:
            self.average_score = 0.0

        self.gate_failure_reasons.clear()
        if self.failed_cases > max_failures:
            self.gate_failure_reasons.append(
                f"Failed cases ({self.failed_cases}) exceeded maximum allowed threshold ({max_failures})."
            )
        if self.error_cases > 0:
            self.gate_failure_reasons.append(
                f"Execution encountered {self.error_cases} error(s) during model invocation."
            )
        if self.average_score < min_score:
            self.gate_failure_reasons.append(
                f"Average score ({self.average_score:.2f}) was below required threshold ({min_score:.2f})."
            )

        self.quality_gate_passed = len(self.gate_failure_reasons) == 0
