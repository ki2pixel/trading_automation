const COLLECTOR = {
  CONFIG_SHEET: 'CONFIG',
  STAGING_SHEET: 'STAGING',
  CHECKPOINTS_SHEET: 'CHECKPOINTS',
  LOGS_SHEET: 'LOGS',
  ROOT_FOLDER_NAME: 'SheetsFinance_Export',
  SPLITS_SUBPATH: ['corporate_actions', 'splits'],

  DATE_FORMAT: 'yyyy-MM-dd',
  DATETIME_FORMAT: 'yyyy-MM-dd HH:mm:ss',
  DEFAULTS: {
    WATCHLIST: 'AAPL,MSFT',
    START_DATE: '2016-01-01',
    END_DATE: '2026-01-01',
    BARS_PERIOD: '5min',
    BARS_WINDOW_DAYS: '7',
    SPLITS_WINDOW_DAYS: '90',
    FX_WINDOW_DAYS: '7',
    BARS_METRICS: 'date&open&high&low&close&volume',
    SPLITS_METRICS: 'date&symbol&numerator&denominator&ratio',    
    FX_METRICS: 'date&open&high&low&close',
    TIME_SERIES_OPTIONS: 'NH',
    SPLITS_OPTIONS: 'NH',
    FX_OPTIONS: 'NH',
    TARGET_CURRENCIES: 'EUR,USD',
    FORMULA_ARG_SEPARATOR: 'AUTO',
    MAX_BARS_WINDOWS_PER_RUN: '6',
    MAX_SPLITS_WINDOWS_PER_RUN: '4',
    MAX_FX_WINDOWS_PER_RUN: '6',
    WAIT_TIMEOUT_SECONDS: '120',
    POLL_INTERVAL_MS: '2000',
    RESPECTFUL_PAUSE_MS: '3000',
    ROOT_FOLDER_NAME: 'SheetsFinance_Export',
    MAX_RETRIES_PER_BATCH: '2',
    RETRY_BACKOFF_MS: '5000',
    AUTO_RELAUNCH_DELAY_MINUTES: '8',
    AUTO_NEXT_CYCLE_DELAY_SECONDS: '30',
    BUSY_RETRY_DELAY_SECONDS: '120',
    EXECUTION_TIME_LIMIT_SECONDS: '330',
    MIN_TIME_REMAINING_SECONDS: 180
  }
};

function getRawSubpath_(period) {
  const p = (period || '5min').trim();
  return ['market_data', 'raw_' + p.replace('min','m').replace('hour','h')];
}

function getFxSubpath_(period) {
  const p = (period || '5min').trim();
  return ['fx_data', 'raw_' + p.replace('min','m').replace('hour','h')];
}

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('SF Collector')
    .addItem('1. Setup collector workbook', 'setupCollectorWorkbook')
    .addSeparator()
    .addItem('Run bars batch', 'runBarsBatch')
    .addItem('Run splits batch', 'runSplitsBatch')
    .addItem('Run FX batch', 'runFxBatch')
    .addItem('Run bars + splits + FX batch', 'runAllBatch')
    .addItem('Resume until complete (timed loop)', 'resumeUntilComplete')
    .addSeparator()
    .addItem('Clear staging', 'clearStaging')
    .addItem('Show status summary', 'showStatusSummary')
    .addSeparator()
    .addItem('Start auto collector', 'startAutoCollector')
    .addItem('Stop auto collector', 'stopAutoCollector')
    .addItem('Run next collector cycle now', 'collectorSupervisor')
    .addToUi();    
}

function setupCollectorWorkbook() {
  const ss = getCollectorSpreadsheet_();
  const config = ensureSheet_(ss, COLLECTOR.CONFIG_SHEET);
  const staging = ensureSheet_(ss, COLLECTOR.STAGING_SHEET);
  const checkpoints = ensureSheet_(ss, COLLECTOR.CHECKPOINTS_SHEET);
  const logs = ensureSheet_(ss, COLLECTOR.LOGS_SHEET);

  setupConfigSheet_(config);
  setupStagingSheet_(staging);
  setupCheckpointsSheet_(checkpoints);
  setupLogsSheet_(logs);

  const cfg = readConfig_();
  ensureDriveFolders_(cfg);

  SpreadsheetApp.getUi().alert('Collector workbook prêt. Vérifiez la feuille CONFIG, puis lancez un batch.');
}

function runAllBatch() {
  runBarsBatch();
  runSplitsBatch();
  runFxBatch();
}

function runBarsBatch() {
  withCollectorLock_(() => runBarsBatchCore_());
}

function runBarsBatchCore_(deadlineMs) {
    const cfg = readConfig_();
    const ss = getCollectorSpreadsheet_();
    const staging = ss.getSheetByName(COLLECTOR.STAGING_SHEET);
    const checkpointsSheet = ss.getSheetByName(COLLECTOR.CHECKPOINTS_SHEET);
    const maxWindows = parseInt(cfg.MAX_BARS_WINDOWS_PER_RUN, 10);
    const pauseMs = parseInt(cfg.RESPECTFUL_PAUSE_MS, 10);
    const windowDays = parseInt(cfg.BARS_WINDOW_DAYS, 10);
    const endDate = parseDate_(cfg.END_DATE);
    const root = ensureDriveFolders_(cfg);
    const watchlist = getWatchlist_(cfg);
    const minRemainingMs = getMinTimeRemainingMs_(cfg);

    validateBarsConfig_(cfg, watchlist, maxWindows);
    toast_(`Bars batch start: ${watchlist.join(', ')} | max windows=${maxWindows}`);

    let processed = 0;
    for (const symbol of watchlist) {
      if (processed >= maxWindows) break;

      let cp = getCheckpoint_(checkpointsSheet, 'bars', symbol);
      let nextStart = cp && cp.next_start ? parseDate_(cp.next_start) : parseDate_(cfg.START_DATE);

      while (processed < maxWindows && nextStart <= endDate) {
        if (shouldStopForTimeBudget_(deadlineMs, minRemainingMs)) {
          Logger.log(`Bars batch stops before next window to preserve execution budget. Processed=${processed}`);
          return;
        }

        const chunkEnd = minDate_(addDays_(nextStart, windowDays - 1), endDate);
        const formula = buildBarsFormula_(symbol, nextStart, chunkEnd, cfg);

        clearStaging_();
        writeFormulaToStaging_(staging, formula, 6);
        toast_(`Bars request: ${symbol} ${fmtDate_(nextStart)} → ${fmtDate_(chunkEnd)}`);

        let rows = [];
        let status = 'OK';
        let message = '';
        try {
          rows = waitForStagingRows_(staging, 6, parseInt(cfg.WAIT_TIMEOUT_SECONDS, 10), parseInt(cfg.POLL_INTERVAL_MS, 10));
          const normalizedRows = normalizeBarsRows_(rows, symbol);
          appendBarsRowsToDrive_(root, symbol, normalizedRows);
          message = `Bars saved: ${normalizedRows.length}`;
        } catch (err) {
          message = String(err && err.message ? err.message : err);
          if (isNoDataError_(err)) {
            status = 'OK';
            message = 'Bars saved: 0 (no data)';
            rows = [];
          } else {
            status = 'ERROR';
            logRun_(symbol, 'bars', nextStart, chunkEnd, 0, status, message);
            setCheckpoint_(checkpointsSheet, 'bars', symbol, nextStart, chunkEnd, 'ERROR', message);
            toast_(`Bars error: ${symbol} ${message}`);
            throw err;
          }
        }

        logRun_(symbol, 'bars', nextStart, chunkEnd, rows.length, status, message);
        const nextChunkStart = addDays_(chunkEnd, 1);
        setCheckpoint_(checkpointsSheet, 'bars', symbol, nextChunkStart, chunkEnd, 'DONE', message);
        processed += 1;
        nextStart = nextChunkStart;

        Utilities.sleep(pauseMs);
      }
    }

    if (processed === 0) {
      toast_('Bars batch: aucune fenêtre traitée. Vérifiez CONFIG et CHECKPOINTS.');
    } else {
      toast_(`Bars batch terminé. Fenêtres traitées: ${processed}`);
    }
}

function runSplitsBatch() {
  withCollectorLock_(() => runSplitsBatchCore_());
}

