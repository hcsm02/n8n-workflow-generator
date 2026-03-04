"""
LangGraph 工作流图定义

简化后的架构：
  architect → (interrupt for user review) → coder → END

Architect 和 Coder 都是单次 LLM 调用，所有参考数据已预加载到 prompt 中。
不再使用 MCP 工具调用循环，性能从 3-5 分钟降到 20-40 秒。
"""
import os
import json
import re
import uuid
from typing import TypedDict, Any, Optional, List
from dotenv import load_dotenv

load_dotenv()

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from agent.prompts import get_architect_prompt, get_coder_prompt
from agent.mcp_client import mcp_client


class AgentState(TypedDict):
    messages: list
    user_request: str
    n8n_version: str
    plan: Optional[dict]
    json_result: Optional[Any]
    error: Optional[str]


# ============================================================
# LLM 初始化
# ============================================================

llm = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL", "gpt-4"),
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    openai_api_base=os.getenv("OPENAI_BASE_URL"),
    temperature=0.2,
)

# 启动时预加载参考数据
mcp_client.load_local_reference_data()


# ============================================================
# JSON 提取工具函数
# ============================================================

def clean_json_string(content: str) -> str:
    """
    从 LLM 回复中提取有效的 JSON 对象。
    策略：
    1. 找所有 Markdown 代码块，只保留以 { 开头的（排除 HTML/text）
    2. 对每个候选块尝试 json.loads 验证
    3. 如果代码块都不行，从全文中提取最外层 { ... }
    """
    # 策略1：查找所有 Markdown 代码块
    all_blocks = re.findall(r'```(?:json|JSON)?\s*\n?(.*?)```', content, re.DOTALL)
    
    # 只保留看起来像 JSON 的块（以 { 开头）
    json_blocks = [b.strip() for b in all_blocks if b.strip().startswith('{')]
    
    if json_blocks:
        # 优先选包含 plan 关键字的块
        plan_blocks = [b for b in json_blocks if '"summary"' in b or '"nodes"' in b]
        candidates = plan_blocks if plan_blocks else json_blocks
        
        # 按长度从大到小排序，尝试解析每个候选
        candidates.sort(key=len, reverse=True)
        for candidate in candidates:
            try:
                json.loads(candidate)
                return candidate
            except json.JSONDecodeError:
                continue
        return candidates[0]

    # 策略2：从全文中提取最外层的 { ... }
    if '{' in content and '}' in content:
        start_idx = content.find('{')
        end_idx = content.rfind('}') + 1
        return content[start_idx:end_idx].strip()
    
    return content.strip()


# ============================================================
# Architect 节点 — 单次 LLM 调用
# ============================================================

async def architect_node(state: AgentState):
    """
    分析用户需求，设计工作流方案。
    不使用工具调用，所有参考数据已嵌入 prompt。
    """
    user_request = state.get('user_request', '')
    n8n_version = state.get('n8n_version', '1.76.1')
    prompt = get_architect_prompt(user_request, n8n_version)
    
    messages = [
        SystemMessage(content=prompt),
        HumanMessage(content=user_request)
    ]

    print(f"=== Architect: invoking LLM (prompt length={len(prompt)}) ===")
    response = await llm.ainvoke(messages)
    print(f"=== Architect: LLM responded (length={len(response.content)}) ===")
    
    # 提取 JSON
    content = clean_json_string(response.content)
    
    try:
        plan = json.loads(content)
        if isinstance(plan, dict) and ("summary" in plan or "nodes" in plan):
            print("=== Architect: Plan parsed successfully ===")
            return {"plan": plan, "messages": [response]}
        else:
            print(f"=== Architect: JSON parsed but not a valid plan. Keys: {list(plan.keys()) if isinstance(plan, dict) else 'N/A'} ===")
            return {"error": f"Architect 返回的 JSON 不是有效的 plan", "messages": [response]}
    except json.JSONDecodeError as e:
        print(f"=== Architect: JSON parse error: {e} ===")
        print(f"=== Content preview: {content[:200]} ===")
        return {"error": f"Architect JSON 解析错误: {str(e)}", "messages": [response]}


# ============================================================
# Coder 节点 — 单次 LLM 调用
# ============================================================

async def coder_node(state: AgentState):
    """
    根据 Architect 的方案，生成完整的 n8n 工作流 JSON。
    不使用工具调用，所有参考数据已嵌入 prompt。
    """
    plan = state.get('plan')
    if not plan:
        return {"error": "没有找到 Architect 的方案"}
    
    coder_sys_prompt = get_coder_prompt(state.get('n8n_version', '1.76.1'))
    plan_text = json.dumps(plan, indent=2, ensure_ascii=False)
    
    messages = [
        SystemMessage(content=coder_sys_prompt),
        HumanMessage(content=f"请将以下工作流方案实现为完整的 n8n 工作流 JSON：\n\n{plan_text}")
    ]

    print(f"=== Coder: invoking LLM (system prompt={len(coder_sys_prompt)}, plan={len(plan_text)}) ===")
    response = await llm.ainvoke(messages)
    print(f"=== Coder: LLM responded (length={len(response.content)}) ===")
    
    # 提取 JSON
    content = clean_json_string(response.content)
    
    try:
        parsed_json = json.loads(content)
        print("=== Coder: JSON parsed successfully ===")
        return {"json_result": parsed_json, "messages": [response]}
    except json.JSONDecodeError as e:
        print(f"=== Coder: JSON parse error: {e} ===")
        return {"error": f"Coder JSON 解析错误: {str(e)}", "json_result": None, "messages": [response]}


# ============================================================
# 构建 LangGraph 图
# ============================================================

builder = StateGraph(AgentState)
builder.add_node("architect", architect_node)
builder.add_node("coder", coder_node)

builder.set_entry_point("architect")

# 简单线性流：architect → coder → END
builder.add_edge("architect", "coder")
builder.add_edge("coder", END)

# 内存检查点 — 用于中断恢复
memory = MemorySaver()

# 编译图，在 coder 前中断让用户审查 plan
graph = builder.compile(checkpointer=memory, interrupt_before=["coder"])
