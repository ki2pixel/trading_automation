from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
import sys
from typing import Iterable, Literal

import math
import pandas as pd

from .data import (
    BASE_TIMEFRAME_MINUTES,
    DataQualityReport,
    OHLC_COLUMNS,
    _raw_folder_name,
    _repair_ohlc_values,
    _is_valid_ohlc,
    _read_market_csvs,
    compute_time_gap_metrics,
    market_csv_files,
    normalize_market_frame,
    parse_numeric_cell,
)

OutputFormat = Literal["csv", "parquet"]


def _progress(message: str, verbose: bool = True) -> None:
    if verbose:
        print(message, file=sys.stderr, flush=True)


@dataclass
class CanonicalBuildItem:
    kind: str
    name: str
    rows: int
    output: str
    report: dict = field(default_factory=dict)


@dataclass
class CanonicalBuildSummary:
    output_dir: str
    items: list[CanonicalBuildItem] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "output_dir": self.output_dir,
            "warnings": self.warnings,
            "items": [asdict(item) for item in self.items],
        }


def list_market_symbols(repo_root: Path, timeframe_minutes: int | str = BASE_TIMEFRAME_MINUTES) -> list[str]:
    root = repo_root / "SheetsFinance_Export" / "market_data" / _raw_folder_name(timeframe_minutes)
    if not root.exists():
        return []
    return sorted(path.name for path in root.iterdir() if path.is_dir())


def list_fx_pairs(repo_root: Path, timeframe_minutes: int | str = BASE_TIMEFRAME_MINUTES) -> list[str]:
    root = repo_root / "SheetsFinance_Export" / "fx_data" / _raw_folder_name(timeframe_minutes)
    if not root.exists():
        return []
    return sorted(path.name for path in root.iterdir() if path.is_dir())


def _is_canonical_fx_file(path: Path) -> bool:
    parts = {part.lower() for part in path.parts}
    name = path.name.lower()
    # Exclude known collector artefacts/non-canonical folders such as
    # raw_5m or raw_1m/USDEUR/Char/USDEUR_5m_Chargem.csv which are not real monthly exports.
    if "char" in parts:
        return False
    if "chargem" in name:
        return False
    return True


def list_split_files(repo_root: Path) -> list[Path]:
    root = repo_root / "SheetsFinance_Export" / "corporate_actions" / "splits"
    return sorted(root.glob("*_splits.csv")) if root.exists() else []


def load_symbol_currency_map(repo_root: Path, timeframe_minutes: int | str = BASE_TIMEFRAME_MINUTES) -> dict[str, str]:
    if not hasattr(load_symbol_currency_map, "_cache"):
        load_symbol_currency_map._cache = {}
    _currency_map_cache = load_symbol_currency_map._cache
    cache_key = (str(repo_root), timeframe_minutes)
    if cache_key in _currency_map_cache:
        return _currency_map_cache[cache_key]
        
    path = repo_root / "SheetsFinance_Export" / "fx_data" / _raw_folder_name(timeframe_minutes) / "symbol_currency_map.csv"
    if not path.exists():
        _currency_map_cache[cache_key] = {}
        return {}
    df = pd.read_csv(path, dtype=str).fillna("")
    result = {row["symbol"]: row["currency"].upper() for _, row in df.iterrows() if row.get("symbol")}
    _currency_map_cache[cache_key] = result
    return result


def infer_market_divisor(symbol: str, raw: pd.DataFrame, currency_map: dict[str, str]) -> tuple[float, str]:
    """Infer a conservative global divisor for market prices.

    This is not meant to be magical. It encodes the current dataset reality:
    decimal separators were stripped, so many equity prices need a global scale.
    Explicit overrides remain preferable for production-grade reconstruction.
    """
    currency = currency_map.get(symbol, "")
    raw_close = raw["close"].map(parse_numeric_cell).dropna()
    median_close = float(raw_close.median()) if len(raw_close) else math.nan

    if currency == "USD":
        return 100.0, "currency_map: USD -> cents-style divisor 100"
    if currency in {"DKK", "SEK", "NOK"}:
        return 10.0, f"currency_map: {currency} -> one-decimal Nordic-style divisor 10"
    if symbol.endswith((".DE", ".MC", ".PA", ".AS", ".BR", ".MI")):
        return 100.0, "European exchange suffix -> cents-style divisor 100"
    if not math.isnan(median_close):
        if median_close >= 10000:
            return 100.0, "median raw close >= 10000 -> divisor 100"
        if median_close >= 1000:
            return 10.0, "median raw close >= 1000 -> divisor 10"
    return 1.0, "no divisor inferred"


