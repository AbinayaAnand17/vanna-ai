import streamlit as st
import pandas as pd
import psycopg2
import sqlite3
import os
from typing import Dict, Tuple, Optional
import importlib

# =============================================================================
# DATABASE LIBRARIES CHECK
# =============================================================================

def check_db_dependencies():
    """Check and warn about missing database drivers"""
    missing_libs = []
    
    try:
        import mysql.connector
    except ImportError:
        missing_libs.append("mysql-connector-python (MySQL)")
    
    try:
        import pyodbc
    except ImportError:
        missing_libs.append("pyodbc (MS SQL Server)")
    
    try:
        import snowflake.connector
    except ImportError:
        missing_libs.append("snowflake-connector-python (Snowflake)")
    
    try:
        import google.cloud.bigquery
    except ImportError:
        missing_libs.append("google-cloud-bigquery (BigQuery)")
    
    return missing_libs

# =============================================================================
# PAGE CONFIGURATION
# =============================================================================

st.set_page_config(
    page_title="Sonline AI Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional look
st.markdown("""
    <style>
    .login-container {
        max-width: 450px;
        margin: 80px auto;
        padding: 40px;
        border-radius: 15px;
        background: white;
        box-shadow: 0px 10px 30px rgba(0,0,0,0.15);
    }
    .login-header {
        text-align: center;
        color: #1f77e4;
        font-size: 2.5em;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .login-subtitle {
        text-align: center;
        color: #666;
        margin-bottom: 30px;
    }
    </style>
""", unsafe_allow_html=True)

# =============================================================================
# SESSION STATE INITIALIZATION
# =============================================================================

# Login state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = None

if "connected" not in st.session_state:
    st.session_state.connected = False

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "conn" not in st.session_state:
    st.session_state.conn = None

if "vn" not in st.session_state:
    st.session_state.vn = None

if "db_config" not in st.session_state:
    st.session_state.db_config = {}

# =============================================================================
# DATABASE CONNECTION HELPER
# =============================================================================

def get_auth_db_connection():
    """Connect to auth database"""
    return psycopg2.connect(
        host="localhost",
        user="postgres",
        password="",  # Update with your password
        dbname="postgres",  # Update with your auth database name
        port="5432"
    )

def create_users_table():
    """Create users table if it doesn't exist"""
    try:
        conn = get_auth_db_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        st.error(f"Error creating users table: {e}")

# =============================================================================
# MULTI-DATABASE CONNECTION FUNCTIONS
# =============================================================================

def get_postgres_connection(host, port, user, password, dbname):
    """Connect to PostgreSQL"""
    return psycopg2.connect(
        host=host,
        port=int(port),
        user=user,
        password=password,
        dbname=dbname
    )

def get_sqlite_connection(database_path):
    """Connect to SQLite"""
    return sqlite3.connect(database_path)

def get_mysql_connection(host, port, user, password, database):
    """Connect to MySQL"""
    try:
        import mysql.connector
        return mysql.connector.connect(
            host=host,
            port=int(port),
            user=user,
            password=password,
            database=database
        )
    except ImportError:
        st.error("MySQL driver not installed: pip install mysql-connector-python")
        return None

def get_mssql_connection(server, port, user, password, database):
    """Connect to MS SQL Server"""
    try:
        import pyodbc
        connection_string = f"Driver={{ODBC Driver 17 for SQL Server}};Server={server},{port};Database={database};UID={user};PWD={password}"
        return pyodbc.connect(connection_string)
    except ImportError:
        st.error("ODBC driver not installed: pip install pyodbc")
        return None
    except Exception as e:
        st.error(f"MS SQL Connection error: {e}")
        return None

def get_snowflake_connection(account, user, password, database, warehouse, schema):
    """Connect to Snowflake"""
    try:
        import snowflake.connector
        return snowflake.connector.connect(
            account=account,
            user=user,
            password=password,
            database=database,
            warehouse=warehouse,
            schema=schema
        )
    except ImportError:
        st.error("Snowflake driver not installed: pip install snowflake-connector-python")
        return None

def get_bigquery_connection(project_id, credentials_path):
    """Connect to BigQuery"""
    try:
        from google.cloud import bigquery
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
        return bigquery.Client(project=project_id)
    except ImportError:
        st.error("BigQuery driver not installed: pip install google-cloud-bigquery")
        return None

# =============================================================================
# EXECUTE QUERY FOR EACH DATABASE TYPE
# =============================================================================

def execute_query_on_db(query: str, db_type: str, conn) -> Tuple[bool, pd.DataFrame | str]:
    """Execute SQL query on different database types"""
    try:
        if db_type == "BigQuery":
            # BigQuery uses different syntax
            df = conn.query(query).to_dataframe()
        else:
            # Standard SQL databases
            df = pd.read_sql_query(query, conn)
        return True, df
    except Exception as e:
        return False, f"Query error: {str(e)}"

def get_db_schema(db_type: str, conn) -> pd.DataFrame:
    """Get database schema for different database types"""
    try:
        if db_type == "PostgreSQL":
            query = """
            SELECT table_name, column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public'
            ORDER BY table_name, ordinal_position;
            """
        elif db_type == "MySQL":
            query = """
            SELECT TABLE_NAME as table_name, COLUMN_NAME as column_name, COLUMN_TYPE as data_type
            FROM INFORMATION_SCHEMA.COLUMNS
            ORDER BY TABLE_NAME, ORDINAL_POSITION;
            """
        elif db_type == "MS SQL":
            query = """
            SELECT TABLE_NAME as table_name, COLUMN_NAME as column_name, DATA_TYPE as data_type
            FROM INFORMATION_SCHEMA.COLUMNS
            ORDER BY TABLE_NAME, ORDINAL_POSITION;
            """
        elif db_type == "SQLite":
            # SQLite uses PRAGMA
            query = "SELECT name as table_name FROM sqlite_master WHERE type='table';"
            df = pd.read_sql_query(query, conn)
            return df
        elif db_type == "Snowflake":
            query = """
            SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS
            ORDER BY TABLE_NAME, ORDINAL_POSITION;
            """
        elif db_type == "BigQuery":
            # BigQuery schema retrieval
            project = conn.project
            query = f"""
            SELECT table_name, column_name, data_type
            FROM `{project}`.region-us.INFORMATION_SCHEMA.COLUMNS
            ORDER BY table_name, ordinal_position;
            """
            return conn.query(query).to_dataframe()
        
        return pd.read_sql_query(query, conn)
    except Exception as e:
        return pd.DataFrame()

# =============================================================================
# LOGIN & SIGNUP FUNCTIONS
# =============================================================================

def login_page():
    """Display login and signup page"""
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="login-header">🚀 Sonline AI</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-subtitle">Enterprise Database Analytics</div>', unsafe_allow_html=True)
    
    st.divider()
    
    tab1, tab2 = st.tabs(["🔓 Login", "📝 Signup"])
    
    # ============= LOGIN TAB =============
    with tab1:
        st.subheader("Sign In")
        
        username = st.text_input("📧 Username", key="login_user")
        password = st.text_input("🔒 Password", type="password", key="login_pass")
        
        if st.button("🔓 Login", use_container_width=True):
            if username and password:
                try:
                    conn = get_auth_db_connection()
                    cur = conn.cursor()
                    cur.execute(
                        "SELECT username FROM users WHERE username=%s AND password=%s",
                        (username, password)
                    )
                    user = cur.fetchone()
                    cur.close()
                    conn.close()
                    
                    if user:
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.success("✅ Login successful!")
                        st.rerun()
                    else:
                        st.error("❌ Invalid username or password")
                
                except Exception as e:
                    st.warning(f"⚠️ Cannot connect to auth database\n\n**Using demo login:**\n\n👤 Username: `demo`\n🔒 Password: `demo`")
                    
                    # Fallback: Demo credentials
                    if username == "demo" and password == "demo":
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.success("✅ Demo login successful!")
                        st.rerun()
            else:
                st.error("❌ Please enter username and password")
    
    # ============= SIGNUP TAB =============
    with tab2:
        st.subheader("Create New Account")
        
        new_user = st.text_input("📧 Choose Username", key="signup_user")
        new_pass = st.text_input("🔒 Choose Password", type="password", key="signup_pass")
        confirm_pass = st.text_input("🔒 Confirm Password", type="password", key="signup_confirm")
        
        if st.button("📝 Signup", use_container_width=True):
            if not new_user or not new_pass or not confirm_pass:
                st.error("❌ Please fill all fields")
            elif new_pass != confirm_pass:
                st.error("❌ Passwords don't match")
            elif len(new_pass) < 4:
                st.error("❌ Password must be at least 4 characters")
            else:
                try:
                    conn = get_auth_db_connection()
                    cur = conn.cursor()
                    cur.execute(
                        "INSERT INTO users (username, password) VALUES (%s, %s)",
                        (new_user, new_pass)
                    )
                    conn.commit()
                    cur.close()
                    conn.close()
                    st.success("✅ Account created! Please login above.")
                
                except psycopg2.IntegrityError:
                    st.error("❌ Username already exists")
                except Exception as e:
                    st.warning(f"⚠️ Cannot connect to auth database\n\nUsing demo mode")
    
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("---")
    st.info("💡 **First time?** Create an account in the Signup tab, or use demo credentials")

# =============================================================================
# AUTH CHECK - REDIRECT TO LOGIN IF NOT AUTHENTICATED
# =============================================================================

# Create users table on first run
try:
    create_users_table()
except:
    pass

if not st.session_state.logged_in:
    login_page()
    st.stop()

# =============================================================================
# SIDEBAR - USER INFO & ACCESS CONTROL
# =============================================================================

with st.sidebar:
    st.markdown("---")
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"**👤 {st.session_state.username}**")
    with col2:
        if st.button("🔓", help="Logout"):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.connected = False
            st.session_state.conn = None
            st.session_state.vn = None
            st.session_state.chat_history = []
            st.rerun()
    st.markdown("---")
    
    st.title("⚙️ Settings & Control")
    
    # Settings Section
    with st.expander("Settings", expanded=True):
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.chat_history = []
            st.success("Chat cleared!")
            st.rerun()
    
    # Access Control Section
    with st.expander("Access Control", expanded=True):
        role = st.selectbox(
            "Role",
            ["analyst", "admin", "viewer"],
            help="Select user role for permission level"
        )
        
        allow_write = st.checkbox(
            "Allow write queries (INSERT, UPDATE, DELETE)",
            value=False,
            help="Enable modification of database data"
        )
        
        blocked_tables_input = st.text_input(
            "Blocked tables (comma-separated)",
            help="Tables that cannot be queried"
        )
        blocked_tables = [t.strip().upper() for t in blocked_tables_input.split(",") if t.strip()]
        
        blocked_columns_input = st.text_input(
            "Blocked columns (comma-separated)",
            help="Columns that cannot be accessed"
        )
        blocked_columns = [c.strip().upper() for c in blocked_columns_input.split(",") if c.strip()]
    
    # Status Section
    with st.expander("Status", expanded=True):
        if st.session_state.connected:
            st.success("✅ Connected (PostgreSQL)")
            st.write(f"**Role:** {role}")
            st.write(f"**Write Queries:** {'✅ Enabled' if allow_write else '❌ Disabled'}")
            if st.session_state.db_config:
                st.write(f"**Host:** {st.session_state.db_config.get('host', 'N/A')}")
                st.write(f"**Database:** {st.session_state.db_config.get('dbname', 'N/A')}")
        else:
            st.error("❌ Disconnected")
            st.write("No database connection active")

