window.BacktestOptimizer = window.BacktestOptimizer || {};

window.BacktestOptimizer.jobsMixin = function jobsMixin() {
  return {
    selectedJobIds: [],
    async optimize() {
      this.isOptimizing = true;
      try {
        if (this.pollTimer) {
          clearTimeout(this.pollTimer);
          this.pollTimer = null;
        }
        this.clearError();
        this.outputText = '';
        this.activeJobIds = [];
        this.currentRecommendations = null;
        this.recommendationsStatus = 'Les recommandations apparaîtront après une optimisation terminée.';
        this.recommendationsError = '';
        this.resetEquityChart('Optimisation en cours…');
        const timeframes = this.selectedTimeframes();
        let estimatePayload = this.lastEstimate;
        if (!estimatePayload || this.estimateDirty) {
          clearTimeout(this.estimateTimer);
          this.estimateTimer = null;
          estimatePayload = await this.estimate();
          if (!estimatePayload) throw new Error(this.errorMessage || 'Estimation indisponible avant optimisation.');
        } else {
          this.updateOptimizeAvailability(estimatePayload);
        }
        if (!this.canOptimize()) throw new Error(this.errorMessage || 'Optimisation bloquée par la validation UI.');
        const createdJobs = [];
        for (const timeframe of timeframes) {
          const payload = this.collectPayload({ timeframe });
          const job = await this.api('/api/optimize', { method: 'POST', body: JSON.stringify(payload) });
          createdJobs.push(job);
        }
        const job = createdJobs[0];
        if (!job) throw new Error('Aucun job créé. Sélectionnez au moins un timeframe.');
        this.activeJobIds = createdJobs.map(item => item.id).filter(Boolean);
        this.activeJobId = job.id;
        this.currentJob = job;
        this.warnings = [
          ...(estimatePayload?.warnings || []),
          ...(createdJobs.length > 1 ? [`${createdJobs.length} timeframes sélectionnés: ${createdJobs.length} jobs créés dans la file.`] : []),
        ];
        this.outputText = createdJobs.length > 1
          ? `Jobs créés: ${createdJobs.map(item => `${item.request?.timeframe_minutes || '?'} min=${String(item.id || '').slice(0, 10)}`).join(' · ')}`
          : '';
        await this.refreshJobs();
        this.renderJobOutput(job);
        await this.pollJob();
      } catch (error) {
        this.updateOptimizeAvailability(this.lastEstimate, error.message || String(error));
        this.outputText = error.message || String(error);
      } finally {
        this.isOptimizing = false;
      }
    },

    async pollJob() {
      if (this.pollTimer) {
        clearTimeout(this.pollTimer);
        this.pollTimer = null;
      }
      const watchedIds = this.watchedJobIds();
      if (!watchedIds.length) return;
      try {
        await this.refreshJobs();
        const watchedJobs = this.jobs.filter(job => watchedIds.includes(job.id));
        const activeWatchedJobs = watchedJobs
          .filter(job => this.isActiveJob(job))
          .sort((left, right) => this.activeJobSortValue(left) - this.activeJobSortValue(right));
        let selectedJob = this.jobs.find(job => job.id === this.activeJobId) || watchedJobs[0] || null;
        if (activeWatchedJobs.length && (!selectedJob || !this.isActiveJob(selectedJob))) {
          selectedJob = activeWatchedJobs[0];
        }
        if (selectedJob) {
          this.activeJobId = selectedJob.id;
          this.currentJob = selectedJob;
          this.renderJobOutput(selectedJob);
        }
        if (activeWatchedJobs.length) {
          this.pollTimer = setTimeout(() => this.pollJob(), 1000);
        } else if (selectedJob) {
          await this.loadRecommendations(selectedJob);
          await this.loadBestEquity(selectedJob);
        }
      } catch (error) {
        this.showError(error.message || String(error));
      }
    },

    watchedJobIds() {
      const ids = Array.isArray(this.activeJobIds) ? this.activeJobIds.filter(Boolean) : [];
      if (!ids.length && this.activeJobId) ids.push(this.activeJobId);
      return [...new Set(ids)];
    },

    isActiveJob(job) {
      return ['PENDING', 'IN_PROGRESS'].includes(job?.status);
    },

    activeJobSortValue(job) {
      const statusWeight = job?.status === 'IN_PROGRESS' ? 0 : 1;
      const createdAt = Number(job?.created_at || 0);
      return statusWeight * 1e15 + createdAt;
    },

    jobRowClasses(job) {
      return {
        selected: job?.id && job.id === this.activeJobId,
        watched: job?.id && this.watchedJobIds().includes(job.id),
      };
    },

    async selectJob(job) {
      if (!job?.id) return;
      // Réinitialiser l'état UI avant de changer de job pour éviter les transitions invalides
      this.currentRecommendations = null;
      this.recommendationsError = '';
      this.recommendationsStatus = 'Chargement...';
      this.resetEquityChart('Chargement de la courbe...');
      // Attendre le prochain tick pour laisser Alpine.js nettoyer le DOM
      await new Promise(resolve => this.$nextTick(resolve));
      this.activeJobId = job.id;
      this.currentJob = job;
      this.renderJobOutput(job);
      if (this.isActiveJob(job)) {
        this.currentRecommendations = null;
        this.recommendationsError = '';
        this.recommendationsStatus = 'Recommandations indisponibles tant que ce job est en cours.';
        this.resetEquityChart('La courbe apparaîtra après une optimisation terminée avec Best Run.');
        if (!this.pollTimer) await this.pollJob();
      } else {
        await this.loadRecommendations(job);
        await this.loadBestEquity(job);
      }
    },

    renderJobOutput(job) {
      if (job.output_dir) this.outputText = `Sorties: ${job.output_dir}`;
      else if (job.error) this.outputText = job.error;
    },

    async cancelJob() {
      if (!this.activeJobId) return;
      await this.api(`/api/jobs/${this.activeJobId}/cancel`, { method: 'POST', body: '{}' });
      await this.pollJob();
    },

    async cancelAllJobs() {
      const activeJobs = this.jobs.filter(job => this.isActiveJob(job));
      if (!activeJobs.length) return;
      const count = activeJobs.length;
      if (!window.confirm(`Voulez-vous vraiment arrêter les ${count} job(s) actif(s) ?`)) return;
      try {
        this.clearError();
        const response = await this.api('/api/jobs/bulk-cancel', {
          method: 'POST',
          body: JSON.stringify({ job_ids: activeJobs.map(j => j.id) })
        });
        const cancelledCount = response.cancelled ?? 0;
        const errors = response.errors || [];
        if (errors.length > 0) {
          this.showError(`${cancelledCount} job(s) annulé(s). ${errors.length} erreur(s).`);
        }
        await this.pollJob();
      } catch (error) {
        this.showError(error.message || String(error));
      }
    },

    async deleteJob(job) {
      if (!job?.id) return;
      if (this.isActiveJob(job) && !job.cancel_requested) {
        this.showError('Ce job est encore actif. Stoppez-le ou attendez sa fin avant suppression.');
        return;
      }
      const shortId = String(job.id).slice(0, 10);
      const outputDir = job.output_dir ? `\n\nDossier supprimé: ${job.output_dir}` : '';
      const confirmed = window.confirm(
        `Supprimer définitivement le job ${shortId}, sa ligne en base SQLite et ses données de rapport ?${outputDir}`
      );
      if (!confirmed) return;

      try {
        this.clearError();
        await this.api(`/api/jobs/${encodeURIComponent(job.id)}`, { method: 'DELETE' });
        this.activeJobIds = (this.activeJobIds || []).filter(id => id !== job.id);
        if (this.activeJobId === job.id) {
          this.activeJobId = null;
          this.currentJob = null;
          this.currentRecommendations = null;
          this.recommendationsError = '';
          this.recommendationsStatus = 'Sélectionnez un job terminé pour afficher les recommandations.';
          this.resetEquityChart('Sélectionnez un job terminé pour afficher la courbe.');
          this.outputText = '';
        }
        await this.refreshJobs();
        if (!this.activeJobId && this.jobs.length) {
          await this.selectJob(this.jobs[0]);
        } else if (this.watchedJobIds().some(id => this.jobs.some(item => item.id === id && this.isActiveJob(item)))) {
          await this.pollJob();
        }
      } catch (error) {
        this.showError(error.message || String(error));
      }
    },

    async refreshJobs() {
      const payload = await this.api('/api/jobs');
      this.jobs = payload.jobs || [];
    },

    async loadRecommendations(job) {
      this.currentRecommendations = null;
      this.recommendationsError = '';
      if (!job?.id || !job.output_dir || !['FINISHED', 'FINISHED_CONVERGED', 'CANCELLED'].includes(job.status)) {
        this.recommendationsStatus = 'Recommandations indisponibles pour ce job.';
        return;
      }
      try {
        this.recommendationsStatus = 'Chargement des recommandations…';
        const payload = await this.api(`/api/jobs/${job.id}/recommendations`);
        this.currentRecommendations = payload;
        const selected = payload?.candidate_pool?.selected_rows;
        const eligible = payload?.candidate_pool?.eligible_rows;
        this.recommendationsStatus = selected != null && eligible != null
          ? `${selected}/${eligible} itérations robustes analysées.`
          : 'Recommandations chargées.';
      } catch (error) {
        this.recommendationsStatus = 'Recommandations indisponibles.';
        this.recommendationsError = error.message || String(error);
      }
    },

    progressPercent() {
      const progress = this.currentJob?.progress || {};
      const current = Number(progress.currentIteration || 0);
      const total = Number(progress.totalIterations || 0);
      return total ? Math.min(100, current / total * 100) : 0;
    },

    progressText() {
      if (!this.currentJob) return 'Aucun run en cours.';
      const progress = this.currentJob.progress || {};
      const base = `${this.formatJobTimeframe(this.currentJob)} · ${this.currentJob.status} · ${progress.currentIteration || 0}/${progress.totalIterations || 0}`;
      const watchedIds = this.watchedJobIds();
      if (watchedIds.length <= 1) return base;
      const watchedJobs = this.jobs.filter(job => watchedIds.includes(job.id));
      const finishedCount = watchedJobs.filter(job => !this.isActiveJob(job)).length;
      const activeCount = watchedJobs.filter(job => this.isActiveJob(job)).length;
      return `${base} · Lot: ${finishedCount}/${watchedIds.length} terminés, ${activeCount} actifs`;
    },

    bestText() {
      return this.currentJob?.best ? `Best: ${this.formatBestSummary(this.currentJob.best)}` : '';
    },

    toggleJobSelection(jobId) {
      if (this.selectedJobIds.includes(jobId)) {
        this.selectedJobIds = this.selectedJobIds.filter(id => id !== jobId);
      } else {
        this.selectedJobIds = [...this.selectedJobIds, jobId];
      }
    },

    isAllJobsSelected() {
      if (!this.jobs.length) return false;
      return this.jobs.every(job => this.selectedJobIds.includes(job.id));
    },

    toggleSelectAllJobs() {
      if (this.isAllJobsSelected()) {
        const visibleIds = this.jobs.map(j => j.id);
        this.selectedJobIds = this.selectedJobIds.filter(id => !visibleIds.includes(id));
      } else {
        const visibleIds = this.jobs.map(j => j.id);
        const newSelection = new Set([...this.selectedJobIds, ...visibleIds]);
        this.selectedJobIds = Array.from(newSelection);
      }
    },

    async deleteSelectedJobs() {
      if (!this.selectedJobIds.length) return;
      
      const count = this.selectedJobIds.length;
      const confirmed = window.confirm(
        `Supprimer définitivement les ${count} jobs sélectionnés ainsi que leurs données de rapport ?`
      );
      if (!confirmed) return;

      try {
        this.clearError();
        const response = await this.api('/api/jobs/bulk-delete', {
          method: 'POST',
          body: JSON.stringify({ job_ids: this.selectedJobIds })
        });

        if (this.selectedJobIds.includes(this.activeJobId)) {
          this.activeJobId = null;
          this.currentJob = null;
          this.currentRecommendations = null;
          this.recommendationsError = '';
          this.recommendationsStatus = 'Sélectionnez un job terminé pour afficher les recommandations.';
          this.resetEquityChart('Sélectionnez un job terminé pour afficher la courbe.');
          this.outputText = '';
        }

        const deletedCount = response.deleted ?? 0;
        const skippedCount = response.skipped_active ?? 0;
        const errors = response.errors || [];
        
        this.selectedJobIds = [];
        await this.refreshJobs();

        let message = `Résumé de la suppression :\n- ${deletedCount} job(s) supprimé(s).`;
        if (skippedCount > 0) {
          message += `\n- ${skippedCount} job(s) actif(s) ignoré(s).`;
        }
        if (errors.length > 0) {
          message += `\n- ${errors.length} erreur(s) rencontrée(s) : \n  ` + errors.slice(0, 5).join('\n  ');
          if (errors.length > 5) {
            message += `\n  ... et ${errors.length - 5} autres erreurs.`;
          }
        }
        window.alert(message);

        if (!this.activeJobId && this.jobs.length) {
          await this.selectJob(this.jobs[0]);
        }
      } catch (error) {
        this.showError(error.message || String(error));
      }
    },
  };
};