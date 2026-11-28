"""Loopback-only serving; confirm 8502 is unused before installation."""
bind = '127.0.0.1:8502'
workers = 2
worker_class = 'sync'
timeout = 120
graceful_timeout = 30
accesslog = '-'
errorlog = '-'
forwarded_allow_ips = '127.0.0.1'
