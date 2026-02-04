import os
from pathlib import Path

BASE_DIR = Path("g:/github/n8n-workflow-generator")
REFERENCE_DIR = BASE_DIR / "reference/n8n"

def load_rules():
    rule_path = REFERENCE_DIR / "generation_rules.md"
    if rule_path.exists():
        return rule_path.read_text(encoding="utf-8")
    return "No rules found."

def load_template_example():
    template_path = REFERENCE_DIR / "templates/daily_email_digest.json"
    if template_path.exists():
        return template_path.read_text(encoding="utf-8")
    return "{}"

def load_knowledge():
    knowledge_path = BASE_DIR / "reference/knowledge/providers.json"
    if knowledge_path.exists():
        return knowledge_path.read_text(encoding="utf-8")
    return "{}"

ARCHITECT_PROMPT_TEMPLATE = """You are an Expert n8n Workflow Architect.
Your goal is to analyze the user's request and design a logical workflow plan.

### KNOWLEDGE BASE (Email Providers & Decision Logic):
Use this to choose the correct node type (e.g., Gmail vs IMAP) and authentication strategy.
{knowledge}

### OUTPUT FORMAT:
Return a JSON object with the following structure:
{{
  "summary": "Brief description...",
  "questions_to_user": ["List of clarifying questions if deployment info is missing (e.g. 'Is your n8n on HTTPS?')"],
  "nodes": [
    {{
      "name": "Node Name",
      "type": "Node Type (e.g., n8n-nodes-base.gmail)",
      "purpose": "Why this node?",
      "notes": "Specific config notes (e.g. 'Use OAuth2')"
    }}
  ],
  "connections_logic": "Describe connections..."
}}

### USER REQUEST:
{user_request}
"""

def load_patterns():
    pattern_dir = REFERENCE_DIR / "patterns"
    if not pattern_dir.exists():
        return ""
    
    patterns = []
    for file in pattern_dir.glob("*.json"):
        content = file.read_text(encoding="utf-8")
        patterns.append(f"--- PATTERN: {file.name} ---\n{content}")
    
    return "\n\n".join(patterns)

CODER_SYSTEM_PROMPT = """You are an Expert n8n Workflow Coder.
Your task is to convert the Architect's plan into a valid n8n workflow JSON.

### STRICT RULES:
{rules}

### REFERENCE PATTERNS (Gold Standards):
Use these patterns to understand how to correctly connect complex nodes (especially AI Agents, Models, and Loops).
{patterns}

### REFERENCE TEMPLATE (Structure Only):
{template_example}

### INSTRUCTIONS:
1. Implement the workflow based on the Architect's plan.
2. CRITICAL: If the plan involves AI/LLM (e.g., summarize, chat, generate), you MUST add a "@n8n/n8n-nodes-langchain.lmChatOpenAi" (or Anthropic) node and connect it to the Agent/Chain node via the `ai_languageModel` input. AI Nodes CANNOT work without a model attached. Refer to the 'webhook_ai_agent.json' pattern above.
3. Return ONLY the raw JSON. Do not wrap in markdown code blocks.
4. Ensure every node has a unique ID and Name.
5. Connect nodes logically in the 'connections' object.
"""

def get_architect_prompt(user_request: str):
    knowledge = load_knowledge()
    return ARCHITECT_PROMPT_TEMPLATE.format(user_request=user_request, knowledge=knowledge)

def get_coder_prompt():
    rules = load_rules()
    template = load_template_example()
    patterns = load_patterns()
    return CODER_SYSTEM_PROMPT.format(rules=rules, template_example=template, patterns=patterns)
