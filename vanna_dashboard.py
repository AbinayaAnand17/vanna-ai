"""
Sonline AI Professional Dashboard - Streamlit Application
A comprehensive web interface for querying PostgreSQL databases using natural language.
Integrates with Sonline AI for SQL generation and policy guardrails.
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
src_path = str(Path(__file__).parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

import streamlit as st
import pandas as pd
from datetime import datetime
import psycopg2
from psycopg2 import sql
import os
from typing import Dict, List, Tuple, Optional
import traceback
import vanna
from vanna.googlegeminicf import vannaGoogleGeminiCF
from vanna.chromadb import ChromaDB_VectorStore

class SonlineAssistant(vannaGoogleGeminiCF, ChromaDB_VectorStore):
    def __init__(self, config=None):
        vannaGoogleGeminiCF.__init__(self, config=config)
        ChromaDB_VectorStore.__init__(self, config=config)

# =============================================================================
# STREAMLIT PAGE CONFIGURATION
# =============================================================================

st.set_page_config(
    page_title="Sonline AI Dashboard",
    page_icon="?",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    .header-title {
        color: #1f77e4;
        font-size: 3em;
        font-weight: bold;
        text-align: center;
        margin-top: 0.5em;
    }
    .header-subtitle {
        color: #666;
        font-size: 1.1em;
        text-align: center;
        margin-top: -0.5em;
        margin-bottom: 2em;
    }
    .status-connected {
        color: #28a745;
        font-weight: bold;
    }
    .status-disconnected {
        color: #dc3545;
        font-weight: bold;
    }
    .query-result-header {
        color: #1f77e4;
        font-size: 1.3em;
        font-weight: bold;
        margin-top: 1em;
        margin-bottom: 0.5em;
    }
    .sql-query {
        background-color: #f8f9fa;
        padding: 1em;
        border-left: 4px solid #1f77e4;
        border-radius: 4px;
        font-family: monospace;
        line-height: 1.5;
    }
    </style>
    """, unsafe_allow_html=True)

# =============================================================================
# SESSION STATE INITIALIZATION
# =============================================================================

def initialize_session_state():
    """Initialize all session state variables"""
    if "db_connection" not in st.session_state:
        st.session_state.db_connection = None
    if "connected" not in st.session_state:
        st.session_state.connected = False
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "db_config" not in st.session_state:
        st.session_state.db_config = {
            "host": "localhost",
            "port": 5432,
            "database": "postgres",
            "user": "postgres",
            "password": ""
        }
    if "access_control" not in st.session_state:
        st.session_state.access_control = {
            "role": "analyst",
            "allow_write": False,
            "blocked_tables": [],
            "blocked_columns": []
        }
    if "vanna_instance" not in st.session_state:
        # Initialize Sonline AI with Gemini (defaulting to environment variable for key)
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key:
            try:
                vn = SonlineAssistant(config={'api_key': api_key, 'model_name': 'gemini-1.5-pro'})
                st.session_state.vanna_instance = vn
                # Initial training as per user suggestion
                vn.train(documentation="""
                You are Sonline AI, an intelligent SQL assistant.
                
                Your job:
                - Convert user questions into SQL queries
                - Do NOT ask user to write SQL
                - Always generate SQL based on the question
                
                Rules:
                - Use correct table and column names
                - Never use SELECT *
                - Add LIMIT 50
                - Explain the query briefly
                """)
            except Exception as e:
                st.error(f"Failed to initialize Sonline AI: {e}")
        else:
            st.session_state.vanna_instance = None

initialize_session_state()

# =============================================================================
# DATABASE CONNECTION FUNCTIONS
# =============================================================================

