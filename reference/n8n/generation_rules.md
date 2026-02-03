# n8n Workflow Generation Rules / n8n 工作流生成规则

## 1. High-Level Structure / 高层结构
A valid n8n workflow JSON must have the following root properties:
有效的 n8n 工作流 JSON 必须包含以下根属性：

```json
{
  "name": "My Workflow",
  "nodes": [ ... ],
  "connections": { ... },
  "settings": { "executionOrder": "v1" }
}
```

## 2. Nodes Array / 节点数组
Each item in `nodes` represents a functional step.
`nodes` 中的每一项代表一个功能步骤。

### Required Fields / 必填字段
- `id`: unique UUID (e.g. `47d7b2cb-5d44-4625-aeab-33e0b7ce529f`).
  唯一 UUID。
- `name`: unique human-readable name (e.g. "Webhook Trigger"). Used in `connections`.
  唯一可读名称，用于 `connections` 中引用。
- `type`: internal node identifier (e.g. `n8n-nodes-base.webhook` or `@n8n/n8n-nodes-langchain.agent`).
  内部节点标识符。
- `typeVersion`: integer (usually 1, check specific node requirements).
  整型版本号（通常为 1）。
- `position`: `[x, y]` array coordinates. Standard spacing is ~200px horizontal, ~100px vertical steps.
  `[x, y]` 数组坐标。标准间距为水平 200px，垂直 100px。
- `parameters`: Object containing node-specific configuration.
  包含特定节点配置的对象。

### Common Node Types / 常见节点类型
- **Trigger (触发器)**: `n8n-nodes-base.webhook`, `n8n-nodes-base.cron`, `n8n-nodes-base.emailReadImap`.
- **Action (动作)**: `n8n-nodes-base.googleSheets`, `n8n-nodes-base.httpRequest`, `n8n-nodes-base.set`.
- **AI/LangChain**:
  - Agent: `@n8n/n8n-nodes-langchain.agent`
  - Model: `@n8n/n8n-nodes-langchain.lmChatAnthropic`, `@n8n/n8n-nodes-langchain.lmChatOpenAi`
  - Memory: `@n8n/n8n-nodes-langchain.memoryBufferWindow`
  - Tool: `@n8n/n8n-nodes-langchain.toolVectorStore`

## 3. Connections Object / 连接对象
Defines the graph topology. Keys are **Source Node Names**.
定义图的拓扑结构。键为 **源节点名称 (Source Node Name)**。

### Standard Connections (Linear Flow) / 标准连接（线性流）
Used for passing data execution flow.
用于传递数据执行流。

```json
"Source Node Name": {
  "main": [
    [
      { "node": "Destination Node Name", "type": "main", "index": 0 }
    ]
  ]
}
```

### AI/LangChain Connections (Reference Flow) / AI/LangChain 连接（引用流）
Used for attaching capabilities (Memory, Tools, Models) to an Agent. These are NOT `main` connections.
用于将能力（记忆、工具、模型）附加到 Agent 上。这些 **不是** `main` 连接。

- **Model -> Agent**: `ai_languageModel`
- **Memory -> Agent**: `ai_memory`
- **Tool -> Agent**: `ai_tool`
- **Embedding -> Vector Store**: `ai_embedding`

**Example (Chat Model attached to Agent):**
```json
"Chat Model": {
  "ai_languageModel": [
    [
      { "node": "RAG Agent", "type": "ai_languageModel", "index": 0 }
    ]
  ]
}
```

## 4. Positioning Strategy / 布局策略
- Start Trigger at `[0, 0]`.
  触发器起始于 `[0, 0]`。
- Propagate linear steps by adding `+220` to X.
  线性步骤 X 轴递增 220。
- For AI Agents, place the Agent node centrally.
  对于 AI Agent，将其居中放置。
  - Place Models/Memory to the LEFT or TOP of the Agent.
    模型/记忆放在 Agent 的左侧或上方。
  - Place Tools to the LEFT or BOTTOM of the Agent.
    工具放在 Agent 的左侧或下方。
  - Verify no overlap.
    确保不重叠。

## 5. Metadata & Credentials / 元数据与凭证
- Do NOT generate `credentials` blocks with actual secrets. Use references like:
  **不要** 生成包含实际密钥的 `credentials` 块。使用如下引用：

```json
"credentials": {
  "googleSheetsOAuth2Api": { "id": "SHEETS_API", "name": "Google Sheets account" }
}
```
- The generic `id` allows the user to map it to their actual credential ID in the n8n UI.
  用户可以在 n8n UI 中将此通用 `id` 映射到实际凭证。
