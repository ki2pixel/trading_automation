### **Q1 — Target Market & Timeframe**
* **Recommendation**: **Daily Timeframe** with **Major Liquid Equities / FX Pairs** (e.g., `LOGI` or currency pairs).
* **Rationale**: 
  * Ehlers' cybernetic indicators and dominant cycle estimation are designed to identify macroeconomic or structural market cycles. 
  * Lower timeframes (like `5m` or `1m`) contain high levels of microstructure noise, bid-ask spread friction, and intraday seasonality which distort phase-crossover signals and trigger excessive false entries.
  * *Implementation Action*: The strategy will be designed dynamically to work on any dataset provided, but the default hyperparameter configurations and benchmarks will target the **Daily** timeframe.

---

### **Q2 — Hilbert Implementation**
* **Recommendation**: **Option B (John Ehlers' discrete FIR filter with Numba `@njit`)**.
* **Rationale**:
  * **Zero Look-ahead Bias (Causality)**: `scipy.signal.hilbert` uses an FFT-based global window which is non-causal (inherently uses future bars for past calculations). Running FFT on a rolling window introduces severe edge effects (Gibbs phenomenon) exactly at the latest bar ($t$), where trading decisions are made. Ehlers' difference FIR filter is strictly causal, relying on a fixed-coefficient historical lag (bar-by-bar).
  * **Computational Speed**: Ehlers' FIR filter can be fully compiled to LLVM using Numba `@njit(cache=True)`. This bypasses the Python interpreter and achieves native $O(1)$ runtime per step, avoiding the CPU bottleneck during deep WFA sweeps.

---

### **Q3 — JournalStorage Scope**
* **Recommendation**: **Option A (Apply `JournalFileStorage` globally when `workers > 1`)**.
* **Rationale**:
  * **Eliminating Locking Errors**: Under multi-processing optimizations (e.g., 24 workers), Optuna's default SQLite driver regularly encounters `"database is locked"` exceptions due to concurrent transactional write demands.
  * **Unified Architecture**: Incorporating `JournalFileStorage` (with symlink-based locking) globally for all parallel optimizations solves the concurrency limit for the entire codebase. This keeps the parallel optimization backend clean and uniform.

---

### **Q4 — Sampler Selection**
* **Recommendation**: **Option C (CLI flag `--sampler` supporting `tpe`/`cma_es`/`random` with strategic defaults)**.
* **Rationale**:
  * **Continuous Phase Space**: CMA-ES is highly optimized for continuous, smooth mathematical search spaces (like Hilbert's phase thresholds and smoothing coefficients). However, it does not handle discrete/categorical hyperparameters as efficiently as TPE.
  * **Strategic Flexibility**: Keeping `tpe` as the default for the existing strategies, defining `cma_es` as the default for the `cybernetic_hilbert` strategy config, and exposing a CLI `--sampler` flag provides optimal flexibility. This allows you to benchmark performance differences across samplers seamlessly.
