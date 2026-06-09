document.addEventListener('alpine:init', () => {
  Alpine.data('viewerApp', () => ({
    theme: localStorage.getItem('theme') || 'light',
    strategy: 'hma_crossover',
    symbol: 'AAPL',
    timeframe: '1h',
    startDate: '',
    endDate: '',
    useFullHistory: false,
    initialCapital: 1000,
    strategyParams: [],
    paramValues: {},
    chart: null,
    isLoading: false,
    sidebarOpen: false,
    sidebarWidth: 320,
    error: null,
    availableSymbols: [],
    availableTimeframes: [],
    availableStrategies: [],
    indicatorData: {},
    signalOverlayIds: [],
    chartType: localStorage.getItem('viewer_chart_type') || 'candle_solid',
    
    presets: [],
    newPresetName: '',
    presetsExpanded: false,

    _allViewerIndicators: [
      'hma_fast', 'hma_slow',
      'avt_adaptive_trend', 'avt_upper_band', 'avt_lower_band',
      'range_filter', 'hband', 'lband',
      'ma1', 'ma2', 'atr',
      'sLow', 'sHigh', 'pattern_tp', 'pattern_sl',
      'sine_wave', 'lead_wave', 'phase_mode', 'dominant_cycle',
    ],

    _getStrategyIndicatorNames(strategy) {
      const mapping = {
        hma_crossover: ['hma_fast', 'hma_slow'],
        pmax_explorer: ['mavg', 'pmax'],
        adaptive_volatility_trend: ['avt_adaptive_trend', 'avt_upper_band', 'avt_lower_band'],
        range_filter: ['range_filter', 'hband', 'lband'],
        '3commas_bot': ['ma1', 'ma2', 'atr'],
        bjorgum_double_tap: ['sLow', 'sHigh', 'atr', 'pattern_tp', 'pattern_sl'],
        cybernetic_hilbert: ['sine_wave', 'lead_wave', 'phase_mode', 'dominant_cycle'],
      };
      return mapping[strategy] || [];
    },

    init() {
      this.applyTheme();
      this.initChart();
      this.loadPresets();
      if (this._initialized) return;
      this._initialized = true;
      this.loadSymbols().then(() => {
        this.loadTimeframes().then(() => {
          this.loadStrategies().then(() => {
            this.loadStrategyParameters().then(() => {
              this.$nextTick(() => {
                this.refreshData();
                lucide.createIcons();
              });
            });
          });
        });
      });
    },

    async loadStrategies() {
      try {
        const res = await fetch('/api/strategies');
        const data = await res.json();
        if (res.ok && data.strategies) {
          this.availableStrategies = data.strategies;
          const names = data.strategies.map(s => s.name);
          if (names.length && !names.includes(this.strategy)) {
            this.strategy = names[0];
          }
        }
      } catch (err) {
        console.warn('Could not load strategies:', err);
      }
    },

    async loadStrategyParameters() {
      try {
        const res = await fetch('/api/strategies');
        const data = await res.json();
        if (res.ok && data.strategies && data.strategies.length > 0) {
          const strat = data.strategies.find(s => s.name === this.strategy) || data.strategies[0];
          this.strategyParams = strat.schema || strat.parameters || [];
          // Reset paramValues for params that are no longer in the current strategy
          const newValues = {};
          this.strategyParams.forEach(p => {
            newValues[p.name] = this.paramValues[p.name] !== undefined
              ? this.paramValues[p.name]
              : (p.default !== undefined ? p.default : null);
          });
          this.paramValues = newValues;
        }
      } catch (err) {
        console.warn('Could not load strategy parameters:', err);
      }
    },

    async onStrategyChange() {
      this.paramValues = {};
      this.strategyParams = [];
      await this.loadStrategyParameters();
      this.destroyChart();
      this.initChart();
      this.$nextTick(() => {
        lucide.createIcons();
        this.refreshData();
      });
    },

    timeframeToMinutes(tf) {
      if (!tf) return 60;
      const lower = String(tf).toLowerCase().trim();
      const m = { '1m': 1, '5m': 5, '15m': 15, '1h': 60, '4h': 240, '1d': 1440 };
      if (m[lower] !== undefined) return m[lower];
      const match = lower.match(/^(\d+)([mhd])$/);
      if (!match) return parseInt(lower, 10) || 60;
      const val = parseInt(match[1], 10);
      const unit = match[2];
      if (unit === 'm') return val;
      if (unit === 'h') return val * 60;
      if (unit === 'd') return val * 60 * 24;
      return val;
    },

    async loadSymbols() {
      try {
        const tf = this.timeframe || '1h';
        const minutes = this.timeframeToMinutes(tf);
        const res = await fetch(`/api/symbols?timeframe_minutes=${minutes}`);
        const data = await res.json();
        if (res.ok && data.symbols) {
          this.availableSymbols = data.symbols;
          if (this.availableSymbols.length && !this.availableSymbols.includes(this.symbol)) {
            this.symbol = this.availableSymbols[0];
          }
        }
      } catch (err) {
        console.warn('Could not load symbols:', err);
      }
    },

    async loadTimeframes() {
      try {
        const res = await fetch(`/api/viewer/timeframes?symbol=${encodeURIComponent(this.symbol)}`);
        const data = await res.json();
        if (res.ok && data.timeframes) {
          this.availableTimeframes = data.timeframes;
          const values = this.availableTimeframes.map(t => t.value);
          if (values.length && !values.includes(this.timeframe)) {
            this.timeframe = values[0];
          }
        }
      } catch (err) {
        console.warn('Could not load timeframes:', err);
      }
    },

    async onSymbolChange() {
      await this.loadTimeframes();
      await this.refreshData();
    },

    async onFullHistoryChange() {
      if (this.useFullHistory) {
        try {
          const minutes = this.timeframeToMinutes(this.timeframe);
          const res = await fetch(`/api/dataset-bounds?symbol=${encodeURIComponent(this.symbol)}&timeframe_minutes=${minutes}`);
          const data = await res.json();
          if (res.ok && data.min_date && data.max_date) {
            this.startDate = data.min_date;
            this.endDate = data.max_date;
          }
        } catch (err) {
          console.warn('Could not load dataset bounds:', err);
        }
      } else {
        this.startDate = '';
        this.endDate = '';
      }
    },

    loadPresets() {
      try {
        const saved = localStorage.getItem('backtest_viewer_presets');
        this.presets = saved ? JSON.parse(saved) : [];
      } catch (e) {
        console.error('Failed to load presets:', e);
        this.presets = [];
      }
    },

    savePresets() {
      try {
        localStorage.setItem('backtest_viewer_presets', JSON.stringify(this.presets));
      } catch (e) {
        console.error('Failed to save presets:', e);
      }
    },

    saveCurrentAsPreset() {
      const name = this.newPresetName.trim();
      if (!name) {
        alert('Veuillez saisir un nom pour le preset.');
        return;
      }
      const existingIndex = this.presets.findIndex(p => p.name === name);
      const presetData = {
        name,
        timestamp: Date.now(),
        strategy: this.strategy,
        symbol: this.symbol,
        timeframe: this.timeframe,
        startDate: this.startDate,
        endDate: this.endDate,
        useFullHistory: this.useFullHistory,
        initialCapital: this.initialCapital,
        paramValues: JSON.parse(JSON.stringify(this.paramValues)),
        chartType: this.chartType
      };
      if (existingIndex !== -1) {
        if (!confirm(`Un preset nommé "${name}" existe déjà. Voulez-vous l'écraser ?`)) {
          return;
        }
        this.presets[existingIndex] = presetData;
      } else {
        this.presets.unshift(presetData);
      }
      this.savePresets();
      this.newPresetName = '';
      if (window.lucide) this.$nextTick(() => lucide.createIcons());
    },

    applyPreset(preset) {
      if (!preset) return;
      try {
        const oldStrategy = this.strategy;
        this.strategy = preset.strategy || 'hma_crossover';
        this.symbol = preset.symbol || (this.availableSymbols.length ? this.availableSymbols[0] : 'AAPL');
        this.timeframe = preset.timeframe || '1h';
        this.useFullHistory = preset.useFullHistory || false;
        this.startDate = preset.startDate || '';
        this.endDate = preset.endDate || '';
        this.initialCapital = preset.initialCapital || 1000;
        this.chartType = preset.chartType || 'candle_solid';
        this.paramValues = { ...this.paramValues, ...JSON.parse(JSON.stringify(preset.paramValues || {})) };
        this.onChartTypeChange();
        
        this.presetsExpanded = false;
        if (oldStrategy !== this.strategy) {
          this.loadStrategyParameters().then(() => {
            this.destroyChart();
            this.initChart();
            this.$nextTick(() => {
              lucide.createIcons();
              this.onSymbolChange();
            });
          });
        } else {
          this.onSymbolChange();
        }
      } catch (e) {
        console.error("Erreur lors de l'application du preset:", e);
        alert(`Erreur lors de l'application du preset: ${e.message}`);
      }
    },

    deletePreset(name) {
      if (!confirm(`Voulez-vous vraiment supprimer le preset "${name}" ?`)) {
        return;
      }
      this.presets = this.presets.filter(p => p.name !== name);
      this.savePresets();
    },

    registerCustomIndicators() {
      const self = this;
      if (typeof klinecharts !== 'undefined' && klinecharts.registerIndicator) {
        this._allViewerIndicators.forEach(name => {
          klinecharts.registerIndicator({
            name: name,
            shortName: name,
            calc: (kLineDataList) => {
              const dataMap = self.indicatorData[name];
              return kLineDataList.map(k => ({
                [name]: dataMap ? dataMap.get(k.timestamp) ?? null : null
              }));
            },
            figures: [{ key: name, title: name, type: 'line' }],
          });
        });
      }
      if (typeof klinecharts !== 'undefined' && klinecharts.registerOverlay) {
        klinecharts.registerOverlay({
          name: 'signalLabel',
          totalStep: 1,
          createPointFigures: ({ overlay, coordinates }) => {
            const { text, color, offset = -20 } = overlay.extendData || {};
            if (!text) return [];
            return [{
              type: 'text',
              attrs: {
                x: coordinates[0].x,
                y: coordinates[0].y + offset,
                text,
                color: color || '#000',
                align: 'center',
                baseline: 'bottom'
              },
              ignoreEvent: true
            }];
          }
        });
      }
    },

    toggleTheme() {
      this.theme = this.theme === 'dark' ? 'light' : 'dark';
      localStorage.setItem('theme', this.theme);
      this.applyTheme();
    },

    applyTheme() {
      document.documentElement.setAttribute('data-theme', this.theme);
      if (this.chart && typeof this.chart.setStyles === 'function') {
        try { this.chart.setStyles(this.getChartStyles()); } catch (e) { /* ignore */ }
      }
    },

    getChartStyles() {
      const isDark = this.theme === 'dark';
      return {
        grid: {
          horizontal: { color: isDark ? '#1e293b' : '#e2e8f0', style: 'dashed' },
          vertical:   { color: isDark ? '#1e293b' : '#e2e8f0', style: 'dashed' },
        },
        candle: {
          type: this.chartType,
          bar: {
            compareRule: 'current_open',
            upColor:        '#22c55e',
            downColor:      '#ef4444',
            noChangeColor:  '#22c55e',
            upBorderColor:  '#22c55e',
            downBorderColor:'#ef4444',
            upWickColor:    '#22c55e',
            downWickColor:  '#ef4444',
            noChangeBorderColor: '#22c55e',
            noChangeWickColor:   '#22c55e',
          }
        },
        indicator: {
          ohlc: {
            compareRule: 'current_open',
            upColor:   'rgba(34,197,94,0.7)',
            downColor: 'rgba(239,68,68,0.7)',
            noChangeColor: 'rgba(34,197,94,0.7)',
          },
        },
        xAxis: {
          axisLine: { color: isDark ? '#334155' : '#cbd5e1' },
          tickLine: { color: isDark ? '#334155' : '#cbd5e1' },
          tickText: { color: isDark ? '#94a3b8' : '#64748b' },
        },
        yAxis: {
          axisLine: { color: isDark ? '#334155' : '#cbd5e1' },
          tickLine: { color: isDark ? '#334155' : '#cbd5e1' },
          tickText: { color: isDark ? '#94a3b8' : '#64748b' },
        },
        separator: {
          color: isDark ? '#1e293b' : '#e2e8f0',
          size: 1,
        },
        crosshair: {
          horizontal: {
            line: { color: isDark ? '#94a3b8' : '#64748b', style: 'dashed' },
            text: { color: isDark ? '#f8fafc' : '#0f172a', backgroundColor: isDark ? '#0f172a' : '#ffffff' },
          },
          vertical: {
            line: { color: isDark ? '#94a3b8' : '#64748b', style: 'dashed' },
            text: { color: isDark ? '#f8fafc' : '#0f172a', backgroundColor: isDark ? '#0f172a' : '#ffffff' },
          },
        },
      };
    },

    onChartTypeChange() {
      localStorage.setItem('viewer_chart_type', this.chartType);
      // Guard: KLineChart v8 needs data loaded before setStyles/resize work
      if (!this.chart || typeof this.chart.setStyles !== 'function') return;
      try {
        this.chart.setStyles(this.getChartStyles());
      } catch (e) { /* ignore setStyles errors on empty chart */ }
      if (typeof this.chart.resize === 'function') {
        try { this.chart.resize(); } catch (e) { /* ignore */ }
      }
    },

    startResizeSidebar(e) {
      const startX = e.clientX;
      const startWidth = this.sidebarWidth || 320;
      const onMove = (ev) => {
        this.sidebarWidth = Math.max(240, Math.min(600, startWidth + ev.clientX - startX));
      };
      const onUp = () => {
        document.removeEventListener('mousemove', onMove);
        document.removeEventListener('mouseup', onUp);
        if (this.chart) this.chart.resize();
      };
      document.addEventListener('mousemove', onMove);
      document.addEventListener('mouseup', onUp);
    },

    initChart() {
      const container = document.getElementById('klinechart');
      if (!container) {
        console.warn('Conteneur #klinechart introuvable');
        return;
      }
      if (typeof klinecharts === 'undefined') {
        console.warn('KLineChart non disponible — le script n\'a pas chargé');
        container.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#ef4444;font-weight:bold;">Erreur : KLineChart n\'a pas pu charger. Verifiez votre connexion.</div>';
        return;
      }

      if (this._chartResizeObserver) {
        this._chartResizeObserver.disconnect();
        this._chartResizeObserver = null;
      }
      if (this.chart) {
        this.chart.destroy();
      }

      this.registerCustomIndicators();

      this.chart = klinecharts.init('klinechart', {
        styles: this.getChartStyles(),
      });

      this._chartResizeObserver = new ResizeObserver(() => {
        if (this.chart && typeof this.chart.resize === 'function') {
          try { this.chart.resize(); } catch (e) { /* ignore */ }
        }
      });
      this._chartResizeObserver.observe(container);

      const indNames = this._getStrategyIndicatorNames(this.strategy);
      if (this.chart && typeof this.chart.createIndicator === 'function') {
        indNames.forEach(name => {
          try { this.chart.createIndicator(name); } catch (e) { /* ignore */ }
        });
      }
    },

    async refreshData() {
      if (this.isLoading) return;
      this.isLoading = true;
      this.error = null;

      // Clear previous signal overlays
      this.signalOverlayIds.forEach(id => {
        try { this.chart.removeOverlay(id); } catch (e) { /* ignore */ }
      });
      this.signalOverlayIds = [];

      try {
        const payload = {
          strategy: this.strategy,
          symbol: this.symbol,
          timeframe: this.timeframe,
          start_date: this.startDate || null,
          end_date: this.endDate || null,
          initial_capital: this.initialCapital,
          ...this.paramValues
        };
        const res = await fetch('/api/viewer/chart-data', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        const data = await res.json();
        console.log('API response', data);
        if (!res.ok || data.error) {
          this.error = data.error || `Erreur API ${res.status}`;
          console.error('API error:', this.error);
          this.isLoading = false;
          return;
        }
        if (!data.klines || !data.klines.length) {
          this.error = 'Aucune donnee retournee pour ce symbole/timeframe.';
          this.isLoading = false;
          return;
        }

        // Populate indicator data maps
        this.indicatorData = {};
        if (data.indicators) {
          Object.keys(data.indicators).forEach(name => {
            this.indicatorData[name] = new Map();
            (data.indicators[name] || []).forEach(p => {
              this.indicatorData[name].set(p.timestamp, p.value);
            });
          });
        }

        if (this.chart && data.klines && data.klines.length) {
          if (typeof this.chart.applyNewData === 'function') {
            this.chart.applyNewData(data.klines);
          }
        }

        // Render signal overlays
        if (this.chart && typeof this.chart.createOverlay === 'function') {
          (data.signals || []).forEach(signal => {
            const overlay = this.makeSignalOverlay(signal);
            if (overlay) {
              const id = this.chart.createOverlay(overlay);
              if (id) this.signalOverlayIds.push(id);
            }
          });
        }
      } catch (err) {
        console.error('Network error:', err);
      } finally {
        this.isLoading = false;
      }
    },

    makeSignalOverlay(signal) {
      const ts = signal.timestamp;
      const price = signal.price;
      if (signal.type === 'entry') {
        const isLong = signal.side === 'LONG';
        return {
          name: 'signalLabel',
          points: [{ timestamp: ts, value: price }],
          extendData: {
            text: isLong ? '▲ Buy' : '▼ Sell',
            color: isLong ? '#22c55e' : '#ef4444',
            offset: -25
          }
        };
      } else if (signal.type === 'exit') {
        const pnl = signal.pnl;
        const hasPnl = pnl !== null && pnl !== undefined;
        const color = hasPnl && pnl >= 0 ? '#3b82f6' : '#f97316';
        const text = hasPnl ? `Exit ${pnl >= 0 ? '+' : ''}${pnl.toFixed(2)}` : 'Exit';
        return {
          name: 'signalLabel',
          points: [{ timestamp: ts, value: price }],
          extendData: {
            text,
            color,
            offset: 15
          }
        };
      }
      return null;
    },

    destroyChart() {
      this.signalOverlayIds.forEach(id => {
        try { this.chart.removeOverlay(id); } catch (e) { /* ignore */ }
      });
      this.signalOverlayIds = [];
      this.indicatorData = {};
      if (this.chart) {
        this.chart.destroy();
        this.chart = null;
      }
      if (this._chartResizeObserver) {
        this._chartResizeObserver.disconnect();
        this._chartResizeObserver = null;
      }
    },
  }));
});
