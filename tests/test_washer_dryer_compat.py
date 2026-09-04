# Copyright (C) 2026 tis24dev
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Regression tests for BHA6SD696M6DB980 Eco W+D command compatibility."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _golden import install_stubs

install_stubs()

from custom_components.addhon.client.engine.parameter.enum import (
    HonParameterEnum,
)
from custom_components.addhon.client.engine.parameter.fixed import (
    HonParameterFixed,
)
from custom_components.addhon.client.engine.parameter.range import (
    HonParameterRange,
)
from custom_components.addhon.washer_dryer_compat import (
    apply_eco_dry_compatibility,
)


def _fixed(name: str, value: str) -> HonParameterFixed:
    return HonParameterFixed(
        name,
        {"category": "command", "typology": "fixed", "fixedValue": value},
        "startProgram",
    )


def _enum(name: str, value: str, values: list[str]) -> HonParameterEnum:
    return HonParameterEnum(
        name,
        {
            "category": "command",
            "typology": "enum",
            "defaultValue": value,
            "enumValues": values,
        },
        "startProgram",
    )


def _range(name: str, value: str, minimum: str, maximum: str) -> HonParameterRange:
    return HonParameterRange(
        name,
        {
            "category": "command",
            "typology": "range",
            "defaultValue": value,
            "minimumValue": minimum,
            "maximumValue": maximum,
            "incrementValue": "1",
        },
        "startProgram",
    )


def _command() -> SimpleNamespace:
    """Build the contradictory parameter schema observed on the appliance."""
    return SimpleNamespace(
        category="eco_40_60_new_energy_label",
        parameters={
            "programType": _fixed("programType", "W+D"),
            "dryOption": _fixed("dryOption", "0"),
            "dryLevel": _enum("dryLevel", "0", ["0"]),
            "dryTime": _range("dryTime", "1", "1", "4"),
            "energyLabel": _range("energyLabel", "4", "3", "5"),
        }
    )


class EcoDryCompatibilityTest(unittest.TestCase):
    def test_schema_setters_reject_the_official_app_values(self) -> None:
        command = _command()
        for name, value in {
            "dryLevel": "1",
            "dryTime": "0",
            "energyLabel": "1",
        }.items():
            with self.subTest(name=name), self.assertRaises(ValueError):
                command.parameters[name].value = value

    def test_exact_contract_gets_app_proven_wire_values(self) -> None:
        command = _command()
        applied = apply_eco_dry_compatibility(
            SimpleNamespace(model_name="BHA6SD696M6DB980"),
            command,
            "eco_40_60_new_energy_label",
        )
        self.assertEqual(
            {"dryLevel": "1", "dryTime": "0", "energyLabel": "1"}, applied
        )
        self.assertEqual(
            {"dryLevel": "1", "dryTime": "0", "energyLabel": "1"},
            {
                name: command.parameters[name].intern_value
                for name in ("dryLevel", "dryTime", "energyLabel")
            },
        )

    def test_zoned_model_name_still_matches(self) -> None:
        command = _command()
        applied = apply_eco_dry_compatibility(
            SimpleNamespace(model_name="BHA6SD696M6DB980 Z1"),
            command,
            "eco_40_60_new_energy_label",
        )
        self.assertEqual("1", applied["dryLevel"])

    def test_active_command_category_matches_without_a_pending_selection(self) -> None:
        command = _command()
        applied = apply_eco_dry_compatibility(
            SimpleNamespace(model_name="BHA6SD696M6DB980"), command, None
        )
        self.assertEqual("1", applied["dryLevel"])

    def test_other_model_is_untouched(self) -> None:
        command = _command()
        self.assertEqual(
            {},
            apply_eco_dry_compatibility(
                SimpleNamespace(model_name="ANOTHER-MODEL"),
                command,
                "eco_40_60_new_energy_label",
            ),
        )
        self.assertEqual("0", command.parameters["dryLevel"].intern_value)

    def test_other_program_is_untouched(self) -> None:
        command = _command()
        self.assertEqual(
            {},
            apply_eco_dry_compatibility(
                SimpleNamespace(model_name="BHA6SD696M6DB980"), command, "cotton"
            ),
        )
        self.assertEqual("0", command.parameters["dryLevel"].intern_value)

    def test_other_active_category_is_untouched_without_pending_selection(self) -> None:
        command = _command()
        command.category = "cotton"
        self.assertEqual(
            {},
            apply_eco_dry_compatibility(
                SimpleNamespace(model_name="BHA6SD696M6DB980"), command, None
            ),
        )
        self.assertEqual("0", command.parameters["dryLevel"].intern_value)

    def test_context_mismatch_fails_closed_without_partial_override(self) -> None:
        command = _command()
        command.parameters["programType"] = _fixed("programType", "W")
        with self.assertRaisesRegex(RuntimeError, "context mismatch"):
            apply_eco_dry_compatibility(
                SimpleNamespace(model_name="BHA6SD696M6DB980"),
                command,
                "eco_40_60_new_energy_label",
            )
        self.assertEqual("0", command.parameters["dryLevel"].intern_value)

    def test_missing_parameter_fails_closed_without_partial_override(self) -> None:
        command = _command()
        del command.parameters["energyLabel"]
        with self.assertRaisesRegex(RuntimeError, "required parameter"):
            apply_eco_dry_compatibility(
                SimpleNamespace(model_name="BHA6SD696M6DB980"),
                command,
                "eco_40_60_new_energy_label",
            )
        self.assertEqual("0", command.parameters["dryLevel"].intern_value)


if __name__ == "__main__":
    unittest.main()
