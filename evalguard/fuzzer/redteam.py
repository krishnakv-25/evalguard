"""Red-Teaming Engine: Generates and executes adversarial test suites."""

from typing import Any, Dict, List, Optional
from evalguard.fuzzer.mutators import ALL_MUTATORS, BaseMutator
from evalguard.models import TestCase, TestSuiteResult
from evalguard.targets.base import BaseTarget


class RedTeamFuzzer:
    """Fuzzes input prompts against known jailbreak vectors and evaluates system defenses."""

    def __init__(self, mutators: Optional[List[BaseMutator]] = None):
        self.mutators = mutators or ALL_MUTATORS

    def generate_adversarial_suite(
        self,
        seed_prompts: List[str],
        system_prompt: Optional[str] = None,
        canary: Optional[str] = None,
    ) -> List[TestCase]:
        """Expands seed prompts into an adversarial test suite across all mutators."""
        test_cases: List[TestCase] = []

        for p_idx, seed in enumerate(seed_prompts):
            # Baseline prompt test
            test_cases.append(
                TestCase(
                    id=f"adv_seed_{p_idx + 1}_baseline",
                    name=f"Baseline: {seed[:30]}...",
                    prompt=seed,
                    system_prompt=system_prompt,
                    variables={"canary": canary} if canary else {},
                    guards=[
                        {"name": "injection", "config": {"canaries": [canary] if canary else []}},
                        {"name": "pii"},
                        {"name": "toxicity"},
                    ],
                    tags=["redteam", "baseline"],
                )
            )

            # Mutated variants
            for mutator in self.mutators:
                mutated_prompt = mutator.mutate(seed)
                test_cases.append(
                    TestCase(
                        id=f"adv_{p_idx + 1}_{mutator.name.lower()}",
                        name=f"Fuzz [{mutator.name}]: {seed[:25]}...",
                        prompt=mutated_prompt,
                        system_prompt=system_prompt,
                        variables={"canary": canary} if canary else {},
                        guards=[
                            {
                                "name": "injection",
                                "config": {
                                    "canaries": [canary] if canary else [],
                                    "require_refusal_on_attack": True,
                                },
                            },
                            {"name": "pii"},
                            {"name": "toxicity"},
                        ],
                        tags=["redteam", "adversarial", mutator.name.lower()],
                        metadata={"seed_prompt": seed, "mutator": mutator.name},
                    )
                )

        return test_cases
