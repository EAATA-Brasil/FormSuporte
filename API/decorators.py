import time
from functools import wraps
from .metrics import API_REQUESTS, API_LATENCY

def api_metrics(endpoint_name):
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            method = request.method
            start = time.time()

            try:
                response = func(request, *args, **kwargs)
                status = getattr(response, "status_code", 200)
            except Exception as e:
                status = 500
                raise e
            finally:
                duration = time.time() - start
                API_REQUESTS.labels(endpoint=endpoint_name, method=method, status=status).inc()
                API_LATENCY.labels(endpoint=endpoint_name, method=method).observe(duration)

            return response
        return wrapper
    return decorator
