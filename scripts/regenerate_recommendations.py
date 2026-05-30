#!/usr/bin/env python3
import argparse
import json
import logging
from pathlib import Path
import traceback
import sys

# Ensure backtest_engine can be imported
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backtest_engine.report_interpreter import write_optimization_recommendations, load_optimization_artifacts
from backtest_engine.reports import write_optimizer_reports

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("regenerate_recommendations")

def regenerate_job_directory(job_dir: Path, dry_run: bool = False) -> bool:
    try:
        # Load artifacts
        results, config = load_optimization_artifacts(job_dir)
        
        # Extract custom quantile/tolerance from config if present
        top_q = config.get("top_quantile")
        score_tol = config.get("score_tolerance_pct")
        
        logger.info(f"Regenerating job in {job_dir}")
        if top_q is not None or score_tol is not None:
            logger.info(f"  Using custom settings from config: top_quantile={top_q}, score_tolerance_pct={score_tol}")
        
        if dry_run:
            logger.info("  [Dry Run] Would call write_optimization_recommendations and write_optimizer_reports")
            return True
            
        # Write recommendations
        recommendations = write_optimization_recommendations(
            job_dir,
            results,
            config,
            top_quantile=top_q,
            score_tolerance_pct=score_tol
        )
        
        # Write optimizer reports
        write_optimizer_reports(job_dir, results, config, recommendations)
        logger.info("  Successfully regenerated recommendations.json and reports.")
        return True
    except Exception as e:
        logger.error(f"  Error regenerating job in {job_dir}: {e}")
        logger.debug(traceback.format_exc())
        return False

def main():
    parser = argparse.ArgumentParser(description="Batch regenerate recommendations and reports for existing optimization runs.")
    parser.add_argument(
        "--reports-dir",
        default="reports",
        help="Directory to scan recursively for optimization runs (default: reports)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Scan and show directories to regenerate without writing files"
    )
    args = parser.parse_args()
    
    reports_dir = Path(args.reports_dir).resolve()
    if not reports_dir.exists():
        logger.error(f"Reports directory does not exist: {reports_dir}")
        sys.exit(1)
        
    logger.info(f"Scanning '{reports_dir}' recursively for optimization runs...")
    
    # We look for folders containing BOTH results.json and optimization_config.json
    job_dirs = []
    for path in reports_dir.rglob("results.json"):
        parent_dir = path.parent
        config_path = parent_dir / "optimization_config.json"
        if config_path.exists():
            job_dirs.append(parent_dir)
            
    if not job_dirs:
        logger.info("No completed optimization jobs found.")
        sys.exit(0)
        
    logger.info(f"Found {len(job_dirs)} completed optimization job(s) to process.")
    
    success_count = 0
    failure_count = 0
    
    for idx, job_dir in enumerate(job_dirs, start=1):
        print(f"[{idx}/{len(job_dirs)}] Processing {job_dir.relative_to(reports_dir.parent)}")
        success = regenerate_job_directory(job_dir, dry_run=args.dry_run)
        if success:
            success_count += 1
        else:
            failure_count += 1
            
    logger.info("\n=== Regeneration Summary ===")
    logger.info(f"Processed: {len(job_dirs)}")
    logger.info(f"Success:   {success_count}")
    logger.info(f"Failure:   {failure_count}")
    
    if failure_count > 0:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()
