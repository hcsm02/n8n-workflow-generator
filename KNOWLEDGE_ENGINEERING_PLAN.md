# Knowledge Engineering Plan: Building the "Brain" of the n8n Agent / n8n Agent 知识工程计划

## 1. Core Philosophy / 核心理念
Code generation is only as good as the domain knowledge behind it. To move from "rendering JSON" to "intelligent engineering", we must build a structured knowledge base that covers **Service Capabilities**, **Architectural Patterns**, and **Runtime Context**.

## 2. Knowledge System Architecture / 知识体系架构

### Layer 1: Service Capabilities (The "What" & "How")
*Static knowledge about external services: Auth methods, API constraints, and best practices.*

| Domain | File | Content Examples |
| :--- | :--- | :--- |
| **Email** | `knowledge/providers.json` | Gmail OAuth vs IMAP, SSL ports, App Passwords. (✅ Started) |
| **LLM** | `knowledge/models.json` | OpenAI/Anthropic/Ollama config differences, Context Window sizes, Function Calling support. |
| **Databases** | `knowledge/databases.json` | Postgres vs MySQL connection strings, SSL requirements, "Upsert" logic differences. |
| **Messaging** | `knowledge/messaging.json` | Slack (Token vs Webhook), Discord (Intents), Teams constraints. |

### Layer 2: Architectural Patterns (The "Structure")
*Best-practice topologies for solving standard problems. Prevents "hallucinated" connections.*

| Pattern Name | File | Description |
| :--- | :--- | :--- |
| **AI Agent** | `patterns/webhook_ai_agent.json` | Standard Agent + Model + Memory wiring. (✅ Started) |
| **Pagination Loop** | `patterns/loop_pagination.json` | `Split In Batches` or `Loop Over Items` for processing API lists. |
| **Error Handling** | `patterns/error_trigger.json` | Global Error Trigger -> Notification flow. |
| **RAG Pipeline** | `patterns/rag_vector_store.json` | Embedding -> Vector Store -> Retreival -> Generation. |
| **Approval Flow** | `patterns/human_approval.json` | Wait node usage + Switch routing. |

### Layer 3: Runtime Context (The "Environment")
*Dynamic knowledge about the user's specific n8n instance.*

| Component | File | Content |
| :--- | :--- | :--- |
| **UserProfile** | `config/user_profile.json` | User's deployment type (Docker/Cloud), HTTPS status, available global env vars. |

## 3. Implementation Roadmap / 实施路线图

### Phase 1: Foundation (Current)
- [x] Email Providers (`providers.json`)
- [x] Basic AI Pattern (`webhook_ai_agent.json`)

### Phase 2: High-Frequency Domains (Next Priority)
- [ ] **LLM Knowledge**: Create `knowledge/models.json` to let Architect choose the right model (e.g., "Use GPT-4o for complex logic, use gpt-3.5/mini for simple summaries").
- [ ] **Data Processing**: Create `patterns/loop_pagination.json` because 50% of workflows involve processing lists (Google Sheets rows, API results).

### Phase 3: Environment Awareness
- [ ] **Context Injection**: Update Architect Prompt to read `user_profile.json` (or ask for it).
- [ ] **Self-Correction**: If user says "I'm on Docker without HTTPS", automatically rule out OAuth nodes.

### Phase 4: Template-First Strategy (The "Shortcuts")
*Why generate from scratch when you can modify a proven solution?*

#### 1. Template Library Structure (`reference/templates/`)
Organize full workflow templates by category:
- `productivity/` (e.g., Daily Digest, Meeting Notes)
- `marketing/` (e.g., Lead Scoring, Social Poster)
- `devops/` (e.g., Error Alerting, Database Backup)

#### 2. Retrieval Logic
The Architect Agent's first step should be **"Similarity Search"**:
1.  **User Request**: "Send me a daily weather report."
2.  **Search**: Vector search against `reference/templates/**`.
3.  **Result**: Found `daily_email_digest.json` (Score: 0.85).
4.  **Action**: Architect instructs Coder: *"Load template 'daily_email_digest.json' and modify the 'Gmail' node to 'Weather API'."*

**Benefit**: Guarantees structure is valid because it starts from a working file.

## 4. Integration Strategy
- **Architect's Role**:
    1.  **Search Templates** (Layer 4).
    2.  If match -> **"Modify Strategy"**.
    3.  If no match -> **"Compose Strategy"** (using Layer 1 & 2).
- **Coder's Role**:
    - Queries **Layer 2 (patterns)** to fill in gaps.

This separation ensures the Architect makes high-level engineering decisions, while the Coder follows strict structural blueprints.
