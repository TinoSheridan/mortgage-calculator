/**
 * Market Data Banner - Displays real-time mortgage market information for loan officers
 */

class MarketBanner {
    constructor() {
        this.container = null;
        this.data = null;
        this.updateInterval = null;
        this.refreshRate = 15 * 60 * 1000; // 15 minutes
        this.isLoading = false;

        this.init();
    }

    init() {
        this.createBanner();
        this.loadMarketData();
        this.startAutoRefresh();

        // Handle page visibility changes
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                this.loadMarketData();
            }
        });
    }

    createBanner() {
        // Create banner container
        this.container = document.createElement('div');
        this.container.className = 'market-banner';
        this.container.innerHTML = this.getLoadingHTML();

        // Insert at the top of the page
        document.body.insertBefore(this.container, document.body.firstChild);
    }

    getLoadingHTML() {
        return `
            <div class="market-banner-content">
                <div class="market-banner-loading">
                    <span>📊</span>
                    <span>Loading market data...</span>
                </div>
            </div>
        `;
    }

    getErrorHTML(message) {
        return `
            <div class="market-banner-content">
                <div class="market-banner-error">
                    ⚠️ Error loading market data: ${message}
                </div>
            </div>
        `;
    }

    async loadMarketData() {
        if (this.isLoading) return;

        this.isLoading = true;

        try {
            const response = await fetch('/api/market-data');
            const result = await response.json();

            if (result.success) {
                this.data = result.data;
                this.renderBanner();
            } else {
                this.renderError(result.error || 'Failed to load market data');
            }
        } catch (error) {
            console.error('Error loading market data:', error);
            this.renderError('Network error loading market data');
        } finally {
            this.isLoading = false;
        }
    }

    renderBanner() {
        if (!this.data) return;

        const html = `
            <div class="market-banner-content">
                <div class="market-banner-grid">
                    ${this.renderMortgageRate()}
                    ${this.renderTreasuryYield()}
                    ${this.renderMBSData()}
                    ${this.renderNews()}
                    ${this.renderTrendIndicator()}
                </div>
                <div class="market-banner-last-updated">
                    Updated: ${this.formatTime(this.data.last_updated)}
                </div>
            </div>
        `;

        this.container.innerHTML = html;
    }

    renderMortgageRate() {
        const mortgageData = this.data.mortgage_rate_30y;
        if (!mortgageData) return '';

        const change = mortgageData.change || 0;
        const changeClass = change > 0 ? 'up' : change < 0 ? 'down' : 'stable';
        const changeSymbol = change > 0 ? '↑' : change < 0 ? '↓' : '→';

        return `
            <div class="market-item market-item-clickable"
                 onclick="window.open('https://fred.stlouisfed.org/series/MORTGAGE30US', '_blank')"
                 title="View 30-Year Fixed Rate Mortgage Average in the United States (FRED)">
                <div class="market-item-icon">🏠</div>
                <div class="market-item-content">
                    <div class="market-item-label">30-Year Fixed</div>
                    <div class="market-item-value">
                        ${mortgageData.current.toFixed(2)}%
                        <span class="market-change ${changeClass}">
                            ${changeSymbol}${Math.abs(change).toFixed(2)}
                        </span>
                    </div>
                </div>
            </div>
        `;
    }

    renderTreasuryYield() {
        const treasuryData = this.data.treasury_10y;
        if (!treasuryData) return '';

        const change = treasuryData.change || 0;
        const changeClass = change > 0 ? 'up' : change < 0 ? 'down' : 'stable';
        const changeSymbol = change > 0 ? '↑' : change < 0 ? '↓' : '→';

        return `
            <div class="market-item market-item-clickable"
                 onclick="window.open('https://fred.stlouisfed.org/series/DGS10', '_blank')"
                 title="View 10-Year Treasury Constant Maturity Rate (FRED)">
                <div class="market-item-icon">📊</div>
                <div class="market-item-content">
                    <div class="market-item-label">10-Year Treasury</div>
                    <div class="market-item-value">
                        ${treasuryData.current.toFixed(2)}%
                        <span class="market-change ${changeClass}">
                            ${changeSymbol}${Math.abs(change).toFixed(2)}
                        </span>
                    </div>
                </div>
            </div>
        `;
    }

    renderMBSData() {
        const mbsData = this.data.mbs_data;
        if (!mbsData) return '';

        return `
            <div class="market-item market-item-clickable"
                 onclick="window.open('https://www.mortgagenewsdaily.com/mbs', '_blank')"
                 title="View Mortgage-Backed Securities (MBS) pricing and spread data">
                <div class="market-item-icon">📈</div>
                <div class="market-item-content">
                    <div class="market-item-label">Mortgage Spread</div>
                    <div class="market-item-value">
                        ${mbsData.spread.toFixed(2)}%
                    </div>
                </div>
            </div>
        `;
    }

    renderNews() {
        const newsData = this.data.news_headlines;
        if (!newsData || newsData.length === 0) return '';

        const headline = newsData[0];

        // Fallback to a reliable mortgage news source if link is invalid
        const safeLink = headline.link && !headline.link.includes('example.com')
            ? headline.link
            : 'https://www.mortgagenewsdaily.com/';

        return `
            <div class="market-item market-news-item market-item-clickable">
                <div class="market-item-icon">📰</div>
                <div class="market-item-content">
                    <div class="market-item-label">Market News</div>
                    <div class="market-item-value">
                        <span class="market-news-text"
                              onclick="window.open('${safeLink}', '_blank')"
                              title="${headline.title} - Click to read more">
                            ${headline.title}
                        </span>
                    </div>
                </div>
            </div>
        `;
    }

    renderTrendIndicator() {
        const trend = this.data.rate_trend;
        if (!trend) return '';

        const trendConfig = {
            'rising': {
                icon: '📈',
                symbol: '↗️',
                label: 'Rising',
                color: '#dc3545',
                bgColor: '#f8d7da',
                status: 'NEGATIVE'
            },
            'falling': {
                icon: '📉',
                symbol: '↘️',
                label: 'Falling',
                color: '#198754',
                bgColor: '#d1e7dd',
                status: 'POSITIVE'
            },
            'stable': {
                icon: '📊',
                symbol: '→',
                label: 'Stable',
                color: '#6c757d',
                bgColor: '#e9ecef',
                status: 'MINIMAL'
            }
        };

        const config = trendConfig[trend] || trendConfig.stable;

        return `
            <div class="market-item market-item-clickable"
                 onclick="window.open('https://www.mortgagenewsdaily.com/mortgage-rates', '_blank')"
                 title="View detailed mortgage rate trends and analysis">
                <div class="market-item-icon">${config.icon}</div>
                <div class="market-item-content">
                    <div class="market-item-label">Rate Trend</div>
                    <div class="market-item-value">
                        <div class="trend-indicator-container">
                            <div class="trend-status-badge" style="background-color: ${config.bgColor}; color: ${config.color};">
                                ${config.status}
                            </div>
                            <div class="trend-description" style="color: ${config.color};">
                                ${config.label} ${config.symbol}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    renderError(message) {
        this.container.innerHTML = this.getErrorHTML(message);
    }

    formatTime(isoString) {
        try {
            const date = new Date(isoString);
            return date.toLocaleTimeString('en-US', {
                hour: '2-digit',
                minute: '2-digit',
                hour12: true
            });
        } catch (error) {
            return 'Unknown';
        }
    }

    startAutoRefresh() {
        // Clear any existing interval
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }

        // Set up auto-refresh
        this.updateInterval = setInterval(() => {
            this.loadMarketData();
        }, this.refreshRate);
    }

    destroy() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }

        if (this.container && this.container.parentNode) {
            this.container.parentNode.removeChild(this.container);
        }
    }
}

// Initialize the market banner when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize if we're on the main calculator page
    if (window.location.pathname === '/' || window.location.pathname === '/index.html') {
        window.marketBanner = new MarketBanner();
    }
});

// Make MarketBanner available globally
window.MarketBanner = MarketBanner;
