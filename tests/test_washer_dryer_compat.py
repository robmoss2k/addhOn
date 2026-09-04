# Copyright (C) 2026 tis24dev
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Regression tests for the narrow BHA6SD696M6DB980 Eco-dry compatibility shim."""
from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest

REPO_ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "washer_dryer_compat",
    REPO_ROOT / "custom_components" / "addhon" / "washer_dryer_compat.py",
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
apply_eco_dry_compatibility = MODULE.apply_eco_dry_compatibility


class Param:
    def __init__(self, value: str) -> None:
        self._value = value

    @property
    def value(self) -> str:
        return self._value

    @property
    def intern_value(self) -> str:
        return self._value


def command() -> SimpleNamespace:
    return SimpleNamespace(
        parameters={
            "programType": Param("W+D"),
            "dryOption": Param("0"),
            "dryLevel": Param("0"),
            "dryTime": Param("1"),
            "energyLabel": Param("4"),
        }
    )


class EcoDryCompatibilityTest(unittest.TestCase):
    def test_exact_model_program_gets_app_proven_values(self) -> None:
        cmd = command()
        applied = apply_eco_dry_compatibility(
            SimpleNamespace(model_name="BHA6SD696M6DB980"),
            cmd,
            "eco_40_60_new_energy_label",
        )
        self.assertEqual(
            {"dryLevel": "1", "dryTime": "0", "energyLabel": "1"}, applied
        )
        self.assertEqual("1", cmd.parameters["dryLevel"].intern_value)
        self.assertEqual("0", cmd.parameters["dryTime"].intern_value)
        self.assertEqual("1", cmd.parameters["energyLabel"].intern_value)

    def test_other_model_is_untouched(self) -> None:
        cmd = command()
        self.assertEqual(
            {},
            apply_eco_dry_compatibility(
                SimpleNamespace(model_name="ANOTHER-MODEL"),
                cmd,
                "eco_40_60_new_energy_label",
            ),
        )
        self.assertEqual("0", cmd.parameters["dryLevel"].intern_value)

    def test_other_program_is_untouched(self) -> None:
        cmd = command()
        self.assertEqual(
            {},
            apply_eco_dry_compatibility(
                SimpleNamespace(model_name="BHA6SD696M6DB980"), cmd, "cotton"
            ),
        )
        self.assertEqual("0", cmd.parameters["dryLevel"].intern_value)

    def test_context_mismatch_fails_closed(self) -> None:
        cmd = command()
        cmd.parameters["programType"] = Param("W")
        with self.assertRaisesRegex(RuntimeError, "context mismatch"):
            apply_eco_dry_compatibility(
                SimpleNamespace(model_name="BHA6SD696M6DB980"),
                cmd,
                "eco_40_60_new_energy_label",
            )

    def test_missing_override_parameter_fails_closed(self) -> None:
        cmd = command()
        del cmd.parameters["energyLabel"]
        with self.assertRaisesRegex(RuntimeError, "required parameter"):
            apply_eco_dry_compatibility(
                SimpleNamespace(model_name="BHA6SD696M6DB980"),
                cmd,
                "eco_40_60_new_energy_label",
            )


if __name__ == "__main__":
    unittest.main()
