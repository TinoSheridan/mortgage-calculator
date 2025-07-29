# Server Error Quick Fix Guide

## 🚨 "This site can't be reached" / 500 Server Error

**Quick Diagnosis:**
```bash
# 1. Check if app starts locally
python3 app.py

# 2. Look for these specific errors:
```

### Error 1: SECRET_KEY Missing
```
RuntimeError: SECRET_KEY environment variable must be set
```

**Quick Fix:**
```bash
# Local - Create .env file
echo "SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')" > .env
echo "FLASK_ENV=development" >> .env

# Render - Add environment variable in dashboard:
# SECRET_KEY = d4PYGtn0dwgmVNOdZQbmXrXdAUMbU01-n20rx-x1_7A
```

### Error 2: Format Specifier Error
```
ValueError: Invalid format specifier ', .2f' for object of type 'float'
```

**Quick Fix:**
```bash
# Find the problematic line (usually in logging)
grep -n ":, \." *.py

# Fix by removing space after comma:
# Change: f"${amount:, .2f}" 
# To:     f"${amount:,.2f}"
```

### Error 3: CSRF Token Issues
```
Bad Request: The CSRF token is missing
```

**Quick Fix:**
- This is normal for direct API calls
- Frontend handles CSRF automatically
- For testing, get token from homepage first

## Test Commands

```bash
# 1. Health check
curl http://localhost:3333/health

# 2. Full calculation test  
curl -c cookies.jar http://localhost:3333/ > /dev/null
CSRF_TOKEN=$(curl -s -b cookies.jar http://localhost:3333/ | grep -o 'csrf-token" content="[^"]*"' | sed 's/csrf-token" content="//; s/"//')
curl -X POST http://localhost:3333/calculate \
  -b cookies.jar \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: $CSRF_TOKEN" \
  -d '{"purchase_price": 300000, "down_payment_percentage": 20, "annual_rate": 6.5, "loan_term": 30, "annual_tax_rate": 1.3, "annual_insurance_rate": 0.35, "loan_type": "conventional"}'
```

## Prevention

Run before every deployment:
```bash
python3 scripts/validate_deployment.py
```

**Last Updated:** July 28, 2025  
**Issue:** Format specifier syntax in app.py logging