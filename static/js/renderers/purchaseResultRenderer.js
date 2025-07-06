/**
 * Purchase Result Renderer
 * Handles rendering of purchase calculation results to the UI
 */

import { updateClosingCostsTable, updateCreditsTable, updatePrepaidsTable } from '../ui/tableUpdaters.js';
import { formatCurrency, formatLabel, formatPercentage, formatPurchasePrice, formatDownPayment, safelyUpdateElement } from '../utils/formatting.js';

export class PurchaseResultRenderer {
    constructor() {
        this.resultElements = this.initializeElements();
    }

    /**
     * Initialize and cache result DOM elements
     */
    initializeElements() {
        return {
            // Main results
            monthlyPayment: document.getElementById('totalMonthlyPayment'),
            loanAmount: document.getElementById('loanAmount'),
            downPayment: document.getElementById('downPaymentAmount'),
            
            // Monthly breakdown
            monthlyMortgage: document.getElementById('principalAndInterest'),
            monthlyTax: document.getElementById('propertyTax'),
            monthlyInsurance: document.getElementById('homeInsurance'),
            monthlyPmi: document.getElementById('pmi'),
            monthlyHoa: document.getElementById('hoaFee'),
            
            // Loan details
            totalCashNeeded: document.getElementById('totalCashToClose'),
            ltvRatio: document.getElementById('ltv'),
            maxSellerContribution: document.getElementById('maxSellerContribution'),
            sellerCreditExceedsMax: null, // Element doesn't exist in current template
        };
    }

    /**
     * Update all purchase results
     * @param {Object} data - Calculation result data
     */
    updateResults(data) {
        console.log('Updating purchase results with data:', data);

        try {
            this.updateMainResults(data);
            this.updateMonthlyBreakdown(data);
            this.updateCashToClose(data);
            this.updateLoanDetails(data);
            this.updateTables(data);
            this.updateSellerContributionInfo(data);
            
            console.log('Purchase results updated successfully');
        } catch (error) {
            console.error('Error updating purchase results:', error);
            throw error;
        }
    }

