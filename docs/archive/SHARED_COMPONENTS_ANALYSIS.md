# Shared Components Analysis

## Core Components That Need Syncing

### 1. **calculator.py** (2,054 lines, 17 classes/functions)
**Critical shared component** - The heart of both versions
- `MortgageCalculator` class with all calculation methods
- PMI, MIP, closing costs, prepaid calculations
- Both versions depend on this for accuracy
- **Sync Priority: CRITICAL** - Any bug fixes or feature updates need both repos

### 2. **config_manager.py** (606 lines, 25 functions)
**Configuration loading and validation**
- Loads JSON config files for closing costs, PMI rates, etc.
- Handles config validation and defaults
- **Sync Priority: HIGH** - Config changes affect both versions

### 3. **constants.py** (203 lines, 14 definitions)
**Shared enums and constants**
- `LOAN_TYPE`, `TRANSACTION_TYPE`, `CalculationConstants`
- Loan limits, default values, calculation constants
- **Sync Priority: HIGH** - Changes could break compatibility

### 4. **Supporting Calculation Modules**
- `mortgage_insurance.py` - PMI/MIP calculations
- `financed_fees.py` - VA funding fee, FHA UFMIP, etc.
- `calculations/title_insurance.py` - Title insurance calculations
- **Sync Priority: MEDIUM-HIGH** - Core calculation logic

### 5. **Configuration Files** (JSON)
- `config/closing_costs.json` - Fee structures
- `config/mortgage_config.json` - Loan limits and defaults
- `config/pmi_rates.json` - PMI rate tables
- `config/compliance_text.json` - Legal disclaimers
- **Sync Priority: HIGH** - Rate changes need both versions

## Version-Specific Analysis

### Simple Version Issues
The `simple_render_app.py` has **major problems**:
- ❌ **Reimplements calculator logic** (lines 35-48) instead of using `calculator.py`
- ❌ **Hardcoded calculations** without proper config
- ❌ **No PMI calculations** - missing important mortgage component
- ❌ **Basic tax/insurance only** - no advanced features
- ❌ **No closing costs** - incomplete mortgage calculation

### Multi-Tenant Version
- ✅ Uses full `calculator.py` with all features
- ✅ Complete PMI, closing costs, prepaid calculations
- ✅ Proper configuration management
- ✅ All loan types supported (Conventional, FHA, VA, USDA)

## Sync Strategy Recommendations

### Option 1: Git Subtrees ✅ **RECOMMENDED**
```bash
# In simple repo
git subtree add --prefix=core mortgage-calculator main --squash
git subtree pull --prefix=core mortgage-calculator main --squash
```
**Pros:** Automatic sync, maintains git history, easy updates
**Cons:** Requires some git knowledge

### Option 2: Shared Package
Create `mortgage-calculator-core` npm/pip package with shared components
**Pros:** Version control, dependency management
**Cons:** Additional complexity, publishing overhead

### Option 3: Manual Copy/Sync Scripts
**Pros:** Simple to understand
**Cons:** Error-prone, easy to forget, no version tracking

## Immediate Action Required

The simple version (`simple_render_app.py`) is **critically flawed**:

1. **Replace inline calculation** with proper `calculator.py` import
2. **Add proper configuration** loading
3. **Include PMI calculations** for accuracy
4. **Add closing costs** for complete mortgage picture

## File Size Impact

**Shared components total:** ~3,600 lines
**Simple version current:** ~100 lines (but incomplete)
**Simple version with proper sharing:** ~200 lines + shared components

The simple version will grow from 100 lines to ~3,800 lines total, but this is **necessary for accuracy**. The alternative is maintaining duplicate, incomplete calculator logic.

## Repository Structure Recommendation

### mortgage-calculator-simple/
```
├── app.py (simple Flask entry point)
├── requirements-simple.txt (Flask + Flask-CORS only)
├── core/ (git subtree from main repo)
│   ├── calculator.py
│   ├── config_manager.py
│   ├── constants.py
│   ├── mortgage_insurance.py
│   ├── financed_fees.py
│   └── calculations/
├── config/ (git subtree from main repo)
├── templates/simple/ (basic UI only)
└── static/simple/ (minimal CSS/JS)
```

This ensures the simple version gets **full calculation accuracy** while maintaining **minimal deployment dependencies**.
