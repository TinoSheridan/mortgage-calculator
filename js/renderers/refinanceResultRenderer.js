/**
 * Refinance Result Renderer
 * Handles rendering of refinance calculation results to the UI
 */

import { formatCurrency, formatLabel, formatPercentage, safelyUpdateElement } from '../utils/formatting.js';

export class RefinanceResultRenderer {
    constructor() {
        this.resultElements = this.initializeElements();
    }

    /**
     * Initialize and cache result DOM elements
     */
    initializeElements() {
        return {
            // Main refinance results (using actual element IDs from HTML)
            newMonthlyPayment: document.getElementById('refinanceTotalMonthlyPayment'),
            newMonthlyPaymentFooter: document.getElementById('refinanceTotalMonthlyPaymentFooter'),
            principalAndInterest: document.getElementById('refinancePrincipalAndInterest'),
            propertyTax: document.getElementById('refinancePropertyTax'),
            homeInsurance: document.getElementById('refinanceHomeInsurance'),
            pmi: document.getElementById('refinancePmi'),
            hoaFee: document.getElementById('refinanceHoaFee'),

            // Loan details (using actual element IDs from HTML)
            newLoanAmount: document.getElementById('newLoanAmount'),
            refinanceNewLoanAmount: document.getElementById('refinance_new_loan_amount'),
            currentBalance: document.getElementById('currentBalance'),
            cashToClose: document.getElementById('refinanceCashToClose'),
            loanIncrease: document.getElementById('loanIncrease'),
            financedClosingCosts: document.getElementById('financedClosingCosts'),
            refinanceLTV: document.getElementById('refinanceLTV'),

            // Comparison and savings elements (in refinanceResultsCard)
            oldMonthlyPayment: document.getElementById('oldMonthlyPayment'),
            newMonthlyPaymentComparison: document.getElementById('newMonthlyPayment'),
            monthlySavings: document.getElementById('monthlySavings'),
            breakEvenPoint: document.getElementById('breakEvenPoint'),
            totalSavings: document.getElementById('totalSavings'),

            // Cash to close breakdown elements
            totalClosingCostsSummary: document.getElementById('refinanceTotalClosingCostsSummary'),
            totalPrepaidsSummary: document.getElementById('refinanceTotalPrepaidsSummary'),
            amountFinanced: document.getElementById('refinanceAmountFinanced'),
            totalCreditsSummary: document.getElementById('refinanceTotalCreditsSummary'),
            finalCashToClose: document.getElementById('refinanceFinalCashToClose'),

            // Prepaid and credits totals
            totalPrepaids: document.getElementById('refinanceTotalPrepaids'),
            totalCredits: document.getElementById('refinanceTotalCredits'),

            // Special messages
            zeroCashMessage: document.getElementById('zero_cash_message'),
            breakEvenMessage: document.getElementById('break_even_message'),
        };
    }

    /**
     * Update all refinance results
     * @param {Object} data - Calculation result data
     */
    updateResults(data) {
        console.log('Updating refinance results with data:', data);

        try {
            const result = data.result || data;

            this.updateMainResults(result);
            this.updateLoanDetails(result);
            this.updateClosingCosts(result);
            this.updatePrepaidsTable(result);
            this.updateCreditsTable(result);
            this.updateCashToCloseTable(result);
            this.updateSpecialMessages(result);
            this.updateLtvTargetsTable(result);

            console.log('Refinance results updated successfully');
        } catch (error) {
            console.error('Error updating refinance results:', error);
            throw error;
        }
    }

    /**
     * Update main refinance calculation results
     * @param {Object} result - Calculation result data
     */
    updateMainResults(result) {
        // New monthly payment (total) - use the total payment including all components
        const breakdown = result.monthly_breakdown || {};
        const totalPayment = breakdown.total || result.new_monthly_payment;

        safelyUpdateElement(this.resultElements.newMonthlyPayment, formatCurrency(totalPayment));
        safelyUpdateElement(this.resultElements.newMonthlyPaymentFooter, formatCurrency(totalPayment));

        // Monthly payment breakdown
        safelyUpdateElement(this.resultElements.principalAndInterest, formatCurrency(breakdown.principal_interest));
        safelyUpdateElement(this.resultElements.propertyTax, formatCurrency(breakdown.property_tax));
        safelyUpdateElement(this.resultElements.homeInsurance, formatCurrency(breakdown.insurance));
        safelyUpdateElement(this.resultElements.pmi, formatCurrency(breakdown.pmi));
        safelyUpdateElement(this.resultElements.hoaFee, formatCurrency(breakdown.hoa));
    }

