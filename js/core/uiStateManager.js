/**
 * UI State Manager for controlling loading states, error displays, and form visibility
 * Centralizes all UI state management operations
 */

export class UIStateManager {
    constructor() {
        // Cache DOM elements for performance
        this.elements = this.initializeElements();
    }

    /**
     * Initialize and cache DOM elements
     * @returns {Object} Cached DOM elements
     */
    initializeElements() {
        return {
            loadingSpinner: document.getElementById('loadingSpinner'),
            errorAlert: document.getElementById('errorAlert'),
            validationAlert: document.getElementById('validationAlert'),
            resultsSection: document.getElementById('resultsSection'),
            mortgageFormSection: document.getElementById('mortgageForm'),
            refinanceFormSection: document.getElementById('refinanceForm'),
            // Refinance result cards
            refinanceResultsCard: document.getElementById('refinanceResultsCard'),
            refinanceClosingCostsCard: document.getElementById('refinanceClosingCostsCard'),
            refinanceMonthlyPaymentCard: document.getElementById('refinanceMonthlyPaymentCard'),
            refinancePrepaidsCard: document.getElementById('refinancePrepaidsCard'),
            refinanceCreditsCard: document.getElementById('refinanceCreditsCard'),
            refinanceCashToCloseCard: document.getElementById('refinanceCashToCloseCard'),
            purchaseRadio: document.getElementById('mode_purchase'),
            refinanceRadio: document.getElementById('mode_refinance'),
            // Purchase result cards
            loanDetailsCard: document.getElementById('loanDetailsCard'),
            monthlyPaymentCard: document.getElementById('monthlyPaymentCard'),
            closingCostsCard: document.getElementById('closingCostsCard'),
            prepaidsCard: document.getElementById('prepaidsCard'),
            cashToCloseCard: document.getElementById('cashToCloseCard'),
        };
    }

    /**
     * Show loading spinner and hide other states
     */
    showLoading() {
        console.log('Showing loading spinner');
        this.safelyShow(this.elements.loadingSpinner);
        this.hideError();
        this.hideValidationError();
    }

    /**
     * Hide loading spinner
     */
    hideLoading() {
        console.log('Hiding loading spinner');
        this.safelyHide(this.elements.loadingSpinner);
    }

    /**
     * Show error message
     * @param {string} message - Error message to display
     * @param {boolean} isHtml - Whether the message contains HTML
     * @param {boolean} autoHide - Whether to auto-hide the message
     */
    showError(message, isHtml = false, autoHide = true) {
        console.log('Showing error:', message);
        const errorAlert = this.elements.errorAlert;

        if (errorAlert) {
            if (isHtml) {
                errorAlert.innerHTML = message;
            } else {
                errorAlert.textContent = message;
            }
            this.safelyShow(errorAlert);
            this.hideValidationError();

            // Auto-hide only if requested
            if (autoHide) {
                // Auto-hide after 30 seconds for HTML content (more time to read options)
                // or 10 seconds for plain text
                const hideTimeout = isHtml ? 30000 : 10000;
                setTimeout(() => this.hideError(), hideTimeout);
            }
        }
    }

    /**
     * Hide error message
     */
    hideError() {
        this.safelyHide(this.elements.errorAlert);
    }

    /**
     * Show validation error message
     * @param {string} message - Validation error message
     */
    showValidationError(message) {
        console.log('Showing validation error:', message);
        const validationAlert = this.elements.validationAlert;

        if (validationAlert) {
            validationAlert.textContent = message;
            this.safelyShow(validationAlert);
            this.hideError();

            // Auto-hide after 8 seconds
            setTimeout(() => this.hideValidationError(), 8000);
        }
    }

    /**
     * Hide validation error message
     */
    hideValidationError() {
        this.safelyHide(this.elements.validationAlert);
    }

    /**
     * Toggle form visibility between purchase and refinance modes
     */
    toggleFormVisibility() {
        const isPurchase = this.elements.purchaseRadio?.checked;

        console.log(`Toggling form visibility - Purchase mode: ${isPurchase}`);

        // Always ensure scenario toggle is visible first
        const scenarioToggle = document.getElementById('scenarioToggleRow');
        if (scenarioToggle) {
            scenarioToggle.style.display = 'block';
            console.log('Scenario toggle made visible');
        } else {
            console.error('Scenario toggle not found!');
        }

        if (isPurchase) {
            this.showPurchaseMode();
        } else {
            this.showRefinanceMode();
        }
    }

    /**
     * Show purchase mode forms and hide refinance elements
     */
    showPurchaseMode() {
        // Show purchase form
        this.safelyShow(this.elements.mortgageFormSection);
        this.safelyHide(this.elements.refinanceFormSection);

        // Always ensure scenario toggle is visible
        const scenarioToggle = document.getElementById('scenarioToggleRow');
        if (scenarioToggle) {
            scenarioToggle.style.display = 'block';
        }

        // Show purchase-only elements (except result cards)
        document.querySelectorAll('.purchase-only:not(.results-card)').forEach(el => {
            el.style.display = 'block';
        });

        // Hide refinance-only elements including results
        document.querySelectorAll('.refinance-only').forEach(el => {
            el.style.display = 'none';
        });

        // Explicitly hide refinance result cards
        this.hideRefinanceResults();
    }

