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

    print(f"Running ESLint on {len(files)} file(s)...", file=sys.stderr, flush=True)
    result = subprocess.run(
        [runner, "eslint", "--fix", *files],
        cwd=frontend_dir,
        capture_output=True,
        text=True,
    )

    output_lines = []
    seen_lines = set()

    noise_patterns = [
        "Resolved, downloaded",
        "Saved lockfile",
        "Saved",
        "Resolving dependencies",
    ]

    def should_skip(line: str) -> bool:
        line_stripped = line.strip()
        return any(pattern in line_stripped for pattern in noise_patterns)

    # Process stdout
    if result.stdout:
        for line in result.stdout.splitlines():
            line_stripped = line.strip()
            if (
                line_stripped
                and line_stripped not in seen_lines
                and not should_skip(line)
            ):
                seen_lines.add(line_stripped)
                output_lines.append(line)

    # Process stderr (deduplicate against stdout)
    if result.stderr:
        for line in result.stderr.splitlines():
            line_stripped = line.strip()
            if (
                line_stripped
                and line_stripped not in seen_lines
                and not should_skip(line)
            ):
                seen_lines.add(line_stripped)
                output_lines.append(line)

    for line in output_lines:
        print(line, file=sys.stderr, flush=True)

    if result.returncode != 0:
        print(
            f"ESLint failed with exit code {result.returncode}",
            file=sys.stderr,
            flush=True,
        )
    else:
        print("ESLint completed successfully", file=sys.stderr, flush=True)

    sys.exit(result.returncode)

except Exception as e:
    print(f"Error running ESLint: {e}", file=sys.stderr)
    import traceback

    traceback.print_exc(file=sys.stderr)
    sys.exit(1)
