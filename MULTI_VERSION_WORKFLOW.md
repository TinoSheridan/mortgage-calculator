# Multi-Version Independent Development Workflow

## Current Repository Status ✅

### Main Repository: `mortgage-calculator`
- **Location**: `/Users/tinosheridan/Documents/Python/MortgageCalc`
- **Version**: 2.8.1 (Full multi-tenant system)
- **Status**: ✅ SAFE and INDEPENDENT
- **Deployment**: "wonder mortgage – calculator" on Render
- **Entry Point**: `api_app.py` (with PMI fix)
- **Last Commit**: f594fe6 "Fix PMI configuration in api_app.py"

### Simple Repository: `mortgage-calculator-simple`
- **Location**: `/Users/tinosheridan/Documents/Python/mortgage-calculator-simple`
- **Version**: 1.0.0 (Lightweight API)
- **Status**: ✅ Ready for independent deployment
- **Deployment**: New Render service (to be created)
- **Entry Point**: `app.py` (minimal Flask API)
- **Last Commit**: 5a07948 "Complete simple repository setup"

## Independent Development Strategy

### 🔄 **Main Repository (v2.8.1+) Development**

```bash
# Work in main repository
cd /Users/tinosheridan/Documents/Python/MortgageCalc

# Normal development workflow
git add .
git commit -m "Feature: Add new admin functionality"
git push origin main

# Render automatically deploys from main branch
# No impact on simple version
```

**For Main Repository:**
- ✅ Continue normal development
- ✅ Add multi-tenant features
- ✅ Update admin panel
- ✅ Version bumps (2.8.2, 2.9.0, etc.)
- ✅ Independent deployment pipeline

### 📦 **Simple Repository Development**

```bash
# Work in simple repository
cd /Users/tinosheridan/Documents/Python/mortgage-calculator-simple

# Independent development
git add .
git commit -m "Improve API response format"
git push origin main

# Deploy to separate Render service
# No impact on main v2.8.1 version
```

**For Simple Repository:**
- ✅ API-only enhancements
- ✅ Performance optimizations
- ✅ Frontend integration improvements
- ✅ Independent versioning (1.1.0, 1.2.0, etc.)
- ✅ Separate deployment pipeline

### 🔄 **Keeping Shared Components in Sync**

When you update core calculation logic in the main repository:

```bash
# 1. Update calculator.py in main repository
cd /Users/tinosheridan/Documents/Python/MortgageCalc
# ... make changes to calculator.py or config files ...
git add . && git commit -m "Update PMI calculation logic"
git push origin main

# 2. Sync changes to simple repository
cd /Users/tinosheridan/Documents/Python/mortgage-calculator-simple
git subtree pull --prefix=core /Users/tinosheridan/Documents/Python/MortgageCalc main --squash
git subtree pull --prefix=config /Users/tinosheridan/Documents/Python/MortgageCalc main --squash

# 3. Commit and deploy updated simple version
git add . && git commit -m "Sync calculation updates from main repository"
git push origin main
```

## Deployment Independence

### Production v2.8.1 (Current - KEEP RUNNING)
```yaml
# render.yaml in main repository
services:
  - type: web
    name: mortgage-calculator-v3
    startCommand: gunicorn api_app:app --bind 0.0.0.0:$PORT
```
- **Service**: "wonder mortgage – calculator"
- **Repository**: mortgage-calculator (main branch)
- **Keep this running independently**

### Simple Version (New Deployment)
```yaml
# render.yaml in simple repository
services:
  - type: web
    name: mortgage-calculator-simple
    startCommand: gunicorn app:app --bind 0.0.0.0:$PORT
```
- **Service**: Create new "mortgage-calculator-simple"
- **Repository**: mortgage-calculator-simple (main branch)
- **Deploy to separate service**

## Version Control Strategy

### Main Repository Versioning
- **Current**: v2.8.1
- **Next**: v2.8.2 (bug fixes), v2.9.0 (features)
- **Track in**: `VERSION.py`
- **Focus**: Multi-tenant, admin, database features

### Simple Repository Versioning
- **Current**: v1.0.0
- **Next**: v1.0.1 (bug fixes), v1.1.0 (features)
- **Track in**: `app.py` version field
- **Focus**: API improvements, performance, integrations

## Safety Guarantees ✅

1. **Complete Independence**: Each repository has separate git history
2. **Separate Deployments**: No shared infrastructure or conflicts
3. **Rollback Safety**: Issues in simple version won't affect main v2.8.1
4. **Feature Isolation**: New features go to appropriate repository
5. **Testing Independence**: Each can be tested separately

## Sync Process for Shared Components

**Files to Keep in Sync:**
- `calculator.py` (core calculation engine)
- `config/*.json` (PMI rates, closing costs, etc.)
- `mortgage_insurance.py`, `financed_fees.py` (supporting calculations)

**Sync Frequency:**
- After major calculation changes
- After config updates (PMI rates, closing costs)
- Before major releases

**Sync Command Reference:**
```bash
# In simple repository:
git subtree pull --prefix=core /path/to/main-repo main --squash
git subtree pull --prefix=config /path/to/main-repo main --squash
```

## Development Workflow Summary

### For Multi-Tenant Features (v2.8.1+):
1. Work in `/Users/tinosheridan/Documents/Python/MortgageCalc`
2. Develop admin, database, user management features
3. Deploy automatically to existing Render service
4. No impact on simple version

### For API/Integration Features:
1. Work in `/Users/tinosheridan/Documents/Python/mortgage-calculator-simple`
2. Develop API improvements, frontend integrations
3. Deploy to separate Render service
4. No impact on main v2.8.1 version

### For Calculation Updates:
1. Make changes in main repository first
2. Sync to simple repository using git subtree
3. Test both versions independently
4. Deploy both if needed

Your v2.8.1 production version is completely safe and will continue running independently while you develop these other versions!
