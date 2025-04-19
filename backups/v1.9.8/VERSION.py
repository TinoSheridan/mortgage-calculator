"""
Version information for the Mortgage Calculator application.
This file helps track which version is deployed and what features are included.
"""

VERSION = "1.9.8"  # Fixed max seller contribution display to show the correct value consistently with the credits section
LAST_UPDATED = "2025-03-25"
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
]
