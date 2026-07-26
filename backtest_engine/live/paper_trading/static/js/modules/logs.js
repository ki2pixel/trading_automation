import { 
    getTransactions, 
    getEvaluations 
} from '../api.js';

import { 
    formatAmountForAsset,
    showToast, 
    showError 
} from '../ui.js';

export let cursorStack = [null]; // each entry: { id: number, timestamp: string } | null
export let currentPageIndex = 0;
export const txLimit = 50;

export let evalCursorStack = [null];
export let currentEvalPageIndex = 0;
export const evalLimit = 100;

export const resetTxPagination = () => {
    cursorStack = [null];
    currentPageIndex = 0;
};

export const goNextTxPage = () => {
    currentPageIndex++;
};

export const goPrevTxPage = () => {
    if (currentPageIndex > 0) {
        currentPageIndex--;
    }
};

export const goNextEvalPage = () => {
    currentEvalPageIndex++;
};

export const goPrevEvalPage = () => {
    if (currentEvalPageIndex > 0) {
        currentEvalPageIndex--;
    }
};

export const fetchTransactions = async () => {
    try {
        const cursor = cursorStack[currentPageIndex];
        const cursorTs = cursor ? cursor.timestamp : null;
        const cursorId = cursor ? cursor.id : null;
        const data = await getTransactions(txLimit, 0, cursorTs, cursorId);
        const tbody = document.getElementById('transactions-body');
        if (!tbody) return;
        tbody.innerHTML = '';

        if (data.length === 0) {
            const tr = document.createElement('tr');
            const td = document.createElement('td');
            td.colSpan = 7;
            td.style.textAlign = 'center';
            td.style.color = 'var(--text-muted)';
            td.textContent = 'No recent transactions';
            tr.appendChild(td);
            tbody.appendChild(tr);
        } else {
            data.forEach(tx => {
                const tr = document.createElement('tr');
                const date = new Date(tx.timestamp).toLocaleString('en-US');
                const actionClass = tx.action === 'BUY' ? 'positive' : 'negative';
                
                const tdDate = document.createElement('td');
                tdDate.textContent = date;
                tr.appendChild(tdDate);

                const tdAsset = document.createElement('td');
                const strongAsset = document.createElement('strong');
                strongAsset.textContent = tx.asset;
                tdAsset.appendChild(strongAsset);
                tr.appendChild(tdAsset);

                const tdStrat = document.createElement('td');
                tdStrat.textContent = tx.strategy_name;
                tr.appendChild(tdStrat);

                const tdAction = document.createElement('td');
                tdAction.className = actionClass;
                tdAction.textContent = tx.action;
                tr.appendChild(tdAction);

                const tdQty = document.createElement('td');
                tdQty.textContent = tx.qty;
                tr.appendChild(tdQty);

                const tdPrice = document.createElement('td');
                tdPrice.textContent = formatAmountForAsset(tx.asset, tx.price);
                tr.appendChild(tdPrice);

                const tdTotal = document.createElement('td');
                tdTotal.textContent = formatAmountForAsset(tx.asset, tx.total_value);
                tr.appendChild(tdTotal);
                
                tbody.appendChild(tr);
            });
        }
        
        // Update UI pagination controls
        const prevBtn = document.getElementById('btn-tx-prev');
        const nextBtn = document.getElementById('btn-tx-next');
        const pageTxt = document.getElementById('txt-tx-page');
        
        if (prevBtn) prevBtn.disabled = currentPageIndex === 0;
        if (nextBtn) nextBtn.disabled = data.length < txLimit;
        if (pageTxt) pageTxt.textContent = `Page ${currentPageIndex + 1}`;

        if (data.length === txLimit) {
            const lastItem = data[data.length - 1];
            const nextCursor = { id: lastItem.id, timestamp: lastItem.timestamp };
            if (cursorStack.length === currentPageIndex + 1) {
                cursorStack.push(nextCursor);
            }
        }
    } catch (e) { console.error('Error rendering transactions', e); }
};

