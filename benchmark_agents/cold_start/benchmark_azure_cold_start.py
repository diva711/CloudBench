import json
import time
import statistics
import requests
import subprocess
from datetime import datetime, timezone

PROVIDER       = "azure"
BENCHMARK_TYPE = "cold_start"
NUM_SAMPLES    = 5
RESULTS_FILE   = r"D:\CloudBench\results\azure_cold_start.json"
VM_NAME        = "cloudbench-vm"
RESOURCE_GROUP = "cloudbench-rg"
FLASK_URL      = "http://20.124.240.168:5000/ping"

def run_az(scripts):
    result = subprocess.run(
        f'az vm run-command invoke --resource-group {RESOURCE_GROUP} --name {VM_NAME} --command-id RunShellScript --scripts "{scripts}"',
        capture_output=True, text=True, shell=True
    )
    return result.stdout

def force_cold_start():
    run_az("pkill -f app.py; sleep 2")
    run_az("sudo /home/azureuser/venv/bin/python3 /home/azureuser/app.py > /home/azureuser/flask.log 2>&1 &")
    time.sleep(5)

def invoke_and_measure():
    start = time.perf_counter()
    response = requests.get(FLASK_URL, timeout=60)
    end = time.perf_counter()
    return round((end - start) * 1000, 2)

def main():
    print(f"Cold Start Benchmark — Azure VM Flask")
    print(f"Running {NUM_SAMPLES} cold start measurements...\n")

    measurements = []

    for i in range(NUM_SAMPLES):
        print(f"Sample {i+1}/{NUM_SAMPLES}:")
        print("  Forcing cold start (restarting Flask)...")
        force_cold_start()
        print("  Invoking endpoint...")
        duration_ms = invoke_and_measure()
        measurements.append(duration_ms)
        print(f"  Cold start duration: {duration_ms}ms\n")

    measurements.sort()

    def percentile(data, p):
        index = int(len(data) * p / 100)
        return round(data[min(index, len(data)-1)], 2)

    stats = {
        "provider":       PROVIDER,
        "benchmark_type": BENCHMARK_TYPE,
        "timestamp":      datetime.now(timezone.utc).isoformat(),
        "function_name":  "azure-flask-cold-start",
        "num_samples":    NUM_SAMPLES,
        "cold_start_ms": {
            "min":  round(min(measurements), 2),
            "max":  round(max(measurements), 2),
            "mean": round(statistics.mean(measurements), 2),
            "p50":  percentile(measurements, 50),
            "p95":  percentile(measurements, 95),
            "p99":  percentile(measurements, 99),
        },
        "raw_measurements_ms": measurements
    }

    print("=" * 50)
    print("COLD START RESULTS")
    print("=" * 50)
    print(f"Samples:    {NUM_SAMPLES}")
    print(f"Min:        {stats['cold_start_ms']['min']}ms")
    print(f"Mean:       {stats['cold_start_ms']['mean']}ms")
    print(f"p50:        {stats['cold_start_ms']['p50']}ms")
    print(f"p95:        {stats['cold_start_ms']['p95']}ms")
    print(f"p99:        {stats['cold_start_ms']['p99']}ms")
    print(f"Max:        {stats['cold_start_ms']['max']}ms")
    print("=" * 50)

    with open(RESULTS_FILE, "w") as f:
        json.dump(stats, f, indent=2)
    print(f"\nResults saved to {RESULTS_FILE}")

if __name__ == "__main__":
    main()