import streamlit as st
import psycopg2
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

DB_CONFIG = {
    "host":     "localhost",
    "port":     5432,
    "database": "benchmarkdb",
    "user":     "postgres",
    "password": "Nuclear$583"
}

@st.cache_data
def load_data():
    conn = psycopg2.connect(**DB_CONFIG)
    df = pd.read_sql("SELECT * FROM benchmark_results ORDER BY timestamp DESC", conn)
    conn.close()
    return df

st.set_page_config(page_title="CloudBench Dashboard", page_icon="☁️", layout="wide")
st.title("☁️ CloudBench — Cloud Provider Performance Dashboard")
st.markdown("Comparing AWS, GCP, and Azure performance across multiple benchmark types.")

df = load_data()

if df.empty:
    st.warning("No benchmark data found. Run some benchmark agents first.")
    st.stop()

st.subheader("Summary")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Benchmarks Run", len(df))
col2.metric("Providers Tested",     df["provider"].nunique())
col3.metric("Benchmark Types",      df["benchmark_type"].nunique())
col4.metric("Total Requests Sent",  f"{df['total_requests'].sum():,}")

st.markdown("---")

st.subheader("Latency Comparison by Provider")
latency_df = df.groupby("provider")[
    ["p50_latency_ms", "p95_latency_ms", "p99_latency_ms"]
].mean().reset_index()

fig_bar = go.Figure()
fig_bar.add_trace(go.Bar(name="p50", x=latency_df["provider"], y=latency_df["p50_latency_ms"], marker_color="#3C3489"))
fig_bar.add_trace(go.Bar(name="p95", x=latency_df["provider"], y=latency_df["p95_latency_ms"], marker_color="#5DCAA5"))
fig_bar.add_trace(go.Bar(name="p99", x=latency_df["provider"], y=latency_df["p99_latency_ms"], marker_color="#F5A623"))
fig_bar.update_layout(
    barmode="group",
    xaxis_title="Cloud Provider",
    yaxis_title="Latency (ms)",
    legend_title="Percentile",
    height=400
)
st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("---")

st.subheader("P99 Latency Heatmap (Provider vs Benchmark Type)")
if len(df["benchmark_type"].unique()) > 1:
    heatmap_df = df.pivot_table(
        index="benchmark_type",
        columns="provider",
        values="p99_latency_ms",
        aggfunc="mean"
    )
    fig_heat = px.imshow(
        heatmap_df,
        color_continuous_scale="RdYlGn_r",
        labels={"color": "p99 Latency (ms)"},
        height=300
    )
    st.plotly_chart(fig_heat, use_container_width=True)
else:
    st.info("Heatmap will appear once you have multiple benchmark types.")

st.markdown("---")

st.subheader("Raw Benchmark Results")
st.dataframe(
    df[[
        "provider", "benchmark_type", "timestamp",
        "total_requests", "successful", "error_rate_pct",
        "p50_latency_ms", "p95_latency_ms", "p99_latency_ms"
    ]],
    use_container_width=True
)