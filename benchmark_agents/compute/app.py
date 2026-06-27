# This is a minimal Flask API that runs on the EC2 VM.
# The benchmark agent will send HTTP requests to this and measure response time.

from flask import Flask, jsonify
import time

app = Flask(__name__)

@app.route("/ping")
def ping():
    return jsonify({"status": "ok", "timestamp": time.time()})

@app.route("/compute")
def compute():
    # Simulate a tiny bit of CPU work so the benchmark is realistic
    result = sum(i * i for i in range(1000))
    return jsonify({"status": "ok", "result": result})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)