export const fetchEvaluations = async () => {
    try {
        const cursor = evalCursorStack[currentEvalPageIndex];
        const cursorTs = cursor ? cursor.timestamp : null;
        const cursorId = cursor ? cursor.id : null;
        const data = await getEvaluations(evalLimit, 0, cursorTs, cursorId);
        const tbody = document.getElementById('evaluations-body');
        if (!tbody) return;
        tbody.innerHTML = '';

        if (data.length === 0) {
            const tr = document.createElement('tr');
            const td = document.createElement('td');
            td.colSpan = 8;
            td.style.textAlign = 'center';
            td.style.color = 'var(--text-muted)';
            td.textContent = 'No evaluations logged';
            tr.appendChild(td);
            tbody.appendChild(tr);
        } else {
            data.forEach(evalItem => {
                const tr = document.createElement('tr');
                const date = new Date(evalItem.timestamp).toLocaleString('en-US');
                
                let statusClass = 'status-no-signal';
                let statusLabel = 'No Signal';
                if (evalItem.status === 'EXECUTED') {
                    statusClass = 'status-executed';
                    statusLabel = 'Executed';
                } else if (evalItem.status === 'REJECTED') {
                    statusClass = 'status-rejected';
                    statusLabel = 'Rejected';
                } else if (evalItem.status === 'NO_SIGNAL') {
                    statusClass = 'status-no-signal';
                    statusLabel = 'No Signal';
                } else if (evalItem.status === 'WAITING_DATA') {
                    statusClass = 'status-waiting';
                    statusLabel = 'Waiting Data';
                } else if (evalItem.status === 'ERROR') {
                    statusClass = 'status-error';
                    statusLabel = 'Error';
                }

                const signalLabel = evalItem.signal_type || 'ENTRY';
                const signalClass = evalItem.signal_triggered ? 'positive' : 'text-muted';
                
                const tdDate = document.createElement('td');
                tdDate.textContent = date;
                tr.appendChild(tdDate);

                const tdAsset = document.createElement('td');
                const strongAsset = document.createElement('strong');
                strongAsset.textContent = evalItem.asset;
                tdAsset.appendChild(strongAsset);
                tr.appendChild(tdAsset);

                const tdStrat = document.createElement('td');
                tdStrat.textContent = evalItem.strategy_name;
                tr.appendChild(tdStrat);

                const tdTimeframe = document.createElement('td');
                tdTimeframe.textContent = evalItem.timeframe;
                tr.appendChild(tdTimeframe);

                const tdSignal = document.createElement('td');
                tdSignal.className = signalClass;
                if (evalItem.signal_triggered) {
                    const strongSignal = document.createElement('strong');
                    strongSignal.textContent = `${signalLabel} (Triggered)`;
                    tdSignal.appendChild(strongSignal);
                } else {
                    tdSignal.textContent = signalLabel;
                }
                tr.appendChild(tdSignal);

                const tdStatus = document.createElement('td');
                const statusSpan = document.createElement('span');
                statusSpan.className = `badge ${statusClass}`;
                statusSpan.textContent = statusLabel;
                tdStatus.appendChild(statusSpan);
                tr.appendChild(tdStatus);

                const tdPrice = document.createElement('td');
                tdPrice.textContent = evalItem.price ? formatAmountForAsset(evalItem.asset, evalItem.price) : '-';
                tr.appendChild(tdPrice);
                
                const tdReason = document.createElement('td');
                let reasonDetail = evalItem.fail_reason || '';
                if (evalItem.details && Object.keys(evalItem.details).length > 0) {
                    const tooltipSpan = document.createElement('span');
                    tooltipSpan.className = 'has-tooltip-detail';
                    tooltipSpan.textContent = reasonDetail || 'Details';
                    const tooltipTextSpan = document.createElement('span');
                    tooltipTextSpan.className = 'tooltip';
                    tooltipTextSpan.textContent = JSON.stringify(evalItem.details, null, 2);
                    tooltipSpan.appendChild(tooltipTextSpan);
                    tdReason.appendChild(tooltipSpan);
                } else {
                    tdReason.textContent = reasonDetail || '-';
                }
                tr.appendChild(tdReason);

                tbody.appendChild(tr);
            });
        }

        // Update UI pagination controls
        const prevBtn = document.getElementById('btn-eval-prev');
        const nextBtn = document.getElementById('btn-eval-next');
        const pageTxt = document.getElementById('txt-eval-page');
        
        if (prevBtn) prevBtn.disabled = currentEvalPageIndex === 0;
        if (nextBtn) nextBtn.disabled = data.length < evalLimit;
        if (pageTxt) pageTxt.textContent = `Page ${currentEvalPageIndex + 1}`;

        if (data.length === evalLimit) {
            const lastItem = data[data.length - 1];
            const nextCursor = { id: lastItem.id, timestamp: lastItem.timestamp };
            if (evalCursorStack.length === currentEvalPageIndex + 1) {
                evalCursorStack.push(nextCursor);
            }
        }
    } catch (e) { console.error('Error rendering evaluations', e); }
};