def connect_to_database(config: Dict) -> Tuple[bool, str]:
    """
    Establish connection to PostgreSQL database
    
    Args:
        config: Dictionary with database configuration
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        connection = psycopg2.connect(
            host=config["host"],
            port=config["port"],
            database=config["database"],
            user=config["user"],
            password=config["password"]
        )
        st.session_state.db_connection = connection
        st.session_state.connected = True
        st.session_state.db_config = config
        return True, "Successfully connected to PostgreSQL database"
    except psycopg2.Error as e:
        st.session_state.connected = False
        error_msg = f"Database connection failed: {str(e)}"
        return False, error_msg
    except Exception as e:
        st.session_state.connected = False
        error_msg = f"Unexpected error during connection: {str(e)}"
        return False, error_msg

def disconnect_database():
    """Close database connection"""
    try:
        if st.session_state.db_connection:
            st.session_state.db_connection.close()
            st.session_state.db_connection = None
            st.session_state.connected = False
            return True, "Disconnected from database"
    except Exception as e:
        return False, f"Error during disconnection: {str(e)}"
    return True, "Already disconnected"

def execute_query(query: str) -> Tuple[bool, pd.DataFrame | str]:
    """
    Execute SQL query on connected database
    
    Args:
        query: SQL query string
        
    Returns:
        Tuple of (success: bool, result: DataFrame or error message)
    """
    if not st.session_state.connected or not st.session_state.db_connection:
        return False, "Not connected to database"
    
    try:
        # Check for blocked operations in write queries
        access_control = st.session_state.access_control
        query_upper = query.upper().strip()
        
        # Check if query contains write operations
        write_operations = ["INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER"]
        is_write_query = any(query_upper.startswith(op) for op in write_operations)
        
        if is_write_query and not access_control["allow_write"]:
            return False, f"? Write queries are not allowed for role '{access_control['role']}'"
        
        # Check for blocked tables
        if access_control["blocked_tables"]:
            blocked_tables = [t.strip().upper() for t in access_control["blocked_tables"]]
            query_tables = extract_table_names(query_upper)
            blocked_in_query = [t for t in query_tables if t.upper() in blocked_tables]
            if blocked_in_query:
                return False, f"? Access denied to table(s): {', '.join(blocked_in_query)}"
        
        # Execute query
        with st.session_state.db_connection.cursor() as cursor:
            cursor.execute(query)
            
            # Fetch results if it's a SELECT query
            if query_upper.startswith("SELECT"):
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                df = pd.DataFrame(rows, columns=columns)
                return True, df
            else:
                st.session_state.db_connection.commit()
                return True, pd.DataFrame()
                
    except psycopg2.Error as e:
        return False, f"SQL Error: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"

def extract_table_names(query: str) -> List[str]:
    """
    Extract table names from SQL query (simplified)
    
    Args:
        query: SQL query string
        
    Returns:
        List of table names
    """
    import re
    # Simple pattern to extract table names from FROM and JOIN clauses
    pattern = r'(?:FROM|JOIN)\s+(\w+)'
    matches = re.findall(pattern, query, re.IGNORECASE)
    return matches

def get_database_schema() -> str:
    """
    Get database schema information for Sonline AI training
    
    Returns:
        Schema information as string
    """
    if not st.session_state.connected:
        return "Not connected to database"
    
    try:
        with st.session_state.db_connection.cursor() as cursor:
            # Get all tables
            cursor.execute("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public'
            """)
            tables = cursor.fetchall()
            
            schema_info = "Database Schema:\n\n"
            
            for (table_name,) in tables:
                schema_info += f"Table: {table_name}\n"
                
                # Get columns for each table
                cursor.execute(f"""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = %s
                """, (table_name,))
                
                columns = cursor.fetchall()
                for col_name, col_type, nullable in columns:
                    nullable_str = "NULL" if nullable == "YES" else "NOT NULL"
                    schema_info += f"  - {col_name}: {col_type} ({nullable_str})\n"
                
                schema_info += "\n"
            
            return schema_info
    except Exception as e:
        return f"Error retrieving schema: {str(e)}"

# =============================================================================
# Sonline AI INTEGRATION (Placeholder)
# =============================================================================

def generate_sql_from_question(question: str) -> Tuple[bool, str]:
    """
    Generate SQL query from natural language question using Sonline AI
    """
    try:
        if st.session_state.vanna_instance is None:
            return False, "Sonline AI is not initialized. Please set GOOGLE_API_KEY environment variable."
        
        vn = st.session_state.vanna_instance
        
        # Ensure we have schema info if connected
        if st.session_state.connected and not getattr(vn, 'trained_on_schema', False):
            schema = get_database_schema()
            vn.train(documentation=f"Database Schema:\n\n{schema}")
            vn.trained_on_schema = True
        
        sql_query = vn.generate_sql(question)
        
        if not sql_query:
            return False, "Vanna failed to generate a SQL query."
            
        return True, sql_query
        
    except Exception as e:
        return False, f"Error generating SQL: {str(e)}"

# =============================================================================
# UI COMPONENTS
# =============================================================================

def render_header():
    """Render page header"""
    # Centered Logo
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        logo_path = os.path.join("img", "sonline_logo.png")
        if os.path.exists(logo_path):
            st.image(logo_path, use_container_width=True)
        else:
            st.markdown('<div class="header-title">? Sonline AI</div>', unsafe_allow_html=True)
            
    st.markdown(
        '<div class="header-subtitle">Enterprise-ready natural language analytics with SQL generation, policy guardrails, and explainable results.</div>',
        unsafe_allow_html=True
    )
    st.divider()

