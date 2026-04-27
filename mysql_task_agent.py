import os
import sys
from pathlib import Path


# Add src directory to Python path to ensure we use our local vanna package
src_path = str(Path(__file__).parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel

from vanna import Agent
from vanna.core.registry import ToolRegistry
from vanna.core.user import UserResolver, User, RequestContext
from vanna.tools import RunSqlTool, VisualizeDataTool
from vanna.tools.agent_memory import SaveQuestionToolArgsTool, SearchSavedCorrectToolUsesTool, SaveTextMemoryTool
from vanna.servers.fastapi import vannaFastAPIServer
from vanna.integrations.google import GeminiLlmService
from vanna.integrations.mysql import MySQLRunner
from vanna.integrations.local.agent_memory import DemoAgentMemory
from vanna.core.system_prompt import DefaultSystemPromptBuilder

# 1. Configure LLM
api_key = os.getenv("SONLINE_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("?? Warning: No SONLINE_API_KEY or GOOGLE_API_KEY found in environment.")

llm = GeminiLlmService(
    model="gemini-2.0-flash-lite",
    api_key=api_key
)

# 2. Configure MySQL Database
mysql_runner = MySQLRunner(
    host=os.getenv("MYSQL_HOST", "localhost"),
    user=os.getenv("MYSQL_USER", "root"),
    password=os.getenv("MYSQL_PASSWORD", "password123"),
    database=os.getenv("MYSQL_DATABASE", "assetmanagement"),
    port=int(os.getenv("MYSQL_PORT", 3306))
)

db_tool = RunSqlTool(sql_runner=mysql_runner)

# 3. Configure Agent Memory
agent_memory = DemoAgentMemory(max_items=1000)

# 4. Configure User Resolver (Simple admin/user scoping)
class SimpleUserResolver(UserResolver):
    async def resolve_user(self, request_context: RequestContext) -> User:
        user_email = request_context.get_cookie('vanna_email') or 'admin@example.com'
        group = 'admin' if user_email == 'admin@example.com' else 'user'
        return User(id=user_email, email=user_email, group_memberships=[group])

user_resolver = SimpleUserResolver()

# 5. Create Agent with a high-fidelity system prompt
system_prompt_builder = DefaultSystemPromptBuilder(
    base_prompt="""
    You are Sonline AI, a premium Enterprise Intelligence Assistant. 
    You have access to a MySQL database (Asset Management).
    
    ### RESPONSE FORMAT RULES:
    Always wrap your response in a clear, conversational message.
    If you find interesting patterns, provide them as a 'Pro Insight'.
    
    To enable high-fidelity UI features, you can respond in a structured JSON format if the user asks for analysis:
    ```json
    {
      "message": "Your conversational response here...",
      "insights": "A professional insight about the data...",
      "followupQuestions": ["Question 1?", "Question 2?"],
      "richData": { ... }
    }
    ```
    
    ### DATABASE SCHEMA:
    The database has a 'tasks' table:
    - id, title, description, status, created_at
    
    And an 'assets' table (Asset Management):
    - id, asset_code, asset_name, category_id, status, current_value, etc.

    Always use the 'run_sql' tool for data operations.
    """
)

tools = ToolRegistry()
tools.register_local_tool(db_tool, access_groups=['admin', 'user'])
tools.register_local_tool(SaveQuestionToolArgsTool(), access_groups=['admin'])
tools.register_local_tool(SearchSavedCorrectToolUsesTool(), access_groups=['admin', 'user'])
tools.register_local_tool(SaveTextMemoryTool(), access_groups=['admin', 'user'])
tools.register_local_tool(VisualizeDataTool(), access_groups=['admin', 'user'])

agent = Agent(
    llm_service=llm,
    tool_registry=tools,
    user_resolver=user_resolver,
    agent_memory=agent_memory,
    system_prompt_builder=system_prompt_builder
)

# 6. Run Server
server = vannaFastAPIServer(agent)
app = server.create_app()

class ConnectRequest(BaseModel):
    type: str = "mysql"
    host: str
    port: int
    user: str
    password: str
    database: str

@app.post("/api/vanna/v2/connect-db")
async def connect_db(req: ConnectRequest):
    try:
        print(f"?? Attempting to connect to: {req.host}:{req.port}/{req.database}")
        
        # 1. Create a new runner
        new_mysql_runner = MySQLRunner(
            host=req.host,
            user=req.user,
            password=req.password,
            database=req.database,
            port=req.port
        )
        
        # 2. Update the existing db_tool's runner
        # Since db_tool was registered in the registry, we update its reference
        db_tool.sql_runner = new_mysql_runner
        
        return {"status": "success", "message": f"Connected to {req.database} successfully"}
    except Exception as e:
        print(f"?? Connection failed: {str(e)}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    print("\n" + "="*50)
    print("SONLINE AI BACKEND IS STARTING")
    print("Listening on: http://localhost:8001")
    print("Tip: Use the 'Database Connection' menu in the UI to sync.")
    print("="*50 + "\n")
    
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
