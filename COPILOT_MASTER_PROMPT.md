# RAVISN Inbound — Master Copilot Prompt

**Use this prompt in VS Code Copilot Chat (`Ctrl+Shift+I`) or GitHub Copilot to systematically implement advanced AI features.**

---

## 🎯 CONTEXT: Project Overview

You are helping improve the **RAVISN Inbound** multi-tenant conversational AI platform. The project:
- **Tech Stack**: FastAPI (Python) + React (JavaScript) + SQLite/PostgreSQL
- **Current AI Stack**: OpenAI/Groq/Gemini LLM routing + simple keyword-based RAG
- **Primary Function**: WhatsApp/Facebook/Instagram chatbot that answers tenant questions from a knowledge base and books appointments
- **Language Support**: Roman Urdu, English, Urdu script

**Current Architecture**:
```
User Message → FastAPI Router → pipeline.py → agent.py (LLM Call) → Response
                                    ↓
                            Knowledge Base (Q&A pairs in DB)
                                    ↓
                            Booking Extraction → DB Storage
```

**Repo Structure**:
```
inbound/
├── app/
│   ├── main.py           # FastAPI app setup
│   ├── agent.py          # LLM orchestration + prompt engineering
│   ├── pipeline.py       # Message processing flow
│   ├── models.py         # SQLAlchemy ORM models
│   ├── crud.py           # Database operations
│   ├── schemas.py        # Pydantic request/response schemas
│   ├── auth.py           # JWT + API key auth
│   ├── routers/          # FastAPI route handlers
│   │   ├── chat.py       # /chat/test-message endpoint
│   │   ├── knowledge.py  # /knowledge CRUD endpoints
│   │   ├── conversations.py
│   │   ├── bookings.py
│   │   ├── whatsapp_official.py
│   │   ├── meta_messaging.py
│   │   └── ...
│   └── database.py       # SQLAlchemy session management
├── requirements.txt      # Python dependencies
├── .env.example          # Config template
├── frontend/             # React dashboard
├── whatsapp-qr-service/  # Node.js Baileys integration
└── smoke_test.py         # Integration tests
```

---

## 🚀 IMPROVEMENT ROADMAP (4-Week Sprint)

### **Phase 1: Semantic Search with Vector Embeddings (Week 1-2)**

**Goal**: Replace keyword-matching KB retrieval with semantic similarity using embeddings.

**What to Build**:
1. Create `app/rag.py` — RAG engine with Chroma vector DB
2. Update `app/models.py` — Add embedding storage
3. Modify `agent.py` — Use semantic search for KB context
4. Add migrations for new schema

**Expected Outcome**: When customer asks "when are you open?", it now matches "Clinic hours: 9am-8pm" even without keyword overlap.

---

### **Phase 2: Tenant Personas & Branded Voice (Week 1-2 Parallel)**

**Goal**: Let each tenant define a persona so replies match their brand voice.

**What to Build**:
1. Create `TenantPersona` model in `models.py`
2. New endpoint: `POST /settings/persona` to configure persona
3. Update system prompt injection in `agent.py`
4. Frontend: Persona editor form in React dashboard

**Expected Outcome**: "Bright Smile Clinic" gets warm, friendly tone; "Corporate Legal" gets formal, precise tone.

---

### **Phase 3: Ollama Local LLM Support (Week 2-3)**

**Goal**: Allow on-premises LLM inference for cost savings & privacy.

**What to Build**:
1. Add `call_ollama()` function to `agent.py`
2. Update `call_llm()` to route to Ollama if available
3. Docker Compose addition for Ollama container
4. Environment variable config (OLLAMA_ENABLED, OLLAMA_MODEL)
5. Tests in `smoke_test.py`

**Expected Outcome**: Businesses can use `qwen2.5:3b` or `llama2:7b` locally, zero API costs.

---

### **Phase 4: Tool Calling for CRM Integration (Week 3-4)**

**Goal**: Agent can query external APIs (calendar, CRM) via function calling.

**What to Build**:
1. Create `app/tools.py` — Define available functions
2. Add function calling logic to `agent.py`
3. Create connectors: `app/integrations/` (Google Calendar, Salesforce stubs)
4. Update booking flow to sync via tools
5. Tests for tool execution

