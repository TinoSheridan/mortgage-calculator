/**
 * Main application initialization and utilities
 */

class MortgageCalculatorApp {
    constructor() {
        this.init();
    }

    init() {
        // Wait for DOM to be fully loaded
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.onDOMReady());
        } else {
            this.onDOMReady();
        }
    }

    onDOMReady() {
        console.log('Mortgage Calculator v2.8.0 - Multi-Tenant System');
        console.log('API Base URL:', getApiBaseUrl());
        
        // Initialize app components
        this.setupEventListeners();
        this.loadUserPreferences();
        this.checkApiConnection();
        
        // Show app info in console for debugging
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            console.log('Development Mode - API calls will go to:', getApiBaseUrl());
        }
    }

    setupEventListeners() {
        // Handle tab switching
        const tabButtons = document.querySelectorAll('[data-bs-toggle="tab"]');
        tabButtons.forEach(button => {
            button.addEventListener('shown.bs.tab', (e) => {
                // Clear results when switching tabs
                const resultsCard = document.getElementById('resultsCard');
                if (resultsCard) {
                    resultsCard.style.display = 'none';
                }
            });
        });

        // Handle form reset buttons
        const resetButtons = document.querySelectorAll('.btn-reset');
        resetButtons.forEach(button => {
            button.addEventListener('click', () => this.resetForm(button.closest('form')));
        });

        // Handle keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyboardShortcuts(e));

        // Handle offline/online status
        window.addEventListener('online', () => this.handleOnlineStatus(true));
        window.addEventListener('offline', () => this.handleOnlineStatus(false));
    }

    handleKeyboardShortcuts(e) {
        // Ctrl/Cmd + Enter to calculate
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            const activeTab = document.querySelector('.tab-pane.active');
            if (activeTab) {
                const form = activeTab.querySelector('form');
                if (form) {
                    form.dispatchEvent(new Event('submit'));
                }
            }
        }
    }

    handleOnlineStatus(isOnline) {
        const statusElement = this.getOrCreateStatusElement();
        
        if (isOnline) {
            statusElement.className = 'alert alert-success position-fixed bottom-0 end-0 m-3';
            statusElement.innerHTML = '<i class="bi bi-wifi"></i> Back online';
            setTimeout(() => statusElement.remove(), 3000);
        } else {
            statusElement.className = 'alert alert-warning position-fixed bottom-0 end-0 m-3';
            statusElement.innerHTML = '<i class="bi bi-wifi-off"></i> Working offline - calculations may not be available';
        }
    }

    getOrCreateStatusElement() {
        let element = document.getElementById('connectionStatus');
        if (!element) {
            element = document.createElement('div');
            element.id = 'connectionStatus';
            element.style.zIndex = '9999';
            document.body.appendChild(element);
        }
        return element;
    }

    async checkApiConnection() {
        try {
            const response = await fetch(getApiUrl('/health'), {
                method: 'GET',
                timeout: 5000
            });
            
            if (response.ok) {
                const data = await response.json();
                console.log('API Health Check:', data);
                
                // Show API status in footer or somewhere subtle
                this.updateApiStatus(true, data);
            } else {
                console.warn('API health check failed:', response.status);
                this.updateApiStatus(false);
            }
        } catch (error) {
            console.warn('Cannot connect to API:', error.message);
            this.updateApiStatus(false, error);
        }
    }

    updateApiStatus(isConnected, data = null) {
        // Add a subtle indicator to the footer or navbar
        const footer = document.querySelector('footer .container');
        if (footer) {
            let statusElement = document.getElementById('apiStatus');
            if (!statusElement) {
                statusElement = document.createElement('span');
                statusElement.id = 'apiStatus';
                statusElement.className = 'ms-2';
                footer.appendChild(statusElement);
            }

            if (isConnected) {
                statusElement.innerHTML = `
                    <small class="text-success">
                        <i class="bi bi-check-circle"></i> API Connected
                        ${data && data.version ? `(${data.version})` : ''}
                    </small>
                `;
            } else {
                statusElement.innerHTML = `
                    <small class="text-warning">
                        <i class="bi bi-exclamation-triangle"></i> API Offline
                    </small>
                `;
            }
        }
    }

    loadUserPreferences() {
        try {
            // Load form preferences from localStorage
            const preferences = localStorage.getItem('calculatorPreferences');
            if (preferences) {
                const prefs = JSON.parse(preferences);
                this.applyPreferences(prefs);
            }
        } catch (error) {
            console.error('Error loading preferences:', error);
        }
    }

    applyPreferences(preferences) {
        // Apply saved form values
        Object.keys(preferences).forEach(key => {
            const element = document.getElementById(key);
            if (element && element.type !== 'submit') {
                element.value = preferences[key];
            }
        });
    }

    saveUserPreferences() {
        try {
            const preferences = {};
            const inputs = document.querySelectorAll('input[type="number"], select');
            
            inputs.forEach(input => {
                if (input.id && input.value) {
                    preferences[input.id] = input.value;
                }
            });

            localStorage.setItem('calculatorPreferences', JSON.stringify(preferences));
        } catch (error) {
            console.error('Error saving preferences:', error);
        }
    }

    resetForm(form) {
        if (form) {
            form.reset();
            
            // Reset to default values
            const defaults = APP_CONFIG.DEFAULTS;
            Object.keys(defaults).forEach(key => {
                const element = document.getElementById(key);
                if (element) {
                    element.value = defaults[key];
                }
            });

            // Hide results
            const resultsCard = document.getElementById('resultsCard');
            if (resultsCard) {
                resultsCard.style.display = 'none';
            }
        }
    }

    // Utility function to format numbers with commas
    formatNumber(num) {
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    }

    // Utility function to parse formatted numbers
    parseNumber(str) {
        return parseFloat(str.toString().replace(/,/g, '')) || 0;
    }

    // Show loading overlay
    showGlobalLoading(message = 'Loading...') {
        let overlay = document.getElementById('globalLoadingOverlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.id = 'globalLoadingOverlay';
            overlay.className = 'position-fixed top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center';
            overlay.style.cssText = 'background: rgba(0,0,0,0.7); z-index: 9999;';
            overlay.innerHTML = `
                <div class="text-center text-white">
                    <div class="spinner-border mb-3" role="status"></div>
                    <div>${message}</div>
                </div>
            `;
            document.body.appendChild(overlay);
        }
        overlay.style.display = 'flex';
    }

    hideGlobalLoading() {
        const overlay = document.getElementById('globalLoadingOverlay');
        if (overlay) {
            overlay.style.display = 'none';
        }
    }

    // Get current page name
    getCurrentPage() {
        const path = window.location.pathname;
        const page = path.split('/').pop() || 'index.html';
        return page.replace('.html', '');
    }

    // Navigation helper
    navigateTo(page) {
        window.location.href = page.includes('.html') ? page : `${page}.html`;
    }

    // Check if user should see upgrade prompts
    shouldShowUpgradePrompts() {
        return !authManager.isAuthenticated && Math.random() < 0.3; // 30% chance
    }

    // Show upgrade prompt for anonymous users
    showUpgradePrompt() {
        if (this.shouldShowUpgradePrompts()) {
            const alert = document.createElement('div');
            alert.className = 'alert alert-info alert-dismissible fade show mt-3';
            alert.innerHTML = `
                <strong>Get More Features!</strong> 
                <a href="login.html" class="alert-link">Create an account</a> to:
                <ul class="mt-2 mb-0">
                    <li>Save your calculations</li>
                    <li>Customize closing costs and fees</li>
                    <li>Access organization-specific settings</li>
                    <li>Get personalized rate recommendations</li>
                </ul>
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            
            const container = document.querySelector('.container');
            if (container && container.firstChild) {
                container.insertBefore(alert, container.firstChild);
            }
        }
    }
}

// Initialize app
window.app = new MortgageCalculatorApp();

// Add some utility functions to global scope
window.formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(amount);
};

window.formatPercent = (rate) => {
    return new Intl.NumberFormat('en-US', {
        style: 'percent',
        minimumFractionDigits: 2,
        maximumFractionDigits: 3
    }).format(rate / 100);
};

// Add event listener to save preferences when user changes inputs
document.addEventListener('DOMContentLoaded', () => {
    const inputs = document.querySelectorAll('input[type="number"], select');
    inputs.forEach(input => {
        input.addEventListener('change', () => {
            // Debounce the save operation
            clearTimeout(window.savePreferencesTimeout);
            window.savePreferencesTimeout = setTimeout(() => {
                window.app.saveUserPreferences();
            }, 1000);
        });
    });
});