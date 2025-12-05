"""Run ESLint on frontend files."""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def resolve_runner() -> list[str]:
    """Return the CLI to run, preferring bunx when available."""
    if shutil.which("bunx"):
        return ["bunx"]
    if shutil.which("bun"):
        return ["bun", "x"]
    if shutil.which("npx"):
        return ["npx"]
    raise SystemExit("Neither bun nor npm (npx) is installed.")


# Change to frontend directory
frontend_dir = Path(__file__).parent.parent / "frontend"

# Run eslint with all passed filenames
command = resolve_runner() + ["eslint", "--fix"] + sys.argv[1:]
result = subprocess.run(command, cwd=frontend_dir)

sys.exit(result.returncode)