def _write_frame(df: pd.DataFrame, path_without_suffix: Path, output_format: OutputFormat, warnings: list[str]) -> Path:
    path_without_suffix.parent.mkdir(parents=True, exist_ok=True)
    if output_format == "parquet":
        try:
            out = Path(str(path_without_suffix) + ".parquet")
            df.to_parquet(out)
            return out
        except Exception as exc:  # pragma: no cover - depends on optional engines
            warnings.append(f"Parquet indisponible ({exc}); fallback CSV gzip pour {path_without_suffix.name}")
    out = Path(str(path_without_suffix) + ".csv.gz")
    df.to_csv(out, compression="gzip")
    return out


def build_market_canonical(
    repo_root: Path,
    output_dir: Path,
    symbols: Iterable[str],
    price_repair: str = "auto",
    market_divisor: str = "auto",
    divisor_overrides: dict[str, float] | None = None,
    output_format: OutputFormat = "csv",
    max_files: int | None = None,
    max_rows: int | None = None,
    warnings: list[str] | None = None,
    verbose: bool = True,
    timeframe_minutes: int | str = BASE_TIMEFRAME_MINUTES,
) -> list[CanonicalBuildItem]:
    warnings = warnings if warnings is not None else []
    currency_map = load_symbol_currency_map(repo_root, timeframe_minutes)
    divisor_overrides = divisor_overrides or {}
    items: list[CanonicalBuildItem] = []

    for symbol in symbols:
        _progress(f"[market] {symbol}: reading raw CSV...", verbose)
        files = market_csv_files(repo_root, symbol, max_files=max_files, timeframe_minutes=timeframe_minutes)
        raw = _read_market_csvs(files, max_rows=max_rows)
        if raw.empty:
            warnings.append(f"Aucune donnée market pour {symbol}")
            continue

        if symbol in divisor_overrides:
            divisor = float(divisor_overrides[symbol])
            divisor_reason = "explicit override"
        elif market_divisor == "auto":
            divisor, divisor_reason = infer_market_divisor(symbol, raw, currency_map)
        else:
            divisor = float(market_divisor)
            divisor_reason = "CLI fixed divisor"

        _progress(f"[market] {symbol}: normalizing {len(raw)} rows with divisor={divisor} ({divisor_reason})...", verbose)
        frame, report = normalize_market_frame(raw, price_repair=price_repair, market_divisor=divisor)
        frame = frame[["symbol", "open", "high", "low", "close", "volume", "ohlc_repaired", "source_file"]]
        frame.attrs["market_divisor"] = divisor
        report_payload = report.to_dict()
        report_payload["market_divisor"] = divisor
        report_payload["market_divisor_reason"] = divisor_reason

        out = _write_frame(frame, output_dir / "market_data_5m" / symbol, output_format, warnings)
        report_path = output_dir / "quality_reports" / "market_data_5m" / f"{symbol}.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report_payload, indent=2, ensure_ascii=False), encoding="utf-8")
        items.append(CanonicalBuildItem("market", symbol, len(frame), str(out), report_payload))
        _progress(f"[market] {symbol}: wrote {len(frame)} rows -> {out}", verbose)
    return items


def parse_lost_decimal_fx(value: object) -> float:
    text = str(value).strip().replace(" ", "").replace("\u00a0", "")
    if text == "":
        return math.nan
    if "," in text or "." in text:
        return parse_numeric_cell(text)
    sign = -1.0 if text.startswith("-") else 1.0
    digits = text[1:] if text.startswith("-") else text
    if digits.startswith("0") and len(digits) > 1:
        return sign * (int(digits) / (10 ** (len(digits) - 1)))
    return parse_numeric_cell(text)