export const initLogsSSE = () => {
    const consoleOutput = document.getElementById('console-output');
    const filterInfo = document.getElementById('filter-info');
    const filterWarn = document.getElementById('filter-warn');
    const filterError = document.getElementById('filter-error');
    const autoscrollCheckbox = document.getElementById('autoscroll-logs');
    if (!consoleOutput || !filterInfo || !filterWarn || !filterError || !autoscrollCheckbox) return;
    
    const applyFilters = () => {
        const lines = consoleOutput.querySelectorAll('.log-line');
        lines.forEach(line => {
            if (line.classList.contains('info')) {
                line.style.display = filterInfo.checked ? 'block' : 'none';
            } else if (line.classList.contains('warning')) {
                line.style.display = filterWarn.checked ? 'block' : 'none';
            } else if (line.classList.contains('error')) {
                line.style.display = filterError.checked ? 'block' : 'none';
            }
        });
    };
    
    filterInfo.addEventListener('change', applyFilters);
    filterWarn.addEventListener('change', applyFilters);
    filterError.addEventListener('change', applyFilters);

    const clearBtn = document.getElementById('clear-console-btn');
    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            consoleOutput.textContent = '';
        });
    }
    
    let evtSource = null;
    let sseErrorCount = 0;
    const MAX_SSE_ERRORS = 5;
    let lastSeqReceived = 0;

    const handleSseMessage = (event) => {
        try {
            const data = JSON.parse(event.data);

            // Deduplicate by monotonic seq number — ignore replayed buffer on reconnect
            if (data.seq <= lastSeqReceived) return;
            lastSeqReceived = data.seq;
            const levelClass = data.level.toLowerCase(); // 'info', 'warning', 'error'
            
            const date = new Date(data.timestamp);
            const timeStr = date.toLocaleTimeString('en-US') + '.' + String(date.getMilliseconds()).padStart(3, '0');
            
            const line = document.createElement('div');
            line.className = `log-line ${levelClass}`;
            
            const timeSpan = document.createElement('span');
            timeSpan.className = 'log-time';
            timeSpan.textContent = `[${timeStr}] `;
            line.appendChild(timeSpan);
            
            const msgText = document.createTextNode(data.message);
            line.appendChild(msgText);
            
            // Hide if unchecked
            if (levelClass === 'info' && !filterInfo.checked) line.style.display = 'none';
            if (levelClass === 'warning' && !filterWarn.checked) line.style.display = 'none';
            if (levelClass === 'error' && !filterError.checked) line.style.display = 'none';
            
            consoleOutput.appendChild(line);
            
            // Keep DOM size down
            if (consoleOutput.children.length > 1000) {
                consoleOutput.removeChild(consoleOutput.firstElementChild);
            }
            
            // Auto scroll
            if (autoscrollCheckbox.checked) {
                consoleOutput.scrollTop = consoleOutput.scrollHeight;
            }
        } catch(e) {
            console.error("Error parsing log line", e);
        }
    };

    const startSSE = () => {
        evtSource = new EventSource('/api/logs/stream');

        evtSource.onerror = async () => {
            sseErrorCount++;
            if (sseErrorCount >= MAX_SSE_ERRORS) {
                evtSource.close();
                try {
                    const authRes = await fetch('/api/status/heartbeat');
                    if (authRes.status === 401) {
                        window.location.href = '/login.html';
                        return;
                    }
                } catch (_) { /* network down */ }
                showError("Log stream connection lost after multiple failures. Retrying in 30s...");
                setTimeout(() => {
                    sseErrorCount = 0;
                    startSSE();
                }, 30000);
            } else if (sseErrorCount === 1) {
                showError("Log stream connection lost. Attempting to reconnect...");
            }
        };

        evtSource.onopen = () => {
            if (sseErrorCount > 0) {
                showToast("Log stream connection established.", "success");
                sseErrorCount = 0;
            }
        };

        evtSource.onmessage = handleSseMessage;
    };

    // Pause SSE when tab is hidden, resume on visibility
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
            if (evtSource) {
                evtSource.close();
                evtSource = null;
            }
        } else {
            if (!evtSource) {
                sseErrorCount = 0;
                startSSE();
            }
        }
    });

    startSSE();
};
