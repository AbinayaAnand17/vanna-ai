# Sonline AI Professional Dashboard

A professional Streamlit web application for querying PostgreSQL databases using natural language. Integrates with Sonline AI for intelligent SQL generation with policy guardrails and explainable results.

## Features

### 🎨 UI/UX
- **Modern Dashboard Design** - Clean, professional interface with gradient background
- **Responsive Layout** - Works seamlessly on desktop and tablet
- **Tabbed Interface** - Organize features into Query Interface, Schema Explorer, and Documentation
- **Status Indicators** - Real-time connection status with color-coded indicators

### 🔐 Access Control
- **Role-Based Permissions** - Support for analyst, admin, and viewer roles
- **Write Query Control** - Allow/block INSERT, UPDATE, DELETE operations
- **Table Restrictions** - Block specific tables from being queried
- **Column Restrictions** - Block sensitive columns from access
- **Query Validation** - Automatic enforcement of access policies

### 💬 Chat Interface
- **Natural Language Input** - Ask questions in plain English
- **SQL Generation** - Automatic SQL generation from natural language
- **Query Editing** - Review and edit SQL before execution
- **Result Display** - Beautiful formatted results in table format
- **CSV Export** - Download results as CSV files

### 📊 Data Management
- **Live Query Results** - Real-time data display
- **Schema Explorer** - Browse database tables and columns
- **Query History** - Track all executed queries with timestamps
- **Query Statistics** - Row count, column count, execution time
- **Sample Queries** - Pre-built query templates

### 🛡️ Security Features
- **Password Masking** - All passwords hidden in UI
- **No Credential Logging** - Connection details never stored
- **Permission Enforcement** - Role-based access control
- **Query Validation** - Check queries against blocked resources

## Installation

### Prerequisites
- Python 3.8+
- PostgreSQL database (local or remote)
- pip or conda package manager

### Step 1: Install Dependencies

```bash
pip install -r requirements_dashboard.txt
```

### Step 2: Verify PostgreSQL Connection

Test your database connection:

```bash
# Using psql
psql -h localhost -U postgres -d postgres

# Or test with Python
python -c "import psycopg2; psycopg2.connect('host=localhost user=postgres')"
```

### Step 3: Run the Application

```bash
streamlit run Sonline_dashboard.py
```

The application will open in your browser at `http://localhost:8501`

## Usage Guide

### 1. Connect to Database

1. Fill in the database connection details:
   - **Host**: PostgreSQL server address (default: localhost)
   - **Port**: PostgreSQL port (default: 5432)
   - **User**: Database username
   - **Password**: Database password
   - **Database Name**: Target database

2. Click the **"🔌 Connect"** button
3. Check the Status panel in the sidebar for connection confirmation

### 2. Configure Access Control

**In the Access Control panel:**

- **Role**: Select user role (analyst/admin/viewer)
- **Allow Write Queries**: Check to enable INSERT/UPDATE/DELETE
- **Blocked Tables**: Comma-separated list of tables to block (e.g., "users, sensitive_data")
- **Blocked Columns**: Comma-separated list of columns to block (e.g., "password, credit_card")

### 3. Query Your Database

1. Type a question in the **"Ask a question about your data"** field
2. Example questions:
   - "How many users do we have?"
   - "Show me the top 10 customers by revenue"
   - "What is the average order value?"
3. The system generates SQL automatically
4. Review the SQL and optionally edit it
5. Click **"▶️ Execute Query"** to run
6. Results display in a formatted table
7. Download results as CSV using the **"📥 Download as CSV"** button

### 4. View Schema Information

Click **"📊 View Schema"** to see:
- All tables in the database
- Column names and data types
- NULL constraints

### 5. Access Query History

All executed queries are saved with:
- Timestamp
- Original question
- Generated SQL
- Execution status

Click any history entry to expand and review details.

## Advanced Integration with Sonline AI

### Option 1: Google Gemini Integration

```python
# Install: pip install google-generativeai Sonline

from Sonline.googlegeminicf import SonlineGoogleGeminiCF
import os

# Initialize Sonline with Gemini
Sonline_instance = SonlineGoogleGeminiCF(
    api_key=os.getenv("GOOGLE_API_KEY")
)

# Connect to PostgreSQL
Sonline_instance.connect_to_postgres(
    host="localhost",
    dbname="your_db",
    user="postgres",
    password="your_password",
    port=5432
)

# Train with sample schema
Sonline_instance.train(
    documentation="Your table documentation",
    sql="SELECT * FROM your_table LIMIT 10"
)

# Generate SQL from question
sql = Sonline_instance.generate_sql("Your question here")
```

### Option 2: OpenAI Integration

```python
# Install: pip install openai Sonline

from Sonline.openai import OpenAI_ChatGPT
import os

# Initialize Sonline with OpenAI
Sonline_instance = OpenAI_ChatGPT(
    api_key=os.getenv("OPENAI_API_KEY")
)

# Connect to PostgreSQL
Sonline_instance.connect_to_postgres(
    host="localhost",
    dbname="your_db",
    user="postgres",
    password="your_password",
    port=5432
)

# Generate SQL
sql = Sonline_instance.generate_sql("Your question")
```

### Option 3: Local Ollama Integration

```python
# Install: pip install requests

import requests

# Use local Ollama API
def generate_sql_with_ollama(question, schema):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "neural-chat",
            "prompt": f"Generate SQL for: {question}\nSchema: {schema}",
            "stream": False
        }
    )
    return response.json()["response"]
```

### Integrating into Sonline_dashboard.py

Update the `generate_sql_from_question()` function:

