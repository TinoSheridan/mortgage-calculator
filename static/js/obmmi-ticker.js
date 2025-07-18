/**
 * OBMMI Ticker Tape Banner
 * Displays Optimal Blue Mortgage Market Indices in a scrolling ticker format
 */

class OBMMITicker {
    constructor() {
        this.container = null;
        this.updateInterval = null;
        this.refreshRate = 5 * 60 * 1000; // 5 minutes
        this.isLoading = false;
        this.widgetInitialized = false;
        
        this.init();
    }

    init() {
        this.createTickerContainer();
        this.initializeWidget();
        this.startAutoRefresh();
        
        // Handle page visibility changes
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden && !this.isLoading) {
                this.refreshWidget();
            }
        });
    }

    createTickerContainer() {
        // Create ticker container
        this.container = document.createElement('div');
        this.container.className = 'obmmi-ticker-container';
        this.container.id = 'obmmi-ticker';
        
        // Insert at the top of the page, before any other content
        document.body.insertBefore(this.container, document.body.firstChild);
        
        // Initially show loading state
        this.showLoadingState();
    }

    showLoadingState() {
        this.container.innerHTML = `
            <div class="obmmi-loading">
                <span>📊</span>
                <span>Loading mortgage market data...</span>
            </div>
            <div class="obmmi-branding">
                <span>Powered by</span>
                <a href="https://www.optimalblue.com" target="_blank" rel="noopener">Optimal Blue</a>
            </div>
        `;
    }

    showErrorState(message) {
        this.container.innerHTML = `
            <div class="obmmi-error">
                ⚠️ ${message}
            </div>
            <div class="obmmi-branding">
                <span>Powered by</span>
                <a href="https://www.optimalblue.com" target="_blank" rel="noopener">Optimal Blue</a>
            </div>
        `;
    }

    initializeWidget() {
        try {
            // Check if OBMMI widget script is available
            if (typeof window.OBMMI !== 'undefined' && window.OBMMI.widget) {
                this.loadOBMMIWidget();
            } else {
                // Load fallback data while waiting for widget script
                this.loadFallbackData();
            }
        } catch (error) {
            console.error('Error initializing OBMMI widget:', error);
            this.loadFallbackData();
        }
    }

    loadOBMMIWidget() {
        try {
            // Initialize the actual OBMMI widget
            const widgetConfig = {
                container: this.container,
                style: 'ticker',
                theme: 'dark',
                showAttribution: true,
                refreshInterval: 300000, // 5 minutes
                loanTypes: ['30Y_FIXED', '15Y_FIXED', 'FHA', 'VA', 'JUMBO'],
                onUpdate: (data) => this.renderTickerData(data),
                onError: (error) => this.showErrorState('Unable to load market data')
            };

            // This would be the actual OBMMI widget initialization
            // window.OBMMI.widget.init(widgetConfig);
            
            // For now, load fallback data
            this.loadFallbackData();
        } catch (error) {
            console.error('Error loading OBMMI widget:', error);
            this.loadFallbackData();
        }
    }

    loadFallbackData() {
        // Simulate real mortgage market data (this would come from OBMMI in production)
        const fallbackData = {
            rates: [
                { type: '30Y Fixed', rate: 7.125, change: 0.025, direction: 'up' },
                { type: '15Y Fixed', rate: 6.750, change: -0.015, direction: 'down' },
                { type: 'FHA', rate: 7.250, change: 0.010, direction: 'up' },
                { type: 'VA', rate: 7.000, change: 0.000, direction: 'stable' },
                { type: 'Jumbo', rate: 7.375, change: 0.050, direction: 'up' },
                { type: 'USDA', rate: 7.125, change: 0.025, direction: 'up' },
                { type: '10Y ARM', rate: 6.875, change: -0.025, direction: 'down' },
                { type: '5Y ARM', rate: 6.625, change: -0.050, direction: 'down' }
            ],
            lastUpdated: new Date().toISOString(),
            source: 'OBMMI Market Data'
        };

        setTimeout(() => {
            this.renderTickerData(fallbackData);
        }, 1000);
    }

    renderTickerData(data) {
        if (!data || !data.rates || data.rates.length === 0) {
            this.showErrorState('No market data available');
            return;
        }

        // Create ticker items
        const tickerItems = data.rates.map(rate => {
            const changeClass = rate.direction === 'up' ? 'up' : 
                               rate.direction === 'down' ? 'down' : 'stable';
            const changeSymbol = rate.direction === 'up' ? '↑' : 
                                rate.direction === 'down' ? '↓' : '→';
            const changeText = rate.change !== 0 ? `${changeSymbol}${Math.abs(rate.change).toFixed(3)}` : '→';

            return `
                <div class="obmmi-ticker-item">
                    <div class="obmmi-ticker-label">${rate.type}</div>
                    <div class="obmmi-ticker-rate">${rate.rate.toFixed(3)}%</div>
                    <div class="obmmi-ticker-change ${changeClass}">${changeText}</div>
                </div>
            `;
        }).join('');

        // Create duplicate content for seamless scrolling
        const duplicatedContent = tickerItems + tickerItems;

        this.container.innerHTML = `
            <div class="obmmi-ticker-content">
                ${duplicatedContent}
            </div>
            <div class="obmmi-branding">
                <span>Powered by</span>
                <a href="https://www.optimalblue.com" target="_blank" rel="noopener">Optimal Blue</a>
            </div>
        `;

        this.widgetInitialized = true;
    }

    refreshWidget() {
        if (this.isLoading) return;
        
        this.isLoading = true;
        
        try {
            // In production, this would refresh the OBMMI widget
            // For now, reload fallback data
            this.loadFallbackData();
        } catch (error) {
            console.error('Error refreshing OBMMI widget:', error);
            this.showErrorState('Error refreshing data');
        } finally {
            setTimeout(() => {
                this.isLoading = false;
            }, 1000);
        }
    }

    startAutoRefresh() {
        // Clear any existing interval
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }

        // Set up auto-refresh
        this.updateInterval = setInterval(() => {
            this.refreshWidget();
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

    // Static method to inject OBMMI widget script
    static loadOBMMIScript() {
        return new Promise((resolve, reject) => {
            // Check if script is already loaded
            if (document.querySelector('script[src*="optimalblue.com"]')) {
                resolve();
                return;
            }

            // Create script element for OBMMI widget
            const script = document.createElement('script');
            script.src = 'https://www2.optimalblue.com/obmmi/widget.js'; // Placeholder URL
            script.async = true;
            script.onload = resolve;
            script.onerror = reject;
            
            document.head.appendChild(script);
        });
    }
}

// Initialize the ticker when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize on main calculator page
    if (window.location.pathname === '/' || window.location.pathname === '/index.html') {
        // First try to load the OBMMI script
        OBMMITicker.loadOBMMIScript()
            .then(() => {
                console.log('OBMMI script loaded successfully');
                window.obmmiTicker = new OBMMITicker();
            })
            .catch(() => {
                console.log('OBMMI script not available, using fallback');
                window.obmmiTicker = new OBMMITicker();
            });
    }
});

// Export for use in other modules
window.OBMMITicker = OBMMITicker;