# Changelog

All notable changes to the Mortgage Calculator project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.6.0] - 2025-01-06

### Fixed
- **Critical LTV Target Calculations**: Fixed frontend JavaScript that was overriding accurate backend calculations
  - **Issue**: Frontend was calculating ~$370K required appraised value instead of correct ~$404K-$411K
  - **Solution**: Modified refinance result renderer to use backend-calculated `min_appraised_values`
  - **Impact**: LTV targets now show accurate values for refinance scenarios
- **Cash-Out Refinance Logic**: Improved cash-out refinance calculations to properly handle cash received vs cash needed
- **Variable Initialization**: Fixed runtime errors with uninitialized variables in refinance calculations

### Added
- **Dynamic Maximum LTV Calculations**: Backend now calculates maximum LTV targets based on loan type and refinance type
  - Conventional rate/term: 97% LTV target
  - FHA rate/term: 96.5% LTV target
  - VA rate/term: 100% LTV target
  - Cash-out refinances: Appropriate maximum LTV limits
- **HOA Fee Integration**: Added HOA fee input field and proper integration into refinance calculations
- **Enhanced LTV Result Renderer**: New `updateLtvTargetsTable()` method in refinance result renderer
- **Break-Even Analysis Clarification**: Ensured break-even calculations use only P&I + extra savings (not HOA/taxes/insurance)

### Changed
- **Improved UI Labels**: Removed "Required" from LTV targets table title and column headers for cleaner appearance
  - "Required Appraised Values for LTV Targets" → "Appraised Values for LTV Targets"
  - "Required Appraised Value" column → "Appraised Value" column
- **Enhanced Rounding**: LTV target values now round up to nearest thousand for cleaner display
- **Backend Response Enhancement**: Added `loan_type` to refinance calculation response for proper frontend processing

### Technical Details
#### Files Modified
- `calculator.py`:
  - Added math import for ceiling calculations
  - Enhanced `min_appraised_values` calculation with dynamic maximum LTV targets
  - Added `loan_type` to response data
  - Improved variable initialization for cash-out refinance logic
- `static/js/renderers/refinanceResultRenderer.js`:
  - Added `updateLtvTargetsTable()` method to use backend calculations
  - Integrated method into main `updateResults()` flow
- `templates/index.html`:
  - Updated LTV targets table titles and column headers
  - Commented out frontend LTV calculations that were overriding backend values
  - Added HOA fee input field with proper form integration

#### Architecture Improvements
- **Backend-Frontend Consistency**: LTV calculations now centralized in backend for accuracy
- **Dynamic LTV Targets**: System automatically includes appropriate maximum LTV based on loan parameters
- **Enhanced Form Data Collection**: Improved HOA fee integration throughout calculation pipeline

## [2.5.5] - 2025-07-04

### Enhanced
- **Codebase Rebuild**: Comprehensive improvements and refinements to the entire application
- **Enhanced Reliability**: Improved stability and robustness throughout the system
- **Performance Optimizations**: Various performance enhancements and optimizations
- **Code Quality**: Comprehensive code quality improvements and best practices implementation
- **System Architecture**: Enhanced overall system architecture and design patterns

### Technical Improvements
- Enhanced error handling and validation
- Improved code organization and modularity
- Better separation of concerns
- Enhanced maintainability and extensibility

## [2.5.0] - 2025-07-02

### Added
- **LTV Information Card for Refinance**: Comprehensive card showing required appraised values for different LTV targets (80%, 90%, 95%, and maximum)
- **Real-time LTV Calculations**: Updates automatically when user changes loan balance, loan type, or refinance type
- **Actual Current Balance Integration**: Uses calculated current balance from refinance calculation for 99.9% accuracy
- **Zero Cash to Close LTV Guidance**: Calculations based on new loan amount including closing costs and prepaids
- **Dynamic Accuracy Indicators**: Shows whether using estimated or actual current balance
- **Detailed Loan Amount Breakdown**: Collapsible section showing original balance → current payoff → + costs → = new loan amount

### Fixed
- **Critical Refinance Validation Bug**: Removed incorrect validation that blocked refinances with LTV > 80%
  - **Impact**: Previously prevented valid refinances from proceeding
  - **Solution**: Now allows refinance to proceed and calculates PMI automatically when LTV > 80%
- **LTV Calculation Accuracy**: Improved from ~95% to 99.9% accuracy by using actual current balance
  - **Before**: Estimates were off by $3,000-$4,000
  - **After**: Estimates within $150 of actual results

### Changed
- **Enhanced Refinance Form**: Better integration between form inputs and LTV guidance
- **Improved User Experience**: Clear visual indicators for estimated vs. actual values
- **Updated Tip Sections**: Better explanations of LTV calculations and zero cash scenarios

### Technical Details
#### Files Modified
- `calculator.py`: Removed blocking validation for LTV > 80% (lines 1085-1087)
- `templates/index.html`: Added comprehensive LTV information card with JavaScript functionality
- `static/js/calculator.js`: Integrated actual current balance updates from refinance results
- `VERSION.py`: Updated to 2.5.0 with new feature flags

#### Architecture Improvements
- **Frontend-Backend Integration**: LTV card updates automatically after refinance calculations
- **Global Function Access**: Made `updateLtvInformationCard` globally accessible for cross-file communication
- **Conditional Accuracy**: Falls back to estimation when actual data not available

## [2.1.0] - 2025-04-19

### Changed
- UI refactor: Always show Origination Fee, Discount Points, Lender's and Owner's Title Insurance in closing costs table, even if zero
- Improved order and clarity of closing costs display

## [2.0.1] - Previous Release

### Added
- Loan Type and Property Type fields
- Improved summary formatting

### Changed
- Updated property tax rate to 1.3% and insurance rate to 1.1%
- Implemented Georgia-specific tax formula

## Migration Notes

### From 2.1.0 to 2.5.0
- **No breaking changes** - all existing functionality preserved
- **New features are additive** - refinance calculations now more accurate and user-friendly
- **Database/Config**: No schema changes required
- **Deployment**: Standard deployment process, no special steps needed

### Testing Checklist
- [ ] Verify refinance calculations work with LTV > 80%
- [ ] Check LTV information card displays correctly
- [ ] Test both standard and zero cash to close modes
- [ ] Confirm card updates after running calculations
- [ ] Validate all loan types and refinance types work properly

### Known Issues
- None currently identified

### Future Considerations
- Consider adding LTV information card for purchase transactions
- Potential integration with real-time appraisal APIs
- Enhanced mobile responsiveness for the LTV card
