from __future__ import annotations

from dataclasses import asdict, dataclass, field
from itertools import product
from pathlib import Path
from typing import Callable, Iterable, Literal

import json
import math
from functools import lru_cache

import pandas as pd
import numpy as np

PriceRepairMode = Literal["none", "auto"]
CanonicalFormat = Literal["parquet", "csv"]

OHLC_COLUMNS = ["open", "high", "low", "close"]
SUPPORTED_TIMEFRAMES_MINUTES = {1, 5, 10, 15, 20, 30, 45, 60, 120, 240}
BASE_TIMEFRAME_MINUTES = 5


def validate_timeframe_minutes(timeframe_minutes: int | str = BASE_TIMEFRAME_MINUTES) -> int:
    """Validate a supported intraday timeframe expressed in minutes.

    Supported canonical resolutions: 1, 5, 10, 15, 20, 30, 45, 60, 120, 240 minutes.
    """
    if isinstance(timeframe_minutes, bool):
        raise ValueError("timeframe_minutes must be an integer")
    try:
        minutes = int(str(timeframe_minutes).strip())
    except (TypeError, ValueError) as exc:
        raise ValueError(f"timeframe_minutes must be a supported integer, got {timeframe_minutes!r}") from exc
    if minutes not in SUPPORTED_TIMEFRAMES_MINUTES:
        raise ValueError(f"timeframe_minutes must be one of {sorted(SUPPORTED_TIMEFRAMES_MINUTES)}, got {minutes}")
    return minutes


def _processed_root(repo_root: Path, processed_dir: str | Path) -> Path:
    root = Path(processed_dir)
    if not root.is_absolute():
        root = repo_root / root
    return root


def canonical_market_data_subdir(timeframe_minutes: int | str = BASE_TIMEFRAME_MINUTES) -> str:
    return f"market_data_{validate_timeframe_minutes(timeframe_minutes)}m"


def canonical_fx_data_subdir(timeframe_minutes: int | str = BASE_TIMEFRAME_MINUTES) -> str:
    return f"fx_data_{validate_timeframe_minutes(timeframe_minutes)}m"


def _parse_window_bound(value: str | pd.Timestamp | None, label: str) -> pd.Timestamp | None:
    if value in (None, ""):
        return None
    timestamp = pd.to_datetime(value, errors="coerce")
    if pd.isna(timestamp):
        raise ValueError(f"Invalid {label}: {value!r}")
    return pd.Timestamp(timestamp)


def filter_time_window(
    data: pd.DataFrame,
    start_date: str | pd.Timestamp | None = None,
    end_date: str | pd.Timestamp | None = None,
) -> pd.DataFrame:
    """Return rows whose DatetimeIndex falls within an optional inclusive window."""
    start = _parse_window_bound(start_date, "start_date")
    end = _parse_window_bound(end_date, "end_date")
    if start is None and end is None:
        return data
    if not isinstance(data.index, pd.DatetimeIndex):
        raise ValueError("Cannot filter a time window without a DatetimeIndex")
    if start is not None and end is not None and start > end:
        raise ValueError(f"start_date must be <= end_date, got {start} > {end}")

    mask = pd.Series(True, index=data.index)
    if start is not None:
        mask &= data.index >= start
    if end is not None:
        mask &= data.index <= end
    return data.loc[mask.to_numpy()]


@lru_cache(maxsize=1)
def _load_market_hours_config(repo_root: Path) -> dict[str, dict]:
    """Load market-hours JSON configuration once and cache it."""
    config_path = repo_root / "configs" / "market_hours.json"
    if not config_path.exists():
        return {}
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _parse_tz_offset(tz_offset: str) -> int:
    """Parse a fixed timezone offset string like '+01:00' or '-05:00' into minutes."""
    sign = 1 if tz_offset[0] == "+" else -1
    hours = int(tz_offset[1:3])
    minutes = int(tz_offset[4:6])
    return sign * (hours * 60 + minutes)


