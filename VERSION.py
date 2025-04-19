"""
Version information for the Mortgage Calculator application.

This file helps track which version is deployed and what features are included.
"""

from datetime import date

# Main application version
VERSION = "2.1.0"  # New version: always show origination fee, discount points, and both title insurance rows in closing costs

# Date of the last update
# Format: YYYY-MM-DD
LAST_UPDATED = date(2025, 4, 19)  # Updated date

# Description of the last update
UPDATE_DESCRIPTION = "UI refactor: Always show Origination Fee, Discount Points, Lender's and Owner's Title Insurance in closing costs table, even if zero. Improved order and clarity."


def get_version_info():
    """Return a dictionary containing version information."""
    return {
        "version": VERSION,
        "last_updated": LAST_UPDATED.strftime("%Y-%m-%d"),
        "description": UPDATE_DESCRIPTION,
    }


# Function to get just the version string
def get_version():
    """Return just the version string."""
    return VERSION


FEATURES = [
    "seller_credits",
    "lender_credits",
    "va_seller_contribution_limits",
    "conventional_seller_limits",
    "robust_form_submission",
    "cross_environment_csrf_protection",
    "admin_closing_costs_fix",
    "three_decimal_percentages",
    "unrestricted_closing_cost_inputs",
    "tax_escrow_december_adjustment",
    "georgia_property_tax_formula",
    "updated_default_rates",
    "enhanced_summary_formatting",
    "dynamic_prepaid_tax_calculation",
]
