import { getCandles, getPerformanceMetrics, getTransactions } from './api.js';
import { formatCurrency, formatPercent, formatUSDT, showError } from './ui.js';

let currentChart = null;
let candleSeries = null;
let equitySeries = null;
let bhSeries = null;
let currentAsset = null;

// Local caching for chart transactions
let cachedTransactions = null;

export function invalidateChartCache() {
    cachedTransactions = null;
    currentAsset = null;
}

export async function loadChart(ticker, forceRefresh = false) {
    if (typeof LightweightCharts === 'undefined') {
        const placeholder = document.getElementById('chart-placeholder');
        if (placeholder) {
            placeholder.style.display = 'flex';
            placeholder.innerHTML = `
                <svg viewBox="0 0 24 24" width="48" height="48" stroke="var(--danger)" stroke-width="1.5" fill="none"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                <p style="color: var(--danger); font-weight: bold; margin-top: 10px;">Lightweight Charts CDN Offline</p>
                <p style="font-size: 13px; max-width: 400px; text-align: center;">Impossible de charger la librairie de graphiques depuis le CDN (unpkg.com). Veuillez vérifier votre connexion Internet.</p>
            `;
        }
        document.getElementById('analytics-grid').style.display = 'none';
        document.getElementById('price-chart').style.display = 'none';
        const selector = document.getElementById('asset-selector');
        if (selector) selector.disabled = true;
        showError("Impossible de charger la librairie de graphiques (CDN hors-ligne).");
        return;
    }

    if (!ticker) {
        document.getElementById('analytics-grid').style.display = 'none';
        document.getElementById('chart-placeholder').style.display = 'flex';
        document.getElementById('price-chart').style.display = 'none';
        currentAsset = null;
        return;
    }
    
    document.getElementById('chart-placeholder').style.display = 'none';
    document.getElementById('price-chart').style.display = 'block';
    document.getElementById('analytics-grid').style.display = 'grid';
    
    const chartContainer = document.getElementById('price-chart');
    
    // Recreate chart only if asset changed or if forced
    if (currentChart && (currentAsset !== ticker || forceRefresh)) {
        try {
            currentChart.remove();
        } catch(e) { console.error("Error destroying chart", e); }
        currentChart = null;
        candleSeries = null;
        equitySeries = null;
        bhSeries = null;
    }
    
    if (!currentChart) {
        // Init Lightweight Chart
        currentChart = LightweightCharts.createChart(chartContainer, {
            layout: {
                backgroundColor: '#070a13',
                textColor: '#64748b',
                fontSize: 11,
                fontFamily: 'Inter, sans-serif',
            },
            grid: {
                vertLines: { color: 'rgba(255, 255, 255, 0.02)' },
                horzLines: { color: 'rgba(255, 255, 255, 0.02)' },
            },
            crosshair: {
                mode: LightweightCharts.CrosshairMode.Normal,
            },
            rightPriceScale: {
                borderColor: 'rgba(255, 255, 255, 0.08)',
                autoScale: true,
            },
            timeScale: {
                borderColor: 'rgba(255, 255, 255, 0.08)',
                timeVisible: true,
                secondsVisible: false,
            },
        });
        
        // Candle series on the right price scale
        candleSeries = currentChart.addCandlestickSeries({
            upColor: '#10b981',
            downColor: '#ef4444',
            borderUpColor: '#10b981',
            borderDownColor: '#ef4444',
            wickUpColor: '#10b981',
            wickDownColor: '#ef4444',
        });
        
        // Account Equity curves on the left price scale
        equitySeries = currentChart.addLineSeries({
            color: '#3b82f6',
            lineWidth: 2,
            priceScaleId: 'equity',
            title: 'Strategy NAV',
        });
        
        bhSeries = currentChart.addLineSeries({
            color: '#8b5cf6',
            lineWidth: 1.5,
            priceScaleId: 'equity',
            title: 'Buy & Hold NAV',
        });
        
        currentChart.priceScale('equity').applyOptions({
            side: 'left',
            autoScale: true,
            borderColor: 'rgba(255, 255, 255, 0.08)',
        });
        
        currentAsset = ticker;
    }
    
    try {
        // Fetch candles
        const candlesData = await getCandles(ticker);
        
        if (candlesData.length === 0) {
            console.warn("No candle data fetched for active asset", ticker);
            return;
        }
        
        candleSeries.setData(candlesData);
        
        // Fetch Transactions for marker overlays (with caching)
        let txData;
        if (cachedTransactions && !forceRefresh) {
            txData = cachedTransactions;
        } else {
            txData = await getTransactions(5000, 0); // Get enough transactions for markers
            cachedTransactions = txData;
        }
        
        // Fetch performance metrics from backend API
        const perfData = await getPerformanceMetrics(ticker);
        
        // Set curves on chart
        equitySeries.setData(perfData.strategy_curve);
        bhSeries.setData(perfData.buy_hold_curve);
        
        // Render KPI metrics cards
        document.getElementById('analytic-winrate').textContent = formatPercent(perfData.win_rate);
        document.getElementById('analytic-profitfactor').textContent = perfData.profit_factor === 'Infinity' ? '∞' : parseFloat(perfData.profit_factor).toFixed(2);
        document.getElementById('analytic-maxdd').textContent = perfData.max_drawdown.toFixed(2) + '%';
        document.getElementById('analytic-currentdd').textContent = perfData.current_drawdown.toFixed(2) + '%';
        
        const isCrypto = ticker.toLowerCase().endsWith('usdt');
        const totalProfitEl = document.getElementById('analytic-totalprofit');
        totalProfitEl.textContent = isCrypto ? formatUSDT(perfData.net_profit) : formatCurrency(perfData.net_profit);
        totalProfitEl.className = 'kpi-value ' + (perfData.net_profit >= 0 ? 'positive' : 'negative');
        
        const totalTrades = perfData.total_trades;
        document.getElementById('analytic-tradescount').textContent = totalTrades;
        
        // Filter transactions matching this asset for markers
        const assetTxs = txData.filter(tx => tx.asset.toLowerCase() === ticker.toLowerCase());
        const sortedTxs = [...assetTxs].sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
        
        // Add BUY / SELL Markers to chart
        const markers = [];
        sortedTxs.forEach(tx => {
            const txTimeSecs = Math.floor(new Date(tx.timestamp).getTime() / 1000);
            const candleMinSecs = Math.floor(txTimeSecs / 60) * 60; // align to minute candle
            
            if (tx.action === 'BUY') {
                markers.push({
                    time: candleMinSecs,
                    position: 'belowBar',
                    color: '#10b981',
                    shape: 'arrowUp',
                    text: 'BUY'
                });
            } else if (tx.action === 'SELL') {
                markers.push({
                    time: candleMinSecs,
                    position: 'aboveBar',
                    color: '#ef4444',
                    shape: 'arrowDown',
                    text: 'SELL'
                });
            }
        });
        
        markers.sort((a, b) => a.time - b.time);
        
        // Deduplicate markers on matching timestamps
        const uniqueMarkers = [];
        const seenTimes = new Set();
        markers.forEach(m => {
            if (!seenTimes.has(m.time)) {
                seenTimes.add(m.time);
                uniqueMarkers.push(m);
            }
        });
        
        candleSeries.setMarkers(uniqueMarkers);
        
    } catch(err) {
        showError("Une erreur est survenue lors de la génération du graphique de performance.", err);
    }
}
