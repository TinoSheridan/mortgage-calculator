// static/js/ui/tableUpdaters.js

// Import necessary utility functions
import { addDebug, formatCurrency } from '../utils/formatting.js'; // Assuming addDebug is still needed here, adjust path if necessary

// Updates the closing costs table with details from the API response
// Returns the calculated total closing costs
export function updateClosingCostsTable(costs, formData, completeResult) {
    const tbody = document.querySelector('#closingCostsTable');
    if (!tbody) {
        console.error("Closing costs table body not found!");
        return 0; // Return 0 if table isn't found
    }

    // Ensure costs is an object, default to empty if not provided or null
    costs = costs && typeof costs === 'object' ? costs : {};

    // Extract the total provided by the server, if available
    const serverTotal = costs.total || 0;
    console.log("Found closing costs total in response:", serverTotal);

    // Clear previous content
    tbody.innerHTML = '';
    let total = 0;

    // --- Always show Origination Fee and Discount Points as the first two rows ---
    // Origination Fee
    const origFee = parseFloat(costs.origination_fee) || 0;
    const origRow = document.createElement('tr');
    origRow.innerHTML = `
        <td>Origination Fee</td>
        <td class="text-end">${formatCurrency(origFee)}</td>
    `;
    tbody.appendChild(origRow);
    if (origFee > 0) total += origFee;

    // Discount Points
    let pointsValue = 0;
    if (typeof costs.discount_points !== 'undefined') {
        pointsValue = parseFloat(costs.discount_points) || 0;
    } else if (formData && formData.discount_points) {
        pointsValue = parseFloat(formData.discount_points) || 0;
    }
    const pointsRow = document.createElement('tr');
    pointsRow.innerHTML = `
        <td>Discount Points${formData && formData.discount_points ? ` (${parseFloat(formData.discount_points).toFixed(3)}%)` : ''}</td>
        <td class="text-end">${formatCurrency(pointsValue)}</td>
    `;
    tbody.appendChild(pointsRow);
    if (pointsValue > 0) total += pointsValue;

    // --- Ensure both lender's and owner's title insurance are always shown, regardless of value or key variant ---
    const lenderKeys = ['lender_title_insurance', 'title_insurance'];
    const ownerKeys = ['owner_title_insurance', 'owners_title_insurance'];
    // Add lender's title insurance row
    let lenderFound = false;
    lenderKeys.forEach(key => {
        if (costs.hasOwnProperty(key)) {
            const value = parseFloat(costs[key]) || 0;
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>Lender's Title Insurance</td>
                <td class="text-end">${formatCurrency(value)}</td>
            `;
            tbody.appendChild(row);
            if (value > 0) total += value;
            lenderFound = true;
        }
    });
    if (!lenderFound) {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>Lender's Title Insurance</td>
            <td class="text-end">$0.00</td>
        `;
        tbody.appendChild(row);
    }
    // Add owner's title insurance row
    let ownerFound = false;
    ownerKeys.forEach(key => {
        if (costs.hasOwnProperty(key)) {
            const value = parseFloat(costs[key]) || 0;
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>Owner's Title Insurance</td>
                <td class="text-end">${formatCurrency(value)}</td>
            `;
            tbody.appendChild(row);
            if (value > 0) total += value;
            ownerFound = true;
        }
    });
    if (!ownerFound) {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>Owner's Title Insurance</td>
            <td class="text-end">$0.00</td>
        `;
        tbody.appendChild(row);
    }
    // --- End always-show title insurance rows ---

    // Define the order and labels for display
    const costOrder = [
        { key: 'processing_fee', label: 'Processing Fee' },
        { key: 'underwriting_fee', label: 'Underwriting Fee' },
        { key: 'admin_fee', label: 'Administration Fee' },
        { key: 'appraisal_fee', label: 'Appraisal Fee' },
        { key: 'credit_report_fee', label: 'Credit Report Fee' },
        { key: "attorney's_fee", label: "Attorney's Fee" }, // Corrected key
        { key: 'recording_fee', label: 'Recording Fee' },
        { key: 'state_tax_stamp', label: 'State Tax/Stamps' },
        { key: 'intangible_tax', label: 'Intangible Tax' },
        { key: 'doc_prep', label: 'Document Preparation' },
        { key: 'verification_fee', label: 'Verification Fee (VOE/VOM)' },
        { key: 'third_party_certs', label: 'Flood Cert/Tax Service' },
        // Discount points are handled separately
    ];

    // Add rows for each defined cost item found in the response, but skip origination fee, discount points, and title insurances to avoid duplicates
    costOrder.forEach(item => {
        if (['origination_fee', 'discount_points'].includes(item.key) || lenderKeys.includes(item.key) || ownerKeys.includes(item.key)) return;
        if (costs.hasOwnProperty(item.key) && costs[item.key] >= 0) {
            const value = parseFloat(costs[item.key]);
            if (value > 0) {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${item.label}</td>
                    <td class="text-end">${formatCurrency(value)}</td>
                `;
                tbody.appendChild(row);
                total += value;
            }
        }
    });

    // Update the total closing costs element in the tfoot
    const totalClosingCostsElement = document.getElementById('totalClosingCosts');
    if (totalClosingCostsElement) {
        totalClosingCostsElement.textContent = formatCurrency(total);
        // Or use innerHTML if you need bold formatting:
        // totalClosingCostsElement.innerHTML = `<strong>${formatCurrency(total)}</strong>`;
    }

    console.log(`Calculated closing costs total: ${total}`);
    return total;
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
        { key: 'tax_escrow_adjustment', label: 'Tax Escrow Adj +/-' } // Added for adjustment
    ];

    // Add rows for each defined prepaid item found in the response
    prepaidOrder.forEach(item => {
        // Check if the key exists and its value is not zero (or it's the adjustment which can be zero/negative)
        if (prepaids.hasOwnProperty(item.key) && (prepaids[item.key] !== 0 || item.key === 'tax_escrow_adjustment')) {
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


// Updates the credits table (seller and lender credits)
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
