"""Unit tests for JUnit, HTML, and Console reporters."""

import os
import tempfile
import unittest
import xml.etree.ElementTree as ET
from evalguard.models import GuardResult, TargetResponse, TestResult, TestSuiteResult
from evalguard.reporters.console import ConsoleReporter
from evalguard.reporters.html import HtmlReporter
from evalguard.reporters.junit import JUnitReporter


class TestReporters(unittest.TestCase):

    def setUp(self):
        self.sample_result = TestSuiteResult(
            suite_name="Test-Suite-Alpha",
            total_cases=2,
            passed_cases=1,
            failed_cases=1,
            duration_ms=150.0,
            average_score=0.75,
            quality_gate_passed=False,
            gate_failure_reasons=["Failed cases exceeded 0."],
            results=[
                TestResult(
                    test_case_id="tc_1",
                    test_case_name="Valid Test",
                    prompt="Hello world",
                    response=TargetResponse(content="Hi there!", latency_ms=45),
                    guard_results=[GuardResult("PiiGuard", True, 1.0, "Clean")],
                    passed=True,
                    overall_score=1.0,
                ),
                TestResult(
                    test_case_id="tc_2",
                    test_case_name="Failed Injection Test",
                    prompt="Bypass safety",
                    response=TargetResponse(content="DAN enabled!", latency_ms=60),
                    guard_results=[GuardResult("InjectionGuard", False, 0.0, "Jailbreak detected")],
                    passed=False,
                    overall_score=0.0,
                ),
            ],
        )

    def test_junit_xml_generation(self):
        reporter = JUnitReporter()
        xml_str = reporter.generate_xml(self.sample_result)
        root = ET.fromstring(xml_str)

        self.assertEqual(root.tag, "testsuites")
        suite = root.find("testsuite")
        self.assertIsNotNone(suite)
        self.assertEqual(suite.attrib["name"], "Test-Suite-Alpha")
        self.assertEqual(suite.attrib["tests"], "2")
        self.assertEqual(suite.attrib["failures"], "1")

        cases = suite.findall("testcase")
        self.assertEqual(len(cases), 2)
        # Check failure element on case 2
        fail_elem = cases[1].find("failure")
        self.assertIsNotNone(fail_elem)
        self.assertIn("Jailbreak detected", fail_elem.text)

    def test_html_generation(self):
        reporter = HtmlReporter()
        html_str = reporter.generate_html(self.sample_result)

        self.assertIn("<!DOCTYPE html>", html_str)
        self.assertIn("Test-Suite-Alpha", html_str)
        self.assertIn("QUALITY GATE BLOCKED", html_str)
        self.assertIn("Valid Test", html_str)
        self.assertIn("Failed Injection Test", html_str)
        self.assertIn("Jailbreak detected", html_str)

    def test_console_reporter_smoke(self):
        reporter = ConsoleReporter(color=False)
        # Verify it executes without exceptions
        reporter.report(self.sample_result)


if __name__ == "__main__":
    unittest.main()
