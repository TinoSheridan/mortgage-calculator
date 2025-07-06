"""Service layer for mortgage calculator business logic."""

import logging
from typing import Any, Dict, Optional
from datetime import datetime

from calculator import MortgageCalculator
from constants import TRANSACTION_TYPE
from validation import MortgageValidator, ValidationError

logger = logging.getLogger(__name__)


class MortgageCalculationService:
    """Service class for handling mortgage calculations."""
    
    def __init__(self):
        """Initialize the service with a calculator instance."""
        self.calculator = MortgageCalculator()
        self.validator = MortgageValidator()
    
    def calculate_purchase_mortgage(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate mortgage details for a purchase transaction.
        
        Args:
            request_data: Dictionary containing calculation parameters
            
        Returns:
            Dictionary with calculation results
            
        Raises:
            ValidationError: If input validation fails
            Exception: If calculation fails
        """
        try:
            logger.info("Starting purchase mortgage calculation")
            
            # Validate input data
            validated_data = self.validator.validate_purchase_request(request_data)
            logger.info(f"Validated purchase request data: {list(validated_data.keys())}")
            
            # Refresh calculator configuration
            self._refresh_calculator_config()
            
            # Extract parameters for calculation
            calc_params = self._prepare_purchase_calculation_params(validated_data)
            
            # Perform calculation
            logger.info("Performing mortgage calculation")
            result = self.calculator.calculate_all(**calc_params)
            
            # Format response
            formatted_result = self._format_purchase_response(result, validated_data)
            
            logger.info("Purchase mortgage calculation completed successfully")
            return formatted_result
            
        except ValidationError:
            logger.error("Validation error in purchase calculation")
            raise
        except Exception as e:
            logger.error(f"Error in purchase mortgage calculation: {str(e)}")
            raise Exception(f"Calculation failed: {str(e)}")
    
    def calculate_refinance_mortgage(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate mortgage details for a refinance transaction.
        
        Args:
            request_data: Dictionary containing refinance parameters
            
        Returns:
            Dictionary with refinance analysis results
            
        Raises:
            ValidationError: If input validation fails
            Exception: If calculation fails
        """
        try:
            logger.info("Starting refinance mortgage calculation")
            
            # Validate input data
            validated_data = self.validator.validate_refinance_request(request_data)
            logger.info(f"Validated refinance request data: {list(validated_data.keys())}")
            
            # Refresh calculator configuration
            self._refresh_calculator_config()
            
            # Extract parameters for calculation
            calc_params = self._prepare_refinance_calculation_params(validated_data)
            
            # Perform calculation
            logger.info("Performing refinance calculation")
            result = self.calculator.calculate_refinance(**calc_params)
            
            # Check for calculation errors
            if 'error' in result:
                raise Exception(result['error'])
            
            # Format response
            formatted_result = self._format_refinance_response(result, validated_data)
            
            logger.info("Refinance mortgage calculation completed successfully")
            return formatted_result
            
        except ValidationError:
            logger.error("Validation error in refinance calculation")
            raise
        except Exception as e:
            logger.error(f"Error in refinance mortgage calculation: {str(e)}")
            raise Exception(f"Refinance calculation failed: {str(e)}")
    
    def calculate_max_seller_contribution(self, request_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Calculate maximum allowed seller contribution.
        
        Args:
            request_data: Dictionary with loan_type, purchase_price, down_payment_amount
            
        Returns:
            Dictionary with max_seller_contribution
        """
        try:
            logger.info("Calculating maximum seller contribution")
            
            # Validate required fields
            required_fields = ['loan_type', 'purchase_price', 'down_payment_amount']
            for field in required_fields:
                if field not in request_data:
                    raise ValidationError(f"Missing required field: {field}")
            
            loan_type = request_data['loan_type']
            purchase_price = float(request_data['purchase_price'])
            down_payment_amount = float(request_data['down_payment_amount'])
            
            # Calculate LTV
            loan_amount = purchase_price - down_payment_amount
            ltv_ratio = (loan_amount / purchase_price) * 100
            
            # Use calculator method
            max_contribution = self.calculator._calculate_max_seller_contribution(
                loan_type, ltv_ratio, purchase_price
            )
            
            logger.info(f"Maximum seller contribution calculated: ${max_contribution:.2f}")
            return {"max_seller_contribution": max_contribution}
            
        except Exception as e:
            logger.error(f"Error calculating max seller contribution: {str(e)}")
            raise Exception(f"Max seller contribution calculation failed: {str(e)}")
    
    def _refresh_calculator_config(self) -> None:
        """Refresh the calculator configuration."""
        try:
            self.calculator.config_manager.load_config()
            self.calculator.config = self.calculator.config_manager.get_config()
            logger.debug("Calculator configuration refreshed")
        except Exception as e:
            logger.warning(f"Failed to refresh calculator config: {str(e)}")
    
    def _prepare_purchase_calculation_params(self, validated_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare parameters for purchase calculation."""
        params = {
            'purchase_price': validated_data['purchase_price'],
            'down_payment_percentage': validated_data['down_payment_percentage'],
            'annual_rate': validated_data['annual_rate'],
            'loan_term': int(validated_data['loan_term']),
            'annual_tax_rate': validated_data['annual_tax_rate'],
            'annual_insurance_rate': validated_data['annual_insurance_rate'],
            'loan_type': validated_data['loan_type'],
            'monthly_hoa_fee': validated_data.get('monthly_hoa_fee', 0.0),
            'seller_credit': validated_data.get('seller_credit', 0.0),
            'lender_credit': validated_data.get('lender_credit', 0.0),
            'discount_points': validated_data.get('discount_points', 0.0),
            'include_owners_title': validated_data.get('include_owners_title', True),
            'transaction_type': TRANSACTION_TYPE.PURCHASE
        }
        
        # Add closing date if provided
        if 'closing_date' in validated_data:
            try:
                params['closing_date'] = datetime.strptime(
                    validated_data['closing_date'], '%Y-%m-%d'
                ).date()
            except ValueError:
                logger.warning(f"Invalid closing date format: {validated_data['closing_date']}")
        
        # Add VA-specific parameters if applicable
        if validated_data['loan_type'] == 'va':
            va_params = {
                'va_service_type': validated_data.get('va_service_type', 'active'),
                'va_usage': validated_data.get('va_usage', 'first'),
                'va_disability_exempt': validated_data.get('va_disability_exempt', False)
            }
            params.update(va_params)
        
        return params
    
    def _prepare_refinance_calculation_params(self, validated_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare parameters for refinance calculation."""
        params = {
            'appraised_value': validated_data['appraised_value'],
            'original_loan_balance': validated_data['original_loan_balance'],
            'original_interest_rate': validated_data['original_interest_rate'],
            'original_loan_term': int(validated_data['original_loan_term']),
            'original_closing_date': validated_data['original_closing_date'],
            'new_interest_rate': validated_data['new_interest_rate'],
            'new_loan_term': int(validated_data['new_loan_term']),
            'extra_monthly_payment': validated_data.get('extra_monthly_payment', 0.0),
            'new_discount_points': validated_data.get('new_discount_points', 0.0),
            'transaction_type': TRANSACTION_TYPE.REFINANCE
        }
        
        return params
    
    def _format_purchase_response(self, result: Dict[str, Any], validated_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format the response for purchase calculation."""
        seller_credit = validated_data.get('seller_credit', 0.0)
        lender_credit = validated_data.get('lender_credit', 0.0)
        
        formatted_result = {
            "success": True,
            "monthly_payment": result["monthly_breakdown"]["total"],
            "loan_amount": result["loan_details"]["loan_amount"],
            "down_payment": result["loan_details"]["down_payment"],
            "monthly_mortgage": result["monthly_breakdown"]["principal_interest"],
            "monthly_tax": result["monthly_breakdown"]["property_tax"],
            "monthly_insurance": result["monthly_breakdown"]["insurance"],
            "monthly_pmi": result["monthly_breakdown"]["pmi"],
            "monthly_hoa": result["monthly_breakdown"]["hoa"],
            "closing_costs": result["closing_costs"],
            "prepaids": result["prepaid_items"],
            "monthly_breakdown": result["monthly_breakdown"],
            "loan_details": {
                **result["loan_details"],
                "transaction_type": TRANSACTION_TYPE.PURCHASE.value,
            },
            "credits": {
                "seller_credit": seller_credit,
                "lender_credit": lender_credit,
                "total": round(seller_credit + lender_credit, 2),
            },
            "total_cash_needed": result.get(
                "total_cash_needed",
                result["loan_details"]["down_payment"]
                + result["closing_costs"].get("total", 0)
                + result["prepaid_items"].get("total", 0)
                - (seller_credit + lender_credit),
            ),
        }
        
        return formatted_result
    
    def _format_refinance_response(self, result: Dict[str, Any], validated_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format the response for refinance calculation."""
        # Add transaction type to result
        if "loan_details" not in result:
            result["loan_details"] = {}
        result["loan_details"]["transaction_type"] = TRANSACTION_TYPE.REFINANCE.value
        
        # Ensure backward compatibility for closing costs structure
        if 'closing_costs' not in result and 'total_closing_costs' in result:
            result['closing_costs'] = {
                'total': result['total_closing_costs'],
                'financed_amount': result.get('financed_closing_costs', 0),
                'cash_to_close': result.get('cash_to_close', 0),
            }
            
            # Add closing cost details if available
            closing_costs_details = result.get('closing_costs_details', {})
            result['closing_costs'].update({
                'appraisal_fee': closing_costs_details.get('appraisal_fee', 675),
                'credit_report_fee': closing_costs_details.get('credit_report_fee', 249),
                'processing_fee': closing_costs_details.get('processing_fee', 575),
                'underwriting_fee': closing_costs_details.get('underwriting_fee', 675),
                'title_fees': closing_costs_details.get('lender_title_insurance', 825),
                'recording_fee': closing_costs_details.get('recording_fee', 60),
                'other_fees': closing_costs_details.get('other_fees', 0)
            })
        
        return {"success": True, "result": result}


class ConfigurationService:
    """Service class for configuration management."""
    
    def __init__(self, config_manager):
        """Initialize with config manager."""
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
    
    def get_default_parameters(self) -> Dict[str, Any]:
        """Get default calculation parameters."""
        try:
            config = self.config_manager.get_config()
            limits = config.get("limits", {})
            
            return {
                "purchase_price": 400000,
                "down_payment_percentage": 20,
                "annual_rate": 6.5,
                "loan_term": 30,
                "annual_tax_rate": 1.0,
                "annual_insurance_rate": 0.35,
                "loan_type": "conventional",
                "hoa_fee": 0,
                "seller_credit": 0,
                "lender_credit": 0,
                "discount_points": 0,
                "limits": limits
            }
        except Exception as e:
            self.logger.error(f"Error getting default parameters: {str(e)}")
            # Return sensible defaults if config fails
            return {
                "purchase_price": 400000,
                "down_payment_percentage": 20,
                "annual_rate": 6.5,
                "loan_term": 30,
                "annual_tax_rate": 1.0,
                "annual_insurance_rate": 0.35,
                "loan_type": "conventional",
                "hoa_fee": 0,
                "seller_credit": 0,
                "lender_credit": 0,
                "discount_points": 0,
                "limits": {}
            }