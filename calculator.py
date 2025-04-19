import calendar
import copy
import logging
from calendar import isleap, monthrange
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Dict, Optional

from calculations.title_insurance import (
    calculate_lenders_title_insurance,
    calculate_owners_title_insurance,
)
from config_manager import ConfigManager
from financed_fees import calculate_fha_ufmip, calculate_usda_upfront_fee
from financed_fees import calculate_va_funding_fee as calculate_external_va_funding_fee
from mortgage_insurance import calculate_conventional_pmi, calculate_fha_mip, calculate_usda_fee

print(f"[calculator.py] __name__ = {__name__}")
print(
    f"[calculator.py] calculate_lenders_title_insurance.__module__ = {calculate_lenders_title_insurance.__module__}"
)


class MortgageCalculator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing MortgageCalculator")
        self.config_manager = ConfigManager()
        self.config = self.config_manager.get_config()
        self.logger.info("Loaded configuration")

    def calculate_monthly_payment(self, principal: float, annual_rate: float, years: int) -> float:
        """Calculate the monthly mortgage payment using Decimal for precision."""
        try:
            # Convert inputs to Decimal
            principal_d = Decimal(str(principal))
            annual_rate_d = Decimal(str(annual_rate))
            years_d = Decimal(str(years))

            self.logger.info(
                f"Calculating monthly payment: principal={principal_d}, rate={annual_rate_d.quantize(Decimal('0.001'))}, years={years_d}"
            )

            if annual_rate_d == Decimal("0"):
                # Use Decimal for division
                payment_d = (principal_d / (years_d * Decimal("12"))).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
                self.logger.info(f"Zero interest rate, monthly payment: {payment_d}")
                return float(payment_d)  # Return as float to match type hint

            # Ensure rate is handled correctly
            monthly_rate_d = annual_rate_d / Decimal("12") / Decimal("100")
            num_payments_d = years_d * Decimal("12")

            # Calculate using Decimal exponentiation and arithmetic
            if monthly_rate_d == Decimal("0"):  # Should have been caught above, but safety check
                payment_d = (principal_d / num_payments_d).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
            else:
                factor = (Decimal("1") + monthly_rate_d) ** num_payments_d
                payment_d = principal_d * (monthly_rate_d * factor) / (factor - Decimal("1"))

            # Quantize to 2 decimal places using ROUND_HALF_UP
            rounded_payment_d = payment_d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            self.logger.info(f"Monthly payment calculated: {rounded_payment_d}")
            # Return as float to match original function signature
            return float(rounded_payment_d)

        except Exception as e:
            self.logger.error(f"Error calculating monthly payment: {e}")
            raise

    def calculate_mortgage_insurance(
        self,
        loan_amount: float,
        home_value: float,
        loan_type: str,
        loan_term_months: int = 360,
    ) -> float:
        """
        Calculate monthly mortgage insurance (private/conventional or government MIP) based on
        loan type, loan amount, and LTV. Dispatches to specific calculation functions.

        Parameters:
            loan_amount (float): Amount being borrowed
            home_value (float): Total value/purchase price of the home
            loan_type (str): Type of loan ('conventional', 'fha', 'va', 'usda')
            loan_term_months (int): Loan term in months

        Returns:
            float: Monthly mortgage insurance premium
        """
        try:
            self.logger.info(
                f"Calculating mortgage insurance: loan_amount=${loan_amount:,.0f}, "
                f"home_value=${home_value:,.0f}, loan_type={loan_type}"
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
                self.logger.info("VA loans do not have monthly mortgage insurance, returning 0")
                return 0.0

            else:
                # Handle unknown or types without monthly MI
                self.logger.info(
                    f"No monthly mortgage insurance configured or needed for loan type: {loan_type}"
                )
                return 0.0

        except Exception as e:
            # Log the error originating from this dispatcher or re-raised from helpers
            self.logger.error(f"Error calculating mortgage insurance: {e}")
            raise  # Re-raise to allow higher-level handling

    def calculate_financed_fees(
        self,
        loan_amount: float,
        home_value: float,  # Keep for potential future use, but not used now
        loan_type: str,
        down_payment_percentage: float,
        va_service_type: str = None,
        va_usage: str = None,
        va_disability_exempt: bool = False,
    ) -> float:
        """
        Calculate financed fees based on loan type by dispatching to dedicated functions.
        - Conventional: No financed fees
        - FHA: Upfront MIP
        - VA: Funding fee
        - USDA: Upfront guarantee fee
        """
        try:
            self.logger.info(
                f"Calculating financed fees: loan_type={loan_type}, loan_amount=${loan_amount:,.2f}"
            )
            loan_type = loan_type.lower()

            # Fetch relevant config sections needed by helper functions
            pmi_rates_config = self.config.get("pmi_rates", {})
            loan_types_config = self.config.get("loan_types", {})

            if loan_type == "conventional":
                self.logger.info("No upfront financed fees for conventional loans")
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
                    f"va_usage={va_usage}, disability_exempt={va_disability_exempt}"
                )

                va_config = loan_types_config.get("va", {})  # Get VA specific config
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
                self.logger.info(f"VA funding fee result: ${total_financed_fees:.2f}")
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
            self.logger.error(f"Error calculating financed fees dispatch: {e}")
            # Log specific parameters that might be relevant
            self.logger.error(
                f"Parameters at time of error: loan_type={loan_type}, loan_amount={loan_amount}, dp%={down_payment_percentage}, va_service={va_service_type}, va_usage={va_usage}, va_exempt={va_disability_exempt}"
            )
            raise  # Re-raise after logging context

    def calculate_all(
        self,
        purchase_price: float,
        down_payment_percentage: float = None,
        down_payment: float = None,
        annual_rate: float = 6.5,
        loan_term: int = 30,
        annual_tax_rate: float = 1.0,
        annual_insurance_rate: float = 0.48,
        loan_type: str = "conventional",
        monthly_hoa_fee: float = 0.0,
        seller_credit: float = 0.0,
        lender_credit: float = 0.0,
        discount_points: float = 0.0,
        va_service_type: Optional[str] = None,
        va_usage: Optional[str] = None,
        va_disability_exempt: bool = False,
        closing_date: Optional[date] = None,
        include_owners_title: bool = True,
    ) -> Dict[str, Any]:
        """
        Calculate full mortgage details with all components.

        Parameters:
            purchase_price (float): Purchase price of the home ($)
            down_payment_percentage (float, optional): Down payment as percentage of purchase price (%)
            down_payment (float, optional): Down payment amount ($) - Deprecated, use down_payment_percentage instead
            annual_rate (float): Annual interest rate (%)
            loan_term (int): Loan term in years
            annual_tax_rate (float): Annual property tax rate (%)
            annual_insurance_rate (float): Annual home insurance rate (%)
            loan_type (str): Type of loan ('conventional', 'fha', 'va', 'usda')
            monthly_hoa_fee (float, optional): Monthly HOA fee ($)
            seller_credit (float, optional): Seller credit toward closing costs ($)
            lender_credit (float, optional): Lender credit toward closing costs ($)
            discount_points (float, optional): Discount points to buy down the rate (%)
            va_service_type (str, optional): For VA loans, type of service ('active' or 'reserves')
            va_usage (str, optional): For VA loans, loan usage ('first' or 'subsequent')
            va_disability_exempt (bool, optional): For VA loans, whether exempt from funding fee
            closing_date (date, optional): Closing date for prepaid interest calculation
            include_owners_title (bool, optional): Whether to include owner's title insurance

        Returns:
            Dict[str, Any]: Dictionary with calculated mortgage details
        """
        try:
            self.logger.info(
                f"Calculating mortgage details: price={purchase_price}, down_payment={down_payment_percentage}%, "
                f"rate={annual_rate}%, term={loan_term}y, type={loan_type}, tax={annual_tax_rate}%, ins={annual_insurance_rate}%"
            )

            # Ensure closing date has the right type
            if closing_date and isinstance(closing_date, str):
                try:
                    self.logger.info(
                        f"Converting closing date string {closing_date} to date object"
                    )
                    closing_date = datetime.strptime(closing_date, "%Y-%m-%d").date()
                    self.logger.info(f"Converted closing date: {closing_date}")
                except ValueError:
                    self.logger.error(f"Invalid closing date format: {closing_date}")
                    closing_date = None

            # Ensure down payment is calculated properly
            if down_payment_percentage is not None:
                down_payment_amount = purchase_price * (down_payment_percentage / 100)
                self.logger.info(
                    f"Using provided down payment percentage: {down_payment_percentage}% = ${down_payment_amount:.2f}"
                )
            elif down_payment is not None:
                down_payment_amount = down_payment
                down_payment_percentage = (down_payment / purchase_price) * 100
                self.logger.info(
                    f"Using provided down payment amount: ${down_payment} = {down_payment_percentage:.2f}%"
                )
            else:
                # Default to 20% down if nothing provided
                down_payment_percentage = 20
                down_payment_amount = purchase_price * 0.2
                self.logger.info(
                    f"No down payment specified, using default: {down_payment_percentage}% = ${down_payment_amount:.2f}"
                )

            # Calculate loan amount
            loan_amount = purchase_price - down_payment_amount
            self.logger.info(
                f"Calculated loan amount: {purchase_price} - {down_payment_amount} = {loan_amount}"
            )

            # Calculate LTV (Loan-to-Value) ratio
            ltv_ratio = (loan_amount / purchase_price) * 100
            self.logger.info(f"Calculated LTV ratio: {ltv_ratio:.2f}%")

            # Add financed fees to loan amount for government loans
            financed_fees = self.calculate_financed_fees(
                loan_amount,
                purchase_price,
                loan_type,
                down_payment_percentage,
                va_service_type,
                va_usage,
                va_disability_exempt,
            )
            self.logger.info(f"Calculated financed fees: ${financed_fees:.2f}")

            original_loan_amount = loan_amount
            if financed_fees > 0:
                loan_amount += financed_fees
                self.logger.info(
                    f"Added financed fees to loan amount: {original_loan_amount} + {financed_fees} = {loan_amount}"
                )

            # Calculate monthly P&I
            principal_interest = self.calculate_monthly_payment(loan_amount, annual_rate, loan_term)
            self.logger.info(f"Calculated P&I: ${principal_interest:.2f}")

            # Calculate monthly tax
            monthly_tax = (purchase_price * annual_tax_rate / 100) / 12
            self.logger.info(f"Calculated monthly tax: ${monthly_tax:.2f}")

            # Calculate monthly insurance
            monthly_insurance = (loan_amount * annual_insurance_rate / 100) / 12
            self.logger.info(f"Calculated monthly insurance: ${monthly_insurance:.2f}")

            # Calculate monthly mortgage insurance
            mortgage_insurance = self.calculate_mortgage_insurance(
                loan_amount, purchase_price, loan_type, loan_term * 12
            )
            self.logger.info(f"Calculated mortgage insurance: ${mortgage_insurance:.2f}")

            # Calculate total monthly payment
            total_payment = (
                principal_interest
                + monthly_tax
                + monthly_insurance
                + monthly_hoa_fee
                + mortgage_insurance
            )
            self.logger.info(f"Calculated total monthly payment: ${total_payment:.2f}")

            # Calculate closing costs
            closing_costs_details = self.calculate_closing_costs(
                purchase_price=purchase_price,
                loan_amount=original_loan_amount,  # Use original loan amount for cost calc
                include_owners_title=include_owners_title,
                discount_points=discount_points,  # Pass discount points here
            )
            self.logger.info(f"Closing costs details: {closing_costs_details}")

            # Calculate prepaid items
            prepaid_items = self.calculate_prepaid_items(
                loan_amount,
                annual_tax_rate,
                annual_insurance_rate,
                annual_rate,
                closing_date,
            )
            self.logger.info(f"Calculated prepaid items: ${prepaid_items['total']:.2f}")

            # Calculate maximum seller contribution based on loan type and LTV
            max_seller_contribution = self._calculate_max_seller_contribution(
                loan_type, ltv_ratio, purchase_price
            )
            self.logger.info(f"Maximum seller contribution: ${max_seller_contribution:.2f}")

            # Check if the seller credit exceeds the maximum allowed
            seller_credit_exceeds_max = seller_credit > max_seller_contribution
            if seller_credit_exceeds_max:
                self.logger.warning(
                    f"Seller credit (${seller_credit:.2f}) exceeds maximum allowed (${max_seller_contribution:.2f})"
                )

            # Extract tax escrow adjustment (seller's tax proration) if it exists
            seller_tax_credit = 0
            if "tax_escrow_adjustment" in prepaid_items:
                seller_tax_credit = abs(prepaid_items["tax_escrow_adjustment"])
                self.logger.info(f"Seller tax credit (proration): ${seller_tax_credit:.2f}")

            # Add seller's tax proration to the credits
            total_credits = seller_credit + lender_credit + seller_tax_credit
            self.logger.info(
                f"Total credits: Seller (${seller_credit:.2f}) + Lender (${lender_credit:.2f}) + "
                f"Tax Proration (${seller_tax_credit:.2f}) = ${total_credits:.2f}"
            )

            # Calculate total cash needed at closing
            total_cash_needed = (
                down_payment_amount
                + closing_costs_details["total"]
                + prepaid_items["total"]
                - total_credits
            )
            self.logger.info(
                f"Total cash needed: Down payment (${down_payment_amount:.2f}) + "
                f"Closing costs (${closing_costs_details['total']:.2f}) + "
                f"Prepaid items (${prepaid_items['total']:.2f}) - "
                f"Credits (${total_credits:.2f}) = ${total_cash_needed:.2f}"
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
            self.logger.error(f"Error in calculate_all: {e}")
            import traceback

            self.logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    def calculate_closing_costs(
        self,
        purchase_price: float,
        loan_amount: float,
        include_owners_title: bool = True,
        discount_points: float = 0.0,
    ) -> Dict[str, float]:
        """Calculate itemized closing costs based on configuration."""
        try:
            self.logger.info(
                f"Calculating closing costs for purchase price: ${purchase_price:,.2f}, loan amount: ${loan_amount:,.2f}, include_owners: {include_owners_title}, discount_points: {discount_points}"
            )

            # Initialize with empty structure
            closing_costs = {}
            total = 0.0

            # Get the closing costs configuration and title insurance config
            closing_costs_config = self.config_manager.get_closing_costs()
            main_config = self.config_manager.get_config()
            title_config = main_config.get("title_insurance", {})

            # For debugging
            self.logger.info(f"Closing costs config type: {type(closing_costs_config).__name__}")
            if isinstance(closing_costs_config, dict):
                self.logger.info(f"Closing costs config keys: {list(closing_costs_config.keys())}")
            elif isinstance(closing_costs_config, list):
                self.logger.info(f"Closing costs config length: {len(closing_costs_config)}")
            else:
                self.logger.info(
                    f"Unexpected closing costs config type: {type(closing_costs_config).__name__}"
                )

            # Check if we're getting closing costs from a JSON file directly
            if not closing_costs_config and "closing_costs" in self.config:
                # Try to use the closing costs from the main config dictionary
                closing_costs_config = self.config.get("closing_costs", {})
                self.logger.info(
                    f"Using closing costs from main config: {type(closing_costs_config).__name__}"
                )

            # Special handling for dictionary format from closing_costs.json
            if isinstance(closing_costs_config, dict):
                self.logger.info("Processing dictionary-format closing costs configuration")
                for item_name, item_config in closing_costs_config.items():
                    # Skip if marked as not enabled
                    if not item_config.get("enabled", True):
                        continue

                    # Special case for title insurance - use imported functions
                    if (
                        item_name == "lender_title_insurance" or item_name == "title_insurance"
                    ):  # Keep handling 'title_insurance' for backward compat?
                        # Note: include_owners_title is passed directly to determine the rate
                        amount = calculate_lenders_title_insurance(
                            loan_amount, include_owners_title, title_config
                        )
                        closing_costs["lender_title_insurance"] = round(
                            amount, 2
                        )  # Standardize key
                        total += amount
                        self.logger.info(f"Added lender's title insurance: ${amount:.2f}")
                        continue

                    elif (
                        item_name == "owner_title_insurance"
                        or item_name == "owners_title_insurance"
                    ):
                        if include_owners_title:
                            # calculate_owners_title_insurance handles the include_owners_title logic internally
                            amount = calculate_owners_title_insurance(
                                purchase_price,
                                loan_amount,
                                include_owners_title,
                                title_config,
                            )
                            closing_costs["owner_title_insurance"] = round(
                                amount, 2
                            )  # Standardize key
                            total += amount
                            self.logger.info(f"Added owner's title insurance: ${amount:.2f}")
                        else:
                            self.logger.info(
                                "Owner's title insurance skipped as per include_owners_title=False"
                            )
                            closing_costs[
                                "owner_title_insurance"
                            ] = 0.0  # Ensure key exists even if 0
                        continue

                    # Calculate regular fee based on type
                    fee_type = item_config.get("type", "fixed")
                    value = float(item_config.get("value", 0))
                    base = item_config.get("calculation_base", "fixed")

                    if fee_type == "fixed":
                        amount = value
                    elif fee_type == "percentage":
                        if base == "loan_amount":
                            amount = (value / 100) * loan_amount
                        elif base == "purchase_price":
                            amount = (value / 100) * purchase_price
                        else:
                            amount = value  # Default to fixed if base is unknown
                    else:
                        self.logger.warning(f"Unknown fee type {fee_type} for {item_name}")
                        amount = 0

                    closing_costs[item_name] = round(amount, 2)
                    total += amount
                    self.logger.info(
                        f"Added closing cost {item_name}: ${closing_costs[item_name]:.2f}"
                    )

            # Handle list format (if it's used in some configurations)
            elif isinstance(closing_costs_config, list):
                self.logger.info("Processing list-format closing costs configuration")
                for item in closing_costs_config:
                    if not isinstance(item, dict):
                        self.logger.error(
                            f"Closing cost item is not a dictionary: {type(item).__name__}"
                        )
                        continue

                    if not item.get("enabled", True):
                        continue

                    item_name = item.get("name", "")
                    if not item_name:
                        continue

                    # Special case for title insurance - use imported functions
                    if item_name == "lender_title_insurance":
                        # Note: include_owners_title is passed directly to determine the rate
                        amount = calculate_lenders_title_insurance(
                            loan_amount, include_owners_title, title_config
                        )
                        closing_costs["lender_title_insurance"] = round(
                            amount, 2
                        )  # Standardize key
                        total += amount
                        self.logger.info(f"Added lender's title insurance: ${amount:.2f}")
                        continue

                    elif item_name == "owner_title_insurance":
                        if include_owners_title:
                            # calculate_owners_title_insurance handles the include_owners_title logic internally
                            amount = calculate_owners_title_insurance(
                                purchase_price,
                                loan_amount,
                                include_owners_title,
                                title_config,
                            )
                            closing_costs["owner_title_insurance"] = round(
                                amount, 2
                            )  # Standardize key
                            total += amount
                            self.logger.info(f"Added owner's title insurance: ${amount:.2f}")
                        else:
                            self.logger.info(
                                "Owner's title insurance skipped as per include_owners_title=False"
                            )
                            closing_costs[
                                "owner_title_insurance"
                            ] = 0.0  # Ensure key exists even if 0
                        continue

                    # Calculate regular fee based on type
                    fee_type = item.get("fee_type", "flat")
                    base = item.get("amount", 0)

                    if fee_type == "flat":
                        amount = base
                    elif fee_type == "percentage_of_loan":
                        amount = base * loan_amount / 100
                    elif fee_type == "percentage_of_purchase":
                        amount = base * purchase_price / 100
                    elif fee_type == "tiered_rate":
                        self.logger.warning(
                            f"Tiered rate not implemented for {item_name}, using flat fee"
                        )
                        amount = base
                    else:
                        self.logger.warning(f"Unknown fee type {fee_type} for {item_name}, using 0")
                        amount = 0
                        continue

                    closing_costs[item_name] = round(amount, 2)
                    total += amount
                    self.logger.info(f"Added closing cost {item_name}: {closing_costs[item_name]}")
            else:
                self.logger.error(
                    f"Closing costs configuration is neither a dictionary nor a list: {type(closing_costs_config)}"
                )

            # Add discount points cost if applicable
            if discount_points > 0:
                discount_points_cost = loan_amount * (discount_points / 100)
                closing_costs["discount_points"] = round(discount_points_cost, 2)
                total += discount_points_cost
                self.logger.info(
                    f"Added discount points ({discount_points}%): ${discount_points_cost:.2f}"
                )
            elif "discount_points" not in closing_costs:
                # Ensure discount_points is present even if zero, for UI consistency
                closing_costs["discount_points"] = 0.0

            # Add the calculated total to the dictionary
            closing_costs["total"] = round(total, 2)
            self.logger.info(f"Total closing costs calculated: ${total:.2f}")

            return closing_costs
        except Exception as e:
            self.logger.error(f"Error calculating closing costs: {e}")
            import traceback

            self.logger.error(f"Traceback: {traceback.format_exc()}")
            # Return at least a valid dictionary with a total
            return {"total": 0.0}

    def _calculate_prepaid_tax(self, closing_date, monthly_tax: float) -> float:
        """
        Calculate prepaid tax amount based on closing date.

        Formula: Annual tax amount minus the number of accrued escrow payments.
        The borrower has paid from the first payment date through November
        since taxes are due in December. Mortgage payments are made in arrears.

        Parameters:
            closing_date: The closing date of the loan
            monthly_tax: The monthly tax amount

        Returns:
            float: The prepaid tax amount
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
            closing_year = closing_date.year

            # First payment is on the 1st of the month after the closing month
            first_payment_month = (
                closing_month + 2 if closing_month < 11 else (closing_month + 2) % 12
            )
            first_payment_year = (
                closing_year if first_payment_month > closing_month else closing_year + 1
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
                f"Annual tax=${annual_tax:.2f}, "
                f"Accrued escrow payments={accrued_escrow_payments}, "
                f"Prepaid tax amount=${prepaid_tax:.2f}"
            )

            return round(prepaid_tax, 2)

        except Exception as e:
            self.logger.error(f"Error calculating prepaid tax: {str(e)}")
            return 0

    def calculate_prepaid_items(
        self,
        loan_amount: float,
        annual_tax_rate: float,
        annual_insurance_rate: float,
        annual_interest_rate: float,
        closing_date=None,
    ) -> Dict[str, float]:
        """Calculate prepaid items (taxes, insurance, interest)."""
        try:
            self.logger.info(
                f"Calculating prepaid items with loan={loan_amount}, tax_rate={annual_tax_rate}, insurance_rate={annual_insurance_rate}, interest_rate={annual_interest_rate}"
            )
            self.logger.info(
                f"Closing date provided: {closing_date} (type: {type(closing_date).__name__ if closing_date else None})"
            )

            # Make a deep copy of the config to avoid modifying the original
            import copy

            config = copy.deepcopy(self.config["prepaid_items"])
            prepaid = {}

            # 1. Calculate prepaid interest first - this is the most important part
            daily_interest = (loan_amount * annual_interest_rate / 100) / 360
            self.logger.info(
                f"Daily interest calculation: {loan_amount} * {annual_interest_rate}% / 360 = ${daily_interest:.2f}/day"
            )

            # Default to 30 days if no closing date is provided (only as fallback)
            days_of_interest = 30
            self.logger.info(f"Default days of interest (fallback): {days_of_interest}")

            # If we have a closing date, calculate the actual days remaining in the month
            if closing_date:
                try:
                    # Get the last day of the month
                    _, last_day = monthrange(closing_date.year, closing_date.month)
                    last_date_of_month = date(closing_date.year, closing_date.month, last_day)

                    # Calculate days from closing to end of month (inclusive of closing day)
                    days_of_interest = (last_date_of_month - closing_date).days + 1

                    self.logger.info(
                        f"Calculated {days_of_interest} days from closing date {closing_date} to end of month {last_date_of_month}"
                    )
                except Exception as e:
                    self.logger.error(f"Error calculating days from closing date: {str(e)}")
                    self.logger.warning(f"Falling back to default 30 days of interest")
            else:
                self.logger.warning(f"No closing date provided, using default 30 days of interest")

            # Calculate the prepaid interest amount
            prepaid_interest = round(daily_interest * days_of_interest, 2)
            self.logger.info(
                f"Prepaid interest calculation: ${daily_interest:.2f}/day × {days_of_interest} days = ${prepaid_interest:.2f}"
            )
            prepaid["prepaid_interest"] = prepaid_interest

            # 2. Calculate prepaid property tax
            monthly_tax = (loan_amount * annual_tax_rate / 100) / 12

            # Use new calculation method if closing date is provided, otherwise fall back to previous method
            if closing_date:
                prepaid["prepaid_tax"] = self._calculate_prepaid_tax(closing_date, monthly_tax)
            else:
                prepaid["prepaid_tax"] = round(monthly_tax * config["months_tax_prepaid"], 2)

            prepaid["tax_escrow"] = round(monthly_tax * config["months_tax_escrow"], 2)

            # Calculate tax escrow adjustment assuming taxes are due in December
            tax_adjustment = 0
            if closing_date:
                tax_adjustment = self._calculate_tax_escrow_adjustment(
                    closing_date=closing_date, monthly_tax=monthly_tax
                )
                self.logger.info(f"Tax escrow adjustment calculated: ${tax_adjustment:.2f}")
                if tax_adjustment != 0:
                    prepaid["tax_escrow_adjustment"] = tax_adjustment

            self.logger.info(
                f"Property tax calculations: monthly=${monthly_tax:.2f}, prepaid=${prepaid['prepaid_tax']:.2f}, escrow=${prepaid['tax_escrow']:.2f}, adjustment=${tax_adjustment:.2f}"
            )

            # 3. Calculate prepaid homeowner's insurance
            monthly_insurance = (loan_amount * annual_insurance_rate / 100) / 12
            prepaid["prepaid_insurance"] = round(
                monthly_insurance * config["months_insurance_prepaid"], 2
            )
            prepaid["insurance_escrow"] = round(
                monthly_insurance * config["months_insurance_escrow"], 2
            )
            self.logger.info(
                f"Insurance calculations: monthly=${monthly_insurance:.2f}, prepaid=${prepaid['prepaid_insurance']:.2f}, escrow=${prepaid['insurance_escrow']:.2f}"
            )

            # 4. Calculate total
            prepaid["total"] = sum(prepaid.values())
            self.logger.info(f"Total prepaid items: ${prepaid['total']:.2f}")

            return prepaid
        except Exception as e:
            self.logger.error(f"Error in calculate_prepaid_items: {str(e)}")
            raise

    def _calculate_tax_escrow_adjustment(self, closing_date, monthly_tax: float) -> float:
        """
        Calculate tax escrow adjustment for Georgia properties where taxes are paid in arrears.

        In Georgia, property taxes are typically paid in arrears (for the previous year).
        The seller provides the buyer with a credit at closing for the portion of the year
        the seller owned the property. This ensures the buyer has funds to pay the full
        tax bill when it comes due.

        Formula:
        Property Tax Adjustment = (Annual Property Tax Amount × Days Seller Owned Property in Tax Year ÷ 365) - Any Prepaid Taxes

        Parameters:
            closing_date: The closing date of the loan
            monthly_tax: The monthly tax amount

        Returns:
            float: The tax escrow adjustment amount (negative value represents credit to buyer)
        """
        try:
            # If no closing date, no adjustment
            if not closing_date:
                return 0

            # Calculate the annual tax amount
            annual_tax = monthly_tax * 12

            # Calculate days in year and days seller owned property
            days_in_year = 366 if calendar.isleap(closing_date.year) else 365
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
                f"Seller's tax portion=${seller_tax_responsibility:.2f}, "
                f"Buyer credit=${abs(adjustment):.2f}"
            )

            return adjustment
        except Exception as e:
            self.logger.error(f"Error calculating tax escrow adjustment: {str(e)}")
            return 0

    def generate_amortization_data(self, principal: float, annual_rate: float, years: int) -> list:
        """Generate amortization data for yearly principal balance over the loan term."""
        try:
            self.logger.info(
                f"Generating amortization data: principal={principal}, rate={annual_rate}, years={years}"
            )

            if annual_rate == 0:
                # Simple case for zero interest rate
                monthly_payment = principal / (years * 12)
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

            self.logger.info(f"Generated {len(balances)} yearly balance data points")
            return balances

        except Exception as e:
            self.logger.error(f"Error generating amortization data: {e}")
            return [principal] * years  # Return flat line as fallback

    def _calculate_max_seller_contribution(
        self, loan_type: str, ltv_ratio: float, purchase_price: float
    ) -> float:
        """
        Calculate maximum seller contribution based on loan type and LTV ratio.

        For most conventional loans:
        - LTV > 90%: maximum 3% of purchase price
        - LTV 75.01-90%: maximum 6% of purchase price
        - LTV ≤ 75%: maximum 9% of purchase price

        For FHA loans:
        - Maximum 6% of purchase price

        For VA loans:
        - Maximum 4% of purchase price for certain fees

        Parameters:
            loan_type: Type of loan ('conventional', 'fha', 'va', 'usda')
            ltv_ratio: Loan-to-value ratio (percentage)
            purchase_price: Purchase price of the property

        Returns:
            float: Maximum allowable seller contribution
        """
        try:
            loan_type = loan_type.lower() if isinstance(loan_type, str) else "conventional"

            if loan_type == "fha":
                # FHA allows up to 6% of purchase price
                max_percent = 6.0
                self.logger.info(f"FHA loan: Maximum seller contribution is 6% of purchase price")
            elif loan_type == "va":
                # VA allows up to 4% for certain closing costs
                max_percent = 4.0
                self.logger.info(f"VA loan: Maximum seller contribution is 4% of purchase price")
            elif loan_type == "usda":
                # USDA typically follows similar guidelines to FHA
                max_percent = 6.0
                self.logger.info(f"USDA loan: Maximum seller contribution is 6% of purchase price")
            else:
                # Conventional loan - based on LTV ratio
                if ltv_ratio > 90:
                    max_percent = 3.0
                    self.logger.info(
                        f"Conventional loan with LTV > 90%: Maximum seller contribution is 3% of purchase price"
                    )
                elif ltv_ratio > 75:
                    max_percent = 6.0
                    self.logger.info(
                        f"Conventional loan with 75% < LTV ≤ 90%: Maximum seller contribution is 6% of purchase price"
                    )
                else:
                    max_percent = 9.0
                    self.logger.info(
                        f"Conventional loan with LTV ≤ 75%: Maximum seller contribution is 9% of purchase price"
                    )

            max_contribution = (max_percent / 100) * purchase_price
            self.logger.info(
                f"Maximum seller contribution: {max_percent}% of ${purchase_price:.2f} = ${max_contribution:.2f}"
            )
            return round(max_contribution, 2)

        except Exception as e:
            self.logger.error(f"Error calculating maximum seller contribution: {str(e)}")
            # Default to 3% as a safe fallback
            return round(0.03 * purchase_price, 2)
