"""Format and Structure Guards: JSON Schema and Regex invariants."""

import json
import re
from typing import Any, Dict, List, Optional
from evalguard.guards.base import BaseGuard
from evalguard.models import TestCase, TargetResponse, GuardResult


def extract_json(text: str) -> Optional[Any]:
    """Extracts JSON object or array from plain text or markdown code fences."""
    text = text.strip()
    
    # 1. Direct parse attempt
    try:
        return json.loads(text)
    except Exception:
        pass

    # 2. Markdown code block extraction
    md_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if md_match:
        try:
            return json.loads(md_match.group(1).strip())
        except Exception:
            pass

    # 3. Bracket extraction: first '{' to last '}' or '[' to ']'
    obj_match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", text)
    if obj_match:
        try:
            return json.loads(obj_match.group(1).strip())
        except Exception:
            pass

    return None


class JsonSchemaGuard(BaseGuard):
    """Enforces valid JSON syntax, required properties, and field types."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("JsonSchemaGuard", config)
        self.required_keys: List[str] = self.config.get("required_keys", [])
        self.field_types: Dict[str, str] = self.config.get("field_types", {})

    def evaluate(self, test_case: TestCase, response: TargetResponse) -> GuardResult:
        content = response.content or ""
        parsed = extract_json(content)

        if parsed is None:
            return GuardResult(
                guard_name=self.name,
                passed=False,
                score=0.0,
                reason="Failed to parse response as valid JSON.",
                details={"raw_content_preview": content[:200]}
            )

        if not isinstance(parsed, dict) and not isinstance(parsed, list):
            return GuardResult(
                guard_name=self.name,
                passed=False,
                score=0.0,
                reason=f"Expected JSON object or list, got {type(parsed).__name__}.",
                details={"parsed_type": type(parsed).__name__}
            )

        errors: List[str] = []

        if isinstance(parsed, dict):
            # Check required keys
            for key in self.required_keys:
                if key not in parsed:
                    errors.append(f"Missing required key: '{key}'")

            # Check field types
            type_mapping = {
                "str": str,
                "string": str,
                "int": int,
                "integer": int,
                "float": (int, float),
                "number": (int, float),
                "bool": bool,
                "boolean": bool,
                "list": list,
                "array": list,
                "dict": dict,
                "object": dict,
            }

            for key, expected_type_name in self.field_types.items():
                if key in parsed:
                    val = parsed[key]
                    expected_python_type = type_mapping.get(expected_type_name.lower())
                    if expected_python_type and not isinstance(val, expected_python_type):
                        errors.append(
                            f"Field '{key}' has type {type(val).__name__}, expected {expected_type_name}"
                        )

        if errors:
            return GuardResult(
                guard_name=self.name,
                passed=False,
                score=0.0,
                reason="; ".join(errors),
                details={"schema_errors": errors, "parsed_keys": list(parsed.keys()) if isinstance(parsed, dict) else []}
            )

        return GuardResult(
            guard_name=self.name,
            passed=True,
            score=1.0,
            reason="JSON response satisfies all schema, type, and required field invariants.",
            details={"parsed_sample": str(parsed)[:200]}
        )


class RegexGuard(BaseGuard):
    """Verifies that response matches mandatory patterns and excludes forbidden patterns."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("RegexGuard", config)
        self.must_match = [re.compile(p) for p in self.config.get("must_match", [])]
        self.must_not_match = [re.compile(p) for p in self.config.get("must_not_match", [])]

    def evaluate(self, test_case: TestCase, response: TargetResponse) -> GuardResult:
        content = response.content or ""
        failures: List[str] = []

        for pat in self.must_match:
            if not pat.search(content):
                failures.append(f"Response failed to match mandatory pattern: '{pat.pattern}'")

        for pat in self.must_not_match:
            if pat.search(content):
                failures.append(f"Response matched forbidden pattern: '{pat.pattern}'")

        if failures:
            return GuardResult(
                guard_name=self.name,
                passed=False,
                score=0.0,
                reason="; ".join(failures),
                details={"regex_failures": failures}
            )

        return GuardResult(
            guard_name=self.name,
            passed=True,
            score=1.0,
            reason="Response satisfied all mandatory and exclusion regex criteria.",
            details={}
        )
