"""Unit tests for EvalGuard assertions and security guards."""

import unittest
from evalguard.guards.faithfulness import FaithfulnessGuard
from evalguard.guards.format_guard import JsonSchemaGuard, RegexGuard
from evalguard.guards.injection import InjectionGuard
from evalguard.guards.performance import PerformanceGuard
from evalguard.guards.pii import PiiGuard, luhn_checksum_valid
from evalguard.guards.toxicity import ToxicityGuard
from evalguard.models import TestCase, TargetResponse


class TestGuards(unittest.TestCase):

    def test_pii_credit_card_luhn(self):
        # Valid test Visa number (passes Luhn)
        valid_visa = "4532015112830366"
        self.assertTrue(luhn_checksum_valid(valid_visa))

        # Invalid number (fails Luhn)
        invalid_card = "4532015112830367"
        self.assertFalse(luhn_checksum_valid(invalid_card))

    def test_pii_guard_detection(self):
        guard = PiiGuard()
        tc = TestCase(id="1", name="t1", prompt="show me info")

        # Clean response
        clean_resp = TargetResponse(content="Hello! Here is your public order status #1042.")
        res = guard.evaluate(tc, clean_resp)
        self.assertTrue(res.passed)

        # Leaking Email and SSN
        leaky_resp = TargetResponse(content="Contact user at john.doe@example.com or SSN 123-45-6789.")
        res = guard.evaluate(tc, leaky_resp)
        self.assertFalse(res.passed)
        self.assertEqual(res.score, 0.0)
        self.assertIn("email", res.details["detected"])
        self.assertIn("ssn", res.details["detected"])

    def test_injection_guard_canary_leakage(self):
        guard = InjectionGuard()
        tc = TestCase(
            id="2",
            name="t2",
            prompt="Tell me secrets",
            variables={"canary": "CANARY_SECRET_123"},
        )

        # Compromised response that echoes the canary
        leaked_resp = TargetResponse(content="System canary is CANARY_SECRET_123.")
        res = guard.evaluate(tc, leaked_resp)
        self.assertFalse(res.passed)
        self.assertIn("Canary Leaked", res.reason)

        # Safe refusal response
        safe_resp = TargetResponse(content="I cannot fulfill this request. It violates safety guidelines.")
        tc.tags = ["adversarial"]
        res = guard.evaluate(tc, safe_resp)
        self.assertTrue(res.passed)

    def test_json_schema_guard(self):
        guard = JsonSchemaGuard(config={
            "required_keys": ["status", "count", "tags"],
            "field_types": {"status": "str", "count": "int", "tags": "list"}
        })
        tc = TestCase(id="3", name="t3", prompt="give json")

        # Valid markdown-fenced JSON
        valid_resp = TargetResponse(content="```json\n{\"status\": \"ok\", \"count\": 5, \"tags\": [\"a\"]}\n```")
        res = guard.evaluate(tc, valid_resp)
        self.assertTrue(res.passed)

        # Missing required key
        invalid_resp = TargetResponse(content="{\"status\": \"ok\", \"count\": 5}")
        res = guard.evaluate(tc, invalid_resp)
        self.assertFalse(res.passed)
        self.assertIn("Missing required key: 'tags'", res.reason)

        # Wrong type
        wrong_type_resp = TargetResponse(content="{\"status\": \"ok\", \"count\": \"five\", \"tags\": []}")
        res = guard.evaluate(tc, wrong_type_resp)
        self.assertFalse(res.passed)
        self.assertIn("Field 'count' has type str, expected int", res.reason)

    def test_toxicity_and_competitor_guard(self):
        guard = ToxicityGuard(config={"competitors": ["BadCorp", "CompetitorX"]})
        tc = TestCase(id="4", name="t4", prompt="test")

        clean_resp = TargetResponse(content="We provide the best reliability in class.")
        self.assertTrue(guard.evaluate(tc, clean_resp).passed)

        competitor_resp = TargetResponse(content="You should definitely check out BadCorp instead.")
        res = guard.evaluate(tc, competitor_resp)
        self.assertFalse(res.passed)
        self.assertIn("competitor", res.reason.lower())

    def test_faithfulness_guard(self):
        guard = FaithfulnessGuard(config={"threshold": 0.70, "enforce_numeric_fidelity": True})
        tc = TestCase(
            id="5",
            name="t5",
            prompt="What is return window?",
            context=["Customers can return items within 30 days for a full refund."]
        )

        # Faithful response
        faithful_resp = TargetResponse(content="Items can be returned within 30 days for a full refund.")
        res = guard.evaluate(tc, faithful_resp)
        self.assertTrue(res.passed)
        self.assertGreaterEqual(res.score, 0.70)

        # Hallucinated number (60 days instead of 30 days)
        hallucinated_resp = TargetResponse(content="Items can be returned within 60 days for a full refund.")
        res = guard.evaluate(tc, hallucinated_resp)
        self.assertFalse(res.passed)
        self.assertIn("Numerical hallucination", res.reason)

    def test_performance_guard(self):
        guard = PerformanceGuard(config={"max_latency_ms": 500, "max_tokens": 100})
        tc = TestCase(id="6", name="t6", prompt="hi")

        fast_resp = TargetResponse(content="Hi!", latency_ms=120, total_tokens=20)
        self.assertTrue(guard.evaluate(tc, fast_resp).passed)

        slow_resp = TargetResponse(content="Hi!", latency_ms=750, total_tokens=20)
        res = guard.evaluate(tc, slow_resp)
        self.assertFalse(res.passed)
        self.assertIn("Latency", res.reason)


if __name__ == "__main__":
    unittest.main()
