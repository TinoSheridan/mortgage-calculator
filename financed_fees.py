# financed_fees.py
import logging
from typing import Dict


def calculate_fha_ufmip(
    loan_amount: float, fha_config: Dict, logger: logging.Logger
) -> float:
    """Calculate FHA Upfront Mortgage Insurance Premium (UFMIP)."""
    try:
        if not fha_config:
            logger.error(
                "FHA configuration (pmi_rates.fha) not found for UFMIP calculation"
            )
            raise ValueError("FHA configuration not found for UFMIP calculation")

        upfront_mip_rate = (
            fha_config.get("upfront_mip_rate", 1.75) / 100
        )  # Default 1.75%
        upfront_mip = loan_amount * upfront_mip_rate
        total_financed_fees = round(upfront_mip, 2)
        logger.info(
            f"FHA upfront MIP calculated: ${total_financed_fees:.2f} (rate: {upfront_mip_rate * 100}%)"
        )
        return total_financed_fees
    except Exception as e:
        logger.error(f"Error calculating FHA UFMIP: {e}")
        raise  # Re-raise the exception


def calculate_usda_upfront_fee(
    loan_amount: float, usda_config: Dict, logger: logging.Logger
) -> float:
    """Calculate USDA Upfront Guarantee Fee."""
    try:
        if not usda_config:
            logger.error(
                "USDA configuration (loan_types.usda) not found for upfront fee calculation"
            )
            raise ValueError("USDA configuration not found for upfront fee calculation")

        upfront_fee_rate = (
            usda_config.get("upfront_fee_rate", 1.0) / 100
        )  # Default 1.0%
        upfront_fee = loan_amount * upfront_fee_rate
        total_financed_fees = round(upfront_fee, 2)
        logger.info(
            f"USDA upfront guarantee fee calculated: ${total_financed_fees:.2f} (rate: {upfront_fee_rate * 100}%)"
        )
        return total_financed_fees
    except Exception as e:
        logger.error(f"Error calculating USDA upfront fee: {e}")
        raise  # Re-raise the exception


