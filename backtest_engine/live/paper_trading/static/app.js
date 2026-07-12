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
    formatAmountForAsset,
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
let isLoading = false;

document.addEventListener('DOMContentLoaded', () => {
    // Modal Accessibility Helper
    const setupModalAccessibility = (modal, closeSelectors, firstFocusSelector) => {
        if (!modal) return;
        
        modal.setAttribute('role', 'dialog');
        modal.setAttribute('aria-modal', 'true');
        
        const closeBtns = modal.querySelectorAll(closeSelectors);
        closeBtns.forEach(btn => {
            btn.setAttribute('aria-label', 'Fermer la modale');
            btn.addEventListener('click', () => {
                modal.style.display = 'none';
                if (modal.triggerElement) {
                    modal.triggerElement.focus();
                }
            });
        });

        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.style.display = 'none';
                if (modal.triggerElement) {
                    modal.triggerElement.focus();
                }
            }
        });

        modal.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                modal.style.display = 'none';
                if (modal.triggerElement) {
                    modal.triggerElement.focus();
                }
            }
            
            if (e.key === 'Tab') {
                const focusableElements = modal.querySelectorAll(
                    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
                );
                const activeElements = Array.from(focusableElements).filter(el => el.tabIndex !== -1 && !el.disabled);
                if (activeElements.length === 0) return;
                
                const firstElement = activeElements[0];
                const lastElement = activeElements[activeElements.length - 1];
                
                if (e.shiftKey) { // Shift + Tab
                    if (document.activeElement === firstElement) {
                        lastElement.focus();
                        e.preventDefault();
                    }
                } else { // Tab
                    if (document.activeElement === lastElement) {
                        firstElement.focus();
                        e.preventDefault();
                    }
                }
            }
        });
    };

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
                const tr = document.createElement('tr');
                const td = document.createElement('td');
                td.colSpan = 6;
                td.style.textAlign = 'center';
                td.style.color = 'var(--text-muted)';
                td.textContent = 'No open positions';
                tr.appendChild(td);
                tbody.appendChild(tr);
            } else {
                data.forEach(pos => {
                    const isCrypto = pos.asset.toLowerCase().endsWith("usdt") || pos.asset.toLowerCase().endsWith("usdc");
                    if (isCrypto) {
                        totalBybitPnl += pos.pnl;
                    } else {
                        totalT212Pnl += pos.pnl;
                    }
                    const pnlStr = formatAmountForAsset(pos.asset, pos.pnl);
                    const pnlClass = pos.pnl >= 0 ? 'positive' : 'negative';
                    
                    const tr = document.createElement('tr');
                    
                    const tdAsset = document.createElement('td');
                    const strongAsset = document.createElement('strong');
                    strongAsset.textContent = pos.asset;
                    tdAsset.appendChild(strongAsset);
                    tr.appendChild(tdAsset);

                    const tdStrat = document.createElement('td');
                    tdStrat.textContent = pos.strategy_name;
                    tr.appendChild(tdStrat);

                    const tdQty = document.createElement('td');
                    tdQty.textContent = pos.qty;
                    tr.appendChild(tdQty);

                    const tdEntry = document.createElement('td');
                    tdEntry.textContent = formatAmountForAsset(pos.asset, pos.entry_price);
                    tr.appendChild(tdEntry);

                    const tdCurrent = document.createElement('td');
                    tdCurrent.textContent = formatAmountForAsset(pos.asset, pos.current_price);
                    tr.appendChild(tdCurrent);

                    const tdPnl = document.createElement('td');
                    tdPnl.className = pnlClass;
                    tdPnl.textContent = pnlStr;
                    tr.appendChild(tdPnl);

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
                
                // Column 1: ID
                const tdId = document.createElement('td');
                tdId.textContent = conf.id;
                tr.appendChild(tdId);

                // Column 2: Strategy Name
                const tdStrat = document.createElement('td');
                const strongStrat = document.createElement('strong');
                strongStrat.textContent = conf.strategy_name;
                tdStrat.appendChild(strongStrat);
                tr.appendChild(tdStrat);

                // Column 3: Asset & Market Status
                const tdAsset = document.createElement('td');
                tdAsset.textContent = conf.asset + ' ';
                const spanMarket = document.createElement('span');
                if (conf.market_open) {
                    spanMarket.className = 'market-status open';
                    spanMarket.title = 'Marché Ouvert';
                } else {
                    spanMarket.className = 'market-status closed';
                    spanMarket.title = 'Marché Fermé';
                }
                spanMarket.textContent = '●';
                tdAsset.appendChild(spanMarket);
                tr.appendChild(tdAsset);

                // Column 4: Timeframe
                const tdTimeframe = document.createElement('td');
                tdTimeframe.textContent = conf.timeframe;
                tr.appendChild(tdTimeframe);

                // Column 5: Initial Capital
                const tdInitCap = document.createElement('td');
                tdInitCap.textContent = formatAmountForAsset(conf.asset, conf.initial_capital);
                tr.appendChild(tdInitCap);

                // Column 6: Initial Capital Bucket
                const tdInitBucket = document.createElement('td');
                tdInitBucket.textContent = formatAmountForAsset(conf.asset, conf.initial_capital_bucket);
                tr.appendChild(tdInitBucket);

                // Column 7: Max Capital Bucket
                const tdMaxBucket = document.createElement('td');
                tdMaxBucket.textContent = formatAmountForAsset(conf.asset, conf.max_capital_bucket);
                tr.appendChild(tdMaxBucket);

                // Column 8: Max Entry Price
                const tdMaxEntry = document.createElement('td');
                tdMaxEntry.textContent = formatAmountForAsset(conf.asset, conf.max_entry_price);
                tr.appendChild(tdMaxEntry);

                // Column 9: Status Badge
                const tdStatus = document.createElement('td');
                const statusSpan = document.createElement('span');
                if (conf.status === 'active') {
                    statusSpan.className = 'badge active';
                    statusSpan.textContent = 'Active';
                } else if (conf.status === 'inactive') {
                    statusSpan.className = 'badge inactive';
                    statusSpan.textContent = 'Inactive';
                } else if (conf.status === 'waiting_data') {
                    statusSpan.className = 'badge warning';
                    statusSpan.textContent = 'En attente';
                } else if (conf.status === 'error') {
                    statusSpan.className = 'badge error';
                    if (conf.last_error) {
                        statusSpan.classList.add('has-tooltip');
                        statusSpan.textContent = 'Erreur';
                        const tooltipSpan = document.createElement('span');
                        tooltipSpan.className = 'tooltip';
                        tooltipSpan.textContent = conf.last_error;
                        statusSpan.appendChild(tooltipSpan);
                    } else {
                        statusSpan.textContent = 'Erreur';
                    }
                } else {
                    statusSpan.className = 'badge inactive';
                    statusSpan.textContent = conf.status || 'Inactive';
                }
                tdStatus.appendChild(statusSpan);
                tr.appendChild(tdStatus);

                // Column 10: Strategy Toggle Switch
                const tdToggle = document.createElement('td');
                const labelSwitch = document.createElement('label');
                labelSwitch.className = 'switch';
                labelSwitch.title = 'Pause / Resume Strategy';

                const inputCheckbox = document.createElement('input');
                inputCheckbox.type = 'checkbox';
                inputCheckbox.className = 'toggle-strategy-active';
                inputCheckbox.setAttribute('data-id', conf.id);
                inputCheckbox.checked = conf.is_active;
                inputCheckbox.setAttribute('aria-label', `Activer ou désactiver la stratégie ${conf.strategy_name} pour ${conf.asset}`);

                const spanSlider = document.createElement('span');
                spanSlider.className = 'slider round';

                labelSwitch.appendChild(inputCheckbox);
                labelSwitch.appendChild(spanSlider);
                tdToggle.appendChild(labelSwitch);
                tr.appendChild(tdToggle);

                // Column 11: Edit Button
                const tdEdit = document.createElement('td');
                const btnEdit = document.createElement('button');
                btnEdit.className = 'btn-edit';
                btnEdit.confData = conf;
                btnEdit.textContent = 'Edit';
                btnEdit.setAttribute('aria-label', `Modifier la configuration de la stratégie ${conf.strategy_name} pour ${conf.asset}`);
                tdEdit.appendChild(btnEdit);
                tr.appendChild(tdEdit);

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
                    const conf = e.currentTarget.confData;
                    openEditModal(conf, e.currentTarget);
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
                    const date = new Date(tx.timestamp).toLocaleString('fr-FR');
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
            
            if (prevBtn) prevBtn.disabled = evalPage === 1;
            if (nextBtn) nextBtn.disabled = data.length < evalLimit;
            if (pageTxt) pageTxt.textContent = `Page ${evalPage}`;
        } catch (e) { console.error('Error rendering evaluations', e); }
    };

    // Modal Logic for Config Editing
    const modal = document.getElementById('edit-modal');
    const form = document.getElementById('config-form');

    const openEditModal = (conf, triggerEl) => {
        modal.triggerElement = triggerEl;
        document.getElementById('edit-id').value = conf.id;
        document.getElementById('edit-initial-cap').value = conf.initial_capital;
        document.getElementById('edit-initial-bucket').value = conf.initial_capital_bucket;
        document.getElementById('edit-max-bucket').value = conf.max_capital_bucket;
        document.getElementById('edit-max-entry').value = conf.max_entry_price;
        document.getElementById('edit-is-active').checked = conf.is_active;
        document.getElementById('edit-indicator-params').value = JSON.stringify(conf.indicator_params || {}, null, 2);
        modal.style.display = 'flex';
        setTimeout(() => {
            const firstInput = document.getElementById('edit-initial-cap');
            if (firstInput) {
                firstInput.focus();
                firstInput.select();
            }
        }, 50);
    };

    setupModalAccessibility(modal, '.close-modal', '#edit-initial-cap');

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
                if (modal.triggerElement) {
                    modal.triggerElement.focus();
                }
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
        const systemStatus = document.querySelector('.system-status');
        const statusIndicator = document.querySelector('.status-indicator');
        const statusText = systemStatus ? systemStatus.querySelector('span') : null;

        try {
            const data = await getHeartbeat();
            
            if (systemStatus && statusIndicator && statusText) {
                systemStatus.classList.remove('offline');
                statusIndicator.classList.remove('offline');
                statusText.textContent = 'Engine Online';
            }
            
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
            if (systemStatus && statusIndicator && statusText) {
                systemStatus.classList.add('offline');
                statusIndicator.classList.add('offline');
                statusText.textContent = 'Engine Offline';
            }
            ['trading212', 'bybit'].forEach(source => {
                const hbDot = document.getElementById(`hb-${source}`);
                if (hbDot) hbDot.className = 'heartbeat-dot offline';
                const container = document.getElementById(`hb-${source}-container`);
                if (container) container.title = `${source.toUpperCase()} Price Feed: OFFLINE`;
            });
            return { transactions: true, evaluations: true, price: true };
        }
    };

    // Panic liquidation close modal
    const initPanicButton = () => {
        const panicBtn = document.getElementById('panic-btn');
        const panicModal = document.getElementById('panic-modal');
        const cancelBtn = document.getElementById('cancel-panic-btn');
        const executeBtn = document.getElementById('execute-panic-btn');
        const confirm1 = document.getElementById('panic-confirm-1');
        const confirm2 = document.getElementById('panic-confirm-2');
        
        setupModalAccessibility(panicModal, '.close-modal, #cancel-panic-btn', '#cancel-panic-btn');
        
        panicBtn.addEventListener('click', () => {
            panicModal.triggerElement = panicBtn;
            panicModal.style.display = 'flex';
            confirm1.checked = false;
            confirm2.checked = false;
            executeBtn.disabled = true;
            setTimeout(() => {
                cancelBtn.focus();
            }, 50);
        });
        
        const checkConfirmation = () => {
            executeBtn.disabled = !(confirm1.checked && confirm2.checked);
        };
        
        confirm1.addEventListener('change', checkConfirmation);
        confirm2.addEventListener('change', checkConfirmation);
        
        const closeModal = () => {
            panicModal.style.display = 'none';
            if (panicModal.triggerElement) {
                panicModal.triggerElement.focus();
            }
        };
        
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

        const clearBtn = document.getElementById('clear-console-btn');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                consoleOutput.textContent = '';
            });
        }
        
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
        if (isLoading) return;
        isLoading = true;
        try {
            const changed = await fetchHeartbeat();
            
            // Refresh configs if configs view is active
            const configsTab = document.getElementById('configs');
            if (configsTab && configsTab.classList.contains('active')) {
                await fetchConfigs();
            }
            
            // Refresh positions/portfolio if prices updated
            if (changed.price) {
                await fetchPortfolio();
                await fetchPositions();
            }
            
            // Refresh evaluations if new evaluations are available
            if (changed.evaluations) {
                await fetchEvaluations();
            }
            
            // If an asset is currently selected, refresh its chart and metrics
            const selector = document.getElementById('asset-selector');
            if (selector && selector.value) {
                if (changed.transactions) {
                    invalidateChartCache();
                }
                // Reload chart only if prices or transactions changed
                if (changed.price || changed.transactions) {
                    await loadChart(selector.value, false);
                }
            }
        } catch (e) {
            console.error("Error in polling interval", e);
        } finally {
            isLoading = false;
        }
    }, 10000);
});
