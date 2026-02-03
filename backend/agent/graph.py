import json
from typing import TypedDict, Annotated, List
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv
import os

from .prompts import get_system_prompt

load_dotenv()

# Select Model based on env (default to OpenAI if not specified, but support Anthropic)
if os.getenv("ANTHROPIC_API_KEY"):
    llm = ChatAnthropic(model="claude-3-5-sonnet-20240620", temperature=0)
else:
    # Support custom OpenAI-compatible providers (e.g. SiliconFlow, DeepSeek)
    base_url = os.getenv("OPENAI_BASE_URL")
    model_name = os.getenv("OPENAI_MODEL", "gpt-4o")
    
    llm = ChatOpenAI(
        model=model_name, 
        temperature=0,
        base_url=base_url if base_url else None
    )

class AgentState(TypedDict):
    messages: List[BaseMessage]
    json_result: dict
    error: str

def clean_json_string(content: str) -> str:
    # Remove markdown code blocks if present
    content = content.replace("```json", "").replace("```", "")
    return content.strip()

def generator_node(state: AgentState):
    messages = state['messages']
    
    # Prepend System Prompt if not present
    if not isinstance(messages[0], SystemMessage):
        system_prompt = get_system_prompt()
        messages.insert(0, SystemMessage(content=system_prompt))
    
    response = llm.invoke(messages)
    content = clean_json_string(response.content)
    
    try:
        parsed_json = json.loads(content)
        return {"json_result": parsed_json, "messages": messages + [response]}
    except json.JSONDecodeError as e:
        return {"error": f"JSON Decode Error: {str(e)}", "messages": messages + [response]}

# Build Graph
builder = StateGraph(AgentState)
builder.add_node("generator", generator_node)
builder.set_entry_point("generator")
builder.add_edge("generator", END)

graph = builder.compile()
