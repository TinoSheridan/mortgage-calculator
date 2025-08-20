#!/bin/bash

echo "🚀 GitHub Repository Setup Script"
echo "================================"
echo ""

# Get GitHub username
echo "What's your GitHub username?"
read -p "GitHub username: " github_username

if [ -z "$github_username" ]; then
    echo "❌ GitHub username is required!"
    exit 1
fi

echo ""
echo "📋 Here's what you need to do:"
echo ""
echo "1. Go to: https://github.com/new"
echo "2. Repository name: mortgage-calculator-api"
echo "3. Make it PUBLIC (required for Railway free tier)"
echo "4. Don't add README or .gitignore (we have them ready)"
echo "5. Click 'Create repository'"
echo ""
echo "Press ENTER when you've created the repository..."
read -p ""

# Navigate to API directory
cd ../mortgage-calculator-api

echo ""
echo "🔗 Connecting to your GitHub repository..."
git remote add origin "https://github.com/${github_username}/mortgage-calculator-api.git"

echo ""
echo "📤 Pushing code to GitHub..."
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ SUCCESS! Your API code is now on GitHub!"
    echo ""
    echo "🔗 Repository URL: https://github.com/${github_username}/mortgage-calculator-api"
    echo ""
    echo "🚀 Next steps for Railway deployment:"
    echo "1. Go to Railway dashboard"
    echo "2. Click 'New Project' → 'Deploy from GitHub repo'"
    echo "3. Select: ${github_username}/mortgage-calculator-api"
    echo "4. Add environment variables:"
    echo "   - SECRET_KEY: your-super-secret-key-change-this-123"
    echo "   - DATABASE_URL: postgresql://postgres:CKxeRjAZdkNhMwlIoFFpJxSoibqGAsXT@hopper.proxy.rlwy.net:25695/railway"
    echo "   - FLASK_ENV: production"
    echo "   - INITIAL_ADMIN_USERNAME: youradmin"
    echo "   - INITIAL_ADMIN_EMAIL: admin@yourdomain.com"
    echo "   - INITIAL_ADMIN_PASSWORD: ChangeMe123!"
    echo ""
    echo "5. Wait for deployment to complete (~3-5 minutes)"
    echo ""
else
    echo ""
    echo "❌ Something went wrong with the push."
    echo "Make sure you:"
    echo "1. Created the repository on GitHub"
    echo "2. Have the correct GitHub username"
    echo "3. Are logged into git (you may need to authenticate)"
    echo ""
    echo "You can also do this manually:"
    echo "git remote add origin https://github.com/${github_username}/mortgage-calculator-api.git"
    echo "git push -u origin main"
fi