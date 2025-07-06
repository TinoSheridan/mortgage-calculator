// static/js/ui/tableUpdaters.js

// Import necessary utility functions
import { addDebug, formatCurrency } from '../utils/formatting.js'; // Assuming addDebug is still needed here, adjust path if necessary

// Updates the closing costs table with details from the API response
// Returns the calculated total closing costs
export function updateClosingCostsTable(closingCosts, formData, calculationResult) {
    console.log('Updating closing costs table with data:', closingCosts);
    console.log('Form data used for updating closing costs:', formData);
    console.log('Full calculation result:', calculationResult);

    const closingCostsTable = document.getElementById('closingCostsTable');

    // Clear existing table first
    closingCostsTable.innerHTML = '';

    // Get transaction type from API result if available, fallback to form radio button
    let transactionType = calculationResult?.loan_details?.transaction_type?.toLowerCase() || '';
    
    // If transaction type not in API response, use the form's calc_mode radio button
    if (!transactionType) {
        const mode = document.querySelector('input[name="calc_mode"]:checked')?.value || 'purchase';
        transactionType = mode.toLowerCase();
    }
    
    console.log(`Current transaction type: ${transactionType}`);

    // Show correct closing costs based on transaction type
    if (transactionType === 'refinance') {
        console.log('Building refinance-specific closing costs table');

        // For refinance, show specific refinance closing costs
        const refinanceCosts = [
            { name: 'Appraisal Fee', value: closingCosts.appraisal_fee },
            { name: 'Credit Report Fee', value: closingCosts.credit_report_fee },
            { name: 'Processing Fee', value: closingCosts.processing_fee },
            { name: 'Underwriting Fee', value: closingCosts.underwriting_fee },
            { name: 'Title Fees', value: closingCosts.title_fees },
            { name: 'Recording Fee', value: closingCosts.recording_fee },
            { name: 'Other Fees', value: closingCosts.other_fees }
        ];

        // Add each line item to the table
        refinanceCosts.forEach(cost => {
            if (cost.value) {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${cost.name}</td>
                    <td class="text-end">${formatCurrency(cost.value)}</td>
                `;
                closingCostsTable.appendChild(row);
            }
        });

        // Add financed amount row if applicable
        if (closingCosts.financed_amount > 0) {
            const financedRow = document.createElement('tr');
            financedRow.innerHTML = `
                <td><em>Amount Financed Into Loan</em></td>
                <td class="text-end"><em>(${formatCurrency(closingCosts.financed_amount)})</em></td>
            `;
            closingCostsTable.appendChild(financedRow);
        }

        // Update the total cell
        const totalCell = document.getElementById('totalClosingCostsCell');
        if (totalCell) {
            totalCell.innerHTML = `<strong>${formatCurrency(closingCosts.total)}</strong>`;
        }

    } else {
        // This is purchase mode, show all standard closing costs
        if (Object.keys(closingCosts).length > 0) {
            // Skip these keys when rendering
            const skipKeys = ['total', 'financed_closing_costs', 'financed_amount', 'cash_to_close'];

            // Sort the keys for consistent display
            const sortedKeys = Object.keys(closingCosts).sort();

            // Add each line item to the table
            // Define items that should always be shown, even if $0
            const alwaysShowItems = ['origination_fee', 'discount_points'];
            
            for (const key of sortedKeys) {
                if (!skipKeys.includes(key)) {
                    const value = closingCosts[key];
                    // Show item if it has a value > 0 OR if it's in the always-show list
                    if (value !== 0 || alwaysShowItems.includes(key)) {
                        // Convert snake_case to Title Case for display
                        const displayName = key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());

                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td>${displayName}</td>
                            <td class="text-end">${formatCurrency(value)}</td>
                        `;
                        closingCostsTable.appendChild(row);
                    }
                }
            }

            // Update the total cell
            const totalCell = document.getElementById('totalClosingCostsCell');
            if (totalCell) {
                totalCell.innerHTML = `<strong>${formatCurrency(closingCosts.total)}</strong>`;
            }
        }
    }
}