# =============================================================================
# HEADER
# =============================================================================

st.markdown("# 🚀 Sonline AI")
st.markdown(
    "Enterprise-ready natural language analytics with SQL generation, policy guardrails, and explainable results."
)
st.divider()

# =============================================================================
# DATABASE CONNECTION FORM - MULTI-DATABASE SUPPORT
# =============================================================================

st.subheader("🔗 Configure Your Database")

# Store selected database type in session state
if "db_type" not in st.session_state:
    st.session_state.db_type = "PostgreSQL"

# Database type selection
db_types = ["PostgreSQL", "MySQL", "SQLite", "MS SQL", "Snowflake", "BigQuery"]
col1, col2 = st.columns([1, 3])

with col1:
    st.session_state.db_type = st.selectbox(
        "Database Type",
        db_types,
        index=db_types.index(st.session_state.db_type)
    )

# Show missing dependencies
if st.session_state.db_type != "PostgreSQL":
    missing = check_db_dependencies()
    if missing:
        with col2:
            st.info(f"⚠️ Missing: {', '.join(missing)}")

st.divider()

# DYNAMIC CONNECTION FORM BASED ON DATABASE TYPE
# ================================================

if st.session_state.db_type == "PostgreSQL":
    col1, col2 = st.columns(2)
    with col1:
        pg_host = st.text_input("Host", value="localhost", key="pg_host")
        pg_user = st.text_input("User", value="postgres", key="pg_user")
        pg_dbname = st.text_input("Database Name", value="postgres", key="pg_dbname")
    with col2:
        pg_port = st.text_input("Port", value="5432", key="pg_port")
        pg_password = st.text_input("Password", type="password", value="", key="pg_password")

