document.addEventListener('DOMContentLoaded', function() {
    const mortgageForm = document.getElementById('mortgageForm');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const errorAlert = document.getElementById('errorAlert');
    const resultsCards = document.querySelectorAll('.results-card');
    const loanTypeSelect = document.getElementById('loan_type');
    const vaOptions = document.querySelector('.va-options');
    const calculateBtn = document.getElementById('calculateBtn');
    const debugOutput = document.getElementById('debugOutput');
    let isCalculating = false;
    
    // Format number as currency
    function formatCurrency(number) {
        if (typeof number !== 'number') {
            console.error('Invalid currency value:', number);
            return '$0.00';
        }
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(number);
    }
    
    // Format number as percentage
    function formatPercentage(number) {
        return new Intl.NumberFormat('en-US', {
            style: 'percent',
            minimumFractionDigits: 3,
            maximumFractionDigits: 3
        }).format(number / 100);
    }
    
    // Set default closing date to today if not already set
    const closingDateInput = document.getElementById('closing_date');
    if (closingDateInput && !closingDateInput.value) {
        const today = new Date();
        const yyyy = today.getFullYear();
        let mm = today.getMonth() + 1; // Months start at 0!
        let dd = today.getDate();

        // Add leading zeros if needed
        if (dd < 10) dd = '0' + dd;
        if (mm < 10) mm = '0' + mm;

        closingDateInput.value = `${yyyy}-${mm}-${dd}`;
        console.log('Set default closing date to today:', closingDateInput.value);
    }
    
    // Function to update insurance label based on loan type
    function updateInsuranceLabel(loanType) {
        const insuranceLabel = document.getElementById('insuranceLabel');
        
        if (!insuranceLabel) return;
        
        switch(loanType.toLowerCase()) {
            case 'conventional':
                insuranceLabel.textContent = 'PMI';
                break;
            case 'fha':
                insuranceLabel.textContent = 'MIP';
                break;
            case 'va':
                insuranceLabel.textContent = 'Funding Fee';
                break;
            case 'usda':
                insuranceLabel.textContent = 'Guarantee Fee';
                break;
            default:
                insuranceLabel.textContent = 'Mortgage Insurance';
        }
    }

    // Loan type change handler
    document.getElementById('loan_type').addEventListener('change', function() {
        updateInsuranceLabel(this.value);
        vaOptions.style.display = this.value === 'va' ? 'block' : 'none';
    });
    
    // Initialize insurance label based on default loan type
    document.addEventListener('DOMContentLoaded', function() {
        const loanTypeSelect = document.getElementById('loan_type');
        if (loanTypeSelect) {
            updateInsuranceLabel(loanTypeSelect.value);
        }
    });
    
    // Debug logging
    function logToDebug(message) {
        console.log(message);
        if (debugOutput) {
            const logLine = document.createElement('div');
            logLine.textContent = message;
            debugOutput.appendChild(logLine);
            debugOutput.scrollTop = debugOutput.scrollHeight;
        }
    }
    
    mortgageForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        logToDebug('Starting calculation...');
        if (isCalculating) {
            logToDebug('Calculation already in progress, ignoring duplicate request');
            return;
        }
        
        // Clear previous results and errors
        errorAlert.style.display = 'none';
        resultsCards.forEach(card => card.style.display = 'none');
        isCalculating = true;
        calculateBtn.disabled = true;
        
        // Show loading spinner
        loadingSpinner.style.display = 'block';
        loadingSpinner.classList.remove('d-none');
        
        // Get form data
        const formData = new FormData(mortgageForm);
        
        // Required fields with their display names
        const requiredFields = {
            'purchase_price': 'Purchase Price',
            'down_payment_percentage': 'Down Payment Percentage',
            'annual_rate': 'Annual Rate',
            'loan_term': 'Loan Term',
            'annual_tax_rate': 'Annual Tax Rate',
            'annual_insurance_rate': 'Annual Insurance Rate',
            'monthly_hoa_fee': 'Monthly HOA Fee',
            'loan_type': 'Loan Type',
            'discount_points': 'Discount Points'
        };
        
        logToDebug('Validation started...');
        // Check for missing required fields
        for (const [field, label] of Object.entries(requiredFields)) {
            const value = formData.get(field);
            if (!value && value !== '0') {
                errorAlert.textContent = `${label} is required`;
                errorAlert.style.display = 'block';
                loadingSpinner.style.display = 'none';
                isCalculating = false;
                calculateBtn.disabled = false;
                return;
            }
        }
        
        logToDebug('Validation passed, preparing data...');
        // Format numeric fields
        const numericFields = [
            'purchase_price',
            'down_payment_percentage',
            'annual_rate',
            'loan_term',
            'annual_tax_rate',
            'annual_insurance_rate',
            'monthly_hoa_fee',
            'seller_credit',
            'lender_credit',
            'discount_points'
        ];
        
        for (const field of numericFields) {
            const value = formData.get(field);
            if (value) {
                formData.set(field, parseFloat(value).toString());
            }
        }
        
        // Ensure interest rate and points have 3 decimal places
        const annualRate = formData.get('annual_rate');
        if (annualRate) {
            formData.set('annual_rate', parseFloat(annualRate).toFixed(3));
        }
        
        const discountPoints = formData.get('discount_points');
        if (discountPoints) {
            formData.set('discount_points', parseFloat(discountPoints).toFixed(3));
        }
        
        // Ensure closing date is correctly formatted and included
        const closingDateInput = document.getElementById('closing_date');
        if (closingDateInput) {
            const closingDateValue = closingDateInput.value;
            logToDebug(`Closing date from input field: "${closingDateValue}"`);
            if (closingDateValue) {
                formData.set('closing_date', closingDateValue);
                logToDebug(`Added closing_date to form data: ${closingDateValue}`);
            } else {
                // If no date is set, use today's date
                const today = new Date();
                const yyyy = today.getFullYear();
                let mm = today.getMonth() + 1; // Months start at 0!
                let dd = today.getDate();
                
                // Add leading zeros if needed
                if (dd < 10) dd = '0' + dd;
                if (mm < 10) mm = '0' + mm;
                
                const todayStr = `${yyyy}-${mm}-${dd}`;
                formData.set('closing_date', todayStr);
                logToDebug(`No closing date found, using today's date: ${todayStr}`);
            }
        }
        
        logToDebug('Data prepared, making API call...');
        // Convert FormData to JSON object
        const jsonData = {};
        formData.forEach((value, key) => {
            // Map form field names to API expected parameter names
            if (key === 'monthly_hoa_fee') {
                jsonData['hoa_fee'] = value;
            } else {
                jsonData[key] = value;
            }
        });
        
        // Debug logging
        logToDebug('Closing date:', jsonData.closing_date);
        logToDebug('Form data being sent to backend:');
        for (const [key, value] of Object.entries(jsonData)) {
            logToDebug(`  ${key}: ${value}`);
            
            // Remove credit_score if it exists in the data
            if (key === 'credit_score') {
                logToDebug('Found credit_score in form data - removing it as it\'s no longer needed');
                delete jsonData['credit_score'];
            }
        }
        
        // Add CSRF token to prevent 403 errors
        let csrfToken;
        try {
            const csrfMeta = document.querySelector('meta[name="csrf-token"]');
            if (!csrfMeta) {
                console.error('CSRF token meta tag not found');
                errorAlert.textContent = 'CSRF token missing. Please refresh the page and try again.';
                errorAlert.style.display = 'block';
                loadingSpinner.style.display = 'none';
                isCalculating = false;
                calculateBtn.disabled = false;
                return;
            }
            csrfToken = csrfMeta.getAttribute('content');
            if (!csrfToken) {
                console.error('CSRF token is empty');
                errorAlert.textContent = 'CSRF token is empty. Please refresh the page and try again.';
                errorAlert.style.display = 'block';
                loadingSpinner.style.display = 'none';
                isCalculating = false;
                calculateBtn.disabled = false;
                return;
            }
        } catch (error) {
            console.error('Error retrieving CSRF token:', error);
            errorAlert.textContent = 'Failed to retrieve CSRF token. Please refresh the page.';
            errorAlert.style.display = 'block';
            loadingSpinner.style.display = 'none';
            isCalculating = false;
            calculateBtn.disabled = false;
            return;
        }
        
        // Make API call
        fetch('/calculate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRF-Token': csrfToken
            },
            body: JSON.stringify(jsonData),
            credentials: 'same-origin' // Include cookies for CSRF validation
        })
        .then(response => {
            logToDebug('API response received...');
            // Always stop the loading spinner
            loadingSpinner.style.display = 'none';
            isCalculating = false;
            calculateBtn.disabled = false;
            
            // Check if content type is JSON
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                console.error('Non-JSON response received:', contentType);
                logToDebug('Error: Non-JSON response received: ' + contentType);
                errorAlert.textContent = 'Server returned an invalid response format. Please try again later.';
                errorAlert.style.display = 'block';
                throw new Error('Non-JSON response from server');
            }
            
            if (!response.ok) {
                // Handle HTTP errors
                return response.json().then(errorData => {
                    console.error('API error:', errorData);
                    logToDebug('API error: ' + JSON.stringify(errorData));
                    errorAlert.textContent = errorData.error || 'An error occurred during calculation';
                    errorAlert.style.display = 'block';
                    
                    // Log detailed error information if available
                    if (errorData.details) {
                        logToDebug('Error details: ' + JSON.stringify(errorData.details));
                        console.error('Error details:', errorData.details);
                    }
                    if (errorData.traceback) {
                        logToDebug('Error traceback: ' + errorData.traceback);
                        console.error('Error traceback:', errorData.traceback);
                    }
                    
                    throw new Error(errorData.error || 'API Error');
                });
            }
            return response.json();
        })
        .then(data => {
            logToDebug('API response processed: ' + JSON.stringify(data, null, 2));
            // Process successful response
            if (data.success) {
                errorAlert.style.display = 'none';
                // Fix: The result data is directly in the data object - extract required properties
                const result = {
                    monthly_breakdown: {
                        principal_interest: data.monthly_breakdown.principal_interest,
                        property_tax: data.monthly_breakdown.property_tax || data.monthly_tax,
                        insurance: data.monthly_breakdown.insurance || data.monthly_insurance,
                        hoa: data.monthly_breakdown.hoa || data.monthly_hoa,
                        pmi: data.monthly_breakdown.pmi || data.monthly_pmi || data.monthly_breakdown.mortgage_insurance
                    },
                    loan_details: data.loan_details,
                    closing_costs: data.closing_costs,
                    prepaid_items: data.prepaids,
                    total_cash_needed: data.total_cash_needed
                };
                updateResults(result);
            } else {
                // Handle business logic errors
                logToDebug('Calculation error: ' + JSON.stringify(data.error));
                console.error('Calculation error:', data.error);
                errorAlert.textContent = data.error || 'An error occurred during calculation';
                errorAlert.style.display = 'block';
            }
        })
        .catch(error => {
            logToDebug('Error during calculation: ' + error.message);
            console.error('Error during calculation:', error);
            errorAlert.textContent = 'An error occurred: ' + error.message;
            errorAlert.style.display = 'block';
            loadingSpinner.style.display = 'none';
            isCalculating = false;
            calculateBtn.disabled = false;
        });
    });
    
    // Update results in the UI
    function updateResults(result) {
        try {
            logToDebug('Updating results with: ' + JSON.stringify(result, null, 2));
            
            if (!result || typeof result !== 'object') {
                throw new Error('Invalid result data');
            }
            
            const { monthly_breakdown, loan_details, closing_costs, prepaid_items, total_cash_needed } = result;
            
            // More detailed validation with specific error messages
            if (!monthly_breakdown) throw new Error('Missing monthly breakdown data');
            if (!loan_details) throw new Error('Missing loan details data');
            if (!closing_costs) throw new Error('Missing closing costs data');
            if (!prepaid_items) throw new Error('Missing prepaid items data');
            
            // Update the insurance label based on the selected loan type
            const loanTypeSelect = document.getElementById('loan_type');
            if (loanTypeSelect) {
                updateInsuranceLabel(loanTypeSelect.value);
            }
            
            // Loan Details
            document.getElementById('purchasePrice').textContent = formatCurrency(loan_details.purchase_price || 0);
            document.getElementById('downPaymentAmount').textContent = formatCurrency(loan_details.down_payment || 0);
            
            // Calculate base loan amount
            const baseLoanAmount = (loan_details.purchase_price || 0) - (loan_details.down_payment || 0);
            document.getElementById('baseLoanAmount').textContent = formatCurrency(baseLoanAmount);
            
            // Handle upfront MIP for FHA loans
            const upfrontMipRow = document.getElementById('upfrontMipRow');
            const upfrontMip = (loan_details.loan_amount || 0) - baseLoanAmount;
            
            // Display upfront MIP row only for FHA loans
            if (document.getElementById('loan_type').value === 'fha' && upfrontMip > 0) {
                upfrontMipRow.style.display = 'table-row';
                document.getElementById('upfrontMip').textContent = formatCurrency(upfrontMip);
            } else {
                upfrontMipRow.style.display = 'none';
            }
            
            document.getElementById('loanAmount').textContent = formatCurrency(loan_details.loan_amount || 0);
            document.getElementById('interestRate').textContent = (loan_details.annual_rate || 0) + '%';
            document.getElementById('loanTermDisplay').textContent = (loan_details.loan_term || 0) + ' years';
            document.getElementById('ltvDisplay').textContent = (loan_details.ltv || 0) + '%';
            
            // Monthly Payment Breakdown
            document.getElementById('monthlyPayment').textContent = formatCurrency(monthly_breakdown.principal_interest || 0);
            document.getElementById('monthlyTax').textContent = formatCurrency(monthly_breakdown.property_tax || 0);
            document.getElementById('monthlyInsurance').textContent = formatCurrency(monthly_breakdown.insurance || 0);
            document.getElementById('monthlyHoa').textContent = formatCurrency(monthly_breakdown.hoa || 0);
            document.getElementById('monthlyPmi').textContent = formatCurrency(monthly_breakdown.pmi || 0);
            
            // Calculate and display total monthly payment
            let totalMonthly = 0;
            if (monthly_breakdown) {
                totalMonthly = (monthly_breakdown.principal_interest || 0) +
                              (monthly_breakdown.property_tax || 0) +
                              (monthly_breakdown.insurance || 0) +
                              (monthly_breakdown.hoa || 0) +
                              (monthly_breakdown.pmi || 0);
            }
            document.getElementById('totalMonthlyPayment').textContent = formatCurrency(totalMonthly);
            
            // Down payment amount is already set in loan details section, don't duplicate
            document.getElementById('downPayment').textContent = formatCurrency(loan_details.down_payment || 0);
            
            // Closing Costs
            const closingCostsTable = document.getElementById('closingCostsTable');
            closingCostsTable.innerHTML = ''; // Clear existing rows
            
            // Add closing costs
            Object.entries(closing_costs).forEach(([name, amount]) => {
                if (name !== 'total' && amount !== undefined) {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</td>
                        <td class="text-end">${formatCurrency(amount)}</td>
                    `;
                    closingCostsTable.appendChild(row);
                }
            });
            
            // Add prepaid items
            const prepaidsTable = document.getElementById('prepaidsTable');
            prepaidsTable.innerHTML = ''; // Clear existing rows
            
            Object.entries(prepaid_items).forEach(([name, amount]) => {
                if (name !== 'total' && amount !== undefined) {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</td>
                        <td class="text-end">${formatCurrency(amount)}</td>
                    `;
                    prepaidsTable.appendChild(row);
                }
            });
            
            // Display totals
            document.getElementById('totalClosingCosts').textContent = formatCurrency(closing_costs.total || 0);
            document.getElementById('totalPrepaids').textContent = formatCurrency(prepaid_items.total || 0);
            document.getElementById('totalCashNeeded').textContent = formatCurrency(total_cash_needed || 0);
            
            // Show results cards
            resultsCards.forEach(card => card.style.display = 'block');
            
            logToDebug('Results successfully updated');
            
        } catch (error) {
            logToDebug('Error updating results: ' + error.message);
            console.error('Error updating results:', error);
            console.error('Result data:', result);
            errorAlert.textContent = 'Error displaying results. Please try again.';
            errorAlert.style.display = 'block';
            resultsCards.forEach(card => card.style.display = 'none');
        }
    }
    
    // Function to initialize form fields - restores the correct configuration
    function initializeFormFields() {
        logToDebug('Initializing form fields with correct configuration...');
        
        // Ensure credit score field is removed if it exists
        const creditScoreField = document.getElementById('credit_score');
        if (creditScoreField) {
            logToDebug('Found credit score field - removing it as it\'s not needed');
            creditScoreField.parentElement.parentElement.remove();
        }
        
        // Ensure closing date field is visible
        const closingDateField = document.getElementById('closing_date');
        if (closingDateField) {
            const closingDateContainer = closingDateField.parentElement.parentElement;
            closingDateContainer.style.display = 'block';
            logToDebug('Ensuring closing date field is visible');
            
            // Set default closing date to today if not already set
            if (!closingDateField.value) {
                const today = new Date();
                const yyyy = today.getFullYear();
                let mm = today.getMonth() + 1; // Months start at 0!
                let dd = today.getDate();

                // Add leading zeros if needed
                if (dd < 10) dd = '0' + dd;
                if (mm < 10) mm = '0' + mm;

                closingDateField.value = `${yyyy}-${mm}-${dd}`;
                logToDebug('Set default closing date to today: ' + closingDateField.value);
            }
        } else {
            logToDebug('WARNING: Closing date field not found in the form!');
        }
    }

    // Call the initialization function when the page loads
    document.addEventListener('DOMContentLoaded', function() {
        logToDebug('DOM loaded, initializing form fields...');
        initializeFormFields();
        
        // Also add a loan type change handler to ensure fields are correct when loan type changes
        const loanTypeSelect = document.getElementById('loan_type');
        if (loanTypeSelect) {
            loanTypeSelect.addEventListener('change', function() {
                initializeFormFields();
            });
        }
    });
});