    /**
     * Update main calculation results
     * @param {Object} data - Calculation result data
     */
    updateMainResults(data) {
        console.log('updateMainResults data:', {
            down_payment: data.down_payment,
            loan_details: data.loan_details
        });
        
        // Main monthly payment
        safelyUpdateElement(this.resultElements.monthlyPayment, formatCurrency(data.monthly_payment));
        
        // Loan details - update both sets of elements
        safelyUpdateElement(this.resultElements.loanAmount, formatCurrency(data.loan_amount, { isLoanAmount: true }));
        safelyUpdateElement(this.resultElements.downPayment, formatDownPayment(data.down_payment));
        
        // Also update the Loan Details card elements
        safelyUpdateElement('purchasePrice', formatPurchasePrice(data.loan_details?.purchase_price || 0));
        safelyUpdateElement('loanAmount', formatCurrency(data.loan_amount, { isLoanAmount: true }));
        
        // Down payment with percentage (special handling for nested span)
        const downPaymentElement = document.getElementById('downPaymentAmount');
        const downPaymentPercentageElement = document.getElementById('downPaymentPercentage');
        if (downPaymentElement) {
            const downPaymentAmount = formatDownPayment(data.down_payment);
            const downPaymentPercent = `${data.loan_details?.down_payment_percentage || 20}%`;
            console.log('Setting down payment:', downPaymentAmount, downPaymentPercent);
            downPaymentElement.innerHTML = `${downPaymentAmount} (<span id="downPaymentPercentage">${downPaymentPercent}</span>)`;
        } else {
            console.error('downPaymentAmount element not found');
        }
        
        // Also update the percentage element directly if it exists
        if (downPaymentPercentageElement) {
            downPaymentPercentageElement.textContent = `${data.loan_details?.down_payment_percentage || 20}%`;
        }
        
        safelyUpdateElement('interestRate', formatPercentage(data.loan_details?.interest_rate || 0));
        safelyUpdateElement('loanTerm', `${data.loan_details?.loan_term_years || 0} years`);
        safelyUpdateElement('loanType', data.loan_details?.loan_type || 'Conventional');
        safelyUpdateElement('propertyType', 'Single Family Home'); // Default property type
        
        // Format closing date if available
        const closingDate = data.loan_details?.closing_date || new Date().toISOString().split('T')[0];
        const formattedDate = new Date(closingDate).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long', 
            day: 'numeric'
        });
        safelyUpdateElement('closingDate', formattedDate);
    }

    /**
     * Update monthly payment breakdown
     * @param {Object} data - Calculation result data
     */
    updateMonthlyBreakdown(data) {
        const breakdown = data.monthly_breakdown || {};
        
        safelyUpdateElement(this.resultElements.monthlyMortgage, formatCurrency(breakdown.principal_interest));
        safelyUpdateElement(this.resultElements.monthlyTax, formatCurrency(breakdown.property_tax));
        safelyUpdateElement(this.resultElements.monthlyInsurance, formatCurrency(breakdown.home_insurance));
        safelyUpdateElement(this.resultElements.monthlyPmi, formatCurrency(breakdown.mortgage_insurance));
        safelyUpdateElement(this.resultElements.monthlyHoa, formatCurrency(breakdown.hoa_fee));
    }

    /**
     * Update cash to close information
     * @param {Object} data - Calculation result data
     */
    updateCashToClose(data) {
        safelyUpdateElement(this.resultElements.totalCashNeeded, formatCurrency(data.total_cash_needed));
    }

    /**
     * Update loan details and ratios
     * @param {Object} data - Calculation result data
     */
    updateLoanDetails(data) {
        const loanDetails = data.loan_details || {};
        
        // LTV Ratio
        if (loanDetails.ltv_ratio !== undefined) {
            safelyUpdateElement(this.resultElements.ltvRatio, formatPercentage(loanDetails.ltv_ratio));
        }
    }

    /**
     * Update seller contribution information
     * @param {Object} data - Calculation result data
     */
    updateSellerContributionInfo(data) {
        const loanDetails = data.loan_details || {};
        
        // Max seller contribution with descriptive message
        if (loanDetails.max_seller_contribution !== undefined) {
            const maxAllowable = loanDetails.max_seller_contribution;
            
            // Calculate total closing costs + prepaid
            const closingCostsTotal = data.closing_costs?.total || 0;
            const prepaidTotal = data.prepaids?.total || 0;
            const totalCostsAndPrepaid = closingCostsTotal + prepaidTotal;
            
            // Debug logging to verify calculation
            console.log('Seller credit calculation debug:', {
                closingCostsTotal,
                prepaidTotal,
                totalCostsAndPrepaid,
                maxAllowable
            });
            
            // Create descriptive message
            let message = `Max allowable seller credit equals ${formatCurrency(maxAllowable)}`;
            
            // Add conditional message if total costs + prepaid < max allowable
            if (totalCostsAndPrepaid < maxAllowable && totalCostsAndPrepaid > 0) {
                message += `. Max allowed for this scenario equals ${formatCurrency(totalCostsAndPrepaid)}`;
            }
            
            safelyUpdateElement(this.resultElements.maxSellerContribution, message);
        }

        // Seller credit exceeds max warning
        const exceedsMaxElement = this.resultElements.sellerCreditExceedsMax;
        if (exceedsMaxElement) {
            if (loanDetails.seller_credit_exceeds_max) {
                exceedsMaxElement.style.display = 'block';
                exceedsMaxElement.classList.remove('d-none');
            } else {
                exceedsMaxElement.style.display = 'none';
                exceedsMaxElement.classList.add('d-none');
            }
        }
    }

    /**
     * Update all data tables
     * @param {Object} data - Calculation result data
     */
    updateTables(data) {
        try {
            // Update closing costs table
            if (data.closing_costs && typeof updateClosingCostsTable === 'function') {
                updateClosingCostsTable(data.closing_costs);
            }

            // Update credits table
            if (data.credits && typeof updateCreditsTable === 'function') {
                updateCreditsTable(data.credits);
            }

            // Update prepaids table
            if (data.prepaids && typeof updatePrepaidsTable === 'function') {
                updatePrepaidsTable(data.prepaids);
            }

            console.log('Purchase tables updated successfully');
        } catch (error) {
            console.error('Error updating purchase tables:', error);
            // Don't throw - table updates are not critical
        }
    }

    /**
     * Update specific element with formatted value
     * @param {string} elementId - Element ID
     * @param {*} value - Value to format and display
     * @param {string} formatter - Formatter function name
     */
    updateElement(elementId, value, formatter = 'formatCurrency') {
        const element = document.getElementById(elementId);
        if (element && value !== undefined && value !== null) {
            let formattedValue = value;
            
            switch (formatter) {
                case 'formatCurrency':
                    formattedValue = formatCurrency(value);
                    break;
                case 'formatPercentage':
                    formattedValue = formatPercentage(value);
                    break;
                case 'formatLabel':
                    formattedValue = formatLabel(value);
                    break;
                default:
                    formattedValue = String(value);
            }
            
            element.textContent = formattedValue;
        }
    }

    /**
     * Clear all purchase results
     */
    clearResults() {
        Object.values(this.resultElements).forEach(element => {
            if (element) {
                element.textContent = '';
            }
        });
        
        console.log('Purchase results cleared');
    }

    /**
     * Show purchase-specific result cards
     */
    showResultCards() {
        // Show purchase-only result cards
        document.querySelectorAll('.purchase-only.results-card').forEach(card => {
            card.style.display = 'block';
            card.classList.remove('d-none');
        });
    }

    /**
     * Hide purchase-specific result cards
     */
    hideResultCards() {
        // Hide purchase-only result cards
        document.querySelectorAll('.purchase-only.results-card').forEach(card => {
            card.style.display = 'none';
            card.classList.add('d-none');
        });
    }

    /**
     * Validate that required result data is present
     * @param {Object} data - Result data to validate
     * @returns {boolean} True if data is valid
     */
    validateResultData(data) {
        const requiredFields = [
            'monthly_payment',
            'loan_amount', 
            'down_payment',
            'total_cash_needed'
        ];

        for (const field of requiredFields) {
            if (data[field] === undefined || data[field] === null) {
                console.warn(`Missing required result field: ${field}`);
                return false;
            }
        }

        return true;
    }
}

// Export singleton instance
export const purchaseResultRenderer = new PurchaseResultRenderer();