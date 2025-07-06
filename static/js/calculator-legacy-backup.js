import { updateClosingCostsTable, updateCreditsTable, updatePrepaidsTable } from './ui/tableUpdaters.js';
import { formatCurrency, formatLabel, formatPercentage, safelyUpdateElement, safeNumber } from './utils/formatting.js';

// Main document ready handler
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing UI');
    
    // Get important elements once
    const mortgageForm = document.getElementById('mortgageForm');
    const refinanceForm = document.getElementById('refinanceForm');
    const purchaseRadio = document.getElementById('mode_purchase');
    const refinanceRadio = document.getElementById('mode_refinance');
    const calculateBtn = document.getElementById('calculateBtn');
    const refinanceCalculateBtn = document.getElementById('refinanceCalculateBtn');
    const errorAlert = document.getElementById('errorAlert');
    const validationAlert = document.getElementById('validationAlert');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const resultsSection = document.getElementById('resultsSection');
    
    // Set up toggle handlers - DISABLED: Using modular calculator now
    if (false && purchaseRadio && refinanceRadio) {
        const toggleFormVisibility = function() {
            // Get the form sections
            const mortgageFormSection = document.getElementById('mortgageFormSection');
            const refinanceFormSection = document.getElementById('refinanceFormSection');
            
            // Get result cards
            const refinanceResultsCard = document.getElementById('refinanceResultsCard');
            const refinanceClosingCostsCard = document.getElementById('refinanceClosingCostsCard');
            
            // Safely check before modifying styles
            if (purchaseRadio.checked) {
                // Show purchase form, hide refinance form
                if (mortgageFormSection) mortgageFormSection.style.display = 'block';
                if (refinanceFormSection) refinanceFormSection.style.display = 'none';
                
                // Show purchase-only elements (except results, which should only appear after calculation)
                document.querySelectorAll('.purchase-only:not(.results-card)').forEach(el => {
                    el.style.display = 'block';
                });
                
                // Hide refinance-only elements including results
                document.querySelectorAll('.refinance-only').forEach(el => {
                    el.style.display = 'none';
                });
                
                // Hide refinance-specific result cards explicitly
                if (refinanceResultsCard) {
                    refinanceResultsCard.style.display = 'none';
                    refinanceResultsCard.classList.add('d-none');
                }
                
                // Hide refinance closing costs details card
                if (refinanceClosingCostsCard) {
                    refinanceClosingCostsCard.style.display = 'none';
                    refinanceClosingCostsCard.classList.add('d-none');
                }
            } else {
                // Show refinance form, hide purchase form
                if (mortgageFormSection) mortgageFormSection.style.display = 'none';
                if (refinanceFormSection) refinanceFormSection.style.display = 'block';
                
                // Show refinance-only elements (except results, which should only appear after calculation)
                document.querySelectorAll('.refinance-only:not(.results-card)').forEach(el => {
                    el.style.display = 'block';
                });
                
                // Hide purchase-only elements including results cards
                document.querySelectorAll('.purchase-only, .results-card:not(.refinance-only)').forEach(el => {
                    el.style.display = 'none';
                });
            }
            
            console.log('Form visibility toggled successfully');
        };
        
        // Initialize form visibility
        toggleFormVisibility();
        
        // Add event handlers for toggle
        purchaseRadio.addEventListener('change', toggleFormVisibility);
        refinanceRadio.addEventListener('change', toggleFormVisibility);
    }
    
    // Set up click handler for calculate buttons
    if (calculateBtn) {
        calculateBtn.addEventListener('click', function(e) {
            submitForm('purchase');
        });
        console.log("Added click handler to purchase button");
    }
    
    if (refinanceCalculateBtn) {
        refinanceCalculateBtn.addEventListener('click', function(e) {
            submitForm('refinance');
        });
        console.log("Added click handler to refinance button");
    }
    
    const refinanceZeroCashBtn = document.getElementById('refinanceZeroCashBtn');
    if (refinanceZeroCashBtn) {
        refinanceZeroCashBtn.addEventListener('click', function(e) {
            submitForm('refinance_zero_cash');
        });
        console.log("Added click handler to refinance zero cash button");
    }
    
    // Form submission function
    function submitForm(mode) {
        console.log(`Handling ${mode} calculation`);
        
        // Hide error messages, results, and reset styles
        errorAlert.classList.add('d-none');
        errorAlert.style.display = 'none';
        validationAlert.classList.add('d-none');
        resultsSection.classList.add('d-none');
        resultsSection.style.display = 'none';
        
        // Show loading spinner
        loadingSpinner.classList.remove('d-none');
        
        // Determine which form to use
        const form = mode.includes('refinance') ? refinanceForm : mortgageForm;
        console.log(`Using ${mode} form:`, form);
        
        if (!form) {
            console.error(`Form not found for mode: ${mode}`);
            loadingSpinner.classList.add('d-none');
            return;
        }
        
        // Collect form data
        const formData = new FormData(form);
        const jsonData = {};
        
        // Convert FormData to JSON
        for (const [key, value] of formData.entries()) {
            jsonData[key] = value;
        }
        
        // Add CSRF token if available
        const csrfToken = document.querySelector('meta[name="csrf-token"]');
        if (csrfToken) {
            jsonData.csrf_token = csrfToken.getAttribute('content');
        }
        
        // Special handling for refinance mode
        if (mode.includes('refinance')) {
            console.log('Processing refinance form data');
            
            // For refinance, we're using a simplified approach where closing costs and new loan amount
            // are calculated automatically by the backend based on the original loan information
            const originalBalance = parseFloat(jsonData.original_loan_balance) || 0;
            
            // Validate original loan balance
            if (originalBalance <= 0) {
                loadingSpinner.classList.add('d-none');
                validationAlert.textContent = "Original loan balance is required for refinance";
                validationAlert.classList.remove('d-none');
                return;
            }
            
            // Remove closing costs fields from the data as they're no longer needed
            delete jsonData.closing_costs;
            delete jsonData.total_closing_costs;
            delete jsonData.new_loan_amount;
            
            console.log('Sending refinance data to server with automatic closing costs calculation:', jsonData);
        }
        
        console.log('Form data ready:', jsonData);
        
        // Handle zero cash mode
        let actualMode = mode;
        let zeroCashMode = false;
        if (mode === 'refinance_zero_cash') {
            actualMode = 'refinance';
            zeroCashMode = true;
            jsonData.zero_cash_to_close = true;
        }
        
        // Add transaction_type explicitly to the data
        jsonData.transaction_type = actualMode;
        console.log(`Setting transaction_type: ${actualMode}, zero_cash_mode: ${zeroCashMode}`);
        
        // API endpoint based on mode
        const endpoint = actualMode === 'refinance' ? '/refinance' : '/calculate';
        console.log(`Submitting to: ${endpoint}`);
        
        // Submit the data
        fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': jsonData.csrf_token || ''
            },
            body: JSON.stringify(jsonData)
        })
        .then(response => {
            console.log(`Response status: ${response.status} from endpoint ${endpoint}`);
            if (!response.ok) {
                return response.text().then(text => {
                    console.error(`Error response from ${endpoint}:`, text);
                    try {
                        return JSON.parse(text);
                    } catch (e) {
                        throw new Error(`Server error: ${text}`);
                    }
                });
            }
            return response.json();
        })
        .then(data => {
            console.log('Received data:', data);
            loadingSpinner.classList.add('d-none');
            
            // Check if there's an error in the response
            if (data.error) {
                console.error('API returned error:', data.error);
                
                // Hide results section and show error
                resultsSection.classList.add('d-none');
                resultsSection.style.display = 'none';
                
                // Show error alert
                errorAlert.textContent = data.error || 'An error occurred during calculation';
                errorAlert.classList.remove('d-none');
                errorAlert.style.display = 'block';
                return;
            }
            
            // For refinance mode, also check for errors within the result object
            if (actualMode === 'refinance' && data.result && data.result.error) {
                console.error('Refinance validation error:', data.result.error);
                console.log('Error alert element:', errorAlert);
                
                // Hide results section and show error
                resultsSection.classList.add('d-none');
                resultsSection.style.display = 'none';
                
                // Show error alert
                errorAlert.textContent = data.result.error;
                errorAlert.classList.remove('d-none');
                errorAlert.style.display = 'block'; // Force display
                console.log('Error alert classes after show:', errorAlert.className);
                console.log('Error alert style after show:', errorAlert.style.display);
                return;
            }
            
            // If we get here, the response was successful
            
            // Show results section
            resultsSection.classList.remove('d-none');
            resultsSection.style.display = 'block';
            
            // Update UI based on mode
            if (actualMode === 'refinance') {
                // For refinance, data may be wrapped in result or directly at root
                updateRefinanceResults(data.result || data);
            } else {
                // For purchase, data is directly at the root level
                updatePurchaseResults(data);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            loadingSpinner.classList.add('d-none');
            errorAlert.textContent = error.message || 'An error occurred';
            errorAlert.classList.remove('d-none');
        });
    }

    // Function to update refinance results
    function updateRefinanceResults(result) {
        console.log('Updating refinance results:', result);
        
        // Update LTV information card with actual current balance from calculation
        if (result.current_balance && typeof window.updateLtvInformationCard === 'function') {
            window.updateLtvInformationCard(result.current_balance);
        }
    // Helper function to safely update DOM elements
    function updateElement(id, value, formatter = null) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = formatter ? formatter(value) : value;
        }
    }
    
    // Show the refinance results card
    const refinanceResultsCard = document.getElementById('refinanceResultsCard');
    if (refinanceResultsCard) {
        refinanceResultsCard.style.display = 'block';
        refinanceResultsCard.classList.remove('d-none');
    } else {
        console.error('refinanceResultsCard element not found');
    }
    
    // Update basic refinance results
    updateElement('currentBalance', result.current_balance, window.formatLoanAmount || formatCurrency);
    updateElement('newLoanAmount', result.new_loan_amount, window.formatLoanAmount || formatCurrency);
    updateElement('refinance_new_loan_amount', result.new_loan_amount, window.formatLoanAmount || formatCurrency);
    updateElement('refinanceLTV', result.ltv, (val) => val + '%');
    updateElement('newMonthlyPayment', result.new_monthly_payment, formatCurrency);
    updateElement('oldMonthlyPayment', result.original_monthly_payment, formatCurrency);
    updateElement('monthlySavings', result.monthly_savings, formatCurrency);
    updateElement('breakEvenPoint', result.break_even_time);
    updateElement('totalSavings', result.total_savings, formatCurrency);

    // Add loan increase explanation if available
    const loanIncreaseElement = document.getElementById('loanIncrease');
    if (loanIncreaseElement && result.loan_increase) {
        loanIncreaseElement.textContent = formatCurrency(result.loan_increase);
        // Show the loan increase section
        const loanIncreaseSection = document.getElementById('loanIncreaseSection');
        if (loanIncreaseSection) {
            loanIncreaseSection.classList.remove('d-none');
        }
    }

    // Add financed closing costs explanation if available
    const financedClosingCostsElement = document.getElementById('financedClosingCosts');
    if (financedClosingCostsElement && result.financed_closing_costs) {
        financedClosingCostsElement.textContent = formatCurrency(result.financed_closing_costs);
        // Show the financed closing costs section
        const financedClosingCostsSection = document.getElementById('financedClosingCostsSection');
        if (financedClosingCostsSection) {
            financedClosingCostsSection.classList.remove('d-none');
        }
    }
    
    // Log the values we're updating for debugging
    console.log('Updating UI with these values:', {
        currentBalance: result.current_balance,
        newLoanAmount: result.new_loan_amount,
        ltv: result.ltv,
        newMonthlyPayment: result.new_monthly_payment,
        oldMonthlyPayment: result.original_monthly_payment,
        monthlySavings: result.monthly_savings
    });
    
    // Update and show the refinance closing costs details card
    if (result.closing_costs_details) {
        console.log('Found closing costs details in result:', result.closing_costs_details);
        
        // Use a simpler approach without dynamic imports
        // Create a direct reference to the updateRefinanceClosingCostsTable function
        const updateTableFn = window.updateRefinanceClosingCostsTable;
        
        if (typeof updateTableFn === 'function') {
            console.log('Calling updateRefinanceClosingCostsTable function');
            updateTableFn(result);
            
            // Show the refinance closing costs details card
            const refinanceClosingCostsCard = document.getElementById('refinanceClosingCostsCard');
            if (refinanceClosingCostsCard) {
                console.log('Found refinanceClosingCostsCard element, showing it');
                refinanceClosingCostsCard.style.display = 'block';
                refinanceClosingCostsCard.classList.remove('d-none');
            } else {
                console.error('refinanceClosingCostsCard element not found');
            }
        } else {
            console.error('updateRefinanceClosingCostsTable function not found in global scope');
            // Fallback: Create a simple table directly
            const tbody = document.getElementById('refinanceClosingCostsTable');
            if (tbody) {
                console.log('Creating simple table directly');
                tbody.innerHTML = '';
                
                // Skip these keys when rendering
                const skipKeys = ['total', 'financed_closing_costs', 'financed_amount', 'cash_to_close'];
                
                // Add each line item to the table
                for (const key in result.closing_costs_details) {
                    if (!skipKeys.includes(key)) {
                        const value = result.closing_costs_details[key];
                        if (value !== 0) {
                            // Convert snake_case to Title Case for display
                            const displayName = key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
                            
                            const row = document.createElement('tr');
                            row.innerHTML = `
                                <td>${displayName}</td>
                                <td class="text-end">${formatCurrency(value)}</td>
                            `;
                            tbody.appendChild(row);
                        }
                    }
                }
                
                // Show the card
                const card = document.getElementById('refinanceClosingCostsCard');
                if (card) {
                    card.style.display = 'block';
                    card.classList.remove('d-none');
                }
            } else {
                console.error('refinanceClosingCostsTable element not found');
            }
        }
    } else {
        console.warn('No closing_costs_details found in result');
    }

    // Update Monthly Payment Breakdown card
    if (result.monthly_breakdown) {
        console.log('Updating refinance monthly payment breakdown:', result.monthly_breakdown);
        
        updateElement('refinancePrincipalAndInterest', result.monthly_breakdown.principal_interest, formatCurrency);
        updateElement('refinancePropertyTax', result.monthly_breakdown.property_tax, formatCurrency);
        updateElement('refinanceHomeInsurance', result.monthly_breakdown.insurance, formatCurrency);
        updateElement('refinancePmi', result.monthly_breakdown.pmi, formatCurrency);
        updateElement('refinanceHoaFee', result.monthly_breakdown.hoa, formatCurrency);
        updateElement('refinanceTotalMonthlyPayment', result.monthly_breakdown.total, formatCurrency);
        updateElement('refinanceTotalMonthlyPaymentFooter', result.monthly_breakdown.total, formatCurrency);
        
        // Show the monthly payment card
        const monthlyPaymentCard = document.getElementById('refinanceMonthlyPaymentCard');
        if (monthlyPaymentCard) {
            monthlyPaymentCard.style.display = 'block';
            monthlyPaymentCard.classList.remove('d-none');
        }
    }

    // Update Prepaids card
    if (result.prepaid_items) {
        console.log('Updating refinance prepaids:', result.prepaid_items);
        
        const prepaidsTable = document.getElementById('refinancePrepaidsTable');
        if (prepaidsTable) {
            prepaidsTable.innerHTML = '';
            
            // Define order and labels for prepaids
            const prepaidOrder = [
                { key: 'prepaid_insurance', label: 'Homeowner\'s Insurance Premium (1 Year)' },
                { key: 'prepaid_tax', label: 'Property Taxes (Months)' },
                { key: 'prepaid_interest', label: 'Per Diem Interest' },
                { key: 'insurance_escrow', label: 'Homeowner\'s Insurance Escrow' },
                { key: 'tax_escrow', label: 'Property Tax Escrow' },
                { key: 'tax_escrow_adjustment', label: 'Seller Tax Proration Credit' },
                { key: 'borrower_escrow_credit', label: 'Borrower Escrow Payment Credit' }
            ];
            
            prepaidOrder.forEach(item => {
                if (result.prepaid_items.hasOwnProperty(item.key)) {
                    const value = parseFloat(result.prepaid_items[item.key]);
                    if (!isNaN(value) && value !== 0) {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td>${item.label}</td>
                            <td class="text-end">${formatCurrency(value)}</td>
                        `;
                        prepaidsTable.appendChild(row);
                    }
                }
            });
            
            updateElement('refinanceTotalPrepaids', result.prepaid_items.total, formatCurrency);
            
            // Show the prepaids card
            const prepaidsCard = document.getElementById('refinancePrepaidsCard');
            if (prepaidsCard) {
                prepaidsCard.style.display = 'block';
                prepaidsCard.classList.remove('d-none');
            }
        }
    }

    // Update Credits card
    if (result.credits) {
        console.log('Updating refinance credits:', result.credits);
        
        const creditsTable = document.getElementById('refinanceCreditsTable');
        if (creditsTable) {
            creditsTable.innerHTML = '';
            
            // Add credit rows
            if (result.credits.seller_credit > 0) {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>Seller Credit</td>
                    <td class="text-end">${formatCurrency(result.credits.seller_credit)}</td>
                `;
                creditsTable.appendChild(row);
            }
            
            if (result.credits.lender_credit > 0) {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>Lender Credit</td>
                    <td class="text-end">${formatCurrency(result.credits.lender_credit)}</td>
                `;
                creditsTable.appendChild(row);
            }
            
            // If no credits, show a "No credits" row
            if (result.credits.total === 0) {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td colspan="2" style="font-style: italic;">No credits applied</td>
                `;
                creditsTable.appendChild(row);
            }
            
            updateElement('refinanceTotalCredits', result.credits.total, formatCurrency);
            
            // Show the credits card
            const creditsCard = document.getElementById('refinanceCreditsCard');
            if (creditsCard) {
                creditsCard.style.display = 'block';
                creditsCard.classList.remove('d-none');
            }
        }
    }

    // Update Cash to Close card
    console.log('Updating refinance cash to close:', result.cash_to_close);
    console.log('Zero cash mode:', result.zero_cash_mode);
    
    updateElement('refinanceCashToClose', result.cash_to_close, formatCurrency);
    updateElement('refinanceTotalClosingCostsSummary', result.total_closing_costs, formatCurrency);
    updateElement('refinanceTotalPrepaidsSummary', result.prepaid_items ? result.prepaid_items.total : 0, formatCurrency);
    updateElement('refinanceAmountFinanced', result.financed_closing_costs, formatCurrency);
    updateElement('refinanceTotalCreditsSummary', result.credits ? result.credits.total : 0, formatCurrency);
    updateElement('refinanceFinalCashToClose', result.cash_to_close, formatCurrency);
    
    // Add special messaging for zero cash mode
    const cashToCloseCard = document.getElementById('refinanceCashToCloseCard');
    if (cashToCloseCard) {
        const cardBody = cashToCloseCard.querySelector('.card-body');
        if (result.zero_cash_mode) {
            // Add zero cash message
            const existingAlert = cardBody.querySelector('.zero-cash-alert');
            if (!existingAlert) {
                const zeroCashAlert = document.createElement('div');
                zeroCashAlert.className = 'alert alert-success zero-cash-alert mb-3';
                zeroCashAlert.innerHTML = '<i class="bi bi-check-circle"></i> <strong>Zero Cash to Close:</strong> All closing costs and prepaids have been added to your loan amount.';
                cardBody.insertBefore(zeroCashAlert, cardBody.firstChild);
            }
        } else {
            // Remove zero cash message if it exists
            const existingAlert = cardBody.querySelector('.zero-cash-alert');
            if (existingAlert) {
                existingAlert.remove();
            }
        }
        
        cashToCloseCard.style.display = 'block';
        cashToCloseCard.classList.remove('d-none');
    }
}

// Function to update purchase results
function updatePurchaseResults(result) {
    console.log('Updating purchase results:', result);
    
    // Helper function to safely update DOM elements
    function updateElement(id, value, formatter = null) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = formatter ? formatter(value) : value;
        } else {
            console.warn(`Element not found: ${id}`);
        }
    }
    
    // Create mobile summary if on mobile device
    if (window.isMobile && window.createMobileResultsSummary) {
        const mobileSummary = window.createMobileResultsSummary(result);
        const summaryContainer = document.getElementById('mobileResultsSummary');
        if (summaryContainer && mobileSummary) {
            summaryContainer.innerHTML = mobileSummary;
        }
    }

    // Update loan details section
    if (result.loan_details) {
        updateElement('loanAmount', result.loan_details.loan_amount, window.formatLoanAmount || formatCurrency);
        updateElement('loanType', result.loan_details.loan_type);
        updateElement('interestRate', result.loan_details.interest_rate, formatPercentage);
        updateElement('loanTerm', result.loan_details.loan_term);
        // Update down payment in the cash needed section
        updateElement('downPayment', result.loan_details.down_payment, formatCurrency);
        
        // Update max seller contribution message
        if (result.loan_details.max_seller_contribution !== undefined) {
            const maxContribElement = document.getElementById('maxSellerContribution');
            if (maxContribElement) {
                const maxAmount = formatCurrency(result.loan_details.max_seller_contribution);
                const loanType = result.loan_details.loan_type || 'this loan type';
                
                if (result.loan_details.seller_credit_exceeds_max) {
                    maxContribElement.textContent = `⚠️ Seller credit exceeds maximum! Max allowed for ${loanType}: ${maxAmount}`;
                    maxContribElement.className = 'form-text text-danger'; // Red warning
                } else {
                    maxContribElement.textContent = `Maximum seller contribution for ${loanType}: ${maxAmount}`;
                    maxContribElement.className = 'form-text text-success'; // Green success
                }
            }
        }
    }
    
    // Update monthly payment breakdown with responsive formatting
    const currencyFormatter = window.formatCurrencyResponsive || formatCurrency;
    
    if (result.monthly_breakdown) {
        updateElement('principalAndInterest', result.monthly_breakdown.principal_interest, currencyFormatter);
        updateElement('propertyTax', result.monthly_breakdown.property_tax, currencyFormatter);
        updateElement('homeInsurance', result.monthly_breakdown.home_insurance, currencyFormatter);
        updateElement('pmi', result.monthly_breakdown.mortgage_insurance, currencyFormatter);
        updateElement('hoaFee', result.monthly_breakdown.hoa_fee, currencyFormatter);
        updateElement('totalMonthlyPayment', result.monthly_breakdown.total, currencyFormatter);
    } else if (result.monthly_payment) {
        // Fallback for older API response structure
        updateElement('principalAndInterest', result.monthly_payment.principal_and_interest, currencyFormatter);
        updateElement('propertyTax', result.monthly_payment.property_tax, currencyFormatter);
        updateElement('homeInsurance', result.monthly_payment.home_insurance, currencyFormatter);
        updateElement('pmi', result.monthly_payment.mortgage_insurance, currencyFormatter);
        updateElement('hoaFee', result.monthly_payment.hoa_fee, currencyFormatter);
        updateElement('totalMonthlyPayment', result.monthly_payment.total, currencyFormatter);
    }
    
    // Update Closing Costs table
    if (result.closing_costs) {
        updateClosingCostsTable(result.closing_costs, null, result);
    }
    
    // Update Prepaid Items table
    if (result.prepaids) {
        updatePrepaidsTable(result.prepaids);
    } else if (result.prepaid_items) {
        // Fallback for older API response structure
        updatePrepaidsTable(result.prepaid_items);
    }
    
    // Update Credits table
    if (result.credits) {
        updateCreditsTable(result);
    }
    
    // Show the main result cards
    const monthlyPaymentCard = document.getElementById('monthlyPaymentCard');
    const closingCostsCard = document.getElementById('closingCostsCard');
    
    if (monthlyPaymentCard) {
        monthlyPaymentCard.style.display = 'block';
        monthlyPaymentCard.classList.remove('d-none');
    }
    
    if (closingCostsCard) {
        closingCostsCard.style.display = 'block';
        closingCostsCard.classList.remove('d-none');
    }
    
    // Show the cash needed summary
    updateElement('totalCashToClose', result.total_cash_needed, formatCurrency);
    
    console.log('Purchase results UI updated successfully');
}
});
