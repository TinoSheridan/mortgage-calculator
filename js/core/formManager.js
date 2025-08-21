/**
 * Form Manager for handling form data collection and validation
 * Manages both purchase and refinance forms
 */

import { safeNumber } from '../utils/formatting.js';

export class FormManager {
    constructor() {
        this.purchaseForm = document.getElementById('mortgageForm');
        this.refinanceForm = document.getElementById('refinanceForm');
    }

    /**
     * Get form data based on the current mode
     * @param {string} mode - 'purchase' or 'refinance'
     * @returns {Object} Form data object
     */
    getFormData(mode) {
        if (mode === 'refinance') {
            return this.getRefinanceFormData();
        } else {
            return this.getPurchaseFormData();
        }
    }

    /**
     * Get purchase form data
     * @returns {Object} Purchase form data
     */
    getPurchaseFormData() {
        const formData = {
            purchase_price: safeNumber(this.getValueById('purchase_price')),
            down_payment_percentage: safeNumber(this.getValueById('down_payment_percentage')),
            annual_rate: safeNumber(this.getValueById('annual_rate')),
            loan_term: safeNumber(this.getValueById('loan_term')),
            annual_tax_rate: safeNumber(this.getValueById('annual_tax_rate')),
            annual_insurance_rate: safeNumber(this.getValueById('annual_insurance_rate')),
            monthly_hoa_fee: safeNumber(this.getValueById('monthly_hoa_fee')),
            loan_type: this.getSelectedValue('loan_type'),
            seller_credit: safeNumber(this.getValueById('seller_credit')),
            lender_credit: safeNumber(this.getValueById('lender_credit')),
            discount_points: safeNumber(this.getValueById('discount_points')),
            closing_date: this.getValueById('closing_date'),
            include_owners_title: this.getCheckboxValue('include_owners_title'),
            // Tax and insurance method overrides
            tax_method: this.getSelectedValue('tax_method'),
            insurance_method: this.getSelectedValue('insurance_method'),
            annual_tax_amount: safeNumber(this.getValueById('annual_tax_amount')),
            annual_insurance_amount: safeNumber(this.getValueById('annual_insurance_amount')),
        };

        // Add VA-specific fields if VA loan type is selected
        if (formData.loan_type === 'va') {
            formData.va_service_type = this.getSelectedValue('va_service_type');
            formData.va_usage = this.getSelectedValue('va_usage');
            formData.va_disability_exempt = this.getCheckboxValue('va_disability_exempt');
        }

        return formData;
    }

    /**
     * Get refinance form data
     * @returns {Object} Refinance form data
     */
    getRefinanceFormData() {
        const cashOption = this.getSelectedValue('cash_option');
        const formData = {
            appraised_value: safeNumber(this.getValueById('appraised_value')),
            original_loan_balance: safeNumber(this.getValueById('original_loan_balance')),
            original_interest_rate: safeNumber(this.getValueById('original_interest_rate')),
            original_loan_term: safeNumber(this.getValueById('original_loan_term')),
            original_closing_date: this.getValueById('original_closing_date'),
            use_manual_balance: this.getCheckboxValue('use_manual_balance'),
            manual_current_balance: safeNumber(this.getValueById('manual_current_balance')),
            cash_option: cashOption,
            new_interest_rate: safeNumber(this.getValueById('new_interest_rate')),
            new_loan_term: safeNumber(this.getValueById('new_loan_term')),
            new_closing_date: this.getValueById('new_closing_date'),
            annual_taxes: safeNumber(this.getValueById('annual_taxes')),
            annual_insurance: safeNumber(this.getValueById('annual_insurance')),
            // Force amount method when actual dollar amounts are provided
            tax_method: 'amount',
            insurance_method: 'amount',
            monthly_hoa_fee: safeNumber(this.getValueById('monthly_hoa_fee')),
            extra_monthly_savings: safeNumber(this.getValueById('extra_monthly_savings')),
            refinance_lender_credit: safeNumber(this.getValueById('refinance_lender_credit')),
            tax_escrow_months: safeNumber(this.getValueById('tax_escrow_months')),
            insurance_escrow_months: safeNumber(this.getValueById('insurance_escrow_months')),
            new_discount_points: safeNumber(this.getValueById('new_discount_points')),
            loan_type: this.getSelectedValue('refinance_loan_type'),
            refinance_type: this.getSelectedValue('refinance_type'),
            zero_cash_to_close: this.getCheckboxValue('zero_cash_to_close'),
        };

        // Only include target_ltv_value if cash_option is 'target_ltv'
        if (cashOption === 'target_ltv') {
            formData.target_ltv_value = safeNumber(this.getValueById('target_ltv_value'));
        }

        // Only include cash_back_amount if cash_option is 'cash_back'
        if (cashOption === 'cash_back') {
            formData.cash_back_amount = safeNumber(this.getValueById('cash_back_amount'));
        }

        return formData;
    }

