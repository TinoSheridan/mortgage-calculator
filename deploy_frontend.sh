#!/bin/bash

echo "🚀 Deploying Mortgage Calculator Frontend to GitHub Pages..."

# Get GitHub username
echo "What's your GitHub username?"
read -p "GitHub username: " github_username

if [ -z "$github_username" ]; then
    echo "❌ GitHub username is required!"
    exit 1
fi

# Create frontend deployment directory
echo "📁 Preparing frontend files..."
mkdir -p ../mortgage-calculator-frontend
cd ../mortgage-calculator-frontend

# Copy frontend files
cp ../MortgageCalc/frontend/* ./ 2>/dev/null || true
cp -r ../MortgageCalc/frontend/* ./ 2>/dev/null || true

# Create README
cat > README.md << EOF
# Mortgage Calculator Frontend

Multi-tenant mortgage calculator with purchase and refinance calculations.

## Features
- Purchase mortgage calculations
- Refinance scenarios
- Multi-tenant user system
- Responsive mobile design
- GitHub Pages deployment

## API Backend
Connected to Railway API at: https://mortgage-calculator-api-production.up.railway.app

## Version: 2.8.0
Built with HTML, CSS, JavaScript, and Bootstrap.
EOF

echo "🔗 Repository URL: https://github.com/${github_username}/mortgage-calculator"
echo ""
echo "📋 Next steps:"
echo "1. Create GitHub repository: 'mortgage-calculator'"
echo "2. Initialize git and push:"
echo "   git init"
echo "   git add ."
echo "   git commit -m 'Initial mortgage calculator frontend'"
echo "   git remote add origin https://github.com/${github_username}/mortgage-calculator.git"
echo "   git push -u origin main"
echo "3. Enable GitHub Pages in repository settings"
echo "4. Visit: https://${github_username}.github.io/mortgage-calculator"
echo ""
echo "✅ Frontend files ready in: $(pwd)"