def filter_market_hours(
    data: pd.DataFrame,
    symbol: str,
    repo_root: Path,
) -> pd.DataFrame:
    """Keep only rows whose UTC timestamp falls within the exchange's local market hours.

    The DataFrame is expected to have a UTC-naive DatetimeIndex.  Timestamps are
    interpreted as UTC, shifted by the fixed offset declared in
    ``configs/market_hours.json`` (no DST handling), and then compared against the
    ``open``/``close`` local times for that symbol.

    If the symbol is absent from the configuration the DataFrame is returned
    unchanged.
    """
    if not isinstance(data.index, pd.DatetimeIndex):
        raise ValueError("Cannot filter market hours without a DatetimeIndex")

    config = _load_market_hours_config(repo_root)
    entry = config.get(symbol)
    if entry is None:
        return data

    open_time = entry.get("open")
    close_time = entry.get("close")
    tz_offset = entry.get("tz_offset")
    if not open_time or not close_time or not tz_offset:
        return data

    offset_minutes = _parse_tz_offset(tz_offset)

    # Localize as UTC then shift by the fixed offset to obtain local wall-clock time
    utc_index = data.index.tz_localize("UTC")
    local_index = utc_index + pd.Timedelta(minutes=offset_minutes)

    # Convert open/close strings to minutes-since-midnight for vector comparison
    open_ts = pd.Timestamp(f"2000-01-01 {open_time}")
    close_ts = pd.Timestamp(f"2000-01-01 {close_time}")
    open_mins = open_ts.hour * 60 + open_ts.minute
    close_mins = close_ts.hour * 60 + close_ts.minute

    local_mins = local_index.hour * 60 + local_index.minute
    mask = (local_mins >= open_mins) & (local_mins <= close_mins)
    return data.loc[mask]


@dataclass
class DataQualityReport:
    symbol: str
    files: int = 0
    rows: int = 0
    invalid_timestamps: int = 0
    invalid_numeric_cells: int = 0
    invalid_ohlc_rows: int = 0
    repairable_ohlc_rows: int = 0
    repaired_ohlc_rows: int = 0
    duplicate_timestamps: int = 0
    first_timestamp: str | None = None
    last_timestamp: str | None = None
    examples: list[dict] = field(default_factory=list)
    gap_count: int = 0
    max_gap_minutes: float = 0.0
    gap_examples: list[dict] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return self.invalid_timestamps + self.invalid_numeric_cells + self.invalid_ohlc_rows

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["error_count"] = self.error_count
        return payload


def _raw_folder_name(timeframe_minutes: int | str = BASE_TIMEFRAME_MINUTES) -> str:
    return f"raw_{validate_timeframe_minutes(timeframe_minutes)}m"


def market_data_dir(repo_root: Path, symbol: str, timeframe_minutes: int | str = BASE_TIMEFRAME_MINUTES) -> Path:
    return repo_root / "SheetsFinance_Export" / "market_data" / _raw_folder_name(timeframe_minutes) / symbol


def market_csv_files(repo_root: Path, symbol: str, max_files: int | None = None, timeframe_minutes: int | str = BASE_TIMEFRAME_MINUTES) -> list[Path]:
    root = market_data_dir(repo_root, symbol, timeframe_minutes)
    if not root.exists():
        raise FileNotFoundError(f"Market data directory not found: {root}")
    files = sorted(root.glob("**/*.csv"))
    return files[:max_files] if max_files else files


def canonical_market_data_path(
    repo_root: Path,
    symbol: str,
    processed_dir: str | Path = "storage/processed",
    timeframe_minutes: int | str = BASE_TIMEFRAME_MINUTES,
) -> tuple[Path, CanonicalFormat]:
    """Return the canonical market dataset path for a symbol.

    Parquet is the preferred production format. A gzip-compressed CSV fallback is
    supported because ``build-canonical`` can transparently fall back to it when
    no Parquet engine is installed.
    """
    minutes = validate_timeframe_minutes(timeframe_minutes)
    root = _processed_root(repo_root, processed_dir)
    for subdir_fn in (canonical_market_data_subdir, canonical_fx_data_subdir):
        base = root / subdir_fn(minutes) / symbol
        parquet_path = Path(str(base) + ".parquet")
        if parquet_path.exists():
            return parquet_path, "parquet"
        csv_path = Path(str(base) + ".csv.gz")
        if csv_path.exists():
            return csv_path, "csv"
    raise FileNotFoundError(
        f"Canonical market data not found for {symbol!r}. Looked for {parquet_path} and {csv_path}. "
        f"Requested timeframe: {minutes} minutes. "
        "Run `python -m backtest_engine build-canonical --format parquet --output-dir storage/processed` first."
    )


