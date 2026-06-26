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
        });
    });

    // Formatting utilities
    const formatCurrency = (val) => new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(val);
    const formatPercent = (val) => new Intl.NumberFormat('fr-FR', { style: 'percent', minimumFractionDigits: 2 }).format(val);

    // Data Fetching
    const fetchPortfolio = async () => {
        try {
            const res = await fetch('/api/portfolio');
            const data = await res.json();
            document.getElementById('kpi-nav').textContent = formatCurrency(data.total_nav);
            document.getElementById('kpi-cash').textContent = formatCurrency(data.cash_balance);
            document.getElementById('kpi-allocated').textContent = formatCurrency(data.allocated_balance);
            
            // We'll calculate open pnl from positions
        } catch (e) { console.error('Error fetching portfolio', e); }
    };

    const fetchPositions = async () => {
        try {
            const res = await fetch('/api/positions');
            const data = await res.json();
            const tbody = document.getElementById('positions-body');
            tbody.innerHTML = '';
            let totalPnl = 0;

            if (data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--text-muted)">No open positions</td></tr>';
            } else {
                data.forEach(pos => {
                    totalPnl += pos.pnl;
                    const pnlClass = pos.pnl >= 0 ? 'positive' : 'negative';
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td><strong>${pos.asset}</strong></td>
                        <td>${pos.strategy_name}</td>
                        <td>${pos.qty}</td>
                        <td>${formatCurrency(pos.entry_price)}</td>
                        <td>${formatCurrency(pos.current_price)}</td>
                        <td class="${pnlClass}">${formatCurrency(pos.pnl)}</td>
                    `;
                    tbody.appendChild(tr);
                });
            }

            const pnlEl = document.getElementById('kpi-pnl');
            pnlEl.textContent = formatCurrency(totalPnl);
            pnlEl.className = 'kpi-value ' + (totalPnl >= 0 ? 'positive' : 'negative');
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
                    statusBadge = '<span class="badge error">Erreur</span>';
                } else {
                    statusBadge = `<span class="badge inactive">${conf.status || 'Inactive'}</span>`;
                }

                tr.innerHTML = `
                    <td>${conf.id}</td>
                    <td><strong>${conf.strategy_name}</strong></td>
                    <td>${conf.asset}</td>
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
    };

    init();
    // Poll data every 10 seconds
    setInterval(() => {
        fetchPortfolio();
        fetchPositions();
    }, 10000);
});
