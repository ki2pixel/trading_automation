document.addEventListener('DOMContentLoaded', () => {
    // Navigation Logic
    const navItems = document.querySelectorAll('.nav-item');
    const sections = document.querySelectorAll('.view-section');

    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = item.getAttribute('data-target');
            
            navItems.forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');

            sections.forEach(sec => sec.classList.remove('active'));
            document.getElementById(targetId).classList.add('active');

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

    // Formatting utilities
    const formatCurrency = (val) => new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(val);
    const formatPercent = (val) => new Intl.NumberFormat('fr-FR', { style: 'percent', minimumFractionDigits: 2 }).format(val);
    const formatUSDT = (val) => new Intl.NumberFormat('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(val) + ' USDT';

    // Data Fetching
    const fetchPortfolio = async () => {
        try {
            const res = await fetch('/api/portfolio');
            const data = await res.json();
            
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
        } catch (e) { console.error('Error fetching portfolio', e); }
    };

    const fetchPositions = async () => {
        try {
            const res = await fetch('/api/positions');
            const data = await res.json();
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
        } catch (e) { console.error('Error fetching positions', e); }
    };

    const fetchConfigs = async () => {
        try {
            const res = await fetch('/api/configs');
            const data = await res.json();
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
                    <td><div style="display: flex; align-items: center; gap: 8px;">${toggleSwitch} ${statusBadge}</div></td>
                    <td><button class="btn-edit" data-conf='${JSON.stringify(conf)}'>Edit</button></td>
                `;
                tbody.appendChild(tr);
            });

            // Populate asset selector dynamically if not loaded yet
            const selector = document.getElementById('asset-selector');
            if (selector && selector.options.length <= 1 && data.length > 0) {
                const uniqueAssets = [...new Set(data.map(conf => conf.asset))].sort();
                uniqueAssets.forEach(asset => {
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
                        const res = await fetch(`/api/configs/${id}/toggle`, {
                            method: 'PUT',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ is_active: isActive })
                        });
                        
                        if (res.ok) {
                            fetchConfigs(); // reload statuses
                        } else {
                            alert('Failed to toggle strategy active status.');
                            e.target.checked = !isActive;
                        }
                    } catch(err) {
                        console.error("Toggle strategy error", err);
                        alert('Error toggling strategy status.');
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
        } catch (e) { console.error('Error fetching configs', e); }
    };

    const fetchTransactions = async () => {
        try {
            const res = await fetch('/api/transactions');
            const data = await res.json();
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
        } catch (e) { console.error('Error fetching transactions', e); }
    };

    const fetchEvaluations = async () => {
        try {
            const res = await fetch('/api/evaluations?limit=100');
            const data = await res.json();
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
        } catch (e) { console.error('Error fetching evaluations', e); }
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
        
        let indicatorParams = {};
        try {
            const rawVal = document.getElementById('edit-indicator-params').value.trim();
            indicatorParams = rawVal ? JSON.parse(rawVal) : {};
        } catch (err) {
            alert('Invalid JSON in Indicator Parameters.');
            return;
        }

        const payload = {
            initial_capital: parseFloat(document.getElementById('edit-initial-cap').value),
            initial_capital_bucket: parseFloat(document.getElementById('edit-initial-bucket').value),
            max_capital_bucket: parseFloat(document.getElementById('edit-max-bucket').value),
            max_entry_price: parseFloat(document.getElementById('edit-max-entry').value),
            is_active: document.getElementById('edit-is-active').checked,
            indicator_params: indicatorParams
        };

        try {
            const res = await fetch(`/api/configs/${id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (res.ok) {
                modal.style.display = 'none';
                fetchConfigs();
            } else {
                alert('Failed to update configuration.');
            }
        } catch (e) {
            console.error(e);
            alert('Error updating configuration.');
        }
    };

    // Heartbeat Status polling
    const fetchHeartbeat = async () => {
        try {
            const res = await fetch('/api/status/heartbeat');
            const data = await res.json();
            
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
        } catch(e) {
            console.error("Error fetching heartbeat status", e);
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
            executeBtn.disabled = true;
            executeBtn.textContent = 'LIQUIDATING...';
            
            try {
                const res = await fetch('/api/control/panic', { method: 'POST' });
                if (res.ok) {
                    const data = await res.json();
                    alert(`Panic Close Success! Closed ${data.closed_positions_count} open positions.`);
                    closeModal();
                    
                    // Reload all metrics
                    fetchPortfolio();
                    fetchPositions();
                    fetchTransactions();
                    
                    const selector = document.getElementById('asset-selector');
                    if (selector && selector.value) {
                        loadChart(selector.value);
                    }
                } else {
                    alert('Panic close failed. Check server logs.');
                }
            } catch(err) {
                console.error("Panic close request error", err);
                alert('An error occurred during panic liquidation.');
            } finally {
                executeBtn.textContent = 'EXECUTE LIQUIDATION';
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
        const clearBtn = document.getElementById('clear-console-btn');
        
        clearBtn.addEventListener('click', () => {
            consoleOutput.innerHTML = '<div class="log-line info"><span class="log-time">[System]</span> Console cleared.</div>';
        });
        
        const applyFilters = () => {
            const showInfo = filterInfo.checked;
            const showWarn = filterWarn.checked;
            const showError = filterError.checked;
            
            document.querySelectorAll('.log-line').forEach(line => {
                if (line.classList.contains('info')) {
                    line.style.display = showInfo ? 'block' : 'none';
                } else if (line.classList.contains('warning')) {
                    line.style.display = showWarn ? 'block' : 'none';
                } else if (line.classList.contains('error')) {
                    line.style.display = showError ? 'block' : 'none';
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
                line.innerHTML = `<span class="log-time">[${timeStr}]</span> ${data.message}`;
                
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

    // Interactive Lightweight Charts and Metrics Engine
    let currentChart = null;
    let candleSeries = null;
    let equitySeries = null;
    let bhSeries = null;

    const loadChart = async (ticker) => {
        if (!ticker) {
            document.getElementById('analytics-grid').style.display = 'none';
            document.getElementById('chart-placeholder').style.display = 'flex';
            document.getElementById('price-chart').style.display = 'none';
            return;
        }
        
        document.getElementById('chart-placeholder').style.display = 'none';
        document.getElementById('price-chart').style.display = 'block';
        document.getElementById('analytics-grid').style.display = 'grid';
        
        const chartContainer = document.getElementById('price-chart');
        if (currentChart) {
            try {
                currentChart.remove();
            } catch(e) { console.error("Error destroying chart", e); }
            currentChart = null;
        }
        
        // Init Lightweight Chart
        currentChart = LightweightCharts.createChart(chartContainer, {
            layout: {
                backgroundColor: '#070a13',
                textColor: '#64748b',
                fontSize: 11,
                fontFamily: 'Inter, sans-serif',
            },
            grid: {
                vertLines: { color: 'rgba(255, 255, 255, 0.02)' },
                horzLines: { color: 'rgba(255, 255, 255, 0.02)' },
            },
            crosshair: {
                mode: LightweightCharts.CrosshairMode.Normal,
            },
            rightPriceScale: {
                borderColor: 'rgba(255, 255, 255, 0.08)',
                autoScale: true,
            },
            timeScale: {
                borderColor: 'rgba(255, 255, 255, 0.08)',
                timeVisible: true,
                secondsVisible: false,
            },
        });
        
        // Candle series on the right price scale
        candleSeries = currentChart.addCandlestickSeries({
            upColor: '#10b981',
            downColor: '#ef4444',
            borderUpColor: '#10b981',
            borderDownColor: '#ef4444',
            wickUpColor: '#10b981',
            wickDownColor: '#ef4444',
        });
        
        // Account Equity curves on the left price scale
        equitySeries = currentChart.addLineSeries({
            color: '#3b82f6',
            lineWidth: 2,
            priceScaleId: 'equity',
            title: 'Strategy NAV',
        });
        
        bhSeries = currentChart.addLineSeries({
            color: '#8b5cf6',
            lineWidth: 1.5,
            priceScaleId: 'equity',
            title: 'Buy & Hold NAV',
        });
        
        currentChart.priceScale('equity').applyOptions({
            side: 'left',
            autoScale: true,
            borderColor: 'rgba(255, 255, 255, 0.08)',
        });
        
        try {
            // Fetch candles
            const candlesRes = await fetch(`/api/candles?ticker=${ticker}`);
            const candlesData = await candlesRes.json();
            
            if (candlesData.length === 0) {
                console.warn("No candle data fetched for active asset", ticker);
                return;
            }
            
            candleSeries.setData(candlesData);
            
            // Fetch Transactions for marker and metrics overlays
            const txRes = await fetch('/api/transactions');
            const txData = await txRes.json();
            
            // Fetch Configs to read Initial Capital
            const configsRes = await fetch('/api/configs');
            const configsData = await configsRes.json();
            
            const activeConfig = configsData.find(c => c.asset.toLowerCase() === ticker.toLowerCase());
            const initialCapital = activeConfig ? activeConfig.initial_capital : 1000.0;
            
            // Filter transactions matching this asset
            const assetTxs = txData.filter(tx => tx.asset.toLowerCase() === ticker.toLowerCase());
            
            // Sort ascending chronologically
            const sortedTxs = [...assetTxs].sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
            
            // FIFO closed trade analysis
            const buyQueue = [];
            const closedTrades = [];
            
            sortedTxs.forEach(tx => {
                if (tx.action === 'BUY') {
                    buyQueue.push({ qty: tx.qty, price: tx.price });
                } else if (tx.action === 'SELL') {
                    let sellQty = tx.qty;
                    let totalBuyCost = 0;
                    
                    while (sellQty > 0 && buyQueue.length > 0) {
                        const oldestBuy = buyQueue[0];
                        if (oldestBuy.qty <= sellQty) {
                            totalBuyCost += oldestBuy.qty * oldestBuy.price;
                            sellQty -= oldestBuy.qty;
                            buyQueue.shift();
                        } else {
                            totalBuyCost += sellQty * oldestBuy.price;
                            oldestBuy.qty -= sellQty;
                            sellQty = 0;
                        }
                    }
                    
                    const sellRevenue = tx.total_value; // Net revenue
                    const pnl = sellRevenue - totalBuyCost;
                    closedTrades.push({ pnl: pnl, costBasis: totalBuyCost });
                }
            });
            
            // Compute KPI metrics
            let wins = 0;
            let totalProfit = 0;
            let totalLosses = 0;
            let netProfit = 0;
            
            closedTrades.forEach(t => {
                netProfit += t.pnl;
                if (t.pnl > 0) {
                    wins++;
                    totalProfit += t.pnl;
                } else {
                    totalLosses += Math.abs(t.pnl);
                }
            });
            
            const totalTrades = closedTrades.length;
            const winRate = totalTrades > 0 ? (wins / totalTrades) : 0;
            const profitFactor = totalLosses > 0 ? (totalProfit / totalLosses) : (totalProfit > 0 ? Infinity : 1.0);
            
            // Reconstruct Account Value Curves over candle intervals
            let cash = initialCapital;
            let qty = 0;
            let txIdx = 0;
            
            const strategyCurve = [];
            const buyHoldCurve = [];
            
            let firstBuyPrice = null;
            if (sortedTxs.length > 0 && sortedTxs[0].action === 'BUY') {
                firstBuyPrice = sortedTxs[0].price;
            }
            
            candlesData.forEach(c => {
                const candleTimeMs = c.time * 1000;
                
                // Process any transactions that occurred up to this candle's timestamp
                while (txIdx < sortedTxs.length && new Date(sortedTxs[txIdx].timestamp).getTime() <= candleTimeMs) {
                    const tx = sortedTxs[txIdx];
                    if (tx.action === 'BUY') {
                        cash -= tx.total_value;
                        qty += tx.qty;
                        if (firstBuyPrice === null) firstBuyPrice = tx.price;
                    } else if (tx.action === 'SELL') {
                        cash += tx.total_value;
                        qty -= tx.qty;
                    }
                    txIdx++;
                }
                
                const currentNav = cash + qty * c.close;
                strategyCurve.push({ time: c.time, value: currentNav });
                
                let bhNav = initialCapital;
                if (firstBuyPrice !== null && firstBuyPrice > 0) {
                    bhNav = initialCapital * (c.close / firstBuyPrice);
                }
                buyHoldCurve.push({ time: c.time, value: bhNav });
            });
            
            equitySeries.setData(strategyCurve);
            bhSeries.setData(buyHoldCurve);
            
            // Calculate Drawdowns
            let peak = -Infinity;
            let maxDrawdown = 0;
            let currentDrawdown = 0;
            
            strategyCurve.forEach(pt => {
                if (pt.value > peak) peak = pt.value;
                const dd = peak > 0 ? ((peak - pt.value) / peak) * 100 : 0;
                if (dd > maxDrawdown) maxDrawdown = dd;
                currentDrawdown = dd;
            });
            
            // Render KPI metrics cards
            document.getElementById('analytic-winrate').textContent = formatPercent(winRate);
            document.getElementById('analytic-profitfactor').textContent = profitFactor === Infinity ? '∞' : profitFactor.toFixed(2);
            document.getElementById('analytic-maxdd').textContent = maxDrawdown.toFixed(2) + '%';
            document.getElementById('analytic-currentdd').textContent = currentDrawdown.toFixed(2) + '%';
            
            const isCrypto = ticker.toLowerCase().endsWith('usdt');
            const totalProfitEl = document.getElementById('analytic-totalprofit');
            totalProfitEl.textContent = isCrypto ? formatUSDT(netProfit) : formatCurrency(netProfit);
            totalProfitEl.className = 'kpi-value ' + (netProfit >= 0 ? 'positive' : 'negative');
            
            document.getElementById('analytic-tradescount').textContent = totalTrades;
            
            // Add BUY / SELL Markers to chart
            const markers = [];
            sortedTxs.forEach(tx => {
                const txTimeSecs = Math.floor(new Date(tx.timestamp).getTime() / 1000);
                const candleMinSecs = Math.floor(txTimeSecs / 60) * 60; // align to minute candle
                
                if (tx.action === 'BUY') {
                    markers.push({
                        time: candleMinSecs,
                        position: 'belowBar',
                        color: '#10b981',
                        shape: 'arrowUp',
                        text: 'BUY'
                    });
                } else if (tx.action === 'SELL') {
                    markers.push({
                        time: candleMinSecs,
                        position: 'aboveBar',
                        color: '#ef4444',
                        shape: 'arrowDown',
                        text: 'SELL'
                    });
                }
            });
            
            markers.sort((a, b) => a.time - b.time);
            
            // Deduplicate markers on matching timestamps
            const uniqueMarkers = [];
            const seenTimes = new Set();
            markers.forEach(m => {
                if (!seenTimes.has(m.time)) {
                    seenTimes.add(m.time);
                    uniqueMarkers.push(m);
                }
            });
            
            candleSeries.setMarkers(uniqueMarkers);
            
        } catch(err) {
            console.error("Error generating chart overlays", err);
        }
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
            loadChart(e.target.value);
        });
    };

    init();

    // Poll status and metrics every 10 seconds
    setInterval(() => {
        fetchPortfolio();
        fetchPositions();
        fetchEvaluations();
        fetchHeartbeat();
        
        // If an asset is currently selected, refresh its chart and metrics
        const selector = document.getElementById('asset-selector');
        if (selector && selector.value) {
            // Keep the chart scroll state by reloading data on existing series if possible, 
            // but simple reload is safe and handles updates.
            loadChart(selector.value);
        }
    }, 10000);
});