def canonical_market_data_path_with_fallback(
    repo_root: Path,
    symbol: str,
    processed_dir: str | Path = "storage/processed",
    timeframe_minutes: int | str = BASE_TIMEFRAME_MINUTES,
) -> tuple[Path, CanonicalFormat, int]:
    """Return the canonical market dataset path for a symbol, with fallback.

    Lookups are attempted in the following order:
    1. market_data_{minutes}m/ (and fx_data_{minutes}m/)
    2. If not found and minutes != 1, market_data_1m/
    3. If not found and minutes != 5, market_data_5m/
    """
    minutes = validate_timeframe_minutes(timeframe_minutes)

    # 1. Try minutes
    try:
        path, fmt = canonical_market_data_path(repo_root, symbol, processed_dir, minutes)
        return path, fmt, minutes
    except FileNotFoundError:
        pass

    # 2. Try 1m if minutes != 1
    if minutes != 1:
        try:
            path, fmt = canonical_market_data_path(repo_root, symbol, processed_dir, 1)
            return path, fmt, 1
        except FileNotFoundError:
            pass

    # 3. Try 5m if minutes != 5
    if minutes != 5:
        try:
            path, fmt = canonical_market_data_path(repo_root, symbol, processed_dir, 5)
            return path, fmt, 5
        except FileNotFoundError:
            pass

    # If all lookups failed, raise FileNotFoundError with a clear message
    raise FileNotFoundError(
        f"Canonical market data not found for {symbol!r} in any supported folders ({minutes}m, 1m, 5m)."
    )


class FastFXProvider:
    def __init__(self, series: pd.Series, is_inverse: bool):
        self.timestamps = series.index.values.view('i8')
        self.values = series.values.astype(float)
        self.is_inverse = is_inverse
        self.last_idx = 0
        self.n = len(self.timestamps)

    def __call__(self, currency: str, ts: object) -> float:
        try:
            if isinstance(ts, pd.Timestamp):
                dt64 = ts.value
            elif hasattr(ts, "value"):
                dt64 = ts.value
            else:
                dt64 = pd.Timestamp(ts).value
                
            idx = self.last_idx
            if idx >= self.n or self.timestamps[idx] > dt64:
                idx = 0
                
            while idx < self.n and self.timestamps[idx] <= dt64:
                idx += 1
                
            idx = max(0, idx - 1)
            self.last_idx = idx
            
            val = self.values[idx]
            if math.isclose(val, 0.0, abs_tol=1e-9) or math.isnan(val):
                return 1.0
            return val if self.is_inverse else 1.0 / val
        except Exception:
            return 1.0

def build_fx_rate_provider(
    repo_root: Path,
    symbol: str,
    account_currency: str = "EUR",
    processed_dir: str | Path = "storage/processed",
    timeframe_minutes: int | str = BASE_TIMEFRAME_MINUTES,
) -> Callable[[str, object], float] | None:
    """Build an FX rate provider for currency conversion during backtests.

    Returns a callable ``(currency, timestamp) -> rate`` where rate means:
    1 unit of the asset currency = ? units of account_currency.

    """
    if not hasattr(build_fx_rate_provider, "_cache"):
        build_fx_rate_provider._cache = {}
    _fx_provider_cache = build_fx_rate_provider._cache

    minutes = validate_timeframe_minutes(timeframe_minutes)
    cache_key = (symbol, account_currency, minutes)
    if cache_key in _fx_provider_cache:
        return _fx_provider_cache[cache_key]

    map_path = repo_root / "SheetsFinance_Export" / "fx_data" / "raw_5m" / "symbol_currency_map.csv"
    if not map_path.exists():
        _fx_provider_cache[cache_key] = None
        return None
        return None

    map_df = pd.read_csv(map_path, dtype=str)
    currency_map = {
        row["symbol"].strip(): row["currency"].strip().upper()
        for _, row in map_df.iterrows()
        if pd.notna(row.get("symbol")) and pd.notna(row.get("currency"))
    }

    asset_currency = currency_map.get(symbol, "").strip().upper()
    if not asset_currency or asset_currency == account_currency.upper():
        return None

    root = _processed_root(repo_root, processed_dir)

    # Direct pair: account_currency + asset_currency (e.g., EURUSD)
    # Data means 1 account = X asset, so 1 asset = 1/X account (inverse needed)
    direct_pair = f"{account_currency}{asset_currency}"
    found_direct_path = None
    for target_minutes in [minutes, 1, 5]:
        if target_minutes not in SUPPORTED_TIMEFRAMES_MINUTES:
            continue
        for subdir_fn in (canonical_fx_data_subdir, canonical_market_data_subdir):
            path = root / subdir_fn(target_minutes) / f"{direct_pair}.parquet"
            if path.exists():
                found_direct_path = path
                break
        if found_direct_path:
            break

    if found_direct_path:
        df = pd.read_parquet(found_direct_path)
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        series = df.dropna(subset=["timestamp"]).set_index("timestamp")["close"].sort_index()

        provider = FastFXProvider(series, is_inverse=False)
        _fx_provider_cache[cache_key] = provider
        return provider

    # Inverse pair: asset_currency + account_currency (e.g., USDEUR)
    # Data means 1 asset = X account, which is exactly what we want
    inverse_pair = f"{asset_currency}{account_currency}"
    found_inverse_path = None
    for target_minutes in [minutes, 1, 5]:
        if target_minutes not in SUPPORTED_TIMEFRAMES_MINUTES:
            continue
        for subdir_fn in (canonical_fx_data_subdir, canonical_market_data_subdir):
            path = root / subdir_fn(target_minutes) / f"{inverse_pair}.parquet"
            if path.exists():
                found_inverse_path = path
                break
        if found_inverse_path:
            break

    if found_inverse_path:
        df = pd.read_parquet(found_inverse_path)
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        series = df.dropna(subset=["timestamp"]).set_index("timestamp")["close"].sort_index()

        provider = FastFXProvider(series, is_inverse=True)
        _fx_provider_cache[cache_key] = provider
        return provider

    _fx_provider_cache[cache_key] = None
    return None


