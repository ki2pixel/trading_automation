from __future__ import annotations

import os
from pathlib import Path

def get_reports_dir(repo_root: Path | str | None = None) -> Path:
    """Resolve the reports directory.

    If BACKTEST_REPORTS_DIR environment variable is set, it will be used as the absolute path.
    Otherwise, it defaults to {repo_root}/reports.
    """
    env_dir = os.environ.get("BACKTEST_REPORTS_DIR")
    if env_dir:
        return Path(env_dir).resolve()
    
    if repo_root is None:
        # Fallback to repository root (one level up from the backtest_engine directory)
        repo_root = Path(__file__).resolve().parents[1]
        
    return Path(repo_root).resolve() / "reports"