**Expected Outcome**: Agent says "Let me check availability" → queries calendar → gives real-time slots.

---

### **Phase 5: Analytics & Feedback Loop (Week 4+)**

**Goal**: Track agent performance, gather feedback for continuous improvement.

**What to Build**:
1. `ReplyFeedback` model for ratings
2. `TenantProfile` model for aggregated insights
3. New endpoint: `POST /conversations/{id}/feedback`
4. Analytics dashboard: `app/routers/analytics.py`
5. Frontend: Rating widget + analytics view

**Expected Outcome**: Dashboard shows "Reply quality: 4.2/5 stars", "Booking conversion: 32%", "Top FAQ".

---

## 📋 STEP-BY-STEP IMPLEMENTATION CHECKLIST

### **✅ PHASE 1A: Set Up Vector Database (Chroma + Embeddings)**

```bash
# In terminal:
pip install chromadb sentence-transformers
```

**TASK 1.1**: Create `app/rag.py`
- [ ] Import Chroma, SentenceTransformers
- [ ] Build `RAGEngine` class with `__init__(tenant_id)`
- [ ] Implement `add_to_kb(question, answer)` → generate embedding, store
- [ ] Implement `retrieve(query, top_k=3)` → query embedding, return top docs
- [ ] Add tenant-specific collection isolation
- **Prompt to Copilot**: "Create a RAGEngine class in app/rag.py that uses Chroma for vector storage and sentence-transformers for embeddings. Each tenant should have an isolated collection."

**TASK 1.2**: Update `app/models.py`
- [ ] Add `embedding_model` field to `Tenant` (track which embedding model used)
- [ ] Consider: Do we need to store embeddings in DB, or compute on-the-fly?
- **Prompt to Copilot**: "Add tenant-level configuration for embedding model selection. Should we cache embeddings in PostgreSQL or recompute on each query?"

**TASK 1.3**: Modify `app/crud.py`
- [ ] Update `add_knowledge()` to sync with RAG engine
- [ ] Add `update_knowledge()` to re-embed on edit
- [ ] Add `delete_knowledge()` to remove from vector DB
- **Prompt to Copilot**: "Update the knowledge CRUD operations to automatically sync with a Chroma RAG engine. Handle embedding generation asynchronously if possible."

**TASK 1.4**: Refactor `app/agent.py`
- [ ] Replace `find_best_kb_entry()` with RAG semantic search
- [ ] Keep `find_relevant_kb_entries()` as fallback
- [ ] Update `build_kb_text()` to use RAG results
- **Prompt to Copilot**: "Replace keyword-based KB retrieval in agent.py with semantic search. The function should call RAGEngine.retrieve() to get top-3 relevant documents, then format them into the system prompt."

**TASK 1.5**: Write tests
- [ ] Add to `smoke_test.py`: "Knowledge entry retrieval now uses semantic search"
- [ ] Test: Add "clinic hours: 9am-8pm", query "when open", verify match
- **Prompt to Copilot**: "Write tests in smoke_test.py to verify that semantic search retrieves relevant KB entries even without exact keyword matches."

---

### **✅ PHASE 1B: Implement Tenant Personas**

**TASK 1.6**: Add Persona Model to `app/models.py`
- [ ] Create `TenantPersona` class:
  ```python
  - id (primary key)
  - tenant_id (foreign key)
  - name (e.g., "Friendly Clinic Assistant")
  - tone (e.g., "warm", "professional", "casual")
  - specialties (comma-separated or JSON)
  - prompt_injection (custom system prompt prefix)
  - response_examples (JSON list of few-shot examples)
  - created_at, updated_at
  ```
- [ ] Add relationship: `Tenant.persona`
- **Prompt to Copilot**: "Add a TenantPersona model to app/models.py. It should store persona attributes (name, tone, specialties) and allow custom prompt injection. Include a one-to-one relationship with Tenant."

**TASK 1.7**: Create CRUD for Personas in `app/crud.py`
- [ ] `create_or_update_persona(db, tenant_id, name, tone, specialties, ...)`
- [ ] `get_tenant_persona(db, tenant_id)`
- [ ] `delete_persona(db, tenant_id)`
- **Prompt to Copilot**: "Add CRUD functions in app/crud.py for TenantPersona. The functions should create, read, update, and delete tenant personas."

