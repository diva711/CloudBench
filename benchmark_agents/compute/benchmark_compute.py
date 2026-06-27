import json
import time
import statistics
import requests
from datetime import datetime, timezone
from google.cloud import storage


EC2_IP         = "20.124.240.168"
GCS_BUCKET     = "cloudbench-results-diva"
GCP_REGION     = "asia-south1"
TARGET_URL     = f"http://{EC2_IP}:5000/ping"
NUM_REQUESTS   = 900
PROVIDER       = "azure"
BENCHMARK_TYPE = "compute_latency"

def run_benchmark():
    print(f"Starting compute latency benchmark against {TARGET_URL}")
    print(f"Sending {NUM_REQUESTS} requests...\n")

    latencies = []
    errors = 0

    for i in range(NUM_REQUESTS):
        try:
            start = time.perf_counter()
            response = requests.get(TARGET_URL, timeout=5)
            end = time.perf_counter()

            if response.status_code == 200:
                latency_ms = (end - start) * 1000
                latencies.append(latency_ms)
            else:
                errors += 1

        except requests.exceptions.RequestException:
            errors += 1

        if (i + 1) % 100 == 0:
            print(f"  {i + 1}/{NUM_REQUESTS} requests done...")

    return latencies, errors

def calculate_stats(latencies, errors):
    if not latencies:
        raise ValueError("No successful requests — check if the VM is running.")

    sorted_lat = sorted(latencies)
    total      = len(latencies) + errors

    def percentile(data, p):
        index = int(len(data) * p / 100)
        return round(data[min(index, len(data) - 1)], 2)

    stats = {
        "provider":        PROVIDER,
        "benchmark_type":  BENCHMARK_TYPE,
        "timestamp":       datetime.now(timezone.utc).isoformat(),
        "target_url":      TARGET_URL,
        "total_requests":  total,
        "successful":      len(latencies),
        "errors":          errors,
        "error_rate_pct":  round((errors / total) * 100, 2),
        "latency_ms": {
            "min":  round(min(latencies), 2),
            "max":  round(max(latencies), 2),
            "mean": round(statistics.mean(latencies), 2),
            "p50":  percentile(sorted_lat, 50),
            "p95":  percentile(sorted_lat, 95),
            "p99":  percentile(sorted_lat, 99),
        }
    }
    return stats


#def save_to_gcs(stats):
#    client    = storage.Client()
#    bucket    = client.bucket(GCS_BUCKET)
#    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
#    filename  = f"{PROVIDER}/{BENCHMARK_TYPE}/{timestamp}.json"
#    blob      = bucket.blob(filename)
#    blob.upload_from_string(json.dumps(stats, indent=2), content_type="application/json")
#    print(f"\nResults saved to gs://{GCS_BUCKET}/{filename}") 


def save_locally(stats):
    local_path = f"results/azure_compute_latency.json"
    with open(local_path, "w") as f:
        json.dump(stats, f, indent=2)
    print(f"Results saved locally to {local_path}")


def main():
    latencies, errors = run_benchmark()
    stats = calculate_stats(latencies, errors)

    print("\n" + "="*50)
    print("BENCHMARK RESULTS")
    print("="*50)
    print(f"Provider:       {stats['provider'].upper()}")
    print(f"Successful:     {stats['successful']}/{stats['total_requests']} requests")
    print(f"Error rate:     {stats['error_rate_pct']}%")
    print(f"Latency (ms):")
    print(f"  Min:          {stats['latency_ms']['min']}")
    print(f"  Mean:         {stats['latency_ms']['mean']}")
    print(f"  p50:          {stats['latency_ms']['p50']}")
    print(f"  p95:          {stats['latency_ms']['p95']}")
    print(f"  p99:          {stats['latency_ms']['p99']}")
    print(f"  Max:          {stats['latency_ms']['max']}")
    print("="*50)

    # save_to_gcs(stats)
    save_locally(stats)
    print("\nBenchmark complete!")

if __name__ == "__main__":
    main()