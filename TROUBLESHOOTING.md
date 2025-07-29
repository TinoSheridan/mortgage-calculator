# Troubleshooting Guide

## Server Error Issues - July 2025

### Issue: "This site can't be reached" / 500 Internal Server Error

**Symptoms:**
- Local development: "This site can't be reached"
- Render deployment: Server error when hitting calculate button
- Frontend shows "Server error. Please try again later."

**Root Causes & Solutions:**

#### 1. Missing SECRET_KEY Environment Variable
**Error:** `RuntimeError: SECRET_KEY environment variable must be set`

**Solution:**
- **Local:** Create `.env` file with `SECRET_KEY=<secure-random-key>`
- **Render:** Add `SECRET_KEY` to environment variables in dashboard or `render.yaml`

**Prevention:**
- Always check `.env.example` exists and create `.env` from it
- Validate environment variables in deployment scripts

#### 2. Invalid Format Specifiers in Logging
**Error:** `ValueError: Invalid format specifier ', .2f' for object of type 'float'`

**Location:** `app.py:372` - Parameter logging in calculate endpoint

**Problem:** 
```python
# WRONG - space after comma
f"Purchase price: ${purchase_price:, .2f}\n"

# CORRECT - no space after comma  
f"Purchase price: ${purchase_price:,.2f}\n"
```

**Solution:**
- Remove spaces in f-string format specifiers
- Use `:,.2f` not `:, .2f`

**Prevention:**
- Enable flake8 E231 rule checking
- Add format specifier validation to pre-commit hooks
- Use IDE with Python formatting validation

#### 3. Dependency Version Mismatches
**Issue:** Different gunicorn versions in `requirements.txt` vs `start.sh`

**Solution:**
- Keep all dependency versions synchronized
- Use single source of truth for version specifications

### Debug Process

1. **Check Application Startup:**
   ```bash
   python3 app.py
   # Look for RuntimeError about SECRET_KEY
   ```

2. **Test Health Endpoint:**
   ```bash
   curl http://localhost:3333/health
   # Should return {"status": "healthy"}
   ```

3. **Test Calculate Endpoint:**
   ```bash
   # Get CSRF token first
   CSRF_TOKEN=$(curl -s http://localhost:3333/ | grep -o 'csrf-token" content="[^"]*"')
   # Then test calculation
   curl -X POST http://localhost:3333/calculate -H "X-CSRFToken: $CSRF_TOKEN" -d '{...}'
   ```

4. **Check Server Logs:**
   - Local: Console output from `python3 app.py`
   - Render: Build logs and application logs in dashboard

### Prevention Checklist

- [ ] `.env` file exists with all required variables
- [ ] Environment variables set in Render dashboard
- [ ] Format specifiers validated (no spaces in `:,.2f`)
- [ ] Dependency versions synchronized across files
- [ ] Pre-commit hooks enabled and passing
- [ ] Health endpoint responding before deployment

### Files Modified in This Fix

- `render.yaml` - Added SECRET_KEY environment variable
- `start.sh` - Updated gunicorn version to match requirements.txt
- `app.py` - Fixed format specifier in logging statement
- `.env` - Created with secure SECRET_KEY for local development

### Testing Commands

```bash
# Local testing
python3 test_calc.py  # Test calculation logic directly
curl http://localhost:3333/health  # Test application health

# Render testing  
curl https://your-app.onrender.com/health  # Test deployed health
```

---
*Last Updated: July 28, 2025*
*Issue Resolution: Format specifier syntax error in logging*