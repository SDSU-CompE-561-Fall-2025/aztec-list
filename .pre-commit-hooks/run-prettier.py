"""Run Prettier on frontend files."""
import shutil
import subprocess
import sys
from pathlib import Path

runner = "bunx" if shutil.which("bunx") else "npx"
frontend_dir = Path(__file__).parent.parent / "frontend"
files = [f.removeprefix("frontend/") for f in sys.argv[1:]]
sys.exit(subprocess.run([runner, "prettier", "--write", *files], cwd=frontend_dir).returncode)
