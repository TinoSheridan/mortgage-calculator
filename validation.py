"""Input validation module for mortgage calculator."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom exception for validation errors."""
    
    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(self.message)


class MortgageValidator:
    """Validator class for mortgage calculation inputs."""
    
    # Define reasonable limits for mortgage calculations
    LIMITS = {
        'purchase_price': {'min': 10000, 'max': 50000000},
        'down_payment_percentage': {'min': 0, 'max': 100},
        'annual_rate': {'min': 0, 'max': 30},
        'loan_term': {'min': 1, 'max': 50},
        'annual_tax_rate': {'min': 0, 'max': 10},
        'annual_insurance_rate': {'min': 0, 'max': 5},
        'monthly_hoa_fee': {'min': 0, 'max': 10000},
        'seller_credit': {'min': 0, 'max': 1000000},
        'lender_credit': {'min': 0, 'max': 1000000},
        'discount_points': {'min': 0, 'max': 10},
        'appraised_value': {'min': 10000, 'max': 50000000},
        'original_loan_balance': {'min': 1000, 'max': 50000000},
        'original_interest_rate': {'min': 0, 'max': 30},
        'original_loan_term': {'min': 1, 'max': 50},
        'new_interest_rate': {'min': 0, 'max': 30},
        'new_loan_term': {'min': 1, 'max': 50},
        'extra_monthly_payment': {'min': 0, 'max': 100000},
        'new_discount_points': {'min': 0, 'max': 10}
    }
    
    VALID_LOAN_TYPES = ['conventional', 'fha', 'va', 'usda']
    VALID_TRANSACTION_TYPES = ['purchase', 'refinance']
    VALID_VA_SERVICE_TYPES = ['active', 'reserves', 'national_guard']
    VALID_VA_USAGE_TYPES = ['first', 'subsequent']
    
    @classmethod
    def validate_purchase_request(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate purchase calculation request data."""
        errors = []
        validated_data = {}
        
        try:
            # Required fields for purchase
            required_fields = [
                'purchase_price', 'down_payment_percentage', 'annual_rate', 
                'loan_term', 'annual_tax_rate', 'annual_insurance_rate'
            ]
            
            for field in required_fields:
                if field not in data or data[field] is None:
                    errors.append(f"Missing required field: {field}")
                    continue
                
                validated_data[field] = cls._validate_numeric_field(
                    field, data[field], required=True
                )
            
            # Optional fields
            optional_fields = [
                'monthly_hoa_fee', 'seller_credit', 'lender_credit', 
                'discount_points'
            ]
            
            for field in optional_fields:
                if field in data and data[field] is not None:
                    validated_data[field] = cls._validate_numeric_field(
                        field, data[field], required=False
                    )
                else:
                    validated_data[field] = 0.0
            
            # Validate loan type
            loan_type = data.get('loan_type', 'conventional')
            validated_data['loan_type'] = cls._validate_loan_type(loan_type)
            
            # Validate transaction type
            transaction_type = data.get('transaction_type', 'purchase')
            validated_data['transaction_type'] = cls._validate_transaction_type(transaction_type)
            
            # Validate boolean fields
            include_owners_title = data.get('include_owners_title', True)
            validated_data['include_owners_title'] = cls._validate_boolean_field(
                'include_owners_title', include_owners_title
            )
            
            # Validate closing date if provided
            if 'closing_date' in data and data['closing_date']:
                validated_data['closing_date'] = cls._validate_date_field(
                    'closing_date', data['closing_date']
                )
            
            # Validate VA-specific fields if loan type is VA
            if validated_data['loan_type'] == 'va':
                va_fields = cls._validate_va_fields(data)
                validated_data.update(va_fields)
            
            # Business logic validations
            cls._validate_business_rules(validated_data)
            
            if errors:
                raise ValidationError(f"Validation errors: {'; '.join(errors)}")
            
            return validated_data
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Unexpected validation error: {str(e)}")
            raise ValidationError(f"Validation failed: {str(e)}")
    
    @classmethod
    def validate_refinance_request(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate refinance calculation request data."""
        errors = []
        validated_data = {}
        
        try:
            # Required fields for refinance
            required_fields = [
                'appraised_value', 'original_loan_balance', 'original_interest_rate',
                'new_interest_rate'
            ]
            
            for field in required_fields:
                if field not in data or data[field] is None:
                    errors.append(f"Missing required field: {field}")
                    continue
                
                validated_data[field] = cls._validate_numeric_field(
                    field, data[field], required=True
                )
            
            # Optional fields with defaults
            optional_fields = {
                'original_loan_term': 30,
                'new_loan_term': 30,
                'extra_monthly_payment': 0.0,
                'new_discount_points': 0.0
            }
            
            for field, default_value in optional_fields.items():
                value = data.get(field, default_value)
                validated_data[field] = cls._validate_numeric_field(
                    field, value, required=False
                )
            
            # Validate original closing date
            original_closing_date = data.get('original_closing_date')
            if not original_closing_date:
                # Default to current date if not provided
                validated_data['original_closing_date'] = datetime.now().strftime('%Y-%m-%d')
            else:
                validated_data['original_closing_date'] = cls._validate_date_string(
                    'original_closing_date', original_closing_date
                )
            
            # Validate transaction type
            validated_data['transaction_type'] = 'refinance'
            
            if errors:
                raise ValidationError(f"Validation errors: {'; '.join(errors)}")
            
            return validated_data
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Unexpected refinance validation error: {str(e)}")
            raise ValidationError(f"Refinance validation failed: {str(e)}")
    
    @classmethod
    def _validate_numeric_field(cls, field_name: str, value: Any, required: bool = True) -> float:
        """Validate a numeric field."""
        if value is None or value == '':
            if required:
                raise ValidationError(f"Field '{field_name}' is required")
            return 0.0
        
        try:
            numeric_value = float(value)
        except (ValueError, TypeError):
            raise ValidationError(f"Field '{field_name}' must be a valid number", field_name)
        
        # Check if field has defined limits
        if field_name in cls.LIMITS:
            limits = cls.LIMITS[field_name]
            if numeric_value < limits['min']:
                raise ValidationError(
                    f"Field '{field_name}' must be at least {limits['min']}", 
                    field_name
                )
            if numeric_value > limits['max']:
                raise ValidationError(
                    f"Field '{field_name}' must not exceed {limits['max']}", 
                    field_name
                )
        
        return numeric_value
    
    @classmethod
    def _validate_loan_type(cls, loan_type: str) -> str:
        """Validate loan type."""
        if not loan_type:
            return 'conventional'
        
        loan_type_lower = loan_type.lower().strip()
        if loan_type_lower not in cls.VALID_LOAN_TYPES:
            raise ValidationError(
                f"Invalid loan type '{loan_type}'. Must be one of: {', '.join(cls.VALID_LOAN_TYPES)}"
            )
        
        return loan_type_lower
    
    @classmethod
    def _validate_transaction_type(cls, transaction_type: str) -> str:
        """Validate transaction type."""
        if not transaction_type:
            return 'purchase'
        
        transaction_type_lower = transaction_type.lower().strip()
        if transaction_type_lower not in cls.VALID_TRANSACTION_TYPES:
            raise ValidationError(
                f"Invalid transaction type '{transaction_type}'. Must be one of: {', '.join(cls.VALID_TRANSACTION_TYPES)}"
            )
        
        return transaction_type_lower
    
    @classmethod
    def _validate_boolean_field(cls, field_name: str, value: Any) -> bool:
        """Validate a boolean field."""
        if isinstance(value, bool):
            return value
        
        if isinstance(value, str):
            value_lower = value.lower().strip()
            if value_lower in ['true', 'yes', '1', 'on']:
                return True
            elif value_lower in ['false', 'no', '0', 'off']:
                return False
        
        raise ValidationError(f"Field '{field_name}' must be a valid boolean value", field_name)
    
    @classmethod
    def _validate_date_field(cls, field_name: str, value: Any) -> str:
        """Validate a date field and return ISO format string."""
        if not value:
            raise ValidationError(f"Field '{field_name}' cannot be empty", field_name)
        
        return cls._validate_date_string(field_name, value)
    
    @classmethod
    def _validate_date_string(cls, field_name: str, date_string: str) -> str:
        """Validate and normalize a date string."""
        try:
            # Try different date formats
            for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%m-%d-%Y']:
                try:
                    parsed_date = datetime.strptime(date_string, fmt)
                    return parsed_date.strftime('%Y-%m-%d')
                except ValueError:
                    continue
            
            raise ValueError("No valid format found")
            
        except ValueError:
            raise ValidationError(
                f"Field '{field_name}' must be a valid date in format YYYY-MM-DD or MM/DD/YYYY", 
                field_name
            )
    
    @classmethod
    def _validate_va_fields(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate VA-specific fields."""
        va_data = {}
        
        # VA service type
        va_service_type = data.get('va_service_type', 'active')
        if va_service_type not in cls.VALID_VA_SERVICE_TYPES:
            raise ValidationError(
                f"Invalid VA service type '{va_service_type}'. Must be one of: {', '.join(cls.VALID_VA_SERVICE_TYPES)}"
            )
        va_data['va_service_type'] = va_service_type
        
        # VA usage
        va_usage = data.get('va_usage', 'first')
        if va_usage not in cls.VALID_VA_USAGE_TYPES:
            raise ValidationError(
                f"Invalid VA usage '{va_usage}'. Must be one of: {', '.join(cls.VALID_VA_USAGE_TYPES)}"
            )
        va_data['va_usage'] = va_usage
        
        # VA disability exempt
        va_disability_exempt = data.get('va_disability_exempt', False)
        va_data['va_disability_exempt'] = cls._validate_boolean_field(
            'va_disability_exempt', va_disability_exempt
        )
        
        return va_data
    
    @classmethod
    def _validate_business_rules(cls, data: Dict[str, Any]) -> None:
        """Validate business logic rules."""
        # Check that down payment doesn't exceed purchase price
        if 'purchase_price' in data and 'down_payment_percentage' in data:
            purchase_price = data['purchase_price']
            down_payment_percentage = data['down_payment_percentage']
            
            if down_payment_percentage >= 100:
                raise ValidationError(
                    "Down payment percentage cannot be 100% or more"
                )
            
            # Check minimum down payment for loan types
            loan_type = data.get('loan_type', 'conventional')
            min_down_payment = cls._get_min_down_payment(loan_type)
            
            if down_payment_percentage < min_down_payment:
                raise ValidationError(
                    f"Minimum down payment for {loan_type} loan is {min_down_payment}%"
                )
        
        # Validate that seller credit doesn't exceed reasonable limits
        if 'seller_credit' in data and 'purchase_price' in data:
            seller_credit = data['seller_credit']
            purchase_price = data['purchase_price']
            
            if seller_credit > purchase_price * 0.1:  # 10% seems reasonable as a warning threshold
                logger.warning(
                    f"Seller credit ({seller_credit}) exceeds 10% of purchase price ({purchase_price})"
                )
    
    @classmethod
    def _get_min_down_payment(cls, loan_type: str) -> float:
        """Get minimum down payment percentage for loan type."""
        min_down_payments = {
            'conventional': 3.0,
            'fha': 3.5,
            'va': 0.0,
            'usda': 0.0
        }
        return min_down_payments.get(loan_type, 3.0)