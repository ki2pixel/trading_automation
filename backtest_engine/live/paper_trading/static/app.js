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
            const bybit = data.bybit || { total_nav: 0, cash_balance: 0, allocated_balance: 0 };
            document.getElementById('kpi-bybit-nav').textContent = formatUSDT(bybit.total_nav);
            document.getElementById('kpi-bybit-cash').textContent = formatUSDT(bybit.cash_balance);
            document.getElementById('kpi-bybit-allocated').textContent = formatUSDT(bybit.allocated_balance);
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

                tr.innerHTML = `
                    <td>${conf.id}</td>
                    <td><strong>${conf.strategy_name}</strong></td>
                    <td>${conf.asset} ${marketDot}</td>
                    <td>${conf.timeframe}</td>
                    <td>${formatCurrency(conf.initial_capital)}</td>
                    <td>${formatCurrency(conf.initial_capital_bucket)}</td>
                    <td>${formatCurrency(conf.max_capital_bucket)}</td>
                    <td>${statusBadge}</td>
                    <td><button class="btn-edit" data-conf='${JSON.stringify(conf)}'>Edit</button></td>
                `;
                tbody.appendChild(tr);
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

    // Modal Logic
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

    // Initialize Dashboard
    const init = () => {
        fetchPortfolio();
        fetchPositions();
        fetchConfigs();
        fetchTransactions();
        fetchEvaluations();
    };

    init();
    // Poll data every 10 seconds
    setInterval(() => {
        fetchPortfolio();
        fetchPositions();
        fetchEvaluations();
    }, 10000);
});
