const {
  apiMixin,
  estimatesMixin,
  equityChartMixin,
  formatterMixin,
  jobsMixin,
  parameterRowsMixin,
  presetsMixin,
} = window.BacktestOptimizer;

function optimizerApp() {
  return {
    theme: localStorage.getItem('theme') || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'),
    isEstimating: false,
    isOptimizing: false,
    defaultWorkers: 1,
    timeframeOptions: [
      { value: '1', label: '1 min' },
      { value: '5', label: '5 min' },
      { value: '10', label: '10 min' },
      { value: '15', label: '15 min' },
      { value: '20', label: '20 min' },
      { value: '30', label: '30 min' },
      { value: '45', label: '45 min' },
      { value: '60', label: '60 min' },
      { value: '120', label: '120 min' },
      { value: '240', label: '240 min' },
    ],
    timeframeDropdownOpen: false,
    strategies: [],
    parameters: [],
    schema: [],
    symbols: [],
    parameterRows: [],
    jobs: [],
    selectedJobIds: [],
    activeJobId: null,
    activeJobIds: [],
    pollTimer: null,
    lastEstimate: null,
    estimateDirty: true,
    errorMessage: '',
    warnings: [],
    outputText: '',
    currentJob: null,
    currentRecommendations: null,
    recommendationsStatus: 'Les recommandations apparaîtront après une optimisation terminée.',
    recommendationsError: '',
    
    isGeneratingAnalysis: false,
    globalAnalysisError: '',
    globalAnalysisLinks: null,
    
    lastEquityPoints: [],
    equityStatus: 'La courbe apparaîtra après une optimisation terminée avec Best Run.',
    equityError: '',
    estimateTimer: null,
    currentEstimateController: null,
    nextRowId: 1,
    bayesianChanged: false,
    form: {
      strategy: '',
      symbol: '',
      processedDir: 'storage/processed',
      timeframes: ['5'],
      startDate: '',
      endDate: '',
      useFullHistory: false,
      configPath: 'configs/strategies/hma_crossover.default.json',
      initialCapital: 1000,
      scoreMetric: '',
      scoreDirection: 'max',
      optimizationMode: 'grid',
      earlyStopDrawdownPct: 50,
      maxIterations: 10000,
      bayesianIntensity: 'standard',
      enableConvergenceStop: true,
      convergencePatience: 100,
      circuitBreakerRatio: 20,
      useVectorbtPrescan: false,
      runPostValidation: true,
      workers: '',
      minClosedTrades: 1,
      maxDrawdownPct: '',
      minExposurePct: '',
      minProfitFactor: '',
      maxRows: '',
    },

    ...apiMixin(),
    ...formatterMixin(),
    ...parameterRowsMixin(),
    ...estimatesMixin(),
    ...equityChartMixin(),
    ...jobsMixin(),
    ...presetsMixin(),

    async init() {
      if (this.theme === 'dark') document.documentElement.setAttribute('data-theme', 'dark');
      try {
        this.loadPresets();
        const strategies = await this.api('/api/strategies');
        this.strategies = strategies.strategies || [];
        this.form.strategy = this.strategies[0]?.name || '';
        this.applyStrategy(this.form.strategy);
        if (this.form.workers === '' || this.form.workers == null) {
          this.form.workers = navigator.hardwareConcurrency
            ? Math.max(1, Math.floor(navigator.hardwareConcurrency / 2))
            : this.defaultWorkers;
        }
        await this.loadSymbols();
        this.addParameterRow();
        this.addParameterRow();
        await this.estimate();
        await this.refreshJobs();
      } catch (error) {
        this.showError(error.message || String(error));
      }
    },

    currentStrategy() {
      return this.strategies.find(strategy => strategy.name === this.form.strategy) || this.strategies[0] || {};
    },

    async onStrategyChange() {
      this.applyStrategy(this.form.strategy);
      this.parameterRows = [];
      this.addParameterRow();
      this.addParameterRow();
      await this.loadSymbols();
      this.scheduleEstimate(0);
    },

    onOptimizationModeChange() {
      this.calculateBayesianIterations();
      this.scheduleEstimate(0);
    },

    onBayesianIntensityChange() {
      this.bayesianChanged = true;
      setTimeout(() => { this.bayesianChanged = false; }, 1200);
      this.calculateBayesianIterations();
      this.scheduleEstimate(0);
    },

    calculateBayesianIterations() {
      if (this.form.optimizationMode !== 'bayesian') return;

      const rawIterations = Number(this.lastEstimate?.total_iterations ?? 0);
      const canonicalIterations = Number(this.lastEstimate?.canonical_iterations ?? rawIterations);
      const gridSpace = canonicalIterations || rawIterations || 10000;

      const intensityMultipliers = {
        fast: 0.0043,
        standard: 0.0085,
        deep: 0.0256,
      };

      const minIterations = { fast: 300, standard: 500, deep: 1000 };
      const maxIterationsCap = { fast: 6400, standard: 12000, deep: 24000 };

      const multiplier = intensityMultipliers[this.form.bayesianIntensity] || intensityMultipliers.standard;
      const calculated = Math.round(gridSpace * multiplier);
      const clamped = Math.max(
        minIterations[this.form.bayesianIntensity] || 500,
        Math.min(calculated, maxIterationsCap[this.form.bayesianIntensity] || 1500)
      );

      this.form.maxIterations = clamped;
    },

    applyStrategy(strategyName) {
      const strategy = this.strategies.find(item => item.name === strategyName) || this.strategies[0] || {};
      this.parameters = strategy.parameters || [];
      this.schema = strategy.schema || this.parameters;
      this.form.configPath = `configs/strategies/${strategy.name || strategyName}.default.json`;
      this.hydrateScoreMetrics(strategy.score_metrics || ['sharpe_ratio']);
    },

    hydrateScoreMetrics(metrics) {
      const previous = this.form.scoreMetric;
      if (metrics.includes(previous)) this.form.scoreMetric = previous;
      else if (metrics.includes('sharpe_ratio')) this.form.scoreMetric = 'sharpe_ratio';
      else this.form.scoreMetric = metrics[0] || '';
      if (!this.form.scoreMetric) this.showError('Aucune métrique de score disponible pour cette stratégie.');
    },

    scoreMetrics() {
      return this.currentStrategy().score_metrics || [];
    },

    selectedTimeframes() {
      const selected = new Set(Array.isArray(this.form.timeframes) ? this.form.timeframes.map(String) : []);
      const ordered = this.timeframeOptions.map(option => option.value).filter(value => selected.has(value));
      return ordered.length ? ordered : [this.timeframeOptions[0]?.value || '5'];
    },

    timeframeSummary() {
      return this.selectedTimeframes()
        .map(value => this.timeframeOptions.find(option => option.value === value)?.label || `${value} min`)
        .join(', ');
    },

    toggleTimeframe(value) {
      const selected = new Set(this.selectedTimeframes());
      if (selected.has(value)) {
        if (selected.size === 1) return;
        selected.delete(value);
      } else {
        selected.add(value);
      }
      this.form.timeframes = this.timeframeOptions.map(option => option.value).filter(optionValue => selected.has(optionValue));
      this.onDatasetChange();
    },

    toggleAllTimeframes() {
      if (this.selectedTimeframes().length === this.timeframeOptions.length) {
        this.form.timeframes = [this.timeframeOptions[0]?.value || '5'];
      } else {
        this.form.timeframes = this.timeframeOptions.map(option => option.value);
      }
      this.onDatasetChange();
    },


    async loadSymbols() {
      const processedDir = encodeURIComponent(this.form.processedDir);
      const timeframe = encodeURIComponent(this.selectedTimeframes()[0] || '5');
      const payload = await this.api(`/api/symbols?processed_dir=${processedDir}&timeframe=${timeframe}`);
      const previous = this.form.symbol;
      this.symbols = payload.symbols || [];
      this.form.symbol = this.symbols.includes(previous) ? previous : (this.symbols[0] || '');
    },

    async onDatasetChange() {
      try {
        await this.loadSymbols();
        this.scheduleEstimate(0);
      } catch (error) {
        this.showError(error.message || String(error));
      }
    },

    async onFullHistoryChange() {
      if (this.form.useFullHistory) {
        try {
          const timeframe = encodeURIComponent(this.selectedTimeframes()[0] || '5');
          const res = await this.api(`/api/dataset-bounds?symbol=${encodeURIComponent(this.form.symbol)}&processed_dir=${encodeURIComponent(this.form.processedDir)}&timeframe_minutes=${timeframe}`);
          if (res.min_date && res.max_date) {
            this.form.startDate = res.min_date;
            this.form.endDate = res.max_date;
            this.scheduleEstimate(0);
          }
        } catch (error) {
          console.warn('Could not load dataset bounds:', error);
        }
      } else {
        this.form.startDate = '';
        this.form.endDate = '';
        this.scheduleEstimate(0);
      }
    },

    toggleTheme() {
      this.theme = this.theme === 'dark' ? 'light' : 'dark';
      if (this.theme === 'dark') {
        document.documentElement.setAttribute('data-theme', 'dark');
      } else {
        document.documentElement.removeAttribute('data-theme');
      }
      localStorage.setItem('theme', this.theme);
      
      // Update chart if it exists
      if (this.lastEquityPoints && this.lastEquityPoints.length) {
        this.renderEquityChart(this.lastEquityPoints);
      }

      // Re-initialize Lucide icons
      this.$nextTick(() => {
        if (window.lucide) lucide.createIcons();
      });
    },

    async generateGlobalAnalysis() {
      this.isGeneratingAnalysis = true;
      this.globalAnalysisError = '';
      this.globalAnalysisLinks = null;
      try {
        const res = await this.api('/api/global-analysis', {
          method: 'POST',
          body: JSON.stringify({ strategy: this.form.strategy })
        });
        this.globalAnalysisLinks = res;
      } catch (error) {
        this.globalAnalysisError = 'Erreur lors de la génération de la synthèse globale : ' + (error.message || String(error));
      } finally {
        this.isGeneratingAnalysis = false;
      }
    },
  };
}

window.BacktestOptimizer.optimizerApp = optimizerApp;
window.optimizerApp = optimizerApp;