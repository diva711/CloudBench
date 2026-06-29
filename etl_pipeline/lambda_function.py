import json
import psycopg2
from datetime import datetime

# For local development we connect directly to local PostgreSQL.
# When deployed to AWS Lambda this will use RDS endpoint instead.
DB_CONFIG = {
    "host":     "localhost",
    "port":     5432,
    "database": "benchmarkdb",
    "user":     "postgres",
    "password": "Nuclear$583"   
}

# MAIN ETL FUNCTION
def process_benchmark_result(json_file_path):
    """
    Reads a benchmark result JSON file and inserts it into PostgreSQL.
    In AWS Lambda this would read from S3 instead of a local file.
    """
    # EXTRACT — read the raw JSON file
    print(f"Reading: {json_file_path}")
    with open(json_file_path, "r") as f:
        data = json.load(f)

    # TRANSFORM — pull out the fields we need
    # Handle both compute (latency_ms) and cold start (cold_start_ms) formats
    latency_data = data.get("latency_ms") or data.get("cold_start_ms")

    record = {
        "provider":        data["provider"],
        "benchmark_type":  data["benchmark_type"],
        "timestamp":       data["timestamp"],
        "target_url":      data.get("target_url", "") or data.get("function_name", ""),
        "total_requests":  data.get("total_requests") or data.get("num_samples", 0),
        "successful":      data.get("successful") or data.get("num_samples", 0),
        "errors":          data.get("errors", 0),
        "error_rate_pct":  data.get("error_rate_pct", 0.0),
        "min_latency_ms":  latency_data["min"],
        "max_latency_ms":  latency_data["max"],
        "mean_latency_ms": latency_data["mean"],
        "p50_latency_ms":  latency_data["p50"],
        "p95_latency_ms":  latency_data["p95"],
        "p99_latency_ms":  latency_data["p99"],
    }

    print(f"Processing: {record['provider']} / {record['benchmark_type']}")

    # LOAD — insert into PostgreSQL
    conn = psycopg2.connect(**DB_CONFIG)
    cur  = conn.cursor()

    cur.execute("""
        INSERT INTO benchmark_results (
            provider, benchmark_type, timestamp, target_url,
            total_requests, successful, errors, error_rate_pct,
            min_latency_ms, max_latency_ms, mean_latency_ms,
            p50_latency_ms, p95_latency_ms, p99_latency_ms
        ) VALUES (
            %(provider)s, %(benchmark_type)s, %(timestamp)s, %(target_url)s,
            %(total_requests)s, %(successful)s, %(errors)s, %(error_rate_pct)s,
            %(min_latency_ms)s, %(max_latency_ms)s, %(mean_latency_ms)s,
            %(p50_latency_ms)s, %(p95_latency_ms)s, %(p99_latency_ms)s
        )
        ON CONFLICT (provider, benchmark_type) DO UPDATE SET
            timestamp      = EXCLUDED.timestamp,
            target_url     = EXCLUDED.target_url,
            total_requests = EXCLUDED.total_requests,
            successful     = EXCLUDED.successful,
            errors         = EXCLUDED.errors,
            error_rate_pct = EXCLUDED.error_rate_pct,
            min_latency_ms = EXCLUDED.min_latency_ms,
            max_latency_ms = EXCLUDED.max_latency_ms,
            mean_latency_ms= EXCLUDED.mean_latency_ms,
            p50_latency_ms = EXCLUDED.p50_latency_ms,
            p95_latency_ms = EXCLUDED.p95_latency_ms,
            p99_latency_ms = EXCLUDED.p99_latency_ms
    """, record)

    conn.commit()
    cur.close()
    conn.close()

    print("Successfully inserted into database!")
    return record

if __name__ == "__main__":
    result = process_benchmark_result(
    r"D:\CloudBench\results\aws_database.json"
    )
    print("\nInserted record:")
    for key, value in result.items():
        print(f"  {key}: {value}")