def _read_market_csvs(files: Iterable[Path], max_rows: int | None = None) -> pd.DataFrame:
    chunks: list[pd.DataFrame] = []
    remaining = max_rows
    for file in files:
        nrows = remaining if remaining is not None else None
        if nrows is not None and nrows <= 0:
            break
        chunk = pd.read_csv(file, dtype=str, nrows=nrows)
        chunk["source_file"] = str(file)
        chunks.append(chunk)
        if remaining is not None:
            remaining -= len(chunk)
    if not chunks:
        return pd.DataFrame(columns=["symbol", "timestamp", *OHLC_COLUMNS, "volume", "source_file"])
    return pd.concat(chunks, ignore_index=True)


def parse_numeric_cell(value: object) -> float:
    """Parse numbers from SheetsFinance CSVs without destroying decimal commas.

    The collector currently strips commas, which can corrupt values already
    exported with a comma decimal separator. This parser is conservative: it can
    parse correct future exports (`4310,5`, `4 310,5`, `4310.5`) but cannot by
    itself recover already-corrupted strings such as `43105`.
    """
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return math.nan
    text = str(value).strip().replace("\u00a0", "").replace(" ", "")
    if text == "":
        return math.nan
    if "," in text and "." not in text:
        text = text.replace(",", ".")
    elif "," in text and "." in text:
        # Handles common thousands/decimal cases: 4,310.5 or 4.310,5.
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    try:
        return float(text)
    except ValueError:
        return math.nan


def _is_valid_ohlc(values: dict[str, float]) -> bool:
    o, h, l, c = (values[col] for col in OHLC_COLUMNS)
    if any(math.isnan(v) for v in (o, h, l, c)):
        return False
    return l <= min(o, c) and h >= max(o, c) and l <= h


def _candidate_scales(value: float) -> list[tuple[float, int]]:
    if math.isnan(value) or value <= 0:
        return [(value, 0)]
    candidates: dict[float, int] = {float(value): 0}
    for power in range(1, 7):
        candidates[value / (10**power)] = power
    for power in range(1, 7):
        candidates[value * (10**power)] = -power
    return [(v, penalty) for v, penalty in candidates.items() if v > 0]


def compute_time_gap_metrics(index: pd.Index, expected_minutes: int = 5) -> tuple[int, float, list[dict]]:
    if not isinstance(index, pd.DatetimeIndex) or len(index) < 2:
        return 0, 0.0, []

    diffs = pd.Series(index).diff().dropna()
    gap_threshold = pd.Timedelta(minutes=expected_minutes)
    gaps = diffs[diffs > gap_threshold]
    if gaps.empty:
        return 0, 0.0, []

    examples: list[dict] = []
    for ts, delta in gaps.sort_values(ascending=False).head(10).items():
        prev_ts = ts - delta
        examples.append(
            {
                "previous_timestamp": str(prev_ts),
                "current_timestamp": str(ts),
                "gap_minutes": round(delta.total_seconds() / 60.0, 2),
            }
        )
    return int(len(gaps)), float(gaps.max().total_seconds() / 60.0), examples


