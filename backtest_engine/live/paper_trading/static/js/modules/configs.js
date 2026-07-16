import { 
    getConfigs, 
    updateConfig, 
    toggleConfig 
} from '../api.js';

import { 
    formatAmountForAsset,
    showToast, 
    showError, 
    setButtonLoading 
} from '../ui.js';

import { setupModalAccessibility } from './dashboard.js';

export let cachedConfigs = null;

export const invalidateConfigsCache = () => {
    cachedConfigs = null;
};

export const fetchConfigs = async (forceRefresh = false) => {
    try {
        let data;
        if (cachedConfigs && !forceRefresh) {
            data = cachedConfigs;
        } else {
            data = await getConfigs();
            cachedConfigs = data;
        }
        
        const tbody = document.getElementById('configs-body');
        if (!tbody) return;
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
                spanMarket.title = 'Market Open';
            } else {
                spanMarket.className = 'market-status closed';
                spanMarket.title = 'Market Closed';
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
                statusSpan.textContent = 'Waiting';
            } else if (conf.status === 'error') {
                statusSpan.className = 'badge error';
                if (conf.last_error) {
                    statusSpan.classList.add('has-tooltip');
                    statusSpan.textContent = 'Error';
                    const tooltipSpan = document.createElement('span');
                    tooltipSpan.className = 'tooltip';
                    tooltipSpan.textContent = conf.last_error;
                    statusSpan.appendChild(tooltipSpan);
                } else {
                    statusSpan.textContent = 'Error';
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
            inputCheckbox.setAttribute('aria-label', `Enable or disable strategy ${conf.strategy_name} for ${conf.asset}`);

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
            btnEdit.setAttribute('aria-label', `Edit configuration for strategy ${conf.strategy_name} for ${conf.asset}`);
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
                        showError('Failed to toggle strategy status.', `Status code: ${res.status}`);
                        e.target.checked = !isActive;
                    }
                } catch(err) {
                    showError('An error occurred while toggling strategy status.', err);
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

export const openEditModal = (conf, triggerEl) => {
    const modal = document.getElementById('edit-modal');
    if (!modal) return;
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

export const initConfigsModule = () => {
    const modal = document.getElementById('edit-modal');
    const form = document.getElementById('config-form');
    if (!modal || !form) return;

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
            showToast('Invalid JSON format in indicator parameters.', 'error');
            return;
        }

        const initialCap = parseFloat(document.getElementById('edit-initial-cap').value);
        const initialBucket = parseFloat(document.getElementById('edit-initial-bucket').value);
        const maxBucket = parseFloat(document.getElementById('edit-max-bucket').value);
        const maxEntry = parseFloat(document.getElementById('edit-max-entry').value);

        if (isNaN(initialCap) || initialCap <= 0) {
            showToast('Initial capital must be a number greater than 0.', 'error');
            return;
        }
        if (isNaN(initialBucket) || initialBucket <= 0) {
            showToast('Initial capital bucket must be a number greater than 0.', 'error');
            return;
        }
        if (isNaN(maxBucket) || maxBucket <= 0) {
            showToast('Maximum capital bucket must be a number greater than 0.', 'error');
            return;
        }
        if (isNaN(maxEntry) || maxEntry <= 0) {
            showToast('Maximum entry price must be a number greater than 0.', 'error');
            return;
        }
        if (initialBucket > maxBucket) {
            showToast('Initial capital bucket cannot exceed maximum bucket.', 'error');
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
                showToast('Configuration updated successfully.', 'success');
                cachedConfigs = null;
                fetchConfigs();
            } else {
                showError('Failed to update configuration.', `Status code: ${res.status}`);
            }
        } catch (err) {
            showError('An error occurred while updating the configuration.', err);
        } finally {
            setButtonLoading(submitBtn, false);
        }
    };
};
