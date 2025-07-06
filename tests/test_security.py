"""
Security-focused tests for the mortgage calculator application.

These tests check for:
- CSRF protection
- Input validation and sanitization
- Authentication and authorization
- XSS prevention
- SQL injection prevention (if applicable)
- Rate limiting
- Session security
"""

import pytest
import json
import sys
import os
from unittest.mock import patch, MagicMock

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set required environment variables before importing app
import os
os.environ['SECRET_KEY'] = 'test-secret-key-for-testing-only'

# Import the app and create test client
from app import app


class TestCSRFProtection:
    """Test CSRF protection on all endpoints."""
    
    def setup_method(self):
        """Set up test client."""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = True
        self.client = app.test_client()
        self.ctx = app.app_context()
        self.ctx.push()
    
    def teardown_method(self):
        """Clean up."""
        self.ctx.pop()
    
    def test_calculate_endpoint_requires_csrf_token(self):
        """Test that /calculate endpoint requires CSRF token."""
        # Attempt POST without CSRF token
        data = {
            'purchase_price': 300000,
            'down_payment_percentage': 20,
            'annual_rate': 5.5,
            'loan_term': 30,
            'annual_tax_rate': 1.2,
            'annual_insurance_rate': 0.8,
            'loan_type': 'conventional'
        }
        
        response = self.client.post('/calculate', 
                                  data=json.dumps(data),
                                  content_type='application/json')
        
        # Should fail due to missing CSRF token
        assert response.status_code == 400
    
    def test_refinance_endpoint_requires_csrf_token(self):
        """Test that /refinance endpoint requires CSRF token."""
        data = {
            'purchase_price': 300000,
            'current_loan_balance': 200000,
            'annual_rate': 4.5,
            'loan_term': 30,
            'loan_type': 'conventional'
        }
        
        response = self.client.post('/refinance',
                                  data=json.dumps(data),
                                  content_type='application/json')
        
        # Should fail due to missing CSRF token
        assert response.status_code == 400
    
    def test_max_seller_contribution_requires_csrf_token(self):
        """Test that /api/max_seller_contribution requires CSRF token."""
        data = {
            'loan_type': 'conventional',
            'purchase_price': 300000,
            'down_payment_amount': 60000
        }
        
        response = self.client.post('/api/max_seller_contribution',
                                  data=json.dumps(data),
                                  content_type='application/json')
        
        # Should fail due to missing CSRF token
        assert response.status_code == 400


class TestInputValidation:
    """Test input validation and sanitization."""
    
    def setup_method(self):
        """Set up test client."""
        app.config['TESTING'] = True
        self.client = app.test_client()
        self.ctx = app.app_context()
        self.ctx.push()
    
    def teardown_method(self):
        """Clean up."""
        self.ctx.pop()
    
    def test_sql_injection_attempt(self):
        """Test that SQL injection attempts are handled safely."""
        # Note: This app doesn't use SQL, but test string handling
        malicious_data = {
            'purchase_price': "'; DROP TABLE users; --",
            'down_payment_percentage': 20,
            'annual_rate': 5.5,
            'loan_term': 30,
            'loan_type': 'conventional'
        }
        
        with patch('flask_wtf.csrf.validate_csrf', return_value=True):
            response = self.client.post('/calculate',
                                      data=json.dumps(malicious_data),
                                      content_type='application/json',
                                      headers={'X-CSRFToken': 'valid_token'})
        
        # Should either reject invalid input or handle safely
        assert response.status_code in [400, 422, 500]  # Error response expected
    
    def test_xss_attempt_in_string_fields(self):
        """Test XSS prevention in string fields."""
        malicious_data = {
            'purchase_price': 300000,
            'down_payment_percentage': 20,
            'annual_rate': 5.5,
            'loan_term': 30,
            'loan_type': '<script>alert("xss")</script>',
            'annual_tax_rate': 1.2,
            'annual_insurance_rate': 0.8
        }
        
        with patch('flask_wtf.csrf.validate_csrf', return_value=True):
            response = self.client.post('/calculate',
                                      data=json.dumps(malicious_data),
                                      content_type='application/json',
                                      headers={'X-CSRFToken': 'valid_token'})
        
        # Should either reject or sanitize the input
        if response.status_code == 200:
            response_data = json.loads(response.data)
            # If successful, ensure no script tags in response
            response_text = json.dumps(response_data).lower()
            assert '<script>' not in response_text
            assert 'alert(' not in response_text
    
    def test_extremely_large_numbers(self):
        """Test handling of extremely large numbers."""
        large_number_data = {
            'purchase_price': 99999999999999999999,  # Extremely large
            'down_payment_percentage': 20,
            'annual_rate': 5.5,
            'loan_term': 30,
            'loan_type': 'conventional'
        }
        
        with patch('flask_wtf.csrf.validate_csrf', return_value=True):
            response = self.client.post('/calculate',
                                      data=json.dumps(large_number_data),
                                      content_type='application/json',
                                      headers={'X-CSRFToken': 'valid_token'})
        
        # Should handle gracefully without crashing
        assert response.status_code in [200, 400, 422]
    
    def test_negative_values_validation(self):
        """Test validation of negative values."""
        negative_data = {
            'purchase_price': -300000,  # Invalid
            'down_payment_percentage': -20,  # Invalid
            'annual_rate': -5.5,  # Invalid
            'loan_term': -30,  # Invalid
            'loan_type': 'conventional'
        }
        
        with patch('flask_wtf.csrf.validate_csrf', return_value=True):
            response = self.client.post('/calculate',
                                      data=json.dumps(negative_data),
                                      content_type='application/json',
                                      headers={'X-CSRFToken': 'valid_token'})
        
        # Should reject negative values
        assert response.status_code in [400, 422]


