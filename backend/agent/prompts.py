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
    # Load a representative example (first 50 lines to save tokens, or full if needed)
    template_path = REFERENCE_DIR / "templates/daily_email_digest.json"
    if template_path.exists():
        return template_path.read_text(encoding="utf-8")
    return "{}"

SYSTEM_PROMPT_TEMPLATE = """You are an expert n8n workflow generator. Your task is to convert the user's natural language request into a valid n8n workflow JSON.

### STRICT RULES:
{rules}

### REFERENCE TEMPLATE (Structure Only):
{template_example}

### INSTRUCTIONS:
1. Return ONLY the raw JSON. Do not wrap in markdown code blocks.
2. Ensure every node has a unique ID and Name.
3. Connect nodes logically in the 'connections' object.
4. Use standard node types (e.g., 'n8n-nodes-base.webhook', 'n8n-nodes-base.httpRequest').
"""

def get_system_prompt():
    rules = load_rules()
    template = load_template_example()
    return SYSTEM_PROMPT_TEMPLATE.format(rules=rules, template_example=template)