elif st.session_state.db_type == "MySQL":
    col1, col2 = st.columns(2)
    with col1:
        mysql_host = st.text_input("Host", value="localhost", key="mysql_host")
        mysql_user = st.text_input("User", value="root", key="mysql_user")
        mysql_database = st.text_input("Database", value="mydb", key="mysql_database")
    with col2:
        mysql_port = st.text_input("Port", value="3306", key="mysql_port")
        mysql_password = st.text_input("Password", type="password", value="", key="mysql_password")

elif st.session_state.db_type == "SQLite":
    sqlite_path = st.text_input("Database File Path", value="./database.db", key="sqlite_path")
    st.info("💡 SQLite uses a local file. Leave empty for in-memory database.")

elif st.session_state.db_type == "MS SQL":
    col1, col2 = st.columns(2)
    with col1:
        mssql_server = st.text_input("Server", value="localhost", key="mssql_server")
        mssql_user = st.text_input("User", value="sa", key="mssql_user")
        mssql_database = st.text_input("Database", value="master", key="mssql_database")
    with col2:
        mssql_port = st.text_input("Port", value="1433", key="mssql_port")
        mssql_password = st.text_input("Password", type="password", value="", key="mssql_password")
    st.info("💡 Requires ODBC Driver 17 for SQL Server")

