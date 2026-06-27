import json
import time

def handler(event, context):
    return {
        "statusCode": 200,
        "body": json.dumps({
            "status": "ok",
            "timestamp": time.time()
        })
    }