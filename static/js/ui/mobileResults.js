// Mobile-optimized results display
import { formatCurrency, formatCurrencyResponsive, formatLoanAmountResponsive, isMobile } from '../utils/formatting.js';

// Create compact mobile results summary
export function createMobileResultsSummary(results) {
    if (!isMobile()) return null;

    const summaryHtml = `
        <div class="results-compact">
            <div class="highlight">
                Monthly Payment: ${formatCurrencyResponsive(results.monthly_breakdown?.total || 0)}
            </div>
            <div class="secondary">
                P&I: ${formatCurrencyResponsive(results.monthly_breakdown?.principal_interest || 0)} •
                Tax: ${formatCurrencyResponsive(results.monthly_breakdown?.property_tax || 0)} •
                Insurance: ${formatCurrencyResponsive(results.monthly_breakdown?.home_insurance || 0)}
                ${results.monthly_breakdown?.mortgage_insurance > 0 ? ` • PMI: ${formatCurrencyResponsive(results.monthly_breakdown.mortgage_insurance)}` : ''}
            </div>
            ${results.total_cash_needed ? `
                <div class="highlight mt-2">
                    Cash to Close: ${formatCurrencyResponsive(results.total_cash_needed)}
                </div>
            ` : ''}
        </div>
    `;

    return summaryHtml;
}

// Create compact table for mobile
export function createMobileTable(data, title) {
    if (!isMobile()) return null;

    const rows = Object.entries(data)
        .filter(([key, value]) => value !== 0 && value !== null && value !== undefined)
        .map(([key, value]) => {
            const label = key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
            return `
                <div class="mobile-table-row">
                    <span class="label">${label}</span>
                    <span class="value">${formatCurrencyResponsive(value)}</span>
                </div>
            `;
        }).join('');

    return `
        <div class="mobile-table">
            <div class="mobile-table-header">${title}</div>
            ${rows}
        </div>
    `;
}

// Optimize existing tables for mobile
export function optimizeTablesForMobile() {
    if (!isMobile()) return;

    // Add mobile classes to tables
    document.querySelectorAll('.table').forEach(table => {
        table.classList.add('table-mobile-optimized');

        // Simplify table structure for mobile
        const rows = table.querySelectorAll('tbody tr');
        rows.forEach(row => {
            const cells = row.querySelectorAll('td');
            if (cells.length >= 2) {
                const label = cells[0].textContent.trim();
                const value = cells[1].textContent.trim();

                // Shorten labels for mobile
                if (label.length > 20) {
                    cells[0].textContent = abbreviateLabel(label);
                    cells[0].title = label; // Full text in tooltip
                }
            }
        });
    });
}

// Abbreviate labels for mobile display
function abbreviateLabel(label) {
    const abbreviations = {
        'Principal & Interest': 'P&I',
        'Property Tax': 'Taxes',
        'Home Insurance': 'Insurance',
        'Mortgage Insurance': 'PMI',
        'HOA Fee': 'HOA',
        'Lender\'s Title Insurance': 'Lender Title',
        'Owner\'s Title Insurance': 'Owner Title',
        'Origination Fee': 'Origination',
        'Processing Fee': 'Processing',
        'Underwriting Fee': 'Underwriting',
        'Appraisal Fee': 'Appraisal',
        'Credit Report Fee': 'Credit Report',
        'Attorney\'s Fee': 'Attorney',
        'Recording Fee': 'Recording',
        'State Tax/Stamps': 'State Tax',
        'Homeowner\'s Insurance Premium': 'Insurance Premium',
        'Per Diem Interest': 'Per Diem',
        'Total Monthly Payment': 'Total Payment',
        'Total Closing Costs': 'Total Closing',
        'Total Prepaid Items': 'Total Prepaids',
        'Total Cash to Close': 'Cash to Close'
    };

    return abbreviations[label] || (label.length > 20 ? label.substring(0, 17) + '...' : label);
}

// Create sticky mobile action bar
export function createMobileActionBar() {
    // Mobile action bar functionality has been removed
    return;
}

// Show toast message
function showToast(message) {
    const toast = document.createElement('div');
    toast.className = 'toast-message';
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        bottom: 100px;
        left: 50%;
        transform: translateX(-50%);
        background: #333;
        color: white;
        padding: 0.75rem 1rem;
        border-radius: 6px;
        z-index: 1000;
        font-size: 0.9rem;
    `;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// Initialize mobile optimizations
export function initializeMobileOptimizations() {
    if (!isMobile()) return;

    // Add mobile-specific CSS class to body
    document.body.classList.add('mobile-device');

    // Optimize existing content
    optimizeTablesForMobile();

    // Create action bar
    createMobileActionBar();

    // Add viewport-specific styles
    const mobileStyles = document.createElement('style');
    mobileStyles.textContent = `
        .mobile-table {
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 1rem;
            overflow: hidden;
        }

        .mobile-table-header {
            background: #f8f9fa;
            padding: 0.75rem;
            font-weight: 600;
            border-bottom: 1px solid #dee2e6;
        }

        .mobile-table-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.5rem 0.75rem;
            border-bottom: 1px solid #f1f3f4;
        }

        .mobile-table-row:last-child {
            border-bottom: none;
        }

        .mobile-table-row .label {
            flex: 1;
            font-weight: 500;
            color: #495057;
        }

        .mobile-table-row .value {
            font-family: 'SF Mono', Monaco, monospace;
            font-weight: 600;
            color: #198754;
        }

        .mobile-action-bar {
            display: flex;
            justify-content: center;
            gap: 0.5rem;
        }

        .table-mobile-optimized {
            font-size: 0.85rem;
        }

        .table-mobile-optimized td {
            padding: 0.4rem 0.2rem;
        }

        .toast-message {
            animation: slideUp 0.3s ease-out;
        }

        @keyframes slideUp {
            from {
                opacity: 0;
                transform: translateX(-50%) translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateX(-50%) translateY(0);
            }
        }
    `;

    document.head.appendChild(mobileStyles);
}
