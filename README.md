# CloudBench — Cloud Provider Performance Benchmarking Platform

A research platform that benchmarks AWS, GCP, and Azure performance across compute latency, cold start times, and storage throughput.

## Results Summary

| Benchmark | AWS p99 | GCP p99 | Azure p99 |
|-----------|---------|---------|-----------|
| Compute Latency | 1740ms | 173ms | 717ms |
| Cold Start | 2053ms | 325ms | 676ms |
| Storage Throughput | 7373ms | 612ms | 1223ms |

**GCP wins** compute and storage from India. **Azure** beats AWS on all metrics.

## Architecture
Benchmark Agents (Python)

→ Results JSON → S3/GCS/Azure Blob

→ ETL Pipeline (Python)

→ PostgreSQL (local)

→ Streamlit Dashboard

## Stack
- **Infrastructure:** Terraform (AWS + GCP + Azure)
- **Benchmarks:** Python (boto3, google-cloud-storage, azure-storage-blob, locust)
- **Database:** PostgreSQL
- **Dashboard:** Streamlit + Plotly
- **Cloud:** AWS ap-south-1, GCP asia-south1, Azure eastus

## Benchmark Agents
- `benchmark_agents/compute/` — VM HTTP latency (1000 requests, p50/p95/p99)
- `benchmark_agents/cold_start/` — Serverless cold start timing
- `benchmark_agents/storage/` — Object storage upload/download throughput

## Setup
```bash
pip install boto3 google-cloud-storage azure-storage-blob streamlit plotly psycopg2-binary requests
```

Configure credentials for each provider, then run any benchmark agent directly.

## Dashboard
```bash
python -m streamlit run dashboard/dashboard.py
```