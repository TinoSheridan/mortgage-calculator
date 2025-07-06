"""
constants.py - Shared constants for the mortgage calculator application.

This module contains enums and constants used throughout the application
to ensure consistency and avoid magic strings.
"""

from enum import Enum, auto


class TRANSACTION_TYPE(str, Enum):
    """
    Enum for mortgage transaction types.
    
    Using str as a base class ensures the enum values are serializable
    and can be easily converted to/from strings in API responses.
    """
    PURCHASE = "purchase"
    REFINANCE = "refinance"


class LOAN_TYPE(str, Enum):
    """
    Enum for mortgage loan types.
    """
    CONVENTIONAL = "conventional"
    FHA = "fha"
    VA = "va"
    USDA = "usda"


# ==============================================================================
# FINANCIAL CALCULATION CONSTANTS
# ==============================================================================

class CalculationConstants:
    """Constants used in mortgage and financial calculations."""
    
    # Interest calculation
    DAYS_IN_STANDARD_YEAR = 360  # Standard banking year for interest calculations
    DAYS_IN_CALENDAR_YEAR = 365  # Calendar year for property tax calculations
    MONTHS_IN_YEAR = 12
    
    # Standard loan terms
    DEFAULT_LOAN_TERM_MONTHS = 360  # 30 years
    DEFAULT_LOAN_TERM_YEARS = 30
    
    # Interest calculation defaults
    DEFAULT_PREPAID_INTEREST_DAYS = 30  # When no closing date provided


class ClosingCostConstants:
    """Constants for closing costs and fees."""
    
    # Standard closing cost fees (fallback values if not in config)
    DEFAULT_APPRAISAL_FEE = 675.0
    DEFAULT_CREDIT_REPORT_FEE = 249.0
    DEFAULT_VERIFICATION_FEE = 150.0
    DEFAULT_PROCESSING_FEE = 575.0
    DEFAULT_UNDERWRITING_FEE = 675.0
    DEFAULT_DOC_PREP_FEE = 115.0
    DEFAULT_ATTORNEY_FEE = 1200.0
    DEFAULT_RECORDING_FEE = 60.0
    DEFAULT_ADMIN_FEE = 125.0
    DEFAULT_STATE_TAX_STAMP = 300.0
    DEFAULT_THIRD_PARTY_CERTS = 55.0


class LTVConstants:
    """Constants related to Loan-to-Value ratios."""
    
    # Key LTV thresholds
    CONVENTIONAL_PMI_THRESHOLD = 80.0  # PMI required above this LTV
    HIGH_LTV_THRESHOLD = 90.0          # High LTV conventional loans
    MAXIMUM_CONVENTIONAL_LTV = 97.0     # Typical max for conventional
    MAXIMUM_FHA_LTV = 96.5             # FHA maximum LTV
    MAXIMUM_VA_LTV = 100.0             # VA allows 100% financing
    MAXIMUM_USDA_LTV = 100.0           # USDA allows 100% financing


class SellerContributionConstants:
    """Constants for seller contribution limits by loan type and LTV."""
    
    # Conventional loan seller contribution limits
    CONV_LOW_LTV_CONTRIBUTION = 0.09   # 9% for LTV ≤ 90%
    CONV_MID_LTV_CONTRIBUTION = 0.06   # 6% for 90% < LTV ≤ 95%
    CONV_HIGH_LTV_CONTRIBUTION = 0.03  # 3% for LTV > 95%
    
    # FHA loan seller contribution limits
    FHA_CONTRIBUTION_LIMIT = 0.06      # 6% for all FHA loans
    
    # VA loan seller contribution limits
    VA_CONTRIBUTION_LIMIT = 0.04       # 4% for all VA loans
    
    # USDA loan seller contribution limits
    USDA_CONTRIBUTION_LIMIT = 0.06     # 6% for all USDA loans


class TaxConstants:
    """Constants for property tax calculations."""
    
    # Georgia-specific tax calculation constants
    GEORGIA_ASSESSMENT_RATIO = 0.40    # Georgia assesses at 40% of fair market value
    GEORGIA_HOMESTEAD_EXEMPTION = 2000 # Standard homestead exemption
    
    # Tax calculation defaults
    DEFAULT_TAX_RATE = 0.012           # 1.2% default property tax rate
    DEFAULT_INSURANCE_RATE = 0.008     # 0.8% default insurance rate


