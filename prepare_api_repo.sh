#!/bin/bash

# Script to prepare API files for Railway deployment
echo "🚀 Preparing API repository for Railway deployment..."

# Create API directory
mkdir -p ../mortgage-calculator-api
cd ../mortgage-calculator-api

# Copy essential API files
echo "📁 Copying API files..."
cp ../MortgageCalc/api_app.py .
cp ../MortgageCalc/models.py .
cp ../MortgageCalc/database.py .
cp ../MortgageCalc/config_service.py .
cp ../MortgageCalc/calculator.py .
cp ../MortgageCalc/auth_routes.py .
cp ../MortgageCalc/config_manager.py .
cp ../MortgageCalc/constants.py .
cp ../MortgageCalc/error_handling.py .
cp ../MortgageCalc/config_factory.py .
cp ../MortgageCalc/requirements-api.txt .
cp ../MortgageCalc/railway.toml .

# Rename Procfile.api to Procfile
cp ../MortgageCalc/Procfile.api ./Procfile

# Copy config directory
cp -r ../MortgageCalc/config .

# Create README for API repo
cat > README.md << EOF
# Mortgage Calculator API

Multi-tenant Flask API backend for the Mortgage Calculator application.

## Deployment

This API is designed to be deployed on Railway with PostgreSQL.

### Environment Variables Required:
- SECRET_KEY
- DATABASE_URL  
- FLASK_ENV=production
- INITIAL_ADMIN_USERNAME
- INITIAL_ADMIN_EMAIL
- INITIAL_ADMIN_PASSWORD

### Endpoints:
- GET /health - Health check
- POST /api/calculate - Purchase calculations
- POST /api/refinance - Refinance calculations
- POST /api/auth/login - User authentication
- POST /api/auth/logout - User logout
- GET /api/user/profile - User profile

## Version: 2.8.0
Multi-tenant system with hierarchical admin controls.
EOF

# Initialize git repository
git init
git add .
git commit -m "Initial API setup for Railway deployment

🚀 Multi-tenant Mortgage Calculator API v2.8.0

Features:
- PostgreSQL database integration
- Flask-SQLAlchemy ORM with multi-tenant models
- User authentication with Flask-Login
- Configuration inheritance system
- Purchase and refinance calculations
- Health monitoring and error handling

Ready for Railway deployment with GitHub Pages frontend.

🤖 Generated with Claude Code"

echo "✅ API repository prepared at: ../mortgage-calculator-api"
echo ""
echo "Next steps:"
echo "1. cd ../mortgage-calculator-api"
echo "2. Create GitHub repository: mortgage-calculator-api"
echo "3. git remote add origin https://github.com/yourusername/mortgage-calculator-api.git"
echo "4. git push -u origin main"
echo "5. Deploy to Railway from GitHub"