    /**
     * Update loan details section
     * @param {Object} result - Calculation result data
     */
    updateLoanDetails(result) {
        // Update loan amounts
        safelyUpdateElement(this.resultElements.newLoanAmount, formatCurrency(result.new_loan_amount));
        safelyUpdateElement(this.resultElements.refinanceNewLoanAmount, formatCurrency(result.new_loan_amount));

        // Update current balance and cash to close
        safelyUpdateElement(this.resultElements.currentBalance, formatCurrency(result.current_balance));

        // Use cash_to_close as the primary value (includes prepaids + cash contribution - credits)
        const cashToClose = result.cash_to_close || 0;
        safelyUpdateElement(this.resultElements.cashToClose, formatCurrency(cashToClose));

        // Update LTV ratio (the refinance calculator returns 'ltv' directly)
        if (result.ltv !== undefined) {
            safelyUpdateElement(this.resultElements.refinanceLTV, formatPercentage(result.ltv));
        }

        // Update comparison and savings data
        safelyUpdateElement(this.resultElements.oldMonthlyPayment, formatCurrency(result.original_monthly_payment));
        safelyUpdateElement(this.resultElements.newMonthlyPaymentComparison, formatCurrency(result.new_monthly_payment));
        // Enhanced monthly savings display with breakdown if extra savings exist
        if (result.extra_monthly_savings && result.extra_monthly_savings > 0) {
            const savingsBreakdown = `${formatCurrency(result.monthly_savings)}
                <small class="text-muted d-block">
                    (Payment savings: ${formatCurrency(result.base_monthly_savings)} +
                    Extra savings: ${formatCurrency(result.extra_monthly_savings)})
                </small>`;
            if (this.resultElements.monthlySavings) {
                this.resultElements.monthlySavings.innerHTML = savingsBreakdown;
            }
        } else {
            safelyUpdateElement(this.resultElements.monthlySavings, formatCurrency(result.monthly_savings));
        }
        safelyUpdateElement(this.resultElements.totalSavings, formatCurrency(result.total_savings));

        // Format break-even point
        if (result.break_even_months !== undefined && result.break_even_months !== null) {
            const breakEvenText = result.break_even_months > 0 ? `${result.break_even_months} months` : 'N/A';
            safelyUpdateElement(this.resultElements.breakEvenPoint, breakEvenText);
        }

        // Update loan increase and financed closing costs if applicable
        if (result.loan_increase) {
            safelyUpdateElement(this.resultElements.loanIncrease, formatCurrency(result.loan_increase));
            const loanIncreaseSection = document.getElementById('loanIncreaseSection');
            if (loanIncreaseSection) {
                loanIncreaseSection.classList.remove('d-none');
            }
        }

        if (result.financed_closing_costs) {
            safelyUpdateElement(this.resultElements.financedClosingCosts, formatCurrency(result.financed_closing_costs));
            const financedSection = document.getElementById('financedClosingCostsSection');
            if (financedSection) {
                financedSection.classList.remove('d-none');
            }
        }
    }

    /**
     * Update closing costs breakdown
     * @param {Object} result - Calculation result data
     */
    updateClosingCosts(result) {
        // Call the global function to update the refinance closing costs table
        if (typeof window.updateRefinanceClosingCostsTable === 'function') {
            console.log('Calling updateRefinanceClosingCostsTable with result:', result);
            window.updateRefinanceClosingCostsTable(result);
        } else {
            console.warn('updateRefinanceClosingCostsTable function not found on window object');

            // Fallback: try to import and call the function
            try {
                import('../ui/tableUpdaters.js').then(module => {
                    if (module.updateRefinanceClosingCostsTable) {
                        console.log('Calling updateRefinanceClosingCostsTable from imported module');
                        module.updateRefinanceClosingCostsTable(result);
                    }
                });
            } catch (error) {
                console.error('Error importing tableUpdaters:', error);
            }
        }
    }