class PMIConstants:
    """Constants for Private Mortgage Insurance calculations."""
    
    # PMI rate ranges (these would typically come from config, but serve as fallbacks)
    DEFAULT_PMI_RATE_80_85 = 0.0032    # 0.32% for 80-85% LTV
    DEFAULT_PMI_RATE_85_90 = 0.0052    # 0.52% for 85-90% LTV  
    DEFAULT_PMI_RATE_90_95 = 0.0067    # 0.67% for 90-95% LTV
    DEFAULT_PMI_RATE_95_97 = 0.0089    # 0.89% for 95-97% LTV


class FHAConstants:
    """Constants specific to FHA loans."""
    
    # FHA Mortgage Insurance Premium rates
    FHA_UPFRONT_MIP_RATE = 0.0175      # 1.75% upfront MIP
    FHA_ANNUAL_MIP_BASE_RATE = 0.0055  # Base annual MIP rate
    
    # FHA loan limits and requirements
    FHA_MIN_DOWN_PAYMENT = 0.035       # 3.5% minimum down payment
    FHA_MIN_CREDIT_SCORE = 580         # Minimum credit score for 3.5% down


class VAConstants:
    """Constants specific to VA loans."""
    
    # VA funding fee rates (by usage and down payment)
    VA_FUNDING_FEE_FIRST_USE_ZERO_DOWN = 0.023     # 2.30% for first use, no down
    VA_FUNDING_FEE_FIRST_USE_5_DOWN = 0.015        # 1.50% for first use, 5%+ down  
    VA_FUNDING_FEE_FIRST_USE_10_DOWN = 0.013       # 1.30% for first use, 10%+ down
    VA_FUNDING_FEE_SUBSEQUENT_ZERO_DOWN = 0.036    # 3.60% for subsequent use, no down
    VA_FUNDING_FEE_SUBSEQUENT_5_DOWN = 0.015       # 1.50% for subsequent use, 5%+ down
    VA_FUNDING_FEE_SUBSEQUENT_10_DOWN = 0.013      # 1.30% for subsequent use, 10%+ down


class USDAConstants:
    """Constants specific to USDA loans."""
    
    # USDA guarantee fee rates
    USDA_UPFRONT_GUARANTEE_FEE = 0.01   # 1% upfront guarantee fee
    USDA_ANNUAL_GUARANTEE_FEE = 0.0035  # 0.35% annual guarantee fee


# ==============================================================================
# VALIDATION CONSTANTS
# ==============================================================================

class ValidationConstants:
    """Constants for input validation."""
    
    # Loan amount limits
    MIN_LOAN_AMOUNT = 10000           # Minimum loan amount
    MAX_LOAN_AMOUNT = 50000000        # Maximum loan amount ($50M)
    
    # Interest rate limits  
    MIN_INTEREST_RATE = 0.0           # 0% (for edge case testing)
    MAX_INTEREST_RATE = 30.0          # 30% maximum
    
    # Down payment limits
    MIN_DOWN_PAYMENT_PCT = 0.0        # 0% (VA/USDA loans)
    MAX_DOWN_PAYMENT_PCT = 100.0      # 100% (cash purchases)
    
    # Loan term limits
    MIN_LOAN_TERM_YEARS = 1           # 1 year minimum
    MAX_LOAN_TERM_YEARS = 50          # 50 years maximum
    
    # Property value limits
    MIN_PROPERTY_VALUE = 10000        # $10,000 minimum
    MAX_PROPERTY_VALUE = 100000000    # $100M maximum


# ==============================================================================
# APPLICATION CONSTANTS
# ==============================================================================

class AppConstants:
    """General application constants."""
    
    # Version and branding
    DEFAULT_APP_NAME = "Enhanced Mortgage Calculator"
    
    # Session and security
    DEFAULT_SESSION_LIFETIME_DAYS = 7
    
    # File paths (relative to project root)
    CONFIG_DIR = "config"
    CLOSING_COSTS_FILE = "config/closing_costs.json"
    PMI_RATES_FILE = "config/pmi_rates.json"
    MORTGAGE_CONFIG_FILE = "config/mortgage_config.json"
    
    # Calculation precision
    CURRENCY_DECIMAL_PLACES = 2
    PERCENTAGE_DECIMAL_PLACES = 3
    LTV_DECIMAL_PLACES = 2
