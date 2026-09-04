# Copyright (C) 2026 tis24dev
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Narrow compatibility corrections for appliance schemas contradicted by hOn history.

The BHA6SD696M6DB980 command catalogue constrains the Eco 40-60 category to
``dryLevel=0``, ``dryTime=1..4`` and ``energyLabel=3..5``.  The same appliance's
official-app command history proves that its accepted wash-and-dry form uses 1, 0 and 1
respectively.  Sending the schema defaults starts a wash-only cycle.

This module deliberately bypasses the parameter setters only for that exact model,
programme and internally consistent W+D category.  It is a compatibility shim, not a
general relaxation of command validation.
"""
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
    """Apply the app-proven Eco wash-and-dry values when the live schema is wrong.

    Returns the values applied, or an empty dict when the exact compatibility contract
    does not match.  A matched contract with a missing parameter fails closed.
    """
    if _model_name(appliance).upper() != _MODEL:
        return {}
    if str(selected_program or "").lower() != _PROGRAM:
        return {}

    params = getattr(command, "parameters", None)
    if not isinstance(params, dict):
        raise RuntimeError("Eco-dry compatibility matched but startProgram has no parameters")

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
        # The cloud schema's setter rejects these values even though the official app's
        # accepted command history proves them.  Assign the wire value directly, within
        # the exact model/program/context gate above.
        params[name]._value = value
    return dict(_APP_PROVEN_OVERRIDES)

