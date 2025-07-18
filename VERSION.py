"""
Version information for the Mortgage Calculator application.

This file helps track which version is deployed and what features are included.
"""

from datetime import date

# Main application version
VERSION = "2.6.2"  # Added comprehensive Property Intelligence system with Spokeo integration

# Date of the last update
# Format: YYYY-MM-DD
LAST_UPDATED = date(2025, 1, 18)  # Updated date

# Description of the last update
UPDATE_DESCRIPTION = "Added comprehensive Property Intelligence system with Spokeo API integration, real-time property analysis popup, address copying functionality, honest data presentation (no test data), and integration with USDA and FEMA APIs for accurate property information."


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
    "refinance_ltv_fix",  # v2.5.0: Fixed LTV > 80% validation that incorrectly blocked refinances
    "ltv_information_card",  # v2.5.0: Comprehensive LTV guidance with accurate appraised value targets
    "zero_cash_ltv_calculations",  # v2.5.0: LTV calculations based on new loan amount including costs
    "actual_current_balance_integration",  # v2.5.0: Uses calculated current balance for 99.9% accuracy
    "conservative_ltv_rounding",  # v2.5.0: Rounds appraised values up to nearest thousand
    "accurate_ltv_backend_calculations",  # v2.6.0: Fixed frontend LTV calculations to use backend values
    "dynamic_max_ltv_targets",  # v2.6.0: Calculates maximum LTV based on loan type and refinance type
    "enhanced_cash_out_refinance_logic",  # v2.6.0: Improved cash-out refinance calculations
    "hoa_fee_integration",  # v2.6.0: Added HOA fee input and calculation integration
    "refined_ui_labels",  # v2.6.0: Improved LTV targets table labels and formatting
    "property_intelligence_system",  # v2.6.2: Comprehensive property analysis popup with real API integration
    "spokeo_api_integration",  # v2.6.2: Primary data source for property details and tax information
    "usda_eligibility_api",  # v2.6.2: Real-time USDA rural development eligibility checking
    "fema_flood_zone_api",  # v2.6.2: Official FEMA flood zone determination
    "property_address_copying",  # v2.6.2: One-click address copying for manual verification
    "honest_data_presentation",  # v2.6.2: Shows "Unknown" instead of test data, provides verification links
    "property_source_links",  # v2.6.2: Direct links to Spokeo, QPublic, county assessors for manual verification
]
