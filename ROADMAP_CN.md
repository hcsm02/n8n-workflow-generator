# 技术路线图：n8n Agent 知识工程与演进策略

本文档概述了将 AI Agent 从简单的"JSON生成器"进化为"资深 n8n 工程师"的战略规划。核心思想是从"规则驱动"转向"知识检索增强 (RAG)"与"模板优先"策略。

## 1. 核心设计理念 (Core Philosophy)
代码生成的上限取决于其背后的领域知识。为了实现生产级可用性，我们必须构建一个覆盖**服务能力**、**架构范式**和**运行环境**的结构化知识库，并优先采用经验证的模板。
**【核心基建升级】**：全面拥抱 [n8n-mcp](https://github.com/czlonkowski/n8n-mcp) 生态。不再手工维护脆弱的节点 JSON 配置字典，而是将 n8n-mcp（其内置了由 n8n 源码解析而来的高优离线 SQLite 知识库引擎）深度挂载为底层 Tool，实现**零幻觉节点认知**、**内置 2500+ 模板秒级检索**以及**原生级工作流校验闭环**。

## 2. 知识体系架构 (Knowledge Architecture)

我们将建设三层知识库：

### 第一层：服务能力 (Service Capabilities)
*定义：关于外部服务的静态知识（认证方式、API限制、最佳实践）。*

| 领域 | 获取方式 & 内容示例 | 状态 |
| :--- | :--- | :--- |
| **All Nodes** | **[核心] 直接调用 n8n-mcp 的 `get_node` 工具**。<br>包含全量 1000+ 节点（官方+验证社区）的参数、Type、默认值。彻底消灭“虚构参数”幻觉。 | 待集成 |
| **应用限制** | 基于 n8n-mcp 返回的关键属性（仅 10-20 个核心参数），指导 AI 准确配置 OAuth、API Key 等鉴权字典。 | 待集成 |

### 第二层：架构范式 (Architectural Patterns)
*定义：解决特定问题的标准拓扑结构，防止 AI "臆测"错误的连线。*

| 范式名称 | 文件位置 | 描述 | 状态 |
| :--- | :--- | :--- | :--- |
| **AI Agent** | `patterns/webhook_ai_agent.json` | 标准 Agent + Model + Memory 连线结构。 | ✅ 已完成 |
| **分页循环** | `patterns/loop_pagination.json` | 处理 API 列表数据的标准 Loop/SplitInBatches 结构。 | 待办 |
| **错误处理** | `patterns/error_trigger.json` | 全局 Error Trigger -> 通知流。 | 待办 |
| **RAG 管道** | `patterns/rag_vector_store.json` | Embedding -> Vector Store -> Retrieval -> Generation。 | 待办 |
| **人工审批** | `patterns/human_approval.json` | Wait 节点 + Switch 路由逻辑。 | 待办 |

### 第三层：运行环境 (Runtime Context)
*定义：关于用户特定 n8n 实例的动态知识。*

| 组件 | 文件位置 | 内容 | 状态 |
| :--- | :--- | :--- | :--- |
| **用户画像** | `config/user_profile.json` | 部署方式 (Docker/Cloud), HTTPS 状态, 全局环境变量。 | 待办 |

---

## 3. 实施路线图 (Implementation Roadmap)

### 第一阶段：基础设施 (阶段演进)
- [x] 建立知识库目录结构与双 Agent (Architect & Coder) 协同原型。
- [x] 注入基础 AI 范式 (`webhook_ai_agent.json`) 和手工测试知识。
- [ ] **【重点转向】集成 n8n-mcp**: 将 n8n-mcp 作为底层工具服务运行，为 LangChain Agent 提供 `get_node`, `search_nodes` 接口。替代原有的 `providers.json`。

### 第二阶段：精准构型与测试闭环 (优先级：高)
- [ ] **Validator 审查者引入**: 在 Agent 链路中引入 `validate_workflow` 调用。生成的工作流必须通过 MCP 内置验证器的约束校验（如缺必填项、连线类型不匹配）才能交付。
- [ ] **直连 N8N 调试**: 支持用户输入自己的 `N8N_API_URL` 和 `N8N_API_KEY`，实现 AI 生成 -> API 直推 n8n 草稿箱 -> 执行测试获取 Log -> 动态微调的完整迭代（完成最后 25% 的调教）。

### 第三阶段：环境感知 (优先级：中)
- [ ] **上下文注入**: 更新 Architect Prompt 读取 `user_profile.json`。
- [ ] **自愈与纠错**: 如果用户表示"我是 Docker 部署且无 HTTPS"，自动排除 OAuth 类节点方案。

### 第四阶段：模板优先策略 (Template-First Strategy)
*核心逻辑：与其从零生成，不如基于成熟方案修改。*

### 第四阶段：模板优先策略 (Template-First Strategy)
*核心逻辑：与其从零生成，不如基于成熟方案修改。复杂流程 75% 靠模板，25% 靠微调。*

**检索逻辑升级 (Powered by n8n-mcp)**
Architect Agent 的第一步动作强制改为 **调用 n8n-mcp 检索模板**：
1.  **用户请求**: "帮我做一个每天定时爬取 HackerNews 并发到企业微信的流程。"
2.  **检索 (MCP)**: 调用 `search_templates({ searchMode: 'by_task', task: 'HackerNews' })` 从 MCP 内置的 2500+ 真人验证模板库检索。
3.  **提取**: 找到相关骨架模板，调用 `get_template` 获取。
4.  **决策组装**: 指挥 Coder *"保留抓取逻辑，把输出端节点用 `get_node` 查询企业微信并替换进去"*。

**收益**: 站在官方模板库的肩膀上，从根本上保证了宏观骨架的一发入魂。

---

## 4. 集成与交互策略

- **Architect (架构师)**:
    1.  优先调用 MCP 执行 **模板检索 (Template Discovery)**。
    2.  若命中模板 -> 提取结构，规划 **"节点替换微调策略"**。
    3.  若未命中 -> 调用 MCP 查阅组合节点，规划 **"组合生成策略"**。
    4.  感知 Layer 3 (环境) 进行初步架构评估。
- **Coder (工程师)**:
    - 根据 Architect 给出的蓝图，调用 MCP 的 `get_node_schema` 准确填充参数，组装完整 JSON 流程图。
- **Critic / Validator (审查测试官)** 【新引入层】:
    - 调用 MCP 的 `validate_workflow` 筛查语法与强约束错误。
    - （进阶）推送到用户 n8n 集群运行，分析 Return Server Logs 进行错误回退自修正。

这种分离不仅各司其职，更是完成了 **“生成 -> 校验 -> 反馈优化”** 的高阶智能体闭环。