function runSplitsBatchCore_(deadlineMs) {
    const cfg = readConfig_();
    const ss = getCollectorSpreadsheet_();
    const staging = ss.getSheetByName(COLLECTOR.STAGING_SHEET);
    const checkpointsSheet = ss.getSheetByName(COLLECTOR.CHECKPOINTS_SHEET);
    const maxWindows = parseInt(cfg.MAX_SPLITS_WINDOWS_PER_RUN, 10);
    const pauseMs = parseInt(cfg.RESPECTFUL_PAUSE_MS, 10);
    const windowDays = parseInt(cfg.SPLITS_WINDOW_DAYS, 10);
    const endDate = parseDate_(cfg.END_DATE);
    const root = ensureDriveFolders_(cfg);
    const watchlist = getWatchlist_(cfg);
    const minRemainingMs = getMinTimeRemainingMs_(cfg);

    if (!watchlist.length) throw new Error('WATCHLIST vide dans CONFIG.');
    if (!cfg.START_DATE || !cfg.END_DATE) throw new Error('START_DATE ou END_DATE manquant dans CONFIG.');
    if (parseDate_(cfg.START_DATE) > parseDate_(cfg.END_DATE)) throw new Error('START_DATE est postérieur à END_DATE.');
    if (!Number.isFinite(maxWindows) || maxWindows <= 0) throw new Error('MAX_SPLITS_WINDOWS_PER_RUN doit être > 0.');

    toast_(`Splits batch start: ${watchlist.join(', ')} | max windows=${maxWindows}`);

    let processed = 0;

    for (const symbol of watchlist) {
      if (processed >= maxWindows) break;

      const cp = getCheckpoint_(checkpointsSheet, 'splits', symbol);
      let nextStart = cp && cp.next_start ? parseDate_(cp.next_start) : parseDate_(cfg.START_DATE);

      while (processed < maxWindows && nextStart <= endDate) {
        if (shouldStopForTimeBudget_(deadlineMs, minRemainingMs)) {
          Logger.log(`Splits batch stops before next window to preserve execution budget. Processed=${processed}`);
          return;
        }

        const chunkEnd = minDate_(addDays_(nextStart, windowDays - 1), endDate);
        const formula = buildSplitsFormula_(symbol, nextStart, chunkEnd, cfg);

        clearStaging_();
        writeFormulaToStaging_(staging, formula, 5);
        toast_(`Splits request: ${symbol} ${fmtDate_(nextStart)} → ${fmtDate_(chunkEnd)}`);

        let rows = [];
        let status = 'OK';
        let message = '';

        try {
          rows = waitForStagingRowsAllowEmpty_(
            staging,
            5,
            parseInt(cfg.WAIT_TIMEOUT_SECONDS, 10),
            parseInt(cfg.POLL_INTERVAL_MS, 10)
          );

          const normalizedRows = normalizeSplitsRows_(rows, symbol);
          appendSplitsRowsToDrive_(root, symbol, normalizedRows);
          message = `Splits saved: ${normalizedRows.length}`;

        } catch (err) {
          const display = staging.getRange('A1').getDisplayValue() || '';
          const rawMessage = String(err && err.message ? err.message : err || '');

          Logger.log(`Splits catch | symbol=${symbol} | display=${display} | err=${rawMessage}`);

          // SheetsFinance renvoie souvent #ERROR! quand il n'y a aucun split sur la période.
          // Pour les splits, on normalise ce cas en 0 ligne au lieu d'un échec bloquant.
          if (display === '#ERROR!' || rawMessage.includes('Erreur SheetsFinance: #ERROR!')) {
            rows = [];
            appendSplitsRowsToDrive_(root, symbol, []);
            status = 'OK';
            message = 'Splits saved: 0 (no split events)';
          } else {
            status = 'ERROR';
            message = rawMessage;
            logRun_(symbol, 'splits', nextStart, chunkEnd, 0, status, message);
            setCheckpoint_(checkpointsSheet, 'splits', symbol, nextStart, chunkEnd, 'ERROR', message);
            toast_(`Splits error: ${symbol} ${message}`);
            throw err;
          }
        }

        logRun_(symbol, 'splits', nextStart, chunkEnd, rows.length, status, message);

        const nextChunkStart = addDays_(chunkEnd, 1);
        setCheckpoint_(checkpointsSheet, 'splits', symbol, nextChunkStart, chunkEnd, 'DONE', message);

        processed += 1;
        nextStart = nextChunkStart;

        Utilities.sleep(pauseMs);
      }
    }

    if (processed === 0) {
      toast_('Splits batch: aucune fenêtre traitée. Vérifiez CONFIG et CHECKPOINTS.');
    } else {
      toast_(`Splits batch terminé. Fenêtres traitées: ${processed}`);
    }
}

function runFxBatch() {
  withCollectorLock_(() => {
    const cfg = readConfig_();
    const deadlineMs = getExecutionDeadlineMs_(cfg);
    runFxBatchCore_(deadlineMs, true);
    if (!isTaskComplete_('fx')) {
      toast_('FX batch interrompu (timeout). Relancez Run FX batch pour reprendre.');
    }
  });
}

function runFxBatchCore_(deadlineMs, opt_ignoreMaxWindows) {
    const cfg = readConfig_();
    const ss = getCollectorSpreadsheet_();
    const staging = ss.getSheetByName(COLLECTOR.STAGING_SHEET);
    const checkpointsSheet = ss.getSheetByName(COLLECTOR.CHECKPOINTS_SHEET);
    const maxWindows = parseInt(cfg.MAX_FX_WINDOWS_PER_RUN, 10);
    const effectiveMaxWindows = opt_ignoreMaxWindows ? Infinity : maxWindows;
    const pauseMs = parseInt(cfg.RESPECTFUL_PAUSE_MS, 10);
    const windowDays = parseInt(cfg.FX_WINDOW_DAYS || cfg.BARS_WINDOW_DAYS, 10);
    const endDate = parseDate_(cfg.END_DATE);
    const root = ensureDriveFolders_(cfg);
    const watchlist = getWatchlist_(cfg);
    const targetCurrencies = getTargetCurrencies_(cfg);
    const minRemainingMs = getMinTimeRemainingMs_(cfg);

    validateFxConfig_(cfg, watchlist, targetCurrencies, maxWindows, windowDays);

    if (!targetCurrencies.length) {
      saveFxPairs_(cfg, []);
      toast_('FX batch ignoré: TARGET_CURRENCIES vide.');
      return;
    }

    const windowsLabel = opt_ignoreMaxWindows ? 'unlimited' : maxWindows;
    toast_(`FX batch start: targets=${targetCurrencies.join(', ')} | max windows=${windowsLabel}`);

    const symbolCurrencyMap = getSymbolCurrencyMap_(staging, watchlist, cfg, pauseMs);
    writeSymbolCurrencyMapToDrive_(root, symbolCurrencyMap);

    const pairs = buildFxPairsFromCurrencyMap_(symbolCurrencyMap, targetCurrencies);
    saveFxPairs_(cfg, pairs.map(pairInfo => pairInfo.pair));

    if (!pairs.length) {
      toast_('FX batch: aucune paire à collecter (devises source = devises cibles).');
      return;
    }

    let processed = 0;

    for (const pairInfo of pairs) {
      if (processed >= effectiveMaxWindows) break;

      if (shouldStopForTimeBudget_(deadlineMs, minRemainingMs)) {
        Logger.log(`FX batch stops before next pair to preserve execution budget. Processed=${processed}`);
        return;
      }

      const pair = pairInfo.pair;
      const cp = getCheckpoint_(checkpointsSheet, 'fx', pair);
      let nextStart = cp && cp.next_start ? parseDate_(cp.next_start) : parseDate_(cfg.START_DATE);

      while (processed < effectiveMaxWindows && nextStart <= endDate) {
        if (shouldStopForTimeBudget_(deadlineMs, minRemainingMs)) {
          Logger.log(`FX batch stops before next window to preserve execution budget. Processed=${processed}`);
          return;
        }

        const chunkEnd = minDate_(addDays_(nextStart, windowDays - 1), endDate);

        let rows = [];
        let normalizedRows = [];
        let status = 'OK';
        let message = '';

        try {
          try {
            const formula = buildFxFormula_(pairInfo.directPair, nextStart, chunkEnd, cfg);
            clearStaging_();
            writeFormulaToStaging_(staging, formula, 5);
            toast_(`FX request: ${pairInfo.directPair} ${fmtDate_(nextStart)} → ${fmtDate_(chunkEnd)}`);

            rows = waitForStagingRows_(
              staging,
              5,
              parseInt(cfg.WAIT_TIMEOUT_SECONDS, 10),
              parseInt(cfg.POLL_INTERVAL_MS, 10)
            );
            normalizedRows = normalizeFxRows_(rows, pair, false);
            message = `FX saved: ${normalizedRows.length}`;
          } catch (directErr) {
            if (isNoDataError_(directErr)) {
              throw directErr;
            }

            const inverseFormula = buildFxFormula_(pairInfo.inversePair, nextStart, chunkEnd, cfg);
            clearStaging_();
            writeFormulaToStaging_(staging, inverseFormula, 5);
            toast_(`FX fallback inverse: ${pairInfo.inversePair} ${fmtDate_(nextStart)} → ${fmtDate_(chunkEnd)}`);

            rows = waitForStagingRows_(
              staging,
              5,
              parseInt(cfg.WAIT_TIMEOUT_SECONDS, 10),
              parseInt(cfg.POLL_INTERVAL_MS, 10)
            );
            normalizedRows = normalizeFxRows_(rows, pair, true);
            message = `FX saved: ${normalizedRows.length} (from inverse ${pairInfo.inversePair})`;
          }

          appendFxRowsToDrive_(root, pair, normalizedRows);
        } catch (err) {
          message = String(err && err.message ? err.message : err);
          if (isNoDataError_(err)) {
            status = 'OK';
            message = `FX saved: 0 (no data)`;
            rows = [];
          } else {
            status = 'ERROR';
            logRun_(pair, 'fx', nextStart, chunkEnd, 0, status, message);
            setCheckpoint_(checkpointsSheet, 'fx', pair, nextStart, chunkEnd, 'ERROR', message);
            toast_(`FX error: ${pair} ${message}`);
            throw err;
          }
        }

        logRun_(pair, 'fx', nextStart, chunkEnd, rows.length, status, message);
        const nextChunkStart = addDays_(chunkEnd, 1);
        setCheckpoint_(checkpointsSheet, 'fx', pair, nextChunkStart, chunkEnd, 'DONE', message);

        processed += 1;
        nextStart = nextChunkStart;

        Utilities.sleep(pauseMs);
      }
    }

    if (processed === 0) {
      toast_('FX batch: aucune fenêtre traitée. Vérifiez CONFIG et CHECKPOINTS.');
    } else {
      toast_(`FX batch terminé. Fenêtres traitées: ${processed}`);
    }
}

