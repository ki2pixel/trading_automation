#!/usr/bin/env python3
"""CLI script to generate Plotly heatmaps from optimization results.

This script reads a JSON file containing optimization results (e.g. from
vectorized_exploration.py) and generates a 2D interactive Plotly heatmap.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

try:
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Plotly Heatmap from optimization results")
    parser.add_argument("--results-file", required=True, help="Path to JSON results file")
    parser.add_argument("--x", required=True, help="Parameter name for X axis (e.g., fast_window)")
    parser.add_argument("--y", required=True, help="Parameter name for Y axis (e.g., slow_window)")
    parser.add_argument("--z", default="total_return_pct", help="Metric name for Z axis/color (e.g., total_return_pct)")
    parser.add_argument("--output", default="heatmap.html", help="Output HTML file path")
    args = parser.parse_args()

    if not PLOTLY_AVAILABLE:
        print("Error: plotly is not installed. Please pip install plotly.")
        return 1

    results_path = Path(args.results_file)
    if not results_path.exists():
        print(f"Error: file not found: {results_path}")
        return 1

    with results_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not data:
        print("Error: JSON file is empty")
        return 1

    df = pd.DataFrame(data)

    if args.x not in df.columns or args.y not in df.columns or args.z not in df.columns:
        print(f"Error: Missing one of the required columns ({args.x}, {args.y}, {args.z}) in data.")
        print(f"Available columns: {list(df.columns)}")
        return 1

    # Pivot to create a 2D matrix
    pivot_df = df.pivot(index=args.y, columns=args.x, values=args.z)

    fig = px.imshow(
        pivot_df,
        labels=dict(x=args.x, y=args.y, color=args.z),
        title=f"Optimization Heatmap: {args.z}",
        aspect="auto"
    )
    
    out_path = Path(args.output)
    fig.write_html(str(out_path))
    print(f"Heatmap successfully written to {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
