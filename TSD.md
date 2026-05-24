Technical Specification Document (TSD)
Project Title

Closira AI Customer Support Workflow System

Version: 1.0
Author: Ayush Kumar
Date: May 2026

1. Overview

This document defines the implementation architecture, technical design decisions, module interactions, APIs, file structure, data schemas, prompts, execution flow, and component-level specifications for the Closira AI Customer Support Workflow System.

This system uses a modular multi-agent workflow to create a safe AI customer support pipeline.

The implementation will use:

Python 3.11+
OpenRouter API
OpenAI SDK
JSON data storage
CLI interaction

No frontend or database will be used.

2. Technical Architecture

System Architecture:

                   ┌────────────────┐
                   │ Customer Input │
                   └────────┬───────┘
                            │
                            ▼
               ┌─────────────────────┐
               │ Conversation Manager│
               └────────┬────────────┘
                        │
        ┌───────────────┼────────────────┐
        │               │                │
        ▼               ▼                ▼

┌────────────┐ ┌──────────────┐ ┌───────────────┐
│ FAQ Agent  │ │ Lead Agent   │ │ Escalation    │
│            │ │              │ │ Agent         │
└─────┬──────┘ └──────┬───────┘ └──────┬────────┘
      │               │                │
      └───────────────┴────────────────┘
                      │
                      ▼
          ┌──────────────────────┐
          │ Safety Reviewer Agent│
          └──────────┬───────────┘
                     │
              Approved?
                /     \
              Yes      No
               |        |
               ▼        ▼

        Send Response Escalate Human

                     │
                     ▼
         ┌────────────────────┐
         │ Summary Generator  │
         └────────────────────┘
3. Project Directory Structure
closira-ai-assignment/

│

├── agents/
│   ├── faq_agent.py
│   ├── qualification_agent.py
│   ├── escalation_agent.py
│   ├── review_agent.py
│   └── summary_agent.py
│
├── data/
│   ├── sop.json
│   └── leads.json
│
├── prompts/
│   ├── faq_prompt.txt
│   ├── review_prompt.txt
│   ├── qualification_prompt.txt
│   └── summary_prompt.txt
│
├── utils/
│   ├── llm.py
│   ├── parser.py
│   ├── logger.py
│   ├── config.py
│   └── memory.py
│
├── logs/
│   └── system.log
│
├── test_transcripts/
│   ├── scenario_1.md
│   ├── scenario_2.md
│   ├── scenario_3.md
│   ├── scenario_4.md
│   └── scenario_5.md
│
├── main.py
├── README.md
├── requirements.txt
├── .env
├── prompt_design.md
├── PRD.md
├── SRS.md
└── TSD.md
4. Component Specifications
4.1 Conversation Manager

File:

main.py

Responsibilities:

receive user input
maintain session state
orchestrate workflow execution
invoke agents
maintain conversation history
route escalation flow
trigger summary generation

Methods:

start_session()

process_message()

route_agent()

generate_summary()

end_session()
4.2 FAQ Agent

File:

agents/faq_agent.py

Responsibilities:

answer SOP questions
prevent hallucinations
generate confidence score

Input:

user_message
sop_data
conversation_history

Output:

{
"answer":"",
"confidence":0.91,
"needs_escalation":false,
"reason":""
}

Implementation:

class FAQAgent:

    def respond():
        pass

Workflow:

Load SOP

↓

Construct prompt

↓

Call LLM

↓

Parse response

↓

Return structured object

4.3 Lead Qualification Agent

File:

agents/qualification_agent.py

Responsibilities:

ask qualification questions
track completed questions
store responses

Questions:

1 What type of business do you run?

2 How large is your team?

3 What tools do you currently use?

Class:

class QualificationAgent:

      ask_next()

      save_response()

      is_complete()

Output:

{
"business_type":"",
"team_size":"",
"tools":""
}
4.4 Escalation Agent

File:

agents/escalation_agent.py

Responsibilities:

detect escalation triggers
return reasons

Detection Rules:

Complaint:

[
"terrible",
"refund",
"bad",
"frustrated",
"angry"
]

Medical:

[
"side effect",
"medical advice",
"pain"
]

Negotiation:

[
"discount",
"cheaper",
"special price"
]

Human Request:

[
"human",
"agent",
"support person"
]

Class:

class EscalationAgent:

      detect()

Output:

{
"escalate":true,
"reason":"complaint"
}
4.5 Safety Reviewer Agent