    /**
     * Update prepaids table for refinance
     * @param {Object} result - Calculation result data
     */
    updatePrepaidsTable(result) {
        const prepaidsTable = document.getElementById('refinancePrepaidsTable');

        if (!prepaidsTable) {
            console.warn('Refinance prepaids table not found');
            return;
        }

        // Clear existing content
        prepaidsTable.innerHTML = '';

        const prepaidItems = result.prepaid_items || {};
        const totalPrepaids = prepaidItems.total || 0;

        // Update total using element reference
        safelyUpdateElement(this.resultElements.totalPrepaids, formatCurrency(totalPrepaids));

        // For refinance, only show relevant items (no seller-related items)
        const refinanceRelevantItems = [
            'prepaid_interest',      // Per diem interest
            'tax_escrow',           // Tax escrow reserves
            'insurance_escrow',     // Insurance escrow reserves
            'prepaid_insurance',    // Insurance premium (if any)
            'prepaid_tax'          // Prepaid taxes (if any)
        ];

        // Custom labels for refinance items
        const refinanceLabels = {
            'prepaid_interest': 'Per Diem Interest',
            'tax_escrow': `Property Tax Escrow (${prepaidItems.tax_escrow_months || 'N/A'} months)`,
            'insurance_escrow': `Insurance Escrow (${prepaidItems.insurance_escrow_months || 'N/A'} months)`,
            'prepaid_insurance': 'Insurance Premium',
            'prepaid_tax': 'Prepaid Property Tax'
        };

        // Add relevant prepaid line items only
        refinanceRelevantItems.forEach(key => {
            const value = prepaidItems[key];
            if (value !== undefined && typeof value === 'number' && value > 0) {
                const row = document.createElement('tr');
                const labelCell = document.createElement('td');
                const valueCell = document.createElement('td');

                labelCell.textContent = refinanceLabels[key] || formatLabel(key);
                valueCell.textContent = formatCurrency(value);
                valueCell.className = 'text-end';

                row.appendChild(labelCell);
                row.appendChild(valueCell);
                prepaidsTable.appendChild(row);
            }
        });

        // If no relevant items, show a message
        if (prepaidsTable.children.length === 0) {
            const row = document.createElement('tr');
            const cell = document.createElement('td');
            cell.colSpan = 2;
            cell.textContent = 'No prepaid items required for this refinance';
            cell.className = 'text-muted fst-italic';
            row.appendChild(cell);
            prepaidsTable.appendChild(row);
        }

        console.log(`Updated refinance prepaids table with total: ${formatCurrency(totalPrepaids)}`);
    }

    /**
     * Update credits table for refinance
     * @param {Object} result - Calculation result data
     */
    updateCreditsTable(result) {
        const creditsTable = document.getElementById('refinanceCreditsTable');

        if (!creditsTable) {
            console.warn('Refinance credits table not found');
            return;
        }

        // Clear existing content
        creditsTable.innerHTML = '';

        const credits = result.credits || {};
        const totalCredits = credits.total || 0;

        // Show/hide credits card based on whether there are credits
        const creditsCard = document.getElementById('refinanceCreditsCard');
        if (totalCredits > 0) {
            creditsCard.style.display = 'block';
        } else {
            creditsCard.style.display = 'none';
        }

        // Update total using element reference
        safelyUpdateElement(this.resultElements.totalCredits, formatCurrency(totalCredits));

        // Add credit line items
        Object.entries(credits).forEach(([key, value]) => {
            if (key !== 'total' && typeof value === 'number' && value > 0) {
                const row = document.createElement('tr');
                const labelCell = document.createElement('td');
                const valueCell = document.createElement('td');

                labelCell.textContent = formatLabel(key);
                valueCell.textContent = formatCurrency(value);
                valueCell.className = 'text-end';

                row.appendChild(labelCell);
                row.appendChild(valueCell);
                creditsTable.appendChild(row);
            }
        });

        console.log(`Updated refinance credits table with total: ${formatCurrency(totalCredits)}`);
    }

