# Repository Separation Plan

## Target Repository Structure

### Repository 1: `mortgage-calculator` (Multi-Tenant) - MAIN REPO
```
mortgage-calculator/
├── README.md (Multi-tenant focus)
├── requirements.txt (Full dependencies)
├── app.py (Main multi-tenant entry point)
├── api_app.py (API-only mode for GitHub Pages)
├── wsgi.py (Production WSGI)
├──
├── # Multi-tenant specific
├── models.py (User, Organization, Configuration models)
├── database.py (Multi-tenant database setup)
├── auth_routes.py (User authentication)
├── admin_routes.py (Admin dashboard)
├── statistics.py (Usage analytics)
├── config_service.py (Multi-tenant config management)
├── forms.py (WTForms for admin)
├──
├── # Shared core (source of truth)
├── calculator.py ⭐ (Core calculation engine)
├── config_manager.py ⭐ (Configuration loading)
├── constants.py ⭐ (Shared constants)
├── error_handling.py ⭐ (Error handling)
├── validation.py ⭐ (Input validation)
├── mortgage_insurance.py ⭐ (PMI/MIP logic)
├── financed_fees.py ⭐ (Fee calculations)
├── calculations/ ⭐ (Title insurance, etc.)
├──
├── # Configuration (source of truth)
├── config/ ⭐
│   ├── closing_costs.json
│   ├── mortgage_config.json
│   ├── pmi_rates.json
│   ├── compliance_text.json
│   └── output_templates.json
├──
├── # Full UI
├── templates/ (Full admin interface)
│   ├── admin/ (Admin dashboard templates)
│   ├── auth/ (Login/register templates)
│   └── index.html (Main calculator)
├── static/ (Full CSS/JS with admin features)
├──
├── # Deployment
├── Dockerfile
├── render.yaml
├── railway.json
└── gunicorn.conf.py
```

### Repository 2: `mortgage-calculator-simple` (Single-Tenant) - NEW REPO
```
mortgage-calculator-simple/
├── README.md (Simple deployment focus)
├── requirements.txt (Minimal: Flask + Flask-CORS only)
├── app.py (Simple Flask entry - replaces simple_render_app.py)
├── Procfile (Simple Render deployment)
├──
├── # Shared core (synced via git subtree)
├── core/ (Git subtree from main repo)
│   ├── calculator.py ⭐
│   ├── config_manager.py ⭐
│   ├── constants.py ⭐
│   ├── error_handling.py ⭐
│   ├── validation.py ⭐
│   ├── mortgage_insurance.py ⭐
│   ├── financed_fees.py ⭐
│   └── calculations/ ⭐
├──
├── # Configuration (synced via git subtree)
├── config/ (Git subtree from main repo)
│   └── [same JSON files] ⭐
├──
├── # Simple UI only
├── templates/
│   └── index.html (Calculator only - no admin)
├── static/
│   ├── css/calculator.css (Basic styling)
│   └── js/calculator.js (Basic functionality)
├──
├── # Simple deployment
├── runtime.txt
└── .gitignore
```

## Sync Strategy: Git Subtrees

### Setup (One-time)
```bash
# In simple repo
git subtree add --prefix=core https://github.com/user/mortgage-calculator.git main --squash
git subtree add --prefix=config https://github.com/user/mortgage-calculator.git main --squash
```

### Regular Updates
```bash
# Pull updates from main repo
git subtree pull --prefix=core https://github.com/user/mortgage-calculator.git main --squash
git subtree pull --prefix=config https://github.com/user/mortgage-calculator.git main --squash
```

### Push Changes Back (if needed)
```bash
# If simple repo makes improvements to core
git subtree push --prefix=core https://github.com/user/mortgage-calculator.git simple-improvements
```

## Migration Steps

### Step 1: Prepare Main Repository
```bash
# Clean up main repo - remove simple deployment files
rm simple_render_app.py ultra_simple_app.py render_app.py
rm requirements-render.txt requirements-full.txt

# Update requirements.txt to be multi-tenant focused
# Keep only: Flask, Flask-SQLAlchemy, Flask-Migrate, bcrypt, etc.
```

### Step 2: Create Simple Repository
```bash
# Create new repository
git init mortgage-calculator-simple
cd mortgage-calculator-simple

# Create minimal app.py (proper version using calculator.py)
# Create minimal requirements.txt
# Create basic templates

# Add shared components via subtree
git subtree add --prefix=core ../mortgage-calculator main --squash
git subtree add --prefix=config ../mortgage-calculator main --squash
```

### Step 3: Update Import Paths
```python
# In simple repo app.py
from core.calculator import MortgageCalculator
from core.config_manager import ConfigManager
from core.constants import LOAN_TYPE
```

### Step 4: Create Simple App Entry Point
```python
# mortgage-calculator-simple/app.py
from flask import Flask, jsonify, request
from flask_cors import CORS
from core.calculator import MortgageCalculator

app = Flask(__name__)
CORS(app, origins=["https://tinosheridan.github.io"])

@app.route("/api/calculate", methods=["POST"])
def calculate():
    calculator = MortgageCalculator()
    # Use full calculator.py logic instead of reimplemented version
    result = calculator.calculate_all(
        purchase_price=data["purchase_price"],
        # ... all proper parameters
    )
    return jsonify({"success": True, "result": result})
```

## Dependencies Comparison

### Main Repo (Multi-Tenant)
```
Flask==3.1.1
Flask-SQLAlchemy==3.1.1
Flask-Migrate==4.0.5
Flask-Login==0.6.3
Flask-WTF==1.2.1
bcrypt==4.1.2
pandas==2.1.4
matplotlib==3.7.5
# ... full stack
```

### Simple Repo (Single-Tenant)
```
Flask==3.1.1
Flask-CORS==4.0.1
python-dotenv==1.0.0
# That's it! Core logic comes from subtree
```

## Deployment Differences

### Main Repo Deployments
- **Render**: Full multi-tenant with database
- **Railway**: Alternative with PostgreSQL
- **Local**: Full development with admin panel

### Simple Repo Deployments
- **Render**: Basic API deployment (current wonder mortgage)
- **Vercel**: Alternative simple hosting
- **GitHub Pages**: Static frontend + simple API backend

## Benefits After Separation

✅ **Clean Dependencies**: Simple version has minimal requirements
✅ **Independent Development**: Features don't interfere between versions
✅ **Easier Testing**: Test each version independently
✅ **Clear Purpose**: Each repo has single responsibility
✅ **Faster Deployments**: Simple version deploys in seconds
✅ **Maintained Accuracy**: Both use same calculation engine
✅ **Easy Updates**: Git subtree keeps shared components in sync

## Maintenance Workflow

1. **Core changes**: Make in main repo (mortgage-calculator)
2. **Simple updates**: Pull via `git subtree pull` in simple repo
3. **Simple-specific features**: Develop in simple repo, optionally push back
4. **Configuration changes**: Update in main repo, pull to simple repo
5. **Testing**: Test both versions after shared component changes

This approach gives you the best of both worlds: clean separation with maintained accuracy.
