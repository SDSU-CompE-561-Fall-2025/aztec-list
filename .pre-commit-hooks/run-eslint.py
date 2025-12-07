"""Run ESLint on frontend files."""
import shutil
import subprocess
import sys
from pathlib import Path

try:
    runner = "bunx" if shutil.which("bunx") else "npx"
    frontend_dir = Path(__file__).parent.parent / "frontend"
    files = [f.removeprefix("frontend/") for f in sys.argv[1:]]

    if not files:
        print("No files to lint", file=sys.stderr)
        sys.exit(0)

    print(f"Running ESLint on {len(files)} file(s) with {runner}...", file=sys.stderr)
    result = subprocess.run(
        [runner, "eslint", "--fix", *files],
        cwd=frontend_dir,
        capture_output=True,
        text=True,
    )

    if result.stdout:
        print(result.stdout, file=sys.stderr)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    if result.returncode != 0:
        print(f"ESLint failed with exit code {result.returncode}", file=sys.stderr)
    else:
        print("ESLint completed successfully", file=sys.stderr)

    sys.exit(result.returncode)

except Exception as e:
    print(f"Error running ESLint: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)