    /**
     * Update cash to close breakdown table
     * @param {Object} result - Calculation result data
     */
    updateCashToCloseTable(result) {
        // Update the breakdown table in the cash to close card using proper element references
        const closingCosts = result.total_closing_costs || 0;
        const prepaids = result.prepaid_items?.total || 0;
        const credits = result.credits?.total || 0;

        // In zero cash mode, both closing costs and prepaids are financed
        // In standard mode, only closing costs are financed
        let financedAmount;
        if (result.zero_cash_mode) {
            financedAmount = (result.financed_closing_costs || 0) + (result.prepaid_items?.total || 0);
        } else {
            financedAmount = result.financed_closing_costs || 0;
        }

        // Use cash_to_close as the primary value (includes prepaids + cash contribution - credits)
        const cashToClose = result.cash_to_close || 0;

        // Update all the summary elements
        safelyUpdateElement(this.resultElements.totalClosingCostsSummary, formatCurrency(closingCosts));
        safelyUpdateElement(this.resultElements.totalPrepaidsSummary, formatCurrency(prepaids));
        safelyUpdateElement(this.resultElements.amountFinanced, `(${formatCurrency(financedAmount)})`);
        safelyUpdateElement(this.resultElements.totalCreditsSummary, `(${formatCurrency(credits)})`);
        safelyUpdateElement(this.resultElements.finalCashToClose, formatCurrency(cashToClose));

        // Show/hide and update additional line items for target LTV scenarios
        const downPaymentRow = document.getElementById('refinanceDownPaymentRow');
        const lenderCreditRow = document.getElementById('refinanceLenderCreditRow');

        // Show cash to pay down loan if this is a target LTV scenario with cash needed
        if (result.cash_option === 'target_ltv' && result.cash_needed_at_closing > 0) {
            if (downPaymentRow) {
                downPaymentRow.style.display = 'table-row';
                safelyUpdateElement(document.getElementById('refinanceDownPayment'), formatCurrency(result.cash_needed_at_closing));
            }
        } else if (downPaymentRow) {
            downPaymentRow.style.display = 'none';
        }

        // Show lender credit if it exists
        if (result.refinance_lender_credit && result.refinance_lender_credit > 0) {
            if (lenderCreditRow) {
                lenderCreditRow.style.display = 'table-row';
                safelyUpdateElement(document.getElementById('refinanceLenderCreditAmount'), `(${formatCurrency(result.refinance_lender_credit)})`);
            }
        } else if (lenderCreditRow) {
            lenderCreditRow.style.display = 'none';
        }

        // Add cash contribution info if applicable
        if (result.cash_option && result.cash_option !== 'finance_all') {
            let contributionText = '';
            const cashDescElement = document.querySelector('#refinanceCashToCloseCard .text-muted');

            if (result.refinance_type === 'cash_out') {
                // Cash-out refinance - show cash received or needed
                if (result.cash_received > 0) {
                    contributionText = ` (cash you receive at closing)`;
                    if (cashDescElement) {
                        cashDescElement.textContent = `Amount of cash you receive at closing${contributionText}`;
                    }
                } else {
                    contributionText = ` (cash you need to bring to closing)`;
                    if (cashDescElement) {
                        cashDescElement.textContent = `Amount you need to bring to closing${contributionText}`;
                    }
                }
            } else {
                // Rate/term refinance
                if (result.cash_option === 'target_ltv' && result.cash_needed_at_closing > 0) {
                    contributionText = ` (to achieve ${result.target_ltv_value}% LTV)`;
                    if (cashDescElement) {
                        cashDescElement.textContent = `Amount you need to bring to closing${contributionText}`;
                    }
                }
            }
        }

        console.log(`Updated cash to close breakdown: ${formatCurrency(cashToClose)}`);
    }

    /**
     * Update special messages and alerts
     * @param {Object} result - Calculation result data
     */
    updateSpecialMessages(result) {
        // Zero cash to close message
        const zeroCashElement = this.resultElements.zeroCashMessage;
        if (zeroCashElement) {
            if (result.zero_cash_to_close_mode || result.cash_to_close <= 0) {
                zeroCashElement.style.display = 'block';
                zeroCashElement.classList.remove('d-none');
            } else {
                zeroCashElement.style.display = 'none';
                zeroCashElement.classList.add('d-none');
            }
        }

        // Break-even analysis message
        const breakEvenElement = this.resultElements.breakEvenMessage;
        if (breakEvenElement && result.break_even_months) {
            const message = `Break-even point: ${result.break_even_months} months`;
            breakEvenElement.textContent = message;
            breakEvenElement.style.display = 'block';
            breakEvenElement.classList.remove('d-none');
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
            console.log(`Updated ${elementId} with ${formattedValue}`);
        } else if (!element) {
            console.warn(`Element with ID ${elementId} not found`);
        }
    }

