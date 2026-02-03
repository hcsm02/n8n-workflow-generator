import json
import os
from typing import TypedDict, Annotated, List, Optional
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv

from .prompts import get_architect_prompt, get_coder_prompt

load_dotenv()

# Select Model
if os.getenv("ANTHROPIC_API_KEY"):
    llm = ChatAnthropic(model="claude-3-5-sonnet-20240620", temperature=0)
else:
    base_url = os.getenv("OPENAI_BASE_URL")
    model_name = os.getenv("OPENAI_MODEL", "gpt-4o")
    llm = ChatOpenAI(
        model=model_name, 
        temperature=0,
        base_url=base_url if base_url else None
    )

class AgentState(TypedDict):
    messages: List[BaseMessage]
    user_request: str
    plan: Optional[dict]
    json_result: Optional[dict]
    error: Optional[str]

def clean_json_string(content: str) -> str:
    content = content.replace("```json", "").replace("```", "")
    return content.strip()

def architect_node(state: AgentState):
    """
    Analyzes the user request and produces a plan.
    """
    user_request = state['user_request']
    prompt = get_architect_prompt(user_request)
    
    response = llm.invoke([HumanMessage(content=prompt)])
    content = clean_json_string(response.content)
    
    try:
        plan = json.loads(content)
        return {"plan": plan, "messages": [response]}
    except json.JSONDecodeError as e:
        return {"error": f"Architect JSON Error: {str(e)}", "messages": [response]}

def coder_node(state: AgentState):
    """
    Generates the n8n workflow based on the approved plan.
    """
    plan = state.get('plan')
    if not plan:
        return {"error": "No plan found provided to Coder."}
    
    coder_sys_prompt = get_coder_prompt()
    # We pass the plan as the user input to the coder
    user_msg = f"Implement this plan:\n{json.dumps(plan, indent=2, ensure_ascii=False)}"
    
    messages = [
        SystemMessage(content=coder_sys_prompt),
        HumanMessage(content=user_msg)
    ]
    
    response = llm.invoke(messages)
    content = clean_json_string(response.content)
    
    try:
        parsed_json = json.loads(content)
        return {"json_result": parsed_json, "messages": [response]}
    except json.JSONDecodeError as e:
        return {"error": f"Coder JSON Error: {str(e)}", "json_result": None}

# Build Graph
builder = StateGraph(AgentState)
builder.add_node("architect", architect_node)
builder.add_node("coder", coder_node)

builder.set_entry_point("architect")
builder.add_edge("architect", "coder")
builder.add_edge("coder", END)

# In-memory checkpointer for persistence
memory = MemorySaver()

# Compile with interrupt before 'coder' to allow Human Review
graph = builder.compile(checkpointer=memory, interrupt_before=["coder"])
