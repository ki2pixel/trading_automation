window.BacktestOptimizer = window.BacktestOptimizer || {};

window.BacktestOptimizer.apiMixin = function apiMixin() {
  return {
    async api(path, options = {}) {
      let response;
      try {
        response = await fetch(path, {
          headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
          ...options,
        });
      } catch (error) {
        if (error?.name === 'AbortError') throw error;
        throw new Error(`Impossible de contacter le serveur: ${error.message || String(error)}`);
      }

      const body = await response.text();
      let payload = null;
      if (body) {
        try {
          payload = JSON.parse(body);
        } catch (error) {
          const status = response.status ? `HTTP ${response.status}` : 'réponse serveur';
          const statusText = response.statusText ? ` ${response.statusText}` : '';
          throw new Error(`Réponse non JSON du serveur (${status}${statusText}).`);
        }
      }

      if (!response.ok) {
        throw new Error(payload?.error || payload?.detail || response.statusText || `Erreur HTTP ${response.status}`);
      }
      if (!payload) throw new Error('Réponse serveur vide ou invalide.');
      return payload;
    },

    showError(message) {
      this.errorMessage = message || '';
    },

    clearError() {
      this.errorMessage = '';
    },
  };
};