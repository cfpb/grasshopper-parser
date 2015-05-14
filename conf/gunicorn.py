import multiprocessing

# Number of workers based on Gunicorn docs:
#   http://gunicorn-docs.readthedocs.org/en/latest/design.html#how-many-workers
workers = multiprocessing.cpu_count() * 2 + 1

# Logging
loglevel = "info"
# "-" = stderr
accesslog = "-"
errorlog = "-"
