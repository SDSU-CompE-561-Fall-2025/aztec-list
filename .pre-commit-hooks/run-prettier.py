"""Run Prettier on frontend files."""

import shutil
import subprocess
import sys
from pathlib import Path

try:
    runner = "bunx" if shutil.which("bunx") else "npx"
    repo_root = Path(__file__).parent.parent
    frontend_dir = repo_root / "frontend"

    frontend_files = []
    backend_files = []

    for f in sys.argv[1:]:
        if f.startswith("backend/"):
            backend_files.append(f)
        else:
            frontend_files.append(f.removeprefix("frontend/"))

    all_files = frontend_files + backend_files

    if not all_files:
        print("No files to format", file=sys.stderr)
        sys.exit(0)

    print(
        f"Running Prettier on {len(all_files)} file(s)...", file=sys.stderr, flush=True
    )

    if frontend_files and not backend_files:
        result = subprocess.run(
            [runner, "prettier", "--write", *frontend_files],
            cwd=frontend_dir,
            capture_output=True,
            text=True,
        )
    elif backend_files and not frontend_files:
        result = subprocess.run(
            [runner, "prettier", "--write", "--parser", "html", *backend_files],
            cwd=repo_root,
            capture_output=True,
            text=True,
        )
    else:
        result_frontend = subprocess.run(
            [runner, "prettier", "--write", *frontend_files],
            cwd=frontend_dir,
            capture_output=True,
            text=True,
        )
        result_backend = subprocess.run(
            [runner, "prettier", "--write", "--parser", "html", *backend_files],
            cwd=repo_root,
            capture_output=True,
            text=True,
        )
        result = subprocess.CompletedProcess(
            args=[],
            returncode=max(result_frontend.returncode, result_backend.returncode),
            stdout=result_frontend.stdout + result_backend.stdout,
            stderr=result_frontend.stderr + result_backend.stderr,
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
            f"Prettier failed with exit code {result.returncode}",
            file=sys.stderr,
            flush=True,
        )
    else:
        print("Prettier completed successfully", file=sys.stderr, flush=True)

    sys.exit(result.returncode)

except Exception as e:
    print(f"Error running Prettier: {e}", file=sys.stderr)
    import traceback

    traceback.print_exc(file=sys.stderr)
    sys.exit(1)
