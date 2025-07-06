# mortgage_insurance.py
import logging
from decimal import ROUND_HALF_UP, Decimal

# Set up module-level logger
logger = logging.getLogger(__name__)


def calculate_conventional_pmi(
    loan_amount: float, home_value: float, pmi_config: dict, logger: logging.Logger
) -> float:
    """Calculate monthly conventional Private Mortgage Insurance (PMI)."""
    try:
        if not pmi_config:
            logger.error("Conventional PMI rates configuration is missing")
            raise ValueError("Conventional PMI rates configuration is missing")

        ltv = round((loan_amount / home_value) * 100, 3)
        logger.info(f"Conventional loan PMI calculation: LTV={ltv:.3f}%")

        # No PMI needed if LTV is 80% or below
        if ltv <= 80:
            logger.info("LTV is 80% or below, no PMI required")
            return 0.0

        # Determine LTV rate
        ltv_ranges = pmi_config.get("ltv_ranges", {})
        if not ltv_ranges:
            logger.error("No LTV ranges defined for PMI calculation")
            raise ValueError("No LTV ranges defined for PMI calculation")

        ltv_rate = 0
        for ltv_range, rate in ltv_ranges.items():
            parts = ltv_range.split("-")
            if len(parts) == 2:
                min_ltv, max_ltv = float(parts[0]), float(parts[1])
                if min_ltv <= ltv <= max_ltv:
                    ltv_rate = rate / 100  # Convert from percentage to decimal
                    logger.info(
                        f"Selected LTV range for PMI: {ltv_range}%, rate: {round(rate, 3)}%"
                    )
                    break

        if ltv_rate == 0:
            logger.warning(f"No matching LTV range found for {ltv:.1f}%, using default rate")
            # Default to highest range if no match found
            highest_range = max(ltv_ranges.items(), key=lambda x: float(x[0].split("-")[0]))
            ltv_rate = highest_range[1] / 100
            logger.info(
                f"Using highest LTV range: {highest_range[0]}%, rate: {round(highest_range[1], 3)}%"
            )

        # Apply credit score adjustment (Currently hardcoded to 700 - consider passing if needed)
        # credit_score_adjustments = pmi_config.get("credit_score_adjustments", {})
        # credit_adjustment = 0
        # for score_range, adjustment in credit_score_adjustments.items():
        #     parts = score_range.split("-")
        #     if len(parts) == 2:
        #         min_score, max_score = int(parts[0]), int(parts[1])
        #         if min_score <= 700 <= max_score: # Placeholder credit score
        #             credit_adjustment = adjustment / 100
        #             logger.info(
        #                 f"Selected credit score range: {score_range}, adjustment: {adjustment}%"
        #             )
        #             break
        # As per MEMORY[384a733a-219d-4706-aaed-a7a8c8796c44], credit_score_adjustments are empty
        credit_adjustment = 0

        # Calculate final PMI rate and monthly amount
        annual_pmi_rate = ltv_rate + credit_adjustment
        monthly_pmi = (loan_amount * annual_pmi_rate) / 12

        rounded_pmi = round(monthly_pmi, 2)
        logger.info(f"Final monthly PMI for conventional loan: {rounded_pmi}")
        return rounded_pmi

    except Exception as e:
        logger.error(f"Error calculating conventional PMI: {e}")
        raise  # Re-raise the exception to be handled by the caller


def calculate_fha_mip(
    loan_amount: float,
    home_value: float,
    loan_term_months: int,
    mip_config: dict,
    logger: logging.Logger,
) -> float:
    """Calculate monthly FHA Mortgage Insurance Premium (MIP)."""
    try:
        if not mip_config:
            logger.error("FHA MIP rates configuration is missing")
            raise ValueError("FHA MIP rates configuration is missing")

        ltv = (loan_amount / home_value) * 100
        standard_loan_limit = mip_config.get(
            "standard_loan_limit", 726200
        )  # Default if not in config

        logger.info(
            f"Calculating FHA MIP with loan_term={loan_term_months / 12} years, loan_amount=${loan_amount:,.2f}, ltv={ltv:.2f}%"
        )

        # Determine term category
        term_category = "long_term" if loan_term_months / 12 > 15 else "short_term"
        logger.info(f"Using {term_category} FHA MIP rates.")

        # Determine amount category
        amount_category = "standard_amount" if loan_amount <= standard_loan_limit else "high_amount"
        logger.info(f"Using {amount_category} FHA MIP rates.")

        # Determine LTV category
        ltv_category = ""
        annual_mip_rate_config = (
            mip_config.get("annual_mip", {}).get(term_category, {}).get(amount_category, {})
        )

        if not annual_mip_rate_config:
            logger.warning(f"Missing FHA MIP rate config for {term_category}/{amount_category}")
            # Use a reasonable default based on term if specific config is missing
            annual_mip_rate = 0.55 if term_category == "long_term" else 0.40
        else:
            # Simplified logic based on common FHA rules
            if term_category == "long_term":
                if ltv <= 95:  # Typically one rate up to 95 LTV
                    ltv_category = "le_95"
                    logger.info("Using FHA MIP LTV rate <= 95%")
                else:  # Higher rate above 95 LTV
                    ltv_category = "gt_95"
                    logger.info("Using FHA MIP LTV rate > 95%")
            else:  # short_term (<= 15 years)
                # Often has a single rate regardless of LTV for shorter terms
                # Check if config specifies LTV breakdown, otherwise use a single key like 'all' or default
                if len(annual_mip_rate_config) == 1 and next(iter(annual_mip_rate_config)) in [
                    "all",
                    "default",
                ]:
                    ltv_category = next(iter(annual_mip_rate_config))
                    logger.info("Using single FHA MIP rate for short term loan")
                elif ltv <= 90:  # Or check common LTV threshold if specified
                    ltv_category = "le_90"
                    logger.info("Using FHA MIP short term LTV rate <= 90%")
                else:
                    ltv_category = "gt_90"
                    logger.info("Using FHA MIP short term LTV rate > 90%")

            annual_mip_rate = annual_mip_rate_config.get(ltv_category, 0)

            if annual_mip_rate == 0:
                logger.warning(
                    f"Could not find specific FHA MIP rate for {term_category}/{amount_category}/{ltv_category}. Using default."
                )
                # Fallback default rate
                annual_mip_rate = 0.55 if term_category == "long_term" else 0.40

        logger.info(f"Selected annual MIP rate: {annual_mip_rate}%")
        annual_mip_rate_decimal = annual_mip_rate / 100
        monthly_mip = (loan_amount * annual_mip_rate_decimal) / 12
        rounded_mip = round(monthly_mip, 2)
        logger.info(f"Final monthly MIP for FHA loan: ${rounded_mip:.2f}")
        return rounded_mip

    except Exception as e:
        logger.error(f"Error calculating FHA MIP: {e}")
        raise


def calculate_usda_fee(loan_amount: float, usda_config: dict, logger: logging.Logger) -> float:
    """Calculate monthly USDA guarantee fee."""
    try:
        if not usda_config:
            logger.error("USDA loan configuration is missing")
            raise ValueError("USDA loan configuration is missing")

        annual_fee_rate = usda_config.get("annual_fee_rate", 0.35) / 100  # Default if not in config
        monthly_fee = (loan_amount * annual_fee_rate) / 12
        rounded_fee = round(monthly_fee, 2)
        logger.info(f"Final monthly guarantee fee for USDA loan: ${rounded_fee:.2f}")
        return rounded_fee

    except Exception as e:
        logger.error(f"Error calculating USDA fee: {e}")
        raise
