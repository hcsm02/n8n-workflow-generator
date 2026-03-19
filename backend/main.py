"""
n8n Workflow Generator — FastAPI 后端

三阶段渐进式生成：
  POST /concept          → Phase 0: 概念建模（逻辑步骤拆解）
  POST /refine-concept   → 用户修改后重新生成逻辑步骤
  POST /confirm-concept  → 确认逻辑步骤，触发节点映射 (Phase 1)
  POST /confirm          → 确认节点方案，触发 JSON 生成 (Phase 2)
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from langchain_core.messages import HumanMessage
from agent.graph import graph
import uuid
import json

app = FastAPI(title="n8n Workflow Generator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# 请求模型
# ============================================================

class ConceptRequest(BaseModel):
    """Phase 0: 概念建模请求"""
    prompt: str
    n8n_version: str = "2.11.4"
    thread_id: Optional[str] = None


class RefineConceptRequest(BaseModel):
    """用户修改逻辑步骤请求"""
    thread_id: str
    feedback: str                           # 用户的修改意见（对话式）
    updated_steps: Optional[List[dict]] = None  # 用户拖拽/删除后的步骤（可选）


class ConfirmConceptRequest(BaseModel):
    """确认逻辑步骤，触发节点映射"""
    thread_id: str
    final_steps: Optional[List[dict]] = None  # 用户最终确认的步骤顺序


class ConfirmRequest(BaseModel):
    """确认节点方案，触发 JSON 生成"""
    thread_id: str
    modifications: Optional[str] = None


# ============================================================
# 健康检查
# ============================================================

@app.get("/")
def health_check():
    return {"status": "ok", "service": "n8n-workflow-generator", "version": "2.0-three-stage"}


# ============================================================
# Phase 0: 概念建模 — 纯逻辑步骤拆解
# ============================================================

@app.post("/concept")
async def create_concept(request: ConceptRequest):
    """
    Phase 0: 将用户需求拆解为高层级逻辑步骤。
    响应极快 (< 5s)，不涉及 n8n 节点。
    """
    print(f"=== /concept: prompt={request.prompt[:50]}... ===")
    thread_id = request.thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    try:
        inputs = {
            "user_request": request.prompt,
            "n8n_version": request.n8n_version,
            "messages": [],
            "interaction_history": "",
        }

        result = graph.invoke(inputs, config=config)

        if result.get("error"):
            raise HTTPException(status_code=500, detail=result["error"])

        return {
            "status": "concept_ready",
            "thread_id": thread_id,
            "concept": result.get("conceptual_steps"),
        }
    except Exception as e:
        print(f"=== /concept error: {e} ===")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# 用户修改逻辑步骤（重新触发概念建模）
# ============================================================

@app.post("/refine-concept")
async def refine_concept(request: RefineConceptRequest):
    """
    用户通过对话或拖拽修改了逻辑步骤后，重新触发概念建模。
    使用新的 thread_id 来避免状态冲突。
    """
    print(f"=== /refine-concept: feedback={request.feedback[:50]}... ===")
    new_thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": new_thread_id}}

    # 构建交互历史
    history_parts = []
    if request.updated_steps:
        history_parts.append(f"用户调整后的步骤顺序：\n{json.dumps(request.updated_steps, ensure_ascii=False, indent=2)}")
    if request.feedback:
        history_parts.append(f"用户的修改意见：{request.feedback}")

    interaction_history = "\n".join(history_parts)

    # 获取原始请求（从旧 thread 的 state 中提取）
    try:
        old_state = graph.get_state({"configurable": {"thread_id": request.thread_id}})
        original_request = old_state.values.get("user_request", "")
    except Exception:
        original_request = request.feedback  # 降级处理

    try:
        inputs = {
            "user_request": original_request,
            "n8n_version": old_state.values.get("n8n_version", "2.11.4") if old_state else "2.11.4",
            "messages": [],
            "interaction_history": interaction_history,
        }

        result = graph.invoke(inputs, config=config)

        if result.get("error"):
            raise HTTPException(status_code=500, detail=result["error"])

        return {
            "status": "concept_ready",
            "thread_id": new_thread_id,
            "concept": result.get("conceptual_steps"),
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"=== /refine-concept error: {e} ===")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# 确认逻辑步骤 → 触发节点映射 (Phase 1)
# ============================================================

@app.post("/confirm-concept")
async def confirm_concept(request: ConfirmConceptRequest):
    """
    用户确认逻辑步骤后，恢复图执行到 architect 节点。
    如果用户提供了 final_steps，则更新 state。
    """
    print(f"=== /confirm-concept: thread_id={request.thread_id} ===")
    config = {"configurable": {"thread_id": request.thread_id}}

    try:
        # 如果用户通过拖拽调整了最终步骤顺序，更新 state
        if request.final_steps:
            current_state = graph.get_state(config)
            concept = current_state.values.get("conceptual_steps", {})
            concept["steps"] = request.final_steps
            graph.update_state(config, {"conceptual_steps": concept})

        # 恢复图执行（从 architect 中断点继续）
        result = graph.invoke(None, config=config)

        if result.get("error"):
            raise HTTPException(status_code=500, detail=result["error"])

        return {
            "status": "plan_ready",
            "thread_id": request.thread_id,
            "plan": result.get("plan"),
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"=== /confirm-concept error: {e} ===")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# 确认节点方案 → 触发 JSON 生成 (Phase 2)
# ============================================================

@app.post("/confirm")
async def confirm_and_generate(request: ConfirmRequest):
    """
    用户确认节点方案后，恢复图执行到 coder 节点生成最终 JSON。
    """
    print(f"=== /confirm: thread_id={request.thread_id} ===")
    config = {"configurable": {"thread_id": request.thread_id}}

    try:
        result = graph.invoke(None, config=config)

        if result.get("error"):
            raise HTTPException(status_code=500, detail=result["error"])

        json_result = result.get("json_result")

        # Fallback
        if not json_result and result.get("plan"):
            plan = result["plan"]
            if isinstance(plan, dict) and "nodes" in plan and "connections" in plan:
                json_result = plan

        return json_result
    except Exception as e:
        print(f"=== /confirm error: {e} ===")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