function resumeUntilComplete() {
  startAutoCollector();
}

function clearStaging() {
  clearStaging_();
}

function showStatusSummary() {
  const snapshot = getCompletionSnapshot_();
  const lines = [];
  for (const [key, value] of Object.entries(snapshot)) {
    lines.push(`${key}: ${value}`);
  }
  SpreadsheetApp.getUi().alert(lines.join('\n'));
}

function debugFirstBarsWindow() {
  const cfg = readConfig_();
  const watchlist = getWatchlist_(cfg);
  validateBarsConfig_(cfg, watchlist, 1);

  const symbol = watchlist[0];
  const startDate = parseDate_(cfg.START_DATE);
  const endDate = minDate_(addDays_(startDate, parseInt(cfg.BARS_WINDOW_DAYS, 10) - 1), parseDate_(cfg.END_DATE));

  const ss = getCollectorSpreadsheet_();
  const staging = ss.getSheetByName(COLLECTOR.STAGING_SHEET);
  const formula = buildBarsFormula_(symbol, startDate, endDate, cfg);

  clearStaging_();
  writeFormulaToStaging_(staging, formula, 6);
  toast_(`Debug bars formula injectée pour ${symbol}`);

  Utilities.sleep(8000);
  SpreadsheetApp.flush();

  const a1Formula = staging.getRange('A1').getFormula();
  const a1Display = staging.getRange('A1').getDisplayValue();
  const lastRow = staging.getLastRow();
  const lastCol = staging.getLastColumn();

  Logger.log('Debug STAGING');
  Logger.log('Formula: ' + a1Formula);
  Logger.log('A1 display: ' + a1Display);
  Logger.log('lastRow=' + lastRow + ' lastCol=' + lastCol);
}

function buildBarsFormula_(symbol, startDate, endDate, cfg) {
  const sep = getFormulaArgSeparator_(cfg);

  return [
    '=SF_TIMESERIES(',
    quoteFormulaArg_(symbol), sep,
    quoteFormulaArg_(fmtDate_(startDate)), sep,
    quoteFormulaArg_(fmtDate_(endDate)), sep,
    quoteFormulaArg_(cfg.BARS_PERIOD), sep,
    quoteFormulaArg_(cfg.BARS_METRICS), sep,
    quoteFormulaArg_(cfg.TIME_SERIES_OPTIONS),
    ')'
  ].join('');
}

function buildSplitsFormula_(symbol, startDate, endDate, cfg) {
  const sep = getFormulaArgSeparator_(cfg);

  return [
    '=SF_CALENDAR(',
    quoteFormulaArg_(`$${symbol}`), sep,
    quoteFormulaArg_('splits'), sep,
    quoteFormulaArg_(fmtDate_(startDate)), sep,
    quoteFormulaArg_(fmtDate_(endDate)), sep,
    quoteFormulaArg_(cfg.SPLITS_METRICS), sep,
    quoteFormulaArg_(cfg.SPLITS_OPTIONS),
    ')'
  ].join('');
}

function buildFxFormula_(pair, startDate, endDate, cfg) {
  const sep = getFormulaArgSeparator_(cfg);

  return [
    '=SF_TIMESERIES(',
    quoteFormulaArg_(pair), sep,
    quoteFormulaArg_(fmtDate_(startDate)), sep,
    quoteFormulaArg_(fmtDate_(endDate)), sep,
    quoteFormulaArg_(cfg.BARS_PERIOD), sep,
    quoteFormulaArg_(cfg.FX_METRICS || COLLECTOR.DEFAULTS.FX_METRICS), sep,
    quoteFormulaArg_(cfg.FX_OPTIONS || cfg.TIME_SERIES_OPTIONS || COLLECTOR.DEFAULTS.FX_OPTIONS),
    ')'
  ].join('');
}

function buildCurrencyFormula_(symbol, cfg) {
  const sep = getFormulaArgSeparator_(cfg);

  return [
    '=SF(',
    quoteFormulaArg_(symbol), sep,
    quoteFormulaArg_('companyInfo'), sep,
    quoteFormulaArg_('currency'), sep,
    quoteFormulaArg_(''), sep,
    quoteFormulaArg_('NH'),
    ')'
  ].join('');
}

function assertSheetsFinanceAvailable_(cfg) {
  const watchlist = getWatchlist_(cfg);
  const symbol = watchlist[0] || 'AAPL';
  const ss = getCollectorSpreadsheet_();
  const staging = ss.getSheetByName(COLLECTOR.STAGING_SHEET);
  if (!staging) throw new Error('La feuille STAGING est introuvable.');

  const probeFormula = buildCurrencyFormula_(symbol, cfg);
  clearStaging_();
  writeFormulaToStaging_(staging, probeFormula, 1);

  try {
    waitForStagingRows_(staging, 1, 20, Math.min(parseInt(cfg.POLL_INTERVAL_MS, 10) || 2000, 2000));
  } catch (err) {
    if (isSheetsFinanceFunctionUnavailableError_(err)) {
      throw new Error(`SheetsFinance indisponible dans ce classeur/ce trigger: ${err.message || err}`);
    }
    throw err;
  }
}

function writeFormulaToStaging_(sheet, formula, expectedCols) {
  sheet.getRange('A1').setFormula(formula);
  SpreadsheetApp.flush();
  if (expectedCols > 0) {
    sheet.getRange(1, 1, sheet.getMaxRows(), expectedCols).setNumberFormat('0.############');
    sheet.getRange(1, 1, sheet.getMaxRows(), 1).setNumberFormat(COLLECTOR.DATETIME_FORMAT);
  }
}

function waitForStagingRows_(sheet, expectedCols, timeoutSeconds, pollMs) {
  const rows = waitForStagingRowsAllowEmpty_(sheet, expectedCols, timeoutSeconds, pollMs);
  if (!rows.length) {
    throw new Error('Aucune ligne récupérée dans STAGING.');
  }
  return rows;
}

function waitForStagingRowsAllowEmpty_(sheet, expectedCols, timeoutSeconds, pollMs) {
  const deadline = Date.now() + timeoutSeconds * 1000;
  let stableCount = 0;
  let previousSignature = '';
  let sawAnyContent = false;

  while (Date.now() < deadline) {
    SpreadsheetApp.flush();
    Utilities.sleep(pollMs);

    const formula = sheet.getRange('A1').getFormula();
    const anchorDisplay = sheet.getRange('A1').getDisplayValue();
    const anchorRaw = sheet.getRange('A1').getValue();

    if (!formula) {
      throw new Error('STAGING!A1 ne contient plus de formule.');
    }

    if (anchorDisplay && anchorDisplay.startsWith('#')) {
      const details = getStagingErrorDetails_(sheet);
      throw new Error(`Erreur SheetsFinance: ${details || anchorDisplay}`);
    }

    const values = sheet.getRange(1, 1, sheet.getMaxRows(), expectedCols).getValues();
    const displayValues = sheet.getRange(1, 1, sheet.getMaxRows(), expectedCols).getDisplayValues();
    const rows = trimTrailingEmptyRows_(values, displayValues);

    const hasAnyContent = rows.length > 0 || (anchorDisplay !== '' && anchorDisplay !== formula) || (anchorRaw !== '' && anchorRaw !== formula);
    if (hasAnyContent) {
      sawAnyContent = true;
    }

    const signature = JSON.stringify({ count: rows.length, last: rows.length ? rows[rows.length - 1] : [], anchorDisplay });
    if (signature === previousSignature) {
      stableCount += 1;
    } else {
      stableCount = 0;
      previousSignature = signature;
    }

    if (sawAnyContent && stableCount >= 1) {
      return rows;
    }
  }

  const formula = sheet.getRange('A1').getFormula();
  const anchorDisplay = sheet.getRange('A1').getDisplayValue();
  throw new Error(`Timeout en attendant le calcul de STAGING. Formula=${formula} | A1=${anchorDisplay}`);
}

