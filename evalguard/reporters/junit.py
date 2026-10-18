"""JUnit XML Reporter for CI/CD test dashboards (GitHub Actions, GitLab, Jenkins)."""

import xml.etree.ElementTree as ET
from evalguard.models import TestSuiteResult


class JUnitReporter:
    """Exports test suite results to standard JUnit XML format."""

    def generate_xml(self, result: TestSuiteResult) -> str:
        """Returns the JUnit XML string representation."""
        testsuites = ET.Element("testsuites")
        suite_elem = ET.SubElement(
            testsuites,
            "testsuite",
            name=result.suite_name,
            tests=str(result.total_cases),
            failures=str(result.failed_cases),
            errors=str(result.error_cases),
            time=f"{result.duration_ms / 1000.0:.3f}",
        )

        for tr in result.results:
            case_time = f"{tr.response.latency_ms / 1000.0:.3f}" if tr.response else "0.000"
            case_elem = ET.SubElement(
                suite_elem,
                "testcase",
                name=tr.test_case_name,
                classname=f"evalguard.{result.suite_name}",
                time=case_time,
            )

            if tr.error:
                error_elem = ET.SubElement(
                    case_elem,
                    "error",
                    message="Model Invocation Error",
                    type="InvocationError"
                )
                error_elem.text = tr.error
            elif not tr.passed:
                failed_guards = [gr for gr in tr.guard_results if not gr.passed]
                reasons = "\n".join(f"[{gr.guard_name}] {gr.reason}" for gr in failed_guards)
                fail_elem = ET.SubElement(
                    case_elem,
                    "failure",
                    message="Quality Guard Assertion Failed",
                    type="AssertionError"
                )
                fail_elem.text = f"Prompt: {tr.prompt}\n\nViolations:\n{reasons}"

        # Pretty indentation
        ET.indent(testsuites, space="  ", level=0)
        return ET.tostring(testsuites, encoding="utf-8", xml_declaration=True).decode("utf-8")

    def write_to_file(self, result: TestSuiteResult, output_path: str) -> None:
        """Writes the XML report to the specified file path."""
        xml_content = self.generate_xml(result)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(xml_content)
