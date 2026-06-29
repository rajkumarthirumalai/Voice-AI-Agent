# Real-Time Bilingual Voice AI Agent (Hall Booking System)

This project provides a production-grade, highly modular, asynchronous Python architecture using **FastAPI** for a real-time, bilingual (Tamil/English) Voice AI Agent. The agent serves a hall booking system, processing real-time audio streams, querying a database for availability and pricing, and implementing a strict **Propose-and-Commit** guardrail pattern before performing any writes.

---

## 🏗️ Architectural Core Principles

1. **WebSocket-First Design**: The interface is built around high-throughput asynchronous WebSockets to prevent audio streaming blockages.
2. **Stateful Session Store**: Implements dedicated session scopes (e.g., Redis) that keep track of active language settings, call histories, and pending/staged booking records (for Propose-and-Commit confirmation).
3. **Tool Isolation**: The LLM Orchestrator never has direct database access. Instead, tools act as isolated interfaces, communicating with SQL queries strictly through bounded parameter structures.
4. **Bilingual Adaptability (Tamil & English)**: Custom logic is implemented for language toggling and localized synthetic audio generation.
5. **Guardrails & LLM Gateway**: The gateway enforces a low-temperature system prompt and limits output sizes to 1-2 sentences. This decreases TTS rendering latencies and mitigates AI hallucinations.
6. **Decoupled Audio Providers**: Integrations with Speech-To-Text (STT) and Text-To-Speech (TTS) are wrapped behind interface classes, allowing hot-swapping providers (e.g., Deepgram vs. Sarvam AI) with simple environment variables.

---

## 📂 File Structure & Responsibilities

```text
/
├── main.py                    # Application entrypoint & FastAPI lifecycle config
├── requirements.txt           # Main production & async dependencies
└── app/
    ├── config.py              # Application settings & validation (Pydantic Settings)
    ├── api/
    │   ├── websockets.py      # Entrypoint: Handles incoming audio streams & outgoing TTS over WS
    │   └── routes.py          # Admin & Health Check HTTP endpoints
    ├── core/
    │   ├── agent.py           # Core orchestrator: LLM gateway, bilingual routing & tool parser
    │   ├── session.py         # Session management (Call history & Propose-and-Commit buffers)
    │   └── guardrails.py      # Middleware: System prompts & response sentence-length validators
    ├── adapters/
    │   ├── base.py            # Abstract Base Classes & Factory injections for STT/TTS
    │   ├── stt/
    │   │   ├── deepgram.py    # Deepgram Speech-to-Text adapter
    │   │   └── sarvam.py      # Sarvam AI Speech-to-Text adapter (localized Indian speech)
    │   └── tts/
    │       ├── deepgram.py    # Deepgram Text-to-Speech audio synthesizer
    │       └── sarvam.py      # Sarvam AI Text-to-Speech audio synthesizer (Tamil accents)
    ├── tools/
    │   ├── base.py            # Bounded tool registry base class
    │   ├── check_availability.py # Tool: Fetches booking availability
    │   ├── get_pricing.py     # Tool: Fetches booking pricing tariffs
    │   ├── stage_booking.py   # Tool: Staging state (Propose)
    │   └── commit_booking.py  # Tool: Final DB write execution (Commit)
    └── database/
        ├── connection.py      # Database async engine configurations (SQLAlchemy)
        └── queries.py         # Strictly bounded database SQL query/ORM execution
```

### File-by-File Responsibilities

- **`main.py`**
  Handles the FastAPI initialization, logger setups, and async startup/shutdown hooks. It configures the DB and Redis session stores dynamically.
- **`app/config.py`**
  Implements configuration loading via environment files (`.env`). Exposes variables for API credentials, database URIs, model configs, and chosen adapter backends.
- **`app/api/websockets.py`**
  Maintains open client WebSocket connections. Receives binary audio packets, channels them to STT, feeds transcribed text into the orchestrator, and routes response TTS audio bytes back to the socket.
- **`app/api/routes.py`**
  REST endpoints enabling health checks and administrative commands (e.g., retrieving active call session contents or clearing stale call sessions).
- **`app/core/agent.py`**
  Houses the LLM orchestration loop. Translates user text intents into tools, manages bilingual user command detection, executes tools, and processes historical context.
