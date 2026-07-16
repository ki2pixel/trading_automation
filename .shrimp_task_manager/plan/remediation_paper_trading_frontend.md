# Specification Plan: Remediation Paper Trading Frontend

This specification lists the tasks required for the complete remediation of the Paper Trading frontend and backend linking layer, grouped by priority.

## Priority 1 (P1) — Security & Immediate Reliability

1. **Backend Authentication Endpoints (SEC-01)**:
   - Migrate authentication endpoints (`POST /api/login`, `GET /api/csrf-token`, and `/api/logout`) from `run_paper_trader.py` directly into the router in `backtest_engine/live/paper_trading/api.py`.
   - Update cookie flags: set session and CSRF cookies to `secure=True` (in production) and `samesite="strict"` (instead of "lax").
   - Import verify and signing helper functions in `run_paper_trader.py` from `api.py` to prevent code duplication and circular imports.

2. **Profit Factor NaN Fix (FIN-01)**:
   - Modify `backtest_engine/live/paper_trading/static/js/chart.js` to correctly display the profit factor `∞` when there are no losses (where `profit_factor` is returned as `null` or `undefined` by the backend).

3. **Chart Async Race Condition Guard (PERF-04)**:
   - Implement a sequence guard counter in `loadChart` inside `chart.js` to prevent asynchronous fetch interleaving when the operator switches between assets quickly.

4. **Configuration Cache Invalidation (FIN-02)**:
   - Add a `forceRefresh` flag to `fetchConfigs` in `app.js` and call it with `true` during polling, ensuring configuration states and market hours updates are regularly retrieved.

5. **Redis Failover Race Condition (PERF-01)**:
   - Secure the state transition variable `_is_failed_over` inside `backtest_engine/live/connection.py` using a mutual exclusion lock (`threading.Lock`).

6. **CSRF Token & Content-Security-Policy Security (SEC-03, SEC-07)**:
   - Restructure the fetch interceptor in `js/api.js` to ensure the `X-CSRFToken` header is only sent on same-origin mutating requests.
   - Refine the security headers to ensure robust Content-Security-Policy (CSP) coverage.
   - Handle 403 and 422 HTTP responses inside the fetch interceptor to show descriptive toasts instead of silent failures.

7. **Authentication Rate Limiting (SEC-02)**:
   - Configure a strict rate limiting threshold (e.g. maximum of 5 requests per 5 minutes per IP address) specifically for the `/api/login` endpoint in the rate limiting middleware.

8. **SSE Reconnection Feedback (PERF-03)**:
   - Implement an `onerror` and `onopen` listener on the `EventSource` object in `app.js` to alert the operator in case of SSE log stream failure/reconnection.

---

## Priority 2 (P2) — Accessibility & UI Standardisation

1. **Interactive Modals via Keyboard (ACC-01, ACC-02)**:
   - Replace generic close spans with semantic `<button type="button" class="close-modal">` tags inside `index.html`.
   - Add explicit `:focus-visible` styling outline rules in `style.css` for sliders and toggle switches.

2. **Accessible Heartbeat Component (ACC-03)**:
   - Enhance the connectivity heartbeat elements inside `index.html` with explicit descriptive `aria-label` properties so screen readers/users can understand status without relying purely on colors.

3. **Internationalisation & Currency Alignment (DT-05, DT-06)**:
   - Translate all remaining French strings to technical English.
   - Standardise currency display format (either using EUR `fr-FR` or USD/USDT `en-US` cleanly based on the asset type).

4. **Logout via POST Method (SEC-06)**:
   - Change the logout trigger in the frontend to execute an asynchronous `POST /api/logout` request with CSRF protection, instead of a GET request.

5. **URI Component Encoding (DT-03)**:
   - Wrap all query parameters (like asset tickers) inside `encodeURIComponent` calls in `js/api.js` to prevent URL injection/malformation issues.

6. **Outdated Financial Data Warning (FIN-05)**:
   - Implement visual warnings (reduced opacity and status text "Outdated") on UI sections when polling calls fail, avoiding displaying stale financial metrics.

---

## Priority 3 (P3) — Architecture & Refactoring

1. **Modular split of app.js (DT-08)**:
   - Deconstruct `app.js` into smaller modular ES6 ES modules:
     - `js/modules/dashboard.js`
     - `js/modules/configs.js`
     - `js/modules/logs.js`
   - Clean up dead variables and unused function imports.

2. **Active Tab Polling Optimization (PERF-06)**:
   - Stop polling intervals when the document is hidden (`document.hidden`), and trigger an immediate refresh when the user brings the page back to the foreground.

3. **Cursor-based Transactions Pagination (DT-07)**:
   - Implement cursor-based pagination using a `cursor_timestamp` parameter instead of SQL `LIMIT`/`OFFSET` to avoid skip/overlap drifts when concurrent transactions are written.

4. **Rationalise CSS variables (DT-02)**:
   - Extract inline CSS from `login.html` and move it to `style.css`, resolving color variable duplications.
