"""Allows ``python -m pandaledger`` to launch the app during development."""

from __future__ import annotations

from pandaledger.app import main

if __name__ == "__main__":
    main().main_loop()
