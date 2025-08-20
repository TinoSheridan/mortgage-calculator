# GitHub Pages Deployment Guide
## Multi-Tenant Mortgage Calculator v2.8.0

This guide will help you deploy the mortgage calculator using GitHub Pages for the frontend and Railway/Vercel for the API backend.

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   GitHub Pages  │    │  Railway/Vercel │    │   PostgreSQL    │
│   (Frontend)    │◄──►│   (API Backend) │◄──►│   (Database)    │
│                 │    │                 │    │                 │
│ - Static HTML   │    │ - Flask API     │    │ - User Data     │
│ - JavaScript    │    │ - Authentication│    │ - Configurations│
│ - CSS           │    │ - Calculations  │    │ - Multi-tenant  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Benefits

✅ **100% Free** - GitHub Pages + Railway free tier  
✅ **Multi-Tenant** - Full database functionality  
✅ **Scalable** - Separates frontend from backend  
✅ **Fast** - CDN delivery for static assets  
✅ **Secure** - HTTPS by default  

## Step 1: Set Up Railway Backend

### 1.1 Create Railway Account
1. Go to [railway.app](https://railway.app)
2. Sign up with your GitHub account
3. Verify your email

### 1.2 Deploy PostgreSQL Database
1. Click "New Project" → "Provision PostgreSQL"
2. Note the database credentials from the "Connect" tab
3. Save these environment variables:
   ```
   DATABASE_URL=postgresql://username:password@host:port/database
   ```

### 1.3 Deploy API Backend
1. Create a new GitHub repository for your API
2. Copy these files to the repository:
   ```
   api_app.py
   requirements-api.txt
   railway.toml
   Procfile.api (rename to Procfile)
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
   ```

3. In Railway:
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your API repository
   - Railway will auto-detect Python and deploy

### 1.4 Configure Environment Variables
In Railway dashboard, go to your API service and add:

```bash
SECRET_KEY=your-super-secret-key-here
DATABASE_URL=postgresql://username:password@host:port/database
FLASK_ENV=production
INITIAL_ADMIN_USERNAME=youradmin
INITIAL_ADMIN_EMAIL=admin@yourdomain.com
INITIAL_ADMIN_PASSWORD=YourSecurePassword123!
```

### 1.5 Initialize Database
1. Go to Railway dashboard → your API service → "Deploy" tab
2. Wait for deployment to complete
3. The database will auto-initialize on first run
4. Check logs to confirm successful initialization

## Step 2: Set Up GitHub Pages Frontend

### 2.1 Create Frontend Repository
1. Create a new GitHub repository (e.g., `mortgage-calculator-frontend`)
2. Copy the `frontend/` directory contents to the repository root:
   ```
   index.html
   login.html
   css/calculator.css
   js/config.js
   js/auth.js
   js/calculator.js
   js/app.js
   ```

### 2.2 Update API Configuration
Edit `js/config.js` and update the API URL:

```javascript
const API_CONFIG = {
    // Replace with your Railway API URL
    BASE_URL: 'https://your-api-name.up.railway.app',  // ← Update this!
    
    // Rest of the config...
};
```

### 2.3 Enable GitHub Pages
1. Go to repository Settings → Pages
2. Source: "Deploy from a branch"
3. Branch: `main` (or `master`)
4. Folder: `/ (root)`
5. Click "Save"

### 2.4 Configure Custom Domain (Optional)
If you have a custom domain:
1. Add CNAME file with your domain
2. Configure DNS A records:
   ```
   185.199.108.153
   185.199.109.153
   185.199.110.153
   185.199.111.153
   ```

## Step 3: Configure CORS

Update your Railway API's CORS settings in `api_app.py`:

```python
# Enable CORS for GitHub Pages
CORS(app, origins=[
    'https://yourusername.github.io',  # ← Update with your GitHub Pages URL
    'https://your-custom-domain.com',  # ← If using custom domain
    'http://localhost:3000',           # For local development
    'http://127.0.0.1:3000'           # For local development
])
```

Redeploy your API after making this change.

## Step 4: Test the Deployment

### 4.1 Test API Health
Visit your Railway API URL + `/health`:
```
https://your-api-name.up.railway.app/health
```

Should return:
```json
{
  "status": "healthy",
  "version": "2.8.0",
  "database_connected": true
}
```

### 4.2 Test Frontend
1. Visit your GitHub Pages URL
2. Try the calculator (should work without login)
3. Click login and use demo credentials:
   - Username: `superadmin`
   - Password: `ChangeMe123!`

### 4.3 Test Multi-Tenant Features
1. Log in as super admin
2. Visit calculator - should show "Using your personalized settings"
3. Try customizing configurations
4. Log out and test anonymous usage

## Step 5: Set Up GitHub Actions (Optional)

Create `.github/workflows/deploy.yml` for automated deployment:

```yaml
name: Deploy to GitHub Pages

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
    
    - name: Install dependencies (if any)
      run: npm install
      
    - name: Build (if needed)
      run: npm run build
      
    - name: Deploy to GitHub Pages
      uses: peaceiris/actions-gh-pages@v3
      with:
        github_token: ${{ secrets.GITHUB_TOKEN }}
        publish_dir: ./
```

## Troubleshooting

### API Connection Issues
- Check CORS configuration
- Verify Railway API is running
- Check browser console for errors
- Test API endpoints directly

### Database Issues
- Check Railway PostgreSQL logs
- Verify DATABASE_URL environment variable
- Test database connection in Railway console

### GitHub Pages Issues
- Check repository settings
- Verify files are in correct locations
- Check browser console for 404 errors
- Clear browser cache

## Cost Breakdown

| Service | Free Tier | Cost |
|---------|-----------|------|
| GitHub Pages | 100GB bandwidth/month | **Free** |
| Railway API | 500 hours/month | **Free** |
| Railway PostgreSQL | 1GB storage | **Free** |
| **Total** | | **$0/month** |

## Scaling Options

When you outgrow free tiers:

- **Railway Pro**: $5/month for 2GB RAM, unlimited hours
- **Vercel Pro**: $20/month for better performance
- **Custom Domain**: $10-15/year
- **Database Upgrade**: $5-10/month for more storage

## Security Notes

1. **Environment Variables**: Never commit secrets to GitHub
2. **CORS**: Only allow your specific domains
3. **HTTPS**: Always use HTTPS (automatic with GitHub Pages)
4. **API Rate Limiting**: Consider adding rate limiting
5. **Database Access**: Use connection pooling for production

## Support

For issues:
1. Check the troubleshooting section above
2. Review Railway and GitHub Pages documentation
3. Check browser console for errors
4. Test API endpoints directly with curl/Postman

Your mortgage calculator is now deployed with full multi-tenant capabilities at zero cost! 🎉