def _best_scaled_value(value: float, reference_price: float | None) -> tuple[float, int]:
    if reference_price is None or reference_price <= 0 or math.isnan(value) or value <= 0:
        return value, 0

    best: tuple[float, float, int] | None = None
    for candidate, penalty in _candidate_scales(value):
        score = abs(math.log(max(candidate, 1e-12) / reference_price)) + 0.03 * abs(penalty)
        if best is None or score < best[0]:
            best = (score, candidate, penalty)
    return (best[1], best[2]) if best else (value, 0)


def _repair_ohlc_values(
    raw: dict[str, float],
    reference_price: float | None = None,
) -> tuple[dict[str, float], bool]:
    """Repair OHLC values by trying decimal shifts.

    The score favours:
      - internally coherent candles with narrow OHLC spread;
      - small decimal shifts;
      - continuity with a reference price when available.
    """
    if reference_price is not None and reference_price > 0:
        values: dict[str, float] = {}
        penalties: dict[str, int] = {}
        for col in OHLC_COLUMNS:
            values[col], penalties[col] = _best_scaled_value(raw[col], reference_price)

        if not _is_valid_ohlc(values):
            # If the individually best-scaled high/low still violates OHLC
            # ordering, preserve open/close and make high/low coherent. This
            # path is deliberately cheap because full datasets contain many
            # intraday rows.
            values["high"] = max(values.values())
            values["low"] = min(values.values())

        changed = any(
            abs(values[col] - raw[col]) > max(abs(raw[col]) * 1e-12, 1e-12)
            for col in OHLC_COLUMNS
        )
        return values, changed

    best: tuple[float, dict[str, float]] | None = None
    candidate_lists = [_candidate_scales(raw[col]) for col in OHLC_COLUMNS]
    for combo in product(*candidate_lists):
        values = dict(zip(OHLC_COLUMNS, [item[0] for item in combo]))
        if not _is_valid_ohlc(values):
            continue
        scale_penalty = sum(abs(item[1]) for item in combo)
        spread = max(values.values()) / max(min(values.values()), 1e-12)
        score = (0.05 * scale_penalty) + abs(math.log(spread))
        if reference_price is not None and reference_price > 0:
            mid_price = (values["open"] + values["high"] + values["low"] + values["close"]) / 4.0
            score += 2.0 * abs(math.log(max(mid_price, 1e-12) / reference_price))
        if best is None or score < best[0]:
            best = (score, values)
    if best is None:
        return raw, False
    changed = any(abs(best[1][col] - raw[col]) > max(abs(raw[col]) * 1e-12, 1e-12) for col in OHLC_COLUMNS)
    return best[1], changed


def repair_ohlc_row(
    row: pd.Series,
    base_divisor: float = 1.0,
    reference_price: float | None = None,
) -> tuple[dict[str, float], bool]:
    """Repair one OHLC row by trying decimal shifts that restore consistency.

    This is deliberately heuristic and should be considered a data rescue tool,
    not a substitute for fixing the collector. It is useful for diagnostics and
    exploratory POCs on already-exported files.
    """
    raw = {col: parse_numeric_cell(row[col]) / base_divisor for col in OHLC_COLUMNS}
    return _repair_ohlc_values(raw, reference_price=reference_price)


def repair_market_continuity_(out: pd.DataFrame) -> pd.DataFrame:
    """Second-pass continuity repair for already parsed OHLC columns.

    Some corrupted rows remain OHLC-valid after global scaling, e.g. a single
    high at 10x the neighbouring prices or an entire row at 1/100th scale. This
    pass uses the previous corrected close, falling back to the global median,
    to repair those cases.
    """
    if out.empty:
        return out

    result = out.sort_values("timestamp").copy()
    closes = pd.to_numeric(result["close"], errors="coerce").replace([math.inf, -math.inf], math.nan).dropna()
    global_reference = float(closes.median()) if len(closes) else None
    previous_close = global_reference

    for idx, row in result.iterrows():
        raw = {col: float(row[col]) for col in OHLC_COLUMNS}
        values, repaired = _repair_ohlc_values(raw, reference_price=previous_close)
        for col in OHLC_COLUMNS:
            result.at[idx, col] = values[col]
        result.at[idx, "ohlc_repaired"] = bool(row.get("ohlc_repaired", False)) or repaired
        if _is_valid_ohlc(values) and values["close"] > 0:
            previous_close = values["close"]

    return result