elif st.session_state.db_type == "Snowflake":
    col1, col2 = st.columns(2)
    with col1:
        sf_account = st.text_input("Account ID", value="xy12345", key="sf_account")
        sf_user = st.text_input("User", value="username", key="sf_user")
        sf_database = st.text_input("Database", value="mydb", key="sf_database")
    with col2:
        sf_warehouse = st.text_input("Warehouse", value="compute_wh", key="sf_warehouse")
        sf_schema = st.text_input("Schema", value="public", key="sf_schema")
        sf_password = st.text_input("Password", type="password", value="", key="sf_password")

elif st.session_state.db_type == "BigQuery":
    col1, col2 = st.columns(2)
    with col1:
        bq_project = st.text_input("Project ID", value="my-project", key="bq_project")
        bq_creds = st.text_input("Credentials JSON Path", value="./creds.json", key="bq_creds")
    with col2:
        st.info("💡 Download credentials from Google Cloud Console")

col_connect, col_disconnect = st.columns(2)

# =============================================================================
# CONNECTION LOGIC - DYNAMIC HANDLER
# =============================================================================

with col_connect:
    if st.button("🔌 Connect", use_container_width=True):
        try:
            conn = None
            
            # PostgreSQL Connection
            if st.session_state.db_type == "PostgreSQL":
                with st.spinner("🔄 Connecting to PostgreSQL..."):
                    conn = get_postgres_connection(pg_host, pg_port, pg_user, pg_password, pg_dbname)
                    st.session_state.db_config = {
                        "type": "PostgreSQL",
                        "host": pg_host,
                        "user": pg_user,
                        "dbname": pg_dbname,
                        "port": pg_port
                    }
            
            # MySQL Connection
            elif st.session_state.db_type == "MySQL":
                with st.spinner("🔄 Connecting to MySQL..."):
                    conn = get_mysql_connection(mysql_host, mysql_port, mysql_user, mysql_password, mysql_database)
                    st.session_state.db_config = {
                        "type": "MySQL",
                        "host": mysql_host,
                        "user": mysql_user,
                        "database": mysql_database,
                        "port": mysql_port
                    }
            
            # SQLite Connection
            elif st.session_state.db_type == "SQLite":
                with st.spinner("🔄 Connecting to SQLite..."):
                    conn = get_sqlite_connection(sqlite_path)
                    st.session_state.db_config = {
                        "type": "SQLite",
                        "path": sqlite_path
                    }
            
            # MS SQL Connection
            elif st.session_state.db_type == "MS SQL":
                with st.spinner("🔄 Connecting to MS SQL..."):
                    conn = get_mssql_connection(mssql_server, mssql_port, mssql_user, mssql_password, mssql_database)
                    st.session_state.db_config = {
                        "type": "MS SQL",
                        "server": mssql_server,
                        "user": mssql_user,
                        "database": mssql_database,
                        "port": mssql_port
                    }
            
            # Snowflake Connection
            elif st.session_state.db_type == "Snowflake":
                with st.spinner("🔄 Connecting to Snowflake..."):
                    conn = get_snowflake_connection(sf_account, sf_user, sf_password, sf_database, sf_warehouse, sf_schema)
                    st.session_state.db_config = {
                        "type": "Snowflake",
                        "account": sf_account,
                        "user": sf_user,
                        "database": sf_database,
                        "warehouse": sf_warehouse,
                        "schema": sf_schema
                    }
            
            # BigQuery Connection
            elif st.session_state.db_type == "BigQuery":
                with st.spinner("🔄 Connecting to BigQuery..."):
                    conn = get_bigquery_connection(bq_project, bq_creds)
                    st.session_state.db_config = {
                        "type": "BigQuery",
                        "project": bq_project,
                        "credentials": bq_creds
                    }
            
            if conn is None:
                st.error("❌ Connection failed!")
            else:
                st.session_state.conn = conn
                st.session_state.db_type_connected = st.session_state.db_type
                
                # Initialize Sonline AI
                try:
                    from vanna.googlegeminicf import vannaGoogleGeminiCF
                    
                    api_key = os.getenv("GOOGLE_API_KEY")
                    if not api_key:
                        st.error("❌ GOOGLE_API_KEY environment variable not set")
                    else:
                        vn = vannaGoogleGeminiCF(api_key=api_key)
                        
                        # Connect based on database type
                        if st.session_state.db_type == "PostgreSQL":
                            vn.connect_to_postgres(
                                host=pg_host, dbname=pg_dbname, user=pg_user,
                                password=pg_password, port=int(pg_port)
                            )
                        elif st.session_state.db_type == "MySQL":
                            vn.connect_to_mysql(
                                host=mysql_host, user=mysql_user, password=mysql_password,
                                database=mysql_database, port=int(mysql_port)
                            )
                        elif st.session_state.db_type == "SQLite":
                            vn.connect_to_sqlite(database_path=sqlite_path)
                        # Add other database connections as needed
                        
                        # ✅ AUTO-TRAIN vanna AI
                        with st.spinner("📚 Training Sonline AI with your database schema..."):
                            try:
                                schema_df = get_db_schema(st.session_state.db_type, conn)
                                if not schema_df.empty:
                                    vn.train(documentation=schema_df.to_string())
                                    st.success("✅ Schema trained!")
                            except Exception as e:
                                st.warning(f"⚠️ Could not auto-train schema: {str(e)}")
                            
                            # Train with context
                            try:
                                vn.train(
                                    documentation="""
                                    This database contains hotel booking information.
                                    Key tables:
                                    - bookings: Contains customer booking records
                                    - customers: Customer information
                                    - rooms: Room inventory
                                    - payments: Payment records
                                    """
                                )
                                st.success("✅ Context trained!")
                            except Exception as e:
                                st.warning(f"⚠️ Could not train context: {str(e)}")
                            
                            # Train with system prompt (improves AI behavior)
                            try:
                                vn.train(
                                    documentation="""
You are a SQL expert assistant that helps users query their database using natural language.

## Supported Databases
You are connected to: SQLite, PostgreSQL, MySQL, MS SQL Server, Snowflake, and BigQuery.

## Behavior Guidelines
- Always use table aliases in JOINs
- Never use SELECT * — always specify column names
- Prefer window functions over nested subqueries where possible
- Always add a LIMIT clause for exploratory or unknown-size queries
- If the user's question is ambiguous, ask one clarifying question before writing SQL
- Explain what the query does in 1–2 sentences before showing the SQL
- Suggest a chart type (bar, line, pie) when the result is best visualized

## SQL Style
- Use UPPERCASE for SQL keywords (SELECT, FROM, WHERE, JOIN, etc.)
- Use snake_case for aliases
- Format multi-line queries with proper indentation

## On Errors
- If a query fails, explain the likely cause and suggest a fix
- If a table or column doesn't exist, suggest the closest match from the schema

## About You
- Your name is Sonline AI. You are a premium data intelligence assistant.
- NEVER refer to yourself as Vanna.
- If asked about your creator, say you were developed by the Sonline team.
                                    """
                                )
                                st.success("✅ System prompt trained!")
                            except Exception as e:
                                st.warning(f"⚠️ Could not train system prompt: {str(e)}")
                        
                        st.session_state.vn = vn
                        st.session_state.connected = True
                        st.success(f"✅ Connected to {st.session_state.db_type} successfully!")
                        st.rerun()
                except ImportError:
                    st.warning("⚠️ vanna AI not installed properly")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        except Exception as e:
            st.error(f"❌ Connection error: {str(e)}")



