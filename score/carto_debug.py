"""Temporary startup diagnostics for CARTO_API_KEY wiring.

Prints whether CARTO_API_KEY is visible at various stages of process startup.
It never prints the secret value -- only presence, emptiness and length -- so it
is safe to leave in pod logs. Grep pod logs for "[CARTO-DEBUG]".

Remove this module (and its call sites) once the env-var wiring is confirmed.
"""

import os
import sys


def probe(stage, *, check_setting=False):
    """Emit a one-line diagnostic about CARTO_API_KEY at a given startup stage.

    Args:
        stage: human-readable label for where in startup this runs.
        check_setting: also report the resolved Django setting (only valid once
            settings are loaded).
    """
    env_val = os.environ.get("CARTO_API_KEY")
    msg = (
        f"[CARTO-DEBUG] stage={stage!r} "
        f"env_present={env_val is not None} "
        f"env_nonempty={bool(env_val)} "
        f"env_len={len(env_val) if env_val else 0}"
    )
    if check_setting:
        try:
            from django.conf import settings

            setting_val = getattr(settings, "CARTO_API_KEY", "\x00__MISSING__")
            if setting_val == "\x00__MISSING__":
                msg += " setting=<MISSING attribute>"
            else:
                msg += (
                    f" setting_nonempty={bool(setting_val)} "
                    f"setting_len={len(setting_val) if setting_val else 0}"
                )
        except Exception as exc:  # settings not configured yet, etc.
            msg += f" setting=<error: {exc!r}>"
    print(msg, file=sys.stderr, flush=True)
