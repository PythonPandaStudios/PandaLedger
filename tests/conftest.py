"""Pytest configuration shared across the whole test suite.

Forces Toga's dummy backend so UI tests run headlessly (no GTK display
required in CI or a dev container). This must be set before anything
imports ``toga``, so it lives at module scope in the top-level conftest,
which pytest loads before collecting any test module.
"""

from __future__ import annotations

import os

os.environ.setdefault("TOGA_BACKEND", "toga_dummy")