// Updates the prepaids table and returns the total
export function updatePrepaidsTable(prepaids) {
    const tbody = document.querySelector('#prepaidsTable');
    if (!tbody) {
        console.error("Prepaids table body not found!");
        return 0;
    }

    // Ensure prepaids is an object, default to empty if not provided or null
    prepaids = prepaids && typeof prepaids === 'object' ? prepaids : {};

    // Extract the total provided by the server, if available
    const serverTotal = prepaids.total || 0;
    console.log("Found prepaids total in response:", serverTotal);

    tbody.innerHTML = ''; // Clear previous content
    let total = 0;

    // Define order and labels
    const prepaidOrder = [
        { key: 'prepaid_insurance', label: 'Homeowner\'s Insurance Premium (1 Year)' },
        { key: 'prepaid_tax', label: 'Property Taxes (Months)' }, // Label updated dynamically below
        { key: 'prepaid_interest', label: 'Per Diem Interest' },
        { key: 'insurance_escrow', label: 'Homeowner\'s Insurance Escrow' },
        { key: 'tax_escrow', label: 'Property Tax Escrow' },
        { key: 'tax_escrow_adjustment', label: 'Seller Tax Proration Credit' }, // Renamed for clarity
        { key: 'borrower_escrow_credit', label: 'Borrower Escrow Payment Credit' } // Added new credit
    ];

    // Add rows for each defined prepaid item found in the response
    prepaidOrder.forEach(item => {
        // Check if the key exists and its value is not zero (or it's an adjustment/credit which can be zero/negative)
        if (prepaids.hasOwnProperty(item.key) && (prepaids[item.key] !== 0 || item.key === 'tax_escrow_adjustment' || item.key === 'borrower_escrow_credit')) {
            const value = parseFloat(prepaids[item.key]);
            if (!isNaN(value)) {
                let displayLabel = item.label;
                // Dynamically update property tax label if months provided
                if (item.key === 'prepaid_tax' && prepaids.prepaid_tax_months) {
                    displayLabel = `Property Taxes (${prepaids.prepaid_tax_months} Months)`;
                }
                // Dynamically update per diem interest label if days provided
                if (item.key === 'prepaid_interest' && prepaids.interest_days) {
                    displayLabel = `Per Diem Interest (${prepaids.interest_days} Days)`;
                }
                // Dynamically update insurance escrow label if months provided
                if (item.key === 'insurance_escrow' && prepaids.insurance_escrow_months) {
                    displayLabel = `Insurance Escrow (${prepaids.insurance_escrow_months} Months)`;
                }
                // Dynamically update tax escrow label if months provided
                if (item.key === 'tax_escrow' && prepaids.tax_escrow_months) {
                    displayLabel = `Tax Escrow (${prepaids.tax_escrow_months} Months)`;
                }

                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${displayLabel}</td>
                    <td class="text-end">${formatCurrency(value)}</td>
                `;
                tbody.appendChild(row);
                total += value;
            }
        }
    });

    // Update total prepaids element in the tfoot
    const totalPrepaidsElement = document.getElementById('totalPrepaids');
    if (totalPrepaidsElement) {
        totalPrepaidsElement.textContent = formatCurrency(total);
        // Or use innerHTML if you need bold formatting:
        // totalPrepaidsElement.innerHTML = `<strong>${formatCurrency(total)}</strong>`;
    }

    console.log(`Calculated prepaids total: ${total}`);
    return total;
}


// Function to update the refinance closing costs details table
function updateRefinanceClosingCostsTable(result) {
    addDebug("Starting refinance closing costs table update...");
    const tbody = document.getElementById('refinanceClosingCostsTable');
    if (!tbody) {
        console.error("Refinance closing costs table body (tbody) not found!");
        addDebug("ERROR: Refinance closing costs table body not found!");
        return 0; // Return 0 if table isn't found
    }
    addDebug("Refinance closing costs table found: " + tbody);

    // Clear previous content
    tbody.innerHTML = '';
    addDebug("Cleared previous table content");

    // Ensure result.closing_costs_details exists and is an object
    const closingCostsDetails = (result && result.closing_costs_details && typeof result.closing_costs_details === 'object') ? result.closing_costs_details : {};
    addDebug("Closing costs details in API result: " + JSON.stringify(closingCostsDetails, null, 2));

    // Skip these keys when rendering
    const skipKeys = ['total', 'financed_closing_costs', 'financed_amount', 'cash_to_close'];
    
    // Sort the keys for consistent display
    const sortedKeys = Object.keys(closingCostsDetails).sort();
    
    // Track if we have any costs to display
    let hasClosingCosts = false;
    
    // Add each line item to the table
    // Define items that should always be shown, even if $0
    const alwaysShowItems = ['origination_fee', 'discount_points'];
    
    for (const key of sortedKeys) {
        if (!skipKeys.includes(key)) {
            const value = closingCostsDetails[key];
            // Show item if it has a value > 0 OR if it's in the always-show list
            if (value !== 0 || alwaysShowItems.includes(key)) {
                hasClosingCosts = true;
                // Convert snake_case to Title Case for display
                const displayName = key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
                
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${displayName}</td>
                    <td class="text-end">${formatCurrency(value)}</td>
                `;
                tbody.appendChild(row);
                addDebug(`Added closing cost: ${displayName} = ${formatCurrency(value)}`);
            }
        }
    }

    // If no closing costs, add a 'No Costs' row
    if (!hasClosingCosts) {
        const noClosingCostsRow = document.createElement('tr');
        noClosingCostsRow.innerHTML = `
            <td style="font-weight: normal; font-style: italic;" colspan="2">No closing costs details available</td>
        `;
        tbody.appendChild(noClosingCostsRow);
        addDebug("Added 'No Closing Costs' row");
    }

    // Add total row
    if (closingCostsDetails.total && closingCostsDetails.total > 0) {
        const totalRow = document.createElement('tr');
        totalRow.classList.add('total-row');
        totalRow.innerHTML = `
            <td>Total Closing Costs</td>
            <td class="text-end">${formatCurrency(closingCostsDetails.total)}</td>
        `;
        tbody.appendChild(totalRow);
        addDebug(`Added total row: ${formatCurrency(closingCostsDetails.total)}`);
        
        // Add explanation about all costs being financed
        const explanationRow = document.createElement('tr');
        explanationRow.innerHTML = `
            <td colspan="2" class="text-info small fst-italic">All closing costs are financed into your new loan amount.</td>
        `;
        tbody.appendChild(explanationRow);
        addDebug('Added explanation row about financed costs');

        // Add financed amount row if applicable
        if (closingCostsDetails.financed_amount > 0) {
            const financedRow = document.createElement('tr');
            financedRow.innerHTML = `
                <td><em>Amount Financed Into Loan</em></td>
                <td class="text-end"><em>(${formatCurrency(closingCostsDetails.financed_amount)})</em></td>
            `;
            tbody.appendChild(financedRow);
            addDebug(`Added financed amount row: ${formatCurrency(closingCostsDetails.financed_amount)}`);
        }

        // Add cash to close row if applicable
        if (closingCostsDetails.cash_to_close && closingCostsDetails.cash_to_close > 0) {
            const cashToCloseRow = document.createElement('tr');
            cashToCloseRow.classList.add('total-row');
            cashToCloseRow.innerHTML = `
                <td>Cash to Close</td>
                <td class="text-end">${formatCurrency(closingCostsDetails.cash_to_close)}</td>
            `;
            tbody.appendChild(cashToCloseRow);
            addDebug(`Added cash to close row: ${formatCurrency(closingCostsDetails.cash_to_close)}`);
        }
    }

    return closingCostsDetails.total || 0;
}

export function updateCreditsTable(result) {
    addDebug("Starting credit table update...");
    const tbody = document.getElementById('creditsTable');
    if (!tbody) {
        console.error("Credits table body (tbody) not found!");
        addDebug("ERROR: Credits table body not found!");
        return 0; // Return 0 if table isn't found
    }
    addDebug("Credits table found: " + tbody);

    // Clear previous content
    tbody.innerHTML = '';
    addDebug("Cleared previous table content");


    // Ensure result.credits exists and is an object
    const credits = (result && result.credits && typeof result.credits === 'object') ? result.credits : {};
    addDebug("Full API result: " + JSON.stringify(result, null, 2));
    addDebug("Credits section in API result: " + JSON.stringify(credits, null, 2));


    // Use optional chaining and nullish coalescing for safer access
    const sellerCredit = parseFloat(credits?.seller_credit ?? 0);
    const lenderCredit = parseFloat(credits?.lender_credit ?? 0);
    // Include tax proration if it exists and is a credit (positive value)
    const sellerTaxProrationCredit = Math.max(0, parseFloat(credits?.seller_tax_proration ?? 0));

    addDebug(`Credits from API: Seller=${sellerCredit}, Lender=${lenderCredit}, TaxProration=${sellerTaxProrationCredit}`);

    if (isNaN(sellerCredit) || isNaN(lenderCredit) || isNaN(sellerTaxProrationCredit)) {
        console.error("Invalid credit values received:", credits);
        addDebug("ERROR: Invalid credit values received.");
        return 0; // Return 0 if values are not valid numbers
    }

    // Calculate total only *after* validation
    const totalCredits = sellerCredit + lenderCredit + sellerTaxProrationCredit;


    // Add rows to the table based on available credits
    let hasCredits = false;

    if (sellerCredit > 0) {
        const row = tbody.insertRow();
        const descCell = row.insertCell(0);
        const amountCell = row.insertCell(1);
        descCell.textContent = 'Seller Credit';
        amountCell.textContent = formatCurrency(sellerCredit);
        amountCell.classList.add('text-end');
        hasCredits = true;
    }

    if (lenderCredit > 0) {
        const row = tbody.insertRow();
        const descCell = row.insertCell(0);
        const amountCell = row.insertCell(1);
        descCell.textContent = 'Lender Credit';
        amountCell.textContent = formatCurrency(lenderCredit);
        amountCell.classList.add('text-end');
        hasCredits = true;
    }

    // Add Tax Proration if it's a credit to the buyer
    if (sellerTaxProrationCredit > 0) {
        const row = tbody.insertRow();
        const descCell = row.insertCell(0);
        const amountCell = row.insertCell(1);
        descCell.textContent = 'Seller Tax Proration Credit'; // Clearer label
        amountCell.textContent = formatCurrency(sellerTaxProrationCredit);
        amountCell.classList.add('text-end');
        hasCredits = true;
    }


    // If no credits, add a 'No Credits' row
    if (!hasCredits) {
        const noCreditsRow = document.createElement('tr');
        noCreditsRow.innerHTML = `
            <td style="font-weight: normal; font-style: italic;" colspan="2">No credits applied</td>
        `;
        tbody.appendChild(noCreditsRow);
        addDebug("Added 'No Credits' row");
    }

    // Make sure the total credits element in the tfoot is updated
    const totalCreditsElement = document.getElementById('totalCredits');
    if (totalCreditsElement) {
        totalCreditsElement.textContent = formatCurrency(totalCredits);
        // Or use innerHTML if you need bold formatting:
        // totalCreditsElement.innerHTML = `<strong>${formatCurrency(totalCredits)}</strong>`;
        addDebug("Updated total credits display element: " + totalCredits);
    } else {
        console.error("Total credits element not found! Check HTML for element with id='totalCredits'");
        addDebug("ERROR: Total credits element not found!");
    }

    //Return the total credits for use in other calculations
    return totalCredits;
}

// Expose functions globally for direct access
window.updateClosingCostsTable = updateClosingCostsTable;
window.updatePrepaidsTable = updatePrepaidsTable;
window.updateCreditsTable = updateCreditsTable;
window.updateRefinanceClosingCostsTable = updateRefinanceClosingCostsTable;