def repair_fx_continuity_(
    out: pd.DataFrame,
    pair_label: str | None = None,
    verbose: bool = True,
) -> pd.DataFrame:
    if out.empty:
        return out

    result = out.sort_values("timestamp").copy()
    closes = pd.to_numeric(result["close"], errors="coerce").replace([math.inf, -math.inf], math.nan).dropna()
    global_reference = float(closes[(closes > 0.05) & (closes < 10)].median()) if len(closes) else None
    if global_reference is None or math.isnan(global_reference):
        global_reference = float(closes.median()) if len(closes) else None
    previous_close = global_reference

    total_rows = len(result)
    repaired_flags: list[bool] = []
    repaired_counter = 0

    for row_number, row in enumerate(result.itertuples(index=True), start=1):
        idx = row.Index
        raw = {
            "open": float(row.open),
            "high": float(row.high),
            "low": float(row.low),
            "close": float(row.close),
        }

        needs_repair = not _is_valid_ohlc(raw)
        if not needs_repair and previous_close is not None and previous_close > 0:
            ratios = [max(v / previous_close, previous_close / v) for v in raw.values() if v > 0]
            max_ratio = max(ratios) if ratios else math.inf
            needs_repair = max_ratio > 5.0

        if needs_repair:
            values, repaired = _repair_ohlc_values(raw, reference_price=previous_close)
        else:
            values, repaired = raw, False

        for col in OHLC_COLUMNS:
            result.at[idx, col] = values[col]
        repaired_flags.append(repaired)
        repaired_counter += int(repaired)
        if _is_valid_ohlc(values) and values["close"] > 0:
            previous_close = values["close"]

        if verbose and row_number % 50000 == 0:
            label = pair_label or "FX"
            _progress(
                f"[fx] {label}: continuity pass {row_number}/{total_rows} rows, repaired={repaired_counter}",
                verbose,
            )

    result["ohlc_repaired"] = repaired_flags
    return result


def normalize_fx_frame(
    raw: pd.DataFrame,
    *,
    pair_label: str | None = None,
    verbose: bool = True,
) -> tuple[pd.DataFrame, DataQualityReport]:
    pair = str(raw["pair"].dropna().iloc[0]) if "pair" in raw and raw["pair"].notna().any() else "UNKNOWN"
    report = DataQualityReport(symbol=pair, files=raw["source_file"].nunique() if "source_file" in raw else 0, rows=len(raw))
    out = raw.copy()
    out.columns = [str(c).strip().lower() for c in out.columns]
    out["timestamp"] = pd.to_datetime(out["timestamp"], errors="coerce")
    report.invalid_timestamps = int(out["timestamp"].isna().sum())
    for col in OHLC_COLUMNS:
        out[col] = out[col].map(parse_lost_decimal_fx)
    out = repair_fx_continuity_(out, pair_label=pair_label or pair, verbose=verbose)
    report.invalid_numeric_cells = int(out[OHLC_COLUMNS].isna().sum().sum())
    valid_ohlc = out[OHLC_COLUMNS].apply(lambda row: _is_valid_ohlc(row.to_dict()), axis=1)
    report.invalid_ohlc_rows = int((~valid_ohlc).sum())
    report.repaired_ohlc_rows = int(out.get("ohlc_repaired", pd.Series(dtype=bool)).sum())
    examples = out.loc[~valid_ohlc, ["timestamp", *OHLC_COLUMNS, "source_file"]].head(10)
    report.examples = examples.assign(timestamp=examples["timestamp"].astype(str)).to_dict("records")
    out = out.dropna(subset=["timestamp", *OHLC_COLUMNS]).sort_values("timestamp")
    report.duplicate_timestamps = int(out["timestamp"].duplicated().sum())
    out = out.drop_duplicates(subset=["timestamp"], keep="last")
    if len(out):
        report.first_timestamp = str(out["timestamp"].iloc[0])
        report.last_timestamp = str(out["timestamp"].iloc[-1])
        report.gap_count, report.max_gap_minutes, report.gap_examples = compute_time_gap_metrics(out["timestamp"])
    return out.set_index("timestamp"), report


