from __future__ import annotations

import os
from pathlib import Path

def _parse_dotenv(repo_root: Path) -> dict[str, str]:
    """Parse the .env file locally and return a dict of key-value pairs."""
    env_vars = {}
    env_path = repo_root / ".env"
    if not env_path.is_file():
        return env_vars

    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip("\"'")
                    if key:
                        env_vars[key] = value
    except Exception:
        pass  # Silent failure for robust execution
    return env_vars

def get_reports_dir(repo_root: Path | str | None = None) -> Path:
    """Resolve the reports directory.

    If BACKTEST_REPORTS_DIR environment variable is set in the OS environment,
    it will be used as the absolute path. Otherwise, if defined in the local
    .env file, that value is used. Otherwise, it defaults to {repo_root}/reports.
    """
    if repo_root is None:
        # Fallback to repository root (one level up from the backtest_engine directory)
        repo_root = Path(__file__).resolve().parents[1]
    else:
        repo_root = Path(repo_root)

    # 1. Check OS environment first
    env_dir = os.environ.get("BACKTEST_REPORTS_DIR")
    if env_dir:
        return Path(env_dir).resolve()

    # 2. Check local .env file
    env_vars = _parse_dotenv(repo_root)
    env_dir = env_vars.get("BACKTEST_REPORTS_DIR")
    if env_dir:
        return Path(env_dir).resolve()

    # 3. Fallback default
    return repo_root.resolve() / "reports"