**TASK 1.8**: Add Persona Schema in `app/schemas.py`
- [ ] `PersonaCreate` (name, tone, specialties, prompt_injection, response_examples)
- [ ] `PersonaOut` (all fields including id, created_at)
- **Prompt to Copilot**: "Add Pydantic schemas for TenantPersona in app/schemas.py. Include validation for tone (must be one of: warm, professional, casual, etc.)."

**TASK 1.9**: Create Persona Endpoints in `app/routers/settings.py`
- [ ] `GET /settings/persona` — Fetch current persona
- [ ] `POST /settings/persona` — Create/update persona
- [ ] `DELETE /settings/persona` — Delete persona
- **Prompt to Copilot**: "Add FastAPI endpoints in app/routers/settings.py for persona CRUD. Include authentication check, ensure tenant can only modify their own persona."

**TASK 1.10**: Update Agent to Use Persona in `app/agent.py`
- [ ] In `generate_reply_with_custom_prompt()`, load tenant persona
- [ ] Prepend persona instructions to system prompt:
  ```
  system_prompt = f"""
  You are {persona.name}.
  Your tone is {persona.tone}.
  Your specialties: {persona.specialties}.
  
  [Include few-shot examples from persona.response_examples]
  
  {SYSTEM_PROMPT_TEMPLATE}
  """
  ```
- [ ] Fallback to default template if no persona set
- **Prompt to Copilot**: "Modify generate_reply_with_custom_prompt() in app/agent.py to load the tenant's persona and inject it into the system prompt. If no persona exists, fall back to the default template."

**TASK 1.11**: Frontend Persona Editor (React)
- [ ] Create `frontend/src/components/PersonaEditor.jsx`
- [ ] Form inputs: name, tone (dropdown), specialties (textarea), prompt_injection (code editor)
- [ ] Submit to `POST /settings/persona`
- **Prompt to Copilot**: "Create a React component PersonaEditor.jsx with form fields for persona name, tone (dropdown with options), specialties, and custom prompt injection. Add validation and error handling."

**TASK 1.12**: Test Personas
- [ ] Add to `smoke_test.py`: "Persona creation and application"
- [ ] Test: Create persona with warm tone → send message → verify response tone
- **Prompt to Copilot**: "Add integration tests to smoke_test.py to verify persona creation and that personas are applied to agent responses."

---

### **✅ PHASE 2: Add Ollama Local LLM Support**

**TASK 2.1**: Add Ollama Function to `app/agent.py`
- [ ] Create `call_ollama(messages: list) -> str`
- [ ] HTTP POST to `OLLAMA_BASE_URL/api/chat`
- [ ] Request JSON format output
- [ ] Handle timeouts, errors gracefully
- **Prompt to Copilot**: "Add a call_ollama() function to app/agent.py that sends messages to a local Ollama instance via HTTP. It should request JSON-formatted output and include error handling."

**TASK 2.2**: Update LLM Router in `app/agent.py`
- [ ] Modify `call_llm()` to try Ollama first (if enabled)
- [ ] Fall through: Ollama → Groq → Gemini → OpenAI
- [ ] Add logging for which provider is used
- **Prompt to Copilot**: "Update the call_llm() function in app/agent.py to try Ollama first if OLLAMA_ENABLED=true, then fall back to Groq, Gemini, and OpenAI in order."

**TASK 2.3**: Add Ollama Environment Variables
- [ ] Update `.env.example`:
  ```
  OLLAMA_ENABLED=false
  OLLAMA_BASE_URL=http://localhost:11434
  OLLAMA_MODEL=qwen2.5:3b
  ```
- **Prompt to Copilot**: "Add Ollama configuration to .env.example with OLLAMA_ENABLED, OLLAMA_BASE_URL, and OLLAMA_MODEL variables."

**TASK 2.4**: Update Docker Compose
- [ ] Add Ollama service:
  ```yaml
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    environment:
      - OLLAMA_KEEP_ALIVE=5m
  ```
- [ ] Add volume declaration
- **Prompt to Copilot**: "Add an Ollama service to docker-compose.yml with GPU support options (cuda/rocm) and volume persistence."