function trimTrailingEmptyRows_(values, displayValues) {
  const rows = [];
  for (let i = 0; i < values.length; i += 1) {
    const rowValues = values[i];
    const rowDisplay = displayValues[i];
    const isEmpty = rowDisplay.every(cell => cell === '');
    if (!isEmpty) {
      rows.push(rowValues.map((value, idx) => value instanceof Date ? formatDateTime_(value) : (rowDisplay[idx] !== '' ? rowDisplay[idx] : value)));
    }
  }
  return rows;
}

function normalizeBarsRows_(rows, symbol) {
  return rows
    .filter(row => row[0] && !String(row[0]).startsWith('#'))
    .map(row => [
      symbol,
      normalizeTimestampString_(row[0]),
      normalizeNumeric_(row[1]),
      normalizeNumeric_(row[2]),
      normalizeNumeric_(row[3]),
      normalizeNumeric_(row[4]),
      normalizeNumeric_(row[5])
    ]);
}

function normalizeSplitsRows_(rows, symbol) {
  return rows
    .filter(row => row[0] && !String(row[0]).startsWith('#'))
    .map(row => [
      symbol,
      normalizeDateString_(row[0]),
      normalizeNumeric_(row[2]),
      normalizeNumeric_(row[3]),
      normalizeNumeric_(row[4])
    ]);
}

function normalizeFxRows_(rows, pair, invert) {
  return rows
    .filter(row => row[0] && !String(row[0]).startsWith('#'))
    .map(row => {
      const open = normalizeFxNumeric_(row[1], invert);
      const high = normalizeFxNumeric_(row[2], invert);
      const low = normalizeFxNumeric_(row[3], invert);
      const close = normalizeFxNumeric_(row[4], invert);

      return [
        pair,
        normalizeTimestampString_(row[0]),
        open,
        invert ? low : high,
        invert ? high : low,
        close
      ];
    });
}

function normalizeFxNumeric_(value, invert) {
  const normalized = normalizeNumeric_(value);
  if (!invert || normalized === '') return normalized;

  const n = parseFloat(normalized);
  if (!Number.isFinite(n) || n === 0) return '';
  return String(1 / n);
}

function appendBarsRowsToDrive_(root, symbol, rows) {
  if (!rows.length) return;

  const groups = {};
  rows.forEach(row => {
    const monthKey = row[1].slice(0, 7);
    if (!groups[monthKey]) groups[monthKey] = [];
    groups[monthKey].push(row);
  });

  Object.keys(groups).sort().forEach(monthKey => {
    const year = monthKey.slice(0, 4);
    const folder = ensureFolderPath_(root.rawFolder, [symbol, year], root.folderCache);
    const fileName = `${symbol}_5m_${monthKey}.csv`;
    const header = ['symbol', 'timestamp', 'open', 'high', 'low', 'close', 'volume'];
    upsertCsvFile_(folder, fileName, header, groups[monthKey], row => `${row[0]}|${row[1]}`);
  });
}

function appendSplitsRowsToDrive_(root, symbol, rows) {
  const folder = root.splitsFolder;
  const fileName = `${symbol}_splits.csv`;
  const header = ['symbol', 'date', 'numerator', 'denominator', 'ratio'];
  upsertCsvFile_(folder, fileName, header, rows, row => `${row[0]}|${row[1]}|${row[4]}`);
}

function appendFxRowsToDrive_(root, pair, rows) {
  if (!rows.length) return;

  const groups = {};
  rows.forEach(row => {
    const monthKey = row[1].slice(0, 7);
    if (!groups[monthKey]) groups[monthKey] = [];
    groups[monthKey].push(row);
  });

  Object.keys(groups).sort().forEach(monthKey => {
    const year = monthKey.slice(0, 4);
    const folder = ensureFolderPath_(root.fxFolder, [pair, year], root.folderCache);
    const fileName = `${pair}_5m_${monthKey}.csv`;
    const header = ['pair', 'timestamp', 'open', 'high', 'low', 'close'];
    upsertCsvFile_(folder, fileName, header, groups[monthKey], row => `${row[0]}|${row[1]}`);
  });
}

function writeSymbolCurrencyMapToDrive_(root, rows) {
  const header = ['symbol', 'currency'];
  upsertCsvFile_(root.fxFolder, 'symbol_currency_map.csv', header, rows, row => row[0]);
}

function upsertCsvFile_(folder, fileName, header, newRows, dedupeKeyFn) {
  let file = findExistingCsvLikeFile_(folder, fileName);
  let existingRows = [];

  if (file) {
    const content = file.getBlob().getDataAsString('UTF-8');
    const parsed = content.trim() ? Utilities.parseCsv(content) : [];
    existingRows = parsed.length > 1 ? parsed.slice(1) : [];
  }

  // Keep one row per logical key, but let newly collected rows replace old rows.
  // This is important after collector fixes: rerunning an already-exported window
  // can repair previously corrupted numeric values instead of being ignored.
  const rowsByKey = {};
  existingRows.forEach(row => {
    rowsByKey[dedupeKeyFn(row)] = row;
  });
  newRows.forEach(row => {
    rowsByKey[dedupeKeyFn(row)] = row;
  });
  const mergedRows = Object.keys(rowsByKey).map(key => rowsByKey[key]);

  mergedRows.sort((a, b) => {
    const left = a[1];
    const right = b[1];
    return left < right ? -1 : left > right ? 1 : 0;
  });

  const csv = rowsToCsv_([header].concat(mergedRows));

  if (file) {
    file.setContent(csv);
  } else {
    // Important : on crée un fichier texte nommé .csv, pas un fichier MimeType.CSV.
    file = folder.createFile(fileName, csv);
  }
}

function rowsToCsv_(rows) {
  return rows.map(row => row.map(csvEscape_).join(',')).join('\n') + '\n';
}

