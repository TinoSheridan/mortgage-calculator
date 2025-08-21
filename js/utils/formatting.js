// static/js/utils/formatting.js

// Format a number as currency with smart precision
export function formatCurrency(number, options = {}) {
    if (typeof number !== 'number') {
        console.error('formatCurrency called with non-number:', number);
        return '$0.00';
    }

    const { compact = false, precision = 2, isLoanAmount = false } = options;

    // For mobile/compact display, use abbreviated format for large numbers
    if (compact && Math.abs(number) >= 1000000) {
        const millions = number / 1000000;
        return `$${millions.toFixed(1)}M`;
    } else if (compact && Math.abs(number) >= 1000) {
        const thousands = number / 1000;
        return `$${thousands.toFixed(0)}K`;
    }

    // Loan amounts should be rounded down to whole dollars
    if (isLoanAmount) {
        const roundedNumber = Math.floor(number);
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(roundedNumber);
    }

    // All other currency values should show exactly 2 decimal places
    const formatOptions = {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    };

    // Override precision if specifically provided
    if (typeof precision === 'number' && precision !== 2) {
        formatOptions.minimumFractionDigits = precision;
        formatOptions.maximumFractionDigits = precision;
    }

    return new Intl.NumberFormat('en-US', formatOptions).format(number);
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
export function safelyUpdateElement(elementOrId, value, formatter = (val) => val) {
    // Handle both element objects and ID strings
    const element = typeof elementOrId === 'string' ? document.getElementById(elementOrId) : elementOrId;

    if (element) {
        // Check for undefined, null values. Allow strings (for formatted values) and numbers
        if (value !== undefined && value !== null) {
            element.textContent = value; // Value is already formatted, just set it directly
        } else {
            // Use a default value for display (e.g., $0.00 for currency)
            element.textContent = formatter(0);
            console.warn(`Value for element is undefined or null:`, value, ' Setting to default.');
        }
    } else {
        const identifier = typeof elementOrId === 'string' ? elementOrId : 'element object';
        console.error(`Element '${identifier}' not found`);
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

// Format number with thousands separators
export function formatNumber(number, decimals = 0) {
    if (typeof number !== 'number') {
        console.error('formatNumber called with non-number:', number);
        return '0';
    }

    return new Intl.NumberFormat('en-US', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    }).format(number);
}

// Detect mobile device
export function isMobile() {
    return window.innerWidth <= 767;
}

// Format loan amounts (rounded down to whole dollars)
export function formatLoanAmount(number) {
    return formatCurrency(number, { isLoanAmount: true });
}

// Smart formatting based on screen size
export function formatCurrencyResponsive(number, options = {}) {
    return formatCurrency(number, { ...options, compact: isMobile() });
}

// Format loan amounts responsively
export function formatLoanAmountResponsive(number) {
    return formatCurrency(number, { isLoanAmount: true, compact: isMobile() });
}

// Format purchase price (whole dollars, no decimals)
export function formatPurchasePrice(number) {
    if (typeof number !== 'number') {
        console.error('formatPurchasePrice called with non-number:', number);
        return '$0';
    }

    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(Math.round(number));
}

// Format purchase price responsively
export function formatPurchasePriceResponsive(number) {
    return formatCurrency(number, { precision: 0, compact: isMobile() });
}

// Format down payment (whole dollars, no decimals)
export function formatDownPayment(number) {
    if (typeof number !== 'number') {
        console.error('formatDownPayment called with non-number:', number);
        return '$0';
    }

    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(Math.round(number));
}

// Format down payment responsively
export function formatDownPaymentResponsive(number) {
    return formatCurrency(number, { precision: 0, compact: isMobile() });
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

// Utility: Safely parse a value as a number, defaulting to 0 if invalid
export function safeNumber(val) {
    const num = parseFloat(val);
    if (isNaN(num) || val === undefined || val === null) {
        return 0;
    }
    return num;
}
