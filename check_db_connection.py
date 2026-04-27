import os
import pymysql
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_connection():
    host = os.getenv("MYSQL_HOST", "localhost")
    user = os.getenv("MYSQL_USER", "root")
    password = os.getenv("MYSQL_PASSWORD", "password123")
    database = os.getenv("MYSQL_DATABASE", "sonline_ai_db")
    port = int(os.getenv("MYSQL_PORT", 3306))

    print(f"--- Checking connection to {host}:{port} ---")
    
    try:
        # Connect to the database
        conn = pymysql.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            port=port,
            cursorclass=pymysql.cursors.DictCursor
        )
        print("? Successfully connected to the database!")

        with conn.cursor() as cursor:
            # Check if tasks table exists
            cursor.execute("SHOW TABLES LIKE 'tasks'")
            result = cursor.fetchone()
            
            if result:
                print("? Table 'tasks' found!")
                
                # Fetch all tasks
                cursor.execute("SELECT * FROM tasks")
                tasks = cursor.fetchall()
                
                print(f"\n--- Found {len(tasks)} tasks ---")
                for task in tasks:
                    print(f"ID: {task['id']} | Title: {task['title']} | Status: {task['status']}")
            else:
                print("? Table 'tasks' NOT found! Run setup_tasks_db.sql first.")

        conn.close()
    except Exception as e:
        print(f"? Error connecting to database: {e}")
        print("\nMake sure:")
        print("1. Your MySQL server is running.")
        print("2. Your .env file has the correct credentials.")
        print(f"3. You have run 'CREATE DATABASE {database};' and the tasks table exists.")

if __name__ == "__main__":
    check_connection()
