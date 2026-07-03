# Architecture Analysis: Single-Tenant vs Multi-Tenant Separation

## Current State Problems

The codebase currently mixes single-tenant and multi-tenant versions in the same directory, causing:
- Deployment conflicts and over-dependencies
- Code confusion and maintenance complexity
- Testing difficulties
- Branch switching requirements for different deployments

## File Classification

### Single-Tenant Only Files
**Simple deployment files (should move to separate repo):**
- `simple_render_app.py` - Basic Flask API for Render
- `ultra_simple_app.py` - Minimal calculator API
- `render_app.py` - Basic render deployment
- `simple_app.py` - Another simple version

### Multi-Tenant Only Files
**Database & Authentication (should stay in main repo):**
- `models.py` - SQLAlchemy models for users, organizations
- `database.py` - Multi-tenant database setup with Flask-Migrate
- `auth_routes.py` - User authentication and session management
- `admin_routes.py` - Admin panel for managing configurations
- `forms.py` - WTForms for user input validation
- `statistics.py` - Usage tracking and analytics
- `config_service.py` - Multi-tenant configuration management

### Shared Core Components
**These need to be synced between both versions:**
- `calculator.py` - Core mortgage calculation logic
- `config_manager.py` - Configuration loading and validation
- `constants.py` - Shared constants and enums
- `error_handling.py` - Error handling utilities
- `validation.py` - Input validation logic
- `mortgage_insurance.py` - PMI/MIP calculation logic
- `financed_fees.py` - Fee calculation logic

**Configuration files (both versions need):**
- `config/closing_costs.json`
- `config/mortgage_config.json`
- `config/pmi_rates.json`
- `config/compliance_text.json`
- `config/output_templates.json`

**Templates (simplified versions for single-tenant):**
- `templates/index.html` - Main calculator interface
- `static/js/calculator.js` - Frontend logic
- `static/css/calculator.css` - Styling

### Main Entry Points
**Current confusion:**
- `app.py` - Full multi-tenant Flask app (port 3333)
- `api_app.py` - API-only version for GitHub Pages
- Various simple_*.py files for basic deployments

## Proposed Repository Structure

### Repository 1: `mortgage-calculator` (Multi-Tenant)
```
mortgage-calculator/
├── app.py (main entry)
├── api_app.py (API-only mode)
├── models.py
├── database.py
├── auth_routes.py
├── admin_routes.py
├── statistics.py
├── [shared core components]
├── config/
├── templates/ (full admin interface)
├── requirements.txt (full dependencies)
```

### Repository 2: `mortgage-calculator-simple` (Single-Tenant)
```
mortgage-calculator-simple/
├── app.py (simple Flask app)
├── [shared core components - synced]
├── config/ (synced)
├── templates/ (basic interface only)
├── requirements.txt (minimal dependencies)
```

## Dependencies Comparison

### Multi-Tenant Requirements:
- Flask + extensions (WTF, Login, SQLAlchemy, Migrate)
- Database (SQLAlchemy, bcrypt)
- Analytics (pandas, matplotlib)
- Full auth and admin stack

### Single-Tenant Requirements:
- Flask + Flask-CORS only
- No database dependencies
- No auth or admin dependencies
- Just calculator core and basic UI

## Migration Strategy

1. **Extract single-tenant** to new repository
2. **Clean main repository** of simple deployment files
3. **Setup sync process** for shared components
4. **Update deployment pipelines** for each repository
5. **Establish maintenance workflow** for dual-repo management

## Benefits After Separation

- ✅ **Clean deployments** - No unused dependencies
- ✅ **Independent development** - Features don't interfere
- ✅ **Simplified testing** - Test each version independently
- ✅ **Clear documentation** - Each repo has single purpose
- ✅ **Easier onboarding** - Developers can focus on one version
