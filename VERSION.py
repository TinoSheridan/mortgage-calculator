"""
Version information for the Mortgage Calculator application.

This file helps track which version is deployed and what features are included.
"""

from datetime import date

# Main application version
VERSION = "2.8.1"  # Fixed admin validation for fixed closing costs + multi-tenant system

# Date of the last update
# Format: YYYY-MM-DD
LAST_UPDATED = date(2025, 9, 2)  # Updated date

# Description of the last update
UPDATE_DESCRIPTION = "CRITICAL ADMIN FIX: Fixed admin validation error preventing updates to fixed closing costs. Added 'fixed' to valid calculation_base options allowing updates to appraisal fees, processing fees, etc. Updated closing costs: processing_fee=$650, doc_prep=$240. Includes all v2.8.0 multi-tenant features."


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
    "target_ltv_input_fix",  # v2.6.3: Fixed target LTV input field not appearing when selected in refinance options
    "multi_tenant_database_system",  # v2.8.0: PostgreSQL-based multi-tenant system with user/organization isolation
    "hierarchical_admin_system",  # v2.8.0: Super Admin, Organization Admin, and Individual User role levels
    "configuration_inheritance",  # v2.8.0: Global -> Organization -> User configuration inheritance system
    "user_customization_preservation",  # v2.8.0: User customizations preserved during version control updates
    "flask_login_authentication",  # v2.8.0: Secure user authentication with Flask-Login and bcrypt
    "role_based_access_control",  # v2.8.0: RBAC system with proper permission boundaries
    "database_migration_support",  # v2.8.0: Automated migration from file-based to database configuration
    "admin_fixed_cost_validation_fix",  # v2.8.1: Fixed admin validation to allow updates to fixed closing costs
]
