/**
 * Modular Mortgage Calculator
 * Main orchestrator that coordinates between form management, API calls, and result rendering
 */

import { apiClient } from './core/apiClient.js';
import { uiStateManager } from './core/uiStateManager.js';
import { formManager } from './core/formManager.js';
import { purchaseResultRenderer } from './renderers/purchaseResultRenderer.js';
import { refinanceResultRenderer } from './renderers/refinanceResultRenderer.js';

class MortgageCalculator {
    constructor() {
        this.initialized = false;
        this.currentMode = 'purchase';
        this.lastCalculationResult = null; // Store last calculation result
    }

    /**
     * Initialize the calculator
     */
    initialize() {
        if (this.initialized) {
            console.log('Calculator already initialized');
            return;
        }

        console.log('Initializing modular mortgage calculator...');

        try {
            this.setupEventListeners();
            this.initializeUI();
            this.initialized = true;
            console.log('Modular calculator initialized successfully');
        } catch (error) {
            console.error('Failed to initialize calculator:', error);
            uiStateManager.showError('Failed to initialize calculator. Please refresh the page.');
        }
    }

    /**
     * Setup all event listeners
     */
    setupEventListeners() {
        // Form toggle listeners
        const purchaseRadio = document.getElementById('mode_purchase');
        const refinanceRadio = document.getElementById('mode_refinance');

        if (purchaseRadio && refinanceRadio) {
            purchaseRadio.addEventListener('change', () => {
                this.currentMode = 'purchase';
                uiStateManager.toggleFormVisibility();
            });

            refinanceRadio.addEventListener('change', () => {
                this.currentMode = 'refinance';
                uiStateManager.toggleFormVisibility();
            });
        }

        // Calculate button listeners
        const calculateBtn = document.getElementById('calculateBtn');
        const refinanceCalculateBtn = document.getElementById('refinanceCalculateBtn');
        const refinanceZeroCashBtn = document.getElementById('refinanceZeroCashBtn');

        if (calculateBtn) {
            calculateBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.handleCalculation('purchase');
            });
        }

        if (refinanceCalculateBtn) {
            refinanceCalculateBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.handleCalculation('refinance');
            });
        }

        if (refinanceZeroCashBtn) {
            refinanceZeroCashBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.handleZeroCashRefinance();
            });
        }

        // Copy button listeners
        const copyResultsBtn = document.getElementById('copyResultsBtn');
        const copyDetailBtn = document.getElementById('copyDetailBtn');

        if (copyResultsBtn) {
            copyResultsBtn.addEventListener('click', () => {
                this.copyResultsSummary();
            });
        }

        if (copyDetailBtn) {
            copyDetailBtn.addEventListener('click', () => {
                this.copyResultsDetails();
            });
        }

        // Initialize form event listeners
        formManager.initializeEventListeners();
        
        // Tax and insurance method toggle listeners
        this.setupTaxInsuranceToggles();
        
        // Manual balance override toggle listener
        this.setupManualBalanceToggle();
        
        // Cash to closing options toggle listener
        this.setupCashOptionsToggle();

        console.log('Event listeners setup complete');
    }

    /**
     * Initialize UI state
     */
    initializeUI() {
        // Set initial form visibility
        uiStateManager.toggleFormVisibility();
        
        // Initialize button states
        uiStateManager.initializeButtons();
        
        // Hide any existing error messages
        uiStateManager.hideError();
        uiStateManager.hideValidationError();
        
        console.log('UI initialization complete');
    }

    /**
     * Handle calculation request
     * @param {string} mode - 'purchase' or 'refinance'
     */
    async handleCalculation(mode) {
        console.log(`Starting ${mode} calculation...`);

        try {
            // Show loading state
            this.setLoadingState(true, mode);

            // Get and validate form data
            const formData = formManager.getFormData(mode);
            const validationErrors = this.validateFormData(formData, mode);

            if (validationErrors.length > 0) {
                this.handleValidationErrors(validationErrors);
                return;
            }

            // Submit calculation
            const response = await apiClient.submitCalculation(formData, mode);

            // Handle response
            await this.handleCalculationResponse(response, mode);

        } catch (error) {
            console.error(`${mode} calculation failed:`, error);
            this.handleCalculationError(error);
        } finally {
            this.setLoadingState(false, mode);
        }
    }

    /**
     * Handle zero cash refinance calculation
     */
    async handleZeroCashRefinance() {
        console.log('Starting zero cash refinance calculation...');

        try {
            this.setLoadingState(true, 'refinance_zero_cash');

            // Get form data and add zero cash flag
            const formData = formManager.getFormData('refinance');
            formData.zero_cash_to_close = true;

            const validationErrors = this.validateFormData(formData, 'refinance');
            if (validationErrors.length > 0) {
                this.handleValidationErrors(validationErrors);
                return;
            }

            const response = await apiClient.submitCalculation(formData, 'refinance');
            await this.handleCalculationResponse(response, 'refinance');

        } catch (error) {
            console.error('Zero cash refinance calculation failed:', error);
            this.handleCalculationError(error);
        } finally {
            this.setLoadingState(false, 'refinance_zero_cash');
        }
    }

    /**
     * Validate form data
     * @param {Object} formData - Form data to validate
     * @param {string} mode - 'purchase' or 'refinance'
     * @returns {Array} Array of validation errors
     */
    validateFormData(formData, mode) {
        if (mode === 'refinance') {
            return formManager.validateRefinanceForm(formData);
        } else {
            return formManager.validatePurchaseForm(formData);
        }
    }

    /**
     * Handle calculation response
     * @param {Object} response - API response
     * @param {string} mode - 'purchase' or 'refinance'
     */
    async handleCalculationResponse(response, mode) {
        if (!response.success && !response.result) {
            throw new Error(response.error || 'Calculation failed');
        }
        
        // Check if result contains an error field (backend validation error)
        if (response.result && response.result.error) {
            throw new Error(response.result.error);
        }

        // Store the calculation result for copy functionality
        this.lastCalculationResult = { data: response, mode: mode };

        // Render results based on mode
        if (mode === 'refinance') {
            await this.renderRefinanceResults(response);
        } else {
            await this.renderPurchaseResults(response);
        }

        // Show results section and appropriate cards based on mode
        if (mode === 'refinance') {
            uiStateManager.showResults();
            uiStateManager.showRefinanceResults();
        } else {
            uiStateManager.showResults();
            // Update loan details after UI state changes (to prevent override)
            this.updateLoanDetailsCard(response);
        }
        
        console.log(`${mode} calculation completed successfully`);
    }

    /**
     * Render purchase results
     * @param {Object} response - API response
     */
    async renderPurchaseResults(response) {
        try {
            // Validate result data
            if (!purchaseResultRenderer.validateResultData(response)) {
                throw new Error('Invalid purchase result data received');
            }

            // Clear any existing results
            purchaseResultRenderer.clearResults();
            
            // Update results
            purchaseResultRenderer.updateResults(response);
            
            // Show result cards
            purchaseResultRenderer.showResultCards();
            
            console.log('Purchase results rendered successfully');
        } catch (error) {
            console.error('Error rendering purchase results:', error);
            throw new Error('Failed to display calculation results');
        }
    }

    /**
     * Render refinance results
     * @param {Object} response - API response
     */
    async renderRefinanceResults(response) {
        try {
            // Validate result data
            if (!refinanceResultRenderer.validateResultData(response)) {
                throw new Error('Invalid refinance result data received');
            }

            // Clear any existing results
            refinanceResultRenderer.clearResults();
            
            // Update results
            refinanceResultRenderer.updateResults(response);
            
            // Show refinance result cards
            uiStateManager.showRefinanceResults();
            
            console.log('Refinance results rendered successfully');
        } catch (error) {
            console.error('Error rendering refinance results:', error);
            throw new Error('Failed to display refinance results');
        }
    }

    /**
     * Handle validation errors
     * @param {Array} errors - Array of validation error messages
     */
    handleValidationErrors(errors) {
        const errorMessage = errors.join('; ');
        console.log('Validation errors:', errorMessage);
        uiStateManager.showValidationError(errorMessage);
    }

    /**
     * Update loan details card after UI state changes
     * @param {Object} response - API response
     */
    updateLoanDetailsCard(response) {
        console.log('Updating loan details card after UI state change');
        const data = response;
        
        // Check if the Loan Details card is visible
        const loanDetailsCard = document.getElementById('loanDetailsCard');
        if (loanDetailsCard) {
            const cardStyle = window.getComputedStyle(loanDetailsCard);
            console.log('Loan Details card visibility:', cardStyle.display);
            console.log('Loan Details card found:', loanDetailsCard);
        } else {
            console.error('Loan Details card (loanDetailsCard) not found!');
        }
        
        // Import formatter functions
        import('./utils/formatting.js').then(({ formatCurrency, formatPercentage, formatPurchasePrice, formatDownPayment }) => {
            // Update loan details card elements directly
            const updateElement = (id, value) => {
                const element = document.getElementById(id);
                if (element) {
                    element.textContent = value;
                    console.log(`Updated ${id} to:`, value);
                } else {
                    console.error(`Element ${id} not found`);
                }
            };
            
            updateElement('purchasePrice', formatPurchasePrice(data.loan_details?.purchase_price || 0));
            updateElement('loanAmount', formatCurrency(data.loan_amount, { isLoanAmount: true }));
            updateElement('interestRate', formatPercentage(data.loan_details?.interest_rate || 0));
            updateElement('loanTerm', `${data.loan_details?.loan_term_years || 0} years`);
            updateElement('loanType', data.loan_details?.loan_type || 'Conventional');
            updateElement('propertyType', 'Single Family Home');
            
            // Update the down payment in the Cash Needed at Closing card
            updateElement('downPayment', formatDownPayment(data.down_payment));
            
            // Special handling for down payment element with nested span
            const downPaymentElement = document.getElementById('downPaymentAmount');
            if (downPaymentElement) {
                const downPaymentAmount = formatDownPayment(data.down_payment);
                const downPaymentPercent = `${data.loan_details?.down_payment_percentage || 20}%`;
                downPaymentElement.innerHTML = `${downPaymentAmount} (<span id="downPaymentPercentage">${downPaymentPercent}</span>)`;
                console.log('Updated downPaymentAmount to:', downPaymentAmount, downPaymentPercent);
                
                // Verify what's actually in the DOM after update
                setTimeout(() => {
                    const verifyElement = document.getElementById('downPaymentAmount');
                    console.log('VERIFICATION - downPaymentAmount content after 100ms:', verifyElement ? verifyElement.innerHTML : 'ELEMENT NOT FOUND');
                    console.log('VERIFICATION - element visible:', verifyElement ? window.getComputedStyle(verifyElement).display : 'N/A');
                }, 100);
            }
            
            // Format closing date
            const closingDate = data.loan_details?.closing_date || new Date().toISOString().split('T')[0];
            const formattedDate = new Date(closingDate).toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'long', 
                day: 'numeric'
            });
            updateElement('closingDate', formattedDate);
        });
    }

    /**
     * Handle calculation errors
     * @param {Error} error - Error object
     */
    handleCalculationError(error) {
        let errorMessage = 'Calculation failed. Please try again.';
        
        if (error.message) {
            errorMessage = error.message;
        }
        
        console.error('Calculation error:', errorMessage);
        
        // Check if this is an LTV validation error that we can help with
        if (error.message && error.message.includes('LTV') && error.message.includes('exceeds maximum')) {
            this.showLTVGuidance(error.message);
        } else {
            uiStateManager.showError(errorMessage);
        }
    }

    /**
     * Show LTV guidance when validation fails
     * @param {string} errorMessage - The LTV validation error message
     */
    showLTVGuidance(errorMessage) {
        // Create a simple guidance message
        const errorHtml = `
            <div class="alert alert-warning" role="alert">
                <h5><i class="bi bi-exclamation-triangle"></i> LTV Limit Exceeded</h5>
                <p>${errorMessage}</p>
                <hr>
                <p><strong>To see how much cash you'd need to bring:</strong></p>
                <ol>
                    <li>Select <strong>"Target specific LTV"</strong> option above</li>
                    <li>Enter your desired LTV percentage (e.g., 80%, 90%, 95%)</li>
                    <li>Click <strong>"Calculate Refinance"</strong> to see the cash required</li>
                </ol>
                <small class="text-muted">This error will remain until you select a target LTV option.</small>
            </div>
        `;
        
        // Show the guidance and don't auto-hide it
        uiStateManager.showError(errorHtml, true, false); // false = don't auto-hide
    }

    /**
     * Set loading state for buttons and UI
     * @param {boolean} isLoading - Loading state
     * @param {string} mode - 'purchase', 'refinance', or 'refinance_zero_cash'
     */
    setLoadingState(isLoading, mode) {
        if (isLoading) {
            uiStateManager.showLoading();
        } else {
            uiStateManager.hideLoading();
        }

        // Update button states based on specific mode
        if (mode === 'purchase') {
            const button = document.getElementById('calculateBtn');
            uiStateManager.setButtonLoading(button, isLoading);
        } else if (mode === 'refinance') {
            const button = document.getElementById('refinanceCalculateBtn');
            uiStateManager.setButtonLoading(button, isLoading);
        } else if (mode === 'refinance_zero_cash') {
            const button = document.getElementById('refinanceZeroCashBtn');
            uiStateManager.setButtonLoading(button, isLoading);
        }
    }

    /**
     * Get current mode
     * @returns {string} Current mode ('purchase' or 'refinance')
     */
    getCurrentMode() {
        return this.currentMode;
    }

    /**
     * Reset calculator to initial state
     */
    reset() {
        // Clear results
        purchaseResultRenderer.clearResults();
        refinanceResultRenderer.clearResults();
        
        // Hide result cards
        purchaseResultRenderer.hideResultCards();
        refinanceResultRenderer.hideResultCards();
        
        // Hide results section
        uiStateManager.hideResults();
        
        // Clear error messages
        uiStateManager.hideError();
        uiStateManager.hideValidationError();
        
        console.log('Calculator reset to initial state');
    }

    /**
     * Setup tax and insurance toggle functionality
     */
    setupTaxInsuranceToggles() {
        // Tax method toggle
        const taxPercentageRadio = document.getElementById('tax_percentage');
        const taxAmountRadio = document.getElementById('tax_amount');
        const taxRateInput = document.getElementById('annual_tax_rate');
        const taxAmountInput = document.getElementById('annual_tax_amount');

        if (taxPercentageRadio && taxAmountRadio && taxRateInput && taxAmountInput) {
            taxPercentageRadio.addEventListener('change', () => {
                if (taxPercentageRadio.checked) {
                    taxRateInput.disabled = false;
                    taxRateInput.required = true;
                    taxAmountInput.disabled = true;
                    taxAmountInput.required = false;
                    taxAmountInput.value = '0';
                }
            });

            taxAmountRadio.addEventListener('change', () => {
                if (taxAmountRadio.checked) {
                    taxRateInput.disabled = true;
                    taxRateInput.required = false;
                    taxAmountInput.disabled = false;
                    taxAmountInput.required = true;
                    taxAmountInput.value = '';
                }
            });
        }

        // Insurance method toggle
        const insurancePercentageRadio = document.getElementById('insurance_percentage');
        const insuranceAmountRadio = document.getElementById('insurance_amount');
        const insuranceRateInput = document.getElementById('annual_insurance_rate');
        const insuranceAmountInput = document.getElementById('annual_insurance_amount');

        if (insurancePercentageRadio && insuranceAmountRadio && insuranceRateInput && insuranceAmountInput) {
            insurancePercentageRadio.addEventListener('change', () => {
                if (insurancePercentageRadio.checked) {
                    insuranceRateInput.disabled = false;
                    insuranceRateInput.required = true;
                    insuranceAmountInput.disabled = true;
                    insuranceAmountInput.required = false;
                    insuranceAmountInput.value = '0';
                }
            });

            insuranceAmountRadio.addEventListener('change', () => {
                if (insuranceAmountRadio.checked) {
                    insuranceRateInput.disabled = true;
                    insuranceRateInput.required = false;
                    insuranceAmountInput.disabled = false;
                    insuranceAmountInput.required = true;
                    insuranceAmountInput.value = '';
                }
            });
        }

        console.log('Tax and insurance toggles initialized');
    }

    /**
     * Setup manual balance override toggle functionality
     */
    setupManualBalanceToggle() {
        const useManualBalanceCheckbox = document.getElementById('use_manual_balance');
        const manualBalanceGroup = document.getElementById('manual_balance_group');
        const manualBalanceInput = document.getElementById('manual_current_balance');

        if (useManualBalanceCheckbox && manualBalanceGroup && manualBalanceInput) {
            useManualBalanceCheckbox.addEventListener('change', () => {
                if (useManualBalanceCheckbox.checked) {
                    manualBalanceGroup.style.display = 'block';
                    manualBalanceInput.required = true;
                } else {
                    manualBalanceGroup.style.display = 'none';
                    manualBalanceInput.required = false;
                    manualBalanceInput.value = '';
                }
            });

            console.log('Manual balance toggle initialized');
        }
    }

    /**
     * Setup cash to closing options toggle functionality
     */
    setupCashOptionsToggle() {
        const financeAllRadio = document.getElementById('finance_all');
        const targetLtvRadio = document.getElementById('target_ltv');
        const targetLtvGroup = document.getElementById('target_ltv_group');
        const targetLtvInput = document.getElementById('target_ltv_value');

        if (financeAllRadio && targetLtvRadio && targetLtvGroup) {
            // Finance all costs (default)
            financeAllRadio.addEventListener('change', () => {
                if (financeAllRadio.checked) {
                    targetLtvGroup.style.display = 'none';
                    if (targetLtvInput) targetLtvInput.required = false;
                }
            });

            // Target LTV
            targetLtvRadio.addEventListener('change', () => {
                if (targetLtvRadio.checked) {
                    targetLtvGroup.style.display = 'block';
                    if (targetLtvInput) targetLtvInput.required = true;
                }
            });

            console.log('Cash options toggle initialized');
        }
    }

    /**
     * Copy results summary to clipboard
     * Copies loan details and totals from result cards in plain text format
     */
    async copyResultsSummary() {
        let summaryText = '';
        const mode = this.getCurrentMode();
        
        if (mode === 'purchase') {
            summaryText = this.generatePurchaseSummary();
        } else {
            summaryText = this.generateRefinanceSummary();
        }
        
        try {
            await navigator.clipboard.writeText(summaryText);
            this.showCopyConfirmation();
            console.log('Results summary copied to clipboard');
        } catch (error) {
            console.error('Failed to copy summary:', error);
            // Fallback for older browsers
            this.fallbackCopyToClipboard(summaryText);
        }
    }

    /**
     * Copy detailed results to clipboard
     * Copies all details from all result cards in formatted plain text
     */
    async copyResultsDetails() {
        let detailsText = '';
        const mode = this.getCurrentMode();
        
        if (mode === 'purchase') {
            detailsText = this.generatePurchaseDetails();
        } else {
            detailsText = this.generateRefinanceDetails();
        }
        
        try {
            await navigator.clipboard.writeText(detailsText);
            this.showCopyConfirmation();
            console.log('Results details copied to clipboard');
        } catch (error) {
            console.error('Failed to copy details:', error);
            // Fallback for older browsers
            this.fallbackCopyToClipboard(detailsText);
        }
    }

    /**
     * Generate purchase summary text
     */
    generatePurchaseSummary() {
        // Use stored calculation data if available, otherwise read from DOM
        const data = this.lastCalculationResult?.data;
        
        // Basic loan info - prefer data from API response
        const purchasePrice = data?.loan_details?.purchase_price ? 
            `$${data.loan_details.purchase_price.toLocaleString()}` : 
            document.getElementById('purchasePrice')?.textContent || '$0.00';
            
        const loanType = data?.loan_details?.loan_type || 
            document.getElementById('loanType')?.textContent || 'Conventional';
            
        const interestRate = data?.loan_details?.interest_rate ? 
            `${data.loan_details.interest_rate}%` : 
            document.getElementById('interestRate')?.textContent || '0.00%';
            
        const loanTerm = data?.loan_details?.loan_term_years ? 
            `${data.loan_details.loan_term_years} years` : 
            document.getElementById('loanTerm')?.textContent || '30 years';

        // Key totals from each card - prefer data from API response
        const monthlyPayment = data?.monthly_payment ? 
            `$${data.monthly_payment.toLocaleString()}` : 
            document.getElementById('totalMonthlyPayment')?.textContent || '$0.00';
            
        const downPayment = data?.down_payment ? 
            `$${data.down_payment.toLocaleString()} (${data.loan_details?.down_payment_percentage || 20}%)` : 
            document.getElementById('downPaymentAmount')?.textContent || '$0.00';
            
        const loanAmount = data?.loan_amount ? 
            `$${data.loan_amount.toLocaleString()}` : 
            document.getElementById('loanAmount')?.textContent || '$0.00';
        
        // Totals from other cards
        const closingCostsTotal = data?.closing_costs?.total ? 
            `$${data.closing_costs.total.toLocaleString()}` : 
            document.getElementById('totalClosingCostsCell')?.textContent || 
            document.querySelector('#closingCostsTable tfoot td:last-child')?.textContent || '$0.00';
            
        const prepaidsTotal = data?.prepaids?.total ? 
            `$${data.prepaids.total.toLocaleString()}` : 
            document.getElementById('totalPrepaids')?.textContent || '$0.00';
            
        const creditsTotal = data?.credits?.total ? 
            `$${data.credits.total.toLocaleString()}` : 
            document.getElementById('totalCredits')?.textContent || '$0.00';
            
        const cashToClose = data?.total_cash_needed ? 
            `$${data.total_cash_needed.toLocaleString()}` : 
            document.getElementById('totalCashToClose')?.textContent || '$0.00';

        return `MORTGAGE CALCULATION SUMMARY

Purchase Price: ${purchasePrice}
Down Payment: ${downPayment}
Loan Amount: ${loanAmount}
Loan Type: ${loanType}
Interest Rate: ${interestRate}
Loan Term: ${loanTerm}

Monthly Payment: ${monthlyPayment}

Closing Costs: ${closingCostsTotal}
Prepaid Items: ${prepaidsTotal}
Credits: ${creditsTotal}

Total Cash Needed: ${cashToClose}

Generated on ${new Date().toLocaleDateString()}`;
    }

    /**
     * Generate refinance summary text
     */
    generateRefinanceSummary() {
        // Use stored calculation data if available, otherwise read from DOM
        const data = this.lastCalculationResult?.data?.result || this.lastCalculationResult?.data;
        
        // Basic refinance info - prefer data from API response
        const currentBalance = data?.current_balance ? 
            `$${data.current_balance.toLocaleString()}` : 
            document.getElementById('currentBalance')?.textContent || '$0.00';
            
        const newLoanAmount = data?.new_loan_amount ? 
            `$${data.new_loan_amount.toLocaleString()}` : 
            document.getElementById('newLoanAmount')?.textContent || '$0.00';
            
        const ltv = data?.ltv ? 
            `${data.ltv}%` : 
            document.getElementById('refinanceLTV')?.textContent || '0.00%';

        // Payment comparison
        const oldPayment = data?.original_monthly_payment ? 
            `$${data.original_monthly_payment.toLocaleString()}` : 
            document.getElementById('oldMonthlyPayment')?.textContent || '$0.00';
            
        const newPayment = data?.new_monthly_payment ? 
            `$${data.new_monthly_payment.toLocaleString()}` : 
            document.getElementById('newMonthlyPayment')?.textContent || '$0.00';
            
        const monthlySavings = data?.monthly_savings ? 
            `$${data.monthly_savings.toLocaleString()}` : 
            document.getElementById('monthlySavings')?.textContent || '$0.00';

        // Costs and savings
        const breakEven = data?.break_even_time || 
            document.getElementById('breakEvenPoint')?.textContent || '0 months';
            
        const totalSavings = data?.total_savings ? 
            `$${data.total_savings.toLocaleString()}` : 
            document.getElementById('totalSavings')?.textContent || '$0.00';
        
        // Get closing costs total
        const refinanceClosingCosts = data?.total_closing_costs ? 
            `$${data.total_closing_costs.toLocaleString()}` : 
            document.querySelector('#refinanceClosingCostsTable .total-row td:last-child')?.textContent || '$0.00';
        
        // Get cash to close
        const cashToClose = data?.cash_to_close ? 
            `$${data.cash_to_close.toLocaleString()}` : 
            document.getElementById('refinanceCashToClose')?.textContent || '$0.00';

        return `REFINANCE CALCULATION SUMMARY

Current Loan Balance: ${currentBalance}
New Loan Amount: ${newLoanAmount}
Loan-to-Value (LTV): ${ltv}

Old Monthly Payment: ${oldPayment}
New Monthly Payment: ${newPayment}
Monthly Savings: ${monthlySavings}

Closing Costs: ${refinanceClosingCosts}
Cash to Close: ${cashToClose}

Break-Even Point: ${breakEven}
Total Savings: ${totalSavings}

Generated on ${new Date().toLocaleDateString()}`;
    }

    /**
     * Generate detailed purchase results
     */
    generatePurchaseDetails() {
        let details = this.generatePurchaseSummary() + '\n\n';
        
        // Add monthly breakdown
        details += 'MONTHLY PAYMENT BREAKDOWN\n';
        details += this.extractTableData('monthlyBreakdownTable') + '\n';
        
        // Add closing costs
        details += 'CLOSING COSTS\n';
        details += this.extractTableData('closingCostsTable') + '\n';
        
        // Add prepaid items
        details += 'PREPAID ITEMS\n';
        details += this.extractTableData('prepaidsTable') + '\n';
        
        // Add credits if any
        details += 'CREDITS\n';
        details += this.extractTableData('creditsTable') + '\n';
        
        return details;
    }

    /**
     * Generate detailed refinance results
     */
    generateRefinanceDetails() {
        let details = this.generateRefinanceSummary() + '\n\n';
        
        // Add monthly breakdown
        details += 'NEW MONTHLY PAYMENT BREAKDOWN\n';
        details += this.extractTableData('refinanceMonthlyPaymentCard') + '\n';
        
        // Add closing costs
        details += 'CLOSING COSTS\n';
        details += this.extractTableData('refinanceClosingCostsTable') + '\n';
        
        return details;
    }

    /**
     * Extract data from table elements
     */
    extractTableData(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return 'No data available\n';
        
        let tableText = '';
        const rows = container.querySelectorAll('tr');
        
        rows.forEach(row => {
            const cells = row.querySelectorAll('td');
            if (cells.length >= 2) {
                const label = cells[0].textContent.trim();
                const value = cells[1].textContent.trim();
                tableText += `${label}: ${value}\n`;
            }
        });
        
        return tableText || 'No data available\n';
    }

    /**
     * Show copy confirmation message
     */
    showCopyConfirmation() {
        const confirmation = document.getElementById('copyConfirmation');
        if (confirmation) {
            confirmation.classList.remove('d-none');
            setTimeout(() => {
                confirmation.classList.add('d-none');
            }, 2000);
        }
    }

    /**
     * Fallback copy method for older browsers
     */
    fallbackCopyToClipboard(text) {
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        
        try {
            document.execCommand('copy');
            this.showCopyConfirmation();
            console.log('Fallback copy successful');
        } catch (err) {
            console.error('Fallback copy failed:', err);
            alert('Copy failed. Please manually select and copy the text.');
        }
        
        document.body.removeChild(textArea);
    }
}

// Initialize calculator when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing modular calculator...');
    
    try {
        const calculator = new MortgageCalculator();
        calculator.initialize();
        
        // Make calculator available globally for debugging
        window.mortgageCalculator = calculator;
        
    } catch (error) {
        console.error('Failed to initialize mortgage calculator:', error);
        
        // Show error to user
        const errorAlert = document.getElementById('errorAlert');
        if (errorAlert) {
            errorAlert.textContent = 'Failed to initialize calculator. Please refresh the page.';
            errorAlert.style.display = 'block';
        }
    }
});

// Export for potential use in other modules
export { MortgageCalculator };