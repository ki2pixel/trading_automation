window.BacktestOptimizer = window.BacktestOptimizer || {};

window.BacktestOptimizer.parameterRowsMixin = function parameterRowsMixin() {
  return {
    optionLabel(param) {
      if (!param || typeof param !== 'object') return '';
      return `${param.name || ''} (${param.value_type || ''})`;
    },

    addParameterRow(defaultName = null) {
      const selected = new Set(this.selectedParameterNames());
      let name = defaultName;
      if (!name || !this.parameters.some(param => param.name === name) || selected.has(name)) {
        name = this.parameters.find(param => !selected.has(param.name))?.name || null;
      }
      if (!name) {
        this.showError('Tous les paramètres optimisables sont déjà présents. Supprimez une ligne avant d’en ajouter une autre.');
        return null;
      }
      const row = { id: this.nextRowId++, name, kind: 'numeric', start: '', end: '', step: '', values: '', error: '' };
      this.hydrateDefaults(row);
      this.parameterRows.push(row);
      this.scheduleEstimate(0);
      this.$nextTick(() => { if (window.lucide) lucide.createIcons(); });
      return row;
    },

    removeParameterRow(row) {
      this.parameterRows = this.parameterRows.filter(item => item.id !== row.id);
      this.scheduleEstimate(0);
    },

    onParameterNameChange(row) {
      this.hydrateDefaults(row);
      this.scheduleEstimate(0);
    },

    hydrateDefaults(row) {
      const metadata = this.parameterMetadata(row.name);
      row.kind = metadata.kind || 'numeric';
      row.start = metadata.default_start ?? '';
      row.end = metadata.default_end ?? '';
      row.step = metadata.default_step ?? '';
      row.values = (metadata.choices || []).join('|');
      row.error = '';
    },

    parameterMetadata(name) {
      return this.parameters.find(param => param.name === name) || this.schemaParameterMetadata(name) || {};
    },

    schemaParameterMetadata(name) {
      return this.schema.find(param => param.name === name) || null;
    },

    selectedParameterNames() {
      return this.parameterRows.map(row => row.name).filter(Boolean);
    },

    duplicateNames() {
      const counts = new Map();
      this.selectedParameterNames().forEach(name => counts.set(name, (counts.get(name) || 0) + 1));
      return new Set(Array.from(counts.entries()).filter(([, count]) => count > 1).map(([name]) => name));
    },

    duplicateError() {
      const duplicate = Array.from(this.duplicateNames())[0];
      return duplicate ? `Paramètre dupliqué: ${duplicate}. Gardez une seule ligne par paramètre.` : '';
    },

    isOptionDisabled(optionName, row) {
      return this.parameterRows.some(other => other.id !== row.id && other.name === optionName);
    },

    inactiveNames() {
      return new Set(this.lastEstimate?.inactive_parameters || []);
    },

    rowClasses(row) {
      const duplicate = this.duplicateNames().has(row.name);
      const inactive = !duplicate && this.inactiveNames().has(row.name);
      return { choice: row.kind === 'choice', bool: row.kind === 'bool', duplicate, inactive };
    },

    rowNote(row) {
      if (row.error) return row.error;
      if (this.duplicateNames().has(row.name)) return 'Doublon: gardez une seule ligne pour ce paramètre avant de lancer l’optimisation.';
      if (this.inactiveNames().has(row.name)) return `Inactif: ${this.inactiveReasonFor(row.name)}. Ces valeurs sont dédupliquées dans la grille canonique.`;
      return this.activeConditionHint(row.name);
    },

    activeConditionHint(name) {
      const metadata = this.schemaParameterMetadata(name);
      if (!metadata?.active_if) return '';
      return `Actif si ${this.formatConditions(metadata.active_if)}.`;
    },

    inactiveReasonFor(name) {
      const metadata = this.schemaParameterMetadata(name);
      if (metadata?.active_if) return `condition non satisfaite (${this.formatConditions(metadata.active_if)})`;
      if (name.includes('_short')) return 'désactivé par une règle de direction de trading côté short';
      if (name.includes('_long')) return 'désactivé par une règle de direction de trading côté long';
      if (name.startsWith('safety_')) return 'désactivé par la configuration safety stop courante';
      return 'règle d’inactivité backend selon la configuration courante';
    },

    formatConditions(conditions) {
      return Object.entries(conditions).map(([key, value]) => `${key}=${String(value)}`).join(' et ');
    },

    validateParameterRows() {
      let firstError = this.duplicateError();
      this.parameterRows.forEach(row => { row.error = ''; });
      for (const row of this.parameterRows) {
        const metadata = this.parameterMetadata(row.name);
        if (row.kind === 'numeric') {
          const values = { start: row.start || metadata.default_start, end: row.end || metadata.default_end, step: row.step || metadata.default_step };
          if (values.start === '' || values.start == null || values.end === '' || values.end == null || values.step === '' || values.step == null) {
            row.error = `Le paramètre ${row.name} nécessite start, end et step. Valeurs par défaut indisponibles pour compléter les champs vides.`;
          } else if (metadata.value_type === 'int') {
            for (const [label, value] of Object.entries(values)) {
              if (!Number.isInteger(Number(value))) {
                row.error = `Le paramètre ${row.name} est entier: ${label} doit être un nombre entier.`;
                break;
              }
            }
          }
        } else if (!row.values.split('|').map(v => v.trim()).filter(Boolean).length) {
          row.error = `Le paramètre ${row.name} nécessite au moins une valeur.`;
        }
        if (!firstError && row.error) firstError = row.error;
      }
      if (!firstError && !this.parameterRows.length) firstError = 'Ajoutez au moins un paramètre à optimiser.';
      if (!firstError && !this.form.scoreMetric) firstError = 'Sélectionnez une métrique de score.';
      return firstError;
    },

    collectPayload(options = {}) {
      const validationError = this.validateParameterRows();
      if (validationError) throw new Error(validationError);
      const timeframe = options.timeframe ?? this.selectedTimeframes()[0] ?? '5';
      return {
        strategy: this.form.strategy,
        symbol: this.form.symbol,
        processed_dir: this.form.processedDir,
        timeframe_minutes: Number(timeframe || 5),
        start_date: this.form.startDate || null,
        end_date: this.form.endDate || null,
        config: this.form.configPath || null,
        initial_capital: Number(this.form.initialCapital || 1000),
        score_metric: this.form.scoreMetric,
        score_direction: this.form.scoreDirection,
        optimization_mode: this.form.optimizationMode,
        early_stop_drawdown_pct: (this.form.earlyStopDrawdownPct === '' || this.form.earlyStopDrawdownPct == null) ? null : Number(this.form.earlyStopDrawdownPct),
        max_iterations: Number(this.form.maxIterations || 10000),
        workers: Number((this.form.workers === '' || this.form.workers == null) ? this.defaultWorkers : this.form.workers),
        min_closed_trades: Number(this.form.minClosedTrades === '' ? 1 : this.form.minClosedTrades),
        max_drawdown_pct: this.form.maxDrawdownPct === '' ? null : Number(this.form.maxDrawdownPct),
        min_exposure_pct: this.form.minExposurePct === '' ? null : Number(this.form.minExposurePct),
        min_profit_factor: this.form.minProfitFactor === '' ? null : Number(this.form.minProfitFactor),
        max_rows: this.form.maxRows ? Number(this.form.maxRows) : null,
        enable_convergence_stop: Boolean(this.form.enableConvergenceStop),
        convergence_patience: Number(this.form.convergencePatience || 100),
        circuit_breaker_ratio: (this.form.circuitBreakerRatio === '' || this.form.circuitBreakerRatio == null) ? 0.2 : Number(this.form.circuitBreakerRatio) / 100.0,
        use_vectorbt_prescan: Boolean(this.form.useVectorbtPrescan),
        run_post_validation: Boolean(this.form.runPostValidation),
        write_best_run: true,
        parameters: this.parameterRows.map(row => {
          const item = { name: row.name, kind: row.kind };
          const metadata = this.parameterMetadata(row.name);
          if (row.kind === 'numeric') {
            item.start = row.start || metadata.default_start;
            item.end = row.end || metadata.default_end;
            item.step = row.step || metadata.default_step;
          } else {
            item.values = row.values.split('|').map(v => v.trim()).filter(Boolean);
          }
          return item;
        }),
      };
    },
  };
};