def render_sidebar():
    """Render sidebar with settings and status"""
    with st.sidebar:
        st.title("?? Settings & Control")
        
        # === SETTINGS SECTION ===
        with st.expander("Settings", expanded=True):
            if st.button("?? Clear Chat", use_container_width=True):
                st.session_state.chat_history = []
                st.success("Chat cleared!")
                st.rerun()
        
        # === ACCESS CONTROL SECTION ===
        with st.expander("Access Control", expanded=True):
            st.session_state.access_control["role"] = st.selectbox(
                "Role",
                ["analyst", "admin", "viewer"],
                help="Select user role for permission level"
            )
            
            st.session_state.access_control["allow_write"] = st.checkbox(
                "Allow Write Queries (INSERT, UPDATE, DELETE)",
                value=st.session_state.access_control["allow_write"],
                help="Allow modification of database data"
            )
            
            blocked_tables_input = st.text_input(
                "Blocked Tables (comma-separated)",
                value=",".join(st.session_state.access_control["blocked_tables"]),
                help="Tables that cannot be queried"
            )
            st.session_state.access_control["blocked_tables"] = [
                t.strip() for t in blocked_tables_input.split(",") if t.strip()
            ]
            
            blocked_columns_input = st.text_input(
                "Blocked Columns (comma-separated)",
                value=",".join(st.session_state.access_control["blocked_columns"]),
                help="Columns that cannot be accessed"
            )
            st.session_state.access_control["blocked_columns"] = [
                c.strip() for c in blocked_columns_input.split(",") if c.strip()
            ]
        
        # === STATUS SECTION ===
        with st.expander("Status", expanded=True):
            if st.session_state.connected:
                st.markdown(
                    '<span class="status-connected">? Connected</span>',
                    unsafe_allow_html=True
                )
                st.write(f"**Role:** {st.session_state.access_control['role']}")
                write_status = "? Enabled" if st.session_state.access_control['allow_write'] else "? Disabled"
                st.write(f"**Write Queries:** {write_status}")
                
                if st.session_state.db_config:
                    st.write(f"**Host:** {st.session_state.db_config.get('host', 'N/A')}")
                    st.write(f"**Database:** {st.session_state.db_config.get('database', 'N/A')}")
            else:
                st.markdown(
                    '<span class="status-disconnected">? Disconnected</span>',
                    unsafe_allow_html=True
                )
                st.write("No database connection active")

def render_connection_panel():
    """Render database connection form"""
    st.subheader("? Database Connection")
    
    col1, col2 = st.columns(2)
    
    with col1:
        db_type = st.selectbox("Database Type", ["PostgreSQL"], disabled=True)
        host = st.text_input("Host", value=st.session_state.db_config["host"])
        port = st.number_input("Port", value=st.session_state.db_config["port"], min_value=1, max_value=65535)
        user = st.text_input("User", value=st.session_state.db_config["user"])
    
    with col2:
        password = st.text_input("Password", value=st.session_state.db_config["password"], type="password")
        database = st.text_input("Database Name", value=st.session_state.db_config["database"])
        st.write("")  # Spacing
    
    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
    
    with col_btn1:
        if st.button("? Connect", use_container_width=True):
            with st.spinner("Connecting..."):
                config = {
                    "host": host,
                    "port": port,
                    "database": database,
                    "user": user,
                    "password": password
                }
                success, message = connect_to_database(config)
                if success:
                    st.success(f"? {message}")
                else:
                    st.error(f"? {message}")
    
    with col_btn2:
        if st.button("? Disconnect", use_container_width=True):
            success, message = disconnect_database()
            if success:
                st.success(f"? {message}")
                st.rerun()
            else:
                st.error(f"? {message}")
    
    with col_btn3:
        if st.session_state.connected:
            if st.button("? View Schema", use_container_width=True):
                st.session_state.show_schema = True

def render_schema_info():
    """Render database schema information"""
    if "show_schema" in st.session_state and st.session_state.show_schema:
        with st.expander("? Database Schema Information", expanded=True):
            schema_info = get_database_schema()
            st.code(schema_info, language="text")
            if st.button("Close Schema"):
                st.session_state.show_schema = False
                st.rerun()

