# Technology Roadmap: Knowledge Engineering & Evolution Strategy for n8n Agent

This document outlines the strategic plan to evolve the AI Agent from a simple "JSON Generator" into a "Senior n8n Engineer". The core philosophy is to shift from "Rule-Based Generation" to "Retrieval-Augmented Generation (RAG)" and a "Template-First" strategy.

## 1. Core Philosophy
The ceiling of code generation is defined by the domain knowledge behind it. To achieve production-grade reliability, we must build a structured knowledge base covering **Service Capabilities**, **Architectural Patterns**, and **Runtime Context**, prioritizing proven templates over scratch generation.

## 2. Knowledge Architecture

We will build a three-layer knowledge base:

### Layer 1: Service Capabilities
*Definition: Static knowledge about external services (Auth methods, API constraints, Best Practices).*

| Domain | File Location | Content Examples | Status |
| :--- | :--- | :--- | :--- |
| **Email** | `knowledge/providers.json` | Gmail OAuth vs IMAP configs, SSL port requirements. | ✅ Done |
| **LLM** | `knowledge/models.json` | OpenAI/Anthropic/DeepSeek param differences, Function Calling support. | To Do |
| **Databases** | `knowledge/databases.json` | Postgres vs MySQL connection strings, SSL requirements, Upsert logic. | To Do |
| **Messaging** | `knowledge/messaging.json` | Slack (Token vs Webhook), Discord (Intents), Teams constraints. | To Do |

### Layer 2: Architectural Patterns
*Definition: Standard topological structures for solving specific problems, preventing AI from "hallucinating" invalid connections.*

| Pattern Name | File Location | Description | Status |
| :--- | :--- | :--- | :--- |
| **AI Agent** | `patterns/webhook_ai_agent.json` | Standard Agent + Model + Memory wiring. | ✅ Done |
| **Pagination Loop** | `patterns/loop_pagination.json` | Standard Loop/SplitInBatches structure for API lists. | To Do |
| **Error Handling** | `patterns/error_trigger.json` | Global Error Trigger -> Notification flow. | To Do |
| **RAG Pipeline** | `patterns/rag_vector_store.json` | Embedding -> Vector Store -> Retrieval -> Generation. | To Do |
| **Human Approval** | `patterns/human_approval.json` | Wait Node + Switch routing logic. | To Do |

### Layer 3: Runtime Context
*Definition: Dynamic knowledge about the user's specific n8n instance.*

| Component | File Location | Content | Status |
| :--- | :--- | :--- | :--- |
| **User Profile** | `config/user_profile.json` | Deployment type (Docker/Cloud), HTTPS status, Global Env Vars. | To Do |

---

## 3. Implementation Roadmap

### Phase 1: Foundation (Completed)
- [x] Established Knowledge Base directory structure.
- [x] Injected Email Provider Knowledge (`providers.json`).
- [x] Injected Basic AI Pattern (`webhook_ai_agent.json`).
- [x] Updated Architect Agent to query Knowledge Base.
- [x] Updated Coder Agent to reference Pattern Code.

### Phase 2: High-Frequency Domains (Priority: High)
- [ ] **LLM Knowledge**: Create `knowledge/models.json` to enable Architect to select models based on task complexity (e.g., mini for summary, sonnet for logic).
- [ ] **Data Processing**: Create `patterns/loop_pagination.json` to solve the #1 business requirement: processing lists/rows without data loss.

### Phase 3: Environment Awareness (Priority: Medium)
- [ ] **Context Injection**: Update Architect Prompt to read `user_profile.json`.
- [ ] **Self-Correction**: Automatically rule out OAuth nodes if user environment (e.g., Docker without HTTPS) doesn't support it.

### Phase 4: Template-First Strategy
*Core Logic: Don't generate from scratch if you can modify a proven solution.*

**1. Template Library Construction (`reference/templates/`)**
Organize templates by business scenario:
- `productivity/` (Daily Digest, Meeting Notes)
- `marketing/` (Lead Scoring, Social Posting)
- `devops/` (Error Alerting, DB Backups)

**2. Retrieval Logic Upgrade**
The Architect Agent's first action becomes **"Similarity Search"**:
1.  **User Request**: "Build a workflow to email me a daily weather report."
2.  **Search**: Vector search in `reference/templates/**`.
3.  **Result**: Found `daily_email_digest.json` (Similarity 0.85).
4.  **Decision**: Instruct Coder: *"Load template 'daily_email_digest.json' and replace 'Gmail' node with 'Weather API' node."*

**Benefit**: Fundamentally guarantees the correctness of the workflow skeleton.

---

## 4. Integration & Interaction Strategy

- **Architect**:
    1.  Prioritize **Template Search (Phase 4)**.
    2.  If Template Match -> Execute **"Adaptation Strategy"**.
    3.  If No Match -> Execute **"Composition Strategy"** (Query Layer 1 & 2).
    4.  Always query **Layer 3 (Context)** for feasibility pre-checks.
- **Coder**:
    - Responsible for detailed parameter filling and querying **Layer 2 (Pattern)** for code snippets when needed.

This separation ensures the Architect focuses on "making the right decisions" while the Coder focuses on "writing the correct code".
