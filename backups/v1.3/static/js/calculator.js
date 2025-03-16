// Format a number as currency
function formatCurrency(number) {
    if (typeof number !== 'number') {
        console.error('formatCurrency called with non-number:', number);
        return '$0.00';
    }
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(number);
}

// Format a number as a percentage (e.g., 5.25%)
function formatPercentage(number) {
    if (typeof number !== 'number') {
        console.error('formatPercentage called with non-number:', number);
        return '0.00%';
    }
    
    return number.toFixed(2) + '%';
}

// Safely updates an element with formatted value
function safelyUpdateElement(elementId, value, formatter = (val) => val) {
    const element = document.getElementById(elementId);
    if (element && value !== undefined) {
        try {
            element.textContent = formatter(value);
        } catch (e) {
            console.error(`Error updating ${elementId}:`, e);
        }
    }
}

// Add debug message to debug output area
function addDebug(message) {
    console.log(message);
    const debugElement = document.getElementById('debugOutput');
    if (debugElement) {
        debugElement.style.display = 'block';
        debugElement.textContent += message + "\n";
    }
}

// Update tables with calculation results
function updateClosingCostsTable(costs) {
    const tbody = document.querySelector('#closingCostsTable');
    if (!tbody) {
        console.error('Closing costs table tbody not found');
        return 0;
    }
    
    // Clear previous content
    tbody.innerHTML = '';
    let total = 0;
    
    // Extract the total directly if it exists
    let serverTotal = 0;
    if (typeof costs === 'object' && costs !== null && 'total' in costs && typeof costs.total === 'number') {
        serverTotal = costs.total;
        console.log(`Found closing costs total in response: ${serverTotal}`);
    }
    
    // Process the line items
    if (typeof costs === 'object' && costs !== null) {
        for (const [key, value] of Object.entries(costs)) {
            if (key !== 'total' && typeof value === 'number') {
                // Skip seller_credit and lender_credit as they'll be in the Credits section
                if (key === 'seller_credit' || key === 'lender_credit') {
                    continue;
                }
                
                total += value;
                
                // Format the item name for display
                const itemName = key.replace(/_/g, ' ')
                    .split(' ')
                    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
                    .join(' ');
                
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${itemName}</td>
                    <td>${formatCurrency(value)}</td>
                `;
                tbody.appendChild(row);
            }
        }
    } else if (typeof costs === 'number') {
        total = costs;
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>Total Closing Costs</td>
            <td>${formatCurrency(costs)}</td>
        `;
        tbody.appendChild(row);
    }
    
    // If we couldn't calculate a total but have a server-provided total, use that
    if (total === 0 && serverTotal > 0) {
        total = serverTotal;
    }
    
    // Update the total closing costs element
    const totalClosingCostsElement = document.getElementById('totalClosingCosts');
    if (totalClosingCostsElement) {
        totalClosingCostsElement.textContent = formatCurrency(total);
    }
    
    console.log(`Calculated closing costs total: ${total}`);
    return total;
}

// Updates the prepaids table with the items from the API
function updatePrepaidsTable(prepaids) {
    const tbody = document.querySelector('#prepaidsTable');
    if (!tbody) {
        console.error('Prepaids table tbody not found');
        return 0;
    }
    
    // Clear previous content
    tbody.innerHTML = '';
    let total = 0;
    
    // Extract the total directly if it exists
    let serverTotal = 0;
    if (typeof prepaids === 'object' && prepaids !== null && 'total' in prepaids && typeof prepaids.total === 'number') {
        serverTotal = prepaids.total;
        console.log(`Found prepaids total in response: ${serverTotal}`);
    }
    
    // Process the line items
    if (typeof prepaids === 'object' && prepaids !== null) {
        for (const [key, amount] of Object.entries(prepaids)) {
            if (key !== 'total' && typeof amount === 'number') {
                total += amount;
                
                // Format the item name for display
                const itemName = key.replace(/_/g, ' ')
                    .split(' ')
                    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
                    .join(' ');
                
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${itemName}</td>
                    <td>${formatCurrency(amount)}</td>
                `;
                tbody.appendChild(row);
            }
        }
    } else if (typeof prepaids === 'number') {
        // Handle case where prepaids is just a number
        total = prepaids;
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>Prepaids</td>
            <td>${formatCurrency(prepaids)}</td>
        `;
        tbody.appendChild(row);
    }
    
    // If we couldn't calculate a total but have a server-provided total, use that
    if (total === 0 && serverTotal > 0) {
        total = serverTotal;
    }
    
    // Update the total prepaids element
    const totalPrepaidsElement = document.getElementById('totalPrepaids');
    if (totalPrepaidsElement) {
        totalPrepaidsElement.textContent = formatCurrency(total);
    }
    
    console.log(`Calculated prepaids total: ${total}`);
    return total;
}

// Updates the credits table with seller and lender credits
function updateCreditsTable(result) {
    const tbody = document.querySelector('#creditsTable');
    if (!tbody) {
        console.error('Credits table tbody not found');
        return 0;
    }
    
    // Clear previous content
    tbody.innerHTML = '';
    
    // Get seller and lender credits from the result
    const sellerCredit = result.seller_credit || 0;
    const lenderCredit = result.lender_credit || 0;
    const totalCredits = sellerCredit + lenderCredit;
    
    // Always show these items, even if they're zero
    const sellerCreditRow = document.createElement('tr');
    sellerCreditRow.innerHTML = `
        <td>Seller Paid Closing</td>
        <td>${formatCurrency(sellerCredit)}</td>
    `;
    tbody.appendChild(sellerCreditRow);
    
    const lenderCreditRow = document.createElement('tr');
    lenderCreditRow.innerHTML = `
        <td>Lender Paid Closing</td>
        <td>${formatCurrency(lenderCredit)}</td>
    `;
    tbody.appendChild(lenderCreditRow);
    
    // Update the total credits element
    const totalCreditsElement = document.getElementById('totalCredits');
    if (totalCreditsElement) {
        totalCreditsElement.textContent = formatCurrency(totalCredits);
    }
    
    console.log(`Calculated credits total: ${totalCredits}`);
    return totalCredits;
}

// Updates the total cash needed at closing
function updateTotalCashNeeded(result, downPayment, closingCostsTotal, prepaidsTotal) {
    try {
        let totalCashNeeded = 0;
        
        // If result contains total_cash_needed, use that
        if (result.total_cash_needed !== undefined) {
            totalCashNeeded = result.total_cash_needed;
            console.log(`Using server-provided total cash needed: ${totalCashNeeded}`);
        } else {
            // Otherwise calculate it
            totalCashNeeded = downPayment + closingCostsTotal + prepaidsTotal - (result.seller_credit || 0) - (result.lender_credit || 0);
            console.log(`Calculated total cash needed: ${totalCashNeeded}`);
        }
        
        // Update the UI
        const element = document.getElementById('totalCashNeeded');
        if (element) {
            element.textContent = formatCurrency(totalCashNeeded);
        }
        
        return totalCashNeeded;
    } catch (e) {
        console.error('Error updating total cash needed:', e);
        return 0;
    }
}

// Handle form submission and calculate mortgage details
document.getElementById('mortgageForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    // Show loading spinner, hide results and error
    document.getElementById('loadingSpinner').style.display = 'block';
    document.getElementById('resultsSection').style.display = 'none';
    document.getElementById('errorAlert').style.display = 'none';
    document.getElementById('loadingProgress').style.display = 'block';
    document.getElementById('calculateButton').disabled = true;
    
    // Add debug information
    const debugElement = document.getElementById('debugOutput');
    if (debugElement) {
        debugElement.textContent = '';  // Clear previous debug output
    }

    try {
        // Get form data
        const formData = new FormData(this);
        const formDataObj = Object.fromEntries(formData.entries());
        
        // Convert percentage inputs to decimal
        formDataObj.down_payment_percentage = parseFloat(formDataObj.down_payment_percentage);
        formDataObj.annual_rate = parseFloat(formDataObj.annual_rate);
        formDataObj.annual_tax_rate = parseFloat(formDataObj.annual_tax_rate);
        formDataObj.annual_insurance_rate = parseFloat(formDataObj.annual_insurance_rate);
        
        // Convert numeric inputs
        formDataObj.purchase_price = parseFloat(formDataObj.purchase_price);
        formDataObj.loan_term = parseInt(formDataObj.loan_term);
        formDataObj.monthly_hoa_fee = parseFloat(formDataObj.monthly_hoa_fee || 0);
        formDataObj.discount_points = parseFloat(formDataObj.discount_points || 0);
        formDataObj.seller_credit = parseFloat(formDataObj.seller_credit || 0);
        formDataObj.lender_credit = parseFloat(formDataObj.lender_credit || 0);
        
        // Handle VA loan parameters
        if (formDataObj.loan_type === 'va') {
            // Add VA service type
            formDataObj.va_service_type = document.getElementById('va_service_type').value;
            
            // Add VA loan usage
            formDataObj.va_usage = document.getElementById('va_usage').value;
            
            // Add VA disability exemption
            formDataObj.va_disability_exempt = document.getElementById('va_disability_exempt').checked;
            
            addDebug(`VA Parameters: Service Type=${formDataObj.va_service_type}, Usage=${formDataObj.va_usage}, Disability Exempt=${formDataObj.va_disability_exempt}`);
        }
        
        // Convert to credit score number from dropdown
        const creditScoreMap = {
            'excellent': 760,
            'good': 720,
            'fair': 680,
            'poor': 640,
            'bad': 600,
            'very_bad': 550
        };
        
        formDataObj.credit_score = creditScoreMap[formDataObj.credit_score] || 720;
        
        // Add debug info
        addDebug(`Form data: ${JSON.stringify(formDataObj, null, 2)}`);
        
        // Make API request
        const response = await fetch('/calculate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formDataObj)
        });
        
        // Hide loading spinner
        document.getElementById('loadingSpinner').style.display = 'none';
        document.getElementById('loadingProgress').style.display = 'none';
        document.getElementById('calculateButton').disabled = false;
        
        // Handle response
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        addDebug(`API response: ${JSON.stringify(result, null, 2)}`);
        
        // Display results
        document.getElementById('resultsSection').style.display = 'block';
        
        // Update loan details
        safelyUpdateElement('loanAmount', result.loan_details.loan_amount, formatCurrency);
        safelyUpdateElement('downPaymentAmount', result.loan_details.down_payment, formatCurrency);
        safelyUpdateElement('interestRate', result.loan_details.annual_rate, formatPercentage);
        safelyUpdateElement('loanTerm', result.loan_details.loan_term);
        safelyUpdateElement('LTV', result.loan_details.ltv, formatPercentage);
        
        // Update monthly payment
        safelyUpdateElement('principalInterest', result.monthly_payment.principal_and_interest, formatCurrency);
        safelyUpdateElement('propertyTax', result.monthly_payment.property_tax, formatCurrency);
        safelyUpdateElement('homeInsurance', result.monthly_payment.home_insurance, formatCurrency);
        safelyUpdateElement('mortgageInsurance', result.monthly_payment.mortgage_insurance, formatCurrency);
        safelyUpdateElement('hoaFee', result.monthly_payment.hoa_fee, formatCurrency);
        safelyUpdateElement('totalMonthlyPayment', result.monthly_payment.total, formatCurrency);
        
        // Update closing costs, prepaids, and credits tables
        const downPayment = result.loan_details.down_payment;
        const closingCostsTotal = updateClosingCostsTable(result.closing_costs);
        const prepaidsTotal = updatePrepaidsTable(result.prepaid_items);
        const creditsTotal = updateCreditsTable(result);
        
        // Calculate and display total cash needed
        updateTotalCashNeeded(result, downPayment, closingCostsTotal, prepaidsTotal);
        
        // Show all results cards
        document.getElementById('loanDetailsCard').style.display = 'block';
        document.getElementById('monthlyPaymentCard').style.display = 'block';
        document.getElementById('closingCostsCard').style.display = 'block';
        
    } catch (error) {
        console.error('Calculation error:', error);
        
        // Hide loading spinner and results, show error
        document.getElementById('loadingSpinner').style.display = 'none';
        document.getElementById('loadingProgress').style.display = 'none';
        document.getElementById('calculateButton').disabled = false;
        document.getElementById('resultsSection').style.display = 'none';
        
        const errorAlert = document.getElementById('errorAlert');
        errorAlert.textContent = `Error: ${error.message || 'Failed to calculate mortgage details.'}`;
        errorAlert.style.display = 'block';
    }
});

// Show/hide VA options based on loan type selection
document.getElementById('loan_type').addEventListener('change', function() {
    const vaOptions = document.getElementById('vaOptions');
    if (this.value === 'va') {
        vaOptions.style.display = 'block';
    } else {
        vaOptions.style.display = 'none';
    }
});
