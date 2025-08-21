/**
 * Configuration file for the GitHub Pages frontend
 * Update API_BASE_URL to point to your deployed API
 */

// API Configuration
const API_CONFIG = {
    // Replace with your Railway/Vercel API URL
    BASE_URL: 'https://mortgage-calculator-api-production.up.railway.app',  // Your Railway API

    // Local development fallback
    DEV_URL: 'http://127.0.0.1:5000',

    // Endpoints
    ENDPOINTS: {
        AUTH: {
            LOGIN: '/api/auth/login',
            LOGOUT: '/api/auth/logout',
            PROFILE: '/api/auth/profile',
            REGISTER: '/auth/register'  // Note: this might redirect to the API's register page
        },
        CALCULATOR: {
            CALCULATE: '/api/calculate',
            REFINANCE: '/api/refinance'
        },
        CONFIG: {
            GET: '/api/config/',  // + config_type
            SET: '/api/config/'   // + config_type
        },
        HEALTH: '/health'
    }
};

// Determine API base URL
function getApiBaseUrl() {
    // Check if we're in local development
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        return API_CONFIG.DEV_URL;
    }

    // Use production API URL
    return API_CONFIG.BASE_URL;
}

// Get full API endpoint URL
function getApiUrl(endpoint) {
    return getApiBaseUrl() + endpoint;
}

// App Configuration
const APP_CONFIG = {
    NAME: 'Mortgage Calculator',
    VERSION: '2.8.0',
    DESCRIPTION: 'Multi-Tenant Mortgage Calculator',

    // Local storage keys
    STORAGE_KEYS: {
        USER_TOKEN: 'mortgage_calc_token',
        USER_DATA: 'mortgage_calc_user',
        LAST_CALCULATION: 'mortgage_calc_last_calc'
    },

    // Default form values
    DEFAULTS: {
        PURCHASE_PRICE: 400000,
        DOWN_PAYMENT: 20,
        INTEREST_RATE: 6.5,
        LOAN_TERM: 30,
        PROPERTY_TAX: 1.2,
        INSURANCE_RATE: 0.35,
        HOA_FEE: 0
    },

    // Feature flags
    FEATURES: {
        MULTI_TENANT: true,
        USER_AUTH: true,
        CUSTOM_CONFIG: true,
        REFINANCE_CALC: true
    }
};

// Export for use in other modules
window.API_CONFIG = API_CONFIG;
window.APP_CONFIG = APP_CONFIG;
window.getApiUrl = getApiUrl;
window.getApiBaseUrl = getApiBaseUrl;
