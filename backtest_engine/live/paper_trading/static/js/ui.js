// UI and formatting utilities

export const formatCurrency = (val) => new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(val);
export const formatPercent = (val) => new Intl.NumberFormat('fr-FR', { style: 'percent', minimumFractionDigits: 2 }).format(val);
export const formatUSDT = (val) => new Intl.NumberFormat('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(val) + ' USDT';

// Show toast notification (Glassmorphic Toast)
export function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;
    
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    const textSpan = document.createElement('span');
    textSpan.innerText = message;
    toast.appendChild(textSpan);
    
    const closeBtn = document.createElement('button');
    closeBtn.className = 'toast-close';
    closeBtn.innerHTML = '&times;';
    closeBtn.onclick = () => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    };
    toast.appendChild(closeBtn);
    
    container.appendChild(toast);
    
    // Trigger animation
    setTimeout(() => toast.classList.add('show'), 10);
    
    // Auto-remove after 4 seconds
    setTimeout(() => {
        if (toast.parentNode) {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }
    }, 4000);
}

// System error handler that prints technical details in console but shows generic messages in UI
export function showError(userMessage, technicalDetails = null) {
    if (technicalDetails) {
        console.error("Technical Details:", technicalDetails);
    }
    showToast(userMessage, 'error');
}

// Manage button loading state with spinner
export function setButtonLoading(btn, isLoading, loadingText = '') {
    if (!btn) return;
    if (isLoading) {
        btn.classList.add('btn-loading');
        btn.disabled = true;
        if (loadingText) {
            btn.dataset.originalText = btn.textContent;
            btn.textContent = loadingText;
        }
    } else {
        btn.classList.remove('btn-loading');
        btn.disabled = false;
        if (btn.dataset.originalText) {
            btn.textContent = btn.dataset.originalText;
            delete btn.dataset.originalText;
        }
    }
}
