import { updateClosingCostsTable, updateCreditsTable, updatePrepaidsTable } from './ui/tableUpdaters.js';
import { formatCurrency, formatLabel, formatPercentage, safelyUpdateElement } from './utils/formatting.js';



// Updates the total cash needed at closing
function updateTotalCashNeeded(result, downPayment, closingCostsTotal, prepaidsTotal) {
    try {
        // Get the total credits from the result or calculate it
        let creditsTotal = 0;
        if (result.credits && typeof result.credits === 'object') {
            // Sum all credits (seller and lender only, NOT tax proration to avoid double counting)
            const sellerCredit = parseFloat(result.credits.seller_credit) || 0;
            const lenderCredit = parseFloat(result.credits.lender_credit) || 0;

            creditsTotal = sellerCredit + lenderCredit;
            console.log(`Credits from API: Seller=${sellerCredit}, Lender=${lenderCredit}, Total=${creditsTotal}`);
        }

        // Update the down payment in the Cash Needed at Closing section
        const downPaymentElement = document.getElementById('downPayment');
        if (downPaymentElement) {
            downPaymentElement.textContent = formatCurrency(downPayment);
            console.log(`Updated down payment display: ${downPayment}`);
        } else {
            console.error('Down payment element not found in Cash Needed section');
        }

        // Update the closing costs in the Cash Needed at Closing section
        const closingCostsElement = document.getElementById('totalClosingCosts');
        if (closingCostsElement) {
            closingCostsElement.textContent = formatCurrency(closingCostsTotal);
            console.log(`Updated closing costs display: ${closingCostsTotal}`);
        }

        // Update the prepaids in the Cash Needed at Closing section
        const prepaidsElement = document.getElementById('totalPrepaids');
        if (prepaidsElement) {
            prepaidsElement.textContent = formatCurrency(prepaidsTotal);
            console.log(`Updated prepaids display: ${prepaidsTotal}`);
        }

        // Update credits display in the Cash Needed at Closing section
        const creditsElement = document.getElementById('totalCredits');
        if (creditsElement) {
            creditsElement.textContent = formatCurrency(creditsTotal);
            console.log(`Updated total credits display: ${creditsTotal}`);
        }

        // Always calculate it based on the displayed values to ensure consistency
        const totalCashNeeded = downPayment + closingCostsTotal + prepaidsTotal - creditsTotal;
        console.log(`Calculated total cash needed: Down payment(${downPayment}) + Closing costs(${closingCostsTotal}) + Prepaids(${prepaidsTotal}) - Credits(${creditsTotal}) = ${totalCashNeeded}`);

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

document.addEventListener('DOMContentLoaded', function () {
    console.log("DOM loaded, setting up form handlers");

    // Get references to important elements
    const form = document.getElementById('mortgageForm');
    const calculateBtn = document.getElementById('calculateBtn');
    const includeOwnersTitleCheckbox = document.getElementById('include_owners_title');

    if (calculateBtn) {
        console.log("Calculate button found with ID:", calculateBtn.id);

        // Add click event listener
        calculateBtn.addEventListener('click', function (e) {
            console.log("Calculate button clicked");

            // Show loading spinner, hide results and error
            const loadingSpinner = document.getElementById('loadingSpinner');
            const resultsSection = document.getElementById('resultsSection');
            const errorAlert = document.getElementById('errorAlert');

            if (loadingSpinner) loadingSpinner.style.display = 'block';
            if (resultsSection) resultsSection.style.display = 'none';
            if (errorAlert) errorAlert.style.display = 'none';

            // Create data object for submission
            const formData = {
                purchase_price: parseFloat(document.getElementById('purchase_price').value),
                down_payment_percentage: parseFloat(document.getElementById('down_payment_percentage').value),
                annual_rate: parseFloat(document.getElementById('annual_rate').value),
                loan_term: parseInt(document.getElementById('loan_term').value),
                annual_tax_rate: parseFloat(document.getElementById('annual_tax_rate').value),
                annual_insurance_rate: parseFloat(document.getElementById('annual_insurance_rate').value),
                loan_type: document.getElementById('loan_type').value,
                monthly_hoa_fee: parseFloat(document.getElementById('monthly_hoa_fee').value || 0),
                seller_credit: parseFloat(document.getElementById('seller_credit').value || 0),
                lender_credit: parseFloat(document.getElementById('lender_credit').value || 0),
                discount_points: parseFloat(document.getElementById('discount_points').value || 0),
                include_owners_title: includeOwnersTitleCheckbox ? includeOwnersTitleCheckbox.checked : true
            };

            // Process closing date - ensure it's in the correct format
            const closingDateField = document.getElementById('closing_date');
            if (closingDateField && closingDateField.value) {
                console.log("Closing date from form:", closingDateField.value);
                // Make sure we send a valid ISO date string (YYYY-MM-DD)
                formData.closing_date = closingDateField.value;
                console.log("Closing date being sent:", formData.closing_date);
            }

            // Add VA loan parameters if applicable
            if (formData.loan_type === 'va') {
                formData.va_service_type = document.getElementById('va_service_type').value;
                formData.va_usage = document.getElementById('va_usage').value;
                formData.va_disability_exempt = document.getElementById('va_disability_exempt').checked;
            }

            console.log("Form data prepared:", formData);

            // Get CSRF token
            const csrfToken = document.querySelector('input[name="csrf_token"]').value;

            // Make API request
            console.log("Sending API request to /calculate");
            fetch('/calculate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify(formData)
            })
                .then(response => {
                    console.log("Response received:", response.status);
                    if (!response.ok) {
                        return response.text().then(text => {
                            throw new Error(`Status ${response.status}: ${text}`);
                        });
                    }
                    return response.text();
                })
                .then(responseText => {
                    console.log("Processing response text");
                    if (!responseText) {
                        throw new Error("Empty response received");
                    }

                    try {
                        const result = JSON.parse(responseText);
                        console.log("Result parsed successfully");

                        // Hide loading spinner
                        if (loadingSpinner) loadingSpinner.style.display = 'none';

                        // Show results section
                        if (resultsSection) resultsSection.style.display = 'block';

                        // Update UI with calculation results
                        updateResultsUI(result, formData);
                    } catch (e) {
                        console.error("JSON parse error:", e);
                        throw new Error(`Failed to parse response: ${e.message}`);
                    }
                })
                .catch(error => {
                    console.error("Error:", error);
                    if (loadingSpinner) loadingSpinner.style.display = 'none';
                    if (errorAlert) {
                        errorAlert.textContent = `Error: ${error.message}`;
                        errorAlert.style.display = 'block';
                    }
                });
        });
    } else {
        console.error("Calculate button not found!");
    }

    // Show/hide VA options based on loan type selection
    const loanTypeSelect = document.getElementById('loan_type');
    if (loanTypeSelect) {
        loanTypeSelect.addEventListener('change', handleLoanTypeChange);
    }

    // Initialize UI based on current loan type
    handleLoanTypeChange();
});

// Helper function to update all UI elements with calculation results
function updateResultsUI(result, formData) {
    console.log("Updating UI with calculation results");

    // Create a complete result object with all needed sections
    const completeResult = {
        loan_details: {
            ...result.loan_details,
            // Ensure critical values are present
            loan_term: result.loan_details.loan_term || result.loan_details.loan_term_years || formData.loan_term || 30,
            annual_rate: result.loan_details.annual_rate || result.loan_details.interest_rate || parseFloat(formData.annual_rate) || 0,
            ltv: result.loan_details.ltv || result.loan_details.ltv_ratio || (result.loan_details.loan_amount / result.loan_details.purchase_price * 100) || 0
        },
        monthly_breakdown: {
            principal_interest: result.monthly_breakdown.principal_interest,
            property_tax: result.monthly_breakdown.property_tax,
            home_insurance: result.monthly_breakdown.home_insurance,
            mortgage_insurance: result.monthly_breakdown.mortgage_insurance,
            hoa_fee: result.monthly_breakdown.hoa_fee,
            total: result.monthly_breakdown.total
        },
        closing_costs: result.closing_costs,
        prepaid_items: result.prepaids || result.prepaid_items,
        credits: result.credits,
        total_cash_needed: result.total_cash_needed
    };

    console.log("Structured result data:", JSON.stringify(completeResult, null, 2));

    // Update loan details
    safelyUpdateElement('purchasePrice', completeResult.loan_details.purchase_price, formatCurrency);
    safelyUpdateElement('downPaymentAmount', completeResult.loan_details.down_payment, formatCurrency);

    // Format down payment percentage correctly
    if (document.getElementById('downPaymentPercentage')) {
        const downPaymentPercentage = completeResult.loan_details.down_payment_percentage ||
            (completeResult.loan_details.down_payment / completeResult.loan_details.purchase_price * 100) || 0;
        document.getElementById('downPaymentPercentage').textContent = downPaymentPercentage.toFixed(3) + '%';
    }

    safelyUpdateElement('loanAmount', completeResult.loan_details.loan_amount, formatCurrency);

    // Enhanced interest rate handling with detailed logging
    const interestRateElement = document.getElementById('interestRate');
    if (interestRateElement) {
        // Log all possible sources for debugging
        console.log('Interest rate sources:', {
            'result.loan_details.annual_rate': result.loan_details.annual_rate,
            'result.loan_details.interest_rate': result.loan_details.interest_rate,
            'formData.annual_rate': formData.annual_rate
        });

        // Try all possible sources for the interest rate value
        let interestRate = 0;
        if (typeof result.loan_details.interest_rate === 'number' && !isNaN(result.loan_details.interest_rate)) {
            interestRate = result.loan_details.interest_rate;
            console.log(`Using interest_rate: ${interestRate}`);
        } else if (typeof result.loan_details.annual_rate === 'number' && !isNaN(result.loan_details.annual_rate)) {
            interestRate = result.loan_details.annual_rate;
            console.log(`Using annual_rate: ${interestRate}`);
        } else if (typeof formData.annual_rate === 'string' || typeof formData.annual_rate === 'number') {
            interestRate = parseFloat(formData.annual_rate);
            console.log(`Using form annual_rate: ${interestRate}`);
        }

        // Display the interest rate
        interestRateElement.textContent = formatPercentage(interestRate);
        console.log(`Final displayed interest rate: ${interestRate}%`);
    } else {
        console.error("Interest rate element not found");
    }

    // Update loan term without bold formatting
    const loanTermElement = document.getElementById('loanTerm');
    if (loanTermElement) {
        const loanTerm = completeResult.loan_details.loan_term || formData.loan_term || 30;
        loanTermElement.textContent = `${loanTerm} years`;
        loanTermElement.style.fontWeight = 'normal';
    }

    // Update discount points - directly use form data
    if (document.getElementById('discountPoints')) {
        const discountPoints = formData.discount_points || 0;
        document.getElementById('discountPoints').textContent = discountPoints.toFixed(3);
        console.log(`Displaying discount points: ${discountPoints}`);
    }

    // Update LTV display with accurate calculation
    const ltvElement = document.getElementById('ltv');
    if (ltvElement) {
        let ltv = 0;
        // Try all possible sources for the LTV value
        if (completeResult.loan_details.ltv) {
            ltv = completeResult.loan_details.ltv;
        } else if (completeResult.loan_details.ltv_ratio) {
            ltv = completeResult.loan_details.ltv_ratio;
        } else {
            // Calculate LTV if not provided
            const loanAmount = parseFloat(completeResult.loan_details.loan_amount) || 0;
            const purchasePrice = parseFloat(completeResult.loan_details.purchase_price) || 1; // Avoid division by zero
            ltv = (loanAmount / purchasePrice) * 100;
        }
        ltvElement.textContent = formatPercentage(ltv);
        console.log(`Displaying LTV: ${ltv}%`);
    }

    // Update closing date if available
    const closingDateElement = document.getElementById('closingDate');
    if (closingDateElement) {
        // First check if the closing date is in the form data (submitted by user)
        if (formData.closing_date) {
            try {
                const closingDate = new Date(formData.closing_date);
                closingDateElement.textContent = closingDate.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });
                console.log("Displaying closing date from form data:", formData.closing_date);
            } catch (e) {
                console.error("Error formatting closing date:", e);
                closingDateElement.textContent = formData.closing_date;
            }
        }
        // Fallback to response data if available
        else if (result.loan_details && result.loan_details.closing_date) {
            try {
                const closingDate = new Date(result.loan_details.closing_date);
                closingDateElement.textContent = closingDate.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });
            } catch (e) {
                closingDateElement.textContent = 'Not specified';
            }
        } else {
            closingDateElement.textContent = 'Not specified';
        }
    }

    // Update Loan Type field with user-friendly name
    const loanTypeElement = document.getElementById('loanType');
    if (loanTypeElement) {
        // Get the raw loan type and format it for display
        const rawLoanType = completeResult.loan_details.loan_type || formData.loan_type;
        let displayLoanType = 'Not specified';

        // Convert the loan type to a user-friendly format
        if (rawLoanType) {
            switch (rawLoanType.toLowerCase()) {
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
        const rawPropertyType = completeResult.loan_details.occupancy || document.getElementById('occupancy')?.value;
        let displayPropertyType = 'Not specified';

        // Convert the property type to a user-friendly format
        if (rawPropertyType) {
            switch (rawPropertyType) {
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

    // Update monthly payment breakdown
    safelyUpdateElement('principalAndInterest', result.monthly_breakdown.principal_interest, formatCurrency);
    safelyUpdateElement('propertyTax', result.monthly_breakdown.property_tax, formatCurrency);
    safelyUpdateElement('homeInsurance', result.monthly_breakdown.home_insurance, formatCurrency);
    safelyUpdateElement('pmi', result.monthly_breakdown.mortgage_insurance, formatCurrency);
    safelyUpdateElement('hoaFee', result.monthly_breakdown.hoa_fee, formatCurrency);
    safelyUpdateElement('totalMonthlyPayment', result.monthly_breakdown.total, formatCurrency);

    // Update closing costs, prepaids, and credits tables
    const downPayment = result.loan_details.down_payment;
    const closingCostsTotal = updateClosingCostsTable(result.closing_costs, formData, completeResult);
    const prepaidsTotal = updatePrepaidsTable(completeResult.prepaid_items);
    const creditsTotal = updateCreditsTable(completeResult);

    // Calculate and display total cash needed
    updateTotalCashNeeded(completeResult, downPayment, closingCostsTotal, prepaidsTotal);

    // Show all results cards - this makes them visible
    const cards = document.querySelectorAll('.results-card');
    cards.forEach(card => {
        card.style.display = 'block';
    });

    // Update max seller contribution display
    updateMaxSellerContributionDisplay(completeResult);

    console.log("UI update complete");
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
    resultsText += `Down Pmt                  ${downPayment}\n`;

    if (totalClosingCosts) {
        resultsText += `Tot Closing               ${totalClosingCosts}\n`;
    }

    if (totalPrepaids) {
        resultsText += `Tot Prepaids              ${totalPrepaids}\n`;
    }

    if (sellerCredit && sellerCredit !== '$0.00') {
        resultsText += `Seller Credit             ${formattedSellerCredit}\n`;
    }

    if (lenderCredit && lenderCredit !== '$0.00') {
        resultsText += `Lender Credit             ${formattedLenderCredit}\n`;
    }

    resultsText += `Cash to Close             ${totalCashToClose}\n`;
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


// Initialize the copy to clipboard functionality when the DOM is loaded
document.addEventListener('DOMContentLoaded', function () {
    // Setup summary copy button
    const copyButton = document.getElementById('copyResultsBtn');
    if (copyButton) {
        copyButton.addEventListener('click', function () {
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
        copyDetailedButton.addEventListener('click', function () {
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
