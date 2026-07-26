import { 
    getPortfolio, 
    getPositions, 
    getHeartbeat, 
    getKillSwitchStatus,
    executePanic,
    resumeTrading
} from '../api.js';

import { 
    formatCurrency, 
    formatPercent, 
    formatUSDT, 
    formatAmountForAsset,
    showToast, 
    showError, 
    setButtonLoading 
} from '../ui.js';

import { 
    loadChart, 
    invalidateChartCache 
} from '../chart.js';

let lastTransactionTime = null;
let lastEvaluationTime = null;
let lastPriceTime = null;

// Modal Accessibility Helper
export const setupModalAccessibility = (modal, closeSelectors, firstFocusSelector) => {
    if (!modal) return;
    
    modal.setAttribute('role', 'dialog');
    modal.setAttribute('aria-modal', 'true');
    
    const closeBtns = modal.querySelectorAll(closeSelectors);
    closeBtns.forEach(btn => {
        btn.setAttribute('aria-label', 'Close modal');
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

export const fetchPortfolio = async () => {
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

export const fetchPositions = async () => {
    try {
        const data = await getPositions();
        const tbody = document.getElementById('positions-body');
        if (!tbody) return;
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
        if (t212PnlEl) {
            totalT212Pnl = Math.round(totalT212Pnl * 100) / 100;
            t212PnlEl.textContent = formatCurrency(totalT212Pnl);
            t212PnlEl.className = 'kpi-value ' + (totalT212Pnl >= 0 ? 'positive' : 'negative');
        }

        const bybitPnlEl = document.getElementById('kpi-bybit-pnl');
        if (bybitPnlEl) {
            totalBybitPnl = Math.round(totalBybitPnl * 100) / 100;
            bybitPnlEl.textContent = formatUSDT(totalBybitPnl);
            bybitPnlEl.className = 'kpi-value ' + (totalBybitPnl >= 0 ? 'positive' : 'negative');
        }
    } catch (e) { console.error('Error rendering positions', e); }
};

export const fetchHeartbeat = async () => {
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
            if (hbDot) {
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

export const renderKillSwitchStatus = (data) => {
    const container = document.getElementById('kill-switch-status');
    const label = document.getElementById('kill-switch-status-text');
    const resumeBtn = document.getElementById('resume-btn');
    if (!container || !label || !resumeBtn) return;

    const suspended = data.status === 'suspended';
    const healthy = data.healthy === true;
    const reason = data.reason || 'No reason supplied';

    container.classList.toggle('suspended', suspended);
    container.classList.toggle('degraded', !healthy);
    resumeBtn.disabled = !suspended || !healthy;

    if (!healthy) {
        label.textContent = `Trading Suspended — ${reason}`;
        container.title = 'Kill Switch state cannot be safely synchronized.';
        return;
    }

    if (suspended) {
        label.textContent = 'Trading Suspended';
        container.title = reason;
        return;
    }

    label.textContent = 'Trading Active';
    container.title = 'Kill Switch state is active.';
};

export const fetchKillSwitchStatus = async () => {
    try {
        const data = await getKillSwitchStatus();
        renderKillSwitchStatus(data);
        return data;
    } catch (err) {
        renderKillSwitchStatus({
            status: 'suspended',
            healthy: false,
            reason: 'Status unavailable'
        });
        console.error('Error fetching Kill Switch status', err);
        return null;
    }
};

export const initResumeButton = () => {
    const resumeBtn = document.getElementById('resume-btn');
    const resumeModal = document.getElementById('resume-modal');
    const cancelBtn = document.getElementById('cancel-resume-btn');
    const executeBtn = document.getElementById('execute-resume-btn');
    const confirm = document.getElementById('resume-confirm');
    if (!resumeBtn || !resumeModal || !cancelBtn || !executeBtn || !confirm) return;

    setupModalAccessibility(resumeModal, '.close-modal, #cancel-resume-btn', '#cancel-resume-btn');

    const closeModal = () => {
        resumeModal.style.display = 'none';
        if (resumeModal.triggerElement) {
            resumeModal.triggerElement.focus();
        }
    };

    const updateConfirmation = () => {
        executeBtn.disabled = !confirm.checked;
    };

    resumeBtn.addEventListener('click', () => {
        resumeModal.triggerElement = resumeBtn;
        resumeModal.style.display = 'flex';
        confirm.checked = false;
        updateConfirmation();
        setTimeout(() => {
            cancelBtn.focus();
        }, 50);
    });

    confirm.addEventListener('change', updateConfirmation);

    executeBtn.addEventListener('click', async () => {
        setButtonLoading(executeBtn, true, 'RESUMING...');

        try {
            const res = await resumeTrading();
            if (!res.ok) {
                const error = await res.json().catch(() => ({}));
                showError('Trading could not be resumed.', error.detail || `Status code: ${res.status}`);
                return;
            }

            await res.json();
            closeModal();
            await fetchKillSwitchStatus();
            showToast('Trading resumed after Kill Switch reconciliation.', 'success');
        } catch (err) {
            showError('An error occurred while resuming trading.', err);
        } finally {
            setButtonLoading(executeBtn, false);
            updateConfirmation();
        }
    });
};

export const initPanicButton = (onPanicSuccess) => {
    const panicBtn = document.getElementById('panic-btn');
    const panicModal = document.getElementById('panic-modal');
    const cancelBtn = document.getElementById('cancel-panic-btn');
    const executeBtn = document.getElementById('execute-panic-btn');
    const confirm1 = document.getElementById('panic-confirm-1');
    const confirm2 = document.getElementById('panic-confirm-2');
    
    if (!panicBtn || !panicModal || !cancelBtn || !executeBtn || !confirm1 || !confirm2) return;
    
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
                showToast(`Emergency liquidation successful! ${data.closed_positions_count} positions closed.`, 'success');
                closeModal();
                
                invalidateChartCache();
                
                if (onPanicSuccess) {
                    onPanicSuccess();
                }
                
                await fetchKillSwitchStatus();
            } else {
                showError('Emergency liquidation failed.', `Status code: ${res.status}`);
            }
        } catch(err) {
            showError('An error occurred during emergency liquidation.', err);
        } finally {
            setButtonLoading(executeBtn, false);
            checkConfirmation();
        }
    });
};