def normalize_market_frame(
    raw: pd.DataFrame,
    price_repair: PriceRepairMode = "none",
    market_divisor: float = 1.0,
) -> tuple[pd.DataFrame, DataQualityReport]:
    symbol = str(raw["symbol"].dropna().iloc[0]) if "symbol" in raw and raw["symbol"].notna().any() else "UNKNOWN"
    report = DataQualityReport(symbol=symbol, files=raw["source_file"].nunique() if "source_file" in raw else 0, rows=len(raw))

    out = raw.copy()
    out.columns = [str(c).strip().lower() for c in out.columns]
    out["timestamp"] = pd.to_datetime(out["timestamp"], errors="coerce")
    report.invalid_timestamps = int(out["timestamp"].isna().sum())

    repaired_flags: list[bool] = []
    parsed_rows: list[dict[str, float]] = []
    for _, row in out.iterrows():
        # First pass: apply only the global divisor. The continuity-aware repair
        # below is much faster and more reliable than a per-row combinatorial
        # repair without context.
        values = {col: parse_numeric_cell(row[col]) / market_divisor for col in OHLC_COLUMNS}
        repaired = False
        parsed_rows.append(values)
        repaired_flags.append(repaired)

    parsed = pd.DataFrame(parsed_rows, index=out.index)
    for col in OHLC_COLUMNS:
        out[col] = parsed[col]
    out["volume"] = out["volume"].map(parse_numeric_cell) if "volume" in out else math.nan
    out["ohlc_repaired"] = repaired_flags
    if price_repair == "auto":
        out = repair_market_continuity_(out)

    numeric_cols = OHLC_COLUMNS + ["volume"]
    report.invalid_numeric_cells = int(out[numeric_cols].isna().sum().sum())
    valid_ohlc = out[OHLC_COLUMNS].apply(lambda row: _is_valid_ohlc(row.to_dict()), axis=1)
    report.invalid_ohlc_rows = int((~valid_ohlc).sum())
    report.repaired_ohlc_rows = int(out["ohlc_repaired"].sum())

    if price_repair == "none":
        # Estimate how many invalid rows are likely repairable without mutating output.
        sample_invalid = out.loc[~valid_ohlc].head(500)
        report.repairable_ohlc_rows = sum(
            repair_ohlc_row(row, base_divisor=market_divisor)[1]
            for _, row in sample_invalid.iterrows()
        )
    else:
        report.repairable_ohlc_rows = report.repaired_ohlc_rows

    examples = out.loc[~valid_ohlc, ["timestamp", *OHLC_COLUMNS, "source_file"]].head(10)
    report.examples = examples.assign(timestamp=examples["timestamp"].astype(str)).to_dict("records")

    out = out.dropna(subset=["timestamp", *OHLC_COLUMNS]).sort_values("timestamp")
    report.duplicate_timestamps = int(out["timestamp"].duplicated().sum())
    out = out.drop_duplicates(subset=["timestamp"], keep="last")
    if len(out):
        report.first_timestamp = str(out["timestamp"].iloc[0])
        report.last_timestamp = str(out["timestamp"].iloc[-1])
        report.gap_count, report.max_gap_minutes, report.gap_examples = compute_time_gap_metrics(out["timestamp"])
    out = out.set_index("timestamp")
    return out, report


def load_market_data(
    symbol: str,
    repo_root: Path,
    price_repair: PriceRepairMode = "none",
    market_divisor: float = 1.0,
    max_files: int | None = None,
    max_rows: int | None = None,
    start_date: str | pd.Timestamp | None = None,
    end_date: str | pd.Timestamp | None = None,
) -> pd.DataFrame:
    files = market_csv_files(repo_root, symbol, max_files=max_files)
    raw = _read_market_csvs(files, max_rows=None if start_date or end_date else max_rows)
    if raw.empty:
        raise ValueError(f"No market data found for symbol {symbol!r}")
    data, report = normalize_market_frame(raw, price_repair=price_repair, market_divisor=market_divisor)
    if report.invalid_ohlc_rows:
        raise ValueError(
            f"{report.invalid_ohlc_rows} invalid OHLC rows remain for {symbol}. "
            "Run `python -m backtest_engine scan ...` or retry with `--price-repair auto`."
        )
    data = filter_time_window(data, start_date=start_date, end_date=end_date)
    if max_rows is not None:
        data = data.head(max_rows)
    return data