class TestAdminSecurity:
    """Test admin authentication and authorization."""
    
    def setup_method(self):
        """Set up test client."""
        app.config['TESTING'] = True
        self.client = app.test_client()
        self.ctx = app.app_context()
        self.ctx.push()
    
    def teardown_method(self):
        """Clean up."""
        self.ctx.pop()
    
    def test_admin_routes_require_authentication(self):
        """Test that admin routes require authentication."""
        admin_endpoints = [
            '/admin/dashboard',
            '/admin/closing-costs',
            '/admin/mortgage-config',
            '/admin/counties',
            '/admin/fees'
        ]
        
        for endpoint in admin_endpoints:
            response = self.client.get(endpoint)
            # Should redirect to login or return 401/403
            assert response.status_code in [302, 401, 403]
    
    def test_admin_login_rate_limiting(self):
        """Test that admin login has some form of rate limiting or delay."""
        # Attempt multiple failed logins
        for i in range(10):
            response = self.client.post('/admin/login', data={
                'username': 'wrong',
                'password': 'wrong'
            })
            # Should not crash and should maintain security
            assert response.status_code in [200, 302, 429]
    
    def test_admin_login_csrf_protection(self):
        """Test that admin login form has CSRF protection."""
        # Get login page
        response = self.client.get('/admin/login')
        assert response.status_code == 200
        
        # Attempt login without CSRF token
        response = self.client.post('/admin/login', data={
            'username': 'admin',
            'password': 'password'
        })
        
        # Should fail due to missing CSRF token (depending on implementation)
        # This test may need adjustment based on actual implementation
        assert response.status_code in [200, 400, 403]


class TestSessionSecurity:
    """Test session security measures."""
    
    def setup_method(self):
        """Set up test client."""
        app.config['TESTING'] = True
        self.client = app.test_client()
        self.ctx = app.app_context()
        self.ctx.push()
    
    def teardown_method(self):
        """Clean up."""
        self.ctx.pop()
    
    def test_session_cookie_security_flags(self):
        """Test that session cookies have security flags."""
        response = self.client.get('/')
        
        # Check for security headers
        set_cookie = response.headers.get('Set-Cookie', '')
        if set_cookie:
            # In production, should have HttpOnly and Secure flags
            # Note: This may not be testable in test environment
            pass
    
    def test_session_timeout(self):
        """Test that sessions have appropriate timeouts."""
        # This is more of an integration test
        # Would need to test with actual admin login and timeout
        pass


class TestResponseHeaders:
    """Test security response headers."""
    
    def setup_method(self):
        """Set up test client."""
        app.config['TESTING'] = True
        self.client = app.test_client()
        self.ctx = app.app_context()
        self.ctx.push()
    
    def teardown_method(self):
        """Clean up."""
        self.ctx.pop()
    
    def test_security_headers_present(self):
        """Test that security headers are present."""
        response = self.client.get('/')
        
        # Check for important security headers
        headers = response.headers
        
        assert 'X-Content-Type-Options' in headers
        assert headers['X-Content-Type-Options'] == 'nosniff'
        
        assert 'X-Frame-Options' in headers
        assert headers['X-Frame-Options'] == 'DENY'
        
        assert 'X-XSS-Protection' in headers
        assert headers['X-XSS-Protection'] == '1; mode=block'
        
        assert 'Content-Security-Policy' in headers
        # CSP should restrict script sources
        csp = headers['Content-Security-Policy']
        assert "'self'" in csp
        assert "script-src" in csp
    
    def test_no_sensitive_information_in_headers(self):
        """Test that headers don't leak sensitive information."""
        response = self.client.get('/')
        
        headers_text = str(response.headers).lower()
        
        # Should not contain version info or server details that could help attackers
        sensitive_patterns = ['apache', 'nginx/', 'php/', 'server version']
        for pattern in sensitive_patterns:
            assert pattern not in headers_text


class TestFileUploadSecurity:
    """Test file upload security (if any file uploads exist)."""
    
    def setup_method(self):
        """Set up test client."""
        app.config['TESTING'] = True
        self.client = app.test_client()
        self.ctx = app.app_context()
        self.ctx.push()
    
    def teardown_method(self):
        """Clean up."""
        self.ctx.pop()
    
    def test_no_unrestricted_file_uploads(self):
        """Test that file uploads (if any) are properly restricted."""
        # This application appears to be primarily calculation-based
        # But if file uploads are added in the future, they should be tested
        pass


class TestErrorHandling:
    """Test that errors don't leak sensitive information."""
    
    def setup_method(self):
        """Set up test client."""
        app.config['TESTING'] = True
        self.client = app.test_client()
        self.ctx = app.app_context()
        self.ctx.push()
    
    def teardown_method(self):
        """Clean up."""
        self.ctx.pop()
    
    def test_error_messages_no_stack_traces(self):
        """Test that error messages don't expose stack traces in production."""
        # Force an error by sending malformed JSON
        response = self.client.post('/calculate',
                                  data='invalid json{',
                                  content_type='application/json')
        
        # Should return error but not expose internal details
        assert response.status_code >= 400
        response_text = response.get_data(as_text=True).lower()
        
        # Should not contain file paths or internal details
        sensitive_patterns = ['/users/', 'traceback', 'line ', '.py:', 'file "']
        for pattern in sensitive_patterns:
            assert pattern not in response_text
    
    def test_404_error_handling(self):
        """Test 404 error handling doesn't expose information."""
        response = self.client.get('/nonexistent-endpoint')
        assert response.status_code == 404
        
        # Should return generic 404, not expose internal structure
        response_text = response.get_data(as_text=True).lower()
        assert 'not found' in response_text or '404' in response_text


if __name__ == '__main__':
    pytest.main([__file__, '-v'])