// static/js/utils/formatting.js

// Format a number as currency
export function formatCurrency(number) {
    if (typeof number !== 'number') {
        console.error('formatCurrency called with non-number:', number);
        return '$0.00';
    }
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(number);
}

// Format a number as a percentage (e.g., 5.250%)
export function formatPercentage(number) {
    if (typeof number !== 'number') {
        console.error('formatPercentage called with non-number:', number);
        return '0.000%';
    }
    return number.toFixed(3) + '%';
}

// Helper function to safely update an element with a value, using a formatter if provided
export function safelyUpdateElement(elementId, value, formatter = (val) => val) {
    const element = document.getElementById(elementId);
    if (element) {
        // Check for undefined, null, or NaN values
        if (value !== undefined && value !== null && !isNaN(value)) {
            element.textContent = formatter(value);
        } else {
            // Use a default value for display (e.g., $0.00 for currency)
            element.textContent = formatter(0);
            console.warn(`Value for ${elementId} is undefined or invalid:`, value, ' Setting to default.');
        }
    } else {
        console.error(`Element with ID '${elementId}' not found`);
    }
}

// Add debug message to debug output area
export function addDebug(message) {
    console.log(message); // Log to console regardless
    const debugElement = document.getElementById('debugOutput');
    if (debugElement) {
        // Check if debug section is visible before appending
        const debugSection = document.getElementById('debugSection');
        if (debugSection && debugSection.style.display !== 'none') {
            debugElement.style.display = 'block'; // Ensure pre is visible
            debugElement.textContent += message + "\n";
        } else {
            // Optionally log that the message wasn't shown in UI if needed
            // console.log("Debug section hidden, message not added to UI:", message);
        }
    }
}

// Abbreviate longer mortgage labels for display
export function abbreviateMortgageLabel(label) {
    const abbreviations = {
        "Principal & Interest": "P&I",
        "Property Tax": "Taxes",
        "Home Insurance": "Insurance",
        "Private Mortgage Insurance": "PMI",
        "Mortgage Insurance Premium": "MIP", // FHA specific
        "VA Funding Fee": "VA FF",       // VA specific
        "USDA Guarantee Fee": "USDA GF", // USDA specific
        "HOA Fee": "HOA",
        "Total Monthly Payment": "Total Payment",
        "Lender's Title Insurance": "Lender Title",
        "Owner's Title Insurance": "Owner Title",
        "Total Closing Costs": "Total Closing",
        "Total Prepaid Items": "Total Prepaids",
        "Total Credits": "Total Credits",
        "Total Cash to Close": "Cash to Close",
        // Add more common closing/prepaid items if needed
        "Origination Fee": "Origination",
        "Processing Fee": "Processing",
        "Underwriting Fee": "Underwriting",
        "Appraisal Fee": "Appraisal",
        "Credit Report Fee": "Credit Report",
        "Recording Fee": "Recording",
        "State Tax/Stamps": "State Tax",
        "Homeowner's Insurance Premium": "Insurance Prem.",
        "Per Diem Interest": "Per Diem",
    };
    return abbreviations[label] || label; // Return abbreviation or original label
}

// Format labels consistently (e.g., capitalize words)
export function formatLabel(key) {
    if (!key) return '';
    return key.replace(/_/g, ' ')
        .split(' ')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
}
