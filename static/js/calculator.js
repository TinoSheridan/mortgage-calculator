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
        return '0.000%';
    }

    return number.toFixed(3) + '%';
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
        // First, add all items except tax_escrow_adjustment (to display it after tax_escrow)
        let taxEscrowAdjustment = null;

        for (const [key, amount] of Object.entries(prepaids)) {
            if (key !== 'total' && typeof amount === 'number') {
                // Handle tax escrow adjustment separately to place it right after tax escrow
                if (key === 'tax_escrow_adjustment') {
                    taxEscrowAdjustment = amount;
                    continue;
                }

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

                // If this was the tax escrow row and we have an adjustment, add it right after
                if (key === 'tax_escrow' && taxEscrowAdjustment !== null) {
                    total += taxEscrowAdjustment;

                    let adjustmentLabel = "Tax Escrow Adjustment (Dec)";
                    // If it's negative, it's a credit (seller's tax responsibility)
                    if (taxEscrowAdjustment < 0) {
                        adjustmentLabel = "Tax Escrow Credit (Seller's Portion)";
                    }

                    const adjustmentRow = document.createElement('tr');
                    adjustmentRow.innerHTML = `
                        <td style="font-weight: normal;">${adjustmentLabel}</td>
                        <td style="font-weight: normal;">${formatCurrency(taxEscrowAdjustment)}</td>
                    `;

                    // Add styling based on whether it's a credit or additional payment
                    if (taxEscrowAdjustment < 0) {
                        adjustmentRow.style.backgroundColor = "#e8f5e9"; // Light green for credits
                    } else if (taxEscrowAdjustment > 1000) {
                        adjustmentRow.style.backgroundColor = "#fffde7"; // Light yellow for significant additions
                    }

                    tbody.appendChild(adjustmentRow);
                    taxEscrowAdjustment = null; // Mark as processed
                }
            }
        }

        // If for some reason we didn't process the tax escrow adjustment above (no tax_escrow item),
        // add it at the end
        if (taxEscrowAdjustment !== null) {
            total += taxEscrowAdjustment;

            let adjustmentLabel = "Tax Escrow Adjustment (Dec)";
            // If it's negative, it's a credit (seller's tax responsibility)
            if (taxEscrowAdjustment < 0) {
                adjustmentLabel = "Tax Escrow Credit (Seller's Portion)";
            }

            const adjustmentRow = document.createElement('tr');
            adjustmentRow.innerHTML = `
                <td style="font-weight: normal;">${adjustmentLabel}</td>
                <td style="font-weight: normal;">${formatCurrency(taxEscrowAdjustment)}</td>
            `;

            // Add styling based on whether it's a credit or additional payment
            if (taxEscrowAdjustment < 0) {
                adjustmentRow.style.backgroundColor = "#e8f5e9"; // Light green for credits
            } else if (taxEscrowAdjustment > 1000) {
                adjustmentRow.style.backgroundColor = "#fffde7"; // Light yellow for significant additions
            }

            tbody.appendChild(adjustmentRow);
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

    // Find the credits table body - NOTE: This was the issue - needed to be more specific with the selector!
    const tbody = document.getElementById('creditsTable');
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
    console.log("Credits section in API result:", result.credits);

    if (result.credits && typeof result.credits === 'object') {
        console.log("Credits object found in result.credits");
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

    // Check if seller credit exceeds maximum allowed
    let maxSellerContribution = 0;
    let sellerCreditExceedsMax = false;
    let isVaLoan = false;
    let vaConcessionsExceedLimit = false;
    let vaConcessionLimit = 0;
    let potentialConcessions = 0;

    if (result.loan_details) {
        // Check if this is a VA loan with special handling
        if (result.loan_details.va_concession_limit !== undefined) {
            isVaLoan = true;
            vaConcessionLimit = parseFloat(result.loan_details.va_concession_limit);
            potentialConcessions = parseFloat(result.loan_details.potential_concessions || 0);
            vaConcessionsExceedLimit = result.loan_details.va_concessions_exceed_limit === true;
            console.log(`VA loan detected - concession limit: ${vaConcessionLimit}, potential concessions: ${potentialConcessions}, exceeds: ${vaConcessionsExceedLimit}`);
        }

        // Get general max seller contribution (handle both numeric and special values)
        if (result.loan_details.max_seller_contribution !== undefined) {
            // Check if it's a very large number (our stand-in for infinity in VA loans)
            if (result.loan_details.max_seller_contribution > 999999) {
                maxSellerContribution = Number.MAX_SAFE_INTEGER;
                console.log("VA loan with unlimited seller contribution detected");
            } else {
                maxSellerContribution = parseFloat(result.loan_details.max_seller_contribution);
            }
            sellerCreditExceedsMax = result.loan_details.seller_credit_exceeds_max === true;
            console.log(`Max seller contribution: ${maxSellerContribution}, Exceeds max: ${sellerCreditExceedsMax}`);
        }
    }

    // Only add rows if there are credits (either seller or lender)
    if (sellerCredit > 0 || lenderCredit > 0) {
        // Add seller credit row if it exists
        if (sellerCredit > 0) {
            const sellerCreditRow = document.createElement('tr');

            // If seller credit exceeds maximum, add warning
            if (sellerCreditExceedsMax) {
                if (isVaLoan) {
                    // Special VA loan warning for concessions limit
                    sellerCreditRow.innerHTML = `
                        <td style="font-weight: normal;">
                            Seller Credit
                            <div class="text-danger mt-1">
                                <i class="fas fa-exclamation-triangle"></i>
                                Warning: VA loans allow unlimited closing costs coverage, but prepaids and discount points
                                (${formatCurrency(potentialConcessions)}) exceed the 4% concession limit: ${formatCurrency(vaConcessionLimit)}
                            </div>
                        </td>
                        <td style="font-weight: normal;" class="text-end text-danger">${formatCurrency(sellerCredit)}</td>
                    `;
                } else {
                    // Standard warning for other loan types
                    sellerCreditRow.innerHTML = `
                        <td style="font-weight: normal;">
                            Seller Credit
                            <div class="text-danger mt-1">
                                <i class="fas fa-exclamation-triangle"></i>
                                Exceeds maximum allowed: ${formatCurrency(maxSellerContribution)}
                            </div>
                        </td>
                        <td style="font-weight: normal;" class="text-end text-danger">${formatCurrency(sellerCredit)}</td>
                    `;
                }
                // Highlight the row with a warning color
                sellerCreditRow.classList.add('table-warning');
            } else {
                sellerCreditRow.innerHTML = `
                    <td style="font-weight: normal;">Seller Credit</td>
                    <td style="font-weight: normal;" class="text-end">${formatCurrency(sellerCredit)}</td>
                `;
            }

            tbody.appendChild(sellerCreditRow);
            console.log("Added seller credit row");
        }

        // Add lender credit row if it exists
        if (lenderCredit > 0) {
            const lenderCreditRow = document.createElement('tr');
            lenderCreditRow.innerHTML = `
                <td style="font-weight: normal;">Lender Credit</td>
                <td style="font-weight: normal;" class="text-end">${formatCurrency(lenderCredit)}</td>
            `;
            tbody.appendChild(lenderCreditRow);
            console.log("Added lender credit row");
        }
    } else {
        // If no credits, add a "No Credits" row to indicate there are no credits
        const noCreditsRow = document.createElement('tr');
        noCreditsRow.innerHTML = `
            <td style="font-weight: normal; font-style: italic;" colspan="2">No credits applied</td>
        `;
        tbody.appendChild(noCreditsRow);
        console.log("Added 'No Credits' row");
    }

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

// Function to update the results area with calculation data
function updateResults(result) {
    try {
        console.log("Updating results with:", result);

        // Check if we have a valid result
        if (!result || !result.monthly_payment) {
            console.error("Invalid result object:", result);
            return;
        }

        // Show the results section
        document.getElementById('resultsSection').classList.remove('d-none');

        // Update monthly payment summary
        updateMonthlySummary(result);

        // Update loan details card
        updateLoanDetails(result);

        // Update monthly breakdown card
        updateMonthlyBreakdown(result);

        // Update closing costs card
        updateClosingCosts(result);

        // Update cash needed at closing card
        updateCashNeededAtClosing(result);

        // Update max seller contribution display
        updateMaxSellerContributionDisplay(result);

        // Enable copy buttons now that we have results
        document.getElementById('copyResultsBtn').disabled = false;
        document.getElementById('copyDetailedResultsBtn').disabled = false;

        // Hide the loading spinner if it's visible
        document.getElementById('loadingSpinner').classList.add('d-none');
    } catch (e) {
        console.error("Error updating results:", e);
    }
}

// Update the max seller contribution display from calculation results
function updateMaxSellerContributionDisplay(result) {
    try {
        const maxContributionElement = document.getElementById('maxSellerContribution');
        if (!maxContributionElement) return;

        // If we have loan details with max seller contribution
        if (result && result.loan_details && result.loan_details.max_seller_contribution !== undefined) {
            const maxContribution = parseFloat(result.loan_details.max_seller_contribution);
            const purchasePrice = parseFloat(document.getElementById('purchase_price').value) || 0;

            // Format as currency
            const formatter = new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: 'USD',
                minimumFractionDigits: 0,
                maximumFractionDigits: 0
            });

            // Special case for VA loans
            if (maxContribution > 999999) {
                maxContributionElement.textContent = `Max contribution: Unlimited for closing costs, ${formatter.format(purchasePrice * 0.04)} for concessions`;
            } else {
                const percentage = (maxContribution / purchasePrice * 100).toFixed(1);
                maxContributionElement.textContent = `Max contribution: ${formatter.format(maxContribution)} (${percentage}% of purchase price)`;
            }

            // Apply warning class if seller credit exceeds max
            const sellerCreditExceedsMax = result.loan_details.seller_credit_exceeds_max === true;
            if (sellerCreditExceedsMax) {
                maxContributionElement.classList.remove('text-info');
                maxContributionElement.classList.add('text-danger');
            } else {
                maxContributionElement.classList.remove('text-danger');
                maxContributionElement.classList.add('text-info');
            }

            // Debug logging
            console.debug(`Max seller contribution updated: ${maxContribution}, Exceeds max: ${sellerCreditExceedsMax}`);
        } else {
            console.warn("Max seller contribution calculation data missing in result", result);
            maxContributionElement.textContent = 'Max contribution will be calculated based on loan type and purchase price';
            maxContributionElement.classList.remove('text-danger');
            maxContributionElement.classList.add('text-info');
        }
    } catch (error) {
        console.error("Error updating max seller contribution:", error);
    }
}

