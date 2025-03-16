import math
from datetime import date
from config_manager import ConfigManager
import logging
import json
import os

class MortgageCalculator:
    def __init__(self, config=None):
        # Initialize logger
        self.logger = logging.getLogger(__name__)
        
        # Initialize config
        if config is None:
            # Initialize config manager
            self._config_manager = ConfigManager()
            self._config = self._config_manager.get_config()
        else:
            self._config = config
        
        # Initialize warnings list
        self._warnings = []
        
        # Get global limits
        self._limits = self._config.get('limits', {})
        self._max_interest_rate = self._limits.get('max_interest_rate', 25.0)
        self._max_loan_term = self._limits.get('max_loan_term', 50)
        self._min_purchase_price = self._limits.get('min_purchase_price', 1000)
        self._max_purchase_price = self._limits.get('max_purchase_price', 10000000)
        
        # Initialize default values
        self._loan_type = 'conventional'  # Set default loan type first
        self._down_payment_percentage = 0.0
        self._purchase_price = 0.0
        self._interest_rate = 0.0
        self._loan_term = 30
        self._property_tax_rate = 0.0
        self._home_insurance_rate = 0.35  # Default home insurance rate as percentage of purchase price
        self._hoa_fee = 0.0
        self._closing_date = None
        self._seller_paid = 0
        self._lender_paid = 0
        self._va_type = 'first'
        self._discount_points = 0
        
        # Initialize loan type configurations
        loan_types = self._config.get('loan_types', {})
        self._fha_annual_mip_rate = float(loan_types.get('fha', {}).get('annual_mip_rate', 0.85))
        self._fha_upfront_mip_rate = float(loan_types.get('fha', {}).get('upfront_mip_rate', 1.75))
        self._usda_annual_fee_rate = float(loan_types.get('usda', {}).get('annual_fee_rate', 0.35))
        self._usda_upfront_fee_rate = float(loan_types.get('usda', {}).get('upfront_fee_rate', 1.0))
        self._va_funding_fee_rates = loan_types.get('va', {}).get('funding_fee_rates', {
            '0': {'first': 2.3, 'subsequent': 3.6, 'reserves': 1.65},
            '5': {'first': 1.65, 'subsequent': 1.65, 'reserves': 1.65},
            '10': {'first': 1.4, 'subsequent': 1.4, 'reserves': 1.4}
        })
        
        # Get prepaid configurations
        prepaid = self._config.get('prepaid_items', {})
        self._months_insurance_prepaid = prepaid.get('months_insurance_prepaid', 12)
        self._months_tax_prepaid = prepaid.get('months_tax_prepaid', 6)
        self._days_interest_prepaid = prepaid.get('days_interest_prepaid', 30)
        
        # Escrow initial deposit
        self._months_insurance_escrow = 2
        self._months_tax_escrow = 3
        
        # Load PMI rates
        self.load_pmi_rates()
    
    def load_pmi_rates(self):
        """Load PMI rates from configuration file"""
        try:
            with open('config/pmi_rates.json', 'r') as f:
                self.pmi_rates = json.load(f)
        except FileNotFoundError:
            self.pmi_rates = None
            print("Warning: PMI rates configuration not found")

    def calculate_pmi_rate(self, loan_type, loan_amount, home_value, credit_score):
        """Calculate PMI rate based on loan type, LTV ratio, and credit score"""
        if not self.pmi_rates:
            return 0.0

        ltv_ratio = (loan_amount / home_value) * 100
        
        if ltv_ratio <= 80:
            return 0.0
            
        if loan_type == 'conventional':
            # Find LTV range
            base_rate = 0.0
            for ltv_range, rate in self.pmi_rates['conventional']['ltv_ranges'].items():
                min_ltv, max_ltv = map(float, ltv_range.split('-'))
                if min_ltv <= ltv_ratio <= max_ltv:
                    base_rate = rate
                    break
            
            # Apply credit score adjustment
            adjustment = 0.0
            for score_range, adj in self.pmi_rates['conventional']['credit_score_adjustments'].items():
                if score_range.endswith('+'):
                    min_score = int(score_range[:-1])
                    if credit_score >= min_score:
                        adjustment = adj
                        break
                else:
                    min_score, max_score = map(int, score_range.split('-'))
                    if min_score <= credit_score <= max_score:
                        adjustment = adj
                        break
            
            return base_rate + adjustment
            
        elif loan_type == 'fha':
            # FHA has both upfront and annual PMI
            if ltv_ratio > 95:
                return self.pmi_rates['fha']['annual']['ltv_over_95']
            return self.pmi_rates['fha']['annual']['ltv_under_95']
            
        return 0.0

    def calculate_upfront_pmi(self, loan_type, loan_amount):
        """Calculate upfront PMI fee for FHA loans"""
        if loan_type == 'fha' and self.pmi_rates:
            return loan_amount * self.pmi_rates['fha']['upfront']
        return 0.0

    def calculate_monthly_pmi(self, loan_amount):
        """Calculate monthly PMI/MIP based on loan type"""
        if self.down_payment_percentage >= 20:
            return 0
            
        base_loan = self.base_loan_amount  # Use base loan amount for PMI calculations
        
        if self.loan_type == 'conventional':
            pmi_rate = self.calculate_pmi_rate(self.loan_type, base_loan, self.purchase_price, 720)
            return base_loan * pmi_rate / 100 / 12
        elif self.loan_type == 'fha':
            return base_loan * self._fha_annual_mip_rate / 100 / 12
        elif self.loan_type == 'usda':
            return base_loan * self._usda_annual_fee_rate / 100 / 12
        
        return 0  # VA and Jumbo loans don't have monthly PMI

    # Property getters and setters
    @property
    def purchase_price(self):
        return self._purchase_price

    @purchase_price.setter
    def purchase_price(self, value):
        value = float(value)
        if value < self._min_purchase_price:
            raise ValueError(f'Purchase price cannot be less than ${self._min_purchase_price:,.2f}')
        if value > self._max_purchase_price:
            raise ValueError(f'Purchase price cannot exceed ${self._max_purchase_price:,.2f}')
        self._purchase_price = value

    @property
    def down_payment_percentage(self):
        """Get down payment percentage"""
        return self._down_payment_percentage

    @down_payment_percentage.setter
    def down_payment_percentage(self, value):
        """Set down payment percentage with validation"""
        try:
            # Handle empty values
            if value in (None, '', 'null', 'undefined'):
                value = 0.0
                
            dp = float(value)
            
            # Validate numeric value
            if math.isnan(dp):
                raise ValueError("Down payment cannot be NaN")
            if dp < 0:
                raise ValueError("Down payment percentage cannot be negative")
            if dp > 100:
                raise ValueError("Down payment percentage cannot exceed 100%")
                
            # Get minimum down payment for loan type
            min_down = self._config.get('loan_types', {}).get(self._loan_type, {}).get('min_down_payment', 0)
            
            # Check if down payment is less than minimum
            if dp < min_down:
                raise ValueError(f"{self._loan_type.upper()} loans require minimum {min_down}% down payment")
                
            self._down_payment_percentage = dp
            self.logger.info(f"Set down payment to {dp}%")
            
        except (TypeError, ValueError) as e:
            self.logger.error(f"Error setting down payment: {e}")
            raise ValueError(str(e))

    @property
    def down_payment_amount(self):
        """Calculate down payment amount"""
        if not hasattr(self, '_purchase_price') or not hasattr(self, '_down_payment_percentage'):
            return 0.0
        return float(self.purchase_price * (self.down_payment_percentage / 100))

    @property
    def interest_rate(self):
        """Get interest rate"""
        return self._interest_rate

    @interest_rate.setter
    def interest_rate(self, value):
        """Set interest rate with validation"""
        try:
            # Handle empty values
            if value in (None, '', 'null', 'undefined'):
                value = 0.0
                
            rate = float(value)
            
            # Validate numeric value
            if math.isnan(rate):
                raise ValueError("Interest rate cannot be NaN")
            if rate < 0:
                raise ValueError("Interest rate cannot be negative")
            if rate > self._max_interest_rate:
                raise ValueError(f"Interest rate cannot exceed {self._max_interest_rate}%")
                
            self._interest_rate = rate
            self.logger.info(f"Set interest rate to {rate}%")
            
        except (TypeError, ValueError) as e:
            self.logger.error(f"Error setting interest rate: {e}")
            raise ValueError(str(e))

    @property
    def loan_term(self):
        """Get loan term in years"""
        return self._loan_term

    @loan_term.setter
    def loan_term(self, value):
        """Set loan term with validation"""
        try:
            term = int(value)
            if term <= 0:
                raise ValueError("Loan term must be positive")
            self._loan_term = term
        except (TypeError, ValueError) as e:
            self.logger.error(f"Error setting loan term: {e}")
            raise ValueError(str(e))

    @property
    def property_tax_rate(self):
        return self._property_tax_rate

    @property_tax_rate.setter
    def property_tax_rate(self, value):
        value = float(value)
        if value < 0:
            raise ValueError('Property tax rate cannot be negative')
        if value > 10:  # Assuming max 10% property tax rate
            raise ValueError('Property tax rate seems unusually high (>10%)')
        self._property_tax_rate = value

    @property
    def home_insurance_rate(self):
        """Get home insurance rate as percentage of purchase price"""
        return self._home_insurance_rate

    @home_insurance_rate.setter
    def home_insurance_rate(self, value):
        """Set home insurance rate as percentage of purchase price"""
        try:
            rate = float(value)
            if rate < 0:
                raise ValueError("Home insurance rate cannot be negative")
            if rate > 2:  # Cap at 2% of purchase price annually
                raise ValueError("Home insurance rate seems unusually high (>2% of purchase price)")
            self._home_insurance_rate = rate
            self.logger.info(f"Set home insurance rate to {rate}% of purchase price")
        except (TypeError, ValueError) as e:
            self.logger.error(f"Error setting home insurance rate: {e}")
            raise ValueError(str(e))

    @property
    def hoa_fee(self):
        return self._hoa_fee

    @hoa_fee.setter
    def hoa_fee(self, value):
        value = float(value)
        if value < 0:
            raise ValueError('HOA fee cannot be negative')
        if value > 5000:  # Assuming max $5000 monthly HOA fee
            raise ValueError('HOA fee seems unusually high (>$5000/month)')
        self._hoa_fee = value

    @property
    def loan_type(self):
        """Get loan type"""
        return self._loan_type

    @loan_type.setter
    def loan_type(self, value):
        """Set loan type with validation"""
        valid_types = ['conventional', 'fha', 'va', 'usda', 'jumbo']
        if value.lower() not in valid_types:
            raise ValueError(f"Invalid loan type. Must be one of: {', '.join(valid_types)}")
        
        # Set the new loan type
        self._loan_type = value.lower()

    @property
    def closing_date(self):
        return self._closing_date

    @closing_date.setter
    def closing_date(self, value):
        from datetime import datetime
        if isinstance(value, str):
            self._closing_date = datetime.strptime(value, '%Y-%m-%d').date()
        else:
            self._closing_date = value

    @property
    def seller_paid(self):
        return self._seller_paid

    @seller_paid.setter
    def seller_paid(self, value):
        value = float(value)
        if value < 0:
            raise ValueError('Seller paid contribution cannot be negative')
        if value > self.purchase_price * 0.09:  # Max 9% of purchase price
            raise ValueError('Seller paid contribution cannot exceed 9% of purchase price')
        self._seller_paid = value
        self.check_tolerances()  # Update warnings

    @property
    def lender_paid(self):
        return self._lender_paid

    @lender_paid.setter
    def lender_paid(self, value):
        value = float(value)
        if value < 0:
            raise ValueError('Lender paid contribution cannot be negative')
        if value > self.total_loan_amount * 0.06:  # Max 6% of loan amount
            raise ValueError('Lender paid contribution cannot exceed 6% of loan amount')
        self._lender_paid = value

    @property
    def va_type(self):
        """Get VA loan usage type"""
        return getattr(self, '_va_type', 'first')

    @va_type.setter
    def va_type(self, value):
        """Set VA loan usage type"""
        valid_types = ['first', 'subsequent', 'reserves']
        if value.lower() not in valid_types:
            raise ValueError(f"VA loan usage type must be one of: {', '.join(valid_types)}")
        self._va_type = value.lower()

    @property
    def discount_points(self):
        """Get discount points"""
        return self._discount_points

    @discount_points.setter
    def discount_points(self, value):
        """Set discount points"""
        value = float(value)
        if value < 0:
            raise ValueError('Discount points cannot be negative')
        self._discount_points = value

    @property
    def base_loan_amount(self):
        """Calculate base loan amount (purchase price - down payment)"""
        return float(self.purchase_price - self.down_payment_amount)

    def calculate_financed_fees(self):
        """Calculate fees that are financed into the loan"""
        total_financed_fees = 0.0
        loan_amount = float(self.purchase_price * (1 - self.down_payment_percentage / 100))
        self.logger.info(f"Calculating financed fees for loan type: {self.loan_type}")
        self.logger.info(f"Loan amount: {loan_amount}, Down payment: {self.down_payment_percentage}%")

        if self.loan_type == 'fha':
            # FHA upfront MIP
            total_financed_fees += float(loan_amount * (self._fha_upfront_mip_rate / 100))
        elif self.loan_type == 'va':
            # VA funding fee
            self.logger.info(f"VA loan type: {self.va_type}")
            self.logger.info(f"VA funding fee rates: {self._va_funding_fee_rates}")
            
            # Get the appropriate funding fee rate based on down payment and usage
            if self.down_payment_percentage >= 10:
                dp_key = '10'
            elif self.down_payment_percentage >= 5:
                dp_key = '5'
            else:
                dp_key = '0'
                
            self.logger.info(f"Selected down payment key: {dp_key}")
                
            try:
                # Get the funding fee rate from the nested structure
                va_rates = self._va_funding_fee_rates.get(dp_key, {})
                self.logger.info(f"VA rates for {dp_key}% down: {va_rates}")
                
                if not va_rates:
                    self.logger.error(f"Invalid down payment bracket: {dp_key}")
                    raise ValueError(f"Invalid down payment bracket: {dp_key}")
                    
                funding_fee_rate = va_rates.get(self.va_type)
                self.logger.info(f"Funding fee rate for {self.va_type} use: {funding_fee_rate}")
                
                if funding_fee_rate is None:
                    self.logger.error(f"Invalid VA type: {self.va_type}")
                    raise ValueError(f"Invalid VA type: {self.va_type}")
                    
                total_financed_fees += float(loan_amount * (funding_fee_rate / 100))
                self.logger.info(f"Calculated VA funding fee: {total_financed_fees:.2f} (rate: {funding_fee_rate}%)")
            except (AttributeError, KeyError) as e:
                self.logger.error(f"Error calculating VA funding fee: {e}")
                self.logger.error(f"VA funding fee rates: {self._va_funding_fee_rates}")
                self.logger.error(f"VA type: {self.va_type}")
                self.logger.error(f"Down payment key: {dp_key}")
                raise ValueError("Error calculating VA funding fee. Please check configuration.")
                
        elif self.loan_type == 'usda':
            # USDA guarantee fee
            total_financed_fees += float(loan_amount * (self._usda_upfront_fee_rate / 100))
            
        return total_financed_fees

    @property
    def total_loan_amount(self):
        """Calculate total loan amount including financed fees"""
        return self.base_loan_amount + self.calculate_financed_fees()

    def calculate_monthly_payment(self, loan_amount):
        """Calculate the basic monthly mortgage payment (principal and interest)"""
        p = loan_amount  # Use total loan amount including financed fees
        r = self.interest_rate / 100 / 12  # Monthly interest rate
        n = self.loan_term * 12  # Number of payments
        
        # Calculate monthly payment using the formula: P = L[c(1 + c)^n]/[(1 + c)^n - 1]
        if r > 0:
            monthly_payment = p * (r * (1 + r) ** n) / ((1 + r) ** n - 1)
        else:
            monthly_payment = p / n
            
        return monthly_payment

    def calculate_monthly_property_tax(self):
        """Calculate monthly property tax payment"""
        return self.purchase_price * self.property_tax_rate / 100 / 12

    def calculate_monthly_insurance(self):
        """Calculate monthly insurance payment based on purchase price"""
        annual_insurance = self.purchase_price * (self.home_insurance_rate / 100)
        return annual_insurance / 12

    def calculate_total_monthly_payment(self):
        """Calculate total monthly payment including taxes, insurance, etc."""
        return (self.calculate_monthly_payment(self.total_loan_amount) +
                self.calculate_monthly_property_tax() +
                self.calculate_monthly_pmi(self.total_loan_amount) +
                self.calculate_monthly_insurance() +
                self.hoa_fee)

    def calculate_closing_costs(self, loan_amount):
        """Calculate closing costs including origination fees, title fees, etc."""
        # Get closing cost configurations
        config = self._config.get('closing_costs', {})
        
        # Initialize closing costs dictionary
        costs = {'items': {}}
        
        # Calculate each closing cost from config
        for name, details in config.items():
            if not isinstance(details, dict):
                continue
                
            cost_type = str(details.get('type', 'fixed'))
            value = float(details.get('value', 0))
            base = str(details.get('calculation_base', 'loan_amount'))
            
            # Calculate amount based on type and base
            if cost_type == 'fixed':
                amount = value
            else:  # percentage
                if base == 'purchase_price':
                    amount = float(self.purchase_price * (value / 100))
                else:  # loan_amount
                    amount = float(loan_amount * (value / 100))
            
            costs['items'][name] = {
                'amount': float(amount),
                'description': str(details.get('description', ''))
            }
        
        # Add discount points if any
        if self.discount_points > 0:
            points_cost = (self.discount_points / 100) * loan_amount
            costs['items']['discount_points'] = {
                'amount': points_cost,
                'description': f'Discount points ({self.discount_points}%)'
            }
        
        # Calculate total before credits
        total_before_credits = sum(item['amount'] for item in costs['items'].values())
        
        # Add credits to items if they exist
        if self.seller_paid > 0:
            costs['items']['seller_credit'] = {
                'amount': -self.seller_paid,
                'description': 'Seller paid closing costs'
            }
        if self.lender_paid > 0:
            costs['items']['lender_credit'] = {
                'amount': -self.lender_paid,
                'description': 'Lender paid closing costs'
            }
        
        # Calculate final total
        costs['total'] = max(0, total_before_credits - self.seller_paid - self.lender_paid)
        
        return costs

    def calculate_all(self):
        """Calculate all mortgage details including payments, fees, and cash needed"""
        # Calculate base loan amount and financed fees
        base_loan = float(self.purchase_price * (1 - self.down_payment_percentage / 100))
        financed_fees = self.calculate_financed_fees()
        total_loan = base_loan + financed_fees
        
        # Calculate monthly payments
        monthly_payment = self.calculate_monthly_payment(total_loan)
        monthly_tax = self.calculate_monthly_property_tax()
        monthly_insurance = float(self.home_insurance_rate / 100 * self.purchase_price) / 12
        monthly_pmi = self.calculate_monthly_pmi(total_loan)
        monthly_hoa = float(self.hoa_fee)
        
        # Calculate closing costs
        closing_costs = self.calculate_closing_costs(total_loan)
        
        # Calculate prepaids
        prepaids = {
            'insurance': float(monthly_insurance * self._months_insurance_prepaid),
            'property_tax': float(monthly_tax * self._months_tax_prepaid),
            'prepaid_interest': float((total_loan * (self.interest_rate/100) / 360) * self._days_interest_prepaid)
        }
        prepaids['total'] = sum(prepaids.values())
        
        # Calculate escrow initial deposit
        escrow_deposit = {
            'insurance': float(monthly_insurance * self._months_insurance_escrow),
            'property_tax': float(monthly_tax * self._months_tax_escrow)
        }
        escrow_deposit['total'] = sum(escrow_deposit.values())
        
        # Calculate down payment amount
        down_payment = float(self.purchase_price * (self.down_payment_percentage / 100))
        
        # Calculate total cash needed
        total_cash = {
            'down_payment': down_payment,
            'closing_costs': float(closing_costs['total']),
            'prepaids': float(prepaids['total']),
            'escrow': float(escrow_deposit['total'])
        }
        total_cash['total'] = sum(total_cash.values())
        
        # Return comprehensive calculation results
        return {
            'monthly_payment': {
                'principal_and_interest': float(monthly_payment),
                'property_tax': float(monthly_tax),
                'insurance': float(monthly_insurance),
                'mortgage_insurance': float(monthly_pmi),
                'hoa': float(monthly_hoa),
                'total': float(monthly_payment + monthly_tax + monthly_insurance + monthly_pmi + monthly_hoa)
            },
            'loan_details': {
                'base_loan': float(base_loan),
                'financed_fees': float(financed_fees),
                'total_loan': float(total_loan),
                'down_payment_amount': float(down_payment),
                'down_payment_percentage': float(self.down_payment_percentage),
                'loan_type': self.loan_type
            },
            'closing_costs': closing_costs,
            'prepaids': prepaids,
            'escrow_deposit': escrow_deposit,
            'total_cash_needed': total_cash
        }

    def calculate_prepaids(self):
        """Calculate prepaid items"""
        monthly_tax = float(self.calculate_monthly_property_tax())
        monthly_insurance = float(self.calculate_monthly_insurance())
        daily_interest = float((self.base_loan_amount * self.interest_rate / 100) / 365)
        
        prepaid_taxes = float(monthly_tax * self._months_tax_prepaid)
        prepaid_insurance = float(monthly_insurance * self._months_insurance_prepaid)
        prepaid_interest = float(daily_interest * self._days_interest_prepaid)
        
        return {
            'prepaid_taxes': prepaid_taxes,
            'prepaid_insurance': prepaid_insurance,
            'prepaid_interest': prepaid_interest,
            'total': prepaid_taxes + prepaid_insurance + prepaid_interest
        }

    def calculate_initial_escrow_deposit(self):
        """Calculate initial escrow account deposits"""
        monthly_tax = float(self.calculate_monthly_property_tax())
        monthly_insurance = float(self.calculate_monthly_insurance())
        
        tax_deposit = float(monthly_tax * self._months_tax_escrow)
        insurance_deposit = float(monthly_insurance * self._months_insurance_escrow)
        
        return {
            'taxes': tax_deposit,
            'insurance': insurance_deposit,
            'total': tax_deposit + insurance_deposit
        }

    def calculate_cash_needed(self):
        """Calculate total cash needed at closing"""
        down_payment = float(self.calculate_down_payment())
        closing_costs = self.calculate_closing_costs(self.total_loan_amount)
        prepaids = self.calculate_prepaids()
        escrow = self.calculate_initial_escrow_deposit()
        
        return {
            'down_payment': down_payment,
            'closing_costs': closing_costs['total'],
            'prepaids': prepaids['total'],
            'escrow': escrow['total'],
            'total': down_payment + closing_costs['total'] + prepaids['total'] + escrow['total']
        }

    def check_tolerances(self):
        """Check all tolerances for the current loan type and return warnings."""
        self._warnings = []  # Reset warnings
        
        # Get loan type configuration
        loan_config = self._config.get('loan_types', {}).get(self._loan_type, {})
        tolerances = loan_config.get('tolerances', {})
        
        # Check seller contributions
        if 'seller_contributions' in tolerances:
            max_seller_percentage = tolerances['seller_contributions']['max_percentage']
            max_seller_amount = self.purchase_price * (max_seller_percentage / 100)
            
            if self._seller_paid > max_seller_amount:
                excess = self._seller_paid - max_seller_amount
                warning = tolerances['seller_contributions']['warning_message'].format(
                    max_amount=f"${max_seller_amount:,.2f}",
                    excess_amount=f"${excess:,.2f}"
                )
                self._warnings.append({
                    'type': 'seller_contributions',
                    'severity': 'error',
                    'message': warning
                })
        
        # Check down payment
        if 'down_payment' in tolerances:
            min_down_percentage = tolerances['down_payment']['min_percentage']
            min_down_amount = self.purchase_price * (min_down_percentage / 100)
            
            if self.down_payment_amount < min_down_amount:
                shortfall = min_down_amount - self.down_payment_amount
                warning = tolerances['down_payment']['warning_message'].format(
                    min_amount=f"${min_down_amount:,.2f}",
                    shortfall_amount=f"${shortfall:,.2f}"
                )
                self._warnings.append({
                    'type': 'down_payment',
                    'severity': 'error',
                    'message': warning
                })
        
        # Check debt-to-income ratio (if provided)
        if 'debt_to_income' in tolerances and hasattr(self, '_monthly_debt') and hasattr(self, '_monthly_income'):
            max_dti = tolerances['debt_to_income']['max_percentage']
            current_dti = (self._monthly_debt / self._monthly_income) * 100
            
            if current_dti > max_dti:
                warning = tolerances['debt_to_income']['warning_message'].format(
                    max_percentage=max_dti,
                    current_percentage=f"{current_dti:.1f}"
                )
                self._warnings.append({
                    'type': 'debt_to_income',
                    'severity': 'warning',
                    'message': warning
                })
        
        # Check income limits for USDA loans
        if self.loan_type == 'usda' and 'income_limit' in tolerances:
            if hasattr(self, '_annual_income') and hasattr(self, '_usda_income_limit'):
                if self._annual_income > self._usda_income_limit:
                    warning = tolerances['income_limit']['warning_message'].format(
                        max_amount=f"${self._usda_income_limit:,.2f}"
                    )
                    self._warnings.append({
                        'type': 'income_limit',
                        'severity': 'error',
                        'message': warning
                    })
        
        return self._warnings
    
    @property
    def warnings(self):
        """Get current warnings."""
        return self._warnings

    def set_seller_paid(self, amount):
        """Set seller paid closing costs with validation."""
        try:
            amount = float(amount)
            if amount < 0:
                raise ValueError("Seller paid amount cannot be negative")
            self._seller_paid = amount
            self.check_tolerances()  # Update warnings
        except (TypeError, ValueError) as e:
            self.logger.error(f"Error setting seller paid amount: {e}")
            raise ValueError(str(e))

    def set_monthly_debt(self, amount):
        """Set monthly debt payments for DTI calculation."""
        try:
            amount = float(amount)
            if amount < 0:
                raise ValueError("Monthly debt cannot be negative")
            self._monthly_debt = amount
            self.check_tolerances()  # Update warnings
        except (TypeError, ValueError) as e:
            self.logger.error(f"Error setting monthly debt: {e}")
            raise ValueError(str(e))

    def set_monthly_income(self, amount):
        """Set monthly income for DTI calculation."""
        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError("Monthly income must be positive")
            self._monthly_income = amount
            self.check_tolerances()  # Update warnings
        except (TypeError, ValueError) as e:
            self.logger.error(f"Error setting monthly income: {e}")
            raise ValueError(str(e))

    def set_annual_income(self, amount):
        """Set annual income for USDA qualification."""
        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError("Annual income must be positive")
            self._annual_income = amount
            self.check_tolerances()  # Update warnings
        except (TypeError, ValueError) as e:
            self.logger.error(f"Error setting annual income: {e}")
            raise ValueError(str(e))

    def set_usda_income_limit(self, amount):
        """Set USDA income limit for the area."""
        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError("Income limit must be positive")
            self._usda_income_limit = amount
            self.check_tolerances()  # Update warnings
        except (TypeError, ValueError) as e:
            self.logger.error(f"Error setting USDA income limit: {e}")
            raise ValueError(str(e))

