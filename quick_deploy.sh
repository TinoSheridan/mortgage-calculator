#!/bin/bash

echo "🚀 Setting up GitHub repository for tinosheridan..."
echo ""

# Navigate to API directory
cd ../mortgage-calculator-api

echo "📋 STEP 1: Create GitHub Repository"
echo "Go to: https://github.com/new"
echo "Repository name: mortgage-calculator-api" 
echo "Make it PUBLIC"
echo "Don't add README or .gitignore"
echo "Click 'Create repository'"
echo ""
echo "Press ENTER when done..."
read

echo ""
echo "🔗 STEP 2: Connecting to GitHub..."
git remote add origin "https://github.com/tinosheridan/mortgage-calculator-api.git"

echo ""
echo "📤 STEP 3: Pushing code to GitHub..."
git push -u origin main

echo ""
echo "✅ Done! Repository: https://github.com/tinosheridan/mortgage-calculator-api"
echo ""
echo "🚀 STEP 4: Deploy to Railway"
echo "1. Go to Railway dashboard"  
echo "2. Click 'New Project' → 'Deploy from GitHub repo'"
echo "3. Select: tinosheridan/mortgage-calculator-api"
echo "4. Add these environment variables:"
echo "   SECRET_KEY=your-super-secret-key-change-this-123"
echo "   DATABASE_URL=postgresql://postgres:CKxeRjAZdkNhMwlIoFFpJxSoibqGAsXT@hopper.proxy.rlwy.net:25695/railway"
echo "   FLASK_ENV=production"
echo "   INITIAL_ADMIN_USERNAME=youradmin"
echo "   INITIAL_ADMIN_EMAIL=admin@yourdomain.com"
echo "   INITIAL_ADMIN_PASSWORD=ChangeMe123!"