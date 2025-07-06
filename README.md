# Enhanced Mortgage Calculator

**Version 2.6.0** - A comprehensive Python-based mortgage calculator that helps users analyze mortgage payments, costs, and amortization schedules. Features both purchase and refinance calculations with accurate LTV guidance and enhanced refinance logic.

## Features

### Core Calculations
- Calculate monthly mortgage payments (Principal & Interest)
- Include additional costs (Property tax, PMI, Insurance, HOA fees)
- Support for multiple loan types (Conventional, FHA, VA, USDA)
- Detailed payment breakdowns and amortization schedules

### Refinance Capabilities ⭐ ENHANCED in v2.6.0
- **Accurate LTV Calculations**: Fixed critical frontend override issues for precise appraised value requirements
- **Dynamic Maximum LTV**: Automatically calculates loan-type-specific maximum LTV targets (97% Conventional, 96.5% FHA, 100% VA)
- **Enhanced Cash-Out Logic**: Improved cash-out refinance calculations with proper cash received vs. cash needed handling
- **HOA Fee Integration**: Complete HOA fee support throughout refinance calculations and monthly payment breakdowns
- **Break-Even Clarity**: Accurate break-even analysis using only P&I + extra savings (excludes HOA/taxes/insurance)

### Advanced Features
- JSON-based configuration management
- Admin interface for rate and cost management
- Multiple closing cost scenarios
- Seller and lender credit calculations

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
