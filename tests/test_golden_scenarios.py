"""Golden regression tests: lock in exact calculator outputs for known scenarios.

These tests exist so that cleanup, refactoring, or dependency changes can NEVER
silently change a number a client or realtor sees. If a test fails, either:
  1. You broke something — fix the code, not the fixture; or
  2. You changed a calculation on purpose — regenerate fixtures with
     `python tests/golden/generate_golden_fixtures.py` and review the diff
     carefully before committing.

Fixtures were generated from v2.8.2-prod (the code live on Railway in July 2026).
Time is frozen (see _meta.frozen_today in the fixture file) because the
refinance path calls date.today().
"""

import json
import os

import pytest
from freezegun import freeze_time

FIXTURE_PATH = os.path.join(os.path.dirname(__file__), "golden", "golden_scenarios.json")

with open(FIXTURE_PATH) as f:
    _FIXTURES = json.load(f)

FROZEN_TODAY = _FIXTURES["_meta"]["frozen_today"]
SCENARIOS = {k: v for k, v in _FIXTURES.items() if not k.startswith("_")}

# Floats are compared to the cent; anything beyond that is a real change.
TOLERANCE = 0.005


def _assert_matches(expected, actual, path=""):
    """Recursively compare expected fixture values against actual output."""
    if isinstance(expected, dict):
        assert isinstance(actual, dict), f"{path}: expected dict, got {type(actual).__name__}"
        missing = set(expected) - set(actual)
        extra = set(actual) - set(expected)
        assert not missing, f"{path}: missing keys {sorted(missing)}"
        assert not extra, f"{path}: unexpected new keys {sorted(extra)}"
        for key in expected:
            _assert_matches(expected[key], actual[key], f"{path}.{key}" if path else key)
    elif isinstance(expected, list):
        assert isinstance(actual, list), f"{path}: expected list, got {type(actual).__name__}"
        assert len(expected) == len(
            actual
        ), f"{path}: length {len(actual)} != expected {len(expected)}"
        for i, (e, a) in enumerate(zip(expected, actual)):
            _assert_matches(e, a, f"{path}[{i}]")
    elif isinstance(expected, (int, float)) and not isinstance(expected, bool):
        assert isinstance(actual, (int, float)) and not isinstance(
            actual, bool
        ), f"{path}: expected number, got {type(actual).__name__} ({actual!r})"
        assert (
            abs(float(expected) - float(actual)) <= TOLERANCE
        ), f"{path}: {actual} != expected {expected}"
    else:
        assert str(expected) == str(actual), f"{path}: {actual!r} != expected {expected!r}"


def _build_inputs(scenario):
    """Deserialize fixture inputs (ISO date strings back to date objects)."""
    from datetime import date

    inputs = dict(scenario["inputs"])
    if "closing_date" in inputs and isinstance(inputs["closing_date"], str):
        inputs["closing_date"] = date.fromisoformat(inputs["closing_date"])
    return inputs


@pytest.mark.parametrize("name", [k for k, v in SCENARIOS.items() if v["kind"] == "purchase"])
def test_golden_purchase(name):
    """Purchase output must match the golden fixture exactly (to the cent)."""
    from calculator import MortgageCalculator

    scenario = SCENARIOS[name]
    with freeze_time(FROZEN_TODAY):
        result = MortgageCalculator().calculate_all(**_build_inputs(scenario))
    normalized = json.loads(json.dumps(result, default=str))
    _assert_matches(scenario["expected"], normalized)


@pytest.mark.parametrize("name", [k for k, v in SCENARIOS.items() if v["kind"] == "refinance"])
def test_golden_refinance(name):
    """Refinance output must match the golden fixture exactly (to the cent)."""
    from calculator import MortgageCalculator

    scenario = SCENARIOS[name]
    with freeze_time(FROZEN_TODAY):
        result = MortgageCalculator().calculate_refinance(**_build_inputs(scenario))
    normalized = json.loads(json.dumps(result, default=str))
    _assert_matches(scenario["expected"], normalized)
