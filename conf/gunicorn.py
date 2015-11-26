import multiprocessing

# Number of workers based on Gunicorn docs:
#   http://gunicorn-docs.readthedocs.org/en/latest/design.html#how-many-workers
workers = multiprocessing.cpu_count() * 2 + 1

# Logging
loglevel = "info"
# "-" = stderr
accesslog = "-"
errorlog = "-"

# Accept X-Forwarded-For from reverse proxy:
#   http://gunicorn-docs.readthedocs.org/en/latest/settings.html#forwarded-allow-ips
#   http://gunicorn-docs.readthedocs.org/en/latest/deploy.html
forwarded_allow_ips = "*"
