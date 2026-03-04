"""
Prompt 模板文件

将缓存的参考数据（规则、模板摘要、节点模式）直接嵌入 LLM prompt，
让 Architect/Coder 在一次性调用中就能获得所有必要信息。
支持根据 n8n 版本选择兼容的节点类型和版本号。
"""
from agent.mcp_client import mcp_client

# ============================================================
# 版本兼容性信息 — 根据 n8n 版本决定节点选择
# ============================================================

VERSION_NODE_GUIDANCE = """
### n8n 版本兼容性（用户版本: {n8n_version}）

#### 重要：你必须只使用与用户 n8n 版本兼容的节点类型和 typeVersion！

#### 通用安全节点（所有版本均支持）：
| 节点类型 | typeVersion | 用途 |
|---------|------------|------|
| n8n-nodes-base.scheduleTrigger | 1.2 | 定时触发（替代已废弃的 cron） |
| n8n-nodes-base.set | 3.4 | 设置/转换数据字段 |
| n8n-nodes-base.if | 2 | 条件判断分支 |
| n8n-nodes-base.httpRequest | 4.2 | HTTP 请求 |
| n8n-nodes-base.code | 2 | 自定义 JavaScript/Python 代码 |
| n8n-nodes-base.merge | 3 | 合并多个输入流 |
| n8n-nodes-base.splitInBatches | 3 | 分批处理 |
| n8n-nodes-base.noOp | 1 | 空操作（占位/调试用） |

#### 常见服务节点：
| 节点类型 | typeVersion | 用途 |
|---------|------------|------|
| n8n-nodes-base.gmail | 2.1 | Gmail 操作（发送/读取邮件） |
| n8n-nodes-base.gmailTrigger | 1.3 | Gmail 新邮件触发器 |
| n8n-nodes-base.slack | 2.4 | Slack 消息操作 |
| n8n-nodes-base.rssFeedRead | 1 | RSS 订阅源读取 |
| n8n-nodes-base.emailSend | 2.1 | SMTP 发送邮件 |
| n8n-nodes-base.emailReadImap | 2 | IMAP 读取邮件 |

#### 已废弃节点（请勿使用！）：
| 已废弃 | 替代方案 |
|-------|---------|
| n8n-nodes-base.cron | 使用 n8n-nodes-base.scheduleTrigger |
| n8n-nodes-base.function | 使用 n8n-nodes-base.code |
| n8n-nodes-base.functionItem | 使用 n8n-nodes-base.code |

#### 使用规则：
1. 只使用上表中列出的节点，或你确信在 v{n8n_version} 中存在的节点。
2. 不要使用 generateHtmlTemplate 等自定义/不标准操作 —— 用 n8n-nodes-base.code 节点替代。
3. typeVersion 必须使用上表中指定的数字。
4. 如果不确定某个节点是否可用，使用 n8n-nodes-base.httpRequest 或 n8n-nodes-base.code 作为通用替代。
"""

# ============================================================
# Architect Prompt — 分析用户需求，设计工作流方案
# ============================================================

ARCHITECT_PROMPT_TEMPLATE = """你是一位 n8n 工作流架构师 (Architect)。
你的任务是分析用户的自动化需求，设计出精确的工作流方案。

{version_guidance}

### 你已有的参考知识

#### 已有模板（可直接参考或改造）：
{templates_summary}

#### n8n 工作流生成规则：
{rules}

### 工作指令：
1. 仔细分析用户的需求，确定需要哪些 n8n 节点。
2. 只使用与用户 n8n 版本 v{n8n_version} 兼容的节点。
3. 如果上面的模板中有相似的，直接参考其节点组合。
4. 为每个节点说明其用途和关键配置。
5. 如果需要额外信息才能完成设计，将问题列入 questions_to_user。

### 输出规则（必须严格遵守）：
- 你的回复必须且只能是一个 JSON 对象，不能包含任何其他文字。
- 不要用 markdown 代码块包裹。
- JSON 必须以 {{ 开头，以 }} 结尾。

### JSON 格式：
{{
  "summary": "工作流描述（中文）",
  "questions_to_user": ["如有需要澄清的问题，列在这里"],
  "nodes": [
    {{
      "name": "节点名称",
      "type": "n8n-nodes-base.xxx",
      "typeVersion": 1,
      "purpose": "节点用途",
      "notes": "关键配置说明"
    }}
  ],
  "connections_logic": "节点之间的连接逻辑描述"
}}

### 用户需求：
{user_request}
"""

# ============================================================
# Coder Prompt — 根据方案生成完整的 n8n 工作流 JSON
# ============================================================

CODER_SYSTEM_PROMPT = """你是一位 n8n 工作流编码专家 (Coder)。
你的任务是将 Architect 的设计方案转换为完整的、可直接导入 n8n v{n8n_version} 的工作流 JSON。

{version_guidance}

### 严格规则：
{rules}

### 参考模式（金标准示例）：
{patterns}

### 工作指令：
1. 严格按照 Architect 的方案实现每个节点。
2. 每个节点必须有唯一的 id（UUID 格式）和 name。
3. typeVersion 必须使用版本兼容表中指定的数字。
4. connections 对象必须正确定义所有节点间的连接。
5. credentials 使用占位符（如 YOUR_CREDENTIAL_ID），不要生成实际密钥。
6. 不要使用任何已废弃的节点类型。

### 输出规则（必须严格遵守）：
- 你的回复必须且只能是一个完整的 n8n 工作流 JSON 对象。
- 不要包含任何解释、说明、markdown 代码块或其他文字。
- JSON 必须以 {{ 开头，以 }} 结尾。
- 必须包含 name, nodes, connections, settings 字段。
"""


def get_architect_prompt(user_request: str, n8n_version: str = "1.76.1") -> str:
    """构建 Architect 的完整 prompt，嵌入缓存的参考数据和版本信息"""
    version_guidance = VERSION_NODE_GUIDANCE.format(n8n_version=n8n_version)
    return ARCHITECT_PROMPT_TEMPLATE.format(
        version_guidance=version_guidance,
        templates_summary=mcp_client.templates_summary or "（暂无模板数据）",
        rules=mcp_client.rules or "（暂无规则数据）",
        n8n_version=n8n_version,
        user_request=user_request
    )


def get_coder_prompt(n8n_version: str = "1.76.1") -> str:
    """构建 Coder 的完整 prompt，嵌入缓存的参考数据和版本信息"""
    version_guidance = VERSION_NODE_GUIDANCE.format(n8n_version=n8n_version)
    return CODER_SYSTEM_PROMPT.format(
        n8n_version=n8n_version,
        version_guidance=version_guidance,
        rules=mcp_client.rules or "（暂无规则数据）",
        patterns=mcp_client.patterns or "（暂无模式数据）"
    )