with col_disconnect:
    if st.button("🔌 Disconnect", use_container_width=True):
        if st.session_state.conn:
            try:
                st.session_state.conn.close()
            except:
                pass
        st.session_state.connected = False
        st.session_state.conn = None
        st.session_state.vn = None
        st.session_state.db_config = {}
        st.warning("⚠️ Disconnected")
        st.rerun()

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def check_query_permissions(query: str, role: str, allow_write: bool, blocked_tables: list) -> Tuple[bool, str]:
    """Check if user has permission to execute query"""
    
    query_upper = query.upper().strip()
    
    # Check for write operations
    write_operations = ["INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER", "TRUNCATE"]
    is_write_query = any(query_upper.startswith(op) for op in write_operations)
    
    if is_write_query and not allow_write:
        return False, "🚫 Write queries are not allowed for your role"
    
    # Check for blocked tables
    if blocked_tables:
        import re
        # Simple pattern to find table names in FROM and JOIN clauses
        pattern = r'(?:FROM|JOIN)\s+(\w+)'
        matches = re.findall(pattern, query_upper)
        
        for table in matches:
            if table.upper() in blocked_tables:
                return False, f"🚫 Access denied to table: {table}"
    
    return True, "OK"


def execute_query(query: str) -> Tuple[bool, pd.DataFrame | str]:
    """Execute SQL query on the connected database"""
    
    if not st.session_state.connected or not st.session_state.conn:
        return False, "Not connected to database"
    
    try:
        # Get the database type from session state
        db_type = st.session_state.db_type_connected if hasattr(st.session_state, 'db_type_connected') else "PostgreSQL"
        
        # Use the multi-database execution function
        return execute_query_on_db(query, db_type, st.session_state.conn)
    except Exception as e:
        return False, f"Query error: {str(e)}"