function csvEscape_(value) {
  const s = value === null || value === undefined ? '' : String(value);
  if (/[",\n]/.test(s)) {
    return '"' + s.replace(/"/g, '""') + '"';
  }
  return s;
}

function ensureDriveFolders_(cfg) {
  const root = ensureRootFolder_(cfg.ROOT_FOLDER_NAME || COLLECTOR.ROOT_FOLDER_NAME);
  const folderCache = {};

  const rawFolder = ensureFolderPath_(root, getRawSubpath_(cfg.BARS_PERIOD), folderCache);
  const splitsFolder = ensureFolderPath_(root, COLLECTOR.SPLITS_SUBPATH, folderCache);
  const fxFolder = ensureFolderPath_(root, getFxSubpath_(cfg.BARS_PERIOD), folderCache);

  return { root, rawFolder, splitsFolder, fxFolder, folderCache };
}

function ensureRootFolder_(name) {
  const iter = DriveApp.getFoldersByName(name);
  if (iter.hasNext()) return iter.next();
  return DriveApp.createFolder(name);
}

function ensureFolderPath_(baseFolder, pathParts, folderCache) {
  let current = baseFolder;
  let currentId = current.getId();
  const cache = folderCache || {};

  pathParts.forEach(part => {
    const cacheKey = `${currentId}/${part}`;
    if (cache[cacheKey]) {
      current = DriveApp.getFolderById(cache[cacheKey]);
      currentId = current.getId();
      return;
    }

    current = findOrCreateFolderWithRetry_(current, part);
    currentId = current.getId();
    cache[cacheKey] = currentId;
  });

  return current;
}

function setupConfigSheet_(sheet) {
  const entries = [
    ['KEY', 'VALUE', 'DESCRIPTION'],
    ['WATCHLIST', COLLECTOR.DEFAULTS.WATCHLIST, 'Comma-separated symbols, e.g. AAPL,MSFT,NVDA'],
    ['START_DATE', COLLECTOR.DEFAULTS.START_DATE, 'Inclusive start date YYYY-MM-DD'],
    ['END_DATE', COLLECTOR.DEFAULTS.END_DATE, 'Inclusive end date YYYY-MM-DD'],
    ['BARS_PERIOD', COLLECTOR.DEFAULTS.BARS_PERIOD, 'Expected: 5min'],
    ['BARS_WINDOW_DAYS', COLLECTOR.DEFAULTS.BARS_WINDOW_DAYS, 'SheetsFinance intraday window size'],
    ['SPLITS_WINDOW_DAYS', COLLECTOR.DEFAULTS.SPLITS_WINDOW_DAYS, 'Calendar request window size'],
    ['FX_WINDOW_DAYS', COLLECTOR.DEFAULTS.FX_WINDOW_DAYS, 'FX time-series window size, usually same as BARS_WINDOW_DAYS'],
    ['BARS_METRICS', COLLECTOR.DEFAULTS.BARS_METRICS, 'date&open&high&low&close&volume'],
    ['SPLITS_METRICS', COLLECTOR.DEFAULTS.SPLITS_METRICS, 'date&symbol&numerator&denominator&ratio'],
    ['FX_METRICS', COLLECTOR.DEFAULTS.FX_METRICS, 'date&open&high&low&close'],
    ['TIME_SERIES_OPTIONS', COLLECTOR.DEFAULTS.TIME_SERIES_OPTIONS, 'Start with NH. Add - only after validating order locally.'],
    ['SPLITS_OPTIONS', COLLECTOR.DEFAULTS.SPLITS_OPTIONS, 'Usually NH'],
    ['FX_OPTIONS', COLLECTOR.DEFAULTS.FX_OPTIONS, 'Usually NH'],
    ['TARGET_CURRENCIES', COLLECTOR.DEFAULTS.TARGET_CURRENCIES, 'Comma-separated currencies to generate FX rates to, e.g. EUR,USD'],
    ['FORMULA_ARG_SEPARATOR', COLLECTOR.DEFAULTS.FORMULA_ARG_SEPARATOR, 'AUTO, ;, or , depending on spreadsheet locale'],
    ['MAX_BARS_WINDOWS_PER_RUN', COLLECTOR.DEFAULTS.MAX_BARS_WINDOWS_PER_RUN, 'Keep runs short and resumable'],
    ['MAX_SPLITS_WINDOWS_PER_RUN', COLLECTOR.DEFAULTS.MAX_SPLITS_WINDOWS_PER_RUN, 'Keep runs short and resumable'],
    ['MAX_FX_WINDOWS_PER_RUN', COLLECTOR.DEFAULTS.MAX_FX_WINDOWS_PER_RUN, 'Keep FX runs short and resumable'],
    ['WAIT_TIMEOUT_SECONDS', COLLECTOR.DEFAULTS.WAIT_TIMEOUT_SECONDS, 'Per formula timeout'],
    ['POLL_INTERVAL_MS', COLLECTOR.DEFAULTS.POLL_INTERVAL_MS, 'Polling interval'],
    ['RESPECTFUL_PAUSE_MS', COLLECTOR.DEFAULTS.RESPECTFUL_PAUSE_MS, 'Pause between requests'],
    ['ROOT_FOLDER_NAME', COLLECTOR.DEFAULTS.ROOT_FOLDER_NAME, 'Google Drive root folder name'],
    ['MAX_RETRIES_PER_BATCH', COLLECTOR.DEFAULTS.MAX_RETRIES_PER_BATCH, 'Nombre maximum de tentatives par batch avant de laisser le superviseur reprogrammer un cycle'],
    ['RETRY_BACKOFF_MS', COLLECTOR.DEFAULTS.RETRY_BACKOFF_MS, 'Pause de base entre deux retries, en millisecondes'],
    ['AUTO_NEXT_CYCLE_DELAY_SECONDS', COLLECTOR.DEFAULTS.AUTO_NEXT_CYCLE_DELAY_SECONDS, 'Délai court avant le prochain cycle automatique normal, après la fin du cycle courant'],
    ['AUTO_RELAUNCH_DELAY_MINUTES', COLLECTOR.DEFAULTS.AUTO_RELAUNCH_DELAY_MINUTES, 'Ancien délai par défaut/fallback en minutes si aucun délai explicite n’est fourni'],
    ['BUSY_RETRY_DELAY_SECONDS', COLLECTOR.DEFAULTS.BUSY_RETRY_DELAY_SECONDS, 'Délai court de retry si un autre collectorSupervisor est déjà en cours'],
    ['EXECUTION_TIME_LIMIT_SECONDS', COLLECTOR.DEFAULTS.EXECUTION_TIME_LIMIT_SECONDS, 'Budget max volontaire par exécution, inférieur à la limite Apps Script de 360 s'],
    ['MIN_TIME_REMAINING_SECONDS', COLLECTOR.DEFAULTS.MIN_TIME_REMAINING_SECONDS, 'Marge minimale restante avant de démarrer une nouvelle fenêtre SheetsFinance'],
    ['AUTO_COLLECTOR_TASKS', 'bars,splits,fx', 'Tâches exécutées par le superviseur auto : bars, splits, fx (virgule-séparées)']
  ];

  sheet.clear();
  sheet.getRange(1, 1, entries.length, entries[0].length).setValues(entries);
  sheet.setFrozenRows(1);
  sheet.getRange(2, 2, entries.length - 1, 1).setNumberFormat('@');
  sheet.autoResizeColumns(1, 3);
}

function setupStagingSheet_(sheet) {
  sheet.clear();
  sheet.getRange('A1').setValue('Formula will be written here by the script.');
  sheet.getRange('A2').setValue('Keep this sheet otherwise empty.');
}

function setupCheckpointsSheet_(sheet) {
  sheet.clear();
  sheet.getRange(1, 1, 1, 8).setValues([['task', 'symbol', 'next_start', 'last_end', 'status', 'updated_at', 'message', 'run_id']]);
  sheet.setFrozenRows(1);
  sheet.autoResizeColumns(1, 8);
}

function setupLogsSheet_(sheet) {
  sheet.clear();
  sheet.getRange(1, 1, 1, 9).setValues([['timestamp', 'task', 'symbol', 'window_start', 'window_end', 'rows', 'status', 'message', 'run_id']]);
  sheet.setFrozenRows(1);
  sheet.autoResizeColumns(1, 9);
}

function readConfig_() {
  const sheet = getCollectorSpreadsheet_().getSheetByName(COLLECTOR.CONFIG_SHEET);
  if (!sheet) throw new Error('La feuille CONFIG est introuvable. Lancez setupCollectorWorkbook().');
  const values = sheet.getDataRange().getValues();
  const cfg = {};
  values.slice(1).forEach(row => {
    if (row[0]) cfg[String(row[0]).trim()] = normalizeConfigValue_(row[1]);
  });
  return cfg;
}

function getWatchlist_(cfg) {
  return (cfg.WATCHLIST || '')
    .split(',')
    .map(s => s.trim().toUpperCase())
    .filter(Boolean);
}

function getAutoCollectorTasks_(cfg) {
  const raw = String(cfg.AUTO_COLLECTOR_TASKS || 'bars,splits,fx').toLowerCase();
  const tasks = raw.split(',').map(s => s.trim()).filter(Boolean);
  return {
    bars: tasks.includes('bars'),
    splits: tasks.includes('splits'),
    fx: tasks.includes('fx')
  };
}

function getTargetCurrencies_(cfg) {
  return (cfg.TARGET_CURRENCIES || '')
    .split(',')
    .map(s => normalizeCurrencyCode_(s))
    .filter(Boolean)
    .filter((currency, idx, arr) => arr.indexOf(currency) === idx);
}

function getRawTargetCurrencyEntries_(cfg) {
  return (cfg.TARGET_CURRENCIES || '')
    .split(',')
    .map(s => String(s || '').trim())
    .filter(Boolean);
}

function normalizeCurrencyCode_(value) {
  const currency = String(value || '').trim().toUpperCase();
  return /^[A-Z]{3}$/.test(currency) ? currency : '';
}

function getSymbolCurrencyMap_(staging, watchlist, cfg, pauseMs) {
  const result = [];

  for (const symbol of watchlist) {
    const formula = buildCurrencyFormula_(symbol, cfg);

    clearStaging_();
    writeFormulaToStaging_(staging, formula, 1);
    toast_(`Currency request: ${symbol}`);

    const rows = waitForStagingRows_(
      staging,
      1,
      parseInt(cfg.WAIT_TIMEOUT_SECONDS, 10),
      parseInt(cfg.POLL_INTERVAL_MS, 10)
    );

    const currency = normalizeCurrencyCode_(rows[0] && rows[0][0]);
    if (!currency) {
      throw new Error(`Devise introuvable ou invalide pour ${symbol}: ${rows[0] && rows[0][0]}`);
    }

    result.push([symbol, currency]);
    Utilities.sleep(pauseMs);
  }

  return result;
}

function buildFxPairsFromCurrencyMap_(symbolCurrencyMap, targetCurrencies) {
  const sourceCurrencies = symbolCurrencyMap
    .map(row => normalizeCurrencyCode_(row[1]))
    .filter(Boolean)
    .filter((currency, idx, arr) => arr.indexOf(currency) === idx);

  const seen = {};
  const pairs = [];

  sourceCurrencies.forEach(source => {
    targetCurrencies.forEach(target => {
      if (source === target) return;

      const pair = `${source}${target}`;
      if (seen[pair]) return;

      seen[pair] = true;
      pairs.push({
        source,
        target,
        pair,
        directPair: pair,
        inversePair: `${target}${source}`
      });
    });
  });

  pairs.sort((a, b) => a.pair < b.pair ? -1 : a.pair > b.pair ? 1 : 0);
  return pairs;
}

function saveFxPairs_(cfg, pairs) {
  const props = PropertiesService.getScriptProperties();
  const key = getFxPairsPropertyKey_(cfg);
  const normalizedPairs = (pairs || [])
    .map(pair => String(pair || '').trim().toUpperCase())
    .filter(Boolean)
    .filter((pair, idx, arr) => arr.indexOf(pair) === idx)
    .sort();

  props.setProperty(key, normalizedPairs.join(','));
}

function getSavedFxPairs_(cfg) {
  const raw = PropertiesService.getScriptProperties().getProperty(getFxPairsPropertyKey_(cfg));
  if (raw === null) return null;
  return raw
    .split(',')
    .map(pair => pair.trim().toUpperCase())
    .filter(Boolean);
}

function getFxPairsPropertyKey_(cfg) {
  const rootName = cfg.ROOT_FOLDER_NAME || COLLECTOR.ROOT_FOLDER_NAME;
  return `SF_COLLECTOR_FX_PAIRS_${rootName}`;
}

function getCheckpoint_(sheet, task, symbol) {
  const values = sheet.getDataRange().getValues();
  for (let i = 1; i < values.length; i += 1) {
    if (values[i][0] === task && values[i][1] === symbol) {
      return {
        row: i + 1,
        next_start: values[i][2],
        last_end: values[i][3],
        status: values[i][4],
        updated_at: values[i][5],
        message: values[i][6],
        run_id: values[i][7]
      };
    }
  }
  return null;
}

function setCheckpoint_(sheet, task, symbol, nextStart, lastEnd, status, message) {
  const existing = getCheckpoint_(sheet, task, symbol);
  const row = existing ? existing.row : sheet.getLastRow() + 1;
  const values = [[
    task,
    symbol,
    fmtDate_(nextStart),
    fmtDate_(lastEnd),
    status,
    new Date(),
    message,
    createRunId_()
  ]];
  sheet.getRange(row, 1, 1, values[0].length).setValues(values);
}

function logRun_(symbol, task, startDate, endDate, rowCount, status, message) {
  const sheet = getCollectorSpreadsheet_().getSheetByName(COLLECTOR.LOGS_SHEET);
  sheet.appendRow([
    new Date(),
    task,
    symbol,
    fmtDate_(startDate),
    fmtDate_(endDate),
    rowCount,
    status,
    message,
    createRunId_()
  ]);
}

function getCompletionSnapshot_() {
  const cfg = readConfig_();
  const checkpoints = getCollectorSpreadsheet_().getSheetByName(COLLECTOR.CHECKPOINTS_SHEET);
  const endDate = cfg.END_DATE;
  const snapshot = {};
  getWatchlist_(cfg).forEach(symbol => {
    const bars = getCheckpoint_(checkpoints, 'bars', symbol);
    const splits = getCheckpoint_(checkpoints, 'splits', symbol);
    snapshot[`bars:${symbol}`] = bars ? `${bars.next_start}|${bars.status}` : `none|pending until ${endDate}`;
    snapshot[`splits:${symbol}`] = splits ? `${splits.next_start}|${splits.status}` : `none|pending until ${endDate}`;
  });

  const fxPairs = getSavedFxPairs_(cfg);
  if (fxPairs === null && getTargetCurrencies_(cfg).length) {
    snapshot['fx:pairs'] = `not initialized|pending until ${endDate}`;
  } else if (fxPairs && fxPairs.length) {
    fxPairs.forEach(pair => {
      const fx = getCheckpoint_(checkpoints, 'fx', pair);
      snapshot[`fx:${pair}`] = fx ? `${fx.next_start}|${fx.status}` : `none|pending until ${endDate}`;
    });
  } else {
    snapshot['fx:pairs'] = 'none|required pairs empty or TARGET_CURRENCIES empty';
  }

  return snapshot;
}

function allComplete_() {
  const cfg = readConfig_();
  const tasks = getAutoCollectorTasks_(cfg);
  const checkpoints = getCollectorSpreadsheet_().getSheetByName(COLLECTOR.CHECKPOINTS_SHEET);
  const endDate = parseDate_(cfg.END_DATE);

  if (tasks.bars) {
    const barsDone = getWatchlist_(cfg).every(symbol => {
      const bars = getCheckpoint_(checkpoints, 'bars', symbol);
      return bars && parseDateSafe_(bars.next_start) > endDate;
    });
    if (!barsDone) return false;
  }

  if (tasks.splits) {
    const splitsDone = getWatchlist_(cfg).every(symbol => {
      const splits = getCheckpoint_(checkpoints, 'splits', symbol);
      return splits && parseDateSafe_(splits.next_start) > endDate;
    });
    if (!splitsDone) return false;
  }

  if (tasks.fx) {
    const targetCurrencies = getTargetCurrencies_(cfg);
    if (!targetCurrencies.length) return true;

    const fxPairs = getSavedFxPairs_(cfg);
    if (fxPairs === null) return false;
    if (!fxPairs.length) return true;

    const fxDone = fxPairs.every(pair => {
      const fx = getCheckpoint_(checkpoints, 'fx', pair);
      return fx && parseDateSafe_(fx.next_start) > endDate;
    });
    if (!fxDone) return false;
  }

  return true;
}

function clearStaging_() {
  const sheet = getCollectorSpreadsheet_().getSheetByName(COLLECTOR.STAGING_SHEET);
  if (!sheet) throw new Error('La feuille STAGING est introuvable.');
  sheet.clearContents();
  sheet.clearFormats();
  SpreadsheetApp.flush();
}

function validateBarsConfig_(cfg, watchlist, maxWindows) {
  if (!watchlist.length) throw new Error('WATCHLIST vide dans CONFIG.');
  if (!cfg.START_DATE || !cfg.END_DATE) throw new Error('START_DATE ou END_DATE manquant dans CONFIG.');
  if (parseDate_(cfg.START_DATE) > parseDate_(cfg.END_DATE)) throw new Error('START_DATE est postérieur à END_DATE.');
  if (!Number.isFinite(maxWindows) || maxWindows <= 0) throw new Error('MAX_BARS_WINDOWS_PER_RUN doit être > 0.');
  const supported = ['1min','5min','15min','30min','1hour'];
  if (!supported.includes((cfg.BARS_PERIOD || '').trim())) throw new Error('BARS_PERIOD doit être l\'un de : ' + supported.join(', '));
}

function validateFxConfig_(cfg, watchlist, targetCurrencies, maxWindows, windowDays) {
  const rawTargetCurrencies = getRawTargetCurrencyEntries_(cfg);

  if (!watchlist.length) throw new Error('WATCHLIST vide dans CONFIG.');
  if (!cfg.START_DATE || !cfg.END_DATE) throw new Error('START_DATE ou END_DATE manquant dans CONFIG.');
  if (parseDate_(cfg.START_DATE) > parseDate_(cfg.END_DATE)) throw new Error('START_DATE est postérieur à END_DATE.');
  if (!Number.isFinite(maxWindows) || maxWindows <= 0) throw new Error('MAX_FX_WINDOWS_PER_RUN doit être > 0.');
  if (!Number.isFinite(windowDays) || windowDays <= 0) throw new Error('FX_WINDOW_DAYS doit être > 0.');
  const supportedFx = ['1min','5min','15min','30min','1hour'];
  if (!supportedFx.includes((cfg.BARS_PERIOD || '').trim())) throw new Error('BARS_PERIOD doit être l\'un de : ' + supportedFx.join(', '));

  if (targetCurrencies.length !== rawTargetCurrencies.length) throw new Error('TARGET_CURRENCIES contient une devise invalide. Utilisez des codes ISO à 3 lettres, e.g. EUR,USD.');
}

function toast_(message) {
  try {
    getCollectorSpreadsheet_().toast(message, 'SF Collector', 5);
  } catch (err) {
    Logger.log(`Toast skipped: ${message}`);
  }
}

function withCollectorLock_(fn) {
  const lock = LockService.getScriptLock();
  lock.waitLock(30000);
  try {
    fn();
  } finally {
    lock.releaseLock();
  }
}

function ensureSheet_(ss, name) {
  return ss.getSheetByName(name) || ss.insertSheet(name);
}

function parseDate_(value) {
  if (value instanceof Date) {
    return new Date(value.getFullYear(), value.getMonth(), value.getDate());
  }

  const s = String(value).trim();
  const iso = s.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (iso) {
    return new Date(Number(iso[1]), Number(iso[2]) - 1, Number(iso[3]));
  }

  const parsed = new Date(s);
  if (!Number.isNaN(parsed.getTime())) {
    return new Date(parsed.getFullYear(), parsed.getMonth(), parsed.getDate());
  }

  throw new Error(`Date invalide dans CONFIG: ${value}`);
}

function parseDateSafe_(value) {
  if (value instanceof Date) return value;
  return parseDate_(value);
}

function addDays_(date, days) {
  const d = new Date(date.getTime());
  d.setDate(d.getDate() + days);
  return d;
}

function minDate_(a, b) {
  return a <= b ? a : b;
}

function fmtDate_(date) {
  if (!(date instanceof Date) || Number.isNaN(date.getTime())) {
    throw new Error(`Impossible de formater une date invalide: ${date}`);
  }
  return Utilities.formatDate(date, Session.getScriptTimeZone(), COLLECTOR.DATE_FORMAT);
}

function formatDateTime_(date) {
  return Utilities.formatDate(date, Session.getScriptTimeZone(), COLLECTOR.DATETIME_FORMAT);
}

function normalizeTimestampString_(value) {
  const s = String(value).trim();
  return s.replace('T', ' ').replace(/\s+/g, ' ');
}

function normalizeDateString_(value) {
  return String(value).trim().slice(0, 10);
}

function normalizeNumeric_(value) {
  if (value === '' || value === null || value === undefined) return '';
  if (typeof value === 'number') return formatCanonicalNumber_(value);

  const parsed = parseLocaleNumber_(value);
  if (parsed === null) return '';
  return formatCanonicalNumber_(parsed);
}

function parseLocaleNumber_(value) {
  if (value === '' || value === null || value === undefined) return null;

  let s = String(value)
    .trim()
    .replace(/\u00a0/g, '')
    .replace(/\u202f/g, '')
    .replace(/\s+/g, '');

  if (s === '') return null;

  // Keep only numeric notation characters. Some display values can include
  // currency symbols or typographic minus signs depending on locale/add-on.
  s = s
    .replace(/−/g, '-')
    .replace(/[A-Za-z]+/g, '')
    .replace(/[^0-9,.\-+]/g, '');

  if (s === '' || s === '-' || s === '+') return null;

  const commaIndex = s.lastIndexOf(',');
  const dotIndex = s.lastIndexOf('.');

  if (commaIndex !== -1 && dotIndex !== -1) {
    // Both separators exist: the rightmost one is treated as decimal separator.
    // Examples: "4,310.5" -> "4310.5" and "4.310,5" -> "4310.5".
    if (commaIndex > dotIndex) {
      s = s.replace(/\./g, '').replace(',', '.');
    } else {
      s = s.replace(/,/g, '');
    }
  } else if (commaIndex !== -1) {
    // Decimal comma locale: "4310,5" -> "4310.5". Multiple commas are treated
    // as thousands separators except the rightmost decimal comma.
    const parts = s.split(',');
    if (parts.length === 2) {
      s = parts[0] + '.' + parts[1];
    } else {
      const decimal = parts.pop();
      s = parts.join('') + '.' + decimal;
    }
  }

  const n = Number(s);
  return Number.isFinite(n) ? n : null;
}

function formatCanonicalNumber_(value) {
  const n = Number(value);
  if (!Number.isFinite(n)) return '';
  // CSV exports must be locale-independent. Always use a dot decimal separator
  // and avoid scientific notation for normal market/FX magnitudes.
  return Number.isInteger(n) ? String(n) : String(Number(n.toFixed(12)));
}

function escapeFormulaString_(value) {
  return String(value).replace(/"/g, '""');
}

function createRunId_() {
  return Utilities.getUuid().slice(0, 8);
}

function normalizeConfigValue_(value) {
  if (value instanceof Date) {
    return Utilities.formatDate(value, Session.getScriptTimeZone(), COLLECTOR.DATE_FORMAT);
  }
  if (value === null || value === undefined) return '';
  return String(value).trim();
}

function quoteFormulaArg_(value) {
  return `"${escapeFormulaString_(value)}"`;
}

function getFormulaArgSeparator_(cfg) {
  const explicit = String(cfg.FORMULA_ARG_SEPARATOR || 'AUTO').trim();
  if (explicit === ';' || explicit === ',') return explicit;

  const locale = SpreadsheetApp.getActive().getSpreadsheetLocale();
  const semicolonLocales = /^(fr|de|es|it|pt|nl|pl|ru|tr|cs|hu|sv|da|fi|no)/i;
  return semicolonLocales.test(locale) ? ';' : ',';
}

function getStagingErrorDetails_(sheet) {
  const cell = sheet.getRange('A1');
  const display = cell.getDisplayValue() || '';
  const note = cell.getNote() || '';
  return [display, note].filter(Boolean).join(' | ');
}

function isNoDataSplitsError_(sheet, err) {
  const text = [
    String(err && err.message ? err.message : err || ''),
    getStagingErrorDetails_(sheet)
  ].join(' | ').toLowerCase();

  return text.includes('no splits calendar data found') ||
         text.includes('no data found');
}

function findOrCreateFolderWithRetry_(parentFolder, folderName) {
  for (let attempt = 1; attempt <= 4; attempt += 1) {
    const folders = parentFolder.getFoldersByName(folderName);
    if (folders.hasNext()) {
      return folders.next();
    }

    const files = parentFolder.getFilesByName(folderName);
    if (files.hasNext()) {
      throw new Error(`Un fichier nommé "${folderName}" existe déjà là où un dossier est attendu.`);
    }

    try {
      return parentFolder.createFolder(folderName);
    } catch (err) {
      if (attempt === 4) throw err;
      Utilities.sleep(1000 * attempt);
    }
  }

  throw new Error(`Impossible de créer ou retrouver le dossier "${folderName}".`);
}

function findExistingCsvLikeFile_(folder, fileName) {
  const exact = folder.getFilesByName(fileName);
  if (exact.hasNext()) return exact.next();

  const baseName = fileName.replace(/\.csv$/i, '');
  const bare = folder.getFilesByName(baseName);
  if (bare.hasNext()) return bare.next();

  return null;
}

function getCollectorSpreadsheet_() {
  const props = PropertiesService.getScriptProperties();
  const savedId = props.getProperty('SF_COLLECTOR_SPREADSHEET_ID');

  const active = SpreadsheetApp.getActiveSpreadsheet() || SpreadsheetApp.getActive();
  if (active) {
    if (savedId !== active.getId()) {
      props.setProperty('SF_COLLECTOR_SPREADSHEET_ID', active.getId());
    }
    return active;
  }

  if (!savedId) {
    throw new Error('Aucun spreadsheet lié au collecteur n’est enregistré.');
  }

  return SpreadsheetApp.openById(savedId);
}

function saveCollectorSpreadsheetId_() {
  const ss = getCollectorSpreadsheet_();
  PropertiesService.getScriptProperties().setProperty('SF_COLLECTOR_SPREADSHEET_ID', ss.getId());
}

function isAutoCollectorEnabled_() {
  return PropertiesService.getScriptProperties().getProperty('SF_COLLECTOR_AUTO_ENABLED') === 'true';
}

function setAutoCollectorEnabled_(enabled) {
  PropertiesService.getScriptProperties().setProperty('SF_COLLECTOR_AUTO_ENABLED', enabled ? 'true' : 'false');
}

function deleteCollectorTriggers_() {
  ScriptApp.getProjectTriggers().forEach(trigger => {
    if (trigger.getHandlerFunction && trigger.getHandlerFunction() === 'collectorSupervisor') {
      ScriptApp.deleteTrigger(trigger);
    }
  });
}

function getIntConfigOrDefault_(cfg, key, fallback) {
  const raw = cfg[key];
  const n = parseInt(raw, 10);
  return Number.isFinite(n) ? n : fallback;
}

function getExecutionDeadlineMs_(cfg) {
  const limitSeconds = getIntConfigOrDefault_(cfg, 'EXECUTION_TIME_LIMIT_SECONDS', 330);
  return Date.now() + Math.max(60, limitSeconds) * 1000;
}

function getMinTimeRemainingMs_(cfg) {
  const minSeconds = getIntConfigOrDefault_(cfg, 'MIN_TIME_REMAINING_SECONDS', 180);
  return Math.max(30, minSeconds) * 1000;
}

function getAutoNextCycleDelayMs_(cfg) {
  const delaySeconds = getIntConfigOrDefault_(cfg, 'AUTO_NEXT_CYCLE_DELAY_SECONDS', parseInt(COLLECTOR.DEFAULTS.AUTO_NEXT_CYCLE_DELAY_SECONDS, 10));
  return Math.max(10, delaySeconds) * 1000;
}

function shouldStopForTimeBudget_(deadlineMs, minRemainingMs) {
  if (!deadlineMs) return false;
  return Date.now() + minRemainingMs >= deadlineMs;
}

function safeToast_(message) {
  try {
    getCollectorSpreadsheet_().toast(message, 'SF Collector', 5);
  } catch (err) {
    Logger.log(`Toast skipped: ${message}`);
  }
}

function shouldRetryBatchError_(err) {
  const message = String(err && err.message ? err.message : err || '').toLowerCase();

  return (
    message.includes('drive') ||
    message.includes('service error') ||
    message.includes('server error') ||
    message.includes('internal error') ||
    message.includes('timeout') ||
    message.includes('temporarily unavailable') ||
    message.includes('exception: service invoked too many times') ||
    message.includes('erreur liée à un service') ||
    message.includes('too many requests') ||
    message.includes('#error!') ||
    message.includes('#name?') ||
    message.includes('fonction inconnue') ||
    message.includes('unknown function')
  );
}

function isNoDataError_(err) {
  const message = String(err && err.message ? err.message : err || '').toLowerCase();
  return (
    message.includes('no intra-day time-series data found') ||
    message.includes('no time-series data found') ||
    message.includes('no data found') ||
    message.includes('no calendar data found') ||
    message.includes('we may not have the requested data') ||
    message.includes('#error!')
  );
}

function isSheetsFinanceFunctionUnavailableError_(err) {
  const message = String(err && err.message ? err.message : err || '').toLowerCase();
  return (
    message.includes('#name?') ||
    message.includes('fonction inconnue') ||
    message.includes('unknown function')
  );
}

function runWithRetries_(label, fn, cfg, deadlineMs) {
  const maxRetries = getIntConfigOrDefault_(cfg, 'MAX_RETRIES_PER_BATCH', 3);
  const baseBackoffMs = getIntConfigOrDefault_(cfg, 'RETRY_BACKOFF_MS', 5000);
  const minRemainingMs = getMinTimeRemainingMs_(cfg);

  let attempt = 0;
  let lastErr = null;

  while (attempt < maxRetries) {
    if (shouldStopForTimeBudget_(deadlineMs, minRemainingMs)) {
      Logger.log(`${label} skipped: not enough execution budget for another attempt.`);
      return;
    }

    try {
      attempt += 1;
      Logger.log(`${label} | attempt ${attempt}/${maxRetries}`);
      return fn();
    } catch (err) {
      lastErr = err;

      const retryable = shouldRetryBatchError_(err);
      Logger.log(`${label} | attempt ${attempt} failed | retryable=${retryable} | err=${err}`);

      if (!retryable || attempt >= maxRetries) {
        throw err;
      }

      const waitMs = baseBackoffMs * attempt;
      if (shouldStopForTimeBudget_(deadlineMs, minRemainingMs + waitMs)) {
        Logger.log(`${label} retry postponed: not enough execution budget after attempt ${attempt}.`);
        return;
      }

      safeToast_(`${label} retry ${attempt}/${maxRetries} dans ${waitMs} ms`);
      Utilities.sleep(waitMs);
    }
  }

  throw lastErr || new Error(`${label} failed after retries`);
}

function startAutoCollector() {
  const cfg = readConfig_();
  saveCollectorSpreadsheetId_();
  setAutoCollectorEnabled_(true);
  deleteCollectorTriggers_();

  safeToast_('Auto collector démarré.');
  scheduleNextCollectorRun_(cfg, 10 * 1000);
}

function stopAutoCollector() {
  setAutoCollectorEnabled_(false);
  deleteCollectorTriggers_();
  safeToast_('Auto collector arrêté.');
}

function scheduleNextCollectorRun_(cfg, delayMs) {
  deleteCollectorTriggers_();

  const defaultDelayMinutes = getIntConfigOrDefault_(cfg, 'AUTO_RELAUNCH_DELAY_MINUTES', 8);
  const finalDelayMs = Number.isFinite(delayMs) ? delayMs : defaultDelayMinutes * 60 * 1000;

  ScriptApp.newTrigger('collectorSupervisor')
    .timeBased()
    .after(finalDelayMs)
    .create();

  Logger.log(`Next collectorSupervisor scheduled in ${finalDelayMs} ms`);
}

function scheduleBusyCollectorRetry_() {
  const cfg = readConfig_();
  const retryDelaySeconds = getIntConfigOrDefault_(cfg, 'BUSY_RETRY_DELAY_SECONDS', 120);
  const retryDelayMs = Math.max(30, retryDelaySeconds) * 1000;

  scheduleNextCollectorRun_(cfg, retryDelayMs);
  Logger.log(`collectorSupervisor busy; retry scheduled in ${retryDelayMs} ms.`);
}

function collectorSupervisor() {
  const lock = LockService.getScriptLock();
  let cfg = null;
  let deadlineMs = null;
  let shouldScheduleNext = false;

  // Si un autre cycle est encore actif, on reprogramme un retry court.
  if (!lock.tryLock(5000)) {
    Logger.log('collectorSupervisor skipped: another execution is still running.');
    scheduleBusyCollectorRetry_();
    return;
  }

  try {
    if (!isAutoCollectorEnabled_()) {
      Logger.log('Auto collector disabled, supervisor exits.');
      return;
    }

    cfg = readConfig_();
    deadlineMs = getExecutionDeadlineMs_(cfg);
    saveCollectorSpreadsheetId_();
    assertSheetsFinanceAvailable_(cfg);

    const tasks = getAutoCollectorTasks_(cfg);

    // Si tout est déjà terminé, on coupe proprement.
    if (allComplete_()) {
      Logger.log('Collection already complete. Auto collector stops.');
      stopAutoCollector();
      return;
    }

    safeToast_('Collector cycle start');
    shouldScheduleNext = true;

    // 1) Priorité aux bars
    if (tasks.bars) {
      runWithRetries_('runBarsBatch', () => runBarsBatchCore_(deadlineMs), cfg, deadlineMs);

      // Si les bars ne sont pas encore finies, le finally programme le prochain cycle.
      if (!isTaskComplete_('bars')) {
        Logger.log('Bars not complete yet. Next cycle will be scheduled after this run.');
        return;
      }
    }

    // 2) Une fois les bars terminées, on traite les splits
    if (tasks.splits) {
      runWithRetries_('runSplitsBatch', () => runSplitsBatchCore_(deadlineMs), cfg, deadlineMs);

      // Si les splits ne sont pas encore finis, le finally programme le prochain cycle.
      if (!isTaskComplete_('splits')) {
        Logger.log('Splits not complete yet. Next cycle will be scheduled after this run.');
        return;
      }
    }

    // 3) Une fois les données de marché et splits terminés, on traite les taux FX
    if (tasks.fx) {
      runWithRetries_('runFxBatch', () => runFxBatchCore_(deadlineMs), cfg, deadlineMs);
    }

    // Si tout est fini, on stoppe proprement sans reprogrammer.
    if (allComplete_()) {
      Logger.log('Collection complete. Auto collector stops.');
      shouldScheduleNext = false;
      stopAutoCollector();
      return;
    }

    Logger.log('Collector cycle complete. Next cycle will be scheduled after this run.');
  } catch (err) {
    Logger.log(`collectorSupervisor error: ${err}`);

    // On ne coupe pas le mode auto.
    // Le finally reprogrammera un cycle si le mode auto est encore actif.
    shouldScheduleNext = true;
    safeToast_(`Collector error, next scheduled cycle will retry: ${err}`);
  } finally {
    try {
      if (shouldScheduleNext && cfg && isAutoCollectorEnabled_() && !allComplete_()) {
        scheduleNextCollectorRun_(cfg, getAutoNextCycleDelayMs_(cfg));
      }
    } finally {
      lock.releaseLock();
    }
  }
}

function isTaskComplete_(taskName) {
  const cfg = readConfig_();
  const checkpoints = getCollectorSpreadsheet_().getSheetByName(COLLECTOR.CHECKPOINTS_SHEET);
  const endDate = parseDate_(cfg.END_DATE);

  if (taskName === 'fx') {
    if (!getTargetCurrencies_(cfg).length) return true;

    const pairs = getSavedFxPairs_(cfg);
    if (pairs === null) return false;
    if (!pairs.length) return true;

    return pairs.every(pair => {
      const cp = getCheckpoint_(checkpoints, 'fx', pair);
      return cp && parseDateSafe_(cp.next_start) > endDate;
    });
  }

  return getWatchlist_(cfg).every(symbol => {
    const cp = getCheckpoint_(checkpoints, taskName, symbol);
    return cp && parseDateSafe_(cp.next_start) > endDate;
  });
}