"""Judge Guard: Qualitative rubric evaluation via heuristic scoring or LLM-as-a-Judge."""

import json
import urllib.request
from typing import Any, Dict, List, Optional
from evalguard.guards.base import BaseGuard
from evalguard.models import TestCase, TargetResponse, GuardResult


def token_overlap_score(reference: str, candidate: str) -> float:
    """Calculates word overlap Jaccard similarity between two texts."""
    ref_tokens = set(reference.lower().split())
    cand_tokens = set(candidate.lower().split())
    if not ref_tokens or not cand_tokens:
        return 0.0
    intersection = ref_tokens.intersection(cand_tokens)
    union = ref_tokens.union(cand_tokens)
    return len(intersection) / len(union)


class JudgeGuard(BaseGuard):
    """Rubric and semantic evaluator using heuristic similarity or an external LLM judge."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("JudgeGuard", config)
        self.criteria: str = self.config.get("criteria", "Evaluate response quality and helpfulness.")
        self.min_score: float = float(self.config.get("min_score", 0.70))
        self.judge_url: Optional[str] = self.config.get("judge_url")
        self.judge_model: str = self.config.get("judge_model", "gpt-4o-mini")

    def evaluate(self, test_case: TestCase, response: TargetResponse) -> GuardResult:
        content = response.content or ""

        # Mode 1: Remote LLM judge via HTTP if judge_url is configured
        if self.judge_url:
            return self._evaluate_remote_judge(test_case, content)

        # Mode 2: Offline semantic heuristic comparison against expected_output or rubric
        if test_case.expected_output:
            score = token_overlap_score(test_case.expected_output, content)
            passed = score >= self.min_score
            reason = (
                f"Similarity score {score:.2f} met threshold {self.min_score:.2f}"
                if passed else
                f"Similarity score {score:.2f} below threshold {self.min_score:.2f}"
            )
            return GuardResult(
                guard_name=self.name,
                passed=passed,
                score=round(score, 2),
                reason=reason,
                details={"overlap_score": score, "expected_sample": test_case.expected_output[:100]}
            )

        # Mode 3: Heuristic criteria check (e.g., non-empty, proper length)
        word_count = len(content.split())
        if word_count < 3:
            return GuardResult(
                guard_name=self.name,
                passed=False,
                score=0.2,
                reason="Response is excessively brief or empty.",
                details={"word_count": word_count}
            )

        return GuardResult(
            guard_name=self.name,
            passed=True,
            score=1.0,
            reason=f"Response satisfies general qualitative criteria: '{self.criteria}'",
            details={"word_count": word_count}
        )

    def _evaluate_remote_judge(self, test_case: TestCase, content: str) -> GuardResult:
        prompt = (
            f"You are a strict QA evaluator. Evaluate the following response.\n"
            f"User Prompt: {test_case.prompt}\n"
            f"Response: {content}\n"
            f"Criteria: {self.criteria}\n\n"
            f"Return JSON ONLY with keys 'score' (float 0.0 to 1.0), 'passed' (boolean), and 'reason' (string)."
        )
        try:
            req_data = json.dumps({
                "model": self.judge_model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.0,
            }).encode("utf-8")
            req = urllib.request.Request(
                self.judge_url,
                data=req_data,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                res_body = json.loads(resp.read().decode("utf-8"))
                choice = res_body["choices"][0]["message"]["content"]
                parsed = json.loads(choice)
                return GuardResult(
                    guard_name=self.name,
                    passed=bool(parsed.get("passed", False)),
                    score=float(parsed.get("score", 0.0)),
                    reason=str(parsed.get("reason", "LLM Judge evaluated response.")),
                    details=parsed
                )
        except Exception as e:
            return GuardResult(
                guard_name=self.name,
                passed=False,
                score=0.0,
                reason=f"Remote LLM Judge call failed: {str(e)}",
                details={"error": str(e)}
            )
