import copy
import logging
from calendar import monthrange
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Dict, Optional

from config_manager import ConfigManager


class MortgageCalculator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing MortgageCalculator")
        self.config_manager = ConfigManager()
        self.config = self.config_manager.get_config()
        self.logger.info("Loaded configuration")

    def calculate_monthly_payment(
        self, principal: float, annual_rate: float, years: int
    ) -> float:
        """Calculate the monthly mortgage payment."""
        try:
            self.logger.info(
                f"Calculating monthly payment: principal={principal}, rate={round(annual_rate, 3)}, years={years}"
            )
            if annual_rate == 0:
                payment = principal / (years * 12)
                self.logger.info(f"Zero interest rate, monthly payment: {payment}")
                return payment

            # Round annual rate to 3 decimal places for consistent calculations
            annual_rate = round(annual_rate, 3)
            monthly_rate = annual_rate / 12 / 100
            num_payments = years * 12

            payment = (
                principal
                * (monthly_rate * (1 + monthly_rate) ** num_payments)
                / ((1 + monthly_rate) ** num_payments - 1)
            )

            rounded_payment = round(payment, 2)
            self.logger.info(f"Monthly payment calculated: {rounded_payment}")
            return rounded_payment
        except Exception as e:
            self.logger.error(f"Error calculating monthly payment: {e}")
            raise

    def calculate_pmi(
        self,
        loan_amount: float,
        home_value: float,
        loan_type: str,
        loan_term_months: int = 360,
    ) -> float:
        """
        Calculate monthly mortgage insurance based on loan type:
        - Conventional: PMI based on LTV and credit score
        - FHA: Monthly MIP
        - VA: No monthly mortgage insurance
        - USDA: Monthly guarantee fee
        """
        try:
            self.logger.info(
                f"Calculating mortgage insurance: loan={loan_amount}, value={home_value}, type={loan_type}"
            )
            loan_type = loan_type.lower()

            # VA loans do not have monthly mortgage insurance
            if loan_type == "va":
                self.logger.info(
                    "VA loans do not have monthly mortgage insurance, returning 0"
                )
                return 0.0

            # Process conventional loan PMI
            if loan_type == "conventional":
                ltv = round((loan_amount / home_value) * 100, 3)
                self.logger.info(f"Conventional loan PMI calculation: LTV={ltv:.3f}%")

                # No PMI needed if LTV is 80% or below
                if ltv <= 80:
                    self.logger.info("LTV is 80% or below, no PMI required")
                    return 0.0

                pmi_rates = self.config.get("pmi_rates", {}).get("conventional", {})
                if not pmi_rates:
                    self.logger.error("PMI rates not found for conventional loans")
                    raise ValueError("PMI rates not found for conventional loans")

                # Determine LTV rate
                ltv_ranges = pmi_rates.get("ltv_ranges", {})
                if not ltv_ranges:
                    self.logger.error("No LTV ranges defined for PMI calculation")
                    raise ValueError("No LTV ranges defined for PMI calculation")

                # Find the applicable LTV rate
                ltv_rate = 0
                for ltv_range, rate in ltv_ranges.items():
                    # Parse range format "XX-YY"
                    parts = ltv_range.split("-")
                    if len(parts) == 2:
                        min_ltv, max_ltv = float(parts[0]), float(parts[1])
                        if min_ltv <= ltv <= max_ltv:
                            ltv_rate = rate / 100  # Convert from percentage to decimal
                            self.logger.info(
                                f"Selected LTV range for PMI: {ltv_range}%, rate: {round(rate, 3)}%"
                            )
                            break

                if ltv_rate == 0:
                    self.logger.warning(
                        f"No matching LTV range found for {ltv:.1f}%, using default rate"
                    )
                    # Default to highest range if no match found
                    highest_range = max(
                        ltv_ranges.items(), key=lambda x: float(x[0].split("-")[0])
                    )
                    ltv_rate = highest_range[1] / 100
                    self.logger.info(
                        f"Using highest LTV range: {highest_range[0]}%, rate: {round(highest_range[1], 3)}%"
                    )

                # Apply credit score adjustment
                credit_score_adjustments = pmi_rates.get("credit_score_adjustments", {})
                credit_adjustment = 0

                for score_range, adjustment in credit_score_adjustments.items():
                    parts = score_range.split("-")
                    if len(parts) == 2:
                        min_score, max_score = int(parts[0]), int(parts[1])
                        if min_score <= 700 <= max_score:
                            credit_adjustment = adjustment / 100
                            self.logger.info(
                                f"Selected credit score range: {score_range}, adjustment: {adjustment}%"
                            )
                            break

                # Calculate final PMI rate and monthly amount
                annual_pmi_rate = ltv_rate + credit_adjustment
                monthly_pmi = (loan_amount * annual_pmi_rate) / 12

                rounded_pmi = round(monthly_pmi, 2)
                self.logger.info(
                    f"Final monthly PMI for conventional loan: {rounded_pmi}"
                )
                return rounded_pmi

            # Process FHA MIP
            elif loan_type == "fha":
                pmi_rates = self.config.get("pmi_rates", {}).get("fha", {})
                if not pmi_rates:
                    self.logger.error("MIP rates not found for FHA loans")
                    raise ValueError("MIP rates not found for FHA loans")

                # Apply FHA MIP rates based on loan term, loan amount, and LTV
                ltv = (loan_amount / home_value) * 100
                standard_loan_limit = pmi_rates.get("standard_loan_limit", 726200)

                self.logger.info(
                    f"Calculating FHA MIP with loan_term={loan_term_months / 12} years, loan_amount=${loan_amount:,.2f}, ltv={ltv:.2f}%"
                )

                # Determine which rate to use based on loan term
                if loan_term_months / 12 > 15:
                    term_category = "long_term"
                    self.logger.info(
                        f"Using long-term FHA MIP rates (>{loan_term_months / 12} years)"
                    )
                else:
                    term_category = "short_term"
                    self.logger.info(
                        f"Using short-term FHA MIP rates (≤{loan_term_months / 12} years)"
                    )

                # Determine which rate to use based on loan amount
                if loan_amount <= standard_loan_limit:
                    amount_category = "standard_amount"
                    self.logger.info(
                        f"Using standard loan amount FHA MIP rates (≤${standard_loan_limit:,.2f})"
                    )
                else:
                    amount_category = "high_amount"
                    self.logger.info(
                        f"Using high loan amount FHA MIP rates (>${standard_loan_limit:,.2f})"
                    )

                # Determine which rate to use based on LTV
                annual_mip_rate = 0
                try:
                    if term_category == "long_term":
                        if ltv <= 90:
                            ltv_category = "low_ltv"
                            self.logger.info("Using low LTV rate (≤90%)")
                        else:
                            ltv_category = "high_ltv"
                            self.logger.info("Using high LTV rate (>90%)")
                    else:  # short_term
                        if amount_category == "high_amount":
                            if ltv <= 78:
                                ltv_category = "very_low_ltv"
                                self.logger.info("Using very low LTV rate (≤78%)")
                            elif ltv <= 90:
                                ltv_category = "low_ltv"
                                self.logger.info("Using low LTV rate (>78% and ≤90%)")
                            else:
                                ltv_category = "high_ltv"
                                self.logger.info("Using high LTV rate (>90%)")
                        else:  # standard_amount
                            if ltv <= 90:
                                ltv_category = "low_ltv"
                                self.logger.info("Using low LTV rate (≤90%)")
                            else:
                                ltv_category = "high_ltv"
                                self.logger.info("Using high LTV rate (>90%)")

                    # Get the annual MIP rate from the configuration
                    annual_mip_rate = (
                        pmi_rates.get("annual_mip", {})
                        .get(term_category, {})
                        .get(amount_category, {})
                        .get(ltv_category, 0)
                    )
                    if annual_mip_rate == 0:
                        self.logger.warning(
                            f"Could not find specific MIP rate for {term_category}/{amount_category}/{ltv_category}, using default"
                        )
                        # Fallback to default rates
                        annual_mip_rate = 0.55 if term_category == "long_term" else 0.40
                except Exception as e:
                    self.logger.error(f"Error determining FHA MIP rate: {e}")
                    # Fallback to default rates
                    annual_mip_rate = 0.55 if term_category == "long_term" else 0.40

                self.logger.info(f"Selected annual MIP rate: {annual_mip_rate}%")
                # Convert annual MIP rate from percentage to decimal
                annual_mip_rate = annual_mip_rate / 100
                monthly_mip = (
                    loan_amount * annual_mip_rate
                ) / 12  # Using total loan amount including upfront MIP
                rounded_mip = round(monthly_mip, 2)
                self.logger.info(f"Final monthly MIP for FHA loan: ${rounded_mip:.2f}")
                return rounded_mip

            # Process VA guarantee fee
            elif loan_type == "usda":
                loan_config = self.config.get("loan_types", {}).get("usda", {})
                if not loan_config:
                    self.logger.error("Configuration not found for USDA loans")
                    raise ValueError("Configuration not found for USDA loans")

                annual_fee_rate = loan_config.get("annual_fee_rate", 0.35) / 100
                monthly_fee = (loan_amount * annual_fee_rate) / 12
                rounded_fee = round(monthly_fee, 2)
                self.logger.info(
                    f"Final monthly guarantee fee for USDA loan: ${rounded_fee:.2f}"
                )
                return rounded_fee

            # Other loan types
            self.logger.info(
                f"No monthly mortgage insurance for loan type: {loan_type}"
            )
            return 0.0

        except Exception as e:
            self.logger.error(f"Error calculating mortgage insurance: {e}")
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
        loan type, loan amount, and LTV.

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

            # Process conventional PMI
            if loan_type == "conventional":
                # Get PMI rates from configuration
                pmi_rates = self.config.get("pmi_rates", {}).get("conventional", {})
                if not pmi_rates:
                    self.logger.error("PMI rates not found for conventional loans")
                    raise ValueError("PMI rates not found for conventional loans")

                ltv = round((loan_amount / home_value) * 100, 3)
                self.logger.info(f"Conventional loan PMI calculation: LTV={ltv:.3f}%")

                # No PMI needed if LTV is 80% or below
                if ltv <= 80:
                    self.logger.info("LTV is 80% or below, no PMI required")
                    return 0.0

                # Determine LTV rate
                ltv_ranges = pmi_rates.get("ltv_ranges", {})
                if not ltv_ranges:
                    self.logger.error("No LTV ranges defined for PMI calculation")
                    raise ValueError("No LTV ranges defined for PMI calculation")

                # Find the applicable LTV rate
                ltv_rate = 0
                for ltv_range, rate in ltv_ranges.items():
                    # Parse range format "XX-YY"
                    parts = ltv_range.split("-")
                    if len(parts) == 2:
                        min_ltv, max_ltv = float(parts[0]), float(parts[1])
                        if min_ltv <= ltv <= max_ltv:
                            ltv_rate = rate / 100  # Convert from percentage to decimal
                            self.logger.info(
                                f"Selected LTV range for PMI: {ltv_range}%, rate: {round(rate, 3)}%"
                            )
                            break

                if ltv_rate == 0:
                    self.logger.warning(
                        f"No matching LTV range found for {ltv:.1f}%, using default rate"
                    )
                    # Default to highest range if no match found
                    highest_range = max(
                        ltv_ranges.items(), key=lambda x: float(x[0].split("-")[0])
                    )
                    ltv_rate = highest_range[1] / 100
                    self.logger.info(
                        f"Using highest LTV range: {highest_range[0]}%, rate: {round(highest_range[1], 3)}%"
                    )

                # Apply credit score adjustment
                credit_score_adjustments = pmi_rates.get("credit_score_adjustments", {})
                credit_adjustment = 0

                for score_range, adjustment in credit_score_adjustments.items():
                    parts = score_range.split("-")
                    if len(parts) == 2:
                        min_score, max_score = int(parts[0]), int(parts[1])
                        if min_score <= 700 <= max_score:
                            credit_adjustment = adjustment / 100
                            self.logger.info(
                                f"Selected credit score range: {score_range}, adjustment: {adjustment}%"
                            )
                            break

                # Calculate final PMI rate and monthly amount
                annual_pmi_rate = ltv_rate + credit_adjustment
                monthly_pmi = (loan_amount * annual_pmi_rate) / 12

                rounded_pmi = round(monthly_pmi, 2)
                self.logger.info(
                    f"Final monthly PMI for conventional loan: {rounded_pmi}"
                )
                return rounded_pmi

            # Process FHA MIP
            elif loan_type == "fha":
                pmi_rates = self.config.get("pmi_rates", {}).get("fha", {})
                if not pmi_rates:
                    self.logger.error("MIP rates not found for FHA loans")
                    raise ValueError("MIP rates not found for FHA loans")

                # Apply FHA MIP rates based on loan term, loan amount, and LTV
                ltv = (loan_amount / home_value) * 100
                standard_loan_limit = pmi_rates.get("standard_loan_limit", 726200)

                self.logger.info(
                    f"Calculating FHA MIP with loan_term={loan_term_months / 12} years, loan_amount=${loan_amount:,.2f}, ltv={ltv:.2f}%"
                )

                # Determine which rate to use based on loan term
                if loan_term_months / 12 > 15:
                    term_category = "long_term"
                    self.logger.info(
                        f"Using long-term FHA MIP rates (>{loan_term_months / 12} years)"
                    )
                else:
                    term_category = "short_term"
                    self.logger.info(
                        f"Using short-term FHA MIP rates (≤{loan_term_months / 12} years)"
                    )

                # Determine which rate to use based on loan amount
                if loan_amount <= standard_loan_limit:
                    amount_category = "standard_amount"
                    self.logger.info(
                        f"Using standard loan amount FHA MIP rates (≤${standard_loan_limit:,.2f})"
                    )
                else:
                    amount_category = "high_amount"
                    self.logger.info(
                        f"Using high loan amount FHA MIP rates (>${standard_loan_limit:,.2f})"
                    )

                # Determine which rate to use based on LTV
                annual_mip_rate = 0
                try:
                    if term_category == "long_term":
                        if ltv <= 90:
                            ltv_category = "low_ltv"
                            self.logger.info("Using low LTV rate (≤90%)")
                        else:
                            ltv_category = "high_ltv"
                            self.logger.info("Using high LTV rate (>90%)")
                    else:  # short_term
                        if amount_category == "high_amount":
                            if ltv <= 78:
                                ltv_category = "very_low_ltv"
                                self.logger.info("Using very low LTV rate (≤78%)")
                            elif ltv <= 90:
                                ltv_category = "low_ltv"
                                self.logger.info("Using low LTV rate (>78% and ≤90%)")
                            else:
                                ltv_category = "high_ltv"
                                self.logger.info("Using high LTV rate (>90%)")
                        else:  # standard_amount
                            if ltv <= 90:
                                ltv_category = "low_ltv"
                                self.logger.info("Using low LTV rate (≤90%)")
                            else:
                                ltv_category = "high_ltv"
                                self.logger.info("Using high LTV rate (>90%)")

                    # Get the annual MIP rate from the configuration
                    annual_mip_rate = (
                        pmi_rates.get("annual_mip", {})
                        .get(term_category, {})
                        .get(amount_category, {})
                        .get(ltv_category, 0)
                    )
                    if annual_mip_rate == 0:
                        self.logger.warning(
                            f"Could not find specific MIP rate for {term_category}/{amount_category}/{ltv_category}, using default"
                        )
                        # Fallback to default rates
                        annual_mip_rate = 0.55 if term_category == "long_term" else 0.40
                except Exception as e:
                    self.logger.error(f"Error determining FHA MIP rate: {e}")
                    # Fallback to default rates
                    annual_mip_rate = 0.55 if term_category == "long_term" else 0.40

                self.logger.info(f"Selected annual MIP rate: {annual_mip_rate}%")
                # Convert annual MIP rate from percentage to decimal
                annual_mip_rate = annual_mip_rate / 100
                monthly_mip = (
                    loan_amount * annual_mip_rate
                ) / 12  # Using total loan amount including upfront MIP
                rounded_mip = round(monthly_mip, 2)
                self.logger.info(f"Final monthly MIP for FHA loan: ${rounded_mip:.2f}")
                return rounded_mip

            # Process VA guarantee fee
            elif loan_type == "usda":
                loan_config = self.config.get("loan_types", {}).get("usda", {})
                if not loan_config:
                    self.logger.error("Configuration not found for USDA loans")
                    raise ValueError("Configuration not found for USDA loans")

                annual_fee_rate = loan_config.get("annual_fee_rate", 0.35) / 100
                monthly_fee = (loan_amount * annual_fee_rate) / 12
                rounded_fee = round(monthly_fee, 2)
                self.logger.info(
                    f"Final monthly guarantee fee for USDA loan: ${rounded_fee:.2f}"
                )
                return rounded_fee

            # Process VA loans
            elif loan_type == "va":
                self.logger.info(
                    "VA loans do not have monthly mortgage insurance, returning 0"
                )
                return 0.0

            # Other loan types
            self.logger.info(
                f"No monthly mortgage insurance for loan type: {loan_type}"
            )
            return 0.0

        except Exception as e:
            self.logger.error(f"Error calculating mortgage insurance: {e}")
            raise

    def calculate_pmi(
        self,
        loan_amount: float,
        home_value: float,
        loan_type: str,
        loan_term_months: int = 360,
    ) -> float:
        """
        Backward compatibility wrapper for calculate_mortgage_insurance method.

        This method exists for backward compatibility with existing code that calls calculate_pmi.
        New code should use calculate_mortgage_insurance instead.
        """
        self.logger.info("Using backward compatibility wrapper calculate_pmi()")
        return self.calculate_mortgage_insurance(
            loan_amount, home_value, loan_type, loan_term_months
        )

    def calculate_va_funding_fee(
        self,
        loan_amount: float,
        down_payment_percentage: float,
        service_type: str,
        loan_usage: str,
        disability_exempt: bool = False,
    ) -> float:
        """
        Calculate the VA funding fee based on loan amount, down payment, service type, and loan usage.

        Args:
            loan_amount (float): The loan amount
            down_payment_percentage (float): Down payment percentage (0-100)
            service_type (str): 'active' for active duty, 'reserves' for reserves/guard
            loan_usage (str): 'first' for first-time use, 'subsequent' for subsequent use
            disability_exempt (bool): Whether the borrower is exempt from funding fee due to disability

        Returns:
            float: The VA funding fee amount
        """
        # If disability exempt, return 0
        if disability_exempt:
            self.logger.info(
                "VA funding fee exemption applied due to disability status"
            )
            return 0.0

        self.logger.info(
            f"Calculating VA funding fee with loan_amount=${loan_amount:,.2f}, "
            f"down_payment_percentage={down_payment_percentage}%, "
            f"service_type={service_type}, loan_usage={loan_usage}, "
            f"disability_exempt={disability_exempt}"
        )

        try:
            # Get funding fee rates from config
            va_config = self.config.get("loan_types", {}).get("va", {})
            funding_fee_rates = va_config.get("funding_fee_rates", {})

            self.logger.debug(f"Funding fee rates from config: {funding_fee_rates}")

            # Normalize inputs to prevent errors
            service_type = str(service_type).lower() if service_type else "active"
            loan_usage = str(loan_usage).lower() if loan_usage else "first"

            # Validate service type
            if service_type not in ["active", "reserves"]:
                self.logger.warning(
                    f"Invalid service type: {service_type}. Defaulting to 'active'"
                )
                service_type = "active"

            # Validate loan usage
            if loan_usage not in ["first", "subsequent"]:
                self.logger.warning(
                    f"Invalid loan usage: {loan_usage}. Defaulting to 'first'"
                )
                loan_usage = "first"

            # Determine down payment bracket
            if down_payment_percentage < 5:
                dp_bracket = "less_than_5"
            elif down_payment_percentage < 10:
                dp_bracket = "5_to_10"
            else:
                dp_bracket = "10_or_more"

            self.logger.info(f"Selected down payment bracket: {dp_bracket}")

            # Get the service type rates
            service_rates = funding_fee_rates.get("funding_fee", {}).get(service_type)
            if not service_rates:
                self.logger.error(
                    f"No funding fee rates found for service type: {service_type}"
                )
                service_rates = funding_fee_rates.get("funding_fee", {}).get("active")
                self.logger.info(f"Falling back to 'active' service rates")

            self.logger.info(f"Service rates found: {service_rates}")

            # Get bracket rates
            bracket_rates = service_rates.get(dp_bracket)
            if not bracket_rates:
                self.logger.error(
                    f"No funding fee rates found for down payment bracket: {dp_bracket}"
                )
                bracket_rates = service_rates.get("less_than_5")
                self.logger.info(f"Falling back to 'less_than_5' bracket rates")

            self.logger.info(f"Bracket rates found: {bracket_rates}")

            # Get fee rate
            fee_rate = bracket_rates.get(loan_usage)
            if fee_rate is None:
                self.logger.error(
                    f"No funding fee rate found for loan usage: {loan_usage} in bracket {dp_bracket}"
                )
                fee_rate = bracket_rates.get("first")
                self.logger.info(f"Falling back to 'first' fee rate")

            self.logger.info(
                f"Fee rate lookup for {service_type}, {dp_bracket}, {loan_usage}: {fee_rate}"
            )

            # Calculate fee
            fee = loan_amount * (fee_rate / 100)
            self.logger.info(
                f"Calculated VA funding fee: ${fee:.2f} (rate: {fee_rate}%, loan_amount: ${loan_amount:.2f})"
            )

            return fee

        except Exception as e:
            self.logger.error(f"Error calculating VA funding fee: {e}")
            self.logger.error(
                f"Parameters: loan_amount=${loan_amount}, down_payment={down_payment_percentage}%, "
                f"service_type={service_type}, loan_usage={loan_usage}, disability_exempt={disability_exempt}"
            )
            # Default to 2.3% (common first-time use rate) as fallback
            default_fee = loan_amount * 0.023
            self.logger.info(f"Using default fee calculation: ${default_fee:.2f}")
            return default_fee

    def calculate_financed_fees(
        self,
        loan_amount: float,
        home_value: float,
        loan_type: str,
        down_payment_percentage: float,
        va_service_type: str = None,
        va_usage: str = None,
        va_disability_exempt: bool = False,
    ) -> float:
        """
        Calculate financed fees based on loan type:
        - Conventional: No financed fees
        - FHA: Upfront MIP
        - VA: Funding fee
        - USDA: Upfront guarantee fee
        """
        try:
            self.logger.info(
                f"Calculating financed fees: loan_type={loan_type}, loan_amount={loan_amount}"
            )
            loan_type = loan_type.lower()
            total_financed_fees = 0.0

            if loan_type == "conventional":
                # No upfront financed fees for conventional loans
                self.logger.info("No upfront financed fees for conventional loans")
                return 0.0

            elif loan_type == "fha":
                # Calculate FHA upfront MIP
                pmi_rates = self.config.get("pmi_rates", {}).get("fha", {})
                if not pmi_rates:
                    self.logger.error("MIP rates not found for FHA loans")
                    raise ValueError("MIP rates not found for FHA loans")

                upfront_mip_rate = pmi_rates.get("upfront_mip_rate", 1.75) / 100
                upfront_mip = loan_amount * upfront_mip_rate
                total_financed_fees = round(upfront_mip, 2)
                self.logger.info(
                    f"FHA upfront MIP: ${total_financed_fees:.2f} (rate: {upfront_mip_rate * 100}%)"
                )

            elif loan_type == "va":
                # Calculate VA funding fee
                self.logger.info(
                    f"Processing VA loan with parameters: va_service_type={va_service_type}, "
                    f"va_usage={va_usage}, va_disability_exempt={va_disability_exempt}"
                )

                # Check VA parameters - use defaults if not provided
                if not va_service_type:
                    va_service_type = "active"
                    self.logger.warning(
                        f"VA service_type not provided, using default: {va_service_type}"
                    )

                if not va_usage:
                    va_usage = "first"
                    self.logger.warning(
                        f"VA loan_usage not provided, using default: {va_usage}"
                    )

                if va_disability_exempt is None:
                    va_disability_exempt = False
                    self.logger.warning(
                        "VA disability_exempt not provided, using default: False"
                    )

                # Special handling for subsequent use to ensure proper fee calculation
                if va_usage == "subsequent":
                    self.logger.info(
                        "VA loan is marked as 'subsequent use', ensuring proper funding fee calculation"
                    )

                # Now calculate the funding fee
                try:
                    total_financed_fees = self.calculate_va_funding_fee(
                        loan_amount,
                        down_payment_percentage,
                        va_service_type,
                        va_usage,
                        va_disability_exempt,
                    )
                    self.logger.info(
                        f"Successfully calculated VA funding fee: ${total_financed_fees:.2f} for {va_usage} use"
                    )
                except Exception as e:
                    self.logger.error(f"Error in VA funding fee calculation: {e}")
                    # Use a default if calculation fails
                    if not va_disability_exempt:
                        default_fee_rate = (
                            2.3  # Default to 2.3% if unable to calculate precisely
                        )
                        total_financed_fees = round(
                            (loan_amount * default_fee_rate) / 100, 2
                        )
                        self.logger.warning(
                            f"Using default VA funding fee rate: {default_fee_rate}%, fee=${total_financed_fees:.2f}"
                        )
                    else:
                        total_financed_fees = 0.0
                        self.logger.info(
                            "No VA funding fee due to disability exemption"
                        )

            elif loan_type == "usda":
                # Calculate USDA upfront guarantee fee
                loan_config = self.config.get("loan_types", {}).get("usda", {})
                if not loan_config:
                    self.logger.error("Configuration not found for USDA loans")
                    raise ValueError("Configuration not found for USDA loans")

                upfront_fee_rate = loan_config.get("upfront_fee_rate", 1.0) / 100
                upfront_fee = loan_amount * upfront_fee_rate
                total_financed_fees = round(upfront_fee, 2)
                self.logger.info(
                    f"USDA upfront guarantee fee: ${total_financed_fees:.2f} (rate: {upfront_fee_rate * 100}%)"
                )

            return total_financed_fees
        except Exception as e:
            self.logger.error(f"Error calculating financed fees: {e}")
            raise

    def calculate_all(
        self,
        purchase_price: float,
        down_payment: float,
        annual_rate: float,
        loan_term: int,
        annual_tax_rate: float,
        annual_insurance_rate: float,
        loan_type: str,
        hoa_fee: float = 0.0,
        seller_credit: float = 0.0,
        lender_credit: float = 0.0,
        discount_points: float = 0.0,
        va_service_type: str = None,
        va_usage: str = None,
        va_disability_exempt: bool = None,
        closing_date=None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Calculate full mortgage details with all components.

        Parameters:
            purchase_price (float): Purchase price of the home ($)
            down_payment (float): Down payment amount ($)
            annual_rate (float): Annual interest rate (%)
            loan_term (int): Loan term in years
            annual_tax_rate (float): Annual property tax rate (%)
            annual_insurance_rate (float): Annual home insurance rate (%)
            loan_type (str): Type of loan ('conventional', 'fha', 'va', 'usda')
            hoa_fee (float, optional): Monthly HOA fee ($)
            seller_credit (float, optional): Seller credit toward closing costs ($)
            lender_credit (float, optional): Lender credit toward closing costs ($)
            discount_points (float, optional): Discount points to buy down the rate (%)
            va_service_type (str, optional): For VA loans, type of service ('active' or 'reserves')
            va_usage (str, optional): For VA loans, loan usage ('first' or 'subsequent')
            va_disability_exempt (bool, optional): For VA loans, whether exempt from funding fee
            closing_date (date, optional): Closing date for prepaid interest calculation

        Returns:
            Dict[str, Any]: Dictionary with calculated mortgage details
        """
        try:
            self.logger.info(
                f"Starting mortgage calculation: price=${purchase_price:,.0f}, down_payment=${down_payment:,.0f}, "
                f"rate={annual_rate}%, term={loan_term} years, loan_type={loan_type}"
            )
            self.logger.info(
                f"Received closing_date: {closing_date} (type: {type(closing_date).__name__ if closing_date else None})"
            )

            # Convert inputs to proper formats
            loan_type = loan_type.lower()
            down_payment_amount = float(down_payment)
            down_payment_percentage = round(
                (down_payment_amount / purchase_price) * 100, 3
            )

            # Calculate base loan amount (before any financed fees)
            base_loan_amount = purchase_price - down_payment_amount
            base_ltv = round((base_loan_amount / purchase_price) * 100, 3)

            self.logger.info(
                f"Base calculations: down_payment=${down_payment_amount:,.2f}, "
                f"down_payment_percentage={down_payment_percentage:.3f}%, loan_type={loan_type}"
            )

            # VA loan specific handling
            if loan_type == "va":
                self.logger.info(
                    f"VA loan parameters: service_type={va_service_type}, usage={va_usage}, "
                    f"disability_exempt={va_disability_exempt}"
                )

                # Normalize VA parameters
                if va_service_type:
                    va_service_type = va_service_type.lower()
                if va_usage:
                    va_usage = va_usage.lower()

            # Calculate financed fees (important for FHA, VA, USDA loans)
            financed_fees = self.calculate_financed_fees(
                base_loan_amount,
                purchase_price,
                loan_type,
                down_payment_percentage,
                va_service_type,
                va_usage,
                va_disability_exempt,
            )

            # Initialize loan amount (may be adjusted with financed fees)
            loan_amount = base_loan_amount

            if financed_fees > 0:
                loan_amount += financed_fees
                fee_type = {
                    "fha": "upfront MIP",
                    "va": "funding fee",
                    "usda": "guarantee fee",
                }.get(loan_type.lower(), "financed fee")

                self.logger.info(
                    f"Added {loan_type} {fee_type} to loan amount: ${financed_fees:.2f}"
                )
                self.logger.info(
                    f"Final loan amount (after adding {fee_type}): ${loan_amount:,.2f}"
                )

            # Get loan type specific configuration
            loan_config = self.config_manager.get_loan_type_config(loan_type)
            if not loan_config:
                raise ValueError(f"Invalid loan type: {loan_type}")

            # Default credit score of 700 for PMI calculations
            credit_score = 700

            # Calculate monthly principal and interest
            monthly_pi = self.calculate_monthly_payment(
                loan_amount, annual_rate, loan_term
            )

            # Calculate monthly mortgage insurance (PMI/MIP/guarantee fee)
            if loan_type.lower() == "fha":
                monthly_mi = self.calculate_mortgage_insurance(
                    loan_amount, purchase_price, loan_type, loan_term * 12
                )
            else:
                monthly_mi = self.calculate_mortgage_insurance(
                    base_loan_amount, purchase_price, loan_type, loan_term * 12
                )

            # Calculate monthly tax and insurance
            monthly_tax = (purchase_price * annual_tax_rate / 100) / 12
            monthly_insurance = (purchase_price * annual_insurance_rate / 100) / 12

            # Calculate total monthly payment
            monthly_payment = (
                monthly_pi + monthly_mi + monthly_tax + monthly_insurance + hoa_fee
            )
            self.logger.info(
                f"Monthly payment breakdown: P&I=${monthly_pi:.2f}, MI=${monthly_mi:.2f}, "
                f"Tax=${monthly_tax:.2f}, Insurance=${monthly_insurance:.2f}, HOA=${hoa_fee:.2f}, "
                f"Total=${monthly_payment:.2f}"
            )

            # Calculate closing costs
            closing_costs = self.calculate_closing_costs(purchase_price, loan_amount)

            # Add discount points to closing costs if applicable
            if discount_points > 0:
                points_cost = (discount_points / 100) * base_loan_amount
                closing_costs["discount_points"] = round(points_cost, 2)
                closing_costs["total"] += points_cost
                self.logger.info(
                    f"Added discount points to closing costs: points={discount_points}%, cost=${points_cost:,.2f}"
                )

            # Calculate prepaid items
            prepaid_items = self.calculate_prepaid_items(
                loan_amount,
                annual_tax_rate,
                annual_insurance_rate,
                annual_rate,
                closing_date,
            )

            # Apply credits
            total_credits = seller_credit + lender_credit
            net_closing_costs = (
                closing_costs["total"] + prepaid_items["total"] - total_credits
            )
            self.logger.info(
                f"Credits and final costs: credits=${total_credits:,.2f}, net_closing_costs=${net_closing_costs:,.2f}"
            )

            # Prepare detailed results
            results = {
                "loan_details": {
                    "purchase_price": purchase_price,
                    "down_payment": down_payment_amount,
                    "down_payment_percentage": round(down_payment_percentage, 3),
                    "base_loan_amount": base_loan_amount,
                    "loan_amount": loan_amount,
                    "loan_term": loan_term,
                    "annual_rate": round(annual_rate, 3),
                    "ltv": round(base_ltv, 3),  # Use base LTV for display
                    "closing_date": closing_date.isoformat() if closing_date else None,
                },
                "monthly_payment": {
                    "principal_and_interest": monthly_pi,
                    "property_tax": monthly_tax,
                    "home_insurance": monthly_insurance,
                    "mortgage_insurance": monthly_mi,
                    "hoa_fee": hoa_fee,
                    "total": monthly_payment,
                },
                "closing_costs": closing_costs,
                "prepaid_items": prepaid_items,
                "credits": {
                    "seller": seller_credit,
                    "lender": lender_credit,
                    "total": total_credits,
                },
                "total_cash_needed": down_payment_amount + net_closing_costs,
            }

            # Add loan type specific information if applicable
            if loan_type.lower() == "va" and va_usage == "subsequent":
                results["loan_details"]["funding_fee"] = financed_fees

            self.logger.info("Calculation completed successfully")
            return results
        except Exception as e:
            self.logger.error(f"Error in calculate_all: {e}")
            raise

    def calculate_closing_costs(
        self, purchase_price: float, loan_amount: float
    ) -> Dict[str, float]:
        """Calculate itemized closing costs based on configuration."""
        try:
            self.logger.info(
                f"Calculating closing costs: price={purchase_price}, loan={loan_amount}"
            )
            closing_costs = {}
            total = 0.0

            for item_name, item_config in self.config["closing_costs"].items():
                cost_type = item_config["type"]
                value = item_config["value"]
                base = item_config["calculation_base"]

                if cost_type == "fixed":
                    amount = value
                elif cost_type == "percentage":
                    if base == "purchase_price":
                        amount = (value / 100) * purchase_price
                    elif base == "loan_amount":
                        amount = (value / 100) * loan_amount
                    else:
                        self.logger.warning(
                            f"Unknown calculation base for {item_name}: {base}"
                        )
                        continue
                else:
                    self.logger.warning(
                        f"Unknown cost type for {item_name}: {cost_type}"
                    )
                    continue

                closing_costs[item_name] = round(amount, 2)
                total += amount
                self.logger.info(
                    f"Added closing cost {item_name}: {closing_costs[item_name]}"
                )

            closing_costs["total"] = round(total, 2)
            self.logger.info(f"Total closing costs: {closing_costs['total']}")
            return closing_costs
        except Exception as e:
            self.logger.error(f"Error calculating closing costs: {e}")
            raise

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
                    last_date_of_month = date(
                        closing_date.year, closing_date.month, last_day
                    )

                    # Calculate days from closing to end of month (inclusive of closing day)
                    days_of_interest = (last_date_of_month - closing_date).days + 1

                    self.logger.info(
                        f"Calculated {days_of_interest} days from closing date {closing_date} to end of month {last_date_of_month}"
                    )
                except Exception as e:
                    self.logger.error(
                        f"Error calculating days from closing date: {str(e)}"
                    )
                    self.logger.warning(f"Falling back to default 30 days of interest")
            else:
                self.logger.warning(
                    f"No closing date provided, using default 30 days of interest"
                )

            # Calculate the prepaid interest amount
            prepaid_interest = round(daily_interest * days_of_interest, 2)
            self.logger.info(
                f"Prepaid interest calculation: ${daily_interest:.2f}/day × {days_of_interest} days = ${prepaid_interest:.2f}"
            )
            prepaid["prepaid_interest"] = prepaid_interest

            # 2. Calculate prepaid property tax
            monthly_tax = (loan_amount * annual_tax_rate / 100) / 12
            prepaid["prepaid_tax"] = round(
                monthly_tax * config["months_tax_prepaid"], 2
            )
            prepaid["tax_escrow"] = round(monthly_tax * config["months_tax_escrow"], 2)
            self.logger.info(
                f"Property tax calculations: monthly=${monthly_tax:.2f}, prepaid=${prepaid['prepaid_tax']:.2f}, escrow=${prepaid['tax_escrow']:.2f}"
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

    def generate_amortization_data(
        self, principal: float, annual_rate: float, years: int
    ) -> list:
        """Generate amortization data for yearly principal balance over the loan term."""
        try:
            self.logger.info(
                f"Generating amortization data: principal={principal}, rate={annual_rate}, years={years}"
            )

            if annual_rate == 0:
                # Simple case for zero interest rate
                monthly_payment = principal / (years * 12)
                yearly_balances = [
                    principal * (1 - (i / years)) for i in range(1, years + 1)
                ]
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
