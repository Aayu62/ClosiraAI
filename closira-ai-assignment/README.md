# Closira AI Customer Support Workflow System

A modular, production-quality Python CLI application implementing an AI-powered customer support workflow for SMBs.

## Project Overview

Closira is an intelligent customer support system that:
- Answers questions using a two-layer information system (SOP + Knowledge Base)
- Escalates medical safety questions immediately without any AI answer
- Qualifies leads through structured questions
- Detects escalation conditions using hybrid rule-based + LLM approaches
- Validates responses through a safety reviewer agent
- Generates structured conversation summaries
- Persists every session to disk in real time

**Technology:** Python 3.11+ | OpenRouter API | OpenAI SDK | JSON storage

## Architecture

```
Customer Input
    ↓
Conversation Manager
    ↓
┌─────────────────────────────────────────┐
│ FAQ Agent (3-Layer Lookup)              │
│                                         │
│  Layer 0: Medical Safety Gate           │ → Immediate escalation
│      ↓ (pass)                           │
│  Layer 1: SOP (strict business facts)   │ → Pricing, hours, booking, location
│      ↓ (not found)                      │
│  Layer 2: Knowledge Base (educational)  │ → Treatment info, descriptions
│      ↓ (not found)                      │
│  Layer 3: Escalate                      │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────┐
│ Escalation Agent            │ → Detects escalation triggers
└─────────────────────────────┘
    ↓
┌─────────────────────────────┐
│ Safety Reviewer Agent       │ → Validates SOP + KB grounding
└─────────────────────────────┘
    ↓
Approved? → Yes → Send Response
    ↓ No
    Escalate to Human
    ↓
┌─────────────────────────────┐
│ Lead Qualification Agent    │ → Collect business info
└─────────────────────────────┘
    ↓
┌─────────────────────────────┐
│ Summary Agent               │ → Generate session summary
└─────────────────────────────┘
    ↓
Summary Output
```

## Directory Structure

```
closira-ai-assignment/
├── agents/                      # Multi-agent implementations
│   ├── faq_agent.py            # FAQ answering from SOP
│   ├── qualification_agent.py   # Lead qualification
│   ├── escalation_agent.py      # Escalation detection
│   ├── review_agent.py          # Safety reviewer
│   └── summary_agent.py         # Summary generation
├── data/
│   ├── sop.json                # Business Standard Operating Procedures
│   ├── service_knowledge.json  # Knowledge Base (treatments, contact, location)
│   └── leads.json              # Lead data storage
├── prompts/                     # External prompt files
│   ├── faq_prompt.txt
│   ├── review_prompt.txt
│   ├── qualification_prompt.txt
│   └── summary_prompt.txt
├── utils/                       # Shared utilities
│   ├── config.py               # Configuration management
│   ├── llm.py                  # LLM client wrapper
│   ├── parser.py               # JSON parsing & validation
│   ├── logger.py               # Logging setup
│   ├── memory.py               # Conversation memory
│   └── session_manager.py      # Persistent session recording
├── sessions/                    # Auto-created session JSON files
│   └── session_YYYYMMDD_HHMMSS.json
├── logs/                        # Application logs
├── test_transcripts/            # Example conversations
│   ├── in_scope.md
│   ├── out_of_scope.md
│   ├── complaint.md
│   ├── lead.md
│   ├── summary.md
│   ├── kb_botox.md             # KB: What is Botox?
│   ├── kb_location.md          # KB: Where are you located?
│   ├── kb_whatsapp_booking.md  # KB: WhatsApp booking
│   └── kb_medical_escalation.md # Medical safety escalation
├── main.py                      # Application entry point
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment template
├── README.md                    # This file
├── prompt_design.md             # Prompt engineering details
└── .gitignore
```

## Setup Instructions

### 1. Clone Repository
```bash
cd closira-ai-assignment
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. OpenRouter Setup

Get your API key from [OpenRouter.ai](https://openrouter.ai):
1. Create account
2. Go to Settings → API Keys
3. Copy your API key

### 5. Environment Configuration
```bash
cp .env.example .env
```

Edit `.env`:
```
OPENROUTER_API_KEY=your_actual_api_key_here
MODEL=deepseek/deepseek-chat
LOG_LEVEL=INFO
```

### 6. Run Application
```bash
python main.py
```

## How to Run

### Start Conversation
```bash
python main.py
```

You'll see:
```
============================================================
Closira AI Customer Support Workflow
============================================================
Welcome to Bloom Aesthetics Clinic AI Support
Type 'quit' to end the conversation
============================================================

