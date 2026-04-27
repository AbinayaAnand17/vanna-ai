# =============================================================
#  Sonline AI  –  FastAPI Backend   (Multi-DB Isolated)
#  Supports : MySQL · PostgreSQL
#  Install  : pip install fastapi uvicorn mysql-connector-python psycopg2-binary
#  Run      : uvicorn main:app --reload --host 0.0.0.0 --port 8001
# =============================================================

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import re, traceback

app = FastAPI(title="Sonline AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Pydantic models ──────────────────────────────────────────────
class DBConfig(BaseModel):
    type    : Optional[str] = "mysql"
    host    : Optional[str] = "34.170.230.124"
    port    : Optional[int] = 3306
    database: Optional[str] = "assetmanagement"
    user    : Optional[str] = "assetmanagementuat"
    password: Optional[str] = "Sonline"
    dbType  : Optional[str] = None   # alias sent by frontend

class QueryRequest(BaseModel):
    question: str
    db      : Optional[DBConfig] = None

# ══════════════════════════════════════════════════════════════════
# DB CONNECTION FACTORY  –  one fresh connection per request
# ══════════════════════════════════════════════════════════════════
def make_conn(cfg: DBConfig):
    """
    Returns a live DB connection scoped ONLY to cfg.database.
    No shared pools – each request is fully isolated.
    """
    db_type = (cfg.dbType or cfg.type or "mysql").lower()

    if db_type == "mysql":
        import mysql.connector
        return mysql.connector.connect(
            host=cfg.host, port=cfg.port or 3306,
            database=cfg.database,
            user=cfg.user, password=cfg.password,
            connection_timeout=10, connect_timeout=10,
        )

    if db_type == "postgresql":
        import psycopg2
        return psycopg2.connect(
            host=cfg.host, port=cfg.port or 5432,
            dbname=cfg.database,          # ← scoped to THIS database only
            user=cfg.user, password=cfg.password,
            connect_timeout=10,
        )

    raise HTTPException(
        status_code=400,
        detail=f"Unsupported database type: '{db_type}'. Supported: mysql, postgresql"
    )


# ── Execute any SQL against the active DB ───────────────────────
def exec_sql(sql: str, cfg: DBConfig):
    conn = make_conn(cfg)
    cur  = conn.cursor()
    try:
        cur.execute(sql)
        cols = [d[0] for d in (cur.description or [])]
        rows = [[str(v) if v is not None else "" for v in r] for r in cur.fetchall()]
    finally:
        cur.close()
        conn.close()
    return cols, rows


# ── Fetch table list scoped to this DB only ──────────────────────
def get_tables(cfg: DBConfig) -> List[str]:
    db_type = (cfg.dbType or cfg.type or "mysql").lower()

    if db_type == "mysql":
        _, rows = exec_sql("SHOW TABLES", cfg)
        return [r[0] for r in rows]

    if db_type == "postgresql":
        # Returns only tables in the 'public' schema of cfg.database
        sql = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_catalog = current_database()
            ORDER BY table_name
        """
        _, rows = exec_sql(sql, cfg)
        return [r[0] for r in rows]

    return []


# ── NL → SQL (DB-aware, uses only the active DB's tables) ────────
def nl_to_sql(question: str, cfg: DBConfig) -> str:
    q       = question.lower().strip()
    db_type = (cfg.dbType or cfg.type or "mysql").lower()
    SKIP    = {"show","list","all","the","for","of","in","me","give",
               "what","are","table","tables","column","columns","schema",
               "describe","field","fields","please","can","you","i","want"}

    # ── list tables ──────────────────────────────────────────────
    if any(x in q for x in ["list table","show table","all table","tables"]):
        if db_type == "postgresql":
            return (
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema='public' AND table_catalog=current_database() ORDER BY table_name"
            )
        return "SHOW TABLES"

    # ── describe / columns ───────────────────────────────────────
    if any(x in q for x in ["column","field","schema","describe"]):
        words = re.findall(r'\b\w+\b', q)
        tbl   = next((w for w in words if w not in SKIP and len(w) > 2), None)
        if tbl:
            if db_type == "postgresql":
                return (
                    f"SELECT column_name, data_type FROM information_schema.columns "
                    f"WHERE table_name='{tbl}' AND table_schema='public'"
                )
            return f"DESCRIBE `{tbl}`"
        return "SHOW TABLES" if db_type == "mysql" else (
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema='public' ORDER BY table_name"
        )

    # ── chart / aggregation – generic (works for any DB) ────────
    def q_col(col, tbl): return f'"{col}"' if db_type == "postgresql" else f"`{col}`"
    def q_tbl(tbl):      return f'"{tbl}"' if db_type == "postgresql" else f"`{tbl}`"

    # Fetch real table list to build smart queries
    try:
        tables = get_tables(cfg)
    except Exception:
        tables = []

    tables_lower = [t.lower() for t in tables]

    def find_table(*candidates):
        for c in candidates:
            for t in tables:
                if c in t.lower():
                    return t
        return tables[0] if tables else "data"

    if "bar chart" in q or "by category" in q:
        tbl = find_table("asset","item","product","order")
        return f"SELECT {q_col('category_id',tbl)} as name, COUNT(*) as value FROM {q_tbl(tbl)} GROUP BY {q_col('category_id',tbl)} ORDER BY value DESC LIMIT 20"

    if any(x in q for x in ["pie chart","donut","distribution","status breakdown"]):
        tbl = find_table("asset","item","order","sale")
        col = "status" if any("status" in t for t in tables_lower) else "id"
        return f"SELECT {q_col(col,tbl)} as name, COUNT(*) as value FROM {q_tbl(tbl)} GROUP BY {q_col(col,tbl)} ORDER BY value DESC LIMIT 10"

    if any(x in q for x in ["line chart","trend","monthly","over time"]):
        tbl = find_table("asset","order","log","sale")
        date_col = "created_at" if db_type == "postgresql" else "created"
        if db_type == "postgresql":
            return f"SELECT TO_CHAR({q_col(date_col,tbl)},'YYYY-MM') as name, COUNT(*) as value FROM {q_tbl(tbl)} GROUP BY name ORDER BY name LIMIT 12"
        return f"SELECT DATE_FORMAT({q_col(date_col,tbl)},'%Y-%m') as name, COUNT(*) as value FROM {q_tbl(tbl)} GROUP BY name ORDER BY name ASC LIMIT 12"

    if any(x in q for x in ["how many","count","total"]):
        tbl = find_table("asset","user","order","vendor")
        return f"SELECT COUNT(*) as total FROM {q_tbl(tbl)}"

    # ── keyword → table fallback ──────────────────────────────────
    kw_map = [
        (["purchase_order","purchase","order"], "purchase_orders"),
        (["maintenance","log"],                 "maintenance_logs"),
        (["vendor"],                            "vendors"),
        (["location"],                          "locations"),
        (["user","staff","employee"],           "users"),
        (["department"],                        "departments"),
        (["audit"],                             "audit_trails"),
        (["depreciation"],                      "depreciation_schedules"),
        (["categor"],                           "asset_categories"),
        (["asset"],                             "assets"),
    ]
    for keywords, fallback_tbl in kw_map:
        if any(kw in q for kw in keywords):
            # Use actual table if it exists in this DB
            actual = next((t for t in tables if fallback_tbl in t.lower() or any(kw in t.lower() for kw in keywords)), None)
            tbl = actual or fallback_tbl
            return f"SELECT * FROM {q_tbl(tbl)} LIMIT 100"

    # ── default: first real table in this DB ────────────────────
    if tables:
        return f"SELECT * FROM {q_tbl(tables[0])} LIMIT 100"
    return "SELECT 'No tables found' as message"


# ── Visualization decision ────────────────────────────────────────
def decide_viz(question: str, headers: List[str]) -> str:
    q = question.lower()
    if any(x in q for x in ["pie","donut","distribution"]): return "pie_chart"
    if any(x in q for x in ["line","trend","monthly"]):     return "line_chart"
    if any(x in q for x in ["bar","chart","graph"]):        return "bar_chart"
    if len(headers) == 2:                                    return "bar_chart"
    return "table"

def to_chart(headers: List[str], rows: List[List[str]]) -> List[dict]:
    out = []
    for r in rows:
        try:    out.append({"name": str(r[0]), "value": float(r[1]) if len(r) > 1 else 1})
        except: out.append({"name": str(r[0]), "value": 1})
    return out


# ══════════════════════════════════════════════════════════════════
# ROUTES
# ══════════════════════════════════════════════════════════════════
@app.get("/")
def root(): return {"status": "Sonline AI running", "port": 8001}

@app.get("/health")
def health(): return {"ok": True}

# Silence any legacy Vanna proxy calls
@app.api_route("/api/vanna/{path:path}", methods=["GET","POST","PUT","DELETE","OPTIONS"])
def vanna_stub(path: str):
    return {"status": "ok", "history": [], "data": []}


# ── Connect + return tables for THIS DB only ──────────────────────
@app.post("/api/db/connect")
def db_connect(config: DBConfig):
    try:
        tables = get_tables(config)
        return {
            "success" : True,
            "message" : f"Connected to {config.database}",
            "tables"  : tables,
            "db_type" : config.dbType or config.type,
            "database": config.database,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Natural-language → SQL → result (scoped to active DB) ────────
@app.post("/api/db/query")
def db_query(req: QueryRequest):
    if not req.db:
        raise HTTPException(status_code=400, detail="No database config provided")
    try:
        sql     = nl_to_sql(req.question, req.db)
        headers, rows = exec_sql(sql, req.db)
        db_name = req.db.database

        db_type = (req.db.dbType or req.db.type or "mysql").lower()
        is_meta = sql.strip().upper().startswith(("SHOW","DESCRIBE","SELECT TABLE_NAME","SELECT COLUMN_NAME"))

        if is_meta:
            return {
                "type"   : "table",
                "text"   : f"Schema info from <b>{db_name}</b>:",
                "sql"    : sql,
                "headers": headers,
                "rows"   : rows,
            }

        viz = decide_viz(req.question, headers)
        if viz != "table":
            return {
                "type": viz,
                "text": f"Results from <b>{db_name}</b>:",
                "sql" : sql,
                "data": to_chart(headers, rows),
            }

        return {
            "type"   : "table",
            "text"   : f"Results from <b>{db_name}</b> ({db_type.upper()}):",
            "sql"    : sql,
            "headers": headers,
            "rows"   : rows,
        }

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ── Run raw SQL ───────────────────────────────────────────────────
@app.post("/api/db/run_sql")
async def run_raw(body: dict):
    sql      = body.get("sql","").strip()
    cfg_data = body.get("db", None)
    if not sql:
        raise HTTPException(status_code=400, detail="No SQL provided")
    if not cfg_data:
        raise HTTPException(status_code=400, detail="No DB config provided")
    try:
        cfg = DBConfig(**cfg_data)
        headers, rows = exec_sql(sql, cfg)
        return {"headers": headers, "rows": rows}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    print("\n✅ Starting Sonline AI Backend → http://127.0.0.1:8001\n")
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
