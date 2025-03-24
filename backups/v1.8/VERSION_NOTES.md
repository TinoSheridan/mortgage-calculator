# Mortgage Calculator Version 1.8

## Release Date
March 17, 2025

## Major Changes

### 1. Seller Contribution Warnings
- Added warning messages when seller credits exceed maximum allowed contributions
- Implemented different handling for VA loans vs. conventional/FHA/USDA loans
- Warnings clearly display the maximum allowed contribution amount

### 2. VA Loan-Specific Rules
- Implemented special handling for VA loans that have different seller contribution rules
- Properly differentiates between unlimited closing costs coverage and 4% limit on concessions (prepaids and discount points)
- Warning message specific to VA loans explains the 4% concession limit

### 3. Discount Points Integration
- Added discount points input field to the mortgage calculator form
- Integrated discount points into the loan details display section
- Points are displayed with 3 decimal places for precision

## Technical Improvements

### 1. Backend Enhancements
- Created a `calculate_max_seller_contribution` function that calculates maximum allowed seller contributions based on:
  - Loan type (conventional, FHA, VA, USDA)
  - LTV ratio
  - Property occupancy (primary residence, second home, investment property)
- Enhanced the `/calculate` endpoint to include maximum seller contribution data and warning flags
- Added special calculation logic for VA loans to check prepaids and discount points against 4% limit

### 2. Frontend Improvements
- Added property usage (occupancy) dropdown field to determine appropriate seller contribution limits
- Implemented dynamic warning display in the credits table 
- Added highlighting for seller credits that exceed limits (warning background and red text)
- Fixed VA loan calculation issues by properly handling large values in JSON responses

## Bug Fixes
- Fixed issue with VA loan calculations by replacing Infinity with a large numeric value for JSON compatibility
- Improved error handling in JavaScript when processing loan details

## Configuration
- Relies on seller_contributions.json for maximum contribution limits by loan type and occupancy
- Frontend and backend validation works together to provide accurate warnings

## UI/UX Improvements
- Warning messages are clear and specific about maximum allowed amounts
- Visual indicators (color) help users quickly identify when limits are exceeded
- Discount points field positioned logically after interest rate in both input and results
