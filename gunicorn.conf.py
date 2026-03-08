"""
Gunicorn Configuration for XAgent Web Admin Interface

This configuration file provides production-ready settings for running
the Web Admin Interface with Gunicorn WSGI HTTP Server.

Usage:
    gunicorn -c gunicorn.conf.py src.xagent.web_admin.server:app

Environment Variables:
    WEB_ADMIN_HOST: Server bind address (default: 0.0.0.0)
    WEB_ADMIN_PORT: Server bind port (default: 5000)
    WEB_ADMIN_WORKERS: Number of worker processes (default: auto-calculated)
    WEB_ADMIN_LOG_LEVEL: Logging level (default: info)
"""

import os
import multiprocessing

# Server Socket
# -------------
# Bind address and port
bind = f"{os.environ.get('WEB_ADMIN_HOST', '0.0.0.0')}:{os.environ.get('WEB_ADMIN_PORT', '5000')}"

# Backlog - The maximum number of pending connections
backlog = 2048


# Worker Processes
# ----------------
# Number of worker processes
# Recommended: (2 x $num_cores) + 1
# Can be overridden with WEB_ADMIN_WORKERS environment variable
workers = int(os.environ.get('WEB_ADMIN_WORKERS', multiprocessing.cpu_count() * 2 + 1))

# Worker class - sync is suitable for CPU-bound tasks
# Use 'gevent' or 'eventlet' for async I/O if needed
worker_class = 'sync'

# Maximum number of requests a worker will process before restarting
# Helps prevent memory leaks
max_requests = 1000
max_requests_jitter = 50  # Randomize restart to avoid all workers restarting at once

# Worker timeout in seconds
# Increase if you have long-running requests
timeout = 120

# Graceful timeout - time to wait for workers to finish serving requests during shutdown
graceful_timeout = 30

# Keep-alive timeout
keepalive = 5


# Logging
# -------
# Log level
loglevel = os.environ.get('WEB_ADMIN_LOG_LEVEL', 'info')

# Access log file path
# Use '-' for stdout, or specify a file path
accesslog = os.environ.get('WEB_ADMIN_ACCESS_LOG', 'logs/web_admin_access.log')

# Error log file path
# Use '-' for stderr, or specify a file path
errorlog = os.environ.get('WEB_ADMIN_ERROR_LOG', 'logs/web_admin_error.log')

# Access log format
# h: remote address, l: '-', u: user name, t: date/time, r: request line,
# s: status, b: response length, f: referer, a: user agent, D: request time in microseconds
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Capture stdout/stderr to log files
capture_output = True

# Enable access log
accesslog = accesslog if accesslog != '-' else None
errorlog = errorlog if errorlog != '-' else None


# Process Naming
# --------------
# Process name prefix
proc_name = 'xagent_web_admin'


# Server Mechanics
# ----------------
# Daemonize the Gunicorn process (detach from terminal)
# Set to True for production deployment with systemd/supervisor
daemon = False

# PID file path
pidfile = os.environ.get('WEB_ADMIN_PID_FILE', 'logs/web_admin.pid')

# User and group to run workers as
# Uncomment and set if you want to drop privileges
# user = 'www-data'
# group = 'www-data'

# Directory to change to before loading the app
# chdir = '/path/to/app'

# Preload application code before worker processes are forked
# This can save RAM and speed up server boot times
preload_app = True


# Server Hooks
# ------------
def on_starting(server):
    """Called just before the master process is initialized."""
    server.log.info("Starting Gunicorn server for Web Admin Interface")


def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP."""
    server.log.info("Reloading Gunicorn workers")


def when_ready(server):
    """Called just after the server is started."""
    server.log.info(f"Gunicorn server is ready. Listening on: {bind}")
    server.log.info(f"Workers: {workers}, Worker class: {worker_class}")


def pre_fork(server, worker):
    """Called just before a worker is forked."""
    pass


def post_fork(server, worker):
    """Called just after a worker has been forked."""
    server.log.info(f"Worker spawned (pid: {worker.pid})")


def pre_exec(server):
    """Called just before a new master process is forked."""
    server.log.info("Forking new master process")


def worker_int(worker):
    """Called when a worker receives the SIGINT or SIGQUIT signal."""
    worker.log.info(f"Worker received INT or QUIT signal (pid: {worker.pid})")


def worker_abort(worker):
    """Called when a worker receives the SIGABRT signal."""
    worker.log.info(f"Worker received SIGABRT signal (pid: {worker.pid})")


def pre_request(worker, req):
    """Called just before a worker processes the request."""
    worker.log.debug(f"{req.method} {req.path}")


def post_request(worker, req, environ, resp):
    """Called after a worker processes the request."""
    pass


def child_exit(server, worker):
    """Called just after a worker has been exited."""
    server.log.info(f"Worker exited (pid: {worker.pid})")


def worker_exit(server, worker):
    """Called just after a worker has been exited."""
    pass


def nworkers_changed(server, new_value, old_value):
    """Called just after num_workers has been changed."""
    server.log.info(f"Number of workers changed from {old_value} to {new_value}")


def on_exit(server):
    """Called just before exiting Gunicorn."""
    server.log.info("Shutting down Gunicorn server")


# SSL Configuration (Optional)
# ----------------------------
# Uncomment and configure if you want to enable HTTPS
# Note: It's recommended to use a reverse proxy (Nginx) for SSL termination

# keyfile = '/path/to/ssl/key.pem'
# certfile = '/path/to/ssl/cert.pem'
# ssl_version = 2  # TLS 1.2
# cert_reqs = 0  # No client certificate required
# ca_certs = '/path/to/ca_certs.pem'
# ciphers = 'TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256:TLS_AES_128_GCM_SHA256'


# Security
# --------
# Limit request line size
limit_request_line = 4096

# Limit request header field size
limit_request_fields = 100
limit_request_field_size = 8190

# Forwarded allow IPs - for proxy setups
# Set to '*' to trust all proxies, or specify IP addresses
forwarded_allow_ips = os.environ.get('FORWARDED_ALLOW_IPS', '127.0.0.1')


# Performance Tuning
# ------------------
# Worker connections (for async workers)
# worker_connections = 1000

# Worker temporary directory
# worker_tmp_dir = '/dev/shm'  # Use RAM disk for better performance

# Paste configuration (optional)
# paste = None
# paste_global_conf = {}