    /**
     * Show refinance mode forms and hide purchase elements
     */
    showRefinanceMode() {
        // Show refinance form
        this.safelyHide(this.elements.mortgageFormSection);
        this.safelyShow(this.elements.refinanceFormSection);

        // Always ensure scenario toggle is visible
        const scenarioToggle = document.getElementById('scenarioToggleRow');
        if (scenarioToggle) {
            scenarioToggle.style.display = 'block';
        }

        // Show refinance-only elements (except result cards)
        document.querySelectorAll('.refinance-only:not(.results-card)').forEach(el => {
            el.style.display = 'block';
        });

        // Hide purchase-only elements including result cards
        document.querySelectorAll('.purchase-only, .results-card:not(.refinance-only)').forEach(el => {
            el.style.display = 'none';
        });
    }

    /**
     * Show results section and purchase result cards
     */
    showResults() {
        this.safelyShow(this.elements.resultsSection);

        // Show all purchase result cards
        this.safelyShow(this.elements.loanDetailsCard);
        this.safelyShow(this.elements.monthlyPaymentCard);
        this.safelyShow(this.elements.closingCostsCard);
        this.safelyShow(this.elements.prepaidsCard);
        this.safelyShow(this.elements.cashToCloseCard);

        // Hide refinance cards if they're visible
        this.safelyHide(this.elements.refinanceResultsCard);
        this.safelyHide(this.elements.refinanceClosingCostsCard);
    }

    /**
     * Hide results section
     */
    hideResults() {
        this.safelyHide(this.elements.resultsSection);
    }

    /**
     * Show refinance results cards and hide purchase cards
     */
    showRefinanceResults() {
        console.log('Showing refinance result cards');

        // Show all refinance cards (credits card shown conditionally by renderer)
        this.safelyShow(this.elements.refinanceResultsCard);
        this.safelyShow(this.elements.refinanceClosingCostsCard);
        this.safelyShow(this.elements.refinanceMonthlyPaymentCard);
        this.safelyShow(this.elements.refinancePrepaidsCard);
        // refinanceCreditsCard shown conditionally by refinanceResultRenderer
        this.safelyShow(this.elements.refinanceCashToCloseCard);

        // Hide all purchase cards
        this.safelyHide(this.elements.loanDetailsCard);
        this.safelyHide(this.elements.monthlyPaymentCard);
        this.safelyHide(this.elements.closingCostsCard);
        this.safelyHide(this.elements.prepaidsCard);
        this.safelyHide(this.elements.cashToCloseCard);
    }

    /**
     * Hide refinance results cards
     */
    hideRefinanceResults() {
        const refinanceCard = this.elements.refinanceResultsCard;
        const closingCostsCard = this.elements.refinanceClosingCostsCard;

        if (refinanceCard) {
            refinanceCard.style.display = 'none';
            refinanceCard.classList.add('d-none');
        }

        if (closingCostsCard) {
            closingCostsCard.style.display = 'none';
            closingCostsCard.classList.add('d-none');
        }
    }

    /**
     * Safely show an element (null check)
     * @param {HTMLElement} element - Element to show
     */
    safelyShow(element) {
        if (element) {
            element.style.display = 'block';
            element.classList.remove('d-none');
        }
    }

    /**
     * Safely hide an element (null check)
     * @param {HTMLElement} element - Element to hide
     */
    safelyHide(element) {
        if (element) {
            element.style.display = 'none';
            element.classList.add('d-none');
        }
    }

    /**
     * Set button loading state
     * @param {HTMLElement} button - Button element
     * @param {boolean} isLoading - Loading state
     */
    setButtonLoading(button, isLoading) {
        if (!button) return;

        if (isLoading) {
            // Save original text and content if not already saved
            if (!button.getAttribute('data-original-text')) {
                button.setAttribute('data-original-text', button.textContent);
                button.setAttribute('data-original-html', button.innerHTML);
            }

            button.disabled = true;
            button.textContent = 'Calculating...';
            button.classList.add('btn-loading');
        } else {
            button.disabled = false;

            // Restore original HTML (includes icons) or fall back to text
            const originalHtml = button.getAttribute('data-original-html');
            const originalText = button.getAttribute('data-original-text');

            if (originalHtml) {
                button.innerHTML = originalHtml;
            } else if (originalText) {
                button.textContent = originalText;
            } else {
                button.textContent = 'Calculate';
            }

            button.classList.remove('btn-loading');
        }
    }

    /**
     * Initialize button loading states (save original text)
     */
    initializeButtons() {
        // Initialize all calculator buttons
        const calculatorButtons = [
            'calculateBtn',
            'refinanceCalculateBtn',
            'refinanceZeroCashBtn'
        ];

        calculatorButtons.forEach(buttonId => {
            const button = document.getElementById(buttonId);
            if (button) {
                if (!button.getAttribute('data-original-text')) {
                    button.setAttribute('data-original-text', button.textContent);
                    button.setAttribute('data-original-html', button.innerHTML);
                }
            }
        });

        // Also initialize any buttons with data-loading-text attribute
        const buttons = document.querySelectorAll('[data-loading-text]');
        buttons.forEach(button => {
            if (!button.getAttribute('data-original-text')) {
                button.setAttribute('data-original-text', button.textContent);
                button.setAttribute('data-original-html', button.innerHTML);
            }
        });
    }
}

// Export singleton instance
export const uiStateManager = new UIStateManager();
