from prometheus_client import Counter, Histogram, Gauge


class Metrics:
    def __init__(self):
        self.requests_total = Counter(
            "requests_total", "Total number of requests", ["endpoint", "method", "status"]
        )
        self.request_latency = Histogram(
            "request_latency_seconds", "Latency of requests in seconds", buckets=(0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10)
        )
        self.gpu_memory_used = Gauge("gpu_memory_used_bytes", "GPU memory used in bytes")
