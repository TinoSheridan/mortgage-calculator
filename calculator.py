"""
calculator.py - Mortgage calculation engine for the application.

Provides the MortgageCalculator class and related logic for all loan calculations.
"""

import logging
import math
from calendar import monthrange  # Import monthrange
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Dict, Optional, Union

from calculations.title_insurance import (
    calculate_lenders_title_insurance,
    calculate_owners_title_insurance,
)
from config_manager import ConfigManager
from constants import LOAN_TYPE, TRANSACTION_TYPE, CalculationConstants
from financed_fees import calculate_fha_ufmip, calculate_usda_upfront_fee
from financed_fees import calculate_va_funding_fee as calculate_external_va_funding_fee
from mortgage_insurance import calculate_conventional_pmi, calculate_fha_mip, calculate_usda_fee


class MortgageCalculator:
    """
    MortgageCalculator provides methods to compute mortgage payments, insurance, closing costs, and related values.
    """

    def __init__(self):
        """
        Initialize the MortgageCalculator with config and logger.
        """
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing MortgageCalculator.")
        self.config_manager = ConfigManager()
        self.config = self.config_manager.get_config()
        self.logger.info("Loaded configuration.")

    def calculate_monthly_payment(self, principal: float, annual_rate: float, years: int) -> float:
        """
        Calculate the monthly mortgage payment using Decimal for precision.

        Args:
            principal (float): The initial amount borrowed.
            annual_rate (float): The annual interest rate (in percent).
            years (int): The number of years the money is borrowed for.

        Returns:
            float: The monthly payment amount.
        """
        try:
            principal_d = Decimal(str(principal))
            annual_rate_d = Decimal(str(annual_rate))
            years_d = Decimal(str(years))
            self.logger.info(
                f"Calculating monthly payment: principal={principal_d}, rate={annual_rate_d.quantize(Decimal('0.001'))}, years={years_d}."
            )
            if annual_rate_d == Decimal("0"):
                payment_d = (principal_d / (years_d * Decimal("12"))).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
                self.logger.info(f"Zero interest rate, monthly payment: {payment_d}.")
                return float(payment_d)
            monthly_rate_d = annual_rate_d / Decimal("12") / Decimal("100")
            num_payments_d = years_d * Decimal("12")
            if monthly_rate_d == Decimal("0"):
                payment_d = (principal_d / num_payments_d).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
            else:
                factor = (Decimal("1") + monthly_rate_d) ** num_payments_d
                payment_d = principal_d * (monthly_rate_d * factor) / (factor - Decimal("1"))
            rounded_payment_d = payment_d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            self.logger.info(f"Monthly payment calculated: {rounded_payment_d}.")
            return float(rounded_payment_d)
        except Exception as e:
            self.logger.error(f"Error calculating monthly payment: {e}.")
            raise

    def calculate_mortgage_insurance(
        self,
        loan_amount: float,
        home_value: float,
        loan_type: str,
        loan_term_months: int = CalculationConstants.DEFAULT_LOAN_TERM_MONTHS,
    ) -> float:
        """
        Calculate monthly mortgage insurance based on loan type, loan amount, and LTV. Dispatches to specific calculation functions.

        Args:
            loan_amount (float): Amount being borrowed.
            home_value (float): Total value/purchase price of the home.
            loan_type (str): Type of loan ('conventional', 'fha', 'va', 'usda').
            loan_term_months (int): Loan term in months.

        Returns:
            float: Monthly mortgage insurance premium.
        """
        try:
            self.logger.info(
                f"Calculating mortgage insurance: loan_amount=${loan_amount:,.0f}, "
                f"home_value=${home_value:,.0f}, loan_type={loan_type}."
            )

            loan_type = loan_type.lower()
            # Get relevant configurations
            pmi_rates_config = self.config.get("pmi_rates", {})
            loan_types_config = self.config.get("loan_types", {})

            if loan_type == "conventional":
                conventional_config = pmi_rates_config.get("conventional", {})
                return calculate_conventional_pmi(
                    loan_amount, home_value, conventional_config, self.logger
                )

            elif loan_type == "fha":
                fha_config = pmi_rates_config.get("fha", {})
                return calculate_fha_mip(
                    loan_amount, home_value, loan_term_months, fha_config, self.logger
                )

            elif loan_type == "usda":
                # USDA annual fee might be in loan_types config
                usda_config = loan_types_config.get("usda", {})
                return calculate_usda_fee(loan_amount, usda_config, self.logger)

            elif loan_type == "va":
                self.logger.info("VA loans do not have monthly mortgage insurance, returning 0.")
                return 0.0

            else:
                # Handle unknown or types without monthly MI
                self.logger.info(
                    f"No monthly mortgage insurance configured or needed for loan type: {loan_type}."
                )
                return 0.0

        except Exception as e:
            # Log the error originating from this dispatcher or re-raised from helpers
            self.logger.error(f"Error calculating mortgage insurance: {e}.")
            raise  # Re-raise to allow higher-level handling

    def calculate_financed_fees(
        self,
        loan_type: str,
        loan_amount: float,
        down_payment_percentage: float = 0.0,
        va_service_type: Optional[str] = None,
        va_usage: Optional[str] = None,
        va_disability_exempt: Optional[bool] = None,
    ) -> float:
        """
        Calculate financed fees (e.g., FHA UFMIP, VA funding fee) to be added to the loan amount.

        Args:
            loan_type (str): Loan type ('conventional', 'fha', 'va', 'usda').
            loan_amount (float): Amount being borrowed.
            down_payment_percentage (float, optional): Down payment as a percentage.
            va_service_type (str, optional): VA service type.
            va_usage (str, optional): VA loan usage.
            va_disability_exempt (bool, optional): VA disability exemption.

        Returns:
            float: Total financed fees to be added to the loan.
        """
        try:
            self.logger.info(
                f"Calculating financed fees: loan_type={loan_type}, loan_amount=${loan_amount:,.2f}."
            )
            loan_type = loan_type.lower()

            # Fetch relevant config sections needed by helper functions
            pmi_rates_config = self.config.get("pmi_rates", {})
            loan_types_config = self.config.get("loan_types", {})

            if loan_type == "conventional":
                self.logger.info("No upfront financed fees for conventional loans.")
                return 0.0

            elif loan_type == "fha":
                fha_config = pmi_rates_config.get("fha", {})
                return calculate_fha_ufmip(loan_amount, fha_config, self.logger)

            elif loan_type == "va":
                # Ensure defaults for VA params if not provided
                va_service_type = va_service_type if va_service_type else "active"
                va_usage = va_usage if va_usage else "first"
                va_disability_exempt = (
                    va_disability_exempt if va_disability_exempt is not None else False
                )

                self.logger.info(
                    f"Dispatching VA funding fee calculation: service_type={va_service_type}, "
                    f"va_usage={va_usage}, disability_exempt={va_disability_exempt}."
                )

                va_config = pmi_rates_config.get("va", {})  # Get VA specific config from pmi_rates
                total_financed_fees = calculate_external_va_funding_fee(  # Call imported function
                    loan_amount,
                    down_payment_percentage,
                    va_service_type,
                    va_usage,
                    va_disability_exempt,
                    va_config,
                    self.logger,
                )
                # Log result (previously inside the old calculate_financed_fees)
                self.logger.info(f"VA funding fee result: ${total_financed_fees: .2f}.")
                return total_financed_fees

            elif loan_type == "usda":
                usda_config = loan_types_config.get("usda", {})
                return calculate_usda_upfront_fee(loan_amount, usda_config, self.logger)

            else:
                self.logger.warning(
                    f"Unknown loan type '{loan_type}' encountered when calculating financed fees."
                )
                return 0.0  # No fees for unknown types

        except Exception as e:
            self.logger.error(f"Error calculating financed fees dispatch: {e}.")
            # Log specific parameters that might be relevant
            self.logger.error(
                f"Parameters at time of error: loan_type={loan_type}, loan_amount={loan_amount}, dp%={down_payment_percentage}, va_service={va_service_type}, va_usage={va_usage}, va_exempt={va_disability_exempt}."
            )
            raise  # Re-raise after logging context

    def calculate_all(
        self,
        purchase_price: float,
        down_payment_percentage: float = 0,
        down_payment: Optional[float] = None,
        annual_rate: float = 6.5,
        loan_term: int = 30,
        annual_tax_rate: float = 1.25,
        annual_insurance_rate: float = 0.35,
        loan_type: Union[str, LOAN_TYPE] = "conventional",
        monthly_hoa_fee: float = 0.0,
        seller_credit: float = 0.0,
        lender_credit: float = 0.0,
        discount_points: float = 0.0,
        va_service_type: Optional[str] = None,
        va_usage: Optional[str] = None,
        va_disability_exempt: Optional[bool] = None,
        closing_date: Optional[date] = None,
        include_owners_title: bool = True,
        transaction_type: Union[str, TRANSACTION_TYPE] = TRANSACTION_TYPE.PURCHASE,
        # Tax and insurance method overrides
        tax_method: str = "percentage",
        insurance_method: str = "percentage",
        annual_tax_amount: float = 0.0,
        annual_insurance_amount: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Calculate full mortgage details with all components.

        Args:
            purchase_price (float): Purchase price of the home ($).
            down_payment_percentage (float, optional): Down payment as percentage of purchase price (%).
            down_payment (float, optional): Down payment amount ($) - Deprecated, use down_payment_percentage instead.
            annual_rate (float): Annual interest rate (%).
            loan_term (int): Loan term in years.
            annual_tax_rate (float): Annual property tax rate (%).
            annual_insurance_rate (float): Annual home insurance rate (%).
            loan_type (str): Type of loan ('conventional', 'fha', 'va', 'usda').
            monthly_hoa_fee (float, optional): Monthly HOA fee ($).
            seller_credit (float, optional): Seller credit toward closing costs ($).
            lender_credit (float, optional): Lender credit toward closing costs ($).
            discount_points (float, optional): Discount points to buy down the rate (%).
            va_service_type (str, optional): For VA loans, type of service ('active' or 'reserves').
            va_usage (str, optional): For VA loans, loan usage ('first' or 'subsequent').
            va_disability_exempt (bool, optional): For VA loans, whether exempt from funding fee.
            closing_date (date, optional): Closing date for prepaid interest calculation.
            include_owners_title (bool, optional): Whether to include owner's title insurance.

        Returns:
            Dict[str, Any]: Dictionary with calculated mortgage details.
        """
        try:
            self.logger.info(
                f"Calculating all: price={purchase_price}, dp%={down_payment_percentage}, "
                f"rate={annual_rate}%, term={loan_term}y, type={loan_type}, tax={annual_tax_rate}%, ins={annual_insurance_rate}%. "
            )

            # Ensure closing date has the right type
            if closing_date and isinstance(closing_date, str):
                try:
                    self.logger.info(
                        f"Converting closing date string {closing_date} to date object."
                    )
                    closing_date = datetime.strptime(closing_date, "%Y-%m-%d").date()
                    self.logger.info(f"Converted closing date: {closing_date}.")
                except ValueError:
                    self.logger.error(f"Invalid closing date format: {closing_date}.")
                    closing_date = None

            # Ensure down payment is calculated properly
            if down_payment_percentage is not None:
                down_payment_amount = purchase_price * (down_payment_percentage / 100)
                self.logger.info(
                    f"Using provided down payment percentage: {down_payment_percentage}% = ${down_payment_amount: .2f}."
                )
            elif down_payment is not None:
                down_payment_amount = down_payment
                down_payment_percentage = (down_payment / purchase_price) * 100
                self.logger.info(
                    f"Using provided down payment amount: ${down_payment} = {down_payment_percentage: .2f}%. "
                )
            else:
                # Default to 20% down if nothing provided
                down_payment_percentage = 20
                down_payment_amount = purchase_price * 0.2
                self.logger.info(
                    f"No down payment specified, using default: {down_payment_percentage}% = ${down_payment_amount: .2f}. "
                )

            # Calculate loan amount
            loan_amount = purchase_price - down_payment_amount
            self.logger.info(
                f"Calculated loan amount: {purchase_price} - {down_payment_amount} = {loan_amount}. "
            )

            # Calculate LTV (Loan-to-Value) ratio
            ltv_ratio = (loan_amount / purchase_price) * 100
            self.logger.info(f"Calculated LTV ratio: {ltv_ratio: .2f}%. ")

            # Add financed fees to loan amount for government loans
            financed_fees = self.calculate_financed_fees(
                loan_type,
                loan_amount,
                down_payment_percentage,
                va_service_type,
                va_usage,
                va_disability_exempt,
            )
            self.logger.info(f"Calculated financed fees: ${financed_fees: .2f}. ")

            original_loan_amount = loan_amount
            if financed_fees > 0:
                loan_amount += financed_fees
                self.logger.info(
                    f"Added financed fees to loan amount: {original_loan_amount} + {financed_fees} = {loan_amount}. "
                )

            # Calculate monthly P&I
            principal_interest = self.calculate_monthly_payment(loan_amount, annual_rate, loan_term)
            self.logger.info(f"Calculated P&I: ${principal_interest: .2f}. ")

            # Calculate monthly tax (with override support)
            if tax_method == "amount" and annual_tax_amount > 0:
                monthly_tax = annual_tax_amount / 12
                self.logger.info(
                    f"Using actual tax amount: ${annual_tax_amount:.2f}/year = ${monthly_tax:.2f}/month"
                )
            else:
                monthly_tax = (purchase_price * annual_tax_rate / 100) / 12
                self.logger.info(f"Calculated monthly tax: ${monthly_tax:.2f} (percentage method)")

            # Calculate monthly insurance (with override support)
            if insurance_method == "amount" and annual_insurance_amount > 0:
                monthly_insurance = annual_insurance_amount / 12
                self.logger.info(
                    f"Using actual insurance amount: ${annual_insurance_amount:.2f}/year = ${monthly_insurance:.2f}/month"
                )
            else:
                monthly_insurance = (loan_amount * annual_insurance_rate / 100) / 12
                self.logger.info(
                    f"Calculated monthly insurance: ${monthly_insurance:.2f} (percentage method)"
                )

            # Calculate monthly mortgage insurance
            mortgage_insurance = self.calculate_mortgage_insurance(
                loan_amount, purchase_price, loan_type, loan_term * 12
            )
            self.logger.info(f"Calculated mortgage insurance: ${mortgage_insurance: .2f}. ")

            # Calculate total monthly payment
            total_payment = (
                principal_interest
                + monthly_tax
                + monthly_insurance
                + monthly_hoa_fee
                + mortgage_insurance
            )
            self.logger.info(f"Calculated total monthly payment: ${total_payment: .2f}. ")

            # Calculate Closing Costs *before* adjusting loan amount for financed fees
            # Note: Closing costs are based on the *original* loan amount
            transaction_type_str = (
                transaction_type.value
                if isinstance(transaction_type, TRANSACTION_TYPE)
                else str(transaction_type).lower()
            )
            if transaction_type_str == "purchase":
                closing_costs_details = self.calculate_closing_costs(
                    purchase_price=purchase_price,
                    loan_amount=original_loan_amount,  # Use original loan amount for cost calc
                    transaction_type=transaction_type,  # Pass the transaction type from parameter
                    include_owners_title=include_owners_title,
                    discount_points=discount_points,  # Pass discount points here
                )
                self.logger.info(
                    f"Calculated purchase closing costs: ${closing_costs_details.get('total', 0.0): .2f}"
                )
            else:  # Refinance
                # For refinance, we might need different parameters or logic
                # Assuming purchase_price is not relevant for refi cost calculation base?
                # Need to clarify how refinance closing costs are determined.
                # For now, pass loan_amount and transaction_type, but may need adjustment.
                closing_costs_details = self.calculate_closing_costs(
                    purchase_price=0,  # Or estimated home value if needed for specific refi costs?
                    loan_amount=original_loan_amount,
                    transaction_type=TRANSACTION_TYPE.REFINANCE,  # Pass the transaction type using enum
                    include_owners_title=False,  # Typically no owner's policy on refi
                    discount_points=discount_points,
                )
                self.logger.info(
                    f"Calculated refinance closing costs: ${closing_costs_details.get('total', 0.0): .2f}"
                )

            # Calculate prepaid items
            prepaid_items = self.calculate_prepaid_items(
                loan_amount,
                annual_tax_rate,
                annual_insurance_rate,
                annual_rate,
                closing_date,
                tax_method,
                insurance_method,
                annual_tax_amount,
                annual_insurance_amount,
                purchase_price,
            )
            self.logger.info(f"Calculated prepaid items: ${prepaid_items['total']: .2f}. ")

            # Calculate maximum seller contribution based on loan type and LTV
            max_seller_contribution = self._calculate_max_seller_contribution(
                loan_type, ltv_ratio, purchase_price
            )
            self.logger.info(f"Maximum seller contribution: ${max_seller_contribution: .2f}. ")

            # Check if the seller credit exceeds the maximum allowed
            seller_credit_exceeds_max = seller_credit > max_seller_contribution
            if seller_credit_exceeds_max:
                self.logger.warning(
                    f"Seller credit (${seller_credit: .2f}) exceeds maximum allowed (${max_seller_contribution: .2f}). "
                )

            # Extract tax escrow adjustment (seller's tax proration) if it exists
            seller_tax_credit = 0
            if "tax_escrow_adjustment" in prepaid_items:
                seller_tax_credit = abs(prepaid_items["tax_escrow_adjustment"])
                self.logger.info(f"Seller tax credit (proration): ${seller_tax_credit: .2f}. ")

            # Add seller's tax proration to the credits
            total_credits = seller_credit + lender_credit + seller_tax_credit
            self.logger.info(
                f"Total credits: Seller (${seller_credit: .2f}) + Lender (${lender_credit: .2f}) + "
                f"Tax Proration (${seller_tax_credit: .2f}) = ${total_credits: .2f}. "
            )

            # Calculate total cash needed at closing
            total_cash_needed = (
                down_payment_amount
                + closing_costs_details["total"]
                + prepaid_items["total"]
                - total_credits
            )
            self.logger.info(
                f"Total cash needed: Down payment (${down_payment_amount: .2f}) + "
                f"Closing costs (${closing_costs_details['total']: .2f}) + "
                f"Prepaid items (${prepaid_items['total']: .2f}) - "
                f"Credits (${total_credits: .2f}) = ${total_cash_needed: .2f}. "
            )

            # Format result into nicely structured dictionary
            result = {
                "loan_details": {
                    "purchase_price": purchase_price,
                    "down_payment": round(down_payment_amount, 2),
                    "down_payment_percentage": down_payment_percentage,
                    "loan_amount": round(loan_amount, 2),
                    "original_loan_amount": round(original_loan_amount, 2),
                    "financed_fees": round(financed_fees, 2),
                    "loan_term_years": loan_term,
                    "interest_rate": annual_rate,
                    "loan_type": loan_type,
                    "ltv_ratio": round(ltv_ratio, 2),
                    "max_seller_contribution": round(max_seller_contribution, 2),
                    "seller_credit_exceeds_max": seller_credit_exceeds_max,
                },
                "monthly_breakdown": {
                    "principal_interest": round(principal_interest, 2),
                    "property_tax": round(monthly_tax, 2),
                    "insurance": round(monthly_insurance, 2),
                    "hoa": round(monthly_hoa_fee, 2),
                    "pmi": round(mortgage_insurance, 2),
                    "total": round(total_payment, 2),
                },
                "closing_costs": closing_costs_details,
                "prepaid_items": prepaid_items,
                "credits": {
                    "seller_credit": round(seller_credit, 2),
                    "lender_credit": round(lender_credit, 2),
                    "seller_tax_proration": round(seller_tax_credit, 2),
                    "total": round(total_credits, 2),
                },
                "total_cash_needed": round(total_cash_needed, 2),
            }

            return result
        except Exception as e:
            self.logger.error(f"Error in calculate_all: {e}. ")
            import traceback

            self.logger.error(f"Traceback: {traceback.format_exc()}. ")
            raise

    def calculate_closing_costs(
        self,
        purchase_price: float,
        loan_amount: float,
        transaction_type: Union[str, TRANSACTION_TYPE],
        include_owners_title: bool = True,
        discount_points: float = 0.0,
    ) -> Dict[str, float]:
        """Calculate itemized closing costs based on configuration and transaction type."""
        try:
            self.logger.info(
                f"Calculating closing costs for purchase price: ${purchase_price:,.2f}, loan amount: ${loan_amount:,.2f}, "
                f"transaction_type: {transaction_type}, include_owners: {include_owners_title}, discount_points: {discount_points}."
            )

            # Initialize with empty structure
            closing_costs = {}
            total = 0.0

            # Get the closing costs configuration and title insurance config
            closing_costs_config = self.config_manager.get_closing_costs()
            main_config = self.config_manager.get_config()
            title_config = main_config.get("title_insurance", {})

            # For debugging
            self.logger.debug(f"Closing costs config type: {type(closing_costs_config).__name__}.")
            if isinstance(closing_costs_config, dict):
                self.logger.debug(
                    f"Closing costs config keys: {list(closing_costs_config.keys())}."
                )
            elif isinstance(closing_costs_config, list):
                self.logger.debug(f"Closing costs config length: {len(closing_costs_config)}.")
            else:
                self.logger.warning(
                    f"Unexpected closing costs config type: {type(closing_costs_config).__name__}."
                )

            # Check if we're getting closing costs from a JSON file directly
            if not closing_costs_config and "closing_costs" in self.config:
                # Try to use the closing costs from the main config dictionary
                closing_costs_config = self.config.get("closing_costs", {})
                self.logger.info(
                    f"Using closing costs from main config: {type(closing_costs_config).__name__}."
                )

            # Special handling for dictionary format from closing_costs.json
            if isinstance(closing_costs_config, dict):
                self.logger.info("Processing dictionary-format closing costs configuration.")
                for item_name, item_config in closing_costs_config.items():
                    # Skip if marked as not enabled
                    if not item_config.get("enabled", True):
                        continue

                    # Check if the cost applies to the current transaction type
                    applies_to = item_config.get("applies_to", ["Purchase", "Refinance"])
                    # Default to both if not specified
                    # Ensure applies_to is a list
                    if isinstance(applies_to, str):
                        applies_to = [applies_to]

                    # Convert transaction_type to string for comparison with config
                    tx_type_str = (
                        transaction_type.value
                        if isinstance(transaction_type, TRANSACTION_TYPE)
                        else transaction_type
                    )
                    tx_type_norm = tx_type_str.lower()

                    # Normalize applies_to for case-insensitive comparison
                    applies_to_norm = [a.lower() for a in applies_to]

                    # Check if this transaction type applies
                    if (
                        tx_type_norm not in applies_to_norm
                        and tx_type_norm.capitalize() not in applies_to
                    ):
                        self.logger.debug(
                            f"Setting cost '{item_name}' to $0 as it does not apply to transaction type '{tx_type_str}'. Applies to: {applies_to}"
                        )
                        # Instead of skipping, add the item with $0 value for frontend display
                        cost_key = item_name.replace(" ", "_").lower()
                        closing_costs[cost_key] = 0.0
                        continue
                    # END ADDED CHECK

                    # Special case for title insurance - use imported functions
                    # Title insurance applies to both, so no explicit transaction type check needed here,
                    # assuming the config reflects this or defaults correctly.
                    if item_name == "lender_title_insurance" or item_name == "title_insurance":
                        amount = calculate_lenders_title_insurance(
                            loan_amount, include_owners_title, title_config
                        )
                        closing_costs["lender_title_insurance"] = round(amount, 2)
                        total += amount
                        self.logger.info(f"Added lender's title insurance: ${amount: .2f}.")
                        continue  # Go to next item after handling title insurance

                    elif (
                        item_name == "owner_title_insurance"
                        or item_name == "owners_title_insurance"
                    ):
                        # Owner's title typically applies only to Purchase, but let config drive this.
                        # The include_owners_title flag handles user preference.
                        if include_owners_title:
                            amount = calculate_owners_title_insurance(
                                purchase_price,
                                loan_amount,
                                include_owners_title,  # This already gates the calculation logic
                                title_config,
                            )
                            # Only add if amount > 0, owner's can be 0 if lender's only is chosen OR if it's a refi where owner's isn't recalculated
                            if amount > 0:
                                closing_costs["owner_title_insurance"] = round(amount, 2)
                                total += amount
                                self.logger.info(f"Added owner's title insurance: ${amount: .2f}.")
                            else:
                                closing_costs["owner_title_insurance"] = 0.0  # Ensure key exists
                                self.logger.info(
                                    "Owner's title insurance calculated as $0.00 (potentially waived or refi)."
                                )

                        else:
                            self.logger.info(
                                "Owner's title insurance skipped as per include_owners_title=False."
                            )
                            closing_costs[
                                "owner_title_insurance"
                            ] = 0.0  # Ensure key exists even if 0
                        continue  # Go to next item

                    # Calculate regular fee based on type
                    fee_type = item_config.get("type", "fixed")
                    value = float(item_config.get("value", 0))
                    base = item_config.get("calculation_base", "fixed")
                    amount = 0.0  # Initialize amount for the item

                    if fee_type == "fixed":
                        amount = value
                    elif fee_type == "percentage":
                        if base == "loan_amount":
                            amount = (value / 100) * loan_amount
                        elif base == "purchase_price":
                            # Use purchase_price only if it's a Purchase transaction
                            tx_type_normalized = (
                                transaction_type.value
                                if isinstance(transaction_type, TRANSACTION_TYPE)
                                else transaction_type
                            )
                            if (
                                tx_type_normalized == TRANSACTION_TYPE.PURCHASE.value
                                or tx_type_normalized.lower() == "purchase"
                            ):
                                amount = (value / 100) * purchase_price
                            else:
                                # For Refinance, if base is purchase_price, what should happen?
                                # Option 1: Use loan amount instead?
                                # amount = (value / 100) * loan_amount
                                # Option 2: Skip this cost for Refi if based on purchase price?
                                self.logger.warning(
                                    f"Cost '{item_name}' based on 'purchase_price' skipped for 'Refinance' transaction."
                                )
                                amount = 0  # Or continue to skip adding it below
                        else:  # Default base or invalid base
                            amount = value  # Default to fixed value if base is unclear or 'fixed'
                            if base != "fixed":
                                self.logger.warning(
                                    f"Unsupported calculation_base '{base}' for item '{item_name}'. Using fixed value."
                                )
                    else:
                        self.logger.warning(
                            f"Unsupported fee_type '{fee_type}' for item '{item_name}'. Skipping."
                        )
                        continue  # Skip items with unsupported types

                    # Add the calculated amount if it's greater than zero
                    # Always include important items even if they're $0
                    always_include_items = ["origination_fee", "discount_points"]
                    cost_key = item_name.replace(" ", "_").lower()  # Basic sanitization

                    if amount > 0:
                        closing_costs[cost_key] = round(amount, 2)
                        total += amount
                        self.logger.info(f"Added cost '{item_name}': ${amount: .2f}.")
                    elif cost_key in always_include_items:
                        # Include important items even when $0 for frontend display
                        closing_costs[cost_key] = 0.0
                        self.logger.info(f"Added {item_name} as $0.00 (always include).")
                    else:
                        self.logger.debug(
                            f"Calculated amount for '{item_name}' is zero or negative. Not adding."
                        )

            # Handle Discount Points separately as they depend on direct input
            points_cost = (discount_points / 100) * loan_amount if discount_points else 0.0
            if points_cost > 0:
                closing_costs["discount_points"] = round(points_cost, 2)
                total += points_cost
                self.logger.info(f"Added discount points cost: ${points_cost: .2f}.")
            else:
                # Ensure the key exists for the frontend table if needed, even if 0
                closing_costs["discount_points"] = 0.0

            # Add Origination Fee if applicable (assuming it's defined elsewhere or should be added)
            # This might need adjustment based on where origination fee comes from.
            # If it's part of closing_costs_config, the loop above handles it.
            # If calculated separately or fixed, add here. Example:
            # origination_fee = self._calculate_origination_fee(loan_amount) # Hypothetical function
            # if origination_fee > 0:
            #    closing_costs['origination_fee'] = round(origination_fee, 2)
            #    total += origination_fee

            # Ensure total is included in the returned dictionary
            closing_costs["total"] = round(total, 2)
            self.logger.info(f"Total calculated closing costs: ${total: .2f}")

            return closing_costs

        except Exception as e:
            self.logger.error(f"Error calculating closing costs: {e}", exc_info=True)
            # Return an empty dict or dict with total 0 on error?
            return {"total": 0.0}  # Return minimal structure on error

    def _calculate_prepaid_tax(self, closing_date, monthly_tax: float) -> float:
        """
        Calculate prepaid tax amount based on closing date.

        Formula: Annual tax amount minus the number of accrued escrow payments.
        The borrower has paid from the first payment date through November
        since taxes are due in December. Mortgage payments are made in arrears.

        Args:
            closing_date: The closing date of the loan.
            monthly_tax: The monthly tax amount.

        Returns:
            float: The prepaid tax amount.
        """
        try:
            # If no closing date, return 0
            if not closing_date:
                return 0

            # Calculate annual tax amount
            annual_tax = monthly_tax * 12

            # Determine first payment date
            # If closing on March 15, first payment is May 1 (representing April)
            closing_month = closing_date.month
            # Note: closing_year removed as it was unused

            # First payment is on the 1st of the month after the closing month
            first_payment_month = (
                closing_month + 2 if closing_month < 11 else (closing_month + 2) % 12
            )

            # Count months from first payment through November
            if first_payment_month <= 11:
                # If first payment is before or in November, count months in current year
                accrued_escrow_payments = 11 - first_payment_month + 1
            else:
                # If first payment is in December or later (next year), no payments for current year
                accrued_escrow_payments = 0

            # Calculate prepaid tax amount
            prepaid_tax = annual_tax - (monthly_tax * accrued_escrow_payments)

            self.logger.info(
                f"Prepaid tax calculation: Closing date={closing_date}, "
                f"First payment month={first_payment_month}, "
                f"Annual tax=${annual_tax: .2f}, "
                f"Accrued escrow payments={accrued_escrow_payments}, "
                f"Prepaid tax amount=${prepaid_tax: .2f}. "
            )

            return round(prepaid_tax, 2)

        except Exception as e:
            self.logger.error(f"Error calculating prepaid tax: {str(e)}. ")
            return 0

    def calculate_prepaid_items(
        self,
        loan_amount: float,
        annual_tax_rate: float,
        annual_insurance_rate: float,
        annual_interest_rate: float,
        closing_date=None,
        tax_method: str = "percentage",
        insurance_method: str = "percentage",
        annual_tax_amount: float = 0.0,
        annual_insurance_amount: float = 0.0,
        purchase_price: float = 0.0,
    ) -> Dict[str, float]:
        """Calculate prepaid items (taxes, insurance, interest)."""
        try:
            self.logger.info(
                f"Calculating prepaid items with loan={loan_amount}, tax_rate={annual_tax_rate}, insurance_rate={annual_insurance_rate}, interest_rate={annual_interest_rate}. "
            )
            self.logger.info(
                f"Closing date provided: {closing_date} (type: {type(closing_date).__name__ if closing_date else None}). "
            )

            # Make a deep copy of the config to avoid modifying the original
            import copy

            config = copy.deepcopy(self.config["prepaid_items"])
            prepaid = {}

            # 1. Calculate prepaid interest first - this is the most important part
            daily_interest = (
                loan_amount * annual_interest_rate / 100
            ) / CalculationConstants.DAYS_IN_STANDARD_YEAR
            self.logger.info(
                f"Daily interest calculation: {loan_amount} * {annual_interest_rate}% / {CalculationConstants.DAYS_IN_STANDARD_YEAR} = ${daily_interest: .2f}/day. "
            )

            # Default to 30 days if no closing date is provided (only as fallback)
            days_of_interest = CalculationConstants.DEFAULT_PREPAID_INTEREST_DAYS
            self.logger.info(f"Default days of interest (fallback): {days_of_interest}. ")

            # If we have a closing date, calculate the actual days remaining in the month
            if closing_date:
                try:
                    # Get the last day of the month
                    _, last_day = monthrange(closing_date.year, closing_date.month)
                    last_date_of_month = date(closing_date.year, closing_date.month, last_day)

                    # Calculate days from closing to end of month (inclusive of closing day)
                    days_of_interest = (last_date_of_month - closing_date).days + 1

                    self.logger.info(
                        f"Calculated {days_of_interest} days from closing date {closing_date} to end of month {last_date_of_month}. "
                    )
                except Exception as e:
                    self.logger.error(f"Error calculating days from closing date: {str(e)}. ")
                    self.logger.warning("Falling back to default 30 days of interest.")
            else:
                self.logger.warning("No closing date provided, using default 30 days of interest.")

            # Calculate the prepaid interest amount
            prepaid_interest = round(daily_interest * days_of_interest, 2)
            self.logger.info(
                f"Prepaid interest calculation: ${daily_interest: .2f}/day × {days_of_interest} days = ${prepaid_interest: .2f}. "
            )
            prepaid["prepaid_interest"] = prepaid_interest

            # 2. Calculate prepaid property tax (with method override support)
            if tax_method == "amount" and annual_tax_amount > 0:
                monthly_tax = annual_tax_amount / 12
                self.logger.info(
                    f"Using actual tax amount for prepaids: ${annual_tax_amount:.2f}/year = ${monthly_tax:.2f}/month"
                )
            else:
                # Use purchase_price for tax calculation if available, otherwise fallback to loan_amount
                tax_base = purchase_price if purchase_price > 0 else loan_amount
                monthly_tax = (tax_base * annual_tax_rate / 100) / 12
                self.logger.info(f"Calculated monthly tax for prepaids: ${monthly_tax:.2f} (percentage method on ${tax_base:.2f})")

            # Prepaid property tax is always 12 months regardless of closing date
            # Seller proration and borrower escrow credits are handled separately
            prepaid["prepaid_tax"] = round(monthly_tax * config["months_tax_prepaid"], 2)

            prepaid["tax_escrow"] = round(monthly_tax * config["months_tax_escrow"], 2)

            # Calculate tax escrow adjustment assuming taxes are due in December
            tax_adjustment = 0
            borrower_escrow_credit = 0
            if closing_date:
                # Calculate seller's proration credit (Jan 1 to closing)
                tax_adjustment = self._calculate_tax_escrow_adjustment(
                    closing_date=closing_date, monthly_tax=monthly_tax
                )
                self.logger.info(
                    f"Seller tax escrow adjustment calculated: ${tax_adjustment: .2f}. "
                )
                if tax_adjustment != 0:
                    prepaid["tax_escrow_adjustment"] = tax_adjustment

                # Calculate borrower's escrow payment credit (first payment to tax due date)
                borrower_escrow_credit = self._calculate_borrower_escrow_credit(
                    closing_date=closing_date, monthly_tax=monthly_tax
                )
                self.logger.info(
                    f"Borrower escrow credit calculated: ${borrower_escrow_credit: .2f}. "
                )
                if borrower_escrow_credit != 0:
                    prepaid["borrower_escrow_credit"] = borrower_escrow_credit

            self.logger.info(
                f"Property tax calculations: monthly=${monthly_tax: .2f}, prepaid=${prepaid['prepaid_tax']: .2f}, escrow=${prepaid['tax_escrow']: .2f}, seller_adjustment=${tax_adjustment: .2f}, borrower_credit=${borrower_escrow_credit: .2f}. "
            )

            # 3. Calculate prepaid homeowner's insurance (with method override support)
            if insurance_method == "amount" and annual_insurance_amount > 0:
                monthly_insurance = annual_insurance_amount / 12
                self.logger.info(
                    f"Using actual insurance amount for prepaids: ${annual_insurance_amount:.2f}/year = ${monthly_insurance:.2f}/month"
                )
            else:
                monthly_insurance = (loan_amount * annual_insurance_rate / 100) / 12
                self.logger.info(f"Calculated monthly insurance for prepaids: ${monthly_insurance:.2f} (percentage method)")
            
            prepaid["prepaid_insurance"] = round(
                monthly_insurance * config["months_insurance_prepaid"], 2
            )
            prepaid["insurance_escrow"] = round(
                monthly_insurance * config["months_insurance_escrow"], 2
            )
            self.logger.info(
                f"Insurance calculations: monthly=${monthly_insurance: .2f}, prepaid=${prepaid['prepaid_insurance']: .2f}, escrow=${prepaid['insurance_escrow']: .2f}. "
            )

            # 4. Calculate total
            prepaid["total"] = sum(prepaid.values())
            self.logger.info(f"Total prepaid items: ${prepaid['total']: .2f}. ")

            return prepaid
        except Exception as e:
            self.logger.error(f"Error in calculate_prepaid_items: {str(e)}. ")
            raise

    def _calculate_tax_escrow_adjustment(self, closing_date, monthly_tax: float) -> float:
        """
        Calculate the property tax proration (seller's tax credit) at closing.

        Property Tax Adjustment = (Annual Property Tax Amount × Days Seller Owned Property in Tax Year ÷ {CalculationConstants.DAYS_IN_CALENDAR_YEAR}) - Any Prepaid Taxes

        Args:
            closing_date: The closing date of the loan.
            monthly_tax: The monthly tax amount.

        Returns:
            float: The tax escrow adjustment amount (negative value represents credit to buyer).
        """
        try:
            # If no closing date, no adjustment
            if not closing_date:
                return 0

            # Calculate the annual tax amount
            annual_tax = monthly_tax * 12

            # Calculate days in year and days seller owned property
            days_in_year = (
                366
                if closing_date.year % 4 == 0
                and (closing_date.year % 100 != 0 or closing_date.year % 400 == 0)
                else CalculationConstants.DAYS_IN_CALENDAR_YEAR
            )
            days_seller_owned = (
                closing_date.timetuple().tm_yday
            )  # Days from beginning of year to closing date

            # Calculate seller's portion of annual taxes (Georgia formula)
            seller_tax_responsibility = annual_tax * (days_seller_owned / days_in_year)

            # In Georgia, this amount becomes a credit to the buyer
            # A negative value represents a credit to the buyer
            adjustment = -round(seller_tax_responsibility, 2)

            # Log the calculation process
            self.logger.info(
                f"Tax proration calculation: Closing={closing_date}, "
                f"Days in year={days_in_year}, Days seller owned={days_seller_owned}, "
                f"Seller's tax portion=${seller_tax_responsibility: .2f}, "
                f"Buyer credit=${abs(adjustment): .2f}. "
            )

            return adjustment
        except Exception as e:
            self.logger.error(f"Error calculating tax escrow adjustment: {str(e)}. ")
            return 0

    def _calculate_borrower_escrow_credit(self, closing_date, monthly_tax: float) -> float:
        """
        Calculate the borrower's credit for tax escrow payments made from first payment date to tax due date.

        Logic:
        - First payment is due the 1st of the month after the end of the closing month
        - Payments are made in arrears (August payment covers July)
        - Taxes are typically due in October/November (we'll use November 1st)
        - Borrower gets credit for months they pay escrow before taxes are due

        Args:
            closing_date: The closing date of the loan
            monthly_tax: The monthly tax amount

        Returns:
            float: Credit amount (negative value represents credit to borrower)
        """
        try:
            if not closing_date:
                return 0

            from calendar import monthrange

            # Calculate first payment date
            # First payment is due the 1st of the month after the end of the closing month
            closing_month = closing_date.month
            closing_year = closing_date.year

            # Move to next month after closing month
            first_payment_month = closing_month + 1
            first_payment_year = closing_year

            # Handle year rollover
            if first_payment_month > 12:
                first_payment_month = 1
                first_payment_year += 1

            # First payment date is the 1st of that month
            from datetime import date

            first_payment_date = date(first_payment_year, first_payment_month, 1)

            # Tax due date (assume November 1st of the tax year)
            # For Georgia, property taxes are typically due in October/November
            tax_due_date = date(closing_year, 11, 1)

            # If closing is after tax due date, use next year's tax due date
            if closing_date >= tax_due_date:
                tax_due_date = date(closing_year + 1, 11, 1)

            # Count months from first payment to tax due date
            current_date = first_payment_date
            months_count = 0

            while current_date < tax_due_date:
                months_count += 1
                # Move to next month
                if current_date.month == 12:
                    current_date = date(current_date.year + 1, 1, 1)
                else:
                    current_date = date(current_date.year, current_date.month + 1, 1)

            # Calculate credit (negative value = credit to borrower)
            credit_amount = -(months_count * monthly_tax)

            self.logger.info(
                f"Borrower escrow credit calculation: Closing={closing_date}, "
                f"First payment={first_payment_date}, Tax due={tax_due_date}, "
                f"Months of escrow payments={months_count}, "
                f"Monthly tax=${monthly_tax: .2f}, Credit=${abs(credit_amount): .2f}"
            )

            return round(credit_amount, 2)

        except Exception as e:
            self.logger.error(f"Error calculating borrower escrow credit: {str(e)}")
            return 0

    def _validate_refinance_parameters(
        self,
        loan_type: str,
        refinance_type: str,
        appraised_value: float,
        loan_amount_for_ltv: float,
        new_interest_rate: float,
        original_interest_rate: float = None,
    ) -> list:
        """
        Validate refinance parameters based on loan type and refinance type requirements.

        Returns:
            list: List of validation error messages, empty if all validations pass
        """
        errors = []

        try:
            # Calculate LTV for validation (using final loan amount after cash contributions)
            ltv = (loan_amount_for_ltv / appraised_value) * 100 if appraised_value > 0 else 0

            # Define LTV limits based on loan type and refinance type from the requirements table
            ltv_limits = {
                "conventional": {
                    "rate_term": 97.0,  # 97% for primary residence rate & term
                    "cash_out": 80.0,  # 80% for cash-out
                    "streamline": 97.0,  # Same as rate & term
                },
                "fha": {
                    "rate_term": 96.5,  # 96.5% for rate & term
                    "cash_out": 80.0,  # 80% for cash-out
                    "streamline": 96.5,  # 96.5% for streamline
                },
                "va": {
                    "rate_term": 100.0,  # VA allows 100% but most lenders cap at 90%
                    "cash_out": 100.0,  # VA allows 100% for cash-out
                    "streamline": 100.0,  # No LTV limit for IRRRL
                },
                "usda": {
                    "rate_term": 100.0,  # No LTV limit for guaranteed loans
                    "cash_out": 0.0,  # USDA doesn't allow cash-out
                    "streamline": 100.0,  # No LTV limit for streamline
                },
            }

            # Check LTV limits
            if loan_type in ltv_limits and refinance_type in ltv_limits[loan_type]:
                max_ltv = ltv_limits[loan_type][refinance_type]
                if max_ltv > 0 and ltv > max_ltv:
                    errors.append(
                        f"LTV of {ltv:.1f}% exceeds maximum {max_ltv:.1f}% for {loan_type.upper()} {refinance_type.replace('_', ' ')} refinance"
                    )

            # Check for invalid combinations
            if loan_type == "usda" and refinance_type == "cash_out":
                errors.append("USDA loans do not allow cash-out refinances")

            # Validate minimum rate reduction for streamline programs
            if refinance_type == "streamline" and original_interest_rate is not None:
                if loan_type == "fha":
                    # FHA Streamline requires 0.5% rate reduction OR reduce term
                    min_reduction = 0.5
                    if new_interest_rate >= (original_interest_rate - min_reduction):
                        errors.append(
                            f"FHA Streamline refinance requires at least {min_reduction}% rate reduction. Current reduction: {original_interest_rate - new_interest_rate:.2f}%"
                        )
                elif loan_type == "va":
                    # VA IRRRL requires some benefit (rate reduction or term reduction)
                    if new_interest_rate >= original_interest_rate:
                        errors.append(
                            "VA IRRRL requires interest rate reduction or other tangible benefit"
                        )
                elif loan_type == "usda":
                    # USDA Streamline requires rate reduction
                    if new_interest_rate >= original_interest_rate:
                        errors.append("USDA Streamline refinance requires interest rate reduction")

            # Add specific loan type validations
            if loan_type == "fha":
                # FHA specific validations
                if ltv > 96.5 and refinance_type in ["rate_term", "streamline"]:
                    errors.append(
                        f"FHA loans require LTV ≤ 96.5% for {refinance_type.replace('_', ' ')} refinance"
                    )
                # FHA cash-out limited to 80% LTV
                if refinance_type == "cash_out" and ltv > 80.0:
                    errors.append("FHA cash-out refinance limited to 80% LTV")

            elif loan_type == "va":
                # VA specific validations
                # Most lenders cap VA at 90% even though VA allows 100%
                if ltv > 90.0 and refinance_type == "cash_out":
                    errors.append("Most lenders limit VA cash-out refinance to 90% LTV")
                # VA IRRRL (streamline) has no LTV limit but should be noted

            elif loan_type == "usda":
                # USDA specific validations
                if refinance_type == "cash_out":
                    errors.append("USDA does not allow cash-out refinances")
                # USDA guaranteed loans have no LTV limit for rate & term or streamline

            elif loan_type == "conventional":
                # Conventional specific validations
                if ltv > 97.0 and refinance_type in ["rate_term", "streamline"]:
                    errors.append(
                        f"Conventional loans typically limited to 97% LTV for {refinance_type.replace('_', ' ')} refinance"
                    )
                if ltv > 80.0 and refinance_type == "cash_out":
                    errors.append("Conventional cash-out refinance limited to 80% LTV")
                # PMI requirements for high LTV are handled automatically in calculation
                # No need to block refinance - PMI will be calculated if LTV > 80%

            # General validation rules
            if appraised_value <= 0:
                errors.append("Appraised value must be greater than zero")

            if loan_amount_for_ltv <= 0:
                errors.append("Loan amount must be greater than zero")

            if new_interest_rate <= 0:
                errors.append("New interest rate must be greater than zero")

            if new_interest_rate > 20:
                errors.append("Interest rate appears unusually high (>20%)")

            # Cash-out amount validation
            if refinance_type == "cash_out":
                max_loan_amount = appraised_value * (
                    ltv_limits.get(loan_type, {}).get("cash_out", 80) / 100
                )
                if loan_amount_for_ltv > max_loan_amount:
                    errors.append(
                        f"Loan amount exceeds maximum allowed for {loan_type.upper()} cash-out refinance"
                    )

            self.logger.info(f"Refinance validation complete: {len(errors)} errors found")

        except Exception as e:
            self.logger.error(f"Error in refinance parameter validation: {str(e)}")
            errors.append(f"Validation error: {str(e)}")

        return errors

    def generate_amortization_data(self, principal: float, annual_rate: float, years: int) -> list:
        """Generate amortization data for yearly principal balance over the loan term."""
        try:
            self.logger.info(
                f"Generating amortization data: principal={principal}, rate={annual_rate}, years={years}. "
            )

            if annual_rate == 0:
                # Simple case for zero interest rate
                # Note: We don't need to store monthly_payment as it's not used
                # Just calculate the yearly balances directly
                yearly_balances = [principal * (1 - (i / years)) for i in range(1, years + 1)]
                return yearly_balances

            # Calculate monthly payment
            monthly_rate = annual_rate / 12 / 100
            num_payments = years * 12

            payment = (
                principal
                * (monthly_rate * (1 + monthly_rate) ** num_payments)
                / ((1 + monthly_rate) ** num_payments - 1)
            )

            # Calculate balance at the end of each year
            balances = []
            balance = principal

            for year in range(1, years + 1):
                for month in range(1, 13):
                    # Skip if we've already reached the end of the loan term
                    if year * 12 + month > num_payments:
                        break

                    # Calculate interest for this month
                    monthly_interest = balance * monthly_rate

                    # Calculate principal payment for this month
                    principal_payment = payment - monthly_interest

                    # Update balance
                    balance -= principal_payment

                    # Ensure we don't go below zero due to rounding
                    balance = max(0, balance)

                # Add balance at the end of the year to our list
                balances.append(round(balance, 2))

            self.logger.info(f"Generated {len(balances)} yearly balance data points. ")
            return balances

        except Exception as e:
            self.logger.error(f"Error generating amortization data: {e}. ")
            return [principal] * years  # Return flat line as fallback

    def _calculate_max_seller_contribution(
        self,
        loan_type: str,
        ltv_ratio: float,
        purchase_price: float,
    ) -> float:
        """
        Calculate the maximum allowable seller contribution based on loan type and LTV ratio.

        - FHA: Maximum 6% of purchase price
        - VA: Maximum 4% of purchase price for certain fees
        - USDA: Maximum 6% of purchase price
        - Conventional: 3%, 6%, or 9% depending on LTV

        Args:
            loan_type: Type of loan ('conventional', 'fha', 'va', 'usda').
            ltv_ratio: Loan-to-value ratio (percentage).
            purchase_price: Purchase price of the property.

        Returns:
            float: Maximum allowable seller contribution.
        """
        try:
            loan_type = loan_type.lower() if isinstance(loan_type, str) else "conventional"

            if loan_type == "fha":
                # FHA allows up to 6% of purchase price
                max_percent = 6.0
                self.logger.info("FHA loan: Maximum seller contribution is 6% of purchase price.")
            elif loan_type == "va":
                # VA allows up to 4% for certain closing costs
                max_percent = 4.0
                self.logger.info("VA loan: Maximum seller contribution is 4% of purchase price.")
            elif loan_type == "usda":
                # USDA typically follows similar guidelines to FHA
                max_percent = 6.0
                self.logger.info("USDA loan: Maximum seller contribution is 6% of purchase price.")
            else:
                # Conventional loan - based on LTV ratio
                if ltv_ratio > 90:
                    max_percent = 3.0
                    self.logger.info(
                        "Conventional loan with LTV > 90%: Maximum seller contribution is 3% of purchase price."
                    )
                elif ltv_ratio > 75:
                    max_percent = 6.0
                    self.logger.info(
                        "Conventional loan with 75% < LTV ≤ 90%: Maximum seller contribution is 6% of purchase price."
                    )
                else:
                    max_percent = 9.0
                    self.logger.info(
                        "Conventional loan with LTV ≤ 75%: Maximum seller contribution is 9% of purchase price."
                    )

            max_contribution = (max_percent / 100) * purchase_price
            self.logger.info(
                f"Maximum seller contribution: {max_percent}% of ${purchase_price: .2f} = ${max_contribution: .2f}. "
            )
            return round(max_contribution, 2)

        except Exception as e:
            self.logger.error(f"Error calculating maximum seller contribution: {str(e)}. ")
            # Default to 3% as a safe fallback
            return round(0.03 * purchase_price, 2)

    def _calculate_refinance_prepaids(
        self,
        loan_amount: float,
        annual_taxes: float,
        annual_insurance: float,
        annual_interest_rate: float,
        closing_date,
        tax_escrow_months: int = 3,
        insurance_escrow_months: int = 2,
    ) -> Dict[str, float]:
        """
        Calculate prepaid items specifically for refinance transactions.

        Args:
            loan_amount (float): The new loan amount
            annual_taxes (float): Annual property tax amount
            annual_insurance (float): Annual homeowner's insurance amount
            annual_interest_rate (float): New loan interest rate
            closing_date: The refinance closing date
            prepaid_months (int): Number of months to collect for escrow

        Returns:
            Dict[str, float]: Dictionary of prepaid items and their amounts
        """
        try:
            prepaid = {}

            # 1. Calculate prepaid interest (per diem interest)
            daily_interest = (
                loan_amount * annual_interest_rate / 100
            ) / CalculationConstants.DAYS_IN_STANDARD_YEAR

            # Calculate days from closing to end of month
            if closing_date:
                _, last_day = monthrange(closing_date.year, closing_date.month)
                days_in_month = last_day - closing_date.day + 1
            else:
                days_in_month = 15  # Default fallback

            prepaid["prepaid_interest"] = daily_interest * days_in_month
            prepaid["interest_days"] = days_in_month

            # 2. Homeowner's insurance premium (no full year for refinance, just current premium)
            # For refinance, we typically don't collect a full year premium
            prepaid["prepaid_insurance"] = 0  # Existing policy continues

            # 3. Property taxes - no prepaid taxes for refinance since taxes are current
            prepaid["prepaid_tax"] = 0
            prepaid["prepaid_tax_months"] = 0

            # 4. Escrow reserves (separate months for tax and insurance)
            monthly_tax = annual_taxes / 12
            monthly_insurance = annual_insurance / 12

            prepaid["tax_escrow"] = monthly_tax * tax_escrow_months
            prepaid["tax_escrow_months"] = tax_escrow_months

            prepaid["insurance_escrow"] = monthly_insurance * insurance_escrow_months
            prepaid["insurance_escrow_months"] = insurance_escrow_months

            # No seller proration credits or borrower escrow credits for refinance
            prepaid["tax_escrow_adjustment"] = 0
            prepaid["borrower_escrow_credit"] = 0

            # Calculate total
            prepaid["total"] = sum(prepaid.values())

            self.logger.info(f"Refinance prepaid items calculated: ${prepaid['total']:.2f}")

            return prepaid

        except Exception as e:
            self.logger.error(f"Error calculating refinance prepaids: {str(e)}")
            return {"total": 0}

    def calculate_refinance(
        self,
        appraised_value: float,
        original_loan_balance: float,
        original_interest_rate: float,
        original_loan_term: int,
        original_closing_date: str,
        new_interest_rate: float,
        new_loan_term: int,
        new_closing_date: str = None,
        annual_taxes: float = None,
        annual_insurance: float = None,
        monthly_hoa_fee: float = 0.0,
        extra_monthly_savings: float = 0.0,
        refinance_lender_credit: float = 0.0,
        use_manual_balance: bool = False,
        manual_current_balance: float = 0.0,
        cash_option: str = "finance_all",
        target_ltv_value: float = 80.0,
        tax_escrow_months: int = 3,
        insurance_escrow_months: int = 2,
        new_discount_points: float = 0.0,
        loan_type: str = "conventional",
        refinance_type: str = "rate_term",
        zero_cash_to_close: bool = False,
        transaction_type: Union[str, TRANSACTION_TYPE] = TRANSACTION_TYPE.REFINANCE,
    ) -> Dict[str, Any]:
        """
        Calculate refinance analysis, including current balance, LTV, break-even, and savings.

        Args:
            appraised_value (float): New appraised value of the property.
            original_loan_balance (float): Original loan balance.
            original_interest_rate (float): Interest rate of the original loan.
            original_loan_term (int): Term of the original loan in years.
            original_closing_date (str): Closing date of the original loan (YYYY-MM-DD).
            new_interest_rate (float): New interest rate.
            new_loan_term (int): New loan term in years.
            new_closing_date (str): New closing date for the refinance (YYYY-MM-DD).
            annual_taxes (float): Annual property taxes amount.
            annual_insurance (float): Annual homeowner's insurance amount.
            prepaid_months (int): Number of months to collect for escrow account.
            new_discount_points (float): Discount points paid for the new loan (as percent of new loan amount).
            loan_type (str): Type of loan ('conventional', 'fha', 'va', 'usda').
            refinance_type (str): Type of refinance ('rate_term', 'cash_out', 'streamline').
            transaction_type (Union[str, TRANSACTION_TYPE]): Transaction type for the refinance.
        """
        try:
            # 1. Calculate current loan balance using amortization
            orig_closing_date = datetime.strptime(original_closing_date, "%Y-%m-%d").date()
            today = date.today()
            months_elapsed = (today.year - orig_closing_date.year) * 12 + (
                today.month - orig_closing_date.month
            )
            orig_monthly_payment = self.calculate_monthly_payment(
                principal=original_loan_balance,
                annual_rate=original_interest_rate,
                years=original_loan_term,
            )
            # Use manual balance if provided, otherwise calculate from amortization
            if use_manual_balance and manual_current_balance > 0:
                current_balance = manual_current_balance
                self.logger.info(f"Using manual current balance: ${current_balance:.2f}")
            else:
                # Remaining balance after N payments (standard amortization calculation)
                r = original_interest_rate / 100 / 12
                n = original_loan_term * 12
                p = original_loan_balance
                k = months_elapsed
                if r == 0:
                    current_balance = max(0, p - (orig_monthly_payment * k))
                else:
                    current_balance = p * (((1 + r) ** n - (1 + r) ** k) / ((1 + r) ** n - 1))

                self.logger.info(f"Calculated current loan balance: ${current_balance:.2f}")

            # 2. Validate refinance parameters based on loan type and refinance type
            # Note: LTV validation moved to after loan amount calculation to handle cash contributions

            # 3. Calculate closing costs automatically (similar to purchase transaction)
            # For refinance, we use the current balance as the basis for calculating closing costs
            closing_costs_details = self.calculate_closing_costs(
                purchase_price=appraised_value,  # Use appraised value as purchase price
                loan_amount=current_balance,  # Use current balance as loan amount
                transaction_type=transaction_type,  # Use passed transaction type
                include_owners_title=False,  # No owner's title insurance for refinance
                discount_points=new_discount_points,
            )

            # Extract total closing costs and financed closing costs
            total_closing_costs = closing_costs_details.get("total", 0.0)
            # For refinance, we typically finance all closing costs minus lender credits
            financed_closing_costs = max(0, total_closing_costs - refinance_lender_credit)

            self.logger.info(f"Calculated closing costs: ${financed_closing_costs: .2f}")

            # 3. Calculate preliminary new loan amount as current balance plus financed closing costs
            preliminary_loan_amount = current_balance + financed_closing_costs
            self.logger.info(
                f"Preliminary loan amount: ${preliminary_loan_amount: .2f} (current balance: ${current_balance: .2f} + financed closing costs: ${financed_closing_costs: .2f})"
            )

            # Initialize variables used across different cash modes
            cash_received = 0  # Initialize cash received for all modes
            cash_needed = 0  # Initialize cash needed for all modes

            # For zero cash mode, we need to calculate prepaids first to add them to loan amount
            if zero_cash_to_close:
                # Calculate prepaid items using preliminary loan amount
                if new_closing_date:
                    try:
                        refinance_closing_date = datetime.strptime(
                            new_closing_date, "%Y-%m-%d"
                        ).date()
                    except ValueError:
                        refinance_closing_date = date.today()
                else:
                    refinance_closing_date = date.today()

                # Calculate prepaid items using actual amounts
                if annual_taxes is not None and annual_insurance is not None:
                    preliminary_prepaid_items = self._calculate_refinance_prepaids(
                        loan_amount=preliminary_loan_amount,
                        annual_taxes=annual_taxes,
                        annual_insurance=annual_insurance,
                        annual_interest_rate=new_interest_rate,
                        closing_date=refinance_closing_date,
                        tax_escrow_months=tax_escrow_months,
                        insurance_escrow_months=insurance_escrow_months,
                    )
                else:
                    # Use standard calculation with rates
                    annual_tax_rate = 1.3  # Default fallback
                    annual_insurance_rate = 1.1  # Default fallback
                    preliminary_prepaid_items = self.calculate_prepaid_items(
                        loan_amount=preliminary_loan_amount,
                        annual_tax_rate=annual_tax_rate,
                        annual_insurance_rate=annual_insurance_rate,
                        annual_interest_rate=new_interest_rate,
                        closing_date=refinance_closing_date,
                        tax_method="percentage",
                        insurance_method="percentage",
                        annual_tax_amount=0.0,
                        annual_insurance_amount=0.0,
                        purchase_price=appraised_value,
                    )

                # Add prepaids to loan amount for zero cash calculation
                prepaid_total = preliminary_prepaid_items.get("total", 0)
                new_loan_amount = current_balance + financed_closing_costs + prepaid_total
                self.logger.info(
                    f"Zero cash mode - New loan amount: ${new_loan_amount: .2f} (current balance: ${current_balance: .2f} + closing costs: ${financed_closing_costs: .2f} + prepaids: ${prepaid_total: .2f})"
                )
            else:
                # Handle different cash contribution scenarios
                if cash_option == "target_ltv":
                    # Calculate loan amount to achieve target LTV
                    target_loan_amount = appraised_value * (target_ltv_value / 100)
                    new_loan_amount = target_loan_amount

                    if refinance_type == "cash_out":
                        # Cash-out refinance: closing costs and prepaids are paid from loan proceeds
                        # Need to calculate prepaids first for cash-out calculation
                        if new_closing_date:
                            try:
                                refinance_closing_date = datetime.strptime(
                                    new_closing_date, "%Y-%m-%d"
                                ).date()
                            except ValueError:
                                refinance_closing_date = date.today()
                        else:
                            refinance_closing_date = date.today()

                        # Calculate prepaid items for cash-out scenario
                        if annual_taxes is not None and annual_insurance is not None:
                            prepaid_items = self._calculate_refinance_prepaids(
                                loan_amount=new_loan_amount,
                                annual_taxes=annual_taxes,
                                annual_insurance=annual_insurance,
                                annual_interest_rate=new_interest_rate,
                                closing_date=refinance_closing_date,
                                tax_escrow_months=tax_escrow_months,
                                insurance_escrow_months=insurance_escrow_months,
                            )
                        else:
                            # Use standard calculation with rates
                            annual_tax_rate = 1.3  # Default fallback
                            annual_insurance_rate = 1.1  # Default fallback
                            prepaid_items = self.calculate_prepaid_items(
                                loan_amount=new_loan_amount,
                                annual_tax_rate=annual_tax_rate,
                                annual_insurance_rate=annual_insurance_rate,
                                annual_interest_rate=new_interest_rate,
                                closing_date=refinance_closing_date,
                                tax_method="percentage",
                                insurance_method="percentage",
                                annual_tax_amount=0.0,
                                annual_insurance_amount=0.0,
                                purchase_price=appraised_value,
                            )

                        prepaids_total = prepaid_items.get("total", 0)
                        financed_closing_costs = 0  # Costs paid from proceeds, not financed
                        cash_needed = 0  # No cash needed from borrower

                        # Calculate cash received = New loan amount - Current balance - Closing costs - Prepaids + Credits
                        total_credits = refinance_lender_credit
                        cash_received = (
                            target_loan_amount
                            - current_balance
                            - total_closing_costs
                            - prepaids_total
                            + total_credits
                        )

                        self.logger.info(
                            f"Cash-out refinance - Target LTV: {target_ltv_value}%, New loan amount: ${new_loan_amount:.2f}, Cash received: ${cash_received:.2f}"
                        )
                    else:
                        # Rate/term or streamline refinance: borrower may need to bring cash
                        cash_needed = preliminary_loan_amount - target_loan_amount

                        # If borrower needs to bring cash, closing costs are NOT financed
                        if cash_needed > 0:
                            financed_closing_costs = 0  # Closing costs paid out of pocket
                            self.logger.info(
                                f"Rate/term refinance - Target LTV: {target_ltv_value}%, New loan amount: ${new_loan_amount:.2f}, Cash needed: ${cash_needed:.2f}, Closing costs paid out of pocket"
                            )
                        else:
                            # If no cash needed, closing costs remain financed
                            self.logger.info(
                                f"Rate/term refinance - Target LTV: {target_ltv_value}%, New loan amount: ${new_loan_amount:.2f}, No cash needed (loan amount sufficient)"
                            )
                else:
                    # Standard refinance - finance all costs
                    new_loan_amount = preliminary_loan_amount
                    cash_needed = 0
                    self.logger.info(f"Standard mode - New loan amount: ${new_loan_amount:.2f}")

            # 4. Validate refinance parameters with final loan amount (after cash contributions)
            validation_errors = self._validate_refinance_parameters(
                loan_type=loan_type,
                refinance_type=refinance_type,
                appraised_value=appraised_value,
                loan_amount_for_ltv=new_loan_amount,
                new_interest_rate=new_interest_rate,
                original_interest_rate=original_interest_rate,
            )

            if validation_errors:
                raise ValueError(f"Refinance validation failed: {'; '.join(validation_errors)}")

            # 5. Calculate LTV
            ltv = 100 * new_loan_amount / appraised_value if appraised_value else 0
            self.logger.info(f"Calculated LTV: {ltv: .2f}%")

            # 6. Calculate new monthly payment
            new_monthly_payment = self.calculate_monthly_payment(
                principal=new_loan_amount,
                annual_rate=new_interest_rate,
                years=new_loan_term,
            )

            # 7. Discount points cost (for reporting purposes, already included in closing_costs_details)
            discount_points_cost = closing_costs_details.get("discount_points", 0.0)

            # 8. Total financed closing costs (discount points already included in closing_costs_details)
            total_financed_closing_costs = financed_closing_costs

            # 9. Monthly savings (including extra savings like eliminated MI)
            base_monthly_savings = orig_monthly_payment - new_monthly_payment
            monthly_savings = base_monthly_savings + extra_monthly_savings

            # 10. Break-even in months
            break_even_months = (
                total_financed_closing_costs / monthly_savings if monthly_savings > 0 else None
            )
            break_even_time = None
            if break_even_months:
                years_part = int(break_even_months // 12)
                months_part = int(round(break_even_months % 12))
                break_even_time = f"{years_part} years, {months_part} months"

            # 11. Total savings over new loan term
            total_savings = (
                monthly_savings * new_loan_term * 12 - total_financed_closing_costs
                if monthly_savings > 0
                else 0
            )

            # 12. Cash to close - will be recalculated later after prepaids are determined
            # For now, store the cash contribution amount for cash scenarios
            if refinance_type == "cash_out" and cash_option == "target_ltv":
                cash_contribution = 0  # No cash contribution for cash-out (they receive cash)
            else:
                cash_contribution = cash_needed

            # 13. Minimum appraised values will be calculated after final loan amount is determined

            # 14. Calculate detailed monthly payment breakdown
            # Use actual tax and insurance amounts provided by user
            if annual_taxes is not None and annual_insurance is not None:
                monthly_tax = annual_taxes / 12
                monthly_insurance = annual_insurance / 12
            else:
                # Fallback to estimates if not provided
                estimated_annual_tax_rate = 1.3  # 1.3% - Georgia average
                estimated_annual_insurance_rate = 1.1  # 1.1% - typical homeowner's insurance
                monthly_tax = (appraised_value * estimated_annual_tax_rate / 100) / 12
                monthly_insurance = (appraised_value * estimated_annual_insurance_rate / 100) / 12

            monthly_hoa = monthly_hoa_fee

            # Calculate mortgage insurance if needed
            ltv_for_mi = (new_loan_amount / appraised_value) * 100
            mortgage_insurance = self.calculate_mortgage_insurance(
                loan_amount=new_loan_amount,
                home_value=appraised_value,
                loan_type=loan_type,
                loan_term_months=new_loan_term * 12,
            )

            # Principal and interest (already calculated as new_monthly_payment)
            principal_interest = new_monthly_payment

            # Total monthly payment including PITI + HOA
            total_monthly_payment = (
                principal_interest
                + monthly_tax
                + monthly_insurance
                + mortgage_insurance
                + monthly_hoa
            )

            # 15. Calculate prepaid items for refinance
            if zero_cash_to_close:
                # In zero cash mode, prepaids were already calculated and added to loan amount
                prepaid_items = preliminary_prepaid_items
            else:
                # Standard mode - calculate prepaids with final loan amount
                # Use the provided closing date or default to today
                if new_closing_date:
                    try:
                        refinance_closing_date = datetime.strptime(
                            new_closing_date, "%Y-%m-%d"
                        ).date()
                    except ValueError:
                        refinance_closing_date = date.today()
                else:
                    refinance_closing_date = date.today()

                # Calculate prepaid items using actual amounts
                if annual_taxes is not None and annual_insurance is not None:
                    # Use custom calculation for refinance with exact amounts
                    prepaid_items = self._calculate_refinance_prepaids(
                        loan_amount=new_loan_amount,
                        annual_taxes=annual_taxes,
                        annual_insurance=annual_insurance,
                        annual_interest_rate=new_interest_rate,
                        closing_date=refinance_closing_date,
                        tax_escrow_months=tax_escrow_months,
                        insurance_escrow_months=insurance_escrow_months,
                    )
                else:
                    # Fallback to standard calculation with rates
                    annual_tax_rate = (
                        (annual_taxes or (appraised_value * 1.3 / 100)) / appraised_value
                    ) * 100
                    annual_insurance_rate = (
                        (annual_insurance or (appraised_value * 1.1 / 100)) / appraised_value
                    ) * 100
                    prepaid_items = self.calculate_prepaid_items(
                        loan_amount=new_loan_amount,
                        annual_tax_rate=annual_tax_rate,
                        annual_insurance_rate=annual_insurance_rate,
                        annual_interest_rate=new_interest_rate,
                        closing_date=refinance_closing_date,
                        tax_method="percentage",
                        insurance_method="percentage",
                        annual_tax_amount=0.0,
                        annual_insurance_amount=0.0,
                        purchase_price=appraised_value,
                    )

            # 16. Calculate credits (lender credits, etc.)
            lender_credit = refinance_lender_credit
            seller_credit = 0  # Not applicable for refinance
            total_credits = lender_credit

            # 17. Calculate cash to close (prepaids + cash contribution - credits)
            if zero_cash_to_close:
                # Zero cash mode - borrower brings nothing to closing
                cash_to_close = 0
                self.logger.info("Zero cash mode - Cash to close set to $0.00")
            elif refinance_type == "cash_out":
                # Cash-out refinance - borrower receives cash (negative value means they bring cash)
                cash_to_close = (
                    -cash_received
                )  # Negative of cash received (positive means they bring cash)
                self.logger.info(
                    f"Cash-out refinance - Cash to close: ${cash_to_close:.2f} (negative of cash received: ${cash_received:.2f})"
                )
            else:
                # Standard mode - borrower pays prepaids plus any cash contribution minus credits
                prepaids_total = prepaid_items.get("total", 0)
                cash_to_close = prepaids_total + cash_contribution - total_credits
                self.logger.info(
                    f"Cash to close: ${cash_to_close:.2f} (prepaids: ${prepaids_total:.2f} + cash contribution: ${cash_contribution:.2f} - credits: ${total_credits:.2f})"
                )

            # 18. Calculate minimum appraised values for LTV targets using final loan amount
            # This needs to account for the fact that in zero cash mode, closing costs and prepaids are financed
            # So we need to work backwards: if we want 80% LTV, what appraised value do we need?
            ltv_targets = [80, 90, 95]

            # Add maximum LTV based on loan type and refinance type
            max_ltv_limits = {
                "conventional": {"rate_term": 97.0, "cash_out": 80.0, "streamline": 97.0},
                "fha": {"rate_term": 96.5, "cash_out": 80.0, "streamline": 96.5},
                "va": {"rate_term": 100.0, "cash_out": 100.0, "streamline": 100.0},
                "usda": {"rate_term": 100.0, "cash_out": 0.0, "streamline": 100.0},
            }

            max_ltv = max_ltv_limits.get(loan_type, {}).get(refinance_type)
            if max_ltv and max_ltv > 0 and max_ltv not in ltv_targets:
                ltv_targets.append(max_ltv)

            min_appraised_values = {}

            for ltv_target in ltv_targets:
                # For zero cash mode, the final loan amount includes current balance + closing costs + prepaids
                # For target LTV modes, we need to calculate what appraised value would be needed to support this loan amount
                if zero_cash_to_close:
                    # In zero cash, the loan amount is current_balance + costs + prepaids
                    # We need: (current_balance + costs + prepaids) / appraised_value = ltv_target / 100
                    # So: appraised_value = (current_balance + costs + prepaids) / (ltv_target / 100)
                    required_appraised_value = new_loan_amount / (ltv_target / 100)
                else:
                    # In standard mode, we assume only current balance for LTV calculation
                    # (since additional costs would be paid cash or financed based on scenario)
                    required_appraised_value = current_balance / (ltv_target / 100)

                # Round up to nearest thousand
                # Use integer key for consistent lookup (e.g., ltv_97 instead of ltv_97.0)
                ltv_key = f"ltv_{int(ltv_target)}"
                min_appraised_values[ltv_key] = math.ceil(required_appraised_value / 1000) * 1000

            self.logger.info(f"Minimum appraised values calculated: {min_appraised_values}")

            # No acceleration analysis for refinance (removed extra monthly payment field)

            return {
                "current_balance": round(current_balance, 2),
                "ltv": round(ltv, 2),
                "new_loan_amount": round(new_loan_amount, 2),
                "original_monthly_payment": round(orig_monthly_payment, 2),
                "new_monthly_payment": round(new_monthly_payment, 2),
                "monthly_savings": round(monthly_savings, 2),
                "base_monthly_savings": round(base_monthly_savings, 2),
                "extra_monthly_savings": round(extra_monthly_savings, 2),
                "refinance_lender_credit": round(refinance_lender_credit, 2),
                "use_manual_balance": use_manual_balance,
                "manual_current_balance": round(manual_current_balance, 2)
                if use_manual_balance
                else None,
                "cash_option": cash_option,
                "target_ltv_value": target_ltv_value if cash_option == "target_ltv" else None,
                "cash_needed_at_closing": round(cash_contribution, 2),
                "cash_received": round(cash_received, 2),
                "refinance_type": refinance_type,
                "loan_type": loan_type,
                "break_even_months": round(break_even_months, 1) if break_even_months else None,
                "break_even_time": break_even_time,
                "total_savings": round(total_savings, 2),
                "discount_points_cost": round(discount_points_cost, 2),
                "discount_points_percent": round(new_discount_points, 3),
                "total_financed_closing_costs": round(total_financed_closing_costs, 2),
                "total_closing_costs": round(total_closing_costs, 2),
                "financed_closing_costs": round(financed_closing_costs, 2),
                "loan_increase": round(
                    new_loan_amount - current_balance, 2
                ),  # Explicitly show the loan increase
                "cash_to_close": round(cash_to_close, 2),
                "zero_cash_mode": zero_cash_to_close,  # Flag to indicate zero cash mode
                "min_appraised_values": min_appraised_values,
                "closing_costs_details": closing_costs_details,
                # Add detailed monthly payment breakdown
                "monthly_breakdown": {
                    "principal_interest": round(principal_interest, 2),
                    "property_tax": round(monthly_tax, 2),
                    "insurance": round(monthly_insurance, 2),
                    "hoa": round(monthly_hoa, 2),
                    "pmi": round(mortgage_insurance, 2),
                    "total": round(total_monthly_payment, 2),
                },
                # Add prepaid items
                "prepaid_items": prepaid_items,
                # Add credits
                "credits": {
                    "lender_credit": round(refinance_lender_credit, 2),
                    "total": round(refinance_lender_credit, 2),
                },
            }
        except Exception as e:
            self.logger.error(f"Error in calculate_refinance: {e}")
            import traceback

            self.logger.error(traceback.format_exc())
            return {"error": str(e)}