def build_fx_canonical(
    repo_root: Path,
    output_dir: Path,
    pairs: Iterable[str],
    output_format: OutputFormat = "csv",
    max_files: int | None = None,
    max_rows: int | None = None,
    warnings: list[str] | None = None,
    verbose: bool = True,
    timeframe_minutes: int | str = BASE_TIMEFRAME_MINUTES,
) -> list[CanonicalBuildItem]:
    warnings = warnings if warnings is not None else []
    root = repo_root / "SheetsFinance_Export" / "fx_data" / _raw_folder_name(timeframe_minutes)
    items: list[CanonicalBuildItem] = []
    for pair in pairs:
        _progress(f"[fx] {pair}: reading raw CSV...", verbose)
        files = sorted(path for path in (root / pair).glob("**/*.csv") if _is_canonical_fx_file(path))
        files = files[:max_files] if max_files else files
        raw = _read_market_csvs(files, max_rows=max_rows).rename(columns={"symbol": "pair"})
        if raw.empty:
            warnings.append(f"Aucune donnée FX pour {pair}")
            continue
        _progress(f"[fx] {pair}: normalizing {len(raw)} rows...", verbose)
        frame, report = normalize_fx_frame(raw, pair_label=pair, verbose=verbose)
        frame = frame[["pair", "open", "high", "low", "close", "ohlc_repaired", "source_file"]]
        out = _write_frame(frame, output_dir / "fx_data_5m" / pair, output_format, warnings)
        report_payload = report.to_dict()
        report_path = output_dir / "quality_reports" / "fx_data_5m" / f"{pair}.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report_payload, indent=2, ensure_ascii=False), encoding="utf-8")
        items.append(CanonicalBuildItem("fx", pair, len(frame), str(out), report_payload))
        _progress(f"[fx] {pair}: wrote {len(frame)} rows -> {out}", verbose)
    return items


def build_splits_canonical(
    repo_root: Path,
    output_dir: Path,
    output_format: OutputFormat = "csv",
    warnings: list[str] | None = None,
    verbose: bool = True,
) -> list[CanonicalBuildItem]:
    warnings = warnings if warnings is not None else []
    items: list[CanonicalBuildItem] = []
    for file in list_split_files(repo_root):
        symbol = file.name.replace("_splits.csv", "")
        _progress(f"[splits] {symbol}: normalizing...", verbose)
        df = pd.read_csv(file, dtype=str)
        if df.empty:
            frame = pd.DataFrame(columns=["symbol", "date", "numerator", "denominator", "ratio"])
        else:
            frame = df.copy()
            frame["date"] = pd.to_datetime(frame["date"], errors="coerce").dt.date.astype(str)
            for col in ["numerator", "denominator", "ratio"]:
                frame[col] = frame[col].map(parse_numeric_cell)
        out = _write_frame(frame, output_dir / "splits" / symbol, output_format, warnings)
        items.append(CanonicalBuildItem("splits", symbol, len(frame), str(out), {}))
        _progress(f"[splits] {symbol}: wrote {len(frame)} rows -> {out}", verbose)
    return items


def build_canonical_dataset(
    repo_root: Path,
    output_dir: Path,
    symbols: list[str] | None = None,
    fx_pairs: list[str] | None = None,
    include_market: bool = True,
    include_fx: bool = True,
    include_splits: bool = True,
    price_repair: str = "auto",
    market_divisor: str = "auto",
    divisor_overrides: dict[str, float] | None = None,
    output_format: OutputFormat = "csv",
    max_files: int | None = None,
    max_rows: int | None = None,
    verbose: bool = True,
    timeframe_minutes: int | str = BASE_TIMEFRAME_MINUTES,
) -> CanonicalBuildSummary:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = CanonicalBuildSummary(output_dir=str(output_dir))
    if include_market:
        selected_symbols = symbols or list_market_symbols(repo_root, timeframe_minutes)
        summary.items.extend(build_market_canonical(
            repo_root, output_dir, selected_symbols, price_repair=price_repair,
            market_divisor=market_divisor, divisor_overrides=divisor_overrides,
            output_format=output_format, max_files=max_files, max_rows=max_rows,
            warnings=summary.warnings, verbose=verbose,
            timeframe_minutes=timeframe_minutes,
        ))
    if include_fx:
        selected_pairs = fx_pairs or list_fx_pairs(repo_root, timeframe_minutes)
        summary.items.extend(build_fx_canonical(
            repo_root, output_dir, selected_pairs, output_format=output_format,
            max_files=max_files, max_rows=max_rows, warnings=summary.warnings,
            verbose=verbose,
            timeframe_minutes=timeframe_minutes,
        ))
    if include_splits:
        summary.items.extend(build_splits_canonical(
            repo_root, output_dir, output_format=output_format,
            warnings=summary.warnings, verbose=verbose,
        ))
    (output_dir / "build_summary.json").write_text(
        json.dumps(summary.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return summary
