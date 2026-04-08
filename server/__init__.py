"""Email Triage OpenEnv server package."""

from __future__ import annotations

import os

import uvicorn

from server.app import app

__all__ = ["app", "main"]


def main() -> None:
    """Entry point used by pyproject scripts and `python -m server`."""
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run("server.app:app", host="0.0.0.0", port=port, reload=False)


if __name__ == "__main__":
    main()
