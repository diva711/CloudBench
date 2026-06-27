import json
import time
import os
import statistics
import subprocess
from datetime import datetime, timezone
from azure.storage.blob import BlobServiceClient

# ─── CONFIG ───────────────────────────────────────────────────────────────────
PROVIDER             = "azure"
BENCHMARK_TYPE       = "storage_throughput"
RESULTS_FILE         = r"D:\CloudBench\results\azure_storage.json"
RESOURCE_GROUP       = "cloudbench-rg"
CONTAINER_NAME       = "benchmarkdata"

FILE_SIZES = {
    "1MB":   1 * 1024 * 1024,
    "10MB":  10 * 1024 * 1024,
    "100MB": 100 * 1024 * 1024,
}
NUM_RUNS = 3

def get_storage_account_name():
    result = subprocess.run([
        "az", "storage", "account", "list",
        "--resource-group", RESOURCE_GROUP,
        "--query", "[0].name",
        "--output", "tsv"
    ], capture_output=True, text=True)
    name = result.stdout.strip()
    if not name:
        raise Exception("No storage account found in resource group. Create one first.")
    return name

def get_connection_string(account_name):
    import subprocess
    result = subprocess.run(
        f'az storage account show-connection-string --resource-group {RESOURCE_GROUP} --name {account_name} --query connectionString --output tsv',
        capture_output=True, text=True, shell=True
    )
    return result.stdout.strip()

def benchmark_size(container_client, label, size_bytes):
    print(f"\n  Testing {label} file ({size_bytes // (1024*1024)}MB)...")
    data = os.urandom(size_bytes)
    blob_name = f"benchmark-test/test_{label}.bin"
    blob_client = container_client.get_blob_client(blob_name)

    upload_times   = []
    download_times = []

    for run in range(NUM_RUNS):
        start = time.perf_counter()
        blob_client.upload_blob(data, overwrite=True)
        upload_ms = (time.perf_counter() - start) * 1000
        upload_times.append(upload_ms)

        start = time.perf_counter()
        blob_client.download_blob().readall()
        download_ms = (time.perf_counter() - start) * 1000
        download_times.append(download_ms)

        print(f"    Run {run+1}: upload={upload_ms:.0f}ms  download={download_ms:.0f}ms")

    try:
        blob_client.delete_blob()
    except Exception:
        pass

    def throughput_mbps(ms, size_bytes):
        return round((size_bytes / (1024 * 1024)) / (ms / 1000), 2)

    return {
        "upload_ms": {
            "mean": round(statistics.mean(upload_times), 2),
            "min":  round(min(upload_times), 2),
            "max":  round(max(upload_times), 2),
        },
        "download_ms": {
            "mean": round(statistics.mean(download_times), 2),
            "min":  round(min(download_times), 2),
            "max":  round(max(download_times), 2),
        },
        "upload_throughput_mbps":   throughput_mbps(statistics.mean(upload_times), size_bytes),
        "download_throughput_mbps": throughput_mbps(statistics.mean(download_times), size_bytes),
    }

def main():
    print("Storage Throughput Benchmark — Azure")
    print("=" * 50)

    STORAGE_ACCOUNT_NAME = "cloudbenchstorage001"
    account_name = STORAGE_ACCOUNT_NAME
    print(f"Using storage account: {account_name}")

    conn_str = get_connection_string(account_name)
    service_client = BlobServiceClient.from_connection_string(conn_str)
    container_client = service_client.get_container_client(CONTAINER_NAME)

    try:
        container_client.create_container()
        print(f"Created container: {CONTAINER_NAME}")
    except Exception:
        print(f"Using existing container: {CONTAINER_NAME}")

    results = {}
    for label, size in FILE_SIZES.items():
        results[label] = benchmark_size(container_client, label, size)

    print("\n" + "=" * 50)
    print("STORAGE THROUGHPUT RESULTS")
    print("=" * 50)
    print(f"{'File Size':<10} {'Upload (ms)':<15} {'Download (ms)':<15} {'Up (MB/s)':<12} {'Down (MB/s)'}")
    print("-" * 65)
    for label, r in results.items():
        print(f"{label:<10} {r['upload_ms']['mean']:<15.0f} {r['download_ms']['mean']:<15.0f} {r['upload_throughput_mbps']:<12.1f} {r['download_throughput_mbps']:.1f}")
    print("=" * 50)

    output = {
        "provider":        PROVIDER,
        "benchmark_type":  BENCHMARK_TYPE,
        "timestamp":       datetime.now(timezone.utc).isoformat(),
        "storage_account": account_name,
        "container":       CONTAINER_NAME,
        "num_runs":        NUM_RUNS,
        "results_by_size": results,
        "latency_ms": {
            "min":  results["10MB"]["upload_ms"]["min"],
            "max":  results["10MB"]["upload_ms"]["max"],
            "mean": results["10MB"]["upload_ms"]["mean"],
            "p50":  results["10MB"]["upload_ms"]["mean"],
            "p95":  results["10MB"]["upload_ms"]["max"],
            "p99":  results["10MB"]["upload_ms"]["max"],
        }
    }

    with open(RESULTS_FILE, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nResults saved to {RESULTS_FILE}")

if __name__ == "__main__":
    main()