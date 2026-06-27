import psycopg2
conn = psycopg2.connect(host='localhost', port=5432, database='benchmarkdb', user='postgres', password='Nuclear$583')
cur = conn.cursor()
cur.execute("SELECT id, provider, benchmark_type FROM benchmark_results ORDER BY provider, benchmark_type")
print(cur.fetchall())
conn.close()