// Handle form submission and calculate mortgage details
document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM loaded, setting up form handlers");

    // Setup mortgage form submission
    const mortgageForm = document.getElementById('mortgageForm');
    if (mortgageForm) {
        console.log("Form found, adding submit handler");

        // Add click handler for the submit button instead of form submit
        document.querySelector('button[type="submit"]').addEventListener('click', async function(e) {
            // Prevent default button behavior
            e.preventDefault();
            console.log("Submit button clicked, handling form submission manually");

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
                const formData = new FormData(mortgageForm);
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
                formDataObj.discount_points = parseFloat(formDataObj.discount_points || 0);

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

                // Get CSRF token
                const csrfToken = document.querySelector('input[name="csrf_token"]').value;
                console.log("Using CSRF token:", csrfToken);

                // Make API request
                const response = await fetch('/calculate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
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
                console.log("API response:", JSON.stringify(result, null, 2));

                // Show results section
                document.getElementById('resultsSection').style.display = 'block';

                // Create a complete result object with all needed sections
                const completeResult = {
                    loan_details: result.loan_details,
                    monthly_breakdown: {
                        principal_interest: result.monthly_breakdown.principal_interest,
                        property_tax: result.monthly_breakdown.property_tax,
                        insurance: result.monthly_breakdown.home_insurance,
                        hoa: result.monthly_breakdown.hoa_fee,
                        pmi: result.monthly_breakdown.mortgage_insurance,
                        total: result.monthly_breakdown.total
                    },
                    closing_costs: result.closing_costs,
                    prepaid_items: result.prepaids || result.prepaid_items,
                    credits: result.credits,  // Make sure credits is included
                    total_cash_needed: result.total_cash_needed
                };

                console.log("Updating results with:", JSON.stringify(completeResult, null, 2));
                console.log("Credits object specifically:", JSON.stringify(completeResult.credits, null, 2));

                // Update loan details
                safelyUpdateElement('purchasePrice', result.loan_details.purchase_price, formatCurrency);
                safelyUpdateElement('downPaymentAmount', result.loan_details.down_payment, formatCurrency);

                // Format down payment percentage correctly
                if (document.getElementById('downPaymentPercentage')) {
                    const downPaymentPercentage = result.loan_details.down_payment_percentage ||
                                                 (result.loan_details.down_payment / result.loan_details.purchase_price * 100);
                    document.getElementById('downPaymentPercentage').textContent = downPaymentPercentage.toFixed(3) + '%';
                }

                safelyUpdateElement('loanAmount', result.loan_details.loan_amount, formatCurrency);
                safelyUpdateElement('interestRate', result.loan_details.annual_rate, formatPercentage);

                // Update loan term without bold formatting
                const loanTermElement = document.getElementById('loanTerm');
                if (loanTermElement) {
                    loanTermElement.textContent = `${result.loan_details.loan_term} years`;
                    loanTermElement.style.fontWeight = 'normal';
                }

                // Update closing date if available
                const closingDateElement = document.getElementById('closingDate');
                if (closingDateElement) {
                    if (result.loan_details.closing_date) {
                        const closingDate = new Date(result.loan_details.closing_date);
                        closingDateElement.textContent = closingDate.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });
                    } else {
                        closingDateElement.textContent = 'Not specified';
                    }
                }

                safelyUpdateElement('ltv', result.loan_details.ltv, formatPercentage);

                // Update Loan Type field with user-friendly name
                const loanTypeElement = document.getElementById('loanType');
                if (loanTypeElement) {
                    // Get the raw loan type and format it for display
                    const rawLoanType = result.loan_details.loan_type || formDataObj.loan_type;
                    let displayLoanType = 'Not specified';

                    // Convert the loan type to a user-friendly format
                    if (rawLoanType) {
                        switch(rawLoanType.toLowerCase()) {
                            case 'conventional':
                                displayLoanType = 'Conventional';
                                break;
                            case 'fha':
                                displayLoanType = 'FHA';
                                break;
                            case 'va':
                                displayLoanType = 'VA';
                                break;
                            case 'usda':
                                displayLoanType = 'USDA';
                                break;
                            default:
                                displayLoanType = rawLoanType.charAt(0).toUpperCase() + rawLoanType.slice(1);
                        }
                    }

                    loanTypeElement.textContent = displayLoanType;
                }

                // Update Property Type field with user-friendly name
                const propertyTypeElement = document.getElementById('propertyType');
                if (propertyTypeElement) {
                    // Get the raw property type (occupancy) and format it for display
                    const rawPropertyType = result.loan_details.occupancy || formDataObj.occupancy;
                    let displayPropertyType = 'Not specified';

                    // Convert the property type to a user-friendly format
                    if (rawPropertyType) {
                        switch(rawPropertyType) {
                            case 'primary_residence':
                                displayPropertyType = 'Primary Residence';
                                break;
                            case 'second_home':
                                displayPropertyType = 'Second Home';
                                break;
                            case 'investment_property':
                                displayPropertyType = 'Investment Property';
                                break;
                            default:
                                displayPropertyType = rawPropertyType
                                    .split('_')
                                    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
                                    .join(' ');
                        }
                    }

                    propertyTypeElement.textContent = displayPropertyType;
                }

                safelyUpdateElement('principalAndInterest', result.monthly_breakdown.principal_interest, formatCurrency);
                safelyUpdateElement('propertyTax', result.monthly_breakdown.property_tax, formatCurrency);
                safelyUpdateElement('homeInsurance', result.monthly_breakdown.home_insurance, formatCurrency);
                safelyUpdateElement('pmi', result.monthly_breakdown.mortgage_insurance, formatCurrency);
                safelyUpdateElement('hoaFee', result.monthly_breakdown.hoa_fee, formatCurrency);
                safelyUpdateElement('totalMonthlyPayment', result.monthly_breakdown.total, formatCurrency);

                // Update discount points
                safelyUpdateElement('discountPoints', formDataObj.discount_points, val => val.toFixed(3));

                // Update closing costs, prepaids, and credits tables
                const downPayment = result.loan_details.down_payment;
                const closingCostsTotal = updateClosingCostsTable(result.closing_costs);
                const prepaidsTotal = updatePrepaidsTable(result.prepaids || result.prepaid_items);
                const creditsTotal = updateCreditsTable(completeResult);

                // Calculate and display total cash needed
                updateTotalCashNeeded(completeResult, downPayment, closingCostsTotal, prepaidsTotal, creditsTotal);

                // Show all results cards - this makes them visible
                const cards = document.querySelectorAll('.results-card');
                cards.forEach(card => {
                    card.style.display = 'block';
                });

                // Update max seller contribution display
                updateMaxSellerContributionDisplay(completeResult);

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
    }

    // Show/hide VA options based on loan type selection
    const loanTypeSelect = document.getElementById('loan_type');
    if (loanTypeSelect) {
        loanTypeSelect.addEventListener('change', handleLoanTypeChange);
    }

    // Initialize UI based on current loan type
    handleLoanTypeChange();
});

