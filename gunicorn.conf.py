"""Gunicorn configuration for production deployment."""
import multiprocessing
import os

# Server socket
bind = "0.0.0.0:8013"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'sync'
worker_connections = 1000
timeout = 30
keepalive = 2

# SSL/TLS Configuration
keyfile = None  # Handled by Render
certfile = None  # Handled by Render
# ssl_version = "TLS"  # Deprecated, using ssl_context instead
ciphers = 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384'

# Process naming
proc_name = 'mortgage_calc'
pythonpath = '.'

# Logging - Store logs in a directory that will be available in Render
log_directory = "./logs"
if not os.path.exists(log_directory):
    os.makedirs(log_directory, exist_ok=True)
    
accesslog = os.path.join(log_directory, "access.log")
errorlog = os.path.join(log_directory, "error.log")
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Server mechanics
daemon = False
pidfile = None  # No pidfile in Render environment
umask = 0o007
user = None  # Let Render handle user permissions
group = None  # Let Render handle group permissions
tmp_upload_dir = None

# SSL Session configuration
ssl_session_cache = None
ssl_session_tickets = False

def when_ready(server):
    """Run when server is ready."""
    pass  # Simply pass as Render handles server readiness

def on_starting(server):
    """Run when server is starting."""
    # Additional startup tasks
    pass

def post_fork(server, worker):
    """Run after worker has been forked."""
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def pre_fork(server, worker):
    """Run before worker is forked."""
    pass

def pre_exec(server):
    """Run before new master process is re-spawned."""
    server.log.info("Forked child, re-executing.")

def when_ready(server):
    """Run when server is ready."""
    server.log.info("Server is ready. Spawning workers...")
