from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from langchain_core.messages import HumanMessage
from agent.graph import graph
import uuid

app = FastAPI(title="n8n Workflow Generator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PlanRequest(BaseModel):
    prompt: str
    n8n_version: str = "1.76.1"  # 用户的 n8n 版本，默认为最新稳定版
    thread_id: Optional[str] = None

class ConfirmRequest(BaseModel):
    thread_id: str
    modifications: Optional[str] = None # Reserved for future use

@app.get("/")
def health_check():
    return {"status": "ok", "service": "n8n-workflow-generator"}

@app.post("/plan")
async def create_plan(request: PlanRequest):
    """
    Step 1: Architect analyzes request and creates a plan.
    Returns: The plan for user review.
    """
    print(f"DEBUG: Received plan request for prompt: {request.prompt}")
    thread_id = request.thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    try:
        # Start the graph. It will stop BEFORE 'coder' node due to interrupt.
        inputs = {"user_request": request.prompt, "n8n_version": request.n8n_version, "messages": []}
        
        print(f"DEBUG: Invoking graph.ainvoke...")
        result = await graph.ainvoke(inputs, config=config)
        print(f"DEBUG: graph.ainvoke completed.")
        
        if result.get("error"):
            raise HTTPException(status_code=500, detail=result["error"])
            
        return {
            "status": "plan_ready",
            "thread_id": thread_id,
            "plan": result.get("plan")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/confirm")
async def confirm_and_generate(request: ConfirmRequest):
    """
    Step 2: User confirms the plan. Coder generates the code.
    Returns: The final n8n JSON.
    """
    config = {"configurable": {"thread_id": request.thread_id}}
    
    try:
        # Resume the graph. sending None proceeds from interrupt.
        print(f"DEBUG: Confirming plan for thread_id: {request.thread_id}")
        result = await graph.ainvoke(None, config=config)
        print(f"DEBUG: Confirm result keys: {list(result.keys()) if result else 'None'}")
        print(f"DEBUG: json_result is {'set' if result.get('json_result') else 'None/empty'}")
        print(f"DEBUG: error is: {result.get('error', 'no error')}")
        
        if result.get("error"):
            raise HTTPException(status_code=500, detail=result["error"])
        
        json_result = result.get("json_result")
        
        # Fallback: if json_result is None but we have a valid plan with nodes/connections,
        # use the plan itself as the workflow JSON (since Architect already produced it)
        if not json_result and result.get("plan"):
            plan = result["plan"]
            if isinstance(plan, dict) and "nodes" in plan and "connections" in plan:
                print("DEBUG: Using plan as fallback json_result (Architect already produced workflow-like JSON)")
                json_result = plan
        
        return json_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
