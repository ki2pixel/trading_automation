window.BacktestOptimizer = window.BacktestOptimizer || {};

window.BacktestOptimizer.estimatesMixin = function estimatesMixin() {
  return {
    scheduleEstimate(wait = 200) {
      this.estimateDirty = true;
      this.errorMessage = "Configuration modifiée. Veuillez cliquer sur 'Pré-calculer' pour valider et estimer.";
    },

    async estimate() {
      this.isEstimating = true;
      if (this.currentEstimateController) this.currentEstimateController.abort();
      const controller = new AbortController();
      this.currentEstimateController = controller;
      try {
        const payload = await this.api('/api/estimate', {
          method: 'POST',
          body: JSON.stringify(this.collectPayload()),
          signal: controller.signal,
        });
        if (this.currentEstimateController !== controller) return null;
        this.currentEstimateController = null;
        this.lastEstimate = payload;
        this.estimateDirty = false;
        this.warnings = payload.warnings || [];
        this.calculateBayesianIterations();
        this.updateOptimizeAvailability(payload);
        return payload;
      } catch (error) {
        if (error?.name === 'AbortError') return null;
        if (this.currentEstimateController !== controller) return null;
        this.currentEstimateController = null;
        this.lastEstimate = null;
        this.estimateDirty = true;
        this.warnings = [];
        this.updateOptimizeAvailability(null, error.message || String(error));
        return null;
      } finally {
        if (this.currentEstimateController === controller || this.currentEstimateController === null) {
          this.isEstimating = false;
        }
      }
    },

    updateOptimizeAvailability(estimatePayload = null, errorMessage = '') {
      let blockingError = errorMessage || this.validateParameterRows();
      const maxIterations = Number(this.form.maxIterations || 10000);
      const rawIterations = Number(estimatePayload?.total_iterations ?? 0);
      const canonicalIterations = Number(estimatePayload?.canonical_iterations ?? rawIterations);

      const isGrid = this.form.optimizationMode !== 'bayesian';

      if (!blockingError && estimatePayload && maxIterations > 0 && rawIterations > maxIterations && isGrid) {
        blockingError = `La grille contient ${rawIterations} itérations brutes, au-dessus de max_iterations=${maxIterations}. Réduisez la grille ou augmentez Max itérations.`;
      }
      if (!blockingError && estimatePayload && maxIterations > 0 && canonicalIterations > maxIterations && isGrid) {
        blockingError = `La grille contient ${canonicalIterations} itérations canoniques, au-dessus de max_iterations=${maxIterations}. Réduisez la grille effective ou augmentez Max itérations.`;
      }

      this.errorMessage = blockingError || '';
    },

    canOptimize() {
      return Boolean(this.lastEstimate) && !this.errorMessage && !this.estimateDirty;
    },
  };
};