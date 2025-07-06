/**
 * API Client for mortgage calculator backend communication
 * Handles all HTTP requests and response processing
 */

export class ApiClient {
    constructor() {
        this.baseUrl = '';
        this.defaultHeaders = {
            'Content-Type': 'application/json',
        };
    }

    /**
     * Get CSRF token from meta tag
     * @returns {string} CSRF token
     */
    getCSRFToken() {
        const token = document.querySelector('meta[name=csrf-token]');
        return token ? token.getAttribute('content') : '';
    }

    /**
     * Submit calculation request to backend
     * @param {Object} formData - Form data to submit
     * @param {string} mode - 'purchase' or 'refinance'
     * @returns {Promise<Object>} Response data
     */
    async submitCalculation(formData, mode) {
        const endpoint = mode === 'refinance' ? '/refinance' : '/calculate';
        
        const headers = {
            ...this.defaultHeaders,
            'X-CSRFToken': this.getCSRFToken(),
        };

        console.log(`Submitting ${mode} calculation to ${endpoint}`);
        console.log('Form data:', formData);
        if (mode === 'refinance') {
            console.log('Cash option being sent:', formData.cash_option);
            console.log('Target LTV value being sent:', formData.target_ltv_value);
        }

        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify(formData),
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            console.log('Response received:', data);
            
            // If there's an error in the result, log it clearly
            if (data.result && data.result.error) {
                console.error('Backend calculation error:', data.result.error);
            }

            return data;
        } catch (error) {
            console.error('API request failed:', error);
            throw this.handleApiError(error);
        }
    }

    /**
     * Handle API errors and convert to user-friendly messages
     * @param {Error} error - Original error
     * @returns {Error} User-friendly error
     */
    handleApiError(error) {
        if (error.name === 'TypeError' && error.message.includes('fetch')) {
            return new Error('Network error. Please check your connection and try again.');
        }

        if (error.message.includes('HTTP 400')) {
            return new Error('Invalid input data. Please check your entries and try again.');
        }

        if (error.message.includes('HTTP 422')) {
            return new Error('Calculation error. Please verify your input values.');
        }

        if (error.message.includes('HTTP 500')) {
            return new Error('Server error. Please try again later.');
        }

        if (error.message.includes('HTTP 429')) {
            return new Error('Too many requests. Please wait a moment and try again.');
        }

        // Return original error if we can't provide a better message
        return error;
    }

    /**
     * Submit max seller contribution request
     * @param {Object} data - Request data
     * @returns {Promise<Object>} Response data
     */
    async getMaxSellerContribution(data) {
        const headers = {
            ...this.defaultHeaders,
            'X-CSRFToken': this.getCSRFToken(),
        };

        try {
            const response = await fetch('/api/max_seller_contribution', {
                method: 'POST',
                headers: headers,
                body: JSON.stringify(data),
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Max seller contribution request failed:', error);
            throw this.handleApiError(error);
        }
    }
}

// Export singleton instance
export const apiClient = new ApiClient();