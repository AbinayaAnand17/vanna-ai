import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add src directory to Python path
src_path = str(Path(__file__).parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

load_dotenv()

# ── Core imports (Verfied paths for local vanna source) ──────────────────────
from vanna.core.agent.agent import Agent
from vanna.core.registry import ToolRegistry
from vanna.core.user.models import User
from vanna.core.user.request_context import RequestContext
from vanna.core.user.resolver import UserResolver
from vanna.core.system_prompt.base import SystemPromptBuilder
from vanna.servers.fastapi.app import vannaFastAPIServer
from vanna.integrations.google.gemini import GeminiLlmService
from vanna.integrations.chromadb.agent_memory import ChromaAgentMemory
from vanna.integrations.local.file_system_conversation_store import FileSystemConversationStore
from vanna.tools.run_sql import RunSqlTool
from vanna.capabilities.sql_runner import SqlRunner, RunSqlToolArgs
from vanna.core.tool import ToolContext
from vanna.tools.visualize_data import VisualizeDataTool
from vanna.tools.agent_memory import (
    SaveQuestionToolArgsTool,
    SearchSavedCorrectToolUsesTool,
    SaveTextMemoryTool
)
from typing import List, Dict, Any, Optional
import pandas as pd
import yaml

# ── LLM ───────────────────────────────────────────────────────────────────────
google_api_key = os.getenv("GOOGLE_API_KEY")
if not google_api_key or google_api_key == "your_key_here":
    print("[!] Warning: GOOGLE_API_KEY is missing or invalid in .env")
    print("    Please get a key from https://aistudio.google.com/app/apikey")
    llm = None
else:
    try:
        llm = GeminiLlmService(
            model="gemini-2.0-flash",
            api_key=google_api_key
        )
    except Exception as e:
        print(f"[!] LLM initialization failed: {e}")
        llm = None

# ── SAFE LOADER ───────────────────────────────────────────────────────────────
# ── DYNAMIC CONNECTION HUB ───────────────────────────────────────────────────
active_db: Dict[str, Any] = {"runner": None, "type": None}

class DynamicSqlRunner(SqlRunner):
    """Proxy runner that delegates to the currently active connection."""
    async def run_sql(self, args: RunSqlToolArgs, context: ToolContext) -> pd.DataFrame:
        if active_db["runner"] is None:
            raise Exception("No active database connection. Please connect via the Dashboard sidebar.")
        return await active_db["runner"].run_sql(args, context)

dynamic_runner = DynamicSqlRunner()
dynamic_sql_tool = RunSqlTool(
    sql_runner=dynamic_runner,
    custom_tool_name="run_active_sql",
    custom_tool_description="Execute SQL against the currently connected database from the UI."
)

def safe_tool(label, build_fn):
    """Try to initialize a DB tool. Returns (tool, status_message)."""
    try:
        t = build_fn()
        return t, f"  [OK]    {label}"
    except Exception as e:
        return None, f"  [FAIL]  {label}: {str(e)[:100]}"

db_tools   = []
status_log = []

# ── 1. SQLite ─────────────────────────────────────────────────────────────────
t, m = safe_tool("SQLite", lambda: RunSqlTool(
    sql_runner=__import__(
        'vanna.integrations.sqlite.sql_runner', fromlist=['SqliteRunner']
    ).SqliteRunner(database_path=os.getenv("SQLITE_PATH", "./sonline.db")),
    custom_tool_name="run_sqlite_sql",
    custom_tool_description="Query the local SQLite database (sonline.db)."
))
if t: db_tools.append(t)
status_log.append(m)

# ── 2. PostgreSQL (DISABLED) ──────────────────────────────────────────────────
# t, m = safe_tool("PostgreSQL — eis", lambda: RunSqlTool(
#     sql_runner=__import__(
#         'vanna.integrations.postgres.sql_runner', fromlist=['PostgresRunner']
#     ).PostgresRunner(
#         host=os.getenv("PG_HOST", "103.231.126.151"),
#         port=int(os.getenv("PG_PORT", 8761)),
#         user=os.getenv("PG_USER", "postgres"),
#         password=os.getenv("PG_PASSWORD", "Admin@123"),
#         database=os.getenv("PG_DB", "eis")
#     ),
#     custom_tool_name="run_postgres_sql",
#     custom_tool_description="Query the PostgreSQL EIS enterprise database."
# ))
# if t: db_tools.append(t)
# status_log.append("  [SKIP]  PostgreSQL (Disabled by user)")

# ── 3. MySQL (Asset Management) ───────────────────────────────────────────────
t, m = safe_tool("MySQL — assetmanagement", lambda: RunSqlTool(
    sql_runner=__import__(
        'vanna.integrations.mysql.sql_runner', fromlist=['MySQLRunner']
    ).MySQLRunner(
        host=os.getenv("MYSQL_HOST", "34.170.230.124"),
        port=int(os.getenv("MYSQL_PORT", 3306)),
        database=os.getenv("MYSQL_DB", "assetmanagement"),
        user=os.getenv("MYSQL_USER", "assetmanagementuat"),
        password=os.getenv("MYSQL_PASSWORD", "Sonline")
    ),
    custom_tool_name="run_mysql_sql",
    custom_tool_description="Query the Asset Management MySQL database."
))
if t: db_tools.append(t)
status_log.append(m)

# ── 4. MS SQL Server ──────────────────────────────────────────────────────────
t, m = safe_tool("MS SQL Server", lambda: RunSqlTool(
    sql_runner=__import__(
        'vanna.integrations.mssql.sql_runner', fromlist=['MSSQLRunner']
    ).MSSQLRunner(odbc_conn_str=os.getenv("MSSQL_CONN", "")),
    custom_tool_name="run_mssql_sql",
    custom_tool_description="Query the MS SQL Server database."
))
if t: db_tools.append(t)
status_log.append(m)

# ── 5. Snowflake ──────────────────────────────────────────────────────────────
t, m = safe_tool("Snowflake", lambda: RunSqlTool(
    sql_runner=__import__(
        'vanna.integrations.snowflake.sql_runner', fromlist=['SnowflakeRunner']
    ).SnowflakeRunner(
        account=os.getenv("SF_ACCOUNT", ""),
        username=os.getenv("SF_USER", ""),
        password=os.getenv("SF_PASSWORD", ""),
        database=os.getenv("SF_DB", ""),
        warehouse=os.getenv("SF_WAREHOUSE", "")
    ),
    custom_tool_name="run_snowflake_sql",
    custom_tool_description="Query the Snowflake data warehouse."
))
if t: db_tools.append(t)
status_log.append(m)

# ── 6. BigQuery ───────────────────────────────────────────────────────────────
t, m = safe_tool("BigQuery", lambda: RunSqlTool(
    sql_runner=__import__(
        'vanna.integrations.bigquery.sql_runner', fromlist=['BigQueryRunner']
    ).BigQueryRunner(
        project_id=os.getenv("BQ_PROJECT", ""),
        cred_file_path=os.getenv("BQ_CREDS", "")
    ),
    custom_tool_name="run_bigquery_sql",
    custom_tool_description="Query Google BigQuery."
))
if t: db_tools.append(t)
status_log.append(m)

# ── 7. Oracle ─────────────────────────────────────────────────────────────────
t, m = safe_tool("Oracle", lambda: RunSqlTool(
    sql_runner=__import__(
        'vanna.integrations.oracle.sql_runner', fromlist=['OracleRunner']
    ).OracleRunner(
        user=os.getenv("ORA_USER", ""),
        password=os.getenv("ORA_PASSWORD", ""),
        dsn=os.getenv("ORA_DSN", "localhost:1521/ORCL")
    ),
    custom_tool_name="run_oracle_sql",
    custom_tool_description="Query the Oracle database."
))
if t: db_tools.append(t)
status_log.append(m)

# ── 8. DuckDB ─────────────────────────────────────────────────────────────────
t, m = safe_tool("DuckDB", lambda: RunSqlTool(
    sql_runner=__import__(
        'vanna.integrations.duckdb.sql_runner', fromlist=['DuckDBRunner']
    ).DuckDBRunner(database_path=os.getenv("DUCKDB_PATH", "./sonline.duckdb")),
    custom_tool_name="run_duckdb_sql",
    custom_tool_description="Query the DuckDB analytical database."
))
if t: db_tools.append(t)
status_log.append(m)

# ── 9. Presto ─────────────────────────────────────────────────────────────────
t, m = safe_tool("Presto", lambda: RunSqlTool(
    sql_runner=__import__(
        'vanna.integrations.presto.sql_runner', fromlist=['PrestoRunner']
    ).PrestoRunner(
        host=os.getenv("PRESTO_HOST", "localhost"),
        port=int(os.getenv("PRESTO_PORT", 443)),
        catalog=os.getenv("PRESTO_CATALOG", "hive"),
        schema=os.getenv("PRESTO_SCHEMA", "default"),
        user=os.getenv("PRESTO_USER", ""),
        password=os.getenv("PRESTO_PASSWORD", "")
    ),
    custom_tool_name="run_presto_sql",
    custom_tool_description="Query the Presto distributed SQL engine."
))
if t: db_tools.append(t)
status_log.append(m)

# ── 10. Hive ──────────────────────────────────────────────────────────────────
t, m = safe_tool("Hive", lambda: RunSqlTool(
    sql_runner=__import__(
        'vanna.integrations.hive.sql_runner', fromlist=['HiveRunner']
    ).HiveRunner(
        host=os.getenv("HIVE_HOST", "localhost"),
        port=int(os.getenv("HIVE_PORT", 10000)),
        database=os.getenv("HIVE_DB", "default"),
        user=os.getenv("HIVE_USER", ""),
        password=os.getenv("HIVE_PASSWORD", "")
    ),
    custom_tool_name="run_hive_sql",
    custom_tool_description="Query Apache Hive on Hadoop."
))
if t: db_tools.append(t)
status_log.append(m)

# ── 11. ClickHouse ────────────────────────────────────────────────────────────
t, m = safe_tool("ClickHouse", lambda: RunSqlTool(
    sql_runner=__import__(
        'vanna.integrations.clickhouse.sql_runner', fromlist=['ClickHouseRunner']
    ).ClickHouseRunner(
        host=os.getenv("CH_HOST", "localhost"),
        port=int(os.getenv("CH_PORT", 8123)),
        database=os.getenv("CH_DB", "default"),
        user=os.getenv("CH_USER", "default"),
        password=os.getenv("CH_PASSWORD", "")
    ),
    custom_tool_name="run_clickhouse_sql",
    custom_tool_description="Query the ClickHouse analytics database."
))
if t: db_tools.append(t)
status_log.append(m)

# ── STORAGE ───────────────────────────────────────────────────────────────────
conversation_store = FileSystemConversationStore(base_dir="./conversations")

# ── MEMORY ────────────────────────────────────────────────────────────────────
try:
    agent_memory = ChromaAgentMemory(
        collection_name="sonline_memory",
        persist_directory="./chroma_db"
    )
except Exception as e:
    print(f"[!] ChromaDB initialization failed: {e}")
    print("    Falling back to basic memory (Warning: Persistance may be limited)")
    agent_memory = None

# ── AUTH ──────────────────────────────────────────────────────────────────────
class SonlineUserResolver(UserResolver):
    async def resolve_user(self, request_context: RequestContext) -> User:
        email = request_context.get_cookie('vanna_email') or 'admin@example.com'
        group = 'admin' if email == 'admin@example.com' else 'user'
        return User(id=email, email=email, group_memberships=[group])

# ── SYSTEM PROMPT ─────────────────────────────────────────────────────────────
SONLINE_SYSTEM_PROMPT = """
You are Sonline AI, an intelligent database assistant built for asset management professionals.

## Identity
- Name: Sonline AI
- Built by: Sonline (where insight meets innovation)
- Tone: Professional, concise, and helpful

## Role
You are connected to a MySQL/PostgreSQL database and help users explore, query, and visualize
their data through natural language. You convert user questions into insights — tables, charts,
summaries — without requiring SQL knowledge.

## On Database Connection
When a user connects a database, acknowledge it warmly and confirm:
- Database name
- Host and port
- Connected username
Then suggest 3–5 starter queries relevant to the schema.

## Capabilities
1. **List Tables** — Show all tables in the connected database
2. **Describe Schema** — Show columns, data types, and keys for any table
3. **Query Data** — Fetch records, apply filters, sort, and paginate
4. **Aggregate & Count** — SUM, COUNT, AVG, GROUP BY operations
5. **Visualize** — Bar charts, pie charts, line charts based on query results
6. **Export** — Allow users to download results as CSV

## Behavior Rules
- ALWAYS check if a database is connected before answering data queries
- If NOT connected, respond: "Please connect to a database first using **Database Connection** in the sidebar."
- NEVER fabricate data — only return results from the actual connected database
- If a query fails, explain the error clearly and suggest a fix
- Keep responses short — lead with the result, then explain if needed
- Format tabular data as structured tables, never as plain text lists

## Supported Query Intents
| User Says | Action |
|---|---|
| "list tables" / "show tables" | List all tables |
| "show columns for [table]" | Describe table schema |
| "show [table]" / "get [table] data" | Fetch top 50 records |
| "count [table]" / "how many [table]" | Return row count |
| "bar chart" / "pie chart" / "line chart" | Visualize last query result |
| "filter [table] where [condition]" | Apply WHERE clause |
| "export" | Download current results as CSV |
| "/help" | Show capability menu |

## Response Format (STRICT JSON)
Always return a VALID JSON object. No markdown wrapping. No preamble.

{{
  "message": "Short summary of what was done",
  "insights": "1-2 sentence analytical summary (optional)",
  "followupQuestions": ["Suggested next query?"],
  "richData": {{
    "type": "sql | dataframe | chart | schema",
    "data": {{ ... }}
  }}
}}

## Supported UI Types

1. SCHEMA — type: "schema", data keys: schema_type ("tables"|"columns"), items (list of strings)
2. DATAFRAME — type: "dataframe", data keys: columns (list), rows (list of objects)
3. CHART — type: "chart", data keys: engine ("recharts"), type ("bar"|"pie"|"line"), title, series

## Security
- Never expose raw connection credentials in responses
- Do not allow DROP, DELETE, TRUNCATE, or ALTER queries unless the user has Admin role
- Warn users before executing any destructive operation
"""

class SonlineSystemPromptBuilder(SystemPromptBuilder):
    async def build_system_prompt(
        self,
        user: User,
        tool_schemas: List[Dict[str, Any]],
        context: Dict[str, Any] = None
    ) -> str:
        context = context or {}
        is_admin = "admin" in user.group_memberships

        active_dbs = "\n".join(
            f"- {t.name}: {t.description}"
            for t in tool_schemas
            if t.name.startswith("run_") and "sql" in t.name
        )

        prompt = SONLINE_SYSTEM_PROMPT
        prompt += f"\n## Active Databases\n{active_dbs if active_dbs else '- run_mysql_sql: Asset Management primary database'}"

        if 'database_schema' in context:
            prompt += f"\n\n## Live Schema Context\n{context['database_schema']}"

        prompt += f"\n\nUser: {user.email} | Role: {'Admin' if is_admin else 'User'}\n"
        return prompt

# ── API ENDPOINTS (Custom Extensions) ─────────────────────────────────────────
def register_custom_routes(app):
    from fastapi import Request

    def build_db_tool(data: dict):
        db_type  = data.get("type", "mysql").lower()
        host     = data.get("host", "")
        port     = int(data.get("port", 0))
        user     = data.get("user", "")
        password = data.get("password", "")
        database = data.get("database", "")

        runners = {
            "mysql": lambda: __import__("vanna.integrations.mysql.sql_runner", fromlist=["MySQLRunner"]).MySQLRunner(
                host=host, port=port or 3306,
                user=user, password=password, database=database
            ),
            "postgresql": lambda: __import__("vanna.integrations.postgres.sql_runner", fromlist=["PostgresRunner"]).PostgresRunner(
                host=host, port=port or 5432,
                user=user, password=password, database=database
            ),
            "mssql": lambda: __import__("vanna.integrations.mssql.sql_runner", fromlist=["MSSQLRunner"]).MSSQLRunner(
                odbc_conn_str=f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={host},{port or 1433};DATABASE={database};UID={user};PWD={password}"
            ),
            "sqlite": lambda: __import__("vanna.integrations.sqlite.sql_runner", fromlist=["SqliteRunner"]).SqliteRunner(
                database_path=database or host or "./sonline.db"
            ),
            "oracle": lambda: __import__("vanna.integrations.oracle.sql_runner", fromlist=["OracleRunner"]).OracleRunner(
                host=host, port=port or 1521,
                user=user, password=password,
                service_name=database
            ),
            "duckdb": lambda: __import__("vanna.integrations.duckdb.sql_runner", fromlist=["DuckDBRunner"]).DuckDBRunner(
                database_path=database or ":memory:"
            ),
            "snowflake": lambda: __import__("vanna.integrations.snowflake.sql_runner", fromlist=["SnowflakeRunner"]).SnowflakeRunner(
                account=host, user=user, password=password,
                database=database, warehouse=str(port)
            ),
            "bigquery": lambda: __import__("vanna.integrations.bigquery.sql_runner", fromlist=["BigQueryRunner"]).BigQueryRunner(
                project_id=database, cred_file_path=password
            ),
        }
        
        # map postgres alias
        if db_type == "postgres":
            db_type = "postgresql"

        if db_type not in runners:
            raise ValueError(f"Unsupported database type: {db_type}")

        return runners[db_type]()

    @app.post("/api/vanna/v2/connect-db")
    async def connect_db(request: Request):
        data = await request.json()
        db_type = data.get("type", "mysql").lower()
        
        try:
            runner = build_db_tool(data)
            
            # Update global state
            active_db["runner"] = runner
            active_db["type"] = db_type
            
            return {
                "status": "success",
                "message": f"Successfully connected to {data.get('database')} ({db_type})"
            }

        except Exception as e:
            return {"status": "error", "message": str(e)}

# ── TOOL REGISTRY ─────────────────────────────────────────────────────────────
tools = ToolRegistry()

for tool in db_tools:
    tools.register_local_tool(tool, access_groups=["admin", "user"])

tools.register_local_tool(dynamic_sql_tool,                access_groups=["admin", "user"])
tools.register_local_tool(SaveQuestionToolArgsTool(),       access_groups=["admin"])
tools.register_local_tool(SearchSavedCorrectToolUsesTool(), access_groups=["admin", "user"])
tools.register_local_tool(SaveTextMemoryTool(),             access_groups=["admin", "user"])
tools.register_local_tool(VisualizeDataTool(),              access_groups=["admin", "user"])

# ── AGENT ─────────────────────────────────────────────────────────────────────
agent = Agent(
    llm_service=llm,
    tool_registry=tools,
    user_resolver=SonlineUserResolver(),
    agent_memory=agent_memory,
    conversation_store=conversation_store,
    system_prompt_builder=SonlineSystemPromptBuilder()
)

# ── SERVER ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    total = len(status_log)
    active = len(db_tools)

    print("=" * 58)
    print("   Sonline AI  —  Multi-Database SQL Assistant")
    print("=" * 58)
    print("\n  Database Status:")
    for line in status_log:
        print(line)
    print(f"\n  Active : {active}/{total} databases connected")
    print(f"  Model  : gemini-2.0-flash")
    print(f"  Memory : ChromaDB  ->  ./chroma_db")
    print(f"  Server : http://0.0.0.0:8001")
    print("=" * 58)

    # ── TRAINING ──────────────────────────────────────────────────────────────
    async def do_training():
        yaml_file = "./config/training.yaml"
        if os.path.exists(yaml_file) and agent_memory:
            print(f"\n[INFO] Loading training data from {yaml_file}...")
            try:
                with open(yaml_file, 'r') as f:
                    training_data = yaml.safe_load(f)
                    if training_data:
                        # Create a dummy context for training
                        dummy_context = ToolContext(
                            user=User(id="system", email="system@sonline.ai"),
                            conversation_id="system_training",
                            request_id="system_training"
                        )
                        for entry in training_data:
                            q = entry.get('question')
                            a = entry.get('answer')
                            if q and a:
                                await agent_memory.train(question=q, sql=a, context=dummy_context)
                        print(f"  [OK] Successfully trained on {len(training_data)} question-SQL pairs.")
            except Exception as e:
                print(f"  [FAIL] Failed to load training data: {e}")

    # Run training before server starts
    import asyncio
    asyncio.run(do_training())

    server = vannaFastAPIServer(agent)
    app = server.create_app()
    register_custom_routes(app)
    
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