You: What are Botox prices?

AI: Botox services at Bloom Aesthetics Clinic start from £200. 
For more details or to book a consultation, you can reach us 
via WhatsApp or our website.

You: ...
```

### Chat Commands

| Command | Description |
|---|---|
| `show session` | Display current session stats (no LLM call) |
| `quit` / `exit` / `bye` | Generate summary, save session, exit cleanly |

**`show session` output:**
```
=============================================
Current Session Info
=============================================
Session ID:   session_20260524_004133
Messages:     10
Escalations:  2
Duration:     3m 42s

Lead Data:
  Business Type: Clinic
  Team Size:     8
  Tools:         Not collected
=============================================
```

**`quit` output:**
```
Preparing conversation summary...

================================================
SESSION SUMMARY
Intent: Botox inquiry
...
================================================

Session saved successfully: sessions/session_20260524_004133.json
Thank you for contacting Bloom Aesthetics Clinic.
```

### Workflow Flow

1. **FAQ Interaction** - Ask questions about services, hours, pricing
2. **Escalation Detection** - Complaints, medical questions, negotiation attempts
3. **Safety Review** - All responses validated before sending
4. **Lead Qualification** - Answer 3 qualification questions
5. **Summary Generation** - Automatic session summary at end

### Example Interactions

**In-Scope Question:**
```
You: What are your hours?
AI: We're open Mon-Sat, 9am-7pm.
```

**Out-of-Scope Question:**
```
You: Do you offer laser treatments?
AI: [ESCALATED] This information is not available in our system...
```

**Complaint Detection:**
```
You: I'm really frustrated with your prices!
AI: [ESCALATED] Your concern has been escalated to our support team...
```

## Folder Explanation

### `/agents/`
Each agent is a self-contained class implementing a single responsibility:
- **FAQ Agent**: Loads SOP, answers questions with confidence scores
- **Qualification Agent**: Asks 3 sequential lead qualification questions
- **Escalation Agent**: Rule-based + LLM hybrid detection
- **Review Agent**: Validates responses before delivery
- **Summary Agent**: Generates structured summaries

### `/data/`
- **sop.json**: Strict business facts (hours, services, booking, pricing)
- **service_knowledge.json**: Knowledge Base (treatment descriptions, clinic contact, location)
- **leads.json**: Collected lead data

### `/prompts/`
External prompt files (NOT hardcoded in code):
- **faq_prompt.txt**: SOP-grounded FAQ instructions
- **review_prompt.txt**: Safety validation instructions
- **qualification_prompt.txt**: Lead qualification instructions
- **summary_prompt.txt**: Summary generation instructions

### `/utils/`
Shared functionality:
- **config.py**: Configuration management
- **llm.py**: LLMClient wrapper for OpenRouter
- **parser.py**: JSON parsing with fallbacks
- **logger.py**: Structured logging to file + console
- **memory.py**: Conversation history management

### `/logs/`
- **system.log**: Rotating application logs

### `/test_transcripts/`
Example conversations demonstrating:
- In-scope questions (answered from SOP)
- Out-of-scope questions (escalated)
- Complaints (escalated)
- Lead qualification
- Summaries

## Features

### Hallucination Prevention
- ✓ Two-layer grounding: SOP (strict) + Knowledge Base (educational)
- ✓ Medical safety gate — escalates before any AI answer
- ✓ Realistic confidence scoring (never 1.0)
- ✓ Low confidence auto-escalation
- ✓ Safety reviewer validates SOP and KB grounding

### Escalation Detection
Automatic escalation for:
- Complaints: "terrible", "frustrated", "angry", "refund"
- Medical safety (Layer 0 gate): "side effects", "pregnant", "pregnancy", "breastfeeding", "treatment risk", "medical suitability"
- Medical keywords: "pain", "doctor", "hospital", "allergy"
- Negotiation: "discount", "cheaper"
- Human requests: "talk to agent"
- Low confidence (<0.70)
- Multiple unanswered questions (>2)

### Confidence Scoring
- Exact SOP match: 0.90–0.95
- Knowledge Base educational answer: 0.80–0.88
- Partial information: 0.50–0.70
- Unknown / not found: 0.10–0.30
- Never returns 1.0

### Lead Qualification
Structured questions:
1. Business type
2. Team size
3. Current tools used

### Conversation Memory
Maintains:
- Full conversation history
- Lead information
- Escalation logs
- Session metadata

### Comprehensive Logging
- API failures
- Escalation triggers
- Review decisions
- Summary generation
- Error tracking

## Configuration

### Model Selection
Edit `.env` to change model:
```
MODEL=deepseek/deepseek-chat      # Default
MODEL=meta-llama/llama-2-70b      # Alternative
```

### Confidence Threshold
Edit `utils/config.py`:
```python
self.confidence_threshold: float = 0.70
```

### Escalation Keywords
Edit `agents/escalation_agent.py` to customize triggers.

## Customizing Knowledge Base

The Knowledge Base is stored in `data/service_knowledge.json`. You can modify it directly — **no code changes required**. The system automatically adapts on the next run.

### What you can customize:

**Add or update a treatment:**
```json
"HydraFacial": {
  "description": "A multi-step facial treatment that cleanses, exfoliates, and hydrates the skin.",
  "common_uses": ["Deep cleansing", "Hydration", "Anti-aging"],
  "duration": "Results last 4–6 weeks.",
  "disclaimer": "Medical suitability questions require specialist guidance."
}
```

**Update WhatsApp number or booking link:**
```json
"clinic_information": {
  "whatsapp_booking": {
    "phone": "+91 XXXXXXXXXX",
    "booking_link": "https://wa.me/91XXXXXXXXXX?text=Hi"
  }
}
```

**Update clinic address or Google Maps link:**
```json
"clinic_information": {
  "address": "Your New Address, City, State, Country",
  "google_maps": "https://maps.app.goo.gl/your-link"
}
```

**Add a new FAQ extension:**
```json
"faq_extensions": {
  "parking": "Free parking is available outside the clinic.",
  "accessibility": "The clinic is wheelchair accessible."
}
```

### Knowledge Base structure:
| Key | Purpose |
|---|---|
| `clinic_information` | Name, address, Google Maps, WhatsApp contact |
| `Botox` / `Fillers` / `Consultation` | Treatment descriptions, uses, duration |
| `faq_extensions` | Additional FAQ topics (booking, location, contact) |

> The FAQ Agent checks the Knowledge Base as Layer 2 after the SOP. Any new treatment entry with a `description` field will be automatically matched when customers ask about it by name.

## Session Storage and Persistence

Every run of `python main.py` automatically creates a new uniquely-named session file.

### How it works

- On startup, `SessionManager` creates `sessions/session_YYYYMMDD_HHMMSS.json`
- Every user message and AI response is written to disk **immediately** after it occurs
- Escalations and lead data are persisted the moment they are captured
- If the application crashes mid-conversation, all messages up to that point are already saved
- On `quit`, the final summary is generated, saved into the session file, and `status` is set to `closed`

### Session file location

```
closira-ai-assignment/
└── sessions/
    ├── session_20260524_004133.json   ← run 1
    ├── session_20260524_011500.json   ← run 2
    └── ...                            ← one file per run
