# Railway Deployment Quick Guide

## Step 1: Railway Account Setup ✅
1. Go to [railway.app](https://railway.app)
2. Sign up with your GitHub account  
3. Verify your email

## Step 2: Deploy PostgreSQL Database

### In Railway Dashboard:
1. Click **"New Project"**
2. Select **"Provision PostgreSQL"** 
3. Wait for deployment to complete (~2 minutes)
4. Click on the PostgreSQL service
5. Go to **"Connect"** tab
6. Copy the **DATABASE_URL** (looks like: `postgresql://postgres:password@hostname:port/railway`)

## Step 3: Create API Repository

### Create a new GitHub repository for your API:
1. Go to GitHub and create new repository: `mortgage-calculator-api`
2. Copy these files from your local project:

**Required Files for API Repository:**
```
api_app.py
models.py  
database.py
config_service.py
calculator.py
auth_routes.py
config_manager.py
constants.py
error_handling.py
config_factory.py
config/ (entire directory)
requirements-api.txt
railway.toml
Procfile.api (rename to Procfile)
```

## Step 4: Deploy API to Railway

### In Railway Dashboard:
1. Click **"New Project"**
2. Select **"Deploy from GitHub repo"**
3. Choose your `mortgage-calculator-api` repository
4. Railway will auto-detect Python and start building

### Set Environment Variables:
In Railway dashboard → your API service → "Variables" tab:

```bash
SECRET_KEY=your-super-secret-key-change-this-in-production
DATABASE_URL=postgresql://postgres:password@hostname:port/railway
FLASK_ENV=production
INITIAL_ADMIN_USERNAME=youradmin
INITIAL_ADMIN_EMAIL=admin@yourdomain.com
INITIAL_ADMIN_PASSWORD=ChangeMe123!
```

**Important:** Replace the DATABASE_URL with the one you copied from Step 2!

## Step 5: Get Your API URL

After deployment completes:
1. Go to your API service in Railway
2. Click on **"Settings"** tab
3. Find **"Domains"** section
4. Copy your Railway app URL (like: `https://your-app-name.up.railway.app`)

## Step 6: Test API Health

Visit: `https://your-app-name.up.railway.app/health`

Should return:
```json
{
  "status": "healthy",
  "version": "2.8.0", 
  "database_connected": true
}
```

## Next Steps

Once your API is deployed:
1. Update frontend `js/config.js` with your Railway API URL
2. Deploy frontend to GitHub Pages
3. Configure CORS settings

---

## Troubleshooting

**Build Fails:** Check that all required files are in your repository
**Database Connection:** Verify DATABASE_URL environment variable
**API 500 Errors:** Check Railway logs in the dashboard