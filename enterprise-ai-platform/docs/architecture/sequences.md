# Sequence Diagrams

## Document Upload and Indexing

```text
User
 |
 | POST /documents
 v
FastAPI Router
 |
 | validate request, auth context
 v
UploadDocument Use Case
 |
 | store metadata, file hash, version
 v
Document Repository + Object Storage
 |
 | emit DocumentUploaded
 v
Queue
 |
 | async job
 v
Ingestion Worker
 |
 | validate file, virus-scan placeholder
 v
Text Extractor
 |
 | extracted text
 v
Cleaner + Chunker
 |
 | chunks
 v
Embedding Gateway
 |
 | vectors
 v
Chunk Repository + Vector Repository
 |
 | mark indexed, emit DocumentIndexed
 v
Metrics + Audit Log
```

Failure behavior:

- unsupported file: reject before storage
- extractor failure: mark version failed and keep audit trail
- embedding rate limit: retry with exponential backoff
- repeated failure: move job to dead-letter queue

## Hybrid Search

```text
User
 |
 | POST /search
 v
FastAPI Router
 |
 v
SearchKnowledge Use Case
 |
 | build tenant and permission filters
 v
Retrieval Service
 |
 +--> Lexical Search Adapter
 |
 +--> Vector Search Adapter
 |
 v
Candidate Merger
 |
 v
Reranker
 |
 v
Citation Builder
 |
 v
Search Response
```

Production note: search must never retrieve documents outside the user's permitted workspaces. Permission filters are part of the retrieval query, not a post-processing step.

## RAG Chat

```text
User
 |
 | POST /chat
 v
FastAPI Router
 |
 v
AskQuestion Use Case
 |
 | load or create conversation
 v
Conversation Repository
 |
 | retrieve relevant chunks
 v
Retrieval Service
 |
 | build context with citations
 v
Context Builder
 |
 | load active prompt version
 v
Prompt Repository
 |
 | generate answer
 v
LLM Gateway
 |
 | persist assistant message, citations, usage
 v
Message Repository
 |
 | emit AnswerGenerated
 v
Evaluation Queue
 |
 v
Response
```

## Online Evaluation

```text
AnswerGenerated Event
 |
 v
Evaluation Worker
 |
 +--> Faithfulness Evaluator
 +--> Groundedness Evaluator
 +--> Answer Relevance Evaluator
 +--> Context Precision Evaluator
 +--> Hallucination Heuristic
 |
 v
Evaluation Repository
 |
 v
Metrics Exporter
```

Evaluation should be asynchronous so user-facing latency is not dominated by evaluator calls.

## Agent Execution

```text
User
 |
 | POST /agents/{id}/runs
 v
RunAgent Use Case
 |
 | load agent definition, policy, tools
 v
Agent Repository
 |
 v
LangGraph Orchestrator
 |
 +--> Knowledge Search Tool
 +--> Calculator Tool
 +--> SQL Tool (future)
 +--> External MCP Tool (future)
 |
 v
Tool Result Validator
 |
 v
LLM Gateway
 |
 v
Agent Run Repository
 |
 v
Trace + Metrics + Audit Log
```