- **`app/core/session.py`**
  Preserves stateful variables across a call duration. Implements the buffer property `pending_booking` to support the propose-and-commit mechanism.
- **`app/core/guardrails.py`**
  Intercepts conversational flow. Restricts generation temperature parameters, inserts custom Tamil/English system prompts, and limits response lengths to 1-2 sentences.
- **`app/adapters/base.py`**
  Specifies the generic schemas `AbstractSTTAdapter` and `AbstractTTSAdapter`. Connects settings to respective active adapters.
- **`app/adapters/stt/`** and **`app/adapters/tts/`**
  Provide plug-and-play network adapters communicating with transcription and audio synthesis service APIs (Deepgram, Sarvam AI).
- **`app/tools/`**
  The bounded tool registry. These tools validate schemas, read stateful details, retrieve records from the database layer, and return formatted responses to the LLM agent.
- **`app/database/`**
  Standard DB integration. Restricts database query capabilities to specific, parametrized routines within `queries.py`, protecting the system from direct LLM manipulation.

---

## 🔄 End-to-End Data Flow

The following sequence details how audio streams transit through the architecture:

```mermaid
sequenceDiagram
    autonumber
    actor User as Bilingual User
    participant WS as WebSocket Router (api/websockets.py)
    participant STT as STT Adapter (adapters/stt)
    participant Agent as LLM Orchestrator (core/agent.py)
    participant Session as Session Store (core/session.py)
    participant Tool as Bounded Tool (tools/)
    participant DB as DB Layer (database/queries.py)
    participant TTS as TTS Adapter (adapters/tts)

    User->>WS: Stream raw audio (Tamil/English)
    WS->>STT: Stream audio chunks
    STT->>WS: Yield transcription chunk
    WS->>Agent: Send transcript + session_id
    Agent->>Session: Load call history & pending state
    Agent->>Agent: Apply system guardrails (Low temp, bilingual)
    Agent->>Agent: Query LLM for next action
    
    alt Tool call required (e.g. check availability or stage booking)
        Agent->>Tool: Execute tool with parameters
        alt Stage Booking (Propose-and-Commit)
            Tool->>Session: Write "pending_booking" buffer
            Tool-->>Agent: Return staging message ("Staged. Please say yes to commit")
        else Commit Booking (User said "Yes")
            Tool->>Session: Read "pending_booking" buffer
            Tool->>DB: Write confirmed booking to DB
            Tool->>Session: Clear "pending_booking" buffer
            Tool-->>Agent: Return success confirmation
        else Read operation (Check Availability)
            Tool->>DB: Execute query
            DB-->>Tool: Return result
            Tool-->>Agent: Return text result
        end
    end

    Agent->>Agent: Apply guardrails (Filter length to 1-2 sentences)
    Agent->>Session: Save response to history
    Agent->>TTS: Stream short text response
    TTS-->>WS: Yield synthetic audio chunks
    WS-->>User: Stream real-time audio out
```

---

## 🔒 Propose-and-Commit Session State Pattern

To guarantee data safety, the agent cannot perform direct, unconfirmed writes:
1. **Propose Phase**: When a user asks to reserve a hall, the orchestrator triggers the `stage_booking` tool. Instead of executing database SQL insert statements, the tool computes pricing, structures the record, and caches it inside the `pending_booking` field of the active `CallSession`. The agent then prompts the user for verification.
2. **Commit Phase**: If the user confirms (saying "yes" or "ஆம்"), the LLM triggers the `commit_booking` tool. The tool retrieves the payload from the session store, creates a database transaction, clears the session buffer, and returns the formal booking identifier. If no booking was staged, the request fails gracefully.

---

## 🚀 Setup & Execution

### 1. Requirements
Ensure Python 3.10+ and a PostgreSQL/Redis instance are available (or run mock fallbacks for testing).

### 2. Installation
```bash
pip install -r requirements.txt
```

### 3. Environment Configuration
Create a `.env` file in the root directory:
```env
ENV=development
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/hall_booking
REDIS_URL=redis://localhost:6379/0
LLM_API_KEY=your_llm_key
STT_PROVIDER=sarvam
STT_API_KEY=your_sarvam_key
TTS_PROVIDER=sarvam
TTS_API_KEY=your_sarvam_key
```

### 4. Running the Server
```bash
uvicorn main:app --reload
```
