# Render V3 Deployment Instructions

This guide will help you create a **separate** Render service for the new v3 calculator, keeping your existing v2.6.3 deployment intact.

## Step 1: Create New Render Service

1. Go to your [Render Dashboard](https://dashboard.render.com/)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository (same repo as v2.6.3)
4. Configure the new service:

### Basic Settings:
- **Name**: `mortgage-calculator-v3` (or your preferred name)
- **Branch**: `main` (or your current branch)
- **Root Directory**: Leave empty (uses repo root)
- **Environment**: `Python 3`

### Build & Deploy:
- **Build Command**: `pip install -r requirements-render.txt`
- **Start Command**: `gunicorn --bind 0.0.0.0:$PORT render_app:app`

### Environment Variables:
Add these environment variables in the Render dashboard:
- `FLASK_ENV`: `production`
- `SECRET_KEY`: `d4PYGtn0dwgmVNOdZQbmXrXdAUMbU01-n20rx-x1_7A` (or generate new)
- `PYTHON_VERSION`: `3.11.0`

### Advanced Settings:
- **Health Check Path**: `/health`
- **Auto-Deploy**: `Yes` (will deploy when you push to GitHub)

## Step 2: Deploy

1. Click **"Create Web Service"**
2. Render will automatically start building and deploying
3. Monitor the build logs for any errors

## Step 3: Test Deployment

Once deployed, test these endpoints:
- `https://your-v3-service-url.onrender.com/health` - Health check
- `https://your-v3-service-url.onrender.com/` - API info
- `https://your-v3-service-url.onrender.com/api/calculate` - Calculator API

## Key Differences from V2.6.3:

- **Minimal Dependencies**: Only Flask, Flask-CORS, and gunicorn
- **No Database**: Removed all database dependencies
- **Simplified App**: Uses `render_app.py` instead of full `app.py`
- **Faster Startup**: Reduced memory footprint and startup time

## Troubleshooting:

If deployment fails:
1. Check build logs in Render dashboard
2. Verify `requirements-render.txt` contains correct dependencies
3. Ensure `render_app.py` runs locally: `python render_app.py`
4. Check environment variables are set correctly

## Frontend Integration:

Update your frontend to use the new API URL:
```javascript
const API_BASE_URL = 'https://your-v3-service-url.onrender.com';
```

This keeps your existing v2.6.3 deployment running while testing the new v3 version.