**TASK 2.5**: Add Model Pulling Script
- [ ] Create `scripts/setup_ollama.sh`:
  ```bash
  #!/bin/bash
  ollama pull qwen2.5:3b
  ollama pull llama2:7b
  echo "Models pulled successfully"
  ```
- **Prompt to Copilot**: "Create a setup script that pulls recommended Ollama models (qwen2.5:3b, llama2:7b). Add instructions for running it in README."

**TASK 2.6**: Update `.env.example` with Ollama Settings Endpoint
- [ ] `GET /settings/api-key` should also return Ollama status
- [ ] Show available local models
- **Prompt to Copilot**: "Update the /settings/api-key endpoint to also check and return Ollama availability and active models."

**TASK 2.7**: Test Ollama Integration
- [ ] Add to `smoke_test.py`: "Test with OLLAMA_ENABLED=true"
- [ ] Mock Ollama response if not running
- **Prompt to Copilot**: "Add smoke tests for Ollama integration. Include a test that sends a message when Ollama is enabled, and another that falls back gracefully when Ollama is unavailable."

---

### **✅ PHASE 3: Tool Calling for CRM/Calendar Integration**

**TASK 3.1**: Create `app/tools.py` — Define Available Functions
- [ ] Define `TOOLS` list with function schemas:
  ```python
  TOOLS = [
      {
          "type": "function",
          "function": {
              "name": "check_availability",
              "description": "Check doctor/service availability for given date/time",
              "parameters": {...}
          }
      },
      {
          "type": "function",
          "function": {
              "name": "create_booking",
              "description": "Create appointment in CRM/calendar",
              "parameters": {...}
          }
      },
      {
          "type": "function",
          "function": {
              "name": "get_pricing",
              "description": "Retrieve service pricing from CRM",
              "parameters": {...}
          }
      }
  ]
  ```
- **Prompt to Copilot**: "Create app/tools.py with a TOOLS list defining function schemas for check_availability, create_booking, and get_pricing. Each should include proper parameter definitions and descriptions."

**TASK 3.2**: Create `app/integrations/` Directory
- [ ] Create `app/integrations/__init__.py`
- [ ] Create `app/integrations/calendar_provider.py` — Abstract base class
- [ ] Create `app/integrations/google_calendar.py` — Google Calendar connector
- [ ] Create `app/integrations/crm_provider.py` — Abstract base class
- [ ] Create `app/integrations/salesforce.py` — Salesforce stub (or use your CRM)
- **Prompt to Copilot**: "Create an integrations module in app/integrations/ with abstract base classes for calendar and CRM providers. Implement stubs for Google Calendar and Salesforce."

**TASK 3.3**: Add Integration Config to `app/models.py`
- [ ] New model: `TenantIntegration`
  ```python
  - id
  - tenant_id
  - provider_type (e.g., "google_calendar", "salesforce")
  - access_token (encrypted)
  - refresh_token (encrypted)
  - metadata (JSON)
  - status (connected/disconnected)
  ```
- **Prompt to Copilot**: "Add a TenantIntegration model to app/models.py to store API credentials for external services. Include encrypted token storage."

**TASK 3.4**: Create Integration CRUD in `app/crud.py`
- [ ] `connect_integration(db, tenant_id, provider_type, access_token, ...)`
- [ ] `get_tenant_integrations(db, tenant_id)`
- [ ] `disconnect_integration(db, tenant_id, provider_type)`
- **Prompt to Copilot**: "Add CRUD operations in app/crud.py for managing tenant integrations. Handle token encryption/decryption."

**TASK 3.5**: Add Function Calling Logic to `app/agent.py`
- [ ] Create `call_llm_with_tools(messages, tenant_id)`:
  - Pass `tools` parameter to LLM
  - Parse `response.tool_calls` if present
  - Execute tool functions
  - Collect results
  - Re-query LLM with tool results
  - Return final response
- **Prompt to Copilot**: "Implement a call_llm_with_tools() function in app/agent.py that handles OpenAI function calling. It should parse tool calls, execute them via integrations, and send results back to the LLM."