def get_canonical_market_data_date_bounds(
    symbol: str,
    repo_root: Path,
    processed_dir: str | Path = "storage/processed",
    timeframe_minutes: int | str = BASE_TIMEFRAME_MINUTES,
) -> tuple[str, str]:
    """Return the (min_date, max_date) ISO strings for a canonical dataset without loading all rows."""
    minutes = validate_timeframe_minutes(timeframe_minutes)
    path, fmt, loaded_minutes = canonical_market_data_path_with_fallback(
        repo_root, symbol, processed_dir=processed_dir, timeframe_minutes=minutes
    )

    if fmt == "parquet":
        try:
            df = pd.read_parquet(path, columns=["timestamp"])
            ts = pd.to_datetime(df["timestamp"])
        except (ValueError, KeyError):
            df = pd.read_parquet(path)
            if not isinstance(df.index, pd.DatetimeIndex):
                df.index = pd.to_datetime(df.index, errors="coerce")
            ts = df.index
    else:
        df = pd.read_csv(path, compression="gzip", usecols=["timestamp"])
        ts = pd.to_datetime(df["timestamp"])

    if ts.empty:
        raise ValueError(f"Canonical market data is empty for symbol {symbol!r}: {path}")

    min_date = pd.Timestamp(ts.min())
    max_date = pd.Timestamp(ts.max())
    return min_date.strftime("%Y-%m-%d"), max_date.strftime("%Y-%m-%d")


def load_canonical_market_data(
    symbol: str,
    repo_root: Path,
    processed_dir: str | Path = "storage/processed",
    max_rows: int | None = None,
    timeframe_minutes: int | str = BASE_TIMEFRAME_MINUTES,
    start_date: str | pd.Timestamp | None = None,
    end_date: str | pd.Timestamp | None = None,
    apply_market_hours: bool = True,
) -> pd.DataFrame:
    """Load cleaned canonical market data from ``storage/processed``.

    This is the production-oriented runner input. It deliberately bypasses the
    raw CSV parsing and repair heuristics used by ``load_market_data`` because
    the canonical builder has already normalized prices, deduplicated timestamps
    and generated quality reports. Timeframes above 5 minutes are loaded from a
    matching ``market_data_{N}m`` dataset when present, otherwise derived on the
    fly from ``market_data_5m`` or ``market_data_1m``.
    """
    minutes = validate_timeframe_minutes(timeframe_minutes)
    path, fmt, loaded_minutes = canonical_market_data_path_with_fallback(
        repo_root, symbol, processed_dir=processed_dir, timeframe_minutes=minutes
    )

    if fmt == "parquet":
        data = pd.read_parquet(path)
    else:
        data = pd.read_csv(path, compression="gzip")

    if data.empty:
        raise ValueError(f"Canonical market data is empty for symbol {symbol!r}: {path}")

    if not isinstance(data.index, pd.DatetimeIndex):
        if "timestamp" in data.columns:
            data["timestamp"] = pd.to_datetime(data["timestamp"], errors="coerce")
            data = data.set_index("timestamp")
        else:
            parsed_index = pd.to_datetime(data.index, errors="coerce")
            if parsed_index.isna().any():
                raise ValueError(f"Canonical data for {symbol!r} has no valid DatetimeIndex or timestamp column: {path}")
            data.index = parsed_index

    if data.index.isna().any():
        raise ValueError(f"Canonical data for {symbol!r} contains invalid timestamps: {path}")

    missing = [col for col in ["open", "high", "low", "close", "volume"] if col not in data.columns]
    if missing:
        raise ValueError(f"Canonical data for {symbol!r} is missing required columns {missing}: {path}")

    out = data.sort_index().copy()
    for col in ["open", "high", "low", "close", "volume"]:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    if out[OHLC_COLUMNS].isna().any().any():
        raise ValueError(f"Canonical data for {symbol!r} contains NaN OHLC values: {path}")

    # Vectorized validation check instead of slow row-by-row apply(axis=1)
    o = out["open"]
    h = out["high"]
    l = out["low"]
    c = out["close"]
    valid_ohlc = (l <= np.minimum(o, c)) & (h >= np.maximum(o, c)) & (l <= h)
    if (~valid_ohlc).any():
        raise ValueError(f"Canonical data for {symbol!r} contains {(~valid_ohlc).sum()} invalid OHLC rows: {path}")

    out = out[~out.index.duplicated(keep="last")]
    if loaded_minutes != minutes:
        out = resample_canonical_market_data(out, timeframe_minutes=minutes, base_minutes=loaded_minutes)
    out = filter_time_window(out, start_date=start_date, end_date=end_date)
    if apply_market_hours:
        out = filter_market_hours(out, symbol=symbol, repo_root=repo_root)
    if max_rows is not None:
        out = out.head(max_rows)
    return out