// Function to handle loan type change
function handleLoanTypeChange() {
    const loanTypeSelect = document.getElementById('loan_type');
    if (!loanTypeSelect) return;

    const vaOptions = document.getElementById('vaOptions');
    if (vaOptions) {
        if (loanTypeSelect.value === 'va') {
            vaOptions.style.display = 'block';
        } else {
            vaOptions.style.display = 'none';
        }
    }
}

// Function to abbreviate mortgage labels intelligently
function abbreviateMortgageLabel(label, maxLength = 25) {
    if (!label) return '';

    // Clean the label
    const cleanLabel = label.trim().replace(/:$/, '').toLowerCase();

    // Direct abbreviation mapping for common mortgage terms
    if (cleanLabel === 'total monthly payment') return 'Tot Monthly Pmt';
    if (cleanLabel === 'owners title insurance' || cleanLabel === 'owner\'s title insurance') return 'Owner Title Ins';
    if (cleanLabel === 'total closing cost' || cleanLabel === 'total closing costs') return 'Tot Closing';
    if (cleanLabel === 'total cash to close' || cleanLabel === 'total cash needed') return 'Cash to Close';
    if (cleanLabel === 'principal and interest' || cleanLabel === 'principal & interest') return 'P&I';
    if (cleanLabel === 'private mortgage insurance') return 'PMI';
    if (cleanLabel === 'mortgage insurance') return 'MI';
    if (cleanLabel === 'property tax') return 'Prop Tax';
    if (cleanLabel === 'homeowner\'s insurance' || cleanLabel === 'home insurance') return 'Insurance';
    if (cleanLabel === 'homeowners association' || cleanLabel === 'homeowner\'s association') return 'HOA';
    if (cleanLabel === 'processing fee') return 'Proc Fee';
    if (cleanLabel === 'recording fee') return 'Rec Fee';
    if (cleanLabel === 'application fee') return 'App Fee';
    if (cleanLabel === 'administration fee') return 'Admin Fee';
    if (cleanLabel === 'document preparation') return 'Doc Prep';
    if (cleanLabel === 'underwriting fee') return 'UW Fee';
    if (cleanLabel === 'transfer tax') return 'Trans Tax';
    if (cleanLabel.includes('lender') && cleanLabel.includes('title insurance')) return 'Lender Title Ins';
    if (cleanLabel === 'down payment') return 'Down Pmt';
    if (cleanLabel === 'purchase price') return 'Purch Price';
    if (cleanLabel === 'loan amount') return 'Loan Amt';
    if (cleanLabel === 'interest rate') return 'Int Rate';
    if (cleanLabel === 'total prepaids') return 'Tot Prepaids';
    if (cleanLabel === 'total credits') return 'Tot Credits';

    // If the label is still too long, truncate it
    if (label.length > maxLength) {
        return label.substring(0, maxLength - 3) + '...';
    }

    // If no abbreviation is defined, return the original
    return label;
}

