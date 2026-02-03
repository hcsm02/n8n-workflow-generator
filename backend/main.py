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
    thread_id: Optional[str] = None

class ConfirmRequest(BaseModel):
    thread_id: str
    modifications: Optional[str] = None # Reserved for future use

@app.get("/")
def health_check():
    return {"status": "ok", "service": "n8n-workflow-generator"}

@app.post("/plan")
def create_plan(request: PlanRequest):
    """
    Step 1: Architect analyzes request and creates a plan.
    Returns: The plan for user review.
    """
    thread_id = request.thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    try:
        # Start the graph. It will stop BEFORE 'coder' node due to interrupt.
        inputs = {"user_request": request.prompt, "messages": []}
        
        # We use stream or invoke. Invoke will run until interrupt.
        # for event in graph.stream(inputs, config=config): pass 
        # But invoke is simpler if we trust it halts.
        
        # We need to run it. 
        # Note: 'invoke' returns the FINAL state. But since it interrupts, it returns state at interrupt.
        result = graph.invoke(inputs, config=config)
        
        return {
            "status": "plan_ready",
            "thread_id": thread_id,
            "plan": result.get("plan")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/confirm")
def confirm_and_generate(request: ConfirmRequest):
    """
    Step 2: User confirms the plan. Coder generates the code.
    Returns: The final n8n JSON.
    """
    config = {"configurable": {"thread_id": request.thread_id}}
    
    try:
        # Resume the graph. sending None proceeds from interrupt.
        result = graph.invoke(None, config=config)
        
        if result.get("error"):
            raise HTTPException(status_code=500, detail=result["error"])
            
        return result.get("json_result")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
