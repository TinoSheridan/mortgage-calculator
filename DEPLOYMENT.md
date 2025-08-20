# Mortgage Calculator Deployment Guide

## Version Tracking

The Mortgage Calculator application now uses explicit version tracking to ensure consistent deployments across environments. This helps identify which features are available in each deployed instance.

### Current Version: 2.7.0 (August 17, 2025)

**Features included in this release:**
- **Intel Functionality Removal**: Removed Property Intelligence and Rate Intel features to refocus the calculator on its core mortgage calculation mission
- **Simplified Navigation**: Cleaned up navbar to focus on essential functionality
- **Core Calculator Focus**: Preserved all essential mortgage calculation features while removing external integrations

**Previous features:**
- Seller credits with proper validation and maximum limits
- Lender credits
- VA seller contribution limits with 4% concession cap checking
- Conventional seller contribution limits based on LTV

## Deployment Process

### Pre-Deployment Verification

Before deploying to Render, run the verification script to ensure all features are properly implemented:

#### 1. Run Deployment Validation Script
```bash
python3 scripts/validate_deployment.py
```

This script checks for:
- ✅ Environment variables (SECRET_KEY, etc.)
- ✅ Format specifier syntax errors
- ✅ Dependency version consistency
- ✅ Critical import availability

#### 2. Manual Environment Variable Check

**For Render Deployment:**
Ensure these environment variables are set in Render dashboard:
- `SECRET_KEY` - Secure random string (32+ characters)
- `FLASK_ENV` - Set to "production"

**For Local Development:**
Ensure `.env` file exists with:
```
SECRET_KEY=your-secure-key-here
FLASK_ENV=development
```

#### 3. Common Issues Prevention

**Format Specifier Errors:**
- ❌ Wrong: `f"Price: ${price:, .2f}"`  (space after comma)
- ✅ Correct: `f"Price: ${price:,.2f}"` (no space)

**Missing Environment Variables:**
- Check `.env.example` for required variables
- Validate Render environment variables are set
- Never commit `.env` to version control

```bash
python3 verify_deployment.py
```

This script checks for:
- Required files for each feature
- Critical code patterns to ensure functionality is properly implemented
- Version consistency across the application

### Deployment Steps

1. Use the deployment script to guide you through the process:

```bash
./deploy_to_render.sh
```

2. The script will:
   - Verify all features are implemented
   - Check git status and help commit changes
   - Ensure you're on the correct branch
   - Pull the latest changes
   - Push to GitHub (which triggers the Render deployment)
   - Provide post-deployment verification steps

### Verifying the Deployment

After Render completes the deployment:

1. Visit the `/health` endpoint to confirm:
   - The correct version is deployed
   - All expected features are listed
   - The environment is set correctly

2. Verify critical functionality:
   - Test with seller credits and lender credits
   - Check VA loan scenarios with seller contributions
   - Ensure all credit amounts appear correctly in the UI

## Troubleshooting Version Mismatches

If you notice feature discrepancies between environments:

1. Compare the `/health` endpoint responses
2. Check Render logs for any deployment failures
3. Verify that all feature-specific code is included in the deployment
4. Consider forcing a clean rebuild on Render by selecting "Clear build cache & deploy"

## Managing Future Updates

When adding or modifying features:

1. Update the `VERSION.py` file with the new version number and feature list
2. Update the verification script if new files or code patterns should be checked
3. Follow the standard deployment process

This versioning system ensures consistent deployments and helps quickly identify when version mismatches occur.