    /**
     * Validate purchase form data
     * @param {Object} formData - Form data to validate
     * @returns {Array} Array of validation error messages
     */
    validatePurchaseForm(formData) {
        const errors = [];

        // Required field validation
        if (!formData.purchase_price || formData.purchase_price <= 0) {
            errors.push('Purchase price must be greater than 0');
        }

        if (formData.down_payment_percentage < 0 || formData.down_payment_percentage > 100) {
            errors.push('Down payment percentage must be between 0 and 100');
        }

        if (!formData.annual_rate || formData.annual_rate <= 0 || formData.annual_rate > 30) {
            errors.push('Interest rate must be between 0 and 30%');
        }

        if (!formData.loan_term || formData.loan_term < 1 || formData.loan_term > 50) {
            errors.push('Loan term must be between 1 and 50 years');
        }

        // Tax validation based on method
        if (formData.tax_method === 'percentage') {
            if (formData.annual_tax_rate < 0 || formData.annual_tax_rate > 10) {
                errors.push('Property tax rate must be between 0 and 10%');
            }
        } else if (formData.tax_method === 'amount') {
            if (!formData.annual_tax_amount || formData.annual_tax_amount < 0) {
                errors.push('Annual tax amount must be greater than or equal to 0');
            }
        }

        // Insurance validation based on method
        if (formData.insurance_method === 'percentage') {
            if (formData.annual_insurance_rate < 0 || formData.annual_insurance_rate > 5) {
                errors.push('Insurance rate must be between 0 and 5%');
            }
        } else if (formData.insurance_method === 'amount') {
            if (!formData.annual_insurance_amount || formData.annual_insurance_amount < 0) {
                errors.push('Annual insurance amount must be greater than or equal to 0');
            }
        }

        // Business logic validation
        const downPaymentAmount = (formData.purchase_price * formData.down_payment_percentage) / 100;
        const loanAmount = formData.purchase_price - downPaymentAmount;

        if (loanAmount <= 0) {
            errors.push('Loan amount must be greater than 0');
        }

        // VA loan specific validation
        if (formData.loan_type === 'va') {
            if (!formData.va_service_type) {
                errors.push('VA service type is required for VA loans');
            }
            if (!formData.va_usage) {
                errors.push('VA usage type is required for VA loans');
            }
        }

        return errors;
    }

    /**
     * Validate refinance form data
     * @param {Object} formData - Form data to validate
     * @returns {Array} Array of validation error messages
     */
    validateRefinanceForm(formData) {
        const errors = [];

        // Required field validation
        if (!formData.appraised_value || formData.appraised_value <= 0) {
            errors.push('Appraised value must be greater than 0');
        }

        if (!formData.original_loan_balance || formData.original_loan_balance <= 0) {
            errors.push('Original loan balance must be greater than 0');
        }

        if (!formData.original_interest_rate || formData.original_interest_rate <= 0) {
            errors.push('Original interest rate must be greater than 0');
        }

        if (!formData.new_interest_rate || formData.new_interest_rate <= 0) {
            errors.push('New interest rate must be greater than 0');
        }

        if (!formData.annual_taxes || formData.annual_taxes < 0) {
            errors.push('Annual taxes cannot be negative');
        }

        if (!formData.annual_insurance || formData.annual_insurance < 0) {
            errors.push('Annual insurance cannot be negative');
        }

        // Manual balance override validation
        if (formData.use_manual_balance) {
            if (!formData.manual_current_balance || formData.manual_current_balance <= 0) {
                errors.push('Manual current balance must be greater than 0 when override is enabled');
            }
            // Ensure manual balance is not greater than original balance
            if (formData.manual_current_balance > formData.original_loan_balance) {
                errors.push('Manual current balance cannot be greater than original loan balance');
            }
        }

        // Cash option validation
        if (formData.cash_option === 'target_ltv') {
            // Get max LTV based on loan type and refinance type
            const maxLtv = this.getMaxLtvForLoanType(formData.loan_type, formData.refinance_type);

            if (!formData.target_ltv_value || formData.target_ltv_value <= 0) {
                errors.push('Target LTV must be greater than 0%');
            } else if (formData.target_ltv_value > maxLtv) {
                errors.push(`Target LTV cannot exceed ${maxLtv}% for ${formData.loan_type} ${formData.refinance_type} refinance`);
            }
        }

        // Cash back validation
        if (formData.cash_option === 'cash_back') {
            if (!formData.cash_back_amount || formData.cash_back_amount <= 0) {
                errors.push('Cash back amount must be greater than $0');
            } else if (formData.cash_back_amount > 1000000) {
                errors.push('Cash back amount cannot exceed $1,000,000');
            }
        }

        // Extra monthly savings validation
        if (formData.extra_monthly_savings < 0) {
            errors.push('Extra monthly savings cannot be negative');
        }

        // Lender credit validation
        if (formData.refinance_lender_credit < 0) {
            errors.push('Lender credit cannot be negative');
        }

        // Escrow months validation
        if (!formData.tax_escrow_months || formData.tax_escrow_months < 1 || formData.tax_escrow_months > 14) {
            errors.push('Tax escrow months must be between 1 and 14');
        }

        if (!formData.insurance_escrow_months || formData.insurance_escrow_months < 1 || formData.insurance_escrow_months > 14) {
            errors.push('Insurance escrow months must be between 1 and 14');
        }

        // Business logic validation
        if (formData.original_loan_balance > formData.appraised_value * 1.2) {
            errors.push('Original loan balance seems too high compared to appraised value');
        }

        return errors;
    }

