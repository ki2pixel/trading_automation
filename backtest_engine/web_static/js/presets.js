window.BacktestOptimizer = window.BacktestOptimizer || {};

window.BacktestOptimizer.presetsMixin = function presetsMixin() {
  const STORAGE_KEY = 'backtest_optimizer_presets';

  return {
    presets: [],
    newPresetName: '',
    presetsDropdownOpen: false,

    loadPresets() {
      try {
        const saved = localStorage.getItem(STORAGE_KEY);
        this.presets = saved ? JSON.parse(saved) : [];
      } catch (e) {
        console.error('Failed to load presets:', e);
        this.presets = [];
      }
    },

    savePresets() {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(this.presets));
      } catch (e) {
        console.error('Failed to save presets:', e);
      }
    },

    saveCurrentAsPreset() {
      const name = this.newPresetName.trim();
      if (!name) {
        this.showError('Veuillez saisir un nom pour le preset.');
        return;
      }

      const existingIndex = this.presets.findIndex(p => p.name === name);
      const presetData = {
        name,
        timestamp: Date.now(),
        form: JSON.parse(JSON.stringify(this.form)),
        parameterRows: JSON.parse(JSON.stringify(this.parameterRows))
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
      // We don't close the dropdown immediately so user sees the new item
      if (window.lucide) lucide.createIcons();
    },

    applyPreset(preset) {
      if (!preset) return;

      try {
        // 1. Update form (Configuration)
        // We use spread to avoid losing any fields that might have been added to the form structure
        // but were missing in the older preset
        this.form = { ...this.form, ...JSON.parse(JSON.stringify(preset.form)) };

        // 2. Handle Strategy and Parameters
        // If the strategy changed, we need to re-hydrate strategy metadata
        this.applyStrategy(this.form.strategy);

        // 3. Update parameterRows in nextTick to ensure DOM options are rendered
        // otherwise x-model forces the <select> to the first option
        this.$nextTick(() => {
          this.parameterRows = JSON.parse(JSON.stringify(preset.parameterRows));
          
          // Update nextRowId to prevent id collisions if user adds rows later
          let maxId = 0;
          this.parameterRows.forEach(r => {
             if (r.id > maxId) maxId = r.id;
          });
          this.nextRowId = Math.max(this.nextRowId, maxId + 1);

          // 4. Update UI and recalculate
          this.scheduleEstimate(0);
          
          if (window.lucide) {
            this.$nextTick(() => lucide.createIcons());
          }
        });
      } catch (e) {
        this.showError(`Erreur lors de l'application du preset: ${e.message}`);
      }
    },

    deletePreset(name) {
      if (!confirm(`Voulez-vous vraiment supprimer le preset "${name}" ?`)) {
        return;
      }
      this.presets = this.presets.filter(p => p.name !== name);
      this.savePresets();
    }
  };
};
