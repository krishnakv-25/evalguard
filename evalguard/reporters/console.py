"""Console Reporter with colorized ANSI output for CI/CD terminals."""

import sys
from evalguard.models import TestSuiteResult, TestResult


class ConsoleColors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"


class ConsoleReporter:
    """Renders formatted test execution results to stdout."""

    def __init__(self, color: bool = True):
        self.use_color = color and sys.stdout.isatty()

    def _c(self, color_code: str, text: str) -> str:
        if not self.use_color:
            return text
        return f"{color_code}{text}{ConsoleColors.RESET}"

    def report(self, result: TestSuiteResult) -> None:
        c = self._c
        print()
        print(c(ConsoleColors.BOLD + ConsoleColors.CYAN, f"=== EvalGuard Test Suite: {result.suite_name} ==="))
        print(c(ConsoleColors.DIM, f"Ran {result.total_cases} test cases in {result.duration_ms / 1000.0:.2f}s"))
        print("-" * 75)

        # Print each test case row
        for res in result.results:
            if res.passed and not res.error:
                status_badge = c(ConsoleColors.GREEN, "[PASS]")
            elif res.error:
                status_badge = c(ConsoleColors.RED, "[ERR ]")
            else:
                status_badge = c(ConsoleColors.RED, "[FAIL]")

            score_str = f"Score: {res.overall_score:.2f}"
            latency_str = f"{res.response.latency_ms:.0f}ms" if res.response else "N/A"
            name_display = res.test_case_name[:38].ljust(40)

            print(f" {status_badge} {name_display} {latency_str.rjust(8)} | {score_str}")

            # Failure details
            if not res.passed or res.error:
                if res.error:
                    print(c(ConsoleColors.RED, f"        Error: {res.error}"))
                for gr in res.guard_results:
                    if not gr.passed:
                        print(c(ConsoleColors.YELLOW, f"        x [{gr.guard_name}] {gr.reason}"))

        print("-" * 75)
        
        # Summary Box
        passed_pct = (result.passed_cases / result.total_cases * 100) if result.total_cases else 0.0
        print(f"Total: {result.total_cases}  |  "
              f"{c(ConsoleColors.GREEN, f'Passed: {result.passed_cases}')}  |  "
              f"{c(ConsoleColors.RED, f'Failed: {result.failed_cases}')}  |  "
              f"Pass Rate: {passed_pct:.1f}%  |  "
              f"Avg Score: {result.average_score:.2f}")

        # Quality Gate Verdict
        print()
        if result.quality_gate_passed:
            verdict = c(ConsoleColors.BOLD + ConsoleColors.GREEN, ">>> CI/CD QUALITY GATE: PASSED <<<")
            print(f"  {verdict}")
        else:
            verdict = c(ConsoleColors.BOLD + ConsoleColors.RED, ">>> CI/CD QUALITY GATE: BLOCKED / FAILED <<<")
            print(f"  {verdict}")
            for reason in result.gate_failure_reasons:
                print(c(ConsoleColors.RED, f"  * {reason}"))
        print()
