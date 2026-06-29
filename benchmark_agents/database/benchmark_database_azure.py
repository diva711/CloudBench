import psycopg2
import json
import time
import threading
import statistics
from datetime import datetime, timezone

DB_CONFIG = {
    "host": "cloudbench-db3.postgres.database.azure.com",
    "port":     5432,
    "database": "postgres",
    "user":     "benchmarkadmin",
    "password": "BenchmarkPass2024!",
    "sslmode":  "require"
}

PROVIDER       = "azure"
BENCHMARK_TYPE = "database_load"
RESULTS_FILE   = r"D:\CloudBench\results\azure_database.json"
CONCURRENCY_LEVELS = [1, 10, 50, 100]
QUERIES_PER_THREAD = 20

def setup_schema(conn):
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS benchmark_test (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100),
            value FLOAT,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    cur.execute("SELECT COUNT(*) FROM benchmark_test")
    if cur.fetchone()[0] < 1000:
        for i in range(1000):
            cur.execute(
                "INSERT INTO benchmark_test (name, value) VALUES (%s, %s)",
                (f"item_{i}", i * 1.5)
            )
    conn.commit()
    cur.close()
    print("Schema ready.")

def worker(results, thread_id):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur  = conn.cursor()
        for i in range(QUERIES_PER_THREAD):
            op = i % 4  # cycle through 4 CRUD operations

            start = time.perf_counter()

            if op == 0:
                # CREATE — INSERT a new row
                cur.execute(
                    "INSERT INTO benchmark_test (name, value) VALUES (%s, %s) RETURNING id",
                    (f"crud_{thread_id}_{i}", thread_id * 1.1)
                )
                cur.fetchone()

            elif op == 1:
                # READ — SELECT a row
                cur.execute(
                    "SELECT * FROM benchmark_test WHERE id = %s",
                    (thread_id % 1000 + 1,)
                )
                cur.fetchone()

            elif op == 2:
                # UPDATE — modify a row
                cur.execute(
                    "UPDATE benchmark_test SET value = %s WHERE id = %s",
                    (thread_id * 2.2, thread_id % 1000 + 1)
                )

            elif op == 3:
                # DELETE — remove a recently inserted row
                cur.execute(
                    "DELETE FROM benchmark_test WHERE name = %s",
                    (f"crud_{thread_id}_{i-3}",)
                )

            conn.commit()
            elapsed_ms = (time.perf_counter() - start) * 1000
            results.append(elapsed_ms)

        cur.close()
        conn.close()
    except Exception as e:
        print(f"Thread {thread_id} error: {e}")
        
def run_at_concurrency(level):
    print(f"\n  Concurrency {level}...")
    results = []
    threads = [threading.Thread(target=worker, args=(results, i)) for i in range(level)]
    start = time.perf_counter()
    for t in threads: t.start()
    for t in threads: t.join()
    total_ms = (time.perf_counter() - start) * 1000
    if not results: return None
    results.sort()
    def pct(d, p): return round(d[min(int(len(d)*p/100), len(d)-1)], 2)
    stats = {
        "concurrency": level,
        "total_queries": len(results),
        "total_time_ms": round(total_ms, 2),
        "throughput_qps": round(len(results) / (total_ms / 1000), 1),
        "latency_ms": {
            "min":  round(min(results), 2),
            "mean": round(statistics.mean(results), 2),
            "p50":  pct(results, 50),
            "p95":  pct(results, 95),
            "p99":  pct(results, 99),
            "max":  round(max(results), 2),
        }
    }
    print(f"    p50={stats['latency_ms']['p50']}ms  p99={stats['latency_ms']['p99']}ms  QPS={stats['throughput_qps']}")
    return stats

def main():
    print("Database Load Benchmark — Azure")
    print("=" * 50)
    conn = psycopg2.connect(**DB_CONFIG)
    setup_schema(conn)
    conn.close()

    all_results = {}
    for level in CONCURRENCY_LEVELS:
        result = run_at_concurrency(level)
        if result:
            all_results[str(level)] = result

    rep = all_results.get("10", list(all_results.values())[0])
    output = {
        "provider":       PROVIDER,
        "benchmark_type": BENCHMARK_TYPE,
        "timestamp":      datetime.now(timezone.utc).isoformat(),
        "target_url":     DB_CONFIG["host"],
        "results_by_concurrency": all_results,
        "latency_ms": {
            "min":  rep["latency_ms"]["min"],
            "max":  rep["latency_ms"]["max"],
            "mean": rep["latency_ms"]["mean"],
            "p50":  rep["latency_ms"]["p50"],
            "p95":  rep["latency_ms"]["p95"],
            "p99":  rep["latency_ms"]["p99"],
        }
    }

    print("\n" + "=" * 50)
    print("RESULTS SUMMARY")
    print("=" * 50)
    print(f"{'Concurrency':<15} {'p50 (ms)':<12} {'p99 (ms)':<12} {'QPS'}")
    print("-" * 50)
    for level, r in all_results.items():
        print(f"{level:<15} {r['latency_ms']['p50']:<12} {r['latency_ms']['p99']:<12} {r['throughput_qps']}")

    with open(RESULTS_FILE, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nSaved to {RESULTS_FILE}")

if __name__ == "__main__":
    main()
