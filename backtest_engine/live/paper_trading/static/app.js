import { 
    fetchPortfolio, 
    fetchPositions, 
    fetchHeartbeat, 
    fetchKillSwitchStatus,
    initPanicButton,
    initResumeButton
} from './js/modules/dashboard.js';

import { 
    fetchConfigs, 
    initConfigsModule,
    invalidateConfigsCache
} from './js/modules/configs.js';

import { 
    fetchTransactions, 
    fetchEvaluations, 
    initLogsSSE,
    resetTxPagination,
    goNextTxPage,
    goPrevTxPage,
    goNextEvalPage,
    goPrevEvalPage
} from './js/modules/logs.js';

import { 
    loadChart, 
    invalidateChartCache 
} from './js/chart.js';

let pollingInterval = null;
let isLoading = false;

document.addEventListener('DOMContentLoaded', () => {
    // Navigation Logic
    const navItems = document.querySelectorAll('.nav-item');
    const sections = document.querySelectorAll('.view-section');

    let tabDebounceTimer = null;
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

            // Debounce fetch by 200ms
            if (tabDebounceTimer) clearTimeout(tabDebounceTimer);
            tabDebounceTimer = setTimeout(() => {
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
            }, 200);
        });
    });

    // Initialize Modules
    initConfigsModule();
    initLogsSSE();
    initResumeButton();
    
    initPanicButton(async () => {
        // Callback on panic success
        resetTxPagination();
        invalidateConfigsCache();
        
        // Priority 1: Critical state (serialized)
        await Promise.all([fetchPortfolio(), fetchPositions(), fetchKillSwitchStatus()]);
        
        // Priority 2: Historical data (serialized after priority 1)
        await fetchTransactions();
        const selector = document.getElementById('asset-selector');
        if (selector && selector.value) {
            await loadChart(selector.value);
        }
    });

    // Bind Logout Button
    const logoutBtn = document.getElementById('btn-logout');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', async () => {
            try {
                const response = await fetch('/api/logout', {
                    method: 'POST'
                });
                if (response.redirected) {
                    window.location.href = response.url;
                } else {
                    window.location.href = '/login.html';
                }
            } catch (e) {
                console.error("Logout failed", e);
                window.location.href = '/login.html';
            }
        });
    }
    
    // Dropdown Asset Selection event
    const selector = document.getElementById('asset-selector');
    if (selector) {
        selector.addEventListener('change', (e) => {
            loadChart(e.target.value, true);
        });
    }

    // Bind Pagination Button Clicks
    const txPrev = document.getElementById('btn-tx-prev');
    const txNext = document.getElementById('btn-tx-next');
    const evalPrev = document.getElementById('btn-eval-prev');
    const evalNext = document.getElementById('btn-eval-next');
    
    if (txPrev) {
        txPrev.addEventListener('click', () => {
            goPrevTxPage();
            fetchTransactions();
        });
    }
    if (txNext) {
        txNext.addEventListener('click', () => {
            goNextTxPage();
            fetchTransactions();
        });
    }
    if (evalPrev) {
        evalPrev.addEventListener('click', () => {
            goPrevEvalPage();
            fetchEvaluations();
        });
    }
    if (evalNext) {
        evalNext.addEventListener('click', () => {
            goNextEvalPage();
            fetchEvaluations();
        });
    }

    // Initialize Dashboard data
    const init = () => {
        fetchPortfolio();
        fetchPositions();
        fetchConfigs();
        fetchTransactions();
        fetchEvaluations();
        fetchHeartbeat();
        fetchKillSwitchStatus();
    };

    init();
    startPolling();
});

const startPolling = () => {
    if (pollingInterval) clearInterval(pollingInterval);
    pollingInterval = setInterval(runPollingCycle, 10000);
};

const stopPolling = () => {
    if (pollingInterval) {
        clearInterval(pollingInterval);
        pollingInterval = null;
    }
};

const runPollingCycle = async () => {
    if (document.hidden) {
        return;
    }
    if (isLoading) return;
    isLoading = true;
    try {
        const changed = await fetchHeartbeat();
        await fetchKillSwitchStatus();
        
        // Refresh configs if configs view is active
        const configsTab = document.getElementById('configs');
        if (configsTab && configsTab.classList.contains('active')) {
            await fetchConfigs(true);
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
        
        // Refresh transactions if transactions view is active
        if (changed.transactions) {
            invalidateChartCache();
            const txTab = document.getElementById('transactions');
            if (txTab && txTab.classList.contains('active')) {
                await fetchTransactions();
            }
        }
        
        // If an asset is currently selected, refresh its chart and metrics
        const selector = document.getElementById('asset-selector');
        if (selector && selector.value) {
            if (changed.price || changed.transactions) {
                await loadChart(selector.value, false);
            }
        }
    } catch (e) {
        console.error("Error in polling cycle", e);
    } finally {
        isLoading = false;
    }
};

const triggerImmediateRefresh = async () => {
    if (isLoading) return;
    await runPollingCycle();
};

document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        stopPolling();
    } else {
        triggerImmediateRefresh();
        startPolling();
    }
});