    /**
     * Helper method to get value by element ID
     * @param {string} id - Element ID
     * @returns {string} Element value or empty string
     */
    getValueById(id) {
        const element = document.getElementById(id);
        return element ? element.value.trim() : '';
    }

    /**
     * Helper method to get selected value from select element or radio button group
     * @param {string} id - Element ID or name attribute for radio groups
     * @returns {string} Selected value or empty string
     */
    getSelectedValue(id) {
        // First try to find element by ID (for select elements)
        const element = document.getElementById(id);
        if (element) {
            return element.value;
        }

        // If not found by ID, try to find checked radio button by name
        const radioElement = document.querySelector(`input[name="${id}"]:checked`);
        return radioElement ? radioElement.value : '';
    }

    /**
     * Helper method to get checkbox value
     * @param {string} id - Element ID
     * @returns {boolean} Checkbox state
     */
    getCheckboxValue(id) {
        const element = document.getElementById(id);
        return element ? element.checked : false;
    }

    /**
     * Reset form to default values
     * @param {string} mode - 'purchase' or 'refinance'
     */
    resetForm(mode) {
        const form = mode === 'refinance' ? this.refinanceForm : this.purchaseForm;
        if (form) {
            form.reset();
            console.log(`${mode} form reset to defaults`);
        }
    }

    /**
     * Set form field value
     * @param {string} id - Element ID
     * @param {*} value - Value to set
     */
    setFieldValue(id, value) {
        const element = document.getElementById(id);
        if (element) {
            if (element.type === 'checkbox') {
                element.checked = Boolean(value);
            } else {
                element.value = value;
            }
        }
    }

    /**
     * Get maximum LTV for loan type and refinance type combination
     * @param {string} loanType - Loan type (conventional, fha, va, usda)
     * @param {string} refinanceType - Refinance type (rate_term, cash_out, streamline)
     * @returns {number} Maximum LTV percentage
     */
    getMaxLtvForLoanType(loanType, refinanceType) {
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

        return maxLtvLimits[loanType]?.[refinanceType] || 95.0;
    }

    /**
     * Get current form mode based on radio selection
     * @returns {string} 'purchase' or 'refinance'
     */
    getCurrentMode() {
        const purchaseRadio = document.getElementById('mode_purchase');
        return purchaseRadio && purchaseRadio.checked ? 'purchase' : 'refinance';
    }

    /**
     * Initialize form event listeners
     */
    initializeEventListeners() {
        // Add input validation listeners
        this.addInputValidationListeners();

        // Add form submission prevention (handled by calculator)
        if (this.purchaseForm) {
            this.purchaseForm.addEventListener('submit', (e) => e.preventDefault());
        }

        if (this.refinanceForm) {
            this.refinanceForm.addEventListener('submit', (e) => e.preventDefault());
        }
    }

    /**
     * Add real-time input validation listeners
     */
    addInputValidationListeners() {
        // Add listeners for numeric inputs to ensure valid ranges
        const numericInputs = document.querySelectorAll('input[type="number"]');

        numericInputs.forEach(input => {
            input.addEventListener('blur', (e) => {
                this.validateNumericInput(e.target);
            });
        });
    }

    /**
     * Validate individual numeric input
     * @param {HTMLElement} input - Input element to validate
     */
    validateNumericInput(input) {
        const value = parseFloat(input.value);
        const min = parseFloat(input.min);
        const max = parseFloat(input.max);

        if (input.value && (isNaN(value) || (min !== null && value < min) || (max !== null && value > max))) {
            input.classList.add('is-invalid');

            // Create or update error message
            let errorDiv = input.parentElement.querySelector('.invalid-feedback');
            if (!errorDiv) {
                errorDiv = document.createElement('div');
                errorDiv.className = 'invalid-feedback';
                input.parentElement.appendChild(errorDiv);
            }

            if (isNaN(value)) {
                errorDiv.textContent = 'Please enter a valid number';
            } else if (min !== null && value < min) {
                errorDiv.textContent = `Value must be at least ${min}`;
            } else if (max !== null && value > max) {
                errorDiv.textContent = `Value must be no more than ${max}`;
            }
        } else {
            input.classList.remove('is-invalid');
            const errorDiv = input.parentElement.querySelector('.invalid-feedback');
            if (errorDiv) {
                errorDiv.remove();
            }
        }
    }
}

// Export singleton instance
export const formManager = new FormManager();
