# Enhanced Mortgage Calculator

A comprehensive Python-based mortgage calculator that helps users analyze mortgage payments, costs, and amortization schedules. The calculator takes into account various factors including property taxes, PMI, home insurance, and HOA fees.

## Features

- Calculate monthly mortgage payments (Principal & Interest)
- Include additional costs (Property tax, PMI, Insurance, HOA fees)
- Support for custom line items and one-time payments
- JSON-based configuration management
- Detailed payment breakdowns and amortization schedules
- Data visualization capabilities

## Installation

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

```python
from Enhanced_Mortgage_Calculator import MortgageCalculator

# Create calculator with default values
calc = MortgageCalculator()

# Or load from config file
calc = MortgageCalculator('config.json')

# Set custom parameters
calc.set_param('loan_amount', 400000)
calc.set_param('annual_interest_rate', 5.5)

# Calculate payments
monthly_payment = calc.calculate_total_monthly_payment()
print(f"Total monthly payment: ${monthly_payment['total']:,.2f}")

# Generate amortization schedule
schedule = calc.generate_amortization_schedule()
```

## Configuration

You can configure the calculator using a JSON file with the following parameters:

- `loan_amount`: Total loan amount
- `annual_interest_rate`: Annual interest rate (%)
- `loan_term_years`: Loan term in years
- `down_payment_percentage`: Down payment (%)
- `property_tax_rate`: Annual property tax rate (%)
- `pmi_rate`: PMI rate (%)
- `home_insurance`: Annual home insurance amount
- `hoa_fee`: Monthly HOA fee
- `additional_payment`: Additional monthly payment
- `one_time_payments`: List of one-time payments
- `custom_line_items`: Custom costs/fees