    /**
     * Clear all refinance results
     */
    clearResults() {
        Object.values(this.resultElements).forEach(element => {
            if (element) {
                element.textContent = '';
            }
        });

        console.log('Refinance results cleared');
    }

    /**
     * Show refinance-specific result cards
     */
    showResultCards() {
        // Show refinance-only result cards
        document.querySelectorAll('.refinance-only.results-card').forEach(card => {
            card.style.display = 'block';
            card.classList.remove('d-none');
        });
    }

    /**
     * Hide refinance-specific result cards
     */
    hideResultCards() {
        // Hide refinance-only result cards
        document.querySelectorAll('.refinance-only.results-card').forEach(card => {
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
        const result = data.result || data;
        const requiredFields = [
            'new_monthly_payment',
            'new_loan_amount',
            'cash_to_close'
        ];


        for (const field of requiredFields) {
            if (result[field] === undefined || result[field] === null) {
                console.warn(`Missing required refinance result field: ${field}`);
                console.warn(`Available fields: ${Object.keys(result).join(', ')}`);
                return false;
            }
        }

        return true;
    }

    /**
     * Update LTV targets table with backend-calculated minimum appraised values
     * @param {Object} result - Calculation result data
     */
    updateLtvTargetsTable(result) {
        // Check if backend provided min_appraised_values
        if (!result.min_appraised_values) {
            console.log('No min_appraised_values in result, skipping LTV targets update');
            return;
        }

        const minAppraisedValues = result.min_appraised_values;
        console.log('Updating LTV targets with backend values:', minAppraisedValues);

        // Update 80% LTV value
        if (minAppraisedValues.ltv_80) {
            const element80 = document.getElementById('ltv80ValueZeroCash');
            if (element80) {
                element80.textContent = formatCurrency(minAppraisedValues.ltv_80);
            }
        }

        // Update 90% LTV value
        if (minAppraisedValues.ltv_90) {
            const element90 = document.getElementById('ltv90ValueZeroCash');
            if (element90) {
                element90.textContent = formatCurrency(minAppraisedValues.ltv_90);
            }
        }

        // Update 95% LTV value
        if (minAppraisedValues.ltv_95) {
            const element95 = document.getElementById('ltv95ValueZeroCash');
            if (element95) {
                element95.textContent = formatCurrency(minAppraisedValues.ltv_95);
            }
        }

        // Update max LTV value if applicable (checking for common loan type max LTVs)
        const loanType = result.loan_type;
        const refinanceType = result.refinance_type;

        if (loanType && refinanceType) {
            const maxLtvLimits = {
                'conventional': {
                    'rate_term': 97.0,
                    'cash_out': 80.0,
                    'streamline': 97.0
                },
                'fha': {
                    'rate_term': 96.5,
                    'cash_out': 80.0,
                    'streamline': 96.5
                },
                'va': {
                    'rate_term': 100.0,
                    'cash_out': 100.0,
                    'streamline': 100.0
                },
                'usda': {
                    'rate_term': 100.0,
                    'cash_out': 0.0,
                    'streamline': 100.0
                }
            };

            const maxLtv = maxLtvLimits[loanType]?.[refinanceType];
            if (maxLtv && maxLtv > 0) {
                const maxLtvKey = `ltv_${Math.round(maxLtv)}`;
                if (minAppraisedValues[maxLtvKey]) {
                    const maxLtvElement = document.getElementById('maxLtvValueZeroCash');
                    if (maxLtvElement) {
                        maxLtvElement.textContent = formatCurrency(minAppraisedValues[maxLtvKey]);
                    }
                }

                // Update max LTV text
                const maxLtvTextElement = document.getElementById('maxLtvText');
                if (maxLtvTextElement) {
                    maxLtvTextElement.textContent = `${maxLtv}% max for ${loanType.toUpperCase()} ${refinanceType.replace('_', ' ')}`;
                }
            }
        }

        console.log('LTV targets table updated with backend values');
    }

}

// Export singleton instance
export const refinanceResultRenderer = new RefinanceResultRenderer();