// Function to format mortgage calculation results for clipboard
function formatResultsForClipboard() {
    // Define column width for label alignment - reduce spacing
    const LABEL_WIDTH = 25;   // Reduced width for labels
    const VALUE_WIDTH = 12;   // Width for values

    let resultsText = "MORTGAGE CALCULATION SUMMARY\n";
    resultsText += "============================\n\n";

    // Loan details section - directly use abbreviated terms
    resultsText += "LOAN DETAILS\n";
    resultsText += "===========\n";

    // Helper function for consistent right-aligned formatting in plain text
    function formatRow(label, value) {
        // Ensure the label fits within LABEL_WIDTH
        let displayLabel = label;
        if (displayLabel.length > LABEL_WIDTH - 2) {
            displayLabel = displayLabel.substring(0, LABEL_WIDTH - 2);
        }

        // Calculate spaces needed for alignment
        const spaces = LABEL_WIDTH - displayLabel.length;

        // Create the row with proper alignment
        return `${displayLabel}${' '.repeat(spaces)}${value}\n`;
    }

    // Get loan details elements using the correct IDs from HTML
    const purchasePrice = document.getElementById('purchasePrice')?.textContent || '';
    const loanAmount = document.getElementById('loanAmount')?.textContent || '';
    const downPayment = document.getElementById('downPaymentAmount')?.textContent || '';
    const interestRate = document.getElementById('interestRate')?.textContent || '';
    const loanTerm = document.getElementById('loanTerm')?.textContent || '';
    const loanType = document.getElementById('loanType')?.textContent || '';
    const propertyType = document.getElementById('propertyType')?.textContent || '';

    // Add loan details section
    resultsText += formatRow("Purch Price", purchasePrice);
    resultsText += formatRow("Loan Amt", loanAmount);
    resultsText += formatRow("Down Pmt", downPayment);
    resultsText += formatRow("Int Rate", interestRate);
    resultsText += formatRow("Loan Term", loanTerm);
    resultsText += formatRow("Loan Type", loanType);
    resultsText += formatRow("Property Type", propertyType);
    resultsText += "\n";

    // Monthly Payment section - directly use abbreviated terms
    resultsText += "MONTHLY PAYMENT\n";
    resultsText += "==============\n";

    // Use the correct element IDs from the HTML
    const principalInterest = document.getElementById('principalAndInterest')?.textContent || '';
    const propertyTax = document.getElementById('propertyTax')?.textContent || '';
    const homeownersInsurance = document.getElementById('homeInsurance')?.textContent || '';
    const mortgageInsurance = document.getElementById('pmi')?.textContent || '';
    const hoa = document.getElementById('hoaFee')?.textContent || '';
    const totalMonthlyPayment = document.getElementById('totalMonthlyPayment')?.textContent || '';

    // Add monthly payment section
    resultsText += formatRow("P&I", principalInterest);
    resultsText += formatRow("Prop Tax", propertyTax);
    resultsText += formatRow("Insurance", homeownersInsurance);

    if (mortgageInsurance && mortgageInsurance.trim() !== '$0' && mortgageInsurance.trim() !== '$0.00') {
        resultsText += formatRow("PMI", mortgageInsurance);
    }

    if (hoa && hoa.trim() !== '$0' && hoa.trim() !== '$0.00') {
        resultsText += formatRow("HOA", hoa);
    }

    resultsText += formatRow("Tot Monthly Pmt", totalMonthlyPayment);
    resultsText += "\n";

    // Cash to Close section
    const totalClosingCosts = document.getElementById('totalClosingCosts')?.textContent || '';
    const totalPrepaids = document.getElementById('totalPrepaids')?.textContent || '';
    const totalCashToClose = document.getElementById('totalCashNeeded')?.textContent || '';

    // Get credits information
    const sellerCreditElement = document.querySelector('#creditsTable tr:nth-child(1) td:nth-child(2)');
    const lenderCreditElement = document.querySelector('#creditsTable tr:nth-child(2) td:nth-child(2)');

    const sellerCredit = sellerCreditElement ? sellerCreditElement.textContent.trim() : '$0.00';
    const lenderCredit = lenderCreditElement ? lenderCreditElement.textContent.trim() : '$0.00';

    // Format credits with parentheses to indicate negative values
    const formattedSellerCredit = sellerCredit !== '$0.00' ? `(${sellerCredit})` : sellerCredit;
    const formattedLenderCredit = lenderCredit !== '$0.00' ? `(${lenderCredit})` : lenderCredit;

    resultsText += "CASH TO CLOSE\n";
    resultsText += "============\n";
    resultsText += formatRow("Down Pmt", downPayment);
    resultsText += formatRow("Closing Costs", totalClosingCosts);
    resultsText += formatRow("Prepaids", totalPrepaids);

    // Only show credits if they exist
    if (sellerCredit && sellerCredit !== '$0.00') {
        resultsText += formatRow("Seller Credit", formattedSellerCredit);
    }

    if (lenderCredit && lenderCredit !== '$0.00') {
        resultsText += formatRow("Lender Credit", formattedLenderCredit);
    }

    resultsText += formatRow("Cash to Close", totalCashToClose);
    resultsText += "\n";

    // Add calculation timestamp
    const date = new Date();
    resultsText += `Calculated on: ${date.toLocaleDateString()} at ${date.toLocaleTimeString()}\n`;

    return resultsText;
}

