# Convert Mortgage Calculator Form to Single-Column Layout

## Goal
Convert the mortgage calculator form from a two-column Bootstrap layout to a single-column layout matching the original v2.6.3 design while maintaining all functionality.

## Analysis
The current HTML file uses Bootstrap's grid system with `div class="row"` and `col-md-6` classes to create a two-column layout. I need to:
1. Remove all Bootstrap row/column grid structures
2. Convert each form section to use `form-group mb-1` structure
3. Maintain all input IDs, names, and functionality
4. Keep all labels and input attributes exactly the same

## Todo Items

### 1. Convert Basic Purchase Fields
- [ ] Convert purchase_price and down_payment_percentage from two-column to single-column
- [ ] These are already in single-column format, verify they follow the correct structure

### 2. Convert Interest Rate and Loan Term Section
- [ ] Remove row/col-md-6 wrapper around annual_rate and loan_term
- [ ] Convert to individual form-group mb-1 structures
- [ ] Maintain input-group structure for interest rate with % symbol
- [ ] Maintain select dropdown for loan term

### 3. Convert Discount Points and Occupancy Section
- [ ] Remove row/col-md-6 wrapper around discount_points and occupancy
- [ ] Convert to individual form-group mb-1 structures

### 4. Convert Loan Type and Property Tax Section
- [ ] Remove row/col-md-6 wrapper around loan_type and annual_tax_rate
- [ ] Convert to individual form-group mb-1 structures
- [ ] Maintain complex property tax radio button structure with percentage/amount options

### 5. Convert Insurance and HOA Section
- [ ] Remove row/col-md-6 wrapper around annual_insurance_rate and monthly_hoa_fee
- [ ] Convert to individual form-group mb-1 structures
- [ ] Maintain complex insurance radio button structure with percentage/amount options

### 6. Convert Closing Date and Title Insurance Section
- [ ] Remove row/col-md-6 wrapper around closing_date and include_owners_title
- [ ] Convert to individual form-group mb-1 structures

### 7. Convert Credits & Costs Section
- [ ] Remove all row/col-md-6 wrappers in the credits section
- [ ] Convert seller_credit, lender_credit, financed_closing_costs, and total_closing_costs to individual form-group mb-1 structures

### 8. Convert Refinance Fields Section
- [ ] Remove row/col-md-6 wrapper around home_value and current_loan_balance
- [ ] Remove row/col-md-6 wrapper around new_interest_rate and new_loan_term
- [ ] Remove row/col-md-6 wrapper around refi_loan_type and cash_out_amount
- [ ] Convert all to individual form-group mb-1 structures

### 9. Final Verification
- [ ] Verify all form inputs maintain their original IDs, names, and attributes
- [ ] Verify all labels are preserved exactly
- [ ] Verify form functionality is not broken
- [ ] Test that the form looks like the original v2.6.3 single-column design

## Notes
- All changes should be minimal and focused only on layout structure
- No functionality should be modified
- All input validation, JavaScript hooks, and form submission should remain identical
- The goal is purely visual: converting from two-column to single-column layout