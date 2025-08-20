/**
 * Calculator utilities for API communication
 */

class Calculator {
    constructor() {
        this.lastResult = null;
        this.init();
    }

    init() {
        // Set up form event listeners
        this.setupFormHandlers();
        
        // Load last calculation if available
        this.loadLastCalculation();
    }

    setupFormHandlers() {
        const purchaseForm = document.getElementById('purchaseForm');
        const refinanceForm = document.getElementById('refinanceForm');

        if (purchaseForm) {
            purchaseForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.calculatePurchase();
            });
        }

        if (refinanceForm) {
            refinanceForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.calculateRefinance();
            });
        }

        // Set up radio button handlers for tax and insurance methods
        this.setupTaxInsuranceHandlers();

        // Add real-time calculation on input change (debounced)
        this.setupRealtimeCalculation();
    }

    setupTaxInsuranceHandlers() {
        // Property Tax radio buttons
        const taxPercentage = document.getElementById('tax_percentage');
        const taxAmount = document.getElementById('tax_amount');
        const taxRateInput = document.getElementById('annual_tax_rate');
        const taxAmountInput = document.getElementById('annual_tax_amount');

        if (taxPercentage && taxAmount) {
            taxPercentage.addEventListener('change', () => {
                if (taxPercentage.checked) {
                    taxRateInput.disabled = false;
                    taxAmountInput.disabled = true;
                    taxAmountInput.value = 0;
                }
            });

            taxAmount.addEventListener('change', () => {
                if (taxAmount.checked) {
                    taxRateInput.disabled = true;
                    taxAmountInput.disabled = false;
                    taxRateInput.value = 0;
                }
            });
        }

        // Insurance radio buttons
        const insurancePercentage = document.getElementById('insurance_percentage');
        const insuranceAmount = document.getElementById('insurance_amount');
        const insuranceRateInput = document.getElementById('annual_insurance_rate');
        const insuranceAmountInput = document.getElementById('annual_insurance_amount');

        if (insurancePercentage && insuranceAmount) {
            insurancePercentage.addEventListener('change', () => {
                if (insurancePercentage.checked) {
                    insuranceRateInput.disabled = false;
                    insuranceAmountInput.disabled = true;
                    insuranceAmountInput.value = 0;
                }
            });

            insuranceAmount.addEventListener('change', () => {
                if (insuranceAmount.checked) {
                    insuranceRateInput.disabled = true;
                    insuranceAmountInput.disabled = false;
                    insuranceRateInput.value = 0;
                }
            });
        }
    }

    setupRealtimeCalculation() {
        let timeout;
        const inputs = document.querySelectorAll('input[type="number"], select');
        
        inputs.forEach(input => {
            input.addEventListener('input', () => {
                clearTimeout(timeout);
                timeout = setTimeout(() => {
                    // Auto-calculate if form is valid
                    const activeTab = document.querySelector('.tab-pane.active');
                    if (activeTab && activeTab.id === 'purchase') {
                        this.calculatePurchase(true); // Silent calculation
                    } else if (activeTab && activeTab.id === 'refinance') {
                        this.calculateRefinance(true); // Silent calculation
                    }
                }, 1000); // 1 second delay
            });
        });
    }

    async calculatePurchase(silent = false) {
        if (!silent) {
            this.showLoading();
        }

        try {
            const formData = this.getPurchaseFormData();
            
            if (!this.validatePurchaseData(formData)) {
                if (!silent) this.hideLoading();
                return;
            }

            const response = await this.makeCalculationRequest('/api/calculate', formData);
            
            if (response.success) {
                this.lastResult = response.result;
                this.saveLastCalculation();
                this.displayResults(response.result, 'purchase');
                
                if (!silent) {
                    this.showSuccess('Calculation completed successfully!');
                }
            } else {
                throw new Error(response.error || 'Calculation failed');
            }
        } catch (error) {
            console.error('Purchase calculation error:', error);
            if (!silent) {
                this.showError(`Calculation failed: ${error.message}`);
            }
        } finally {
            if (!silent) {
                this.hideLoading();
            }
        }
    }

    async calculateRefinance(silent = false) {
        if (!silent) {
            this.showLoading();
        }

        try {
            const formData = this.getRefinanceFormData();
            
            if (!this.validateRefinanceData(formData)) {
                if (!silent) this.hideLoading();
                return;
            }

            const response = await this.makeCalculationRequest('/api/refinance', formData);
            
            if (response.success) {
                this.lastResult = response.result;
                this.saveLastCalculation();
                this.displayResults(response.result, 'refinance');
                
                if (!silent) {
                    this.showSuccess('Refinance calculation completed!');
                }
            } else {
                throw new Error(response.error || 'Refinance calculation failed');
            }
        } catch (error) {
            console.error('Refinance calculation error:', error);
            if (!silent) {
                this.showError(`Refinance calculation failed: ${error.message}`);
            }
        } finally {
            if (!silent) {
                this.hideLoading();
            }
        }
    }

    async makeCalculationRequest(endpoint, data) {
        const url = getApiUrl(endpoint);
        
        let response;
        if (authManager.isAuthenticated) {
            // Use authenticated API call
            response = await authManager.apiCall(url, {
                method: 'POST',
                body: JSON.stringify(data)
            });
        } else {
            // Use anonymous API call
            response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
        }

        if (!response.ok) {
            throw new Error(`API error: ${response.status} ${response.statusText}`);
        }

        return await response.json();
    }

    getPurchaseFormData() {
        const purchasePrice = parseFloat(document.getElementById('purchase_price').value);
        
        // Handle tax method (percentage or dollar amount)
        let taxRate = 0;
        const taxMethodPercentage = document.getElementById('tax_percentage');
        if (taxMethodPercentage && taxMethodPercentage.checked) {
            taxRate = parseFloat(document.getElementById('annual_tax_rate').value);
        } else {
            // Convert dollar amount to percentage
            const taxAmount = parseFloat(document.getElementById('annual_tax_amount').value || 0);
            taxRate = purchasePrice > 0 ? (taxAmount / purchasePrice) * 100 : 0;
        }
        
        // Handle insurance method (percentage or dollar amount)
        let insuranceRate = 0;
        const insuranceMethodPercentage = document.getElementById('insurance_percentage');
        if (insuranceMethodPercentage && insuranceMethodPercentage.checked) {
            insuranceRate = parseFloat(document.getElementById('annual_insurance_rate').value);
        } else {
            // Convert dollar amount to percentage
            const insuranceAmount = parseFloat(document.getElementById('annual_insurance_amount').value || 0);
            insuranceRate = purchasePrice > 0 ? (insuranceAmount / purchasePrice) * 100 : 0;
        }

        return {
            purchase_price: purchasePrice,
            down_payment_percentage: parseFloat(document.getElementById('down_payment_percentage').value),
            annual_rate: parseFloat(document.getElementById('annual_rate').value),
            loan_term: parseInt(document.getElementById('loan_term').value),
            loan_type: document.getElementById('loan_type').value,
            annual_tax_rate: taxRate,
            annual_insurance_rate: insuranceRate,
            monthly_hoa_fee: parseFloat(document.getElementById('monthly_hoa_fee').value || 0),
            seller_credit: parseFloat(document.getElementById('seller_credit').value || 0),
            lender_credit: parseFloat(document.getElementById('lender_credit').value || 0),
            discount_points: parseFloat(document.getElementById('discount_points').value || 0)
        };
    }

    getRefinanceFormData() {
        return {
            home_value: parseFloat(document.getElementById('home_value').value),
            current_loan_balance: parseFloat(document.getElementById('current_loan_balance').value),
            new_interest_rate: parseFloat(document.getElementById('new_interest_rate').value),
            new_loan_term: parseInt(document.getElementById('new_loan_term').value),
            loan_type: document.getElementById('refi_loan_type').value,
            cash_out_amount: parseFloat(document.getElementById('cash_out_amount').value || 0),
            annual_tax_rate: parseFloat(document.getElementById('annual_tax_rate').value),
            annual_insurance_rate: parseFloat(document.getElementById('annual_insurance_rate').value),
            monthly_hoa_fee: parseFloat(document.getElementById('monthly_hoa_fee').value || 0)
        };
    }

    validatePurchaseData(data) {
        if (data.purchase_price <= 0) {
            this.showError('Purchase price must be greater than 0');
            return false;
        }
        if (data.down_payment_percentage < 0 || data.down_payment_percentage > 100) {
            this.showError('Down payment percentage must be between 0 and 100');
            return false;
        }
        if (data.annual_rate <= 0 || data.annual_rate > 20) {
            this.showError('Interest rate must be between 0 and 20%');
            return false;
        }
        return true;
    }

    validateRefinanceData(data) {
        if (data.home_value <= 0) {
            this.showError('Home value must be greater than 0');
            return false;
        }
        if (data.current_loan_balance < 0) {
            this.showError('Current loan balance cannot be negative');
            return false;
        }
        if (data.new_interest_rate <= 0 || data.new_interest_rate > 20) {
            this.showError('Interest rate must be between 0 and 20%');
            return false;
        }
        return true;
    }

    displayResults(result, calculationType) {
        const resultsCard = document.getElementById('resultsCard');
        const resultsContent = document.getElementById('resultsContent');

        if (!resultsCard || !resultsContent) return;

        // Show results card
        resultsCard.style.display = 'block';

        // Format and display results
        let html = '';
        
        if (calculationType === 'purchase') {
            html = this.formatPurchaseResults(result);
        } else if (calculationType === 'refinance') {
            html = this.formatRefinanceResults(result);
        }

        resultsContent.innerHTML = html;

        // Scroll to results on mobile
        if (window.innerWidth < 768) {
            resultsCard.scrollIntoView({ behavior: 'smooth' });
        }
    }

    formatPurchaseResults(result) {
        const monthly = result.monthly_payment || {};
        const summary = result.loan_summary || {};
        const costs = result.closing_costs || {};

        return `
            <div class="mb-3">
                <h6 class="text-success"><i class="bi bi-calculator"></i> Monthly Payment</h6>
                <div class="fs-4 fw-bold text-success">
                    $${this.formatCurrency(monthly.total_payment)}
                </div>
                <small class="text-muted">Principal & Interest: $${this.formatCurrency(monthly.principal_and_interest)}</small>
            </div>

            <div class="mb-3">
                <h6><i class="bi bi-list-ul"></i> Payment Breakdown</h6>
                <div class="row g-2 small">
                    <div class="col-6">Principal & Interest:</div>
                    <div class="col-6 text-end">$${this.formatCurrency(monthly.principal_and_interest)}</div>
                    
                    <div class="col-6">Property Tax:</div>
                    <div class="col-6 text-end">$${this.formatCurrency(monthly.property_tax)}</div>
                    
                    <div class="col-6">Insurance:</div>
                    <div class="col-6 text-end">$${this.formatCurrency(monthly.homeowners_insurance)}</div>
                    
                    ${monthly.pmi ? `
                    <div class="col-6">PMI:</div>
                    <div class="col-6 text-end">$${this.formatCurrency(monthly.pmi)}</div>
                    ` : ''}
                    
                    ${monthly.hoa_fee > 0 ? `
                    <div class="col-6">HOA:</div>
                    <div class="col-6 text-end">$${this.formatCurrency(monthly.hoa_fee)}</div>
                    ` : ''}
                </div>
            </div>

            <div class="mb-3">
                <h6><i class="bi bi-info-circle"></i> Loan Details</h6>
                <div class="small">
                    <strong>Loan Amount:</strong> $${this.formatCurrency(summary.loan_amount)}<br>
                    <strong>Down Payment:</strong> $${this.formatCurrency(summary.down_payment)}<br>
                    <strong>Interest Rate:</strong> ${summary.interest_rate}%<br>
                    <strong>Loan Term:</strong> ${summary.loan_term} years
                </div>
            </div>

            ${costs.total_closing_costs ? `
            <div class="mb-3">
                <h6><i class="bi bi-cash-stack"></i> Closing Costs</h6>
                <div class="fw-bold">
                    Total: $${this.formatCurrency(costs.total_closing_costs)}
                </div>
                <small class="text-muted">
                    Cash needed at closing: $${this.formatCurrency(costs.cash_to_close)}
                </small>
            </div>
            ` : ''}

            ${authManager.isAuthenticated ? `
            <div class="alert alert-info small">
                <i class="bi bi-person-check"></i> Using your personalized settings
            </div>
            ` : `
            <div class="alert alert-warning small">
                <i class="bi bi-exclamation-triangle"></i> 
                <a href="login.html" class="alert-link">Login</a> for personalized calculations
            </div>
            `}
        `;
    }

    formatRefinanceResults(result) {
        const monthly = result.new_monthly_payment || {};
        const summary = result.refinance_summary || {};
        const savings = result.monthly_savings || 0;

        return `
            <div class="mb-3">
                <h6 class="text-success"><i class="bi bi-arrow-repeat"></i> New Monthly Payment</h6>
                <div class="fs-4 fw-bold text-success">
                    $${this.formatCurrency(monthly.total_payment)}
                </div>
                ${savings > 0 ? `
                <div class="text-success small">
                    <i class="bi bi-arrow-down"></i> Save $${this.formatCurrency(savings)}/month
                </div>
                ` : savings < 0 ? `
                <div class="text-warning small">
                    <i class="bi bi-arrow-up"></i> Increase $${this.formatCurrency(Math.abs(savings))}/month
                </div>
                ` : ''}
            </div>

            <div class="mb-3">
                <h6><i class="bi bi-list-ul"></i> Payment Breakdown</h6>
                <div class="row g-2 small">
                    <div class="col-6">Principal & Interest:</div>
                    <div class="col-6 text-end">$${this.formatCurrency(monthly.principal_and_interest)}</div>
                    
                    <div class="col-6">Property Tax:</div>
                    <div class="col-6 text-end">$${this.formatCurrency(monthly.property_tax)}</div>
                    
                    <div class="col-6">Insurance:</div>
                    <div class="col-6 text-end">$${this.formatCurrency(monthly.homeowners_insurance)}</div>
                    
                    ${monthly.pmi ? `
                    <div class="col-6">PMI:</div>
                    <div class="col-6 text-end">$${this.formatCurrency(monthly.pmi)}</div>
                    ` : ''}
                </div>
            </div>

            <div class="mb-3">
                <h6><i class="bi bi-info-circle"></i> Refinance Details</h6>
                <div class="small">
                    <strong>New Loan Amount:</strong> $${this.formatCurrency(summary.new_loan_amount)}<br>
                    <strong>Current Balance:</strong> $${this.formatCurrency(summary.current_balance)}<br>
                    <strong>New Rate:</strong> ${summary.new_interest_rate}%<br>
                    <strong>New Term:</strong> ${summary.new_loan_term} years<br>
                    ${summary.cash_out_amount > 0 ? `<strong>Cash Out:</strong> $${this.formatCurrency(summary.cash_out_amount)}<br>` : ''}
                    <strong>LTV:</strong> ${summary.ltv_ratio}%
                </div>
            </div>

            ${authManager.isAuthenticated ? `
            <div class="alert alert-info small">
                <i class="bi bi-person-check"></i> Using your personalized settings
            </div>
            ` : `
            <div class="alert alert-warning small">
                <i class="bi bi-exclamation-triangle"></i> 
                <a href="login.html" class="alert-link">Login</a> for personalized calculations
            </div>
            `}
        `;
    }

    formatCurrency(amount) {
        if (typeof amount !== 'number' || isNaN(amount)) return '0';
        return amount.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
    }

    saveLastCalculation() {
        try {
            const calculationData = {
                result: this.lastResult,
                timestamp: new Date().toISOString()
            };
            localStorage.setItem(APP_CONFIG.STORAGE_KEYS.LAST_CALCULATION, JSON.stringify(calculationData));
        } catch (error) {
            console.error('Error saving calculation:', error);
        }
    }

    loadLastCalculation() {
        try {
            const saved = localStorage.getItem(APP_CONFIG.STORAGE_KEYS.LAST_CALCULATION);
            if (saved) {
                const data = JSON.parse(saved);
                // Only load if it's from today
                const savedDate = new Date(data.timestamp);
                const today = new Date();
                if (savedDate.toDateString() === today.toDateString()) {
                    this.lastResult = data.result;
                    // Optionally display the saved result
                }
            }
        } catch (error) {
            console.error('Error loading last calculation:', error);
        }
    }

    showLoading() {
        const submitButtons = document.querySelectorAll('button[type="submit"]');
        submitButtons.forEach(btn => {
            btn.disabled = true;
            btn.innerHTML = '<i class="bi bi-hourglass-split"></i> Calculating...';
        });
    }

    hideLoading() {
        const purchaseBtn = document.querySelector('#purchase button[type="submit"]');
        const refinanceBtn = document.querySelector('#refinance button[type="submit"]');
        
        if (purchaseBtn) {
            purchaseBtn.disabled = false;
            purchaseBtn.innerHTML = '<i class="bi bi-calculator"></i> Calculate Payment';
        }
        
        if (refinanceBtn) {
            refinanceBtn.disabled = false;
            refinanceBtn.innerHTML = '<i class="bi bi-arrow-repeat"></i> Calculate Refinance';
        }
    }

    showSuccess(message) {
        this.showAlert(message, 'success');
    }

    showError(message) {
        this.showAlert(message, 'danger');
    }

    showAlert(message, type) {
        // Create alert element
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        alert.style.cssText = 'top: 20px; right: 20px; z-index: 9999; max-width: 400px;';
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(alert);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (alert.parentNode) {
                alert.remove();
            }
        }, 5000);
    }
}

// Initialize calculator when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.calculator = new Calculator();
});