def calculate_va_funding_fee(
    loan_amount: float,
    down_payment_percentage: float,
    service_type: str,
    loan_usage: str,
    disability_exempt: bool,
    va_config: Dict,  # Pass relevant VA config section
    logger: logging.Logger,
) -> float:
    """
    Calculate the VA funding fee based on loan amount, down payment, service type, and loan usage.

    Args:
        loan_amount (float): The loan amount
        down_payment_percentage (float): Down payment percentage (0-100)
        service_type (str): 'active' for active duty, 'reserves' for reserves/guard
        loan_usage (str): 'first' for first-time use, 'subsequent' for subsequent use
        disability_exempt (bool): Whether the borrower is exempt from funding fee due to disability
        va_config (Dict): Configuration dictionary specifically for VA loans (e.g., from loan_types.va)
        logger (logging.Logger): Logger instance

    Returns:
        float: The VA funding fee amount
    """
    # If disability exempt, return 0
    if disability_exempt:
        logger.info("VA funding fee exemption applied due to disability status")
        return 0.0

    logger.info(
        f"Calculating VA funding fee with loan_amount=${loan_amount:,.2f}, "
        f"down_payment_percentage={down_payment_percentage}%, "
        f"service_type={service_type}, loan_usage={loan_usage}, "
        f"disability_exempt={disability_exempt}"
    )

    try:
        # Get funding fee rates from the passed config
        funding_fee_rates = va_config.get("funding_fee_rates", {})
        if not funding_fee_rates:
            logger.error("VA funding_fee_rates not found in provided VA config")
            raise ValueError("VA funding_fee_rates not found in VA config")

        logger.debug(f"Funding fee rates from config: {funding_fee_rates}")

        # Normalize inputs to prevent errors
        service_type = str(service_type).lower() if service_type else "active"
        loan_usage = str(loan_usage).lower() if loan_usage else "first"

        # Validate service type
        if service_type not in ["active", "reserves"]:
            logger.warning(
                f"Invalid service type: {service_type}. Defaulting to 'active'"
            )
            service_type = "active"

        # Validate loan usage
        if loan_usage not in ["first", "subsequent"]:
            logger.warning(f"Invalid loan usage: {loan_usage}. Defaulting to 'first'")
            loan_usage = "first"

        # Determine down payment bracket
        if down_payment_percentage < 5:
            dp_bracket = "less_than_5"
        elif down_payment_percentage < 10:
            dp_bracket = "5_to_10"
        else:
            dp_bracket = "10_or_more"

        logger.info(f"Selected down payment bracket: {dp_bracket}")

        # Get the service type rates
        # Structure assumed: funding_fee_rates -> funding_fee -> service_type -> dp_bracket -> loan_usage
        service_rates = funding_fee_rates.get("funding_fee", {}).get(service_type)
        if not service_rates:
            logger.error(f"No funding fee rates found for service type: {service_type}")
            # Fallback strategy: Use 'active' if primary type not found
            service_rates = funding_fee_rates.get("funding_fee", {}).get("active", {})
            logger.info(f"Falling back to 'active' service rates")
            if not service_rates:  # Still not found? Raise error.
                raise ValueError(
                    f"Could not find VA funding fee rates for service type '{service_type}' or fallback 'active'"
                )

        logger.info(f"Service rates found: {service_rates}")

        # Get bracket rates
        bracket_rates = service_rates.get(dp_bracket)
        if not bracket_rates:
            logger.error(
                f"No funding fee rates found for down payment bracket: {dp_bracket}"
            )
            # Fallback strategy: Use 'less_than_5' if primary bracket not found
            bracket_rates = service_rates.get("less_than_5", {})
            logger.info(f"Falling back to 'less_than_5' bracket rates")
            if not bracket_rates:  # Still not found? Raise error.
                raise ValueError(
                    f"Could not find VA funding fee rates for DP bracket '{dp_bracket}' or fallback 'less_than_5'"
                )

        logger.info(f"Bracket rates found: {bracket_rates}")

        # Get fee rate based on loan usage
        fee_rate = bracket_rates.get(loan_usage)
        if fee_rate is None:
            logger.error(
                f"No funding fee rate found for loan usage: {loan_usage} in bracket {dp_bracket}"
            )
            # Fallback strategy: Use 'first' if primary usage not found
            fee_rate = bracket_rates.get("first")
            logger.info(f"Falling back to 'first' fee rate")
            if fee_rate is None:  # Still not found? Raise error.
                raise ValueError(
                    f"Could not find VA funding fee rate for usage '{loan_usage}' or fallback 'first'"
                )

        logger.info(
            f"Fee rate lookup for {service_type}, {dp_bracket}, {loan_usage}: {fee_rate}"
        )

        # Calculate fee
        fee = loan_amount * (fee_rate / 100)
        logger.info(
            f"Calculated VA funding fee: ${fee:.2f} (rate: {fee_rate}%, loan_amount: ${loan_amount:.2f})"
        )

        return round(fee, 2)  # Ensure rounded value

    except Exception as e:
        logger.error(f"Error calculating VA funding fee: {e}")
        logger.error(
            f"Parameters: loan_amount=${loan_amount}, down_payment={down_payment_percentage}%, "
            f"service_type={service_type}, loan_usage={loan_usage}, disability_exempt={disability_exempt}"
        )
        # Default to 2.3% (common first-time use rate for active duty, <5% down) as fallback
        # only if not disability exempt
        if not disability_exempt:
            default_fee = loan_amount * 0.023
            logger.warning(
                f"Using default fee calculation due to error: ${default_fee:.2f} (2.3%)"
            )
            return round(default_fee, 2)
        else:
            # Should have been caught earlier, but safety check
            logger.info(
                "VA Funding Fee is 0 due to disability exemption (error fallback check)."
            )
            return 0.0
