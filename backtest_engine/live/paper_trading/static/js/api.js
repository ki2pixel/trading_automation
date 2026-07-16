// API Client Module with Fetch Interceptor and CSRF Management
import { showError } from './ui.js';

let cachedCsrfToken = null;

// Global fetch reference for interceptor
const originalFetch = window.fetch;

// Helper to verify same-origin destinations
function isSameOrigin(url) {
    if (typeof url !== 'string') {
        return false;
    }
    // Relative URLs are always same-origin
    if (!url.startsWith('http://') && !url.startsWith('https://') && !url.startsWith('//')) {
        return true;
    }
    try {
        const targetUrl = new URL(url, window.location.href);
        return targetUrl.origin === window.location.origin;
    } catch (e) {
        return false;
    }
}

// Helper to get or retrieve CSRF token asynchronously
export async function ensureCsrfToken() {
    if (cachedCsrfToken) return cachedCsrfToken;
    try {
        const response = await originalFetch('/api/csrf-token');
        if (response.ok) {
            const data = await response.json();
            cachedCsrfToken = data.csrf_token;
        }
    } catch (e) {
        console.error("Failed to fetch CSRF token", e);
    }
    return cachedCsrfToken || '';
}

// Global fetch interceptor to handle session expiration (401), network errors, 500/503 and CSRF tokens
window.fetch = async function(url, options = {}) {
    const method = (options.method || 'GET').toUpperCase();
    if (['POST', 'PUT', 'DELETE', 'PATCH'].includes(method) && url !== '/api/csrf-token' && isSameOrigin(url)) {
        const csrf = await ensureCsrfToken();
        options.headers = options.headers || {};
        if (options.headers instanceof Headers) {
            options.headers.set('X-CSRFToken', csrf);
        } else {
            options.headers['X-CSRFToken'] = csrf;
        }
    }
    
    let response;
    try {
        response = await originalFetch(url, options);
    } catch (netError) {
        showError("Unable to contact the server. Please check your network connection.", netError);
        throw netError;
    }
    
    if (response.status === 401) {
        window.location.href = '/login.html';
    } else if (response.status === 403) {
        showError("Access denied or CSRF token invalid/expired (403). Please refresh the page.");
    } else if (response.status === 422) {
        try {
            const errData = await response.clone().json();
            let errMsg = "Data validation error (422).";
            if (errData && errData.detail) {
                if (typeof errData.detail === 'string') {
                    errMsg += ` Detail: ${errData.detail}`;
                } else if (Array.isArray(errData.detail)) {
                    const details = errData.detail.map(d => `${d.loc.join('.')}: ${d.msg}`).join(', ');
                    errMsg += ` Details: ${details}`;
                }
            }
            showError(errMsg);
        } catch (e) {
            showError("Data validation error (422).");
        }
    } else if (response.status === 500) {
        showError("An internal server error occurred (500).");
    } else if (response.status === 503) {
        showError("The service is temporarily unavailable (503).");
    }
    
    return response;
};

// API Fetching Functions
export async function getPortfolio() {
    const res = await fetch('/api/portfolio');
    return await res.json();
}

export async function getPositions() {
    const res = await fetch('/api/positions');
    return await res.json();
}

export async function getConfigs() {
    const res = await fetch('/api/configs');
    return await res.json();
}

export async function updateConfig(id, payload) {
    return await fetch(`/api/configs/${encodeURIComponent(id)}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });
}

export async function toggleConfig(id, is_active) {
    return await fetch(`/api/configs/${encodeURIComponent(id)}/toggle`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_active })
    });
}

export async function getTransactions(limit = 50, offset = 0, cursorTimestamp = null) {
    let url = `/api/transactions?limit=${encodeURIComponent(limit)}&offset=${encodeURIComponent(offset)}`;
    if (cursorTimestamp) {
        url += `&cursor_timestamp=${encodeURIComponent(cursorTimestamp)}`;
    }
    const res = await fetch(url);
    return await res.json();
}

export async function getEvaluations(limit = 100, offset = 0) {
    const res = await fetch(`/api/evaluations?limit=${encodeURIComponent(limit)}&offset=${encodeURIComponent(offset)}`);
    return await res.json();
}

export async function getHeartbeat() {
    const res = await fetch('/api/status/heartbeat');
    return await res.json();
}

export async function getKillSwitchStatus() {
    const res = await fetch('/api/status/kill-switch');
    return await res.json();
}

export async function executePanic() {
    return await fetch('/api/control/panic', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    });
}

export async function resumeTrading() {
    return await fetch('/api/control/resume', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    });
}

export async function getPerformanceMetrics(ticker) {
    const res = await fetch(`/api/performance/metrics?ticker=${encodeURIComponent(ticker)}`);
    return await res.json();
}

export async function getCandles(ticker) {
    const res = await fetch(`/api/candles?ticker=${encodeURIComponent(ticker)}`);
    return await res.json();
}
