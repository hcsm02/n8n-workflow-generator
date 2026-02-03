from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from langchain_core.messages import HumanMessage
from agent.graph import graph

app = FastAPI(title="n8n Workflow Generator")

class WorkflowRequest(BaseModel):
    prompt: str
    preferred_nodes: Optional[List[str]] = None

@app.get("/")
def health_check():
    return {"status": "ok", "service": "n8n-workflow-generator"}

@app.post("/generate")
def generate_workflow(request: WorkflowRequest):
    try:
        inputs = {"messages": [HumanMessage(content=request.prompt)]}
        result = graph.invoke(inputs)
        
        if result.get("error"):
            raise HTTPException(status_code=500, detail=result["error"])
            
        # Refactor: Return valid n8n JSON structure directly
        # If the LLM returned a valid dict, we return it as is.
        # This matches n8n's "Import from File" requirement.
        return result.get("json_result")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