def resample_canonical_market_data(
    data: pd.DataFrame,
    timeframe_minutes: int | str,
    base_minutes: int | None = None,
) -> pd.DataFrame:
    """Aggregate canonical OHLCV bars from a base timeframe to a larger timeframe multiple."""
    minutes = validate_timeframe_minutes(timeframe_minutes)
    if base_minutes is not None:
        base = validate_timeframe_minutes(base_minutes)
        if base == minutes:
            return data.copy()
        if base > minutes:
            raise ValueError(f"Cannot resample from a larger timeframe ({base}m) to a smaller one ({minutes}m)")
    else:
        if minutes == BASE_TIMEFRAME_MINUTES:
            return data.copy()

    if not isinstance(data.index, pd.DatetimeIndex):
        raise ValueError("Canonical data must have a DatetimeIndex before resampling")

    required = ["open", "high", "low", "close", "volume"]
    missing = [col for col in required if col not in data.columns]
    if missing:
        raise ValueError(f"Cannot resample canonical data missing columns {missing}")

    aggregations: dict[str, str] = {
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "volume": "sum",
    }
    if "symbol" in data.columns:
        aggregations["symbol"] = "last"
    if "ohlc_repaired" in data.columns:
        aggregations["ohlc_repaired"] = "max"

    resampled = (
        data.sort_index()
        .resample(f"{minutes}min", label="left", closed="left")
        .agg(aggregations)
        .dropna(subset=OHLC_COLUMNS)
    )
    for col in required:
        resampled[col] = pd.to_numeric(resampled[col], errors="coerce")
    if resampled[OHLC_COLUMNS].isna().any().any():
        raise ValueError(f"Resampled canonical data contains NaN OHLC values for {minutes}m timeframe")
    valid_ohlc = resampled[OHLC_COLUMNS].apply(lambda row: _is_valid_ohlc(row.to_dict()), axis=1)
    if (~valid_ohlc).any():
        raise ValueError(f"Resampled canonical data contains {(~valid_ohlc).sum()} invalid OHLC rows for {minutes}m timeframe")
    return resampled


def scan_market_data(
    symbol: str,
    repo_root: Path,
    price_repair: PriceRepairMode = "none",
    market_divisor: float = 1.0,
    max_files: int | None = None,
    max_rows: int | None = None,
) -> DataQualityReport:
    files = market_csv_files(repo_root, symbol, max_files=max_files)
    raw = _read_market_csvs(files, max_rows=max_rows)
    _, report = normalize_market_frame(raw, price_repair=price_repair, market_divisor=market_divisor)
    return report

def split_wfo_windows(data: pd.DataFrame, windows: int, train_ratio: float) -> list[tuple[pd.DataFrame, pd.DataFrame]]:
    """Split a DataFrame into Walk-Forward Optimization (WFO) windows.
    
    Each window contains an In-Sample (IS) training set and an Out-of-Sample (OOS) testing set.
    The windows are strictly chronological and respect the train_ratio.
    """
    if windows <= 0:
        raise ValueError("Number of windows must be strictly positive")
    if not (0.0 < train_ratio < 1.0):
        raise ValueError("train_ratio must be between 0 and 1 (exclusive)")
    
    total_rows = len(data)
    if total_rows == 0:
        return []
        
    window_size = total_rows // windows
    if window_size == 0:
        raise ValueError("Not enough data to create the requested number of windows")
        
    wfo_windows = []
    for i in range(windows):
        start_idx = i * window_size
        end_idx = (i + 1) * window_size if i < windows - 1 else total_rows
        
        window_data = data.iloc[start_idx:end_idx]
        train_size = max(1, int(len(window_data) * train_ratio))
        
        train_data = window_data.iloc[:train_size]
        test_data = window_data.iloc[train_size:]
        
        wfo_windows.append((train_data, test_data))
        
    return wfo_windows
