# Repository Separation Migration Checklist

## Phase 1: Pre-Migration Preparation ✅ COMPLETED

- [x] **Architecture Analysis** - Documented current problems with mixed versions
- [x] **File Classification** - Mapped files to single-tenant vs multi-tenant
- [x] **Shared Components Analysis** - Identified critical components needing sync
- [x] **Directory Structure Plan** - Designed target repository layouts
- [x] **Sync Strategy** - Selected git subtrees approach

## Phase 2: Create Simple Repository (NEXT STEPS)

### 2.1 Repository Setup
- [ ] **Create new GitHub repository**: `mortgage-calculator-simple`
- [ ] **Initialize local repository** with basic structure
- [ ] **Set up git remotes** for both repositories

### 2.2 Create Minimal Simple App
- [ ] **Write new app.py** (replace flawed simple_render_app.py)
  - Use proper `calculator.py` import (via subtree)
  - Include full calculation logic (PMI, closing costs, etc.)
  - Remove hardcoded calculations
- [ ] **Create minimal requirements.txt**
  - Flask==3.1.1
  - Flask-CORS==4.0.1
  - python-dotenv==1.0.0
- [ ] **Create basic templates/index.html** (calculator UI only)

### 2.3 Add Shared Components via Git Subtree
```bash
# Commands to run:
git subtree add --prefix=core https://github.com/TinoSheridan/mortgage-calculator.git main --squash
git subtree add --prefix=config https://github.com/TinoSheridan/mortgage-calculator.git main --squash
```

### 2.4 Test Simple Version
- [ ] **Test locally** - Verify calculator works with shared components
- [ ] **Deploy to Render** - Confirm clean deployment with minimal dependencies
- [ ] **API testing** - Ensure calculation results match main version

## Phase 3: Clean Main Repository

### 3.1 Remove Simple Deployment Files
```bash
# Files to remove:
rm simple_render_app.py
rm ultra_simple_app.py
rm render_app.py
rm simple_app.py
```

### 3.2 Clean Up Requirements
- [ ] **Update requirements.txt** - Remove simple-deployment comments
- [ ] **Remove unused requirements files**:
  - requirements-render.txt
  - requirements-full.txt
  - requirements-dev.txt (consolidate into main)

### 3.3 Update Documentation
- [ ] **Update README.md** - Focus on multi-tenant capabilities
- [ ] **Add repository links** - Reference simple version repo
- [ ] **Clean up deployment docs** - Separate simple vs multi-tenant instructions

## Phase 4: Deployment Configuration

### 4.1 Configure Simple Repository Deployments
- [ ] **Render deployment**: Point "wonder mortgage – calculator" to simple repo
- [ ] **Update CORS origins**: Ensure GitHub Pages integration works
- [ ] **Environment variables**: Set up minimal config (just SECRET_KEY)

### 4.2 Update Main Repository Deployments
- [ ] **Railway deployment**: Configure for full multi-tenant
- [ ] **Local development**: Ensure database setup works
- [ ] **API-only mode**: Verify api_app.py for GitHub Pages integration

## Phase 5: Establish Sync Process

### 5.1 Create Sync Documentation
- [ ] **Document git subtree commands** for regular updates
- [ ] **Create sync script** for easier maintenance
- [ ] **Testing checklist** after shared component updates

### 5.2 Initial Sync Test
- [ ] **Make small change** in main repo calculator.py
- [ ] **Pull via subtree** in simple repo
- [ ] **Verify change appears** and tests pass
- [ ] **Deploy both versions** to confirm sync works

## Phase 6: Validation & Testing

### 6.1 Functional Testing
- [ ] **Calculation accuracy**: Compare results between versions
- [ ] **All loan types**: Test Conventional, FHA, VA, USDA in both
- [ ] **PMI calculations**: Ensure simple version has full PMI logic
- [ ] **Closing costs**: Verify complete closing cost calculations

### 6.2 Deployment Testing
- [ ] **Simple version**: Fast deployment with minimal dependencies
- [ ] **Main version**: Full deployment with database, auth, admin
- [ ] **API compatibility**: Ensure GitHub Pages frontend works with both

### 6.3 Performance Testing
- [ ] **Load times**: Simple version should be significantly faster
- [ ] **Memory usage**: Verify simple version uses less resources
- [ ] **Bundle size**: Confirm minimal dependencies in simple version

## Immediate Action Items (Priority Order)

### 1. **Fix Simple Version Calculator Logic** (Critical)
The current `simple_render_app.py` has flawed calculations. Create proper version:

```python
# mortgage-calculator-simple/app.py
from flask import Flask, jsonify, request
from flask_cors import CORS
from core.calculator import MortgageCalculator

app = Flask(__name__)
CORS(app, origins=["https://tinosheridan.github.io"])

@app.route("/api/calculate", methods=["POST"])
def calculate():
    try:
        data = request.get_json()
        calculator = MortgageCalculator()

        # Use FULL calculator logic instead of hardcoded math
        result = calculator.calculate_all(
            purchase_price=float(data.get("purchase_price")),
            down_payment_percentage=float(data.get("down_payment_percentage")),
            annual_rate=float(data.get("annual_rate")),
            loan_term=int(data.get("loan_term")),
            loan_type=data.get("loan_type", "conventional"),
            annual_tax_rate=float(data.get("annual_tax_rate", 1.2)),
            annual_insurance_rate=float(data.get("annual_insurance_rate", 0.35)),
            monthly_hoa_fee=float(data.get("monthly_hoa_fee", 0))
        )

        return jsonify({"success": True, "result": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400
```

### 2. **Create Repository Structure** (High)
- Set up new `mortgage-calculator-simple` repository
- Add git subtrees for shared components
- Test local development environment

### 3. **Deploy and Validate** (Medium)
- Deploy simple version to Render
- Compare calculation results with main version
- Update "wonder mortgage – calculator" deployment

## Success Criteria

- ✅ **Simple version**: Deploys with <10 dependencies, loads in <2 seconds
- ✅ **Calculation accuracy**: Identical results between versions for all loan types
- ✅ **Independent development**: Changes to admin features don't affect simple version
- ✅ **Sync process**: Shared component updates propagate cleanly to both versions
- ✅ **Clear documentation**: Each repository has focused, clear purpose and instructions

## Risk Mitigation

- **Backup current working state** before major changes
- **Test in separate branch** before affecting main deployments
- **Keep current simple_render_app.py** until new version is validated
- **Document rollback process** if separation causes issues

This separation will solve the deployment conflicts and give you clean, maintainable versions for different use cases.
