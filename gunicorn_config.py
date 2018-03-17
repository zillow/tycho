import os
import multiprocessing
import sys
# extra worker is to take advantage of all CPUs,
# even during a restart.
workers = multiprocessing.cpu_count() + 1
max_requests = 10000
# this should be max_requests / 2, to provide
# adequate jitter between worker restarts.
max_requests_jitter = 5000
worker_class = "aiohttp.worker.GunicornWebWorker"
bind = "0.0.0.0:80"
