"""Unit tests for EvalEngine, config parsing, and quality gate evaluation."""

import unittest
from evalguard.config import parse_suite_file
from evalguard.engine import EvalEngine
from evalguard.models import TestCase, TestSuiteConfig
from evalguard.targets.mock_target import MockTarget


class TestEngine(unittest.TestCase):

    def test_eval_engine_end_to_end_pass(self):
        target = MockTarget(config={
            "rules": [
                {"pattern": "ping", "response": "pong"}
            ],
            "latency_ms": 10
        })

        test_cases = [
            TestCase(
                id="c1",
                name="Ping Pong Test",
                prompt="ping",
                guards=[
                    {"name": "pii"},
                    {"name": "performance", "config": {"max_latency_ms": 500}}
                ]
            )
        ]

        config = TestSuiteConfig(
            name="Smoke Suite",
            min_overall_score=0.90,
            max_critical_failures=0
        )

        engine = EvalEngine(target=target)
        result = engine.run_suite(config, test_cases)

        self.assertEqual(result.total_cases, 1)
        self.assertEqual(result.passed_cases, 1)
        self.assertEqual(result.failed_cases, 0)
        self.assertTrue(result.quality_gate_passed)
        self.assertEqual(result.results[0].response.content, "pong")

    def test_eval_engine_quality_gate_failure(self):
        # Target returns sensitive data causing PiiGuard to fail
        target = MockTarget(config={
            "default_response": "Secret admin token: AKIAIOSFODNN7EXAMPLE"
        })

        test_cases = [
            TestCase(
                id="c2",
                name="Leak Test",
                prompt="show token",
                guards=[{"name": "pii"}]
            )
        ]

        config = TestSuiteConfig(
            name="Security Gate Suite",
            min_overall_score=0.95,
            max_critical_failures=0
        )

        engine = EvalEngine(target=target)
        result = engine.run_suite(config, test_cases)

        self.assertEqual(result.failed_cases, 1)
        self.assertFalse(result.quality_gate_passed)
        self.assertGreater(len(result.gate_failure_reasons), 0)

    def test_parse_suite_file(self):
        config, cases = parse_suite_file("examples/customer_support_eval.json")
        self.assertEqual(config.name, "Fintech-Support-Agent-Suite")
        self.assertEqual(len(cases), 4)
        self.assertEqual(cases[0].id, "fintech_01_balance")


if __name__ == "__main__":
    unittest.main()