**TASK 3.6**: Implement Tool Executors in `app/tools.py`
- [ ] `execute_check_availability(tenant_id, date, time_slot, doctor)`
- [ ] `execute_create_booking(tenant_id, name, phone, date, time, notes)`
- [ ] `execute_get_pricing(tenant_id, service)`
- [ ] Route to appropriate integration provider
- **Prompt to Copilot**: "Implement tool executor functions in app/tools.py that call the appropriate integration (Google Calendar, Salesforce, etc.) and return structured results."

**TASK 3.7**: Update Pipeline to Use Tools
- [ ] Modify `app/pipeline.py` → `process_incoming_message()`
- [ ] Call `agent.generate_reply_with_tools()` instead of `agent.generate_reply()`
- [ ] Pass tenant ID so tools can access integrations
- **Prompt to Copilot**: "Update app/pipeline.py to use tool-calling in the message processing pipeline. Pass tenant_id and integration data to the agent."

**TASK 3.8**: Create Integration Management Endpoints
- [ ] `POST /settings/integrations/{provider}` — Connect
- [ ] `GET /settings/integrations` — List
- [ ] `DELETE /settings/integrations/{provider}` — Disconnect
- [ ] OAuth callback handling (if applicable)
- **Prompt to Copilot**: "Add FastAPI endpoints in app/routers/settings.py for managing integrations. Include OAuth 2.0 callback handling for Google Calendar."

**TASK 3.9**: Frontend Integration Manager (React)
- [ ] Create `frontend/src/components/IntegrationManager.jsx`
- [ ] Show available integrations (Google Calendar, Salesforce, etc.)
- [ ] "Connect" button → OAuth flow
- [ ] "Disconnect" button
- [ ] Status indicator (connected/disconnected)
- **Prompt to Copilot**: "Create a React component IntegrationManager.jsx that displays available integrations with connect/disconnect buttons. Include OAuth flow handling."

**TASK 3.10**: Test Tool Calling
- [ ] Add to `smoke_test.py`: "Tool calling for booking"
- [ ] Test: Send message → agent calls `create_booking()` → verify DB update
- **Prompt to Copilot**: "Add integration tests in smoke_test.py to verify tool calling. Mock the external APIs and ensure bookings are created correctly."

---

### **✅ PHASE 4: Analytics & Feedback Loop**

**TASK 4.1**: Add Feedback Model to `app/models.py`
- [ ] `ReplyFeedback` class:
  ```python
  - id
  - conversation_id (FK)
  - reply_id (FK to Message)
  - rating (1-5 stars)
  - feedback_text
  - created_at
  ```
- [ ] `TenantProfile` class (aggregate insights):
  ```python
  - tenant_id (PK)
  - top_questions (JSON)
  - common_booking_times (JSON)
  - avg_response_rating (float)
  - total_conversations (int)
  - booking_conversion_rate (float)
  - updated_at
  ```
- **Prompt to Copilot**: "Add ReplyFeedback and TenantProfile models to app/models.py for tracking agent performance metrics."

**TASK 4.2**: Add Feedback CRUD in `app/crud.py`
- [ ] `save_reply_feedback(db, reply_id, rating, feedback_text)`
- [ ] `get_reply_feedback(db, reply_id)`
- [ ] `update_tenant_profile(db, tenant_id)` — Calculate aggregates
- **Prompt to Copilot**: "Add CRUD functions in app/crud.py for storing and retrieving reply feedback. Implement update_tenant_profile() to recalculate performance metrics."

**TASK 4.3**: Add Feedback Schema in `app/schemas.py`
- [ ] `ReplyFeedbackIn` (rating, feedback_text)
- [ ] `ReplyFeedbackOut` (id, reply_id, rating, created_at)
- [ ] `TenantProfileOut` (all metrics)
- **Prompt to Copilot**: "Add Pydantic schemas for ReplyFeedback and TenantProfile in app/schemas.py."

**TASK 4.4**: Create Analytics Endpoints
- [ ] Create `app/routers/analytics.py`:
  - `GET /analytics/agent-performance` — Overall metrics
  - `GET /analytics/top-faq` — Most asked questions
  - `GET /analytics/conversation-trend` — Time-series data
  - `GET /analytics/escalations` — Common escalation issues
