"""
LangGraph 工作流图定义 — 三阶段渐进式工作流生成

流程：
  concept_architect → (interrupt: 用户审核/修改逻辑步骤)
                    → architect → (interrupt: 用户审核节点方案)
                    → coder → END

Phase 0 (concept_architect): 纯逻辑拆解，极快响应
Phase 1 (architect): 节点映射 + 模板参考
Phase 2 (coder): 生成最终 JSON
"""
import os
import json
import re
import uuid
import sqlite3
from typing import TypedDict, Any, Optional, List
from dotenv import load_dotenv

load_dotenv()

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver

from agent.prompts import get_concept_prompt, get_architect_prompt, get_coder_prompt
from agent.mcp_client import mcp_client


class AgentState(TypedDict):
    messages: list
    user_request: str
    n8n_version: str
    # Phase 0: 概念建模
    conceptual_steps: Optional[dict]       # AI 生成的逻辑步骤
    interaction_history: Optional[str]     # 用户修改历史（对话式）
    # Phase 1: 节点映射
    plan: Optional[dict]
    # Phase 2: JSON 生成
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
    1. 找所有 Markdown 代码块，只保留以 { 开头的
    2. 对每个候选块尝试 json.loads 验证
    3. 如果代码块都不行，从全文中提取最外层 { ... }
    """
    # 策略1：查找所有 Markdown 代码块
    all_blocks = re.findall(r'```(?:json|JSON)?\s*\n?(.*?)```', content, re.DOTALL)
    json_blocks = [b.strip() for b in all_blocks if b.strip().startswith('{')]

    if json_blocks:
        plan_blocks = [b for b in json_blocks if '"summary"' in b or '"nodes"' in b or '"steps"' in b]
        candidates = plan_blocks if plan_blocks else json_blocks
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
# Phase 0: Concept Architect 节点 — 纯逻辑步骤拆解
# ============================================================

def concept_architect_node(state: AgentState):
    """
    将用户需求拆解为高层级逻辑步骤。
    不涉及 n8n 节点，响应极快。
    """
    user_request = state.get('user_request', '')
    interaction_history = state.get('interaction_history', '')
    prompt = get_concept_prompt(user_request, interaction_history)

    messages = [
        SystemMessage(content=prompt),
        HumanMessage(content=user_request)
    ]

    print(f"=== Concept Architect: invoking LLM (prompt length={len(prompt)}) ===")
    response = llm.invoke(messages)
    print(f"=== Concept Architect: LLM responded (length={len(response.content)}) ===")

    content = clean_json_string(response.content)

    try:
        concept = json.loads(content)
        if isinstance(concept, dict) and "steps" in concept:
            print(f"=== Concept Architect: {len(concept['steps'])} steps parsed ===")
            return {"conceptual_steps": concept, "messages": [response]}
        else:
            return {"error": "概念建模返回的 JSON 无效", "messages": [response]}
    except json.JSONDecodeError as e:
        print(f"=== Concept Architect: JSON parse error: {e} ===")
        return {"error": f"概念建模 JSON 解析错误: {str(e)}", "messages": [response]}


# ============================================================
# Phase 1: Technical Architect 节点 — 节点映射
# ============================================================

def architect_node(state: AgentState):
    """
    将用户确认的逻辑步骤映射为 n8n 节点方案。
    此时才参考模板和版本信息。
    """
    conceptual_steps = state.get('conceptual_steps')
    if not conceptual_steps:
        return {"error": "没有找到已确认的逻辑步骤"}

    n8n_version = state.get('n8n_version', '1.76.1')
    steps_text = json.dumps(conceptual_steps, indent=2, ensure_ascii=False)
    prompt = get_architect_prompt(steps_text, n8n_version)

    messages = [
        SystemMessage(content=prompt),
        HumanMessage(content=f"请将以下逻辑步骤映射为 n8n 节点方案：\n\n{steps_text}")
    ]

    print(f"=== Architect: invoking LLM (prompt length={len(prompt)}) ===")
    response = llm.invoke(messages)
    print(f"=== Architect: LLM responded (length={len(response.content)}) ===")

    content = clean_json_string(response.content)

    try:
        plan = json.loads(content)
        if isinstance(plan, dict) and ("summary" in plan or "nodes" in plan):
            print("=== Architect: Plan parsed successfully ===")
            return {"plan": plan, "messages": [response]}
        else:
            return {"error": "Architect 返回的 JSON 不是有效的 plan", "messages": [response]}
    except json.JSONDecodeError as e:
        print(f"=== Architect: JSON parse error: {e} ===")
        return {"error": f"Architect JSON 解析错误: {str(e)}", "messages": [response]}


# ============================================================
# Phase 2: Coder 节点 — 生成最终 JSON
# ============================================================

def coder_node(state: AgentState):
    """
    根据 Architect 的方案，生成完整的 n8n 工作流 JSON。
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
    response = llm.invoke(messages)
    print(f"=== Coder: LLM responded (length={len(response.content)}) ===")

    content = clean_json_string(response.content)

    try:
        parsed_json = json.loads(content)
        print("=== Coder: JSON parsed successfully ===")
        return {"json_result": parsed_json, "messages": [response]}
    except json.JSONDecodeError as e:
        print(f"=== Coder: JSON parse error: {e} ===")
        return {"error": f"Coder JSON 解析错误: {str(e)}", "json_result": None, "messages": [response]}


# ============================================================
# 构建 LangGraph 图 — 三阶段流程
# ============================================================

builder = StateGraph(AgentState)
builder.add_node("concept_architect", concept_architect_node)
builder.add_node("architect", architect_node)
builder.add_node("coder", coder_node)

builder.set_entry_point("concept_architect")

# 线性流：concept_architect → architect → coder → END
builder.add_edge("concept_architect", "architect")
builder.add_edge("architect", "coder")
builder.add_edge("coder", END)

# 内存检查点 — 用于中断恢复 (已改为 SQLite 持久化)
# 注意：在生产环境建议使用更复杂的连接管理
db_path = "checkpoints.sqlite"
conn = sqlite3.connect(db_path, check_same_thread=False)
memory = SqliteSaver(conn)

# 编译图，在 architect 和 coder 前分别添加中断：
# - architect 前中断：让用户审核/修改逻辑步骤
# - coder 前中断：让用户审核节点方案
graph = builder.compile(
    checkpointer=memory,
    interrupt_before=["architect", "coder"]
)
