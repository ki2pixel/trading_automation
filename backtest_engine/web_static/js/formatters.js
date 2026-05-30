window.BacktestOptimizer = window.BacktestOptimizer || {};

window.BacktestOptimizer.formatterMixin = function formatterMixin() {
  return {
    formatBestSummary(best) {
      if (!best) return '-';
      const parts = [];
      if (best.iteration != null) parts.push(`#${best.iteration}`);
      if (best.status && best.status !== 'COMPLETED') parts.push(best.status);
      if (best.score != null) parts.push(`score=${this.formatNumber(best.score)}`);
      if (best.secondary_score != null) parts.push(`secondary=${this.formatNumber(best.secondary_score)}`);
      const parameterText = Object.entries(best.parameters || {}).map(([key, value]) => `${key}=${value}`).join(', ');
      if (parameterText) parts.push(parameterText);
      const metrics = best.metrics || {};
      if (metrics.closed_trades != null) parts.push(`trades=${metrics.closed_trades}`);
      if (metrics.total_net_pnl != null) parts.push(`net=${this.formatNumber(metrics.total_net_pnl)}`);
      if (metrics.max_drawdown != null) parts.push(`dd=${this.formatNumber(metrics.max_drawdown)}`);
      return parts.join(' · ') || '-';
    },

    recommendationParameterRows() {
      const parameters = this.currentRecommendations?.parameters || {};
      return Object.entries(parameters).map(([name, item]) => ({ name, ...(item || {}) }));
    },

    formatRecommendedSummary(report) {
      const recommended = report?.recommended;
      if (!recommended) return '-';
      const parts = [];
      if (recommended.iteration != null) parts.push(`#${recommended.iteration}`);
      if (recommended.score != null) parts.push(`score=${this.formatNumber(recommended.score)}`);
      if (recommended.secondary_score != null) parts.push(`secondary=${this.formatNumber(recommended.secondary_score)}`);
      const parameterText = Object.entries(recommended.parameters || {}).map(([key, value]) => `${key}=${value}`).join(', ');
      if (parameterText) parts.push(parameterText);
      const metrics = recommended.metrics || {};
      if (metrics.closed_trades != null) parts.push(`trades=${metrics.closed_trades}`);
      if (metrics.total_net_pnl != null) parts.push(`net=${this.formatNumber(metrics.total_net_pnl)}`);
      if (metrics.max_drawdown != null) parts.push(`dd=${this.formatNumber(metrics.max_drawdown)}`);
      return parts.join(' · ') || '-';
    },

    formatRecommendationValue(item) {
      if (!item || item.recommended_value == null) return '-';
      return String(item.recommended_value);
    },

    formatRecommendationRange(item) {
      if (!item) return '-';
      const range = item.sweet_spot_range || item.extended_range;
      return Array.isArray(range) && range.length === 2 ? `${range[0]} → ${range[1]}` : '-';
    },

    formatRecommendationConfidence(value) {
      return ({ high: 'élevée', medium: 'moyenne', low: 'faible' }[value] || value || '-');
    },

    formatNumber(value) {
      const number = Number(value);
      if (!Number.isFinite(number)) return String(value);
      return Math.abs(number) >= 100 ? number.toFixed(2) : number.toFixed(4).replace(/0+$/, '').replace(/\.$/, '');
    },

    estimateText(key, fallback = '-') {
      const value = this.lastEstimate?.[key];
      return value == null ? fallback : String(value);
    },

    formatJobTimeframe(job) {
      const value = job?.request?.timeframe_minutes;
      return value == null ? '-' : `${value} min`;
    },

    formatParameterSpec(spec) {
      if (!spec?.name) return '';
      if (spec.kind === 'numeric') {
        const start = spec.start ?? '';
        const end = spec.end ?? '';
        const step = spec.step ?? '';
        const range = start === end ? String(start) : `${start}-${end}`;
        const stepText = step && Number(step) !== 1 ? ` step=${step}` : '';
        return `${spec.name}=${range}${stepText}`;
      }
      const values = Array.isArray(spec.values) ? spec.values : [];
      return `${spec.name}=${values.join('|')}`;
    },

    formatJobConfig(job) {
      const parameters = Array.isArray(job?.request?.parameters) ? job.request.parameters : [];
      const text = parameters.map(spec => this.formatParameterSpec(spec)).filter(Boolean).join(', ');
      return text || '-';
    },
  };
};