- **Prompt to Copilot**: "Create app/routers/analytics.py with endpoints for agent performance metrics, top FAQs, conversation trends, and escalation analysis."

**TASK 4.5**: Add Feedback Endpoint in `app/routers/conversations.py`
- [ ] `POST /conversations/{convo_id}/messages/{reply_id}/feedback`
- [ ] Accept rating + feedback text
- [ ] Save to DB
- [ ] Update tenant profile
- [ ] If rating <= 2, flag for admin review
- **Prompt to Copilot**: "Add a feedback endpoint to app/routers/conversations.py that accepts star ratings and feedback comments. Auto-flag low ratings for admin review."

**TASK 4.6**: Frontend Rating Widget (React)
- [ ] Create `frontend/src/components/ReplyRating.jsx`
- [ ] 5-star rating UI
- [ ] Optional text feedback field
- [ ] Submit to backend
- [ ] Show success message
- **Prompt to Copilot**: "Create a React component ReplyRating.jsx with a 5-star rating widget and optional feedback text field. Submit feedback to the backend API."

**TASK 4.7**: Frontend Analytics Dashboard (React)
- [ ] Create `frontend/src/components/AnalyticsDashboard.jsx`
- [ ] Display:
  - Avg reply rating (gauge chart)
  - Booking conversion rate (progress bar)
  - Total conversations (metric card)
  - Top 5 FAQ (table)
  - Conversation trend (line chart)
  - Escalation summary (alert box)
- **Prompt to Copilot**: "Create a React analytics dashboard component that displays agent performance metrics using charts (recharts or chart.js). Include rating, conversion rate, top FAQs, and trends."

**TASK 4.8**: Test Analytics
- [ ] Add to `smoke_test.py`: "Feedback collection and analytics"
- [ ] Test: Rate a reply → verify feedback saved → check analytics endpoint
- **Prompt to Copilot**: "Add smoke tests for feedback collection and analytics endpoints. Verify that feedback is correctly saved and aggregated in tenant profiles."

---

## 🛠️ PROMPTS FOR DIFFERENT TASKS

### **For Bug Fixes / Debugging**
```
Context: I'm working on the RAVISN Inbound project (FastAPI + React chatbot).
File: app/agent.py, function generate_reply_with_custom_prompt()
Issue: [describe the issue]
Current code: [paste snippet]
Expected behavior: [describe expected]

What's the root cause, and how should I fix it?
```

### **For New Features**
```
Context: RAVISN Inbound — multi-tenant conversational AI platform.
Feature: [Feature name]
Requirements:
- [requirement 1]
- [requirement 2]
- [requirement 3]

Which files should I modify? Give me a step-by-step implementation plan.
```

### **For Code Review**
```
Context: RAVISN Inbound project.
Files changed: [list files]
Purpose: [describe PR purpose]

Please review for:
1. Multi-tenant isolation (no data leakage)
2. Error handling (graceful degradation)
3. Performance (N+1 queries, unnecessary DB calls)
4. Security (SQL injection, auth bypass)
5. Code style (FastAPI conventions)

What issues do you find? How should I fix them?
```

### **For Testing**
```
Context: RAVISN Inbound.
Component: [component name]
Test scenarios:
- [scenario 1]
- [scenario 2]
- [scenario 3]

Write comprehensive tests using pytest + FastAPI TestClient. Include mocking for external APIs.
```

---

## 📚 KEY FILES REFERENCE

| File | Purpose | Key Functions |
|------|---------|---|
| `app/agent.py` | LLM orchestration | `generate_reply()`, `call_llm()`, `find_best_kb_entry()` |
| `app/pipeline.py` | Message processing | `process_incoming_message()` |
| `app/models.py` | Database schemas | `Tenant`, `Conversation`, `Message`, `KnowledgeEntry`, `Booking` |
| `app/crud.py` | Database queries | All CRUD operations |
| `app/routers/chat.py` | Chat endpoint | `POST /chat/test-message` |
| `app/routers/knowledge.py` | KB management | `GET/POST /knowledge` |
| `.env.example` | Config template | `OPENAI_API_KEY`, `OPENAI_MODEL` |
| `smoke_test.py` | Integration tests | End-to-end test scenarios |

