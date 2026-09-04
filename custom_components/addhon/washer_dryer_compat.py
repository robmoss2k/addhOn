# Copyright (C) 2026 tis24dev
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Narrow compatibility corrections for washer-dryer command schemas."""
from __future__ import annotations

from typing import Any

_MODEL = "BHA6SD696M6DB980"
_PROGRAM = "eco_40_60_new_energy_label"
_REQUIRED_CONTEXT = {"programType": "W+D", "dryOption": "0"}
_APP_PROVEN_OVERRIDES = {"dryLevel": "1", "dryTime": "0", "energyLabel": "1"}


def _model_name(appliance: Any) -> str:
    """Return the unzoned model identifier exposed by the appliance."""
    for attr in ("model_name", "modelName", "model"):
        value = getattr(appliance, attr, None)
        if value:
            return str(value).split(" Z", 1)[0]
    info = getattr(appliance, "info", None)
    if isinstance(info, dict):
        return str(info.get("modelName") or info.get("model") or "")
    return ""


def apply_eco_dry_compatibility(
    appliance: Any,
    command: Any,
    selected_program: str | None,
) -> dict[str, str]:
    """Apply app-proven Eco W+D values where the live schema is incorrect.

    The BHA6SD696M6DB980 catalogue restricts ``dryLevel``, ``dryTime`` and
    ``energyLabel`` to values which start a wash-only cycle. Command history from the
    same appliance records the official app successfully sending the values below.

    Return the applied values, or an empty dict when the exact compatibility contract
    does not match. A matched contract with missing or inconsistent parameters fails
    closed instead of constructing a partially corrected command.
    """
    if _model_name(appliance).upper() != _MODEL:
        return {}
    active_program = selected_program or getattr(command, "category", None)
    if str(active_program or "").lower() != _PROGRAM:
        return {}

    params = getattr(command, "parameters", None)
    if not isinstance(params, dict):
        raise TypeError("Eco-dry compatibility matched but startProgram has no parameters")

    for name, expected in _REQUIRED_CONTEXT.items():
        param = params.get(name)
        actual = getattr(param, "intern_value", getattr(param, "value", None))
        if str(actual) != expected:
            raise RuntimeError(
                f"Eco-dry compatibility context mismatch: {name}={actual!s}, expected {expected}"
            )

    missing = [name for name in _APP_PROVEN_OVERRIDES if name not in params]
    if missing:
        raise RuntimeError(
            "Eco-dry compatibility matched but required parameter(s) are missing: "
            + ", ".join(missing)
        )

    for name, value in _APP_PROVEN_OVERRIDES.items():
        # The setters reject these values because they enforce the contradictory live
        # schema. Assign the wire value directly only after the exact model, programme,
        # W+D category, dry option and complete parameter set have all been verified.
        params[name]._value = value
    return dict(_APP_PROVEN_OVERRIDES)
