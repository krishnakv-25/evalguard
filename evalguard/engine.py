"""Test Execution Engine for concurrent evaluation and quality gating."""

from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from typing import List, Optional
from evalguard.guards import create_guard
from evalguard.models import TestCase, TestResult, TestSuiteConfig, TestSuiteResult, TargetResponse
from evalguard.targets import BaseTarget, create_target


class EvalEngine:
    """Executes test cases against a target system and runs quality guardrail assertions."""

    def __init__(self, target: Optional[BaseTarget] = None):
        self.target = target

    def run_case(self, test_case: TestCase, target: BaseTarget) -> TestResult:
        """Runs a single test case through target invocation and guardrail evaluations."""
        # 1. Target invocation
        try:
            response: TargetResponse = target.invoke(test_case)
        except Exception as e:
            return TestResult(
                test_case_id=test_case.id,
                test_case_name=test_case.name,
                prompt=test_case.prompt,
                response=None,
                passed=False,
                overall_score=0.0,
                error=f"Target invocation failed with exception: {str(e)}",
                tags=test_case.tags,
            )

        if response.error:
            return TestResult(
                test_case_id=test_case.id,
                test_case_name=test_case.name,
                prompt=test_case.prompt,
                response=response,
                passed=False,
                overall_score=0.0,
                error=response.error,
                tags=test_case.tags,
            )

        # 2. Guard evaluations
        guard_results = []
        for g_spec in test_case.guards:
            try:
                guard = create_guard(g_spec)
                res = guard.evaluate(test_case, response)
                guard_results.append(res)
            except Exception as e:
                # If a guard throws an unexpected exception, fail gracefully
                from evalguard.models import GuardResult
                guard_name = g_spec.get("name") or g_spec.get("type", "UnknownGuard")
                guard_results.append(
                    GuardResult(
                        guard_name=guard_name,
                        passed=False,
                        score=0.0,
                        reason=f"Guard evaluation crashed: {str(e)}",
                        details={"error": str(e)}
                    )
                )

        result = TestResult(
            test_case_id=test_case.id,
            test_case_name=test_case.name,
            prompt=test_case.prompt,
            response=response,
            guard_results=guard_results,
            tags=test_case.tags,
        )
        result.calculate_status()
        return result

    def run_suite(
        self,
        config: TestSuiteConfig,
        test_cases: List[TestCase],
        target_override: Optional[BaseTarget] = None
    ) -> TestSuiteResult:
        """Executes an entire test suite with concurrency control and computes quality gate verdict."""
        start_time = time.perf_counter()
        active_target = target_override or self.target or create_target(config.target)

        results: List[TestResult] = []
        max_workers = max(1, min(config.concurrency, len(test_cases) or 1))

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_case = {
                executor.submit(self.run_case, tc, active_target): tc for tc in test_cases
            }
            for future in as_completed(future_to_case):
                results.append(future.result())

        # Sort results by original test case order
        case_order = {tc.id: idx for idx, tc in enumerate(test_cases)}
        results.sort(key=lambda r: case_order.get(r.test_case_id, 999999))

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        suite_result = TestSuiteResult(
            suite_name=config.name,
            duration_ms=round(elapsed_ms, 2),
            results=results,
        )
        suite_result.evaluate_quality_gate(
            min_score=config.min_overall_score,
            max_failures=config.max_critical_failures
        )
        return suite_result
