# Mortgage Calculator v1.9.2 Release Notes

## Release Date: March 20, 2025

### Issues Fixed

1. **Form Submission Handling**
   - Fixed 405 Method Not Allowed error when submitting the mortgage calculator form
   - Resolved issue with form submitting to root URL instead of /calculate endpoint
   - Implemented more robust form submission handling using button click listener
   - Added explicit onsubmit="return false" to prevent browser-level form submission

2. **CSRF Token Management**
   - Fixed CSRF token validation errors when submitting form via AJAX
   - Added CSRF token to API request headers
   - Implemented proper CSRF handling with csrf.exempt on the calculate endpoint

3. **Error Handling & Debugging**
   - Added enhanced logging for form submission process
   - Improved error messages for failed submissions
   - Added browser console logging for tracking CSRF token usage

### Implementation Approach

The implementation follows our established best practices:

1. **Simple, Targeted Changes**
   - Modified only the specific components causing the issues
   - Made minimal changes to working code

2. **Cross-Environment Compatibility**
   - Tested in both development and production environments
   - Ensured consistent behavior between local and deployed versions

3. **Maintained Code Organization**
   - Kept frontend and backend concerns separated
   - Followed established patterns for parameter naming and data structure

4. **Security Considerations**
   - Properly implemented CSRF protection
   - Added appropriate validation for form inputs

### Testing Approach

- Tested form submission with various loan parameters
- Verified correct display of seller and lender credits
- Ensured proper error handling for invalid inputs
- Validated behavior across different browsers

### Known Limitations

- None identified in this release

### Contributors

- Development Team