// Function to format detailed mortgage calculation results including all line items
function formatDetailedResultsForClipboard() {
    // Define column width for label alignment
    const LABEL_WIDTH = 30;

    let resultsText = "DETAILED MORTGAGE CALCULATION RESULTS\n";
    resultsText += "=====================================\n\n";

    // Get all result cards
    const resultCards = document.querySelectorAll('.results-card');

    // Track what tables we've already processed to avoid duplication
    const processedTables = new Set();
    const processedCardIds = new Set();

    // First, process only the loan details and monthly payment cards
    resultCards.forEach(card => {
        if (card.style.display === 'none') return; // Skip hidden cards

        // Get card header/title
        const cardHeader = card.querySelector('.card-header');
        if (cardHeader) {
            const title = cardHeader.textContent.trim();
            // Skip the closing costs, prepaids, and credits cards
            if (title.toLowerCase().includes("closing cost") ||
                title.toLowerCase().includes("prepaid") ||
                title.toLowerCase().includes("credit") ||
                title.toLowerCase().includes("cash needed")) {
                return;
            }

            resultsText += `${title.toUpperCase()}\n`;
            resultsText += "".padEnd(title.length, '=') + "\n";
        }

        // Get all table rows in this card
        const tables = card.querySelectorAll('table');
        tables.forEach(table => {
            // Mark this table as processed and skip if it's one of our special tables
            // that we'll process separately
            if (table.id === 'closingCostsTable' ||
                table.id === 'prepaidsTable' ||
                table.id === 'creditsTable') {
                processedTables.add(table.id);
                return;
            }

            const rows = table.querySelectorAll('tbody tr');
            rows.forEach(row => {
                const label = row.querySelector('td:first-child');
                const value = row.querySelector('td:last-child');

                if (label && value) {
                    // Use our direct label formatter
                    const formattedLabel = formatLabel(label.textContent.trim(), LABEL_WIDTH);
                    resultsText += `${formattedLabel} ${value.textContent.trim()}\n`;
                }
            });
        });

        resultsText += "\n"; // Add extra line between cards
    });

    // Store down payment value
    let downPaymentValue = "";
    const downPaymentElement = document.getElementById('downPaymentAmount');
    if (downPaymentElement) {
        downPaymentValue = downPaymentElement.textContent;
    }

    // Add closing costs table details
    const closingCostsTable = document.getElementById('closingCostsTable');
    let closingCostsTotal = "";
    if (closingCostsTable) {
        resultsText += "CLOSING COSTS BREAKDOWN\n";
        resultsText += "=======================\n";

        const rows = closingCostsTable.querySelectorAll('tr');
        rows.forEach(row => {
            const cells = row.querySelectorAll('td');
            if (cells.length === 2) {
                // Use our direct label formatter
                const formattedLabel = formatLabel(cells[0].textContent.trim(), LABEL_WIDTH);
                resultsText += `${formattedLabel} ${cells[1].textContent.trim()}\n`;
            }
        });

        // Add total closing costs
        const totalClosingCosts = document.getElementById('totalClosingCosts');
        if (totalClosingCosts) {
            closingCostsTotal = totalClosingCosts.textContent;
            // Directly use the abbreviation
            resultsText += `Tot Closing               ${closingCostsTotal}\n`;
        }

        resultsText += "\n";
    }

    // Add prepaids table details
    const prepaidsTable = document.getElementById('prepaidsTable');
    let prepaidsTotal = "";
    if (prepaidsTable) {
        resultsText += "PREPAIDS BREAKDOWN\n";
        resultsText += "==================\n";

        const rows = prepaidsTable.querySelectorAll('tr');
        rows.forEach(row => {
            const cells = row.querySelectorAll('td');
            if (cells.length === 2) {
                // Use our direct label formatter
                const formattedLabel = formatLabel(cells[0].textContent.trim(), LABEL_WIDTH);
                resultsText += `${formattedLabel} ${cells[1].textContent.trim()}\n`;
            }
        });

        // Add total prepaids
        const totalPrepaids = document.getElementById('totalPrepaids');
        if (totalPrepaids) {
            prepaidsTotal = totalPrepaids.textContent;
            // Directly use the abbreviation
            resultsText += `Tot Prepaids              ${prepaidsTotal}\n`;
        }

        resultsText += "\n";
    }

    // Add credits table details if it exists
    const creditsTable = document.getElementById('creditsTable');
    let creditsTotal = "";
    if (creditsTable) {
        resultsText += "CREDITS BREAKDOWN\n";
        resultsText += "=================\n";

        const rows = creditsTable.querySelectorAll('tr');
        rows.forEach(row => {
            const cells = row.querySelectorAll('td');
            if (cells.length === 2) {
                // Use our direct label formatter
                const formattedLabel = formatLabel(cells[0].textContent.trim(), LABEL_WIDTH);
                resultsText += `${formattedLabel} ${cells[1].textContent.trim()}\n`;
            }
        });

        // Add total credits
        const totalCredits = document.getElementById('totalCredits');
        if (totalCredits) {
            creditsTotal = totalCredits.textContent;
            // Directly use the abbreviation
            resultsText += `Tot Credits              ${creditsTotal}\n`;
        }

        resultsText += "\n";
    }

    // Calculate and add cash to close (down payment + closing costs + prepaids - credits)
    resultsText += "TOTAL CASH TO CLOSE\n";
    resultsText += "==================\n";
    resultsText += `Down Pmt                  ${downPaymentValue}\n`;

    if (closingCostsTotal) {
        resultsText += `Tot Closing               ${closingCostsTotal}\n`;
    }

    if (prepaidsTotal) {
        resultsText += `Tot Prepaids              ${prepaidsTotal}\n`;
    }

    if (creditsTotal) {
        resultsText += `Tot Credits               ${creditsTotal}\n`;
    }

    const totalCashNeeded = document.getElementById('totalCashNeeded');
    if (totalCashNeeded) {
        resultsText += `Cash to Close             ${totalCashNeeded.textContent}\n`;
    }

    // Add calculation timestamp
    const date = new Date();
    resultsText += `\nCalculated on: ${date.toLocaleDateString()} at ${date.toLocaleTimeString()}\n`;

    return resultsText;
}