```

### Session file schema

```json
{
  "session_id": "session_20260524_004133",
  "start_time": "2026-05-24T00:41:33",
  "end_time": "2026-05-24T00:45:15",
  "status": "closed",
  "customer_intent": "Botox pricing inquiry",
  "messages": [
    {"timestamp": "...", "role": "user",      "content": "What is Botox?"},
    {"timestamp": "...", "role": "assistant", "content": "Botox is...", "confidence": 0.85}
  ],
  "lead_information": {
    "business_type": "Clinic",
    "team_size": "8",
    "tools": "None"
  },
  "escalations": [
    {"timestamp": "...", "reason": "low_confidence", "message": "cake recipe"}
  ],
  "summary": { ... },
  "statistics": {
    "message_count": 10,
    "escalation_count": 2
  }
}
```

### Use cases

- **Debugging**: inspect exactly what the AI said and with what confidence
- **Auditing**: full timestamped record of every escalation
- **Lead review**: see collected lead data per session
- **Crash recovery**: messages are never lost — they are on disk before the next prompt
- **Analytics**: count sessions, escalation rates, common SOP gaps across files

### Inspecting a session

```bash
# Windows
type sessions\session_20260524_004133.json

# Unix
cat sessions/session_20260524_004133.json
```

## Error Handling

The system handles:
- ✓ Session files persist every message to disk in real time
- ✓ Crash-safe atomic writes (`.tmp` → rename)
- ✓ `show session` command for live stats
- ✓ Clean exit with summary and session close
- ✓ Invalid API keys → Clear error message
- ✓ Network timeouts → Retry + fallback
- ✓ Malformed JSON → Parser fallback
- ✓ Missing SOP → Graceful failure
- ✓ Reviewer failures → Auto-escalation

## Tradeoffs & Design Decisions

### Why No Database?
- Simplicity for assignment context
- Single-session scope
- JSON sufficient for requirements
- Can be added later without changing architecture

### Why Separate Prompts?
- Prompts are business logic, not code
- Easy to tweak without redeploying
- Clear separation of concerns
- Supports prompt versioning

### Why Hybrid Escalation?
- Rule-based: Fast, deterministic (complaints, medical)
- LLM: Semantic understanding (low confidence)
- Combined: Best of both approaches

### Why Safety Reviewer?
- Second validation layer
- Catches LLM hallucinations
- Ensures customer safety
- Auditable decision trail

## Code Quality

✓ Type hints throughout
✓ Comprehensive logging
✓ Exception handling
✓ Modular class design
✓ PEP8 formatting
✓ Docstrings
✓ No code duplication

## Limitations

1. Single-user CLI only (no multi-channel)
2. English language only
3. Session-based (persistent JSON files in `sessions/`)
4. No RAG/vector search
5. No authentication/authorization
6. Demo-scale (single SOP file)

## Future Improvements

- [ ] Multi-channel support (WhatsApp, Email, Web)
- [ ] Vector database + RAG for dynamic SOP
- [ ] LLM fine-tuning on domain data
- [ ] Admin dashboard
- [ ] Analytics & reporting
- [ ] Multilingual support
- [ ] Sentiment analysis
- [ ] A/B testing framework
- [ ] Performance profiling

## Acceptance Criteria Met

✓ FAQ answers from SOP only
✓ Unsupported questions escalate
✓ Complaints automatically escalated
✓ Reviewer catches unsafe output
✓ Lead information collected
✓ Summaries generated
✓ Logs created (system.log)
✓ Structured JSON outputs
✓ Modular architecture
✓ Type hints & documentation
✓ Error handling
✓ CLI-only implementation
✓ OpenRouter integration
✓ No hallucinations

## Running Tests

See `/test_transcripts/` for example conversations:
```bash
cat test_transcripts/in_scope.md              # In-scope Q&A (SOP)
cat test_transcripts/out_of_scope.md          # Out-of-scope escalation
cat test_transcripts/complaint.md             # Complaint escalation
cat test_transcripts/lead.md                  # Lead qualification
cat test_transcripts/summary.md               # Session summary
cat test_transcripts/kb_botox.md              # KB: What is Botox?
cat test_transcripts/kb_location.md           # KB: Where are you located?
cat test_transcripts/kb_whatsapp_booking.md   # KB: WhatsApp booking
cat test_transcripts/kb_medical_escalation.md # Medical safety escalation
```

## Logging

View logs:
```bash
tail -f logs/system.log
```

Log entries include:
- Agent processing steps
- Escalation triggers
- Review decisions
- Errors and warnings

## Support

For issues:
1. Check `logs/system.log` for detailed error messages
2. Verify `.env` configuration
3. Ensure OpenRouter API key is valid
4. Check internet connectivity

## Author

Ayush Kumar  
Closira AI - Customer Support Workflow System  
May 2026

## License

Educational project - Assignment submission
