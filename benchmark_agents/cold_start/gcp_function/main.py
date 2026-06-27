import functions_framework
import time

@functions_framework.http
def hello(request):
    return {"status": "ok", "provider": "gcp", "timestamp": time.time()}