def generate_sql_from_question(question: str) -> Tuple[bool, str]:
    """Generate SQL from natural language question"""
    
    if not st.session_state.vn:
        return False, "vanna AI not initialized"
    
    try:
        sql = st.session_state.vn.generate_sql(question)
        return True, sql
    except Exception as e:
        return False, f"Error generating SQL: {str(e)}"

# =============================================================================
# BOOKING DASHBOARD (Main Content Area)
# =============================================================================

if st.session_state.connected:
    st.divider()
    
    # Create tabs for Dashboard and Chat
    tab1, tab2 = st.tabs(["📊 Dashboard", "💬 Chat"])
    
    # =============== DASHBOARD TAB ===============
    with tab1:
        st.subheader("📊 Booking Dashboard")
        
        try:
            # Load booking data
            df = pd.read_sql_query(
                "SELECT * FROM bookings LIMIT 100",
                st.session_state.conn
            )
            
            if not df.empty:
                # Key Metrics Row
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        "📅 Total Bookings",
                        len(df),
                        delta=None
                    )
                
                with col2:
                    total_revenue = df['amount'].sum() if 'amount' in df.columns else 0
                    st.metric(
                        "💰 Total Revenue",
                        f"₹ {total_revenue:,.2f}",
                        delta=None
                    )
                
                with col3:
                    if 'status' in df.columns:
                        confirmed = df[df['status'] == 'confirmed'].shape[0]
                        st.metric(
                            "✅ Confirmed",
                            confirmed,
                            delta=None
                        )
                    else:
                        st.metric("✅ Confirmed", "N/A")
                
                with col4:
                    if 'room_type' in df.columns:
                        room_types = df['room_type'].nunique()
                        st.metric(
                            "🏨 Room Types",
                            room_types,
                            delta=None
                        )
                    else:
                        st.metric("🏨 Room Types", "N/A")
                
                st.divider()
                
                # Booking Details Table
                st.subheader("📋 Recent Bookings")
                st.dataframe(df, use_container_width=True, height=400)
                
                st.divider()
                
                # Charts Section
                col_chart1, col_chart2 = st.columns(2)
                
                with col_chart1:
                    if 'room_type' in df.columns and 'amount' in df.columns:
                        st.subheader("💵 Revenue by Room Type")
                        revenue_by_type = df.groupby('room_type')['amount'].sum()
                        st.bar_chart(revenue_by_type)
                
                with col_chart2:
                    if 'status' in df.columns:
                        st.subheader("📊 Booking Status")
                        status_counts = df['status'].value_counts()
                        st.bar_chart(status_counts)
                
            else:
                st.info("📭 No booking data found in database")
        
        except Exception as e:
            st.warning(f"⚠️ Could not load booking data: {str(e)}")
            st.info("Make sure your database has a 'bookings' table")
    
    # =============== CHAT TAB ===============
    with tab2:
        st.subheader("💬 Ask Your Database")
        
        question = st.text_input(
            "Ask a question about your data:",
            placeholder="e.g., 'How many bookings in total?' or 'Show me high-revenue bookings'"
        )
        
        if question:
            try:
                # Generate SQL
                with st.spinner("🔄 Generating SQL..."):
                    success, sql = generate_sql_from_question(question)
                
                if not success:
                    st.error(f"❌ {sql}")
                else:
                    # Display SQL
                    st.markdown("**Generated SQL Query:**")
                    st.code(sql, language="sql")
                    
                    # Allow editing
                    edited_sql = st.text_area(
                        "Edit SQL (optional):",
                        value=sql,
                        height=100,
                        label_visibility="collapsed"
                    )
                    
                    # Check permissions
                    permission_ok, permission_msg = check_query_permissions(
                        edited_sql,
                        role,
                        allow_write,
                        blocked_tables
                    )
                    
                    if not permission_ok:
                        st.warning(permission_msg)
                    else:
                        # Execute button
                        if st.button("▶️ Execute Query", use_container_width=True):
                            with st.spinner("⏳ Executing query..."):
                                success, result = execute_query(edited_sql)
                            
                            if not success:
                                st.error(f"❌ {result}")
                            else:
                                if isinstance(result, pd.DataFrame):
                                    if not result.empty:
                                        st.markdown("**Query Results:**")
                                        st.dataframe(result, use_container_width=True)
                                        
                                        # Display statistics
                                        col1, col2, col3 = st.columns(3)
                                        with col1:
                                            st.metric("Rows Returned", len(result))
                                        with col2:
                                            st.metric("Columns", len(result.columns))
                                        with col3:
                                            st.metric("Size", f"{result.memory_usage(deep=True).sum() / 1024:.1f} KB")
                                        
                                        # Download button
                                        csv = result.to_csv(index=False)
                                        st.download_button(
                                            label="📥 Download as CSV",
                                            data=csv,
                                            file_name="query_results.csv",
                                            mime="text/csv"
                                        )
                                    else:
                                        st.info("✓ Query executed successfully but returned no results.")
                                
                                # Add to history
                                st.session_state.chat_history.append({
                                    "question": question,
                                    "sql": edited_sql,
                                    "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
                                })
            
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
        
        # Query History (in Chat Tab)
        if st.session_state.chat_history:
            st.divider()
            st.subheader("📜 Query History")
            
            for idx, chat in enumerate(reversed(st.session_state.chat_history)):
                with st.expander(
                    f"{chat.get('timestamp', 'N/A')} | {chat['question'][:50]}..."
                ):
                    st.write(f"**Question:** {chat['question']}")
                    st.code(chat['sql'], language="sql")
# FOOTER
# =============================================================================

st.divider()
st.markdown("""
**How to Use:**
1. Enter your PostgreSQL connection details
2. Click 'Connect'
3. Ask a question about your data in natural language
4. Review the generated SQL and click 'Execute Query'
5. View results and download as CSV if needed

**Access Control:**
- Configure your role and permissions in the sidebar
- Blocked tables and columns will prevent queries
- Write queries can be disabled for read-only access
""")
