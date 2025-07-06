import logging
from decimal import ROUND_HALF_UP, Decimal

logger = logging.getLogger(__name__)


def calculate_total_title_insurance(purchase_price: float, title_config: dict) -> float:
    """Calculate total title insurance premium using tiered rates from config."""
    try:
        logger.info(f"Calculating total title insurance for purchase price: ${purchase_price:,.2f}")
        purchase_price_d = Decimal(str(purchase_price))
        rate = Decimal("0.0")  # Default rate

        # Get rates from config, sort by 'up_to' threshold
        rate_tiers = sorted(
            title_config.get("total_rates_tiers", []),
            key=lambda x: x.get("up_to") if x.get("up_to") is not None else float("inf"),
        )

        if not rate_tiers:
            logger.warning("No total_rates_tiers found in title_insurance config.")
            return 0.0

        # Find the correct rate based on purchase price
        for tier in rate_tiers:
            threshold = tier.get("up_to")
            tier_rate = Decimal(str(tier.get("rate_percentage", 0))) / Decimal("100")
            if threshold is None or purchase_price_d <= Decimal(str(threshold)):
                rate = tier_rate
                break
        else:
            # If purchase price exceeds all defined 'up_to' values, use the last tier's rate
            rate = Decimal(str(rate_tiers[-1].get("rate_percentage", 0))) / Decimal("100")

        base_premium_d = purchase_price_d * rate

        # Get flat fee from config, default to 150.00 if not found
        flat_fee_d = Decimal(str(title_config.get("simultaneous_issuance_fee", 150.00)))
        total_premium_d = base_premium_d + flat_fee_d

        logger.info(
            f"Total title insurance: ${total_premium_d:.2f} "
            + f"(base=${base_premium_d:.2f} at rate={rate:.5f}, flat fee=${flat_fee_d:.2f})"
        )

        # Round to 2 decimal places
        rounded_premium = float(total_premium_d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
        return rounded_premium

    except Exception as e:
        logger.error(f"Error calculating total title insurance: {e}")
        return 0.0


def calculate_lenders_title_insurance(
    loan_amount: float, include_owners_title: bool, title_config: dict
) -> float:
    """
    Calculate lender's title insurance using tiered rates.
    If owner's title insurance is included, this gets a discount (lower rate).
    If owner's title is waived, full rate applies (or a higher rate).
    """
    # NOTE: Reads rates and multiplier from title_config dictionary.
    try:
        loan_amount_d = Decimal(str(loan_amount))
        logger.info(
            f"Calculating lender's title insurance for loan amount: ${loan_amount_d:,.2f}, include_owners_title={include_owners_title}"
        )

        rate_d = Decimal("0.0")  # Default rate

        # Get rates from config, sort by 'up_to' threshold
        # Assumes structure like: title_config['lender_rates_simultaneous_tiers']
        rate_tiers = sorted(
            title_config.get("lender_rates_simultaneous_tiers", []),
            key=lambda x: x.get("up_to") if x.get("up_to") is not None else float("inf"),
        )

        if not rate_tiers:
            logger.warning("No lender_rates_simultaneous_tiers found in title_insurance config.")
            # Fallback to simpler logic or return 0? For now, return 0.
            return 0.0

        # Find the correct rate based on loan amount
        for tier in rate_tiers:
            threshold = tier.get("up_to")
            tier_rate = Decimal(str(tier.get("rate_percentage", 0))) / Decimal("100")
            if threshold is None or loan_amount_d <= Decimal(str(threshold)):
                rate_d = tier_rate
                break
        else:
            # If loan amount exceeds all defined 'up_to' values, use the last tier's rate
            rate_d = Decimal(str(rate_tiers[-1].get("rate_percentage", 0))) / Decimal("100")

        # If owner's title is not included, apply the waiver multiplier from config
        if not include_owners_title:
            waiver_multiplier_d = Decimal(
                str(title_config.get("lender_rate_waiver_multiplier", 1.25))
            )
            rate_d *= waiver_multiplier_d
            logger.info(
                f"Applied waiver multiplier ({waiver_multiplier_d}), new rate: {rate_d:.5f}"
            )

        lenders_title_d = loan_amount_d * rate_d

        # Round to 2 decimal places
        rounded_premium = float(lenders_title_d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

        logger.info(
            f"Lender's title insurance: ${rounded_premium:.2f} (rate={rate_d:.5f}, "
            + f"discount={(include_owners_title and 'Applied' or 'Not Applied')})"
        )

        return rounded_premium

    except Exception as e:
        logger.error(f"Error calculating lender's title insurance: {e}")
        return 0.0


def calculate_owners_title_insurance(
    purchase_price: float,
    loan_amount: float,
    include_owners_title: bool,
    title_config: dict,
) -> float:
    """
    Calculate owner's title insurance.
    If owner's title insurance is included, it's the difference between
    the total premium and the discounted lender's premium.
    If waived, it's 0.
    """
    # NOTE: Calls other functions which now read from title_config.
    try:
        # If owner's title is waived, return 0
        if not include_owners_title:
            logger.info("Owner's title insurance waived, returning 0.0")
            return 0.0

        # Owner's title is the difference between total title and lender's title (with discount)
        # Use Decimal for intermediate calculations
        total_title_d = Decimal(str(calculate_total_title_insurance(purchase_price, title_config)))
        # Ensure we calculate lender's title *with* the discount applied for this calculation
        lenders_title_discounted_d = Decimal(
            str(
                calculate_lenders_title_insurance(
                    loan_amount, include_owners_title=True, title_config=title_config
                )
            )
        )

        owners_title_d = total_title_d - lenders_title_discounted_d

        # Ensure non-negative result
        owners_title_d = max(Decimal("0.0"), owners_title_d)

        # Round to 2 decimal places
        rounded_premium = float(owners_title_d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

        logger.info(
            f"Owner's title insurance: ${rounded_premium:.2f} (from total ${total_title_d:.2f} - discounted lender's ${lenders_title_discounted_d:.2f})"
        )

        return rounded_premium

    except Exception as e:
        logger.error(f"Error calculating owner's title insurance: {e}")
        return 0.0