---

## 🔐 SECURITY GUIDELINES

When implementing new features, ensure:
1. **Multi-tenant isolation**: Always filter by `tenant_id` in queries
2. **Auth checks**: All endpoints must verify tenant ownership via `get_current_tenant_flexible()`
3. **Secret management**: Store API keys encrypted in DB or `.env`, never commit them
4. **Input validation**: Use Pydantic schemas to validate all inputs
5. **Error handling**: Catch exceptions gracefully, never expose stack traces to clients
6. **CORS & rate limiting**: Already configured, maintain them

Example:
```python
@router.post("/some-endpoint")
def some_handler(payload: SomeSchema, db: Session = Depends(get_db), 
                 tenant: Tenant = Depends(get_current_tenant_flexible)):
    # ✅ Tenant is authenticated
    # ✅ Filter by tenant_id
    data = db.query(SomeModel).filter_by(tenant_id=tenant.id).first()
    # ✅ Validate input via Pydantic
    # ✅ Handle errors gracefully
    return response
```

---

## 🚨 ANTI-PATTERNS (DO NOT DO)

❌ **Don't**:
- Access data without filtering by `tenant_id` (data leakage)
- Log sensitive data like API keys or customer messages
- Use string formatting for SQL queries (SQL injection)
- Block on external API calls without timeout (hangs)
- Return detailed error messages to clients (info disclosure)
- Skip validation on user inputs (crashes, security issues)

✅ **Do**:
- Always filter queries by `tenant_id`
- Use Pydantic for validation
- Catch exceptions and return generic error messages
- Set timeouts on external API calls (e.g., `timeout=30.0`)
- Log only essential events, sanitize sensitive data
- Use `.env` for secrets, never hardcode them

---

## 🎬 GETTING STARTED

1. **Copy this prompt** into a file: `COPILOT_MASTER_PROMPT.md` (already done ✅)
2. **In VS Code**, open GitHub Copilot Chat (`Ctrl+Shift+I` or `Cmd+Shift+I`)
3. **Paste a specific task** from the checklist above
4. **Copilot will generate code** → review, adjust, implement
5. **Test** using `smoke_test.py`
6. **Commit** with clear message referencing the phase/task

Example workflow:
```
You: "TASK 1.1: Create app/rag.py with a RAGEngine class..."
Copilot: [Generates code for RAGEngine]
You: [Review] "Good, but I need to add X..."
Copilot: [Updates code]
You: [Copy & paste into editor, test]
```

---

## 📞 WHEN TO USE SPECIFIC PROMPTS

| Scenario | Prompt Template |
|----------|---|
| Stuck on implementation | Feature prompt + file structure |
| Code crashes / error | Bug fix prompt + traceback |
| Reviewing PR | Code review prompt |
| Writing tests | Testing prompt |
| Need architecture advice | "Context: ..., Design question: ..." |

---

## 🔄 ITERATIVE WORKFLOW

1. **Start with Phase 1A** (Vector embeddings RAG)
   - Implement, test, commit
2. **Run Phase 1B in parallel** (Personas)
   - Easier, can overlap
3. **Move to Phase 2** (Ollama) once 1A+1B stable
4. **Phase 3** (Tool calling) is high-effort, plan 2 weeks
5. **Phase 4** (Analytics) is quick polish, save for end

Each phase should take ~1 week with focused effort + Copilot assistance.

---

## ✨ FINAL CHECKLIST

Before pushing to production:

- [ ] All new endpoints have auth checks (`get_current_tenant_flexible`)
- [ ] Multi-tenant isolation verified (no data leakage)
- [ ] Error handling in place (no raw exceptions to client)
- [ ] Tests written and passing (`pytest smoke_test.py`)
- [ ] Pydantic schemas updated and validated
- [ ] Database migrations created (`alembic`)
- [ ] Environment variables documented in `.env.example`
- [ ] Frontend components tested
- [ ] Performance acceptable (no N+1 queries, reasonable timeouts)
- [ ] Security review passed (no secrets in code, SQL injection protection)
- [ ] README updated with new features/setup instructions

---

**Happy coding! 🚀 Use this prompt as your guide. Copilot Chat will help you implement each task.**