def render_chat_interface():
    """Render the main chat interface"""
    st.subheader("? Natural Language Query Interface")
    
    if not st.session_state.connected:
        st.warning("?? Please connect to a database first to start querying.")
        return
    
    # Chat input
    question = st.text_input(
        "Ask a question about your data",
        placeholder="e.g., 'How many users do we have?' or 'Show me the top 5 customers'"
    )
    
    if question:
        # Generate SQL
        with st.spinner("? Generating SQL query..."):
            success, sql_query = generate_sql_from_question(question)
        
        if not success:
            st.error(f"? {sql_query}")
            return
        
        # Display generated SQL
        st.markdown('<div class="query-result-header">Generated SQL Query:</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="sql-query">{sql_query}</div>', unsafe_allow_html=True)
        
        # Allow user to edit SQL before execution
        st.markdown("**Edit Query (Optional):**")
        edited_sql = st.text_area("", value=sql_query, height=100, label_visibility="collapsed")
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            execute_button = st.button("?? Execute Query", use_container_width=True)
        
        if execute_button:
            with st.spinner("? Executing query..."):
                success, result = execute_query(edited_sql)
            
            if not success:
                st.error(f"? {result}")
            else:
                # Display results
                if isinstance(result, pd.DataFrame):
                    if not result.empty:
                        st.markdown('<div class="query-result-header">Query Results:</div>', unsafe_allow_html=True)
                        st.dataframe(result, use_container_width=True)
                        
                        # Display query statistics
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Rows Returned", len(result))
                        with col2:
                            st.metric("Columns", len(result.columns))
                        with col3:
                            st.metric("Execution Time", "< 1s")
                        
                        # Download option
                        csv = result.to_csv(index=False)
                        st.download_button(
                            label="? Download as CSV",
                            data=csv,
                            file_name=f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                    else:
                        st.info("? Query executed successfully but returned no results.")
                
                # Add to chat history
                chat_entry = {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "question": question,
                    "sql": edited_sql,
                    "status": "? Success"
                }
                st.session_state.chat_history.append(chat_entry)

def render_chat_history():
    """Render chat history"""
    if st.session_state.chat_history:
        st.subheader("? Query History")
        
        for i, entry in enumerate(reversed(st.session_state.chat_history)):
            with st.expander(
                f"{entry['timestamp']} | {entry['question'][:50]}... | {entry['status']}",
                expanded=False
            ):
                st.write(f"**Question:** {entry['question']}")
                st.code(entry['sql'], language="sql")

def render_sample_queries():
    """Render sample queries section"""
    st.subheader("? Sample Queries")
    
    sample_queries = {
        "Get table count": "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';",
        "List all tables": "SELECT tablename FROM pg_tables WHERE schemaname = 'public';",
        "Get database size": "SELECT pg_size_pretty(pg_database_size(current_database()));",
        "Top 10 records": "SELECT * FROM information_schema.tables WHERE table_schema = 'public' LIMIT 10;",
    }
    
    col1, col2 = st.columns(2)
    
    for idx, (label, query) in enumerate(sample_queries.items()):
        with col1 if idx % 2 == 0 else col2:
            if st.button(label, use_container_width=True):
                st.session_state.sample_query = query
                success, result = execute_query(query)
                if success and isinstance(result, pd.DataFrame) and not result.empty:
                    st.write(result)
                else:
                    st.info("Query executed or no results returned.")

# =============================================================================
# MAIN APPLICATION
# =============================================================================

def main():
    """Main application logic"""
    # Render header
    render_header()
    
    # Render sidebar
    render_sidebar()
    
    # Main content area
    tab1, tab2, tab3 = st.tabs(["? Query Interface", "? Schema Explorer", "? Documentation"])
    
    with tab1:
        # Connection panel
        render_connection_panel()
        st.divider()
        
        # Schema information
        render_schema_info()
        
        # Chat interface
        render_chat_interface()
        st.divider()
        
        # Chat history
        render_chat_history()
    
    with tab2:
        st.subheader("? Database Schema Explorer")
        
        if st.session_state.connected:
            schema_info = get_database_schema()
            st.code(schema_info, language="text")
        else:
            st.warning("?? Please connect to a database to view schema information.")
    
    with tab3:
        st.subheader("? Documentation & Help")
        
        st.markdown("""
        ### How to Use Sonline AI Dashboard
        
        **1. Connect to Database**
        - Fill in your PostgreSQL connection details
        - Click "Connect" button
        - Check the status indicator in the sidebar
        
        **2. Ask Questions**
        - Enter a natural language question in the query box
        - The system will generate SQL automatically
        - Review and optionally edit the SQL before executing
        - Click "Execute Query" to run it
        
        **3. Access Control**
        - Set your role (analyst, admin, viewer)
        - Enable/disable write queries based on permissions
        - Add tables/columns to blocked list for restrictions
        
        **4. Query History**
        - All executed queries are saved in history
        - Click on entries to review previous queries
        - Download results as CSV files
        
        ### Features
        
        ? **Natural Language to SQL** - Ask questions naturally, get SQL automatically
        ? **Policy Guardrails** - Role-based access control and query restrictions
        ? **Query Editing** - Review generated SQL before execution
        ? **Results Export** - Download query results as CSV
        ? **Schema Explorer** - Browse database structure
        ? **Query History** - Track all executed queries
        
        ### Security
        
        - Passwords are never logged or stored
        - Write query execution requires explicit permission
        - Table and column access can be restricted
        - Role-based permissions control available actions
        """)

if __name__ == "__main__":
    main()
