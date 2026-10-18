"""Faithfulness and Groundedness Guard for RAG and Document QA pipelines."""

import re
from typing import Any, Dict, List, Optional, Set
from evalguard.guards.base import BaseGuard
from evalguard.models import TestCase, TargetResponse, GuardResult


def extract_keywords(text: str) -> Set[str]:
    """Extracts non-stopword tokens, capitalized entities, and numerical tokens."""
    stop_words = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with",
        "by", "from", "up", "about", "into", "over", "after", "is", "are", "was", "were",
        "be", "been", "being", "have", "has", "had", "do", "does", "did", "this", "that",
        "these", "those", "it", "its", "they", "them", "their", "we", "us", "our", "you",
        "your", "he", "him", "his", "she", "her", "i", "me", "my", "as", "can", "will"
    }
    tokens = re.findall(r"\b[A-Za-z0-9_$%.-]+\b", text.lower())
    return {t for t in tokens if t not in stop_words and len(t) > 2}


def extract_numbers_and_entities(text: str) -> Set[str]:
    """Extracts numbers, percentages, currencies, and dates."""
    patterns = [
        r"\$?\b\d+(?:,\d{3})*(?:\.\d+)?%?\b",  # Numbers, currency, percentages
        r"\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}(?:,\s+\d{4})?\b",
    ]
    matches = set()
    for pat in patterns:
        for m in re.finditer(pat, text, re.IGNORECASE):
            matches.add(m.group(0).lower())
    return matches


class FaithfulnessGuard(BaseGuard):
    """Verifies that response claims and numbers are strictly grounded in retrieved context."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("FaithfulnessGuard", config)
        self.min_groundedness_score: float = self.config.get("threshold", 0.75)
        self.enforce_numeric_fidelity: bool = self.config.get("enforce_numeric_fidelity", True)

    def evaluate(self, test_case: TestCase, response: TargetResponse) -> GuardResult:
        content = response.content or ""
        context_docs = test_case.context or []

        if not context_docs:
            return GuardResult(
                guard_name=self.name,
                passed=True,
                score=1.0,
                reason="No context documents provided for test case; skipped faithfulness evaluation.",
                details={"skipped": True}
            )

        combined_context = " ".join(context_docs)
        context_keywords = extract_keywords(combined_context)
        context_numbers = extract_numbers_and_entities(combined_context)

        # 1. Numerical & Entity fidelity check
        response_numbers = extract_numbers_and_entities(content)
        hallucinated_numbers = [num for num in response_numbers if num not in context_numbers]

        if self.enforce_numeric_fidelity and hallucinated_numbers:
            return GuardResult(
                guard_name=self.name,
                passed=False,
                score=0.4,
                reason=f"Numerical hallucination: Response mentions numbers/dates not present in context: {hallucinated_numbers}",
                details={"hallucinated_numbers": hallucinated_numbers}
            )

        # 2. Sentence-level claim groundedness
        sentences = [s.strip() for s in re.split(r"[.!?\n]", content) if len(s.strip()) > 15]
        if not sentences:
            return GuardResult(
                guard_name=self.name,
                passed=True,
                score=1.0,
                reason="Response has no distinct factual claims to verify.",
                details={}
            )

        supported_sentences = 0
        unsupported_sentences = []

        for sentence in sentences:
            sent_keywords = extract_keywords(sentence)
            if not sent_keywords:
                supported_sentences += 1
                continue

            overlap = sent_keywords.intersection(context_keywords)
            overlap_ratio = len(overlap) / len(sent_keywords)

            # A sentence is considered supported if at least 40% of its key terms exist in context
            if overlap_ratio >= 0.40:
                supported_sentences += 1
            else:
                unsupported_sentences.append({
                    "sentence": sentence,
                    "overlap_ratio": round(overlap_ratio, 2),
                    "missing_keywords": list(sent_keywords - context_keywords)[:5]
                })

        groundedness_score = round(supported_sentences / len(sentences), 2)
        passed = groundedness_score >= self.min_groundedness_score

        if not passed:
            return GuardResult(
                guard_name=self.name,
                passed=False,
                score=groundedness_score,
                reason=(
                    f"Groundedness score ({groundedness_score:.2f}) fell below threshold "
                    f"({self.min_groundedness_score:.2f}). {len(unsupported_sentences)} sentence(s) ungrounded."
                ),
                details={"unsupported_sentences": unsupported_sentences}
            )

        return GuardResult(
            guard_name=self.name,
            passed=True,
            score=groundedness_score,
            reason=f"Response is faithful to context with {groundedness_score * 100:.0f}% groundedness.",
            details={"groundedness_score": groundedness_score}
        )
