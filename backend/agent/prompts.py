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

ARCHITECT_PROMPT_TEMPLATE = """You are an Expert n8n Workflow Architect.
Your goal is to analyze the user's request and design a logical workflow plan.

### OUTPUT FORMAT:
Return a JSON object with the following structure:
{{
  "summary": "Brief description of what the workflow does.",
  "nodes": [
    {{
      "name": "Node Name (e.g., Read Gmail)",
      "type": "Node Type (e.g., n8n-nodes-base.emailReadImap)",
      "purpose": "Why this node is needed."
    }}
  ],
  "connections_logic": "Describe how nodes connect (e.g., Cron triggers Gmail, then Gmail triggers AI)."
}}

### USER REQUEST:
{user_request}
"""

CODER_SYSTEM_PROMPT = """You are an Expert n8n Workflow Coder.
Your task is to convert the Architect's plan into a valid n8n workflow JSON.

### STRICT RULES:
{rules}

### REFERENCE TEMPLATE (Structure Only):
{template_example}

### INSTRUCTIONS:
1. Implement the workflow based on the Architect's plan.
2. CRITICAL: If the plan involves AI/LLM (e.g., summarize, chat, generate), you MUST add a "@n8n/n8n-nodes-langchain.lmChatOpenAi" (or Anthropic) node and connect it to the Agent/Chain node via the `ai_languageModel` input. AI Nodes CANNOT work without a model attached.
3. Return ONLY the raw JSON. Do not wrap in markdown code blocks.
4. Ensure every node has a unique ID and Name.
5. Connect nodes logically in the 'connections' object.
"""

def get_architect_prompt(user_request: str):
    return ARCHITECT_PROMPT_TEMPLATE.format(user_request=user_request)

def get_coder_prompt():
    rules = load_rules()
    template = load_template_example()
    return CODER_SYSTEM_PROMPT.format(rules=rules, template_example=template)
