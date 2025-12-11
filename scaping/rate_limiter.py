"""Simple per-host rate limiter (minimum delay between requests per host)."""
import threading
import time
from urllib.parse import urlparse


class HostRateLimiter:
    def __init__(self, min_delay=0.5):
        self.min_delay = float(min_delay)
        self.lock = threading.Lock()
        self.last_access = {}

    def wait(self, url):
        host = urlparse(url).netloc
        now = time.time()
        with self.lock:
            last = self.last_access.get(host, 0)
            next_allowed = last + self.min_delay
            if next_allowed > now:
                to_sleep = next_allowed - now
                time.sleep(to_sleep)
            self.last_access[host] = time.time()
