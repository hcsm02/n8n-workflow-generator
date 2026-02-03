# Roadmap: Advanced RAG Strategy for n8n Generation / 进阶 RAG 策略路线图

This document outlines the strategy to evolve the agent from a simple generator to a "Senior n8n Engineer" by integrating large-scale reference datasets.

## 1. Core Philosophy / 核心理念
The current "Rule-based + Few-shot" approach is insufficient for complex production workflows. We must shift to a **"Retrieval-Augmented Generation (RAG)"** architecture that grounds the AI in real-world patterns.

## 2. Reference Data Sources / 参考数据源
Based on analysis, we will ingest the following GitHub repositories:

| Category | Repository | Purpose |
| :--- | :--- | :--- |
| **Structure (结构)** | `Danitilahun/n8n-workflow-templates` | **2,000+ Samples**. Learning coordinate layouts, ID generation, and common connection topologies. |
| **Logic (逻辑)** | `fayazam33/n8n-projects` | **Multi-Agent & RAG**. Learning how to wire AI Agents with Tools and Memory properly. |
| **Robustness (鲁棒)** | `enescingoz/awesome-n8n-templates` | **Error Handling**. Learning `If`, `Wait`, and `Error Trigger` patterns. |
| **Production (生产)** | `n8n-io/self-hosted-ai-starter-kit` | **Environment Config**. Learning credential mapping and vector DB integration. |

## 3. RAG Modeling Strategy / RAG 建模策略
We will not just "dump" JSONs into a vector DB. We will process them into **Semantic Layers**:

### Layer 1: Topology Index (Skeleton) / 拓扑骨架层
- **Goal**: Architect Agent use only.
- **Content**: Abstracted graphs removing specific parameters.
- **Example**: `[Webhook] -> [HTTP Request] -> [IF] -> (True: [Slack])`
- **Use Case**: When user asks for "Sync data with error check", retrieve the Skeleton with error handling.

### Layer 2: Pattern Library (Snippets) / 范式代码层
- **Goal**: Coder Agent use only.
- **Content**: Specific JSON blocks for complex nodes.
- **Examples**:
    - **"AI Chain Pattern"**: The correct `Chain -> Model -> Memory` structure.
    - **"Pagination Loop"**: How to set up a loop to fetch all pages from an API.
    - **"Expression Snippet"**: Common JS expressions like `{{ $json["data"] }}`.

### Layer 3: Parameter Dictionary / 参数字典层
- **Goal**: Validation.
- **Content**: Schema definitions for specific node types (e.g., specific fields required for `n8n-nodes-base.googleSheets`).

## 4. Implementation Plan (v0.2 -> v1.0) / 实施计划

### Phase 1: Data Ingestion (Manual Start)
- [ ] Create `reference/patterns/` directory.
- [ ] Manually extract 5-10 "Gold Standard" patterns (e.g., Simple AI, Complex Loop, Error Handler).
- [ ] Update `Coder` prompt to load these patterns dynamically.

### Phase 2: Vector Search Integration
- [ ] Deploy a local vector store (e.g., ChromaDB or simple faiss).
- [ ] Ingest the `Danitilahun` dataset.
- [ ] Implement a `Retriever Node` in LangGraph before the `Architect` node.

## 5. Immediate Action / 立即行动
- **Action**: Download 1-2 complex JSONs from the recommended repos.
- **Task**: Dissect them into the `reference/patterns` folder to fix the "AI Node missing Model" issue permanently via pattern injection.