File:

agents/review_agent.py

Purpose:

Final response verification before delivery.

Responsibilities:

Verify:

SOP grounding
confidence threshold
unsupported claims
escalation conditions

Input:

customer_message

generated_response

confidence

sop

Output:

{
"approved":true,
"risk":"low",
"reason":""
}

Class:

class ReviewAgent:

      validate()

Review Workflow:

Response Generated

↓

Compare against SOP

↓

Check escalation rules

↓

Check confidence

↓

Approve/Reject

4.6 Summary Agent

File:

agents/summary_agent.py

Responsibilities:

Generate structured summary

Input:

conversation_history

lead_data

escalation_logs

Output:

Intent:

Lead Information:

SOP Gaps:

Escalations:

Recommended Action:

Class:

class SummaryAgent:

      generate()
5. Utility Components
5.1 LLM Service

File:

utils/llm.py

Responsibilities:

Centralized API access.

Implementation:

from openai import OpenAI

client=OpenAI(
base_url="https://openrouter.ai/api/v1",
api_key=API_KEY
)

Method:

call_llm(
system_prompt,
user_prompt
)

Benefits:

Single change point for model swapping.

5.2 Parser Utility

File:

utils/parser.py

Responsibilities:

Parse LLM structured outputs

Handle malformed responses

Functions:

parse_json()

safe_extract()
5.3 Memory Manager

File:

utils/memory.py

Responsibilities:

Maintain conversation state.

Data:

conversation=[]

lead_info={}

escalations=[]

Methods:

add_message()

store_lead()

get_history()
5.4 Logger

File:

utils/logger.py

Responsibilities:

Log:

escalations
API errors
review failures
summaries

Example:

INFO:

Escalation Triggered

reason=medical_question

confidence=.42
6. Prompt Specifications
FAQ Prompt

System Prompt:

You are a customer support assistant for Bloom Aesthetics Clinic.

You may ONLY answer using provided SOP information.

Never invent information.

If information does not exist:

say information unavailable

set escalation=true

Return only JSON:

{
"answer":"",
"confidence":"",
"needs_escalation":"",
"reason":""
}
Reviewer Prompt
Review generated response.

Determine:

1 supported by SOP?

2 confidence sufficient?

3 unsupported claims?

Return:

{
"approved":true,
"risk":"",
"reason":""
}
Summary Prompt
Generate structured summary.

Include:

Intent

Lead Details

SOP gaps

Escalation reasons

Next action
7. API Specification

Endpoint:

POST

https://openrouter.ai/api/v1/chat/completions

Request:

{
"model":"deepseek/deepseek-chat",

"messages":[
{
"role":"system",
"content":"..."
},
{
"role":"user",
"content":"..."
}
]
}

Response:

{
"choices":[
{
"message":{
"content":"..."
}
}
]
}
8. Data Schemas
SOP
{
"business":"Bloom Aesthetics Clinic",

"hours":"Mon-Sat,9am-7pm",

"services":{
"Botox":"£200",
"Fillers":"£250"
},

"booking":"WhatsApp",

"cancellation":"24hrs"
}
Lead Information
{
"business_type":"",

"team_size":"",

"tools":""
}
Escalation Log
{
"time":"",

"reason":"",

"message":""
}
9. Sequence Flow
User Input

↓

FAQ Agent

↓

Escalation Agent

↓

Reviewer Agent

↓

Approved?

↓

Yes → Send Response

No → Human Escalation

↓

Lead Qualification

↓

Summary Generation
10. Error Handling

API Failure:

Retry once

Log issue

Show user message

Malformed JSON:

Parser fallback

Missing SOP:

Terminate application

Reviewer failure:

Automatic escalation

11. Performance Targets

Average response:

<5 seconds

Escalation detection:

<1 second

Summary generation:

<3 seconds

12. Future Extension Hooks

Future plug-ins:

WhatsApp integration
Email channel
Voice support
RAG retrieval
database persistence
analytics dashboard
multi-language support
13. Implementation Notes For AI Coding Agent

Rules:

Use modular architecture
Use class-based agents
Use structured JSON outputs only
No hardcoded API keys
Keep prompts separate from code
Use type hints
Add logging
Add exception handling
Avoid LangChain
Reviewer agent must run before sending responses
Use OpenRouter endpoint compatibility with OpenAI SDK
Keep implementation readable over optimized