// Function to directly format labels for clipboard with abbreviations
function formatLabel(label, width = 30) {
    // Clean the label
    const cleanLabel = label.trim().replace(/:$/, '').toLowerCase();

    // Direct abbreviation mapping
    let abbr = label.trim().replace(/:$/, '');

    // Map common terms to their abbreviations
    if (cleanLabel === 'total monthly payment') abbr = 'Tot Monthly Pmt';
    else if (cleanLabel === 'owners title insurance') abbr = 'Owner Title Ins';
    else if (cleanLabel === 'owner\'s title insurance') abbr = 'Owner Title Ins';
    else if (cleanLabel === 'total closing cost' || cleanLabel === 'total closing costs') abbr = 'Tot Closing';
    else if (cleanLabel === 'total cash to close' || cleanLabel === 'total cash needed') abbr = 'Cash to Close';
    else if (cleanLabel === 'principal and interest' || cleanLabel === 'principal & interest') abbr = 'P&I';
    else if (cleanLabel === 'private mortgage insurance') abbr = 'PMI';
    else if (cleanLabel === 'mortgage insurance') abbr = 'MI';
    else if (cleanLabel === 'property tax') abbr = 'Prop Tax';
    else if (cleanLabel === 'homeowner\'s insurance' || cleanLabel === 'home insurance') abbr = 'Insurance';
    else if (cleanLabel === 'homeowners association' || cleanLabel === 'homeowner\'s association') abbr = 'HOA';
    else if (cleanLabel === 'processing fee') abbr = 'Proc Fee';
    else if (cleanLabel === 'recording fee') abbr = 'Rec Fee';
    else if (cleanLabel === 'application fee') abbr = 'App Fee';
    else if (cleanLabel === 'administration fee') abbr = 'Admin Fee';
    else if (cleanLabel === 'document preparation') abbr = 'Doc Prep';
    else if (cleanLabel === 'underwriting fee') abbr = 'UW Fee';
    else if (cleanLabel === 'transfer tax') abbr = 'Trans Tax';
    else if (cleanLabel.includes('lender') && cleanLabel.includes('title insurance')) abbr = 'Lender Title Ins';
    else if (cleanLabel === 'down payment') abbr = 'Down Pmt';
    else if (cleanLabel === 'purchase price') abbr = 'Purch Price';
    else if (cleanLabel === 'loan amount') abbr = 'Loan Amt';
    else if (cleanLabel === 'interest rate') abbr = 'Int Rate';
    else if (cleanLabel === 'total prepaids') abbr = 'Tot Prepaids';
    else if (cleanLabel === 'total credits') abbr = 'Tot Credits';

    // Pad the label to the desired width
    return abbr.padEnd(width);
}

