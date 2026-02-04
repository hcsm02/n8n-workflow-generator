# 技术路线图：n8n Agent 知识工程与演进策略

本文档概述了将 AI Agent 从简单的"JSON生成器"进化为"资深 n8n 工程师"的战略规划。核心思想是从"规则驱动"转向"知识检索增强 (RAG)"与"模板优先"策略。

## 1. 核心设计理念 (Core Philosophy)
代码生成的上限取决于其背后的领域知识。为了实现生产级可用性，我们必须构建一个覆盖**服务能力**、**架构范式**和**运行环境**的结构化知识库，并优先采用经验证的模板。

## 2. 知识体系架构 (Knowledge Architecture)

我们将建设三层知识库：

### 第一层：服务能力 (Service Capabilities)
*定义：关于外部服务的静态知识（认证方式、API限制、最佳实践）。*

| 领域 | 文件位置 | 内容示例 | 状态 |
| :--- | :--- | :--- | :--- |
| **邮件** | `knowledge/providers.json` | Gmail OAuth 对比 IMAP 配置，SSL 端口要求。 | ✅ 已完成 |
| **大模型** | `knowledge/models.json` | OpenAI/Anthropic/DeepSeek 参数差异，Function Calling 支持情况。 | 待办 |
| **数据库** | `knowledge/databases.json` | Postgres vs MySQL 连接串格式，SSL 要求，Upsert 逻辑差异。 | 待办 |
| **消息** | `knowledge/messaging.json` | Slack (Token vs Webhook), Discord (Intents), Teams 限制。 | 待办 |

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

### 第一阶段：基础设施 (已完成)
- [x] 建立知识库目录结构。
- [x] 注入邮件服务商知识 (`providers.json`)。
- [x] 注入基础 AI 范式 (`webhook_ai_agent.json`)。
- [x] 更新 Architect Agent 以支持查阅知识库。
- [x] 更新 Coder Agent 以支持参考范式代码。

### 第二阶段：高频场景攻坚 (优先级：高)
- [ ] **LLM 模型知识**: 创建 `knowledge/models.json`，让 Architect 能根据任务复杂度选择模型（如：简单总结用 mini，复杂逻辑用 sonnet）。
- [ ] **数据流处理**: 创建 `patterns/loop_pagination.json`，解决 50% 以上工作流都会遇到的列表处理和分页问题。

### 第三阶段：环境感知 (优先级：中)
- [ ] **上下文注入**: 更新 Architect Prompt 读取 `user_profile.json`。
- [ ] **自愈与纠错**: 如果用户表示"我是 Docker 部署且无 HTTPS"，自动排除 OAuth 类节点方案。

### 第四阶段：模板优先策略 (Template-First Strategy)
*核心逻辑：与其从零生成，不如基于成熟方案修改。*

**1. 模板库建设 (`reference/templates/`)**
按业务场景通过文件夹组织模板：
- `productivity/` (日报, 会议纪要)
- `marketing/` (线索评分, 社交媒体发布)
- `devops/` (故障报警, 数据库备份)

**2. 检索逻辑升级**
Architect Agent 的第一步动作改为 **"相似度检索"**：
1.  **用户请求**: "帮我做一个每天发天气预报邮件的工作流"。
2.  **检索**: 在 `reference/templates/**` 中向量搜索。
3.  **结果**: 找到 `daily_email_digest.json` (相似度 0.85)。
4.  **决策**: 指挥 Coder *"加载 'daily_email_digest.json' 模板，将其中的 'Gmail' 节点替换为 'Weather API' 节点"*。

**收益**: 从根本上保证了工作流骨架的正确性。

---

## 4. 集成与交互策略

- **Architect (架构师)**:
    1.  优先执行 **模板检索 (Phase 4)**。
    2.  若命中模板 -> 执行 **"修改/适配策略"**。
    3.  若未命中 -> 执行 **"组合生成策略"** (查询 Layer 1 & 2)。
    4.  始终查询 **Layer 3 (环境)** 进行可行性预检。
- **Coder (工程师)**:
    - 负责细节参数填充，并在需要时查询 **Layer 2 (范式)** 补充代码片段。

这种分离确保了架构师专注于"做正确的决定"，而工程师专注于"把代码写对"。
