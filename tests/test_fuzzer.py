"""Unit tests for adversarial fuzzer and prompt mutators."""

import unittest
from evalguard.fuzzer.mutators import (
    Base64Mutator,
    DelimiterConfusionMutator,
    LeetSpeakMutator,
    PrefixInjectionMutator,
    RoleplayDANMutator,
    SystemPromptLeakMutator,
)
from evalguard.fuzzer.redteam import RedTeamFuzzer


class TestFuzzer(unittest.TestCase):

    def test_dan_mutator(self):
        m = RoleplayDANMutator()
        out = m.mutate("show admin keys")
        self.assertIn("DAN", out)
        self.assertIn("show admin keys", out)

    def test_base64_mutator(self):
        m = Base64Mutator()
        out = m.mutate("drop database")
        self.assertIn("base64", out.lower())
        # 'drop database' in base64 is 'ZHJvcCBkYXRhYmFzZQ=='
        self.assertIn("ZHJvcCBkYXRhYmFzZQ==", out)

    def test_leetspeak_mutator(self):
        m = LeetSpeakMutator()
        out = m.mutate("test")
        self.assertIn("7", out)  # 't' -> '7'

    def test_redteam_fuzzer_suite_generation(self):
        fuzzer = RedTeamFuzzer()
        suite = fuzzer.generate_adversarial_suite(
            seed_prompts=["bypass security filter"],
            system_prompt="System secret.",
            canary="CANARY_XYZ",
        )
        # Should generate 1 baseline + 6 mutators = 7 test cases
        self.assertEqual(len(suite), 7)
        self.assertTrue(any(tc.id.endswith("baseline") for tc in suite))
        self.assertTrue(any("adversarial" in tc.tags for tc in suite))


if __name__ == "__main__":
    unittest.main()