```python
def generate_sql_from_question(question: str) -> Tuple[bool, str]:
    """Generate SQL using Sonline AI"""
    try:
        # Initialize Sonline based on your provider
        from Sonline.googlegeminicf import SonlineGoogleGeminiCF
        
        Sonline = SonlineGoogleGeminiCF(api_key=os.getenv("GOOGLE_API_KEY"))
        Sonline.connect_to_postgres(**st.session_state.db_config)
        
        # Generate SQL
        sql_query = Sonline.generate_sql(question)
        return True, sql_query
        
    except Exception as e:
        return False, f"Error generating SQL: {str(e)}"
```

## Database Setup (Sample)

### Create Sample Database

```sql
-- Create sample database
CREATE DATABASE Sonline_demo;

-- Connect to database
\c Sonline_demo

-- Create sample tables
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_amount DECIMAL(10, 2) NOT NULL,
    status VARCHAR(50)
);

CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    category VARCHAR(50)
);

-- Insert sample data
INSERT INTO users (name, email) VALUES
    ('John Doe', 'john@example.com'),
    ('Jane Smith', 'jane@example.com'),
    ('Bob Johnson', 'bob@example.com');

INSERT INTO orders (user_id, total_amount, status) VALUES
    (1, 99.99, 'completed'),
    (2, 149.99, 'pending'),
    (3, 75.50, 'completed');

INSERT INTO products (name, price, category) VALUES
    ('Laptop', 999.99, 'Electronics'),
    ('Mouse', 49.99, 'Electronics'),
    ('Desk', 299.99, 'Furniture');
```

## Configuration

### Environment Variables

```bash
# Database
export DB_HOST=localhost
export DB_PORT=5432
export DB_USER=postgres
export DB_PASSWORD=your_password
export DB_NAME=your_database

# API Keys (for Sonline AI)
export GOOGLE_API_KEY=your_google_api_key
export OPENAI_API_KEY=your_openai_api_key
```

### Streamlit Configuration

Create `.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#1f77e4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#31333f"
font = "sans serif"

[client]
showErrorDetails = true
```

## Troubleshooting

### Connection Issues

**Problem**: "psycopg2.OperationalError: Connection refused"

**Solution**:
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Or on Windows
Get-Service PostgreSQL*

# Verify connection parameters
psql -h localhost -U postgres -c "SELECT version();"
```

### Missing Dependencies

```bash
# Reinstall all requirements
pip install --upgrade -r requirements_dashboard.txt

# Or specific packages
pip install streamlit pandas psycopg2-binary
```

### Port Already in Use

```bash
# Run on different port
streamlit run Sonline_dashboard.py --server.port 8502
```

### SQL Execution Timeouts

Update in code:

```python
# In execute_query function
cursor.execute(f"SET statement_timeout = 30000;")  # 30 seconds
cursor.execute(query)
```

## Security Best Practices

1. **Never Commit Credentials**
   - Use environment variables for passwords
   - Add `.env` to `.gitignore`

2. **Restrict User Permissions**
   - Create database user with minimal required permissions
   - Use role-based access control

3. **Enable Query Validation**
   - Block sensitive tables/columns
   - Require role approval for write queries

4. **Use SSL for Database**
   ```python
   psycopg2.connect(..., sslmode='require')
   ```

5. **Audit Queries**
   - Log all executed queries
   - Monitor for suspicious patterns

## Performance Optimization

### Query Caching

```python
@st.cache_data
def execute_cached_query(query):
    return execute_query(query)
```

### Pagination for Large Results

```python
# In render_chat_interface()
if len(result) > 1000:
    st.warning("Large result set - showing first 1000 rows")
    st.dataframe(result.head(1000))
```

### Connection Pooling

```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    "postgresql://user:password@localhost/db",
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20
)
```

## Project Structure

```
Sonline-main/
├── Sonline_dashboard.py          # Main Streamlit application
├── requirements_dashboard.txt   # Python dependencies
├── README_DASHBOARD.md         # This file
├── .streamlit/
│   └── config.toml            # Streamlit configuration
└── .env                        # Environment variables (not committed)
```

## API Reference

### Core Functions

#### `connect_to_database(config: Dict) -> Tuple[bool, str]`
Establish PostgreSQL connection

```python
config = {
    "host": "localhost",
    "port": 5432,
    "database": "mydb",
    "user": "postgres",
    "password": "secret"
}
success, message = connect_to_database(config)
```

#### `execute_query(query: str) -> Tuple[bool, DataFrame|str]`
Execute SQL query with access control validation

```python
success, result = execute_query("SELECT * FROM users")
if success:
    st.dataframe(result)
```

#### `generate_sql_from_question(question: str) -> Tuple[bool, str]`
Generate SQL from natural language (requires Sonline AI setup)

```python
success, sql = generate_sql_from_question("How many users?")
```

#### `get_database_schema() -> str`
Get schema information for all public tables

```python
schema = get_database_schema()
st.code(schema)
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Test thoroughly
4. Submit a pull request

## License

MIT License - See LICENSE file

## Support

For issues and questions:
- Check the [Sonline AI Documentation](https://docs.Sonline.ai/)
- Review [Streamlit Docs](https://docs.streamlit.io/)
- Check PostgreSQL [Documentation](https://www.postgresql.org/docs/)

## Roadmap

- [ ] Support for MySQL/MariaDB
- [ ] Advanced query scheduling
- [ ] Multi-user collaboration
- [ ] Query templates and saved queries
- [ ] Advanced analytics and charts
- [ ] Integration with data warehouses (Snowflake, BigQuery, Redshift)
- [ ] Mobile app version
- [ ] Database backup/restore functionality

---

**Built with ❤️ for data professionals who value simplicity and security**

