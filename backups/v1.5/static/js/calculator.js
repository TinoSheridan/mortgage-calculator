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
    } else {
        console.error(`Element with id ${elementId} not found or value is undefined`);
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
                total += value;
                
                // Format the item name for display
                const itemName = key.replace(/_/g, ' ')
                    .split(' ')
                    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
                    .join(' ');
                
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td style="font-weight: normal;">${itemName}</td>
                    <td style="font-weight: normal;">${formatCurrency(value)}</td>
                `;
                tbody.appendChild(row);
            }
        }
    } else if (typeof costs === 'number') {
        total = costs;
        const row = document.createElement('tr');
        row.innerHTML = `
            <td style="font-weight: normal;">Total Closing Costs</td>
            <td style="font-weight: normal;">${formatCurrency(costs)}</td>
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
                    <td style="font-weight: normal;">${itemName}</td>
                    <td style="font-weight: normal;">${formatCurrency(amount)}</td>
                `;
                tbody.appendChild(row);
            }
        }
    } else if (typeof prepaids === 'number') {
        // Handle case where prepaids is just a number
        total = prepaids;
        const row = document.createElement('tr');
        row.innerHTML = `
            <td style="font-weight: normal;">Prepaids</td>
            <td style="font-weight: normal;">${formatCurrency(prepaids)}</td>
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

// Updates the credits table (seller and lender credits)
function updateCreditsTable(result) {
    console.log("Starting credit table update...");
    
    // Find the credits table body
    const tbody = document.querySelector('#creditsTable');
    if (!tbody) {
        console.error('Credits table tbody not found! Check HTML for element with id="creditsTable"');
        return 0;
    }
    
    console.log("Credits table found:", tbody);
    
    // Clear previous content
    tbody.innerHTML = '';
    console.log("Cleared previous table content");
    
    // Get seller and lender credits from the credits object in the result
    let sellerCredit = 0;
    let lenderCredit = 0;
    
    // Debug the result structure
    console.log("Full API result:", result);
    
    if (result.credits && typeof result.credits === 'object') {
        sellerCredit = parseFloat(result.credits.seller_credit) || 0;
        lenderCredit = parseFloat(result.credits.lender_credit) || 0;
        console.log("Found credits in result.credits:", result.credits);
    } else {
        console.log("No credits object found in result, checking other locations");
        
        // Alternative locations to check
        if (result.closing_costs && typeof result.closing_costs === 'object') {
            if ('seller_credit' in result.closing_costs) {
                sellerCredit = parseFloat(result.closing_costs.seller_credit) || 0;
                console.log("Found seller credit in closing_costs:", sellerCredit);
            }
            if ('lender_credit' in result.closing_costs) {
                lenderCredit = parseFloat(result.closing_costs.lender_credit) || 0;
                console.log("Found lender credit in closing_costs:", lenderCredit);
            }
        }
        
        // Last resort - try form input values
        if (sellerCredit === 0) {
            const sellerCreditInput = document.getElementById('seller_credit');
            if (sellerCreditInput) {
                sellerCredit = parseFloat(sellerCreditInput.value) || 0;
                console.log("Using seller credit from form input:", sellerCredit);
            }
        }
        
        if (lenderCredit === 0) {
            const lenderCreditInput = document.getElementById('lender_credit');
            if (lenderCreditInput) {
                lenderCredit = parseFloat(lenderCreditInput.value) || 0;
                console.log("Using lender credit from form input:", lenderCredit);
            }
        }
    }
    
    const totalCredits = sellerCredit + lenderCredit;
    console.log(`Credits - Seller: ${sellerCredit}, Lender: ${lenderCredit}, Total: ${totalCredits}`);
    
    // Always add seller credit row, even if zero
    const sellerCreditRow = document.createElement('tr');
    sellerCreditRow.innerHTML = `
        <td style="font-weight: normal;">Seller Credit</td>
        <td style="font-weight: normal;" class="text-end">${formatCurrency(sellerCredit)}</td>
    `;
    tbody.appendChild(sellerCreditRow);
    console.log("Added seller credit row");
    
    // Always add lender credit row, even if zero
    const lenderCreditRow = document.createElement('tr');
    lenderCreditRow.innerHTML = `
        <td style="font-weight: normal;">Lender Credit</td>
        <td style="font-weight: normal;" class="text-end">${formatCurrency(lenderCredit)}</td>
    `;
    tbody.appendChild(lenderCreditRow);
    console.log("Added lender credit row");
    
    // Make sure the total credits element is updated
    const totalCreditsElement = document.getElementById('totalCredits');
    if (totalCreditsElement) {
        totalCreditsElement.textContent = formatCurrency(totalCredits);
        console.log("Updated total credits element:", totalCredits);
    } else {
        console.error("Total credits element not found! Check HTML for element with id='totalCredits'");
    }
    
    return totalCredits;
}

// Updates the total cash needed at closing
function updateTotalCashNeeded(result, downPayment, closingCostsTotal, prepaidsTotal, creditsTotal) {
    try {
        let totalCashNeeded = 0;
        
        // Update the down payment in the Cash Needed at Closing section
        const downPaymentElement = document.getElementById('downPayment');
        if (downPaymentElement) {
            downPaymentElement.textContent = formatCurrency(downPayment);
            console.log(`Updated down payment display: ${downPayment}`);
        } else {
            console.error('Down payment element not found in Cash Needed section');
        }
        
        // If result contains total_cash_needed, use that
        if (result.total_cash_needed !== undefined) {
            totalCashNeeded = result.total_cash_needed;
            console.log(`Using server-provided total cash needed: ${totalCashNeeded}`);
        } else {
            // Otherwise calculate it (subtracting credits from the sum)
            totalCashNeeded = downPayment + closingCostsTotal + prepaidsTotal - creditsTotal;
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
    
    // Clear any previous errors
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
        
        // Handle response
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        addDebug(`API response: ${JSON.stringify(result, null, 2)}`);
        
        // Show results section
        document.getElementById('resultsSection').style.display = 'block';
        
        // Update loan details
        safelyUpdateElement('purchasePrice', result.loan_details.purchase_price, formatCurrency);
        safelyUpdateElement('downPaymentAmount', result.loan_details.down_payment, formatCurrency);
        
        // Format down payment percentage correctly
        if (document.getElementById('downPaymentPercentage')) {
            const downPaymentPercentage = result.loan_details.down_payment_percentage || 
                                         (result.loan_details.down_payment / result.loan_details.purchase_price * 100);
            document.getElementById('downPaymentPercentage').textContent = downPaymentPercentage.toFixed(2) + '%';
        }
        
        safelyUpdateElement('loanAmount', result.loan_details.loan_amount, formatCurrency);
        safelyUpdateElement('interestRate', result.loan_details.annual_rate, formatPercentage);
        
        // Update loan term without bold formatting
        const loanTermElement = document.getElementById('loanTerm');
        if (loanTermElement) {
            loanTermElement.textContent = `${result.loan_details.loan_term} years`;
            loanTermElement.style.fontWeight = 'normal';
        }
        
        safelyUpdateElement('ltv', result.loan_details.ltv, formatPercentage);
        
        // Update monthly payment
        safelyUpdateElement('principalAndInterest', result.monthly_breakdown.principal_interest, formatCurrency);
        safelyUpdateElement('propertyTax', result.monthly_breakdown.property_tax, formatCurrency);
        safelyUpdateElement('homeInsurance', result.monthly_breakdown.home_insurance, formatCurrency);
        safelyUpdateElement('pmi', result.monthly_breakdown.mortgage_insurance, formatCurrency);
        safelyUpdateElement('hoaFee', result.monthly_breakdown.hoa_fee, formatCurrency);
        safelyUpdateElement('totalMonthlyPayment', result.monthly_breakdown.total, formatCurrency);
        
        // Update closing costs, prepaids, and credits tables
        const downPayment = result.loan_details.down_payment;
        const closingCostsTotal = updateClosingCostsTable(result.closing_costs);
        const prepaidsTotal = updatePrepaidsTable(result.prepaids || result.prepaid_items);
        const creditsTotal = updateCreditsTable(result);
        
        // Calculate and display total cash needed
        updateTotalCashNeeded(result, downPayment, closingCostsTotal, prepaidsTotal, creditsTotal);
        
        // Show all results cards - this makes them visible
        const cards = document.querySelectorAll('.results-card');
        cards.forEach(card => {
            card.style.display = 'block';
        });
        
    } catch (error) {
        console.error('Calculation error:', error);
        
        // Hide loading spinner and results, show error
        document.getElementById('loadingSpinner').style.display = 'none';
        document.getElementById('resultsSection').style.display = 'none';
        
        const errorAlert = document.getElementById('errorAlert');
        if (errorAlert) {
            errorAlert.textContent = `Error: ${error.message || 'Failed to calculate mortgage details.'}`;
            errorAlert.style.display = 'block';
        } else {
            console.error('Error alert element not found');
        }
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
