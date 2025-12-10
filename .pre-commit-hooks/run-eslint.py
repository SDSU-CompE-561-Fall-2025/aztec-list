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

    print(
        f"\nRunning ESLint on {len(files)} file(s) with {runner}...\n", file=sys.stderr
    )
    result = subprocess.run(
        [runner, "eslint", "--fix", *files],
        cwd=frontend_dir,
        capture_output=True,
        text=True,
    )

    if result.stdout:
        for line in result.stdout.splitlines():
            print(line, file=sys.stderr, flush=True)

    if result.stderr:
        for line in result.stderr.splitlines():
            print(line, file=sys.stderr, flush=True)

    if result.returncode != 0:
        print(
            f"\n❌ ESLint failed with exit code {result.returncode}\n",
            file=sys.stderr,
            flush=True,
        )
    else:
        print("\n✅ ESLint completed successfully\n", file=sys.stderr, flush=True)

    sys.exit(result.returncode)

except Exception as e:
    print(f"Error running ESLint: {e}", file=sys.stderr)
    import traceback

    traceback.print_exc(file=sys.stderr)
    sys.exit(1)
