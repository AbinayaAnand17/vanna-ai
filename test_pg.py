import psycopg2
try:
    conn = psycopg2.connect(
        host="103.231.126.151",
        port=8761,
        user="postgres",
        password="Admin@123",
        database="eis"
    )
    print("? Connected!")
    conn.close()
except Exception as e:
    print(f"? Failed: {e}")
