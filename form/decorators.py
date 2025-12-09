import time
from functools import wraps
from .metrics import FORM_LATENCIA

def form_metrics(endpoint_name):
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            method = request.method
            inicio = time.time()

            try:
                response = func(request, *args, **kwargs)
                status = getattr(response, "status_code", 200)
            except Exception:
                status = 500
                raise
            finally:
                duracao = time.time() - inicio
                FORM_LATENCIA.labels(endpoint=endpoint_name, method=method).observe(duracao)

            return response
        return wrapper
    return decorator
