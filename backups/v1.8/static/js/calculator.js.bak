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
    
    console.log(`Calculated credits total: ${totalCredits} (seller=${sellerCredit}, lender=${lenderCredit})`);
    return totalCredits;
}

function updateTotalCashNeeded(result, downPayment, closingCostsTotal, prepaidsTotal) {
    const totalCashNeededElement = document.getElementById('totalCashNeeded');
    if (!totalCashNeededElement) {
        console.error('Total cash needed element not found');
        return;
    }
    
    // Get credits from seller and lender
    const sellerCredit = result.seller_credit || 0;
    const lenderCredit = result.lender_credit || 0;
    const totalCredits = sellerCredit + lenderCredit;
    
    // First priority: Use server-provided total if available
    if (result && result.total_cash_needed && typeof result.total_cash_needed === 'number') {
        console.log(`Using server-provided total cash needed: ${result.total_cash_needed}`);
        totalCashNeededElement.textContent = formatCurrency(result.total_cash_needed);
        return result.total_cash_needed;
    }
    
    // Second priority: Calculate from components
    const total = downPayment + closingCostsTotal + prepaidsTotal - totalCredits;
    totalCashNeededElement.textContent = formatCurrency(total);
    
    console.log(`Calculated total cash needed: ${total} (down=${downPayment}, closing=${closingCostsTotal}, prepaids=${prepaidsTotal}, credits=${totalCredits})`);
    return total;
}

// Handle form submission and calculate mortgage details
document.getElementById('mortgageForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    // Show loading spinner, hide results and error
    document.getElementById('loadingSpinner').style.display = 'block';
    document.getElementById('errorMessage').style.display = 'none';
    // Intentionally don't hide results yet to avoid flickering
    
    let debugOutput = "";
    const addDebugLocal = (message) => {
        console.log(message);
        debugOutput += message + "\n";
        const debugElement = document.getElementById('debugOutput');
        if (debugElement) {
            debugElement.textContent = debugOutput;
        }
    };
    
    try {
        // Get form data
        const formData = new FormData(this);
        const formDataObj = Object.fromEntries(formData.entries());
        
        // Add current date if closing date is not specified
        if (!formDataObj.closing_date || formDataObj.closing_date === '') {
            const today = new Date();
            const yyyy = today.getFullYear();
            let mm = today.getMonth() + 1;
            let dd = today.getDate();
            
            if (dd < 10) dd = '0' + dd;
            if (mm < 10) mm = '0' + mm;
            
            formDataObj.closing_date = `${yyyy}-${mm}-${dd}`;
            addDebugLocal(`Using current date for closing: ${formDataObj.closing_date}`);
        }
        
        addDebugLocal('Submitting form data to calculate endpoint...');
        
        // Send data to backend
        const response = await fetch('/calculate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formDataObj)
        });
        
        // Handle response
        if (!response.ok) {
            throw new Error(`Server responded with ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        addDebugLocal('Received response from server');
        
        if (!result.success) {
            throw new Error(result.error || 'Unknown calculation error');
        }
        
        // Hide loading spinner
        document.getElementById('loadingSpinner').style.display = 'none';
        
        // Show results sections
        document.getElementById('resultsSection').style.display = 'block';
        document.getElementById('closingCostsCard').style.display = 'block';
        
        // Update monthly payment summary
        safelyUpdateElement('monthlyPayment', result.monthly_payment, formatCurrency);
        safelyUpdateElement('totalMonthlyPayment', result.monthly_payment, formatCurrency);
        
        // Update monthly payment breakdown
        safelyUpdateElement('monthlyPrincipalInterest', result.monthly_mortgage, formatCurrency);
        safelyUpdateElement('monthlyPropertyTax', result.monthly_tax, formatCurrency);
        safelyUpdateElement('monthlyInsurance', result.monthly_insurance, formatCurrency);
        safelyUpdateElement('monthlyPMI', result.monthly_pmi, formatCurrency);
        safelyUpdateElement('monthlyHOA', result.monthly_hoa, formatCurrency);
        
        addDebugLocal('Updated monthly payment breakdown');
        
        // Update loan details
        if (result.loan_details) {
            safelyUpdateElement('purchasePrice', result.loan_details.purchase_price, formatCurrency);
            safelyUpdateElement('baseLoanAmount', result.loan_details.loan_amount, formatCurrency);
            safelyUpdateElement('downPaymentAmount', result.loan_details.down_payment, formatCurrency);
            safelyUpdateElement('downPaymentPercentage', result.loan_details.down_payment_percentage, formatPercentage);
            safelyUpdateElement('interestRate', result.loan_details.interest_rate, formatPercentage);
            safelyUpdateElement('loanTermYears', `${result.loan_details.loan_term} years`);
            safelyUpdateElement('loanTypeDisplay', result.loan_details.loan_type.charAt(0).toUpperCase() + result.loan_details.loan_type.slice(1));
            safelyUpdateElement('loanToValue', result.loan_details.ltv, formatPercentage);
        }
        
        addDebugLocal('Updated loan details');
        
        // Update closing costs and prepaids sections
        const closingCostsTotal = updateClosingCostsTable(result.closing_costs || {});
        const prepaidsTotal = updatePrepaidsTable(result.prepaids || {});
        const creditsTotal = updateCreditsTable(result);
        
        addDebugLocal('Updated closing costs table');
        addDebugLocal('Updated prepaids table');
        
        // Update the down payment in the cash needed section
        safelyUpdateElement('downPayment', result.down_payment, formatCurrency);
        
        // Update total closing costs in the cash needed section
        if (result.closing_costs && typeof result.closing_costs.total === 'number') {
            safelyUpdateElement('totalClosingCosts', result.closing_costs.total, formatCurrency);
        }
        
        // Update total prepaids in the cash needed section
        if (result.prepaids && typeof result.prepaids.total === 'number') {
            safelyUpdateElement('totalPrepaids', result.prepaids.total, formatCurrency);
        }
        
        // Update total cash needed - use server provided total if available
        const downPayment = result.down_payment || 0;
        updateTotalCashNeeded(result, downPayment, closingCostsTotal, prepaidsTotal);
        
        // Show the closing costs card
        document.getElementById('closingCostsCard').style.display = 'block';
        
    } catch (error) {
        console.error('Calculation error:', error);
        
        // Hide loading spinner and results, show error
        document.getElementById('loadingSpinner').style.display = 'none';
        document.getElementById('resultsSection').style.display = 'none';
        const errorElement = document.getElementById('errorMessage');
        errorElement.style.display = 'block';
        
        const errorTextElement = document.getElementById('errorText');
        if (errorTextElement) {
            errorTextElement.textContent = error.message || 'An unexpected error occurred.';
        }
    }
});

// Show/hide VA options based on loan type selection
document.getElementById('loan_type').addEventListener('change', function() {
    const vaOptions = document.getElementById('vaOptions');
    if (this.value === 'va') {
        vaOptions.style.display = 'flex';
    } else {
        vaOptions.style.display = 'none';
    }
});
