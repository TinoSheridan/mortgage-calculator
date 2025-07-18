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
            // Load the real OBMMI widget iframe
            this.loadRealOBMMIWidget();
        } catch (error) {
            console.error('Error initializing OBMMI widget:', error);
            this.loadFallbackData();
        }
    }

    loadRealOBMMIWidget() {
        try {
            // The OBMMI widget URLs are not publicly accessible
            // This likely requires registration with Optimal Blue
            // Show a professional message about obtaining access
            
            console.log('OBMMI widget integration: Requires registration with Optimal Blue');
            
            // Show professional message about obtaining OBMMI access
            this.showOBMMIAccessRequired();
            
        } catch (error) {
            console.error('Error loading OBMMI widget:', error);
            this.loadFallbackData();
        }
    }

    extractOBMMIData(iframe) {
        try {
            // Due to CORS restrictions, we cannot directly access iframe content
            // from a different domain. Instead, we'll use a polling approach
            // to check if the widget provides data via postMessage or similar
            
            // Listen for messages from the OBMMI widget
            window.addEventListener('message', (event) => {
                if (event.origin === 'https://www2.optimalblue.com') {
                    if (event.data && event.data.type === 'obmmi-data') {
                        this.parseOBMMIData(event.data);
                    }
                }
            });
            
            // For now, continue with fallback data
            // The iframe will display the widget, but we'll show ticker with fallback
            console.log('OBMMI widget loaded, using fallback data for ticker');
            
        } catch (error) {
            console.error('Error extracting OBMMI data:', error);
            this.loadFallbackData();
        }
    }

    parseOBMMIData(data) {
        try {
            // Parse the real OBMMI data into our ticker format
            const rates = data.rates || [];
            const formattedData = {
                rates: rates.map(rate => ({
                    type: rate.loanType || 'Unknown',
                    rate: parseFloat(rate.rate) || 0,
                    change: parseFloat(rate.change) || 0,
                    direction: rate.change > 0 ? 'up' : rate.change < 0 ? 'down' : 'stable'
                })),
                lastUpdated: data.lastUpdated || new Date().toISOString(),
                source: 'OBMMI Real Data'
            };
            
            this.renderTickerData(formattedData);
        } catch (error) {
            console.error('Error parsing OBMMI data:', error);
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
            source: 'Demo Data'
        };

        setTimeout(() => {
            this.renderTickerData(fallbackData);
        }, 1000);
    }

    loadFallbackDataWithRealWidgetNote() {
        // Show a professional message directing users to real data
        this.container.innerHTML = `
            <div class="obmmi-ticker-content" style="animation: none; justify-content: center; text-align: center;">
                <div class="obmmi-ticker-item" style="background: rgba(255,255,255,0.2); padding: 8px 16px;">
                    <div class="obmmi-ticker-rate" style="font-size: 14px;">
                        📊 Live OBMMI Market Data Available
                    </div>
                </div>
            </div>
            <div class="obmmi-branding">
                <span>Powered by</span>
                <a href="https://www.optimalblue.com" target="_blank" rel="noopener">Optimal Blue</a>
                <button class="obmmi-expand-button" onclick="window.obmmiTicker.showFullWidget()" style="background: rgba(34,197,94,0.9); border-color: rgba(34,197,94,1); animation: pulse 2s infinite;">
                    📊 View Real Data
                </button>
            </div>
        `;
        
        // Add pulse animation for the button
        const style = document.createElement('style');
        style.textContent = `
            @keyframes pulse {
                0% { transform: scale(1); }
                50% { transform: scale(1.05); }
                100% { transform: scale(1); }
            }
        `;
        document.head.appendChild(style);

        // Create modal for full widget (only once)
        if (!document.getElementById('obmmi-modal')) {
            this.createFullWidgetModal();
        }

        this.widgetInitialized = true;
    }

    showOBMMIAccessRequired() {
        // Show a professional message about obtaining OBMMI access
        this.container.innerHTML = `
            <div class="obmmi-ticker-content" style="animation: none; justify-content: center; text-align: center;">
                <div class="obmmi-ticker-item" style="background: rgba(255,255,255,0.2); padding: 8px 16px;">
                    <div class="obmmi-ticker-rate" style="font-size: 14px;">
                        📊 OBMMI Widget Access Required
                    </div>
                </div>
            </div>
            <div class="obmmi-branding">
                <span>Powered by</span>
                <a href="https://www.optimalblue.com" target="_blank" rel="noopener">Optimal Blue</a>
                <button class="obmmi-expand-button" onclick="window.obmmiTicker.showAccessInfo()" style="background: rgba(255,193,7,0.9); border-color: rgba(255,193,7,1);">
                    ℹ️ Get Access
                </button>
            </div>
        `;

        // Create modal for access info (only once)
        if (!document.getElementById('obmmi-access-modal')) {
            this.createAccessInfoModal();
        }

        this.widgetInitialized = true;
    }

    createAccessInfoModal() {
        const modal = document.createElement('div');
        modal.id = 'obmmi-access-modal';
        modal.className = 'obmmi-modal';
        modal.innerHTML = `
            <div class="obmmi-modal-content">
                <div class="obmmi-modal-header">
                    <h3 class="obmmi-modal-title">📊 OBMMI Widget Access Required</h3>
                    <button class="obmmi-close" onclick="window.obmmiTicker.hideAccessInfo()">&times;</button>
                </div>
                <div style="padding: 20px;">
                    <div style="margin-bottom: 20px; padding: 15px; background: #fff3cd; border: 1px solid #ffecb5; border-radius: 4px; color: #856404;">
                        <strong>⚠️ Registration Required:</strong> The OBMMI widget requires registration with Optimal Blue to access real-time mortgage market data.
                    </div>
                    
                    <h4 style="color: #1e3c72; margin-bottom: 15px;">How to Get OBMMI Access:</h4>
                    <ol style="line-height: 1.8; margin-bottom: 20px;">
                        <li><strong>Visit Optimal Blue:</strong> Go to <a href="https://www.optimalblue.com" target="_blank" style="color: #1e3c72;">optimalblue.com</a></li>
                        <li><strong>Register for OBMMI:</strong> Sign up for access to the Optimal Blue Mortgage Market Indices</li>
                        <li><strong>Get Widget Code:</strong> Obtain your personalized widget embed code</li>
                        <li><strong>Replace Integration:</strong> Update this ticker with your authorized widget code</li>
                    </ol>
                    
                    <div style="margin-top: 20px; padding: 15px; background: #d1ecf1; border: 1px solid #bee5eb; border-radius: 4px; color: #0c5460;">
                        <strong>🎯 OBMMI Benefits:</strong>
                        <ul style="margin: 10px 0; padding-left: 20px;">
                            <li>Real-time data from ~35% of the U.S. mortgage market</li>
                            <li>Based on actual loan locks, not advertised rates</li>
                            <li>Multiple loan types: Conventional, FHA, VA, USDA, Jumbo</li>
                            <li>Updated throughout the day</li>
                        </ul>
                    </div>
                    
                    <div style="margin-top: 20px; text-align: center;">
                        <a href="https://www.optimalblue.com" target="_blank" class="btn btn-primary" style="background: #1e3c72; border: none; padding: 10px 20px; text-decoration: none; border-radius: 4px; color: white;">
                            Get OBMMI Access
                        </a>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        
        // Close modal when clicking outside
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                this.hideAccessInfo();
            }
        });
        
        // Close modal with Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && modal.style.display === 'block') {
                this.hideAccessInfo();
            }
        });
    }

    showAccessInfo() {
        const modal = document.getElementById('obmmi-access-modal');
        if (modal) {
            modal.style.display = 'block';
            document.body.style.overflow = 'hidden';
        }
    }

    hideAccessInfo() {
        const modal = document.getElementById('obmmi-access-modal');
        if (modal) {
            modal.style.display = 'none';
            document.body.style.overflow = '';
        }
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
                <button class="obmmi-expand-button" onclick="window.obmmiTicker.showFullWidget()">
                    📊 Full Widget
                </button>
            </div>
        `;

        // Create modal for full widget (only once)
        if (!document.getElementById('obmmi-modal')) {
            this.createFullWidgetModal();
        }

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