// Initialize the copy to clipboard functionality when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Setup summary copy button
    const copyButton = document.getElementById('copyResultsBtn');
    if (copyButton) {
        copyButton.addEventListener('click', function() {
            // Generate results text
            const resultsText = formatResultsForClipboard();

            // Use the Clipboard API to copy text
            navigator.clipboard.writeText(resultsText)
                .then(() => {
                    // Show the success message
                    const copyConfirmation = document.getElementById('copyConfirmation');
                    if (copyConfirmation) {
                        copyConfirmation.textContent = 'Results copied to clipboard!';
                        copyConfirmation.classList.remove('d-none');

                        // Hide the confirmation after 3 seconds
                        setTimeout(() => {
                            copyConfirmation.classList.add('d-none');
                        }, 3000);
                    }
                })
                .catch(() => {
                    alert('Failed to copy results to clipboard. Please try again.');
                });
        });
    }

    // Setup detailed results copy button
    const copyDetailedButton = document.getElementById('copyDetailBtn');
    if (copyDetailedButton) {
        copyDetailedButton.addEventListener('click', function() {
            // Generate detailed results text
            const detailedResultsText = formatDetailedResultsForClipboard();

            // Use the Clipboard API to copy text
            navigator.clipboard.writeText(detailedResultsText)
                .then(() => {
                    // Show the success message
                    const copyConfirmation = document.getElementById('copyConfirmation');
                    if (copyConfirmation) {
                        copyConfirmation.textContent = 'Detailed results copied to clipboard!';
                        copyConfirmation.classList.remove('d-none');

                        // Hide the confirmation after 3 seconds
                        setTimeout(() => {
                            copyConfirmation.classList.add('d-none');
                        }, 3000);
                    }
                })
                .catch(() => {
                    alert('Failed to copy detailed results to clipboard. Please try again.');
                });
        });
    }
});
