window.BacktestOptimizer = window.BacktestOptimizer || {};

let chartInstance = null;
let candleSeries = null;
let equitySeries = null;
let chartResizeObserver = null;

window.BacktestOptimizer.equityChartMixin = function equityChartMixin() {
  return {
    async loadBestEquity(job) {
      if (!job?.id || !job.best?.best_backtest_dir) {
        this.resetEquityChart('Aucun Best Run exploitable pour afficher une courbe d’équité.');
        return;
      }
      try {
        this.equityStatus = 'Chargement des données du graphique…';
        this.equityError = '';
        const payload = await this.api(`/api/jobs/${job.id}/chart-data`);
        this.lastChartData = payload;
        this.renderInteractiveChart(payload);
      } catch (error) {
        this.resetEquityChart('Graphique indisponible.');
        this.equityError = error.message || String(error);
      }
    },

    renderInteractiveChart(data) {
      if (!data || (!data.ohlc.length && !data.equity.length)) {
        this.resetEquityChart('Les données du graphique sont vides.');
        return;
      }
      this.equityStatus = `${data.ohlc.length} bougies, ${data.markers.length} trades, ${data.equity.length} points d'équité.`;
      this.equityError = '';
      
      this.$nextTick(() => {
        const container = document.getElementById('equityChartContainer');
        if (!container || typeof LightweightCharts === 'undefined') {
          this.equityError = 'LightweightCharts n’est pas chargé.';
          return;
        }
        
        if (chartInstance) {
            chartInstance.remove();
            chartInstance = null;
            candleSeries = null;
            equitySeries = null;
        }
        
        container.innerHTML = '';

        const style = getComputedStyle(document.documentElement);
        const textColor = style.getPropertyValue('--text-color').trim() || '#0f172a';
        const borderColor = style.getPropertyValue('--card-border').trim() || '#e2e8f0';
        const primaryColor = style.getPropertyValue('--primary-color').trim() || '#4f46e5';

        const chartOptions = {
          layout: {
            background: { type: 'solid', color: 'transparent' },
            textColor: textColor,
          },
          grid: {
            vertLines: { color: borderColor },
            horzLines: { color: borderColor },
          },
          rightPriceScale: {
            borderColor: borderColor,
          },
          timeScale: {
            borderColor: borderColor,
            timeVisible: true,
            secondsVisible: false,
          },
          crosshair: {
            mode: LightweightCharts.CrosshairMode.Normal,
          }
        };

        chartInstance = LightweightCharts.createChart(container, chartOptions);

        candleSeries = chartInstance.addSeries(LightweightCharts.CandlestickSeries, {
            upColor: '#26a69a',
            downColor: '#ef5350',
            borderVisible: false,
            wickUpColor: '#26a69a',
            wickDownColor: '#ef5350',
            priceFormat: {
                type: 'price',
                precision: 4,
                minMove: 0.0001,
            }
        });

        if (data.ohlc && data.ohlc.length > 0) {
            // lightweight-charts needs strictly ascending time without duplicates
            const uniqueOhlc = [];
            const seenOhlcTimes = new Set();
            for (const item of data.ohlc) {
                if (!seenOhlcTimes.has(item.time)) {
                    seenOhlcTimes.add(item.time);
                    uniqueOhlc.push(item);
                }
            }
            candleSeries.setData(uniqueOhlc);
        }

        if (data.markers && data.markers.length > 0) {
            // Deduplicate markers at the exact same second by slightly shifting if needed,
            // or just rely on the library handling multiple markers at the same time (it usually does).
            // Actually, lightweight-charts supports multiple markers per timestamp if passed as an array to setMarkers.
            candleSeries.setMarkers(data.markers);
        }

        if (data.equity && data.equity.length > 0) {
            equitySeries = chartInstance.addSeries(LightweightCharts.LineSeries, {
                color: primaryColor,
                lineWidth: 2,
                priceScaleId: 'equity',
            });
            
            // Deduplicate equity points
            const uniqueEquity = [];
            const seenEquityTimes = new Set();
            for (const item of data.equity) {
                if (!seenEquityTimes.has(item.time)) {
                    seenEquityTimes.add(item.time);
                    uniqueEquity.push(item);
                }
            }
            equitySeries.setData(uniqueEquity);

            // Configure the secondary scale for equity
            chartInstance.priceScale('equity').applyOptions({
                scaleMargins: {
                    top: 0.8, // place it at the bottom
                    bottom: 0,
                },
            });
            
            // Adjust main scale to leave room
            chartInstance.priceScale('right').applyOptions({
                scaleMargins: {
                    top: 0.1,
                    bottom: 0.25,
                },
            });
        } else {
             // If no equity, adjust main scale
            chartInstance.priceScale('right').applyOptions({
                scaleMargins: {
                    top: 0.1,
                    bottom: 0.1,
                },
            });
        }

        chartInstance.timeScale().fitContent();

        if (chartResizeObserver) {
            chartResizeObserver.disconnect();
            chartResizeObserver = null;
        }
        // Make chart responsive
        chartResizeObserver = new ResizeObserver(entries => {
            if (entries.length === 0 || entries[0].target !== container) { return; }
            const newRect = entries[0].contentRect;
            chartInstance.applyOptions({ height: newRect.height, width: newRect.width });
        });
        chartResizeObserver.observe(container);
      });
    },

    resetEquityChart(status) {
      this.equityStatus = status;
      this.equityError = '';
      if (chartResizeObserver) {
        chartResizeObserver.disconnect();
        chartResizeObserver = null;
      }
      if (chartInstance) {
        chartInstance.remove();
        chartInstance = null;
        candleSeries = null;
        equitySeries = null;
      }
      const container = document.getElementById('equityChartContainer');
      if (container) {
          container.innerHTML = '';
      }
    },
  };
};