# Example usage
if __name__ == "__main__":
    # Create a calculator with default values
    calc = MortgageCalculator()
    
    # Set up parameters
    calc.purchase_price = 400000
    calc.down_payment_percentage = 10
    calc.interest_rate = 5.75
    calc.loan_term = 30
    calc.property_tax_rate = 1.2
    calc.home_insurance_rate = 0.35
    calc.hoa_fee = 250
    calc.loan_type = 'fha'
    calc.seller_paid = 5000
    calc.lender_paid = 2000
    calc.discount_points = 1
    
    # Calculate and display the monthly payment breakdown
    print("Monthly Payment Breakdown:")
    print(f"Total Monthly Payment: ${calc.calculate_total_monthly_payment():.2f}")
    
    # Calculate and display the down payment
    print(f"\nDown Payment: ${calc.calculate_down_payment():.2f}")
    
    # Calculate and display the closing costs
    closing_costs = calc.calculate_closing_costs(calc.total_loan_amount)
    print("\nClosing Costs:")
    for name, cost_info in closing_costs['items'].items():
        print(f"{name.replace('_', ' ').title()}: ${cost_info['amount']:.2f}")
    
    # Calculate and display the prepaid items
    prepaids = calc.calculate_prepaids()
    print("\nPrepaid Items:")
    for item, amount in prepaids.items():
        print(f"{item.replace('_', ' ').title()}: ${amount:.2f}")
    
    # Calculate and display the initial escrow deposit
    escrow_deposit = calc.calculate_initial_escrow_deposit()
    print("\nInitial Escrow Deposit:")
    for item, amount in escrow_deposit.items():
        print(f"{item.replace('_', ' ').title()}: ${amount:.2f}")
    
    # Calculate and display the cash needed at closing
    cash_needed = calc.calculate_cash_needed()
    print("\nCash Needed at Closing:")
    for item, amount in cash_needed.items():
        print(f"{item.replace('_', ' ').title()}: ${amount:.2f}")