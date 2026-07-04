import { 
    getPortfolio, 
    getPositions, 
    getConfigs, 
    updateConfig, 
    toggleConfig, 
    getTransactions, 
    getEvaluations, 
    getHeartbeat, 
    executePanic 
} from './js/api.js';

import { 
    formatCurrency, 
    formatPercent, 
    formatUSDT, 
    showToast, 
    showError, 
    setButtonLoading 
} from './js/ui.js';

import { 
    loadChart, 
    invalidateChartCache 
} from './js/chart.js';

// Local state for pagination and polling checks
let txPage = 1;
const txLimit = 50;
let evalPage = 1;
const evalLimit = 100;

let lastTransactionTime = null;
let lastEvaluationTime = null;
let lastPriceTime = null;

let cachedConfigs = null;
let cachedTransactions = null;

document.addEventListener('DOMContentLoaded', () => {
    // Navigation Logic
    const navItems = document.querySelectorAll('.nav-item');
    const sections = document.querySelectorAll('.view-section');

    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            const targetId = item.getAttribute('data-target');
            if (!targetId) return; // Allow normal link behavior (e.g. Logout)
            
            e.preventDefault();
            
            navItems.forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');

            sections.forEach(sec => sec.classList.remove('active'));
            const targetSection = document.getElementById(targetId);
            if (targetSection) {
                targetSection.classList.add('active');
            }

            // Immediate fetch on tab change
            if (targetId === 'dashboard') {
                fetchPortfolio();
                fetchPositions();
            } else if (targetId === 'configs') {
                fetchConfigs();
            } else if (targetId === 'transactions') {
                fetchTransactions();
            } else if (targetId === 'evaluations') {
                fetchEvaluations();
            }
        });
    });

    // Data Fetching and DOM Rendering Functions
    const fetchPortfolio = async () => {
        try {
            const data = await getPortfolio();
            
            // Stocks (Trading 212)
            const t212 = data.trading212 || { total_nav: 0, cash_balance: 0, allocated_balance: 0 };
            document.getElementById('kpi-t212-nav').textContent = formatCurrency(t212.total_nav);
            document.getElementById('kpi-t212-cash').textContent = formatCurrency(t212.cash_balance);
            document.getElementById('kpi-t212-allocated').textContent = formatCurrency(t212.allocated_balance);
            
            // Crypto (Bybit)
            const bybit = data.bybit || { total_nav: 0, cash_balance: 0, allocated_balance: 0, secured_balance: 0 };
            document.getElementById('kpi-bybit-nav').textContent = formatUSDT(bybit.total_nav);
            document.getElementById('kpi-bybit-cash').textContent = formatUSDT(bybit.cash_balance);
            document.getElementById('kpi-bybit-allocated').textContent = formatUSDT(bybit.allocated_balance);
            document.getElementById('kpi-bybit-secured').textContent = formatCurrency(bybit.secured_balance || 0);
        } catch (e) { console.error('Error rendering portfolio', e); }
    };

    const fetchPositions = async () => {
        try {
            const data = await getPositions();
            const tbody = document.getElementById('positions-body');
            tbody.innerHTML = '';
            let totalT212Pnl = 0;
            let totalBybitPnl = 0;

            if (data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--text-muted)">No open positions</td></tr>';
            } else {
                data.forEach(pos => {
                    const isCrypto = pos.asset.toLowerCase().endsWith("usdt");
                    let pnlStr = '';
                    if (isCrypto) {
                        totalBybitPnl += pos.pnl;
                        pnlStr = formatUSDT(pos.pnl);
                    } else {
                        totalT212Pnl += pos.pnl;
                        pnlStr = formatCurrency(pos.pnl);
                    }
                    
                    const pnlClass = pos.pnl >= 0 ? 'positive' : 'negative';
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td><strong>${pos.asset}</strong></td>
                        <td>${pos.strategy_name}</td>
                        <td>${pos.qty}</td>
                        <td>${isCrypto ? formatUSDT(pos.entry_price) : formatCurrency(pos.entry_price)}</td>
                        <td>${isCrypto ? formatUSDT(pos.current_price) : formatCurrency(pos.current_price)}</td>
                        <td class="${pnlClass}">${pnlStr}</td>
                    `;
                    tbody.appendChild(tr);
                });
            }

            const t212PnlEl = document.getElementById('kpi-t212-pnl');
            t212PnlEl.textContent = formatCurrency(totalT212Pnl);
            t212PnlEl.className = 'kpi-value ' + (totalT212Pnl >= 0 ? 'positive' : 'negative');

            const bybitPnlEl = document.getElementById('kpi-bybit-pnl');
            bybitPnlEl.textContent = formatUSDT(totalBybitPnl);
            bybitPnlEl.className = 'kpi-value ' + (totalBybitPnl >= 0 ? 'positive' : 'negative');
        } catch (e) { console.error('Error rendering positions', e); }
    };

    const fetchConfigs = async () => {
        try {
            let data;
            if (cachedConfigs) {
                data = cachedConfigs;
            } else {
                data = await getConfigs();
                cachedConfigs = data;
            }
            
            const tbody = document.getElementById('configs-body');
            tbody.innerHTML = '';

            data.forEach(conf => {
                const tr = document.createElement('tr');
                let statusBadge = '';
                if (conf.status === 'active') {
                    statusBadge = '<span class="badge active">Active</span>';
                } else if (conf.status === 'inactive') {
                    statusBadge = '<span class="badge inactive">Inactive</span>';
                } else if (conf.status === 'waiting_data') {
                    statusBadge = '<span class="badge warning">En attente</span>';
                } else if (conf.status === 'error') {
                    if (conf.last_error) {
                        statusBadge = `<span class="badge error has-tooltip">Erreur<span class="tooltip">${conf.last_error}</span></span>`;
                    } else {
                        statusBadge = '<span class="badge error">Erreur</span>';
                    }
                } else {
                    statusBadge = `<span class="badge inactive">${conf.status || 'Inactive'}</span>`;
                }

                const marketDot = conf.market_open 
                    ? '<span class="market-status open" title="Marché Ouvert">●</span>' 
                    : '<span class="market-status closed" title="Marché Fermé">●</span>';

                // Strategy Toggle Switch HTML
                const toggleSwitch = `
                    <label class="switch" title="Pause / Resume Strategy">
                        <input type="checkbox" class="toggle-strategy-active" data-id="${conf.id}" ${conf.is_active ? 'checked' : ''}>
                        <span class="slider round"></span>
                    </label>
                `;

                tr.innerHTML = `
                    <td>${conf.id}</td>
                    <td><strong>${conf.strategy_name}</strong></td>
                    <td>${conf.asset} ${marketDot}</td>
                    <td>${conf.timeframe}</td>
                    <td>${formatCurrency(conf.initial_capital)}</td>
                    <td>${formatCurrency(conf.initial_capital_bucket)}</td>
                    <td>${formatCurrency(conf.max_capital_bucket)}</td>
                    <td>${conf.asset.toLowerCase().endsWith('usdt') ? formatUSDT(conf.max_entry_price) : formatCurrency(conf.max_entry_price)}</td>
                    <td>${statusBadge}</td>
                    <td>${toggleSwitch}</td>
                    <td><button class="btn-edit" data-conf='${JSON.stringify(conf)}'>Edit</button></td>
                `;
                tbody.appendChild(tr);
            });

            // Bind Asset Select Dropdown if empty
            const selector = document.getElementById('asset-selector');
            if (selector && selector.options.length <= 1) {
                const assets = [...new Set(data.map(c => c.asset))];
                assets.forEach(asset => {
                    const opt = document.createElement('option');
                    opt.value = asset;
                    opt.textContent = asset;
                    selector.appendChild(opt);
                });
            }

            // Bind strategy toggle switches
            document.querySelectorAll('.toggle-strategy-active').forEach(checkbox => {
                checkbox.addEventListener('change', async (e) => {
                    const id = e.target.getAttribute('data-id');
                    const isActive = e.target.checked;
                    
                    try {
                        const res = await toggleConfig(id, isActive);
                        if (res.ok) {
                            cachedConfigs = null; // Invalidate cache
                            fetchConfigs(); // reload statuses
                        } else {
                            showError('Impossible de modifier le statut de la stratégie.', `Status code: ${res.status}`);
                            e.target.checked = !isActive;
                        }
                    } catch(err) {
                        showError('Une erreur est survenue lors de la modification du statut de la stratégie.', err);
                        e.target.checked = !isActive;
                    }
                });
            });

            // Bind edit buttons
            document.querySelectorAll('.btn-edit').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const conf = JSON.parse(e.target.getAttribute('data-conf'));
                    openEditModal(conf);
                });
            });
        } catch (e) { console.error('Error rendering configs', e); }
    };

    const fetchTransactions = async () => {
        try {
            const data = await getTransactions(txLimit, (txPage - 1) * txLimit);
            const tbody = document.getElementById('transactions-body');
            tbody.innerHTML = '';

            if (data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: var(--text-muted)">No recent transactions</td></tr>';
            } else {
                data.forEach(tx => {
                    const tr = document.createElement('tr');
                    const date = new Date(tx.timestamp).toLocaleString('fr-FR');
                    const actionClass = tx.action === 'BUY' ? 'positive' : 'negative';
                    tr.innerHTML = `
                        <td>${date}</td>
                        <td><strong>${tx.asset}</strong></td>
                        <td>${tx.strategy_name}</td>
                        <td class="${actionClass}">${tx.action}</td>
                        <td>${tx.qty}</td>
                        <td>${formatCurrency(tx.price)}</td>
                        <td>${formatCurrency(tx.total_value)}</td>
                    `;
                    tbody.appendChild(tr);
                });
            }
            
            // Update UI pagination controls
            const prevBtn = document.getElementById('btn-tx-prev');
            const nextBtn = document.getElementById('btn-tx-next');
            const pageTxt = document.getElementById('txt-tx-page');
            
            if (prevBtn) prevBtn.disabled = txPage === 1;
            if (nextBtn) nextBtn.disabled = data.length < txLimit;
            if (pageTxt) pageTxt.textContent = `Page ${txPage}`;
        } catch (e) { console.error('Error rendering transactions', e); }
    };

    const fetchEvaluations = async () => {
        try {
            const data = await getEvaluations(evalLimit, (evalPage - 1) * evalLimit);
            const tbody = document.getElementById('evaluations-body');
            tbody.innerHTML = '';

            if (data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; color: var(--text-muted)">No evaluations logged</td></tr>';
            } else {
                data.forEach(evalItem => {
                    const tr = document.createElement('tr');
                    const date = new Date(evalItem.timestamp).toLocaleString('fr-FR');
                    
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
                    const displaySignal = evalItem.signal_triggered ? `<strong>${signalLabel} (Triggered)</strong>` : signalLabel;

                    const priceStr = evalItem.price ? formatCurrency(evalItem.price) : '-';
                    
                    // Reason and detail formatting
                    let reasonDetail = evalItem.fail_reason || '';
                    if (evalItem.details && Object.keys(evalItem.details).length > 0) {
                        const tooltipText = JSON.stringify(evalItem.details, null, 2);
                        reasonDetail = `<span class="has-tooltip-detail">${reasonDetail || 'Details'}<span class="tooltip">${tooltipText}</span></span>`;
                    }
                    if (!reasonDetail) reasonDetail = '-';

                    tr.innerHTML = `
                        <td>${date}</td>
                        <td><strong>${evalItem.asset}</strong></td>
                        <td>${evalItem.strategy_name}</td>
                        <td>${evalItem.timeframe}</td>
                        <td class="${signalClass}">${displaySignal}</td>
                        <td><span class="badge ${statusClass}">${statusLabel}</span></td>
                        <td>${priceStr}</td>
                        <td>${reasonDetail}</td>
                    `;
                    tbody.appendChild(tr);
                });
            }

            // Update UI pagination controls
            const prevBtn = document.getElementById('btn-eval-prev');
            const nextBtn = document.getElementById('btn-eval-next');
            const pageTxt = document.getElementById('txt-eval-page');
            
            if (prevBtn) prevBtn.disabled = evalPage === 1;
            if (nextBtn) nextBtn.disabled = data.length < evalLimit;
            if (pageTxt) pageTxt.textContent = `Page ${evalPage}`;
        } catch (e) { console.error('Error rendering evaluations', e); }
    };

    // Modal Logic for Config Editing
    const modal = document.getElementById('edit-modal');
    const closeBtn = document.querySelector('.close-modal');
    const form = document.getElementById('config-form');

    const openEditModal = (conf) => {
        document.getElementById('edit-id').value = conf.id;
        document.getElementById('edit-initial-cap').value = conf.initial_capital;
        document.getElementById('edit-initial-bucket').value = conf.initial_capital_bucket;
        document.getElementById('edit-max-bucket').value = conf.max_capital_bucket;
        document.getElementById('edit-max-entry').value = conf.max_entry_price;
        document.getElementById('edit-is-active').checked = conf.is_active;
        document.getElementById('edit-indicator-params').value = JSON.stringify(conf.indicator_params || {}, null, 2);
        modal.style.display = 'flex';
    };

    closeBtn.onclick = () => modal.style.display = 'none';
    window.onclick = (e) => { if (e.target === modal) modal.style.display = 'none'; };

    form.onsubmit = async (e) => {
        e.preventDefault();
        const id = document.getElementById('edit-id').value;
        const submitBtn = form.querySelector('button[type="submit"]');
        
        let indicatorParams = {};
        try {
            const rawVal = document.getElementById('edit-indicator-params').value.trim();
            indicatorParams = rawVal ? JSON.parse(rawVal) : {};
        } catch (err) {
            showToast('Format JSON invalide dans les paramètres d\'indicateur.', 'error');
            return;
        }

        const initialCap = parseFloat(document.getElementById('edit-initial-cap').value);
        const initialBucket = parseFloat(document.getElementById('edit-initial-bucket').value);
        const maxBucket = parseFloat(document.getElementById('edit-max-bucket').value);
        const maxEntry = parseFloat(document.getElementById('edit-max-entry').value);

        if (isNaN(initialCap) || initialCap <= 0) {
            showToast('Le capital initial doit être un nombre supérieur à 0.', 'error');
            return;
        }
        if (isNaN(initialBucket) || initialBucket <= 0) {
            showToast('Le bucket de capital initial doit être un nombre supérieur à 0.', 'error');
            return;
        }
        if (isNaN(maxBucket) || maxBucket <= 0) {
            showToast('Le bucket de capital maximum doit être un nombre supérieur à 0.', 'error');
            return;
        }
        if (isNaN(maxEntry) || maxEntry <= 0) {
            showToast('Le prix d\'entrée maximum doit être un nombre supérieur à 0.', 'error');
            return;
        }
        if (initialBucket > maxBucket) {
            showToast('Le bucket de capital initial ne peut pas dépasser le bucket maximum.', 'error');
            return;
        }

        const payload = {
            initial_capital: initialCap,
            initial_capital_bucket: initialBucket,
            max_capital_bucket: maxBucket,
            max_entry_price: maxEntry,
            is_active: document.getElementById('edit-is-active').checked,
            indicator_params: indicatorParams
        };

        setButtonLoading(submitBtn, true, 'Saving...');

        try {
            const res = await updateConfig(id, payload);
            if (res.ok) {
                modal.style.display = 'none';
                showToast('Configuration mise à jour avec succès.', 'success');
                cachedConfigs = null;
                fetchConfigs();
            } else {
                showError('Impossible de mettre à jour la configuration.', `Status code: ${res.status}`);
            }
        } catch (err) {
            showError('Une erreur est survenue lors de la mise à jour de la configuration.', err);
        } finally {
            setButtonLoading(submitBtn, false);
        }
    };

    // Heartbeat Status polling
    const fetchHeartbeat = async () => {
        try {
            const data = await getHeartbeat();
            
            ['trading212', 'bybit'].forEach(source => {
                const hbDot = document.getElementById(`hb-${source}`);
                const status = data[source] ? data[source].status : 'offline';
                const lastUpdate = data[source] ? data[source].last_update : null;
                const secondsAgo = data[source] ? data[source].seconds_ago : null;
                
                hbDot.className = `heartbeat-dot ${status}`;
                
                // Update tooltip text
                const container = document.getElementById(`hb-${source}-container`);
                if (container) {
                    if (status === 'offline') {
                        container.title = `${source.toUpperCase()} Price Feed: OFFLINE`;
                    } else {
                        const timeStr = lastUpdate ? new Date(lastUpdate).toLocaleTimeString('fr-FR') : '-';
                        container.title = `${source.toUpperCase()} Feed: ${status.toUpperCase()}\nLast Tick: ${timeStr} (${Math.round(secondsAgo)}s ago)`;
                    }
                }
            });

            // Return dirty flags comparing timestamps
            const changed = {
                transactions: data.last_transaction_time !== lastTransactionTime,
                evaluations: data.last_evaluation_time !== lastEvaluationTime,
                price: data.last_price_time !== lastPriceTime
            };

            // Update cache timestamps
            lastTransactionTime = data.last_transaction_time;
            lastEvaluationTime = data.last_evaluation_time;
            lastPriceTime = data.last_price_time;

            return changed;
        } catch(e) {
            console.error("Error fetching heartbeat status", e);
            return { transactions: true, evaluations: true, price: true };
        }
    };

    // Panic liquidation close modal
    const initPanicButton = () => {
        const panicBtn = document.getElementById('panic-btn');
        const panicModal = document.getElementById('panic-modal');
        const closeSpan = document.getElementById('close-panic-modal');
        const cancelBtn = document.getElementById('cancel-panic-btn');
        const executeBtn = document.getElementById('execute-panic-btn');
        const confirm1 = document.getElementById('panic-confirm-1');
        const confirm2 = document.getElementById('panic-confirm-2');
        
        panicBtn.addEventListener('click', () => {
            panicModal.style.display = 'flex';
            confirm1.checked = false;
            confirm2.checked = false;
            executeBtn.disabled = true;
        });
        
        const checkConfirmation = () => {
            executeBtn.disabled = !(confirm1.checked && confirm2.checked);
        };
        
        confirm1.addEventListener('change', checkConfirmation);
        confirm2.addEventListener('change', checkConfirmation);
        
        const closeModal = () => {
            panicModal.style.display = 'none';
        };
        
        closeSpan.addEventListener('click', closeModal);
        cancelBtn.addEventListener('click', closeModal);
        window.addEventListener('click', (e) => {
            if (e.target === panicModal) closeModal();
        });
        
        executeBtn.addEventListener('click', async () => {
            setButtonLoading(executeBtn, true, 'LIQUIDATING...');
            
            try {
                const res = await executePanic();
                if (res.ok) {
                    const data = await res.json();
                    showToast(`Liquidation d'urgence réussie ! ${data.closed_positions_count} positions fermées.`, 'success');
                    closeModal();
                    
                    // Invalidate caches
                    cachedTransactions = null;
                    cachedConfigs = null;
                    lastTransactionTime = null; // Force dirty next check
                    invalidateChartCache();
                    
                    // Reload all metrics
                    fetchPortfolio();
                    fetchPositions();
                    fetchTransactions();
                    
                    const selector = document.getElementById('asset-selector');
                    if (selector && selector.value) {
                        loadChart(selector.value);
                    }
                } else {
                    showError('Échec de la liquidation d\'urgence.', `Status code: ${res.status}`);
                }
            } catch(err) {
                showError('Une erreur est survenue lors de la liquidation d\'urgence.', err);
            } finally {
                setButtonLoading(executeBtn, false);
                checkConfirmation();
            }
        });
    };

    // System Log stream client
    const initLogsSSE = () => {
        const consoleOutput = document.getElementById('console-output');
        const filterInfo = document.getElementById('filter-info');
        const filterWarn = document.getElementById('filter-warn');
        const filterError = document.getElementById('filter-error');
        const autoscrollCheckbox = document.getElementById('autoscroll-logs');
        
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
        
        const evtSource = new EventSource('/api/logs/stream');
        
        evtSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                const levelClass = data.level.toLowerCase(); // 'info', 'warning', 'error'
                
                const date = new Date(data.timestamp);
                const timeStr = date.toLocaleTimeString('fr-FR') + '.' + String(date.getMilliseconds()).padStart(3, '0');
                
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
                if (consoleOutput.childNodes.length > 1000) {
                    consoleOutput.removeChild(consoleOutput.firstChild);
                }
                
                // Auto scroll
                if (autoscrollCheckbox.checked) {
                    consoleOutput.scrollTop = consoleOutput.scrollHeight;
                }
            } catch(e) {
                console.error("Error parsing log line", e);
            }
        };
        
        evtSource.onerror = (err) => {
            console.error("Logs SSE stream error:", err);
        };
    };

    // Initialize Dashboard
    const init = () => {
        fetchPortfolio();
        fetchPositions();
        fetchConfigs();
        fetchTransactions();
        fetchEvaluations();
        fetchHeartbeat();
        
        // Connect SSE and Panic buttons
        initLogsSSE();
        initPanicButton();
        
        // Dropdown Asset Selection event
        const selector = document.getElementById('asset-selector');
        selector.addEventListener('change', (e) => {
            loadChart(e.target.value, true);
        });

        // Bind Pagination Button Clicks
        const txPrev = document.getElementById('btn-tx-prev');
        const txNext = document.getElementById('btn-tx-next');
        const evalPrev = document.getElementById('btn-eval-prev');
        const evalNext = document.getElementById('btn-eval-next');
        
        if (txPrev) {
            txPrev.addEventListener('click', () => {
                if (txPage > 1) {
                    txPage--;
                    fetchTransactions();
                }
            });
        }
        if (txNext) {
            txNext.addEventListener('click', () => {
                txPage++;
                fetchTransactions();
            });
        }
        if (evalPrev) {
            evalPrev.addEventListener('click', () => {
                if (evalPage > 1) {
                    evalPage--;
                    fetchEvaluations();
                }
            });
        }
        if (evalNext) {
            evalNext.addEventListener('click', () => {
                evalPage++;
                fetchEvaluations();
            });
        }
    };

    init();

    // Poll status and metrics every 10 seconds
    setInterval(async () => {
        const changed = await fetchHeartbeat();
        
        // Refresh positions/portfolio if prices updated
        if (changed.price) {
            fetchPortfolio();
            fetchPositions();
        }
        
        // Refresh evaluations if new evaluations are available
        if (changed.evaluations) {
            fetchEvaluations();
        }
        
        // If an asset is currently selected, refresh its chart and metrics
        const selector = document.getElementById('asset-selector');
        if (selector && selector.value) {
            // Reload chart only if prices or transactions changed
            if (changed.price || changed.transactions) {
                loadChart(selector.value, false);
            }
        }
    }, 10000);
});
