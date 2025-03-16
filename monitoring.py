"""Monitoring configuration for the mortgage calculator application."""
from prometheus_flask_exporter import PrometheusMetrics
from flask import request
import logging
import time
from functools import wraps

class MonitoringManager:
    def __init__(self, app=None):
        self.app = app
        self.logger = logging.getLogger(__name__)
        self.metrics = None
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize monitoring for the application."""
        self.app = app
        
        # Initialize Prometheus metrics
        self.metrics = PrometheusMetrics(app)
        
        # Add default metrics
        self.metrics.info('app_info', 'Application info', version='1.0.0')
        
        # Define custom metrics
        self.request_latency = self.metrics.histogram(
            'request_latency_seconds',
            'Request latency in seconds',
            labels={'path': lambda: request.path}
        )
        
        self.active_users = self.metrics.gauge(
            'active_users',
            'Number of active users'
        )
        
        self.calculation_errors = self.metrics.counter(
            'calculation_errors_total',
            'Total number of calculation errors'
        )
        
        # Register monitoring endpoints
        @app.route('/metrics')
        @self.metrics.do_not_track()
        def metrics():
            return self.metrics.generate_latest()
        
        @app.route('/health')
        @self.metrics.do_not_track()
        def health():
            return {'status': 'healthy'}
        
        # Add request monitoring
        @app.before_request
        def before_request():
            request.start_time = time.time()
        
        @app.after_request
        def after_request(response):
            if hasattr(request, 'start_time'):
                request_latency = time.time() - request.start_time
                self.request_latency.observe(request_latency)
            return response
    
    def track_calculation(self):
        """Decorator to track mortgage calculations."""
        def decorator(f):
            @wraps(f)
            def wrapped(*args, **kwargs):
                try:
                    start_time = time.time()
                    result = f(*args, **kwargs)
                    calculation_time = time.time() - start_time
                    
                    # Record calculation time
                    self.metrics.histogram(
                        'mortgage_calculation_seconds',
                        'Time spent calculating mortgage details'
                    ).observe(calculation_time)
                    
                    return result
                except Exception as e:
                    # Record calculation error
                    self.calculation_errors.inc()
                    self.logger.error(f"Calculation error: {str(e)}")
                    raise
            return wrapped
        return decorator
    
    def track_active_user(self):
        """Decorator to track active users."""
        def decorator(f):
            @wraps(f)
            def wrapped(*args, **kwargs):
                self.active_users.inc()
                try:
                    return f(*args, **kwargs)
                finally:
                    self.active_users.dec()
            return wrapped
        return decorator
