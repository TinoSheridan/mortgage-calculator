# Mortgage Calculator API Documentation

**Version**: 2.5.5  
**Last Updated**: July 4, 2025  
**Status**: Production Ready

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Security](#security)
4. [Core API Endpoints](#core-api-endpoints)
5. [Admin API Endpoints](#admin-api-endpoints)
6. [Chat API Endpoints](#chat-api-endpoints)
7. [Beta API Endpoints](#beta-api-endpoints)
8. [Health Check Endpoints](#health-check-endpoints)
9. [Error Handling](#error-handling)
10. [Rate Limiting](#rate-limiting)
11. [Examples](#examples)

---

## Overview

The Mortgage Calculator API provides comprehensive mortgage calculation services, admin management capabilities, and real-time chat functionality. The API is built using Flask and follows RESTful principles with CSRF protection and comprehensive input validation.

### Base URL
```
https://your-domain.com/
```

### Content Type
All API requests must use:
```
Content-Type: application/json
```

---

## Authentication

### Admin Authentication
Admin endpoints require session-based authentication:

1. **Login**: POST `/admin/login`
2. **Session Management**: Cookie-based sessions with 7-day expiration
3. **Logout**: GET `/admin/logout`

### CSRF Protection
All POST/PUT/DELETE endpoints require CSRF tokens:
- Include `X-CSRFToken` header with valid token
- Token obtained from form or meta tag in HTML

---

## Security

### Headers Required
- `Content-Type: application/json`
- `X-CSRFToken: <token>` (for state-changing operations)

### Security Features
- HTTPS enforcement in production
- Content Security Policy (CSP)
- XSS protection
- Input validation and sanitization
- Rate limiting (admin endpoints)

---

## Core API Endpoints

### 1. Home Page
```http
GET /
```
**Description**: Main calculator interface  
**Authentication**: None  
**Response**: HTML template with calculator form

---

### 2. Calculate Mortgage
```http
POST /calculate
```
**Description**: Perform comprehensive mortgage calculations  
**Authentication**: CSRF token required  
**Content-Type**: `application/json`

#### Request Body
```json
{
  "purchase_price": 400000,
  "down_payment_percentage": 20,
  "annual_rate": 6.5,
  "loan_term": 30,
  "loan_type": "conventional",
  "annual_tax_rate": 1.2,
  "annual_insurance_rate": 0.5,
  "monthly_hoa_fee": 100,
  "seller_credit": 5000,
  "lender_credit": 2000,
  "discount_points": 0.5,
  "include_owners_title": true,
  "closing_date": "2025-06-01",
  "va_service_type": "active",
  "va_usage": "first",
  "va_disability_exempt": false
}
```

#### Response
```json
{
  "success": true,
  "monthly_payment": 2847.23,
  "loan_amount": 320000,
  "down_payment": 80000,
  "monthly_breakdown": {
    "principal_interest": 2108.02,
    "property_tax": 400.00,
    "home_insurance": 183.33,
    "mortgage_insurance": 155.88,
    "hoa_fee": 100.00,
    "total": 2847.23
  },
  "loan_details": {
    "purchase_price": 400000,
    "loan_amount": 320000,
    "loan_term_years": 30,
    "interest_rate": 6.5,
    "loan_type": "conventional",
    "ltv_ratio": 80.0,
    "transaction_type": "purchase"
  },
  "closing_costs": {
    "total": 8542.50,
    "origination_fee": 3200.00,
    "appraisal_fee": 675.00,
    "title_insurance": 1200.00,
    "recording_fee": 125.00,
    "other_fees": 3342.50
  },
  "prepaids": {
    "total": 2134.56,
    "property_tax": 800.00,
    "insurance": 550.00,
    "interest": 784.56
  },
  "total_cash_needed": 83677.06
}
```

---

### 3. Refinance Calculator
```http
POST /refinance
```
**Description**: Calculate refinance scenarios and savings  
**Authentication**: CSRF token required  
**Content-Type**: `application/json`

#### Request Body
```json
{
  "appraised_value": 450000,
  "original_loan_balance": 320000,
  "original_interest_rate": 7.5,
  "original_loan_term": 30,
  "original_closing_date": "2020-01-01",
  "new_interest_rate": 6.0,
  "new_loan_term": 30,
  "new_closing_date": "2025-02-01",
  "annual_taxes": 4800,
  "annual_insurance": 1800,
  "loan_type": "conventional",
  "refinance_type": "rate_term",
  "zero_cash_to_close": false,
  "new_discount_points": 0
}
```

#### Response
```json
{
  "success": true,
  "result": {
    "new_loan_amount": 325675.00,
    "new_monthly_payment": 1951.25,
    "original_monthly_payment": 2237.07,
    "monthly_savings": 285.82,
    "total_closing_costs": 5675.00,
    "break_even_months": 20,
    "lifetime_savings": 45234.78,
    "cash_to_close": 5675.00
  }
}
```

---

### 4. Maximum Seller Contribution
```http
POST /api/max_seller_contribution
```
**Description**: Calculate maximum allowed seller contribution  
**Authentication**: CSRF token required  
**Content-Type**: `application/json`

#### Request Body
```json
{
  "loan_type": "conventional",
  "purchase_price": 400000,
  "down_payment_amount": 80000
}
```

#### Response
```json
{
  "max_seller_contribution": 24000
}
```

---

### 5. Static Files
```http
GET /static/<path:filename>
```
**Description**: Serve static assets (CSS, JS, images)  
**Authentication**: None  
**Response**: Static file content

---

## Admin API Endpoints

### Authentication Routes

#### Admin Login
```http
POST /admin/login
```
**Description**: Authenticate admin user  
**Authentication**: Form-based login

#### Admin Logout
```http
GET /admin/logout
```
**Description**: End admin session  
**Authentication**: Active session required

---

### Dashboard & Statistics

#### Admin Dashboard
```http
GET /admin/dashboard
```
**Description**: Admin control panel  
**Authentication**: Admin session required

#### Dashboard Data
```http
GET /admin/dashboard/data
```
**Description**: Get dashboard statistics  
**Authentication**: Admin session required

#### Statistics Export
```http
GET /admin/api/statistics/export
```
**Description**: Export usage statistics  
**Authentication**: Admin session required

#### Statistics Purge
```http
POST /admin/api/statistics/purge
```
**Description**: Clear old statistics data  
**Authentication**: Admin session required

---

### County Management

#### List Counties
```http
GET /admin/counties
```
**Description**: View all counties and tax rates  
**Authentication**: Admin session required

#### Add County
```http
POST /admin/counties/add
```
**Description**: Add new county with tax rates  
**Authentication**: Admin session required

#### Edit County
```http
POST /admin/counties/edit/<county_name>
```
**Description**: Update county information  
**Authentication**: Admin session required

#### Delete County
```http
POST /admin/counties/delete/<county_name>
```
**Description**: Remove county from system  
**Authentication**: Admin session required

---

### Closing Costs Management

#### List Closing Costs
```http
GET /admin/closing-costs
```
**Description**: View all closing cost configurations  
**Authentication**: Admin session required

#### Get Closing Cost Details
```http
GET /admin/closing-costs/<name>
```
**Description**: Get specific closing cost configuration  
**Authentication**: Admin session required

#### Add Closing Cost
```http
POST /admin/closing-costs/add
```
**Description**: Add new closing cost item  
**Authentication**: Admin session required

#### Update Closing Cost
```http
PUT /admin/closing-costs/<name>
POST /admin/closing-costs/<name>
```
**Description**: Update existing closing cost  
**Authentication**: Admin session required

#### Delete Closing Cost
```http
DELETE /admin/closing-costs/<name>
```
**Description**: Remove closing cost item  
**Authentication**: Admin session required

---

### PMI/MIP Configuration

#### PMI Rates Management
```http
GET /admin/pmi-rates
```
**Description**: View PMI/MIP rate configurations  
**Authentication**: Admin session required

#### PMI Rates Data
```http
GET /admin/pmi-rates/data
```
**Description**: Get PMI rates in JSON format  
**Authentication**: Admin session required

#### Update PMI Rates
```http
POST /admin/pmi-rates/update
```
**Description**: Update PMI/MIP rates  
**Authentication**: Admin session required

---

### Mortgage Configuration

#### Mortgage Config
```http
GET /admin/mortgage-config
```
**Description**: View mortgage configuration settings  
**Authentication**: Admin session required

#### Update Mortgage Config
```http
POST /admin/mortgage-config/update
```
**Description**: Update mortgage configuration  
**Authentication**: Admin session required

#### Update Prepaid Items
```http
POST /admin/mortgage-config/prepaid/update
```
**Description**: Update prepaid items configuration  
**Authentication**: Admin session required

#### Update Loan Limits
```http
POST /admin/mortgage-config/limits/update
```
**Description**: Update loan limits  
**Authentication**: Admin session required

---

### Title Insurance Configuration

#### Title Insurance Settings
```http
GET /admin/title-insurance
```
**Description**: View title insurance configuration  
**Authentication**: Admin session required

#### Update Title Insurance
```http
POST /admin/title-insurance/update
```
**Description**: Update title insurance settings  
**Authentication**: Admin session required

---

### Configuration Validation

#### Validation Dashboard
```http
GET /admin/validation
```
**Description**: View configuration validation status  
**Authentication**: Admin session required

#### Run Validation
```http
POST /admin/validation/run
```
**Description**: Execute configuration validation  
**Authentication**: Admin session required

#### Validation Details
```http
GET /admin/validation/details/<filename>
```
**Description**: Get detailed validation results  
**Authentication**: Admin session required

#### Configuration Schema
```http
GET /admin/validation/schema/<filename>
```
**Description**: Get JSON schema for configuration file  
**Authentication**: Admin session required

---

## Chat API Endpoints

### Send Message
```http
POST /api/chat/message
```
**Description**: Send chat message and receive automated response  
**Authentication**: None  
**Content-Type**: `application/json`

#### Request Body
```json
{
  "message": "What is PMI?",
  "session_id": "unique-session-id"
}
```

#### Response
```json
{
  "status": "success",
  "response": "Private Mortgage Insurance (PMI) is typically required when your down payment is less than 20% on a conventional loan. It protects the lender if you default.",
  "timestamp": "2025-01-03T10:30:00Z"
}
```

### Get Chat History
```http
GET /api/chat/history
```
**Description**: Retrieve chat conversation history  
**Authentication**: Session-based  
**Parameters**: `session_id` (query parameter)

### Get Chat Updates
```http
GET /api/chat/updates
```
**Description**: Get real-time chat updates  
**Authentication**: Session-based  
**Parameters**: `session_id` (query parameter)

---

## Beta API Endpoints

### Submit Feedback
```http
POST /beta/feedback
```
**Description**: Submit beta testing feedback  
**Authentication**: Beta access required  
**Content-Type**: `application/x-www-form-urlencoded`

#### Request Body
```
feedback_type=bug&
user_email=test@example.com&
message=Calculator not working properly&
priority=high
```

#### Response
```json
{
  "status": "success",
  "message": "Feedback submitted successfully"
}
```

---

## Health Check Endpoints

### Application Health
```http
GET /health
```
**Description**: Get application health status  
**Authentication**: None

#### Response
```json
{
  "status": "healthy",
  "version": "2.0.1",
  "features": [
    "mortgage_calculator",
    "refinance_calculator",
    "admin_dashboard",
    "chat_support"
  ],
  "last_updated": "2025-01-03T00:00:00Z",
  "environment": "production",
  "timestamp": "2025-01-03T10:30:00Z"
}
```

---

## Error Handling

### Error Response Format
All API endpoints return errors in a consistent format:

```json
{
  "success": false,
  "error": "Error message description",
  "field": "field_name",
  "value": "invalid_value",
  "code": "ERROR_CODE"
}
```

### Common HTTP Status Codes
- `200 OK`: Successful request
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Access denied
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error

### Validation Errors
Input validation errors include specific field information:

```json
{
  "success": false,
  "error": "Purchase price must be greater than 0",
  "field": "purchase_price",
  "value": -100000,
  "code": "VALIDATION_ERROR"
}
```

---

## Rate Limiting

### Admin Endpoints
- **Rate Limit**: 100 requests per minute per IP
- **Burst Limit**: 20 requests per 10 seconds
- **Headers**: `X-RateLimit-Limit`, `X-RateLimit-Remaining`

### Public Endpoints
- **Rate Limit**: 60 requests per minute per IP
- **Burst Limit**: 10 requests per 10 seconds

---

## Examples

### Calculate Conventional Loan
```bash
curl -X POST https://your-domain.com/calculate \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: your-csrf-token" \
  -d '{
    "purchase_price": 350000,
    "down_payment_percentage": 20,
    "annual_rate": 6.75,
    "loan_term": 30,
    "loan_type": "conventional",
    "annual_tax_rate": 1.1,
    "annual_insurance_rate": 0.45,
    "monthly_hoa_fee": 75
  }'
```

### Calculate FHA Loan
```bash
curl -X POST https://your-domain.com/calculate \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: your-csrf-token" \
  -d '{
    "purchase_price": 280000,
    "down_payment_percentage": 3.5,
    "annual_rate": 6.25,
    "loan_term": 30,
    "loan_type": "fha",
    "annual_tax_rate": 1.0,
    "annual_insurance_rate": 0.4
  }'
```

### Calculate VA Loan
```bash
curl -X POST https://your-domain.com/calculate \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: your-csrf-token" \
  -d '{
    "purchase_price": 420000,
    "down_payment_percentage": 0,
    "annual_rate": 6.0,
    "loan_term": 30,
    "loan_type": "va",
    "annual_tax_rate": 1.3,
    "annual_insurance_rate": 0.5,
    "va_service_type": "veteran",
    "va_usage": "first",
    "va_disability_exempt": true
  }'
```

### Refinance Analysis
```bash
curl -X POST https://your-domain.com/refinance \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: your-csrf-token" \
  -d '{
    "appraised_value": 500000,
    "original_loan_balance": 380000,
    "original_interest_rate": 7.25,
    "new_interest_rate": 6.125,
    "new_loan_term": 30,
    "annual_taxes": 6000,
    "annual_insurance": 2200,
    "loan_type": "conventional",
    "refinance_type": "rate_term"
  }'
```

---

## Changelog

### Version 2.0.1 (Current)
- Added comprehensive input validation
- Enhanced security with CSRF protection
- Improved error handling and response format
- Added refinance calculator functionality
- Implemented admin dashboard with statistics
- Added chat support system
- Enhanced PMI/MIP calculations for all loan types

### Version 2.0.0
- Major API restructure
- Added transaction type support
- Implemented seller contribution calculations
- Enhanced closing cost calculations
- Added title insurance configuration
- Improved VA loan calculations

---

## Support

For API support and questions:
- **Documentation**: This document
- **Issues**: Check application logs
- **Admin Support**: Use admin dashboard validation tools

---

**Generated by**: Claude Code Assistant  
**Documentation Status**: ✅ Complete  
**API Status**: Production Ready  
**Last Validation**: January 3, 2025