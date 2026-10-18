"""Configuration and test suite parser for EvalGuard."""

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple
from evalguard.models import TestCase, TestSuiteConfig


def parse_suite_file(file_path: str) -> Tuple[TestSuiteConfig, List[TestCase]]:
    """Loads and validates a test suite configuration from a JSON file.

    Args:
        file_path: Path to the JSON/YAML suite file.

    Returns:
        A tuple of (TestSuiteConfig, List[TestCase]).
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Suite file not found: {file_path}")

    raw_text = path.read_text(encoding="utf-8")
    
    # Attempt standard JSON first
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as json_err:
        # If pyyaml is available, try loading with pyyaml
        try:
            import yaml  # type: ignore
            data = yaml.safe_load(raw_text)
        except ImportError:
            raise ValueError(
                f"Failed to parse '{file_path}' as JSON: {json_err}. "
                "For YAML support, install PyYAML or provide a valid .json file."
            )
        except Exception as yaml_err:
            raise ValueError(f"Failed to parse suite file '{file_path}': {yaml_err}")

    # Parse Suite Config
    suite_name = data.get("name", path.stem)
    config = TestSuiteConfig(
        name=suite_name,
        description=data.get("description", ""),
        target=data.get("target", {}),
        default_guards=data.get("default_guards", []),
        min_overall_score=float(data.get("min_overall_score", 0.85)),
        max_critical_failures=int(data.get("max_critical_failures", 0)),
        concurrency=int(data.get("concurrency", 4)),
        timeout_seconds=float(data.get("timeout_seconds", 30.0)),
    )

    # Parse Test Cases
    raw_cases = data.get("test_cases") or data.get("tests", [])
    test_cases: List[TestCase] = []

    for idx, rc in enumerate(raw_cases):
        case_id = str(rc.get("id", f"case_{idx + 1}"))
        name = rc.get("name", f"Test Case {idx + 1}")
        prompt = rc.get("prompt", "")
        if not prompt:
            raise ValueError(f"Test case '{case_id}' is missing mandatory 'prompt' field.")

        # Merge suite default guards with case-specific guards
        case_guards = list(config.default_guards)
        if "guards" in rc:
            case_guards.extend(rc["guards"])

        tc = TestCase(
            id=case_id,
            name=name,
            prompt=prompt,
            system_prompt=rc.get("system_prompt"),
            context=rc.get("context"),
            expected_output=rc.get("expected_output"),
            variables=rc.get("variables", {}),
            guards=case_guards,
            tags=rc.get("tags", []),
            metadata=rc.get("metadata", {}),
        )
        test_cases.append(tc)

    return config, test_cases
