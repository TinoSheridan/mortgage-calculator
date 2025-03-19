# Mortgage Calculator Deployment Guide

## Version Tracking

The Mortgage Calculator application now uses explicit version tracking to ensure consistent deployments across environments. This helps identify which features are available in each deployed instance.

### Current Version: 1.9.1 (March 19, 2025)

**Features included:**
- Seller credits with proper validation and maximum limits
- Lender credits
- VA seller contribution limits with 4% concession cap checking
- Conventional seller contribution limits based on LTV

## Deployment Process

### Pre-Deployment Verification

Before deploying to Render, run the verification script to ensure all features are properly implemented:

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
