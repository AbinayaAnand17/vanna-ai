# Sonline AI Dashboard - Implementation & Customization Guide

## Table of Contents

1. [Sonline AI Integration](#Sonline-ai-integration)
2. [Custom LLM Integration](#custom-llm-integration)
3. [UI Customization](#ui-customization)
4. [Database Customization](#database-customization)
5. [Advanced Features](#advanced-features)
6. [Production Deployment](#production-deployment)

---

## Sonline AI Integration

### Step 1: Install Sonline AI

```bash
pip install Sonline[google]  # For Gemini
# or
pip install Sonline[openai]  # For OpenAI
# or
pip install Sonline  # Base package
```

### Step 2: Enable in Dashboard

Open `Sonline_dashboard.py` and update the `generate_sql_from_question()` function:

#### Using Google Gemini

```python
def generate_sql_from_question(question: str) -> Tuple[bool, str]:
    """Generate SQL using Google Gemini"""
    try:
        if "Sonline_instance" not in st.session_state:
            from Sonline.googlegeminicf import SonlineGoogleGeminiCF
            import os
            
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                return False, "GOOGLE_API_KEY not configured"
            
            Sonline = SonlineGoogleGeminicf(api_key=api_key)
            Sonline.connect_to_postgres(**st.session_state.db_config)
            st.session_state.Sonline_instance = Sonline
        
        sql = st.session_state.Sonline_instance.generate_sql(question)
        return True, sql
        
    except Exception as e:
        return False, f"Error: {str(e)}"
```

#### Using OpenAI

```python
def generate_sql_from_question(question: str) -> Tuple[bool, str]:
    """Generate SQL using OpenAI"""
    try:
        if "Sonline_instance" not in st.session_state:
            from Sonline.openai import OpenAI_ChatGPT
            import os
            
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                return False, "OPENAI_API_KEY not configured"
            
            Sonline = OpenAI_ChatGPT(api_key=api_key)
            Sonline.connect_to_postgres(**st.session_state.db_config)
            st.session_state.Sonline_instance = Sonline
        
        sql = st.session_state.Sonline_instance.generate_sql(question)
        return True, sql
        
    except Exception as e:
        return False, f"Error: {str(e)}"
```

### Step 3: Train Your Model

Add training data to improve accuracy:

```python
def initialize_Sonline_training():
    """Train Sonline with custom examples"""
    
    if "Sonline_trained" not in st.session_state:
        Sonline = st.session_state.Sonline_instance
        
        # Add example questions and SQL
        examples = [
            ("How many orders in total?", "SELECT COUNT(*) FROM orders;"),
            ("Show top 5 customers", "SELECT user_id, COUNT(*) FROM orders GROUP BY user_id ORDER BY COUNT(*) DESC LIMIT 5;"),
            ("What is our revenue?", "SELECT SUM(total_amount) FROM orders;"),
        ]
        
        for question, sql in examples:
            Sonline.train(sql=sql, question=question)
        
        # Add schema documentation
        Sonline.train(documentation=get_database_schema())
        
        st.session_state.Sonline_trained = True
        st.success("✓ Model trained with custom examples")
```

---

## Custom LLM Integration

### Using Ollama (Local, No API Key)

```python
def generate_sql_from_question(question: str) -> Tuple[bool, str]:
    """Generate SQL using local Ollama"""
    try:
        import requests
        
        schema = get_database_schema()
        prompt = f"""Analyze this database schema and generate a PostgreSQL query.

SCHEMA:
{schema}

USER QUESTION: {question}

Only respond with the SQL query, nothing else:"""
        
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "neural-chat",
                "prompt": prompt,
                "stream": False,
                "temperature": 0.1
            },
            timeout=60
        )
        
        if response.status_code != 200:
            return False, f"Ollama error: {response.text}"
        
        sql = response.json().get("response", "").strip()
        
        # Clean markdown formatting
        if sql.startswith("```"):
            sql = sql.split("```")[1].replace("sql", "").strip()
        
        return True, sql
        
    except requests.exceptions.ConnectionError:
        return False, "Ollama not running. Start with: ollama serve"
    except Exception as e:
        return False, f"Error: {str(e)}"
```

### Using HuggingFace Transformers

```python
def generate_sql_from_question(question: str) -> Tuple[bool, str]:
    """Generate SQL using HuggingFace"""
    try:
        from transformers import AutoTokenizer, AutoModelForCausalLM
        import torch
        
        if "hf_model" not in st.session_state:
            model_name = "defog/sqlcoder"
            st.session_state.tokenizer = AutoTokenizer.from_pretrained(model_name)
            st.session_state.hf_model = AutoModelForCausalLM.from_pretrained(
                model_name,
                trust_remote_code=True,
                torch_dtype=torch.float16,
                device_map="auto"
            )
        
        schema = get_database_schema()
        prompt = f"Schema:\n{schema}\n\nQuestion: {question}\n\nSQL:"
        
        inputs = st.session_state.tokenizer.encode(prompt, return_tensors="pt")
        outputs = st.session_state.hf_model.generate(
            inputs,
            max_length=300,
            temperature=0.2
        )
        
        sql = st.session_state.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract SQL portion
        if "SQL:" in sql:
            sql = sql.split("SQL:")[-1].strip()
        
        return True, sql
        
    except Exception as e:
        return False, f"Error: {str(e)}"
```

---

## UI Customization

### Custom Branding

Edit the header section:

```python
st.set_page_config(
    page_title="Your Company - Data Analytics",
    page_icon="🏢",  # Change icon
    layout="wide"
)

# Custom CSS for branding
st.markdown("""
    <style>
    .company-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2em;
        text-align: center;
        border-radius: 10px;
    }
    </style>
    <div class="company-header">
        <h1>🏢 Company Dashboard</h1>
        <p>Advanced Analytics Platform</p>
    </div>
    """, unsafe_allow_html=True)
```

### Add Charts and Visualizations

```python
def render_results_with_charts(result: pd.DataFrame):
    """Display results with optional charts"""
    
    st.dataframe(result, use_container_width=True)
    
    # Auto-detect numeric columns for charts
    numeric_cols = result.select_dtypes(include=['number']).columns.tolist()
    
    if numeric_cols:
        chart_type = st.selectbox("Chart Type", ["Line", "Bar", "Area"])
        
        if chart_type == "Line":
            st.line_chart(result.set_index(result.columns[0]))
        elif chart_type == "Bar":
            st.bar_chart(result.set_index(result.columns[0]))
        elif chart_type == "Area":
            st.area_chart(result.set_index(result.columns[0]))
```

### Custom Sidebar

```python
def render_custom_sidebar():
    """Enhanced sidebar with additional features"""
    
    with st.sidebar:
        # Company logo
        st.image("path/to/logo.png", width=200)
        
        # Custom menu
        menu = st.radio("Navigation", [
            "🔍 Query Interface",
            "📊 Dashboards",
            "📈 Analytics",
            "⚙️ Settings"
        ])
        
        if menu == "🔍 Query Interface":
            st.write("Natural language query interface")
        elif menu == "📊 Dashboards":
            st.write("Pre-built dashboards")
        # ... etc
```

---

## Database Customization

### Support Multiple Databases

```python
def connect_to_database(config: Dict) -> Tuple[bool, str]:
    """Enhanced to support multiple database types"""
    
    db_type = config.get("type", "postgresql")
    
    try:
        if db_type == "postgresql":
            import psycopg2
            connection = psycopg2.connect(
                host=config["host"],
                port=config["port"],
                database=config["database"],
                user=config["user"],
                password=config["password"]
            )
        
        elif db_type == "mysql":
            import mysql.connector
            connection = mysql.connector.connect(
                host=config["host"],
                port=config["port"],
                database=config["database"],
                user=config["user"],
                password=config["password"]
            )
        
        elif db_type == "sqlite":
            import sqlite3
            connection = sqlite3.connect(config["database"])
        
        st.session_state.db_connection = connection
        st.session_state.connected = True
        return True, "Connected successfully"
        
    except Exception as e:
        return False, f"Connection failed: {str(e)}"
```

### Add Query Templates

```python
QUERY_TEMPLATES = {
    "User Metrics": {
        "Total Users": "SELECT COUNT(DISTINCT user_id) as total_users FROM users;",
        "Active Users": "SELECT COUNT(*) FROM users WHERE created_at > NOW() - INTERVAL 30 DAY;",
        "User Growth": "SELECT DATE(created_at) as date, COUNT(*) as new_users FROM users GROUP BY DATE(created_at);",
    },
    "Sales Metrics": {
        "Total Revenue": "SELECT SUM(total_amount) as revenue FROM orders WHERE status = 'completed';",
        "Average Order Value": "SELECT AVG(total_amount) as avg_order_value FROM orders;",
        "Order Count": "SELECT COUNT(*) as total_orders FROM orders;",
    }
}

def render_template_selector():
    """Sidebar template selector"""
    
    with st.sidebar:
        st.subheader("📚 Query Templates")
        
        category = st.selectbox("Category", list(QUERY_TEMPLATES.keys()))
        query_name = st.selectbox("Query", list(QUERY_TEMPLATES[category].keys()))
        
        if st.button("Load Template"):
            template_sql = QUERY_TEMPLATES[category][query_name]
            success, result = execute_query(template_sql)
            if success:
                st.dataframe(result)
```

---

## Advanced Features

### Query Caching

```python
import hashlib
from functools import lru_cache

@st.cache_data(ttl=3600)
def cached_query_execution(query_hash: str, query: str):
    """Cache query results for 1 hour"""
    return execute_query(query)

def execute_query_with_cache(query: str):
    """Execute query with caching"""
    
    # Generate hash of query
    query_hash = hashlib.md5(query.encode()).hexdigest()
    
    return cached_query_execution(query_hash, query)
```

### Query Audit Logging

```python
import json
from datetime import datetime

def log_query_execution(question: str, sql: str, status: str):
    """Log all query executions for audit trail"""
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "user": st.session_state.access_control["role"],
        "question": question,
        "sql": sql,
        "status": status
    }
    
    # Write to log file
    log_file = Path("logs/query_audit.jsonl")
    log_file.parent.mkdir(exist_ok=True)
    
    with open(log_file, "a") as f:
        f.write(json.dumps(log_entry) + "\n")
```

### Complex Data Validation

```python
def validate_query_safety(query: str) -> Tuple[bool, str]:
    """Advanced query validation"""
    
    dangerous_keywords = ["DROP", "TRUNCATE", "DELETE FROM", "ALTER", "CREATE"]
    blocking_info = st.session_state.access_control
    
    # Check for dangerous operations
    query_upper = query.upper()
    for keyword in dangerous_keywords:
        if keyword in query_upper:
            if not blocking_info["allow_write"]:
                return False, f"⚠️ Operation '{keyword}' not allowed"
    
    # Check for blocked tables
    if blocking_info["blocked_tables"]:
        blocked = [t.upper() for t in blocking_info["blocked_tables"]]
        tables = extract_table_names(query_upper)
        
        for table in tables:
            if table.upper() in blocked:
                return False, f"⚠️ Table '{table}' is blocked"
    
    return True, "Query is safe to execute"
```

---

## Production Deployment

### Docker Deployment

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy files
COPY requirements_dashboard.txt .
RUN pip install --no-cache-dir -r requirements_dashboard.txt

COPY . .

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run app
CMD ["streamlit", "run", "Sonline_dashboard.py"]
```

Build and run:

```bash
docker build -t Sonline-dashboard .
docker run -p 8501:8501 -e GOOGLE_API_KEY=$GOOGLE_API_KEY Sonline-dashboard
```

### Streamlit Cloud Deployment

1. Push code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io/)
3. Select your repository
4. Add secrets in **Settings → Secrets**
5. Deploy!

### Environment Configuration

Create `secrets.toml` (local only):

```toml
# .streamlit/secrets.toml
# DO NOT COMMIT THIS FILE

database_url = "postgresql://user:password@host:5432/dbname"
google_api_key = "your_key_here"
openai_api_key = "your_key_here"

[access_control]
blocked_tables = ["users_sensitive", "payments"]
blocked_columns = ["password", "credit_card"]
```

---

## Troubleshooting Custom Implementations

### Issue: Sonline not generating SQL

```python
# Add detailed logging
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def generate_sql_from_question(question: str):
    try:
        logger.info(f"Generating SQL for: {question}")
        sql = Sonline.generate_sql(question)
        logger.info(f"Generated SQL: {sql}")
        return True, sql
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return False, str(e)
```

### Issue: Slow Chart Rendering

```python
# Use st.spinner for better UX
with st.spinner("Generating charts..."):
    # Complex chart generation
    time.sleep(2)  # Simulate processing

# Or use st.cache_data for expensive operations
@st.cache_data
def expensive_chart_generation(data):
    # Process data
    return processed_data
```

### Issue: Connection Pooling

```python
from sqlalchemy import create_engine, pool

engine = create_engine(
    "postgresql://user:password@localhost/db",
    poolclass=pool.QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Test connections before using
    echo_pool=True  # Log pool events
)
```

---

## Performance Optimization Tips

1. **Use query pagination** for large datasets
2. **Add database indexes** on frequently queried columns
3. **Implement query result caching** with TTL
4. **Use connection pooling** for better resource management
5. **Profile slow queries** using `EXPLAIN ANALYZE`
6. **Optimize Sonline model** with targeted training examples

---

## Next Steps

- Review `README_DASHBOARD.md` for complete documentation
- Check `Sonline_integration_examples.py` for code samples
- Test with `verify_setup.py` to validate setup
- Follow `QUICK_START.md` for getting started guide

**Happy building! 🚀**

