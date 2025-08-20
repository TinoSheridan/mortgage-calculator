# Railway Account Setup - Step by Step Guide

## What is Railway?
Railway is a cloud platform that makes it easy to deploy applications and databases. We're using it because:
- ✅ **Free tier** includes PostgreSQL database
- ✅ **Easy GitHub integration** for automatic deployments
- ✅ **Simple environment variable management**
- ✅ **Built-in monitoring and logs**

---

## Step 1: Create Railway Account

### 1.1 Go to Railway Website
- Open your browser and go to **[railway.app](https://railway.app)**

### 1.2 Sign Up with GitHub
- Click **"Login"** in the top right corner
- Click **"Continue with GitHub"**
- **Authorize Railway** to access your GitHub account
- This connects Railway to your GitHub for easy deployments

### 1.3 Verify Email (if prompted)
- Check your email for a verification message from Railway
- Click the verification link if you receive one

### 1.4 Complete Profile
- You may be asked to complete your profile
- Add your name and any other required information

---

## Step 2: Deploy PostgreSQL Database

### 2.1 Create New Project
- Once logged in, you'll see the Railway dashboard
- Click the **"New Project"** button (big purple/blue button)

### 2.2 Choose PostgreSQL
- You'll see several options like "Deploy from GitHub repo", "Empty Project", etc.
- Click **"Provision PostgreSQL"**
- Railway will start creating your database (takes 1-2 minutes)

### 2.3 Get Database Connection Info
- After the database is created, click on the **PostgreSQL service** in your project
- Click the **"Connect"** tab
- You'll see connection details like:
  ```
  PGHOST=containers-us-west-xyz.railway.app
  PGPORT=1234
  PGDATABASE=railway  
  PGUSER=postgres
  PGPASSWORD=abc123xyz
  ```

### 2.4 Copy DATABASE_URL
- In the Connect tab, look for **"DATABASE_URL"**
- Click the **copy button** next to it
- It will look like: `postgresql://postgres:password@host:port/railway`
- **Save this URL** - you'll need it for the API deployment

---

## Step 3: Prepare for API Deployment

### 3.1 Note Your Project Name
- Your Railway project will have a name (shown at the top)
- You can rename it by clicking on the project name
- Suggested name: `mortgage-calculator`

### 3.2 Understand the Dashboard
- **Services**: Shows your PostgreSQL database and (later) your API
- **Deployments**: Shows deployment history and logs
- **Settings**: Project settings and environment variables
- **Usage**: Shows resource usage and billing

---

## Step 4: GitHub Repository Setup (Next Step)

After your Railway account is ready, we'll:
1. Create a GitHub repository for your API
2. Connect Railway to that repository  
3. Deploy your API automatically

---

## Railway Free Tier Limits

**What you get for FREE:**
- ✅ **$5 credit per month** (usually enough for small apps)
- ✅ **PostgreSQL database** with 1GB storage
- ✅ **Automatic deployments** from GitHub
- ✅ **Custom domains** and SSL certificates
- ✅ **Environment variables** and secrets management

**Usage estimates for your app:**
- PostgreSQL database: ~$1-2/month
- API backend: ~$2-3/month  
- **Total: ~$3-5/month** (within free tier!)

---

## Troubleshooting

### ❓ Can't find "Provision PostgreSQL"?
- Make sure you're logged in
- Try refreshing the page
- Look for "Add Service" or "New Service" buttons

### ❓ Database creation failed?
- Try again - sometimes there are temporary issues
- Make sure you're verified on Railway
- Check if you've hit any account limits

### ❓ Can't see connection details?
- Click on the PostgreSQL service box in your project
- Look for "Connect", "Variables", or "Settings" tabs
- The DATABASE_URL should be visible in the Variables tab

### ❓ Need help?
- Railway has good documentation at [docs.railway.app](https://docs.railway.app)
- You can also check their Discord community

---

## Next Steps

Once you have:
✅ Railway account created  
✅ PostgreSQL database deployed  
✅ DATABASE_URL copied and saved  

Let me know and I'll help you:
1. Create the GitHub repository for your API
2. Deploy the API to Railway
3. Configure the frontend to connect to your API
4. Set up GitHub Pages for the frontend

**Ready to continue? Just say "database is ready" and share your DATABASE_URL (you can redact the password if you want).**