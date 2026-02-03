# Project Journey & Development Log / 项目发展历程与开发日志

## 1. Conception Phase / 构思阶段
- **Initial Idea**: The user encountered an article about n8n + AI but couldn't access it. The discussion shifted towards building an application that automatically generates n8n workflows from natural language.
  **初始想法**：用户尝试访问一篇关于 n8n + AI 的文章失败，讨论转向构建一个能够通过自然语言自动生成 n8n 工作流的应用程序。
- **Feasibility Study**: valid n8n workflows are essentially JSON files with `nodes` and `connections`. We determined that an LLM with access to the correct schema and examples could generate these files.
  **可行性研究**：有效的 n8n 工作流本质上是包含 `nodes` 和 `connections` 的 JSON 文件。我们确定只要 LLM 掌握了正确的 Schema 和示例，就可以生成这些文件。

## 2. Architecture Design / 架构设计
- **Core Strategy**: "Local Knowledge Base" (RAG-lite). Instead of fine-tuning, we provide the LLM with:
  1.  `generation_rules.md`: Strict rules for coordinate calculation and ID generation.
  2.  `templates/*.json`: Real-world working examples (Webhook, Gmail, Feishu, etc.).
  **核心策略**：“本地知识库”（轻量级 RAG）。不进行微调，而是为 LLM 提供：
  1.  `generation_rules.md`：关于坐标计算和 ID 生成的严格规则。
  2.  `templates/*.json`：真实可用的工作流示例（Webhook, Gmail, 飞书等）。
- **Tech Stack / 技术栈**:
  - **Backend**: Python (FastAPI) + LangGraph (for orchestration).
  - **Frontend**: Next.js + Tailwind CSS (Planned).
  - **Model**: Support for OpenAI, Anthropic, and Custom Providers (SiliconFlow/DeepSeek).

## 3. Implementation Steps / 实施步骤
### Phase 1: Knowledge Base Setup / 知识库搭建
- Created `reference/n8n/templates` and fetched reference JSONs from GitHub.
- Analyzed templates to create `generation_rules.md` (Bilingual).
  创建了 `reference` 目录并抓取了 GitHub 上的模板，分析后编写了生成规则文档。

### Phase 2: Backend Development / 后端开发
- Initialized project at `g:\github\n8n-workflow-generator`.
- Implemented `backend/agent/graph.py`: A LangGraph agent that loads rules and prompts the LLM.
- Implemented `backend/main.py`: A FastAPI endpoint `/generate`.
  初始化项目，并实现了能够加载规则、提示 LLM 生成 JSON 的 LangGraph Agent 以及 FastAPI 接口。

### Phase 3: Custom Model Support / 自定义模型支持
- Configured `.env` to support `OPENAI_BASE_URL` and `OPENAI_MODEL`.
- Successfully integrated SiliconFlow (DeepSeek-V3.2).
  配置了环境变量以支持自定义 OpenAI 兼容接口，成功接入硅基流动 (DeepSeek)。

### Phase 4: Format Debugging / 格式调试
- **Issue**: The API initially returned a wrapped JSON (`{ "status": "success", "workflow": ... }`), which n8n could not import directly.
- **Fix**: Refactored `main.py` to return the raw `workflow` object directly. Use verified the fix.
  **问题**：API 最初返回包裹后的 JSON，导致 n8n 无法直接导入。
  **修复**：重构代码，直接返回原始 `workflow` 对象，用户验证通过。

## 4. Current Status / 当前状态
- **Backend**: Functional. Can generate valid n8n JSONs via Swagger UI.
- **Frontend**: Initialized (Next.js) but not yet connected to backend.
- **Next Steps**: Build the Chat UI and Visualization in Frontend.
  **后端**：功能正常，可通过 Swagger UI 生成。
  **前端**：已初始化但尚未对接。
  **下一步**：构建聊天界面和可视化预览。
