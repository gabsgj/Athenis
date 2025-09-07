from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry

class Metrics:
    def __init__(self):
        # Use a dedicated registry for this instance
        self.registry = CollectorRegistry()

        self.requests_total = Counter(
            "requests_total", 
            "Total number of requests", 
            ["endpoint", "method", "status"], 
            registry=self.registry  # attach to custom registry
        )

        self.request_latency = Histogram(
            "request_latency_seconds", 
            "Latency of requests in seconds", 
            buckets=(0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10),
            registry=self.registry
        )

        self.gpu_memory_used = Gauge(
            "gpu_memory_used_bytes", 
            "GPU memory used in bytes",
            registry=self.registry
        )
