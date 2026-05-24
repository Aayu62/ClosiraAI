Software Requirements Specification (SRS)
Project Title

Closira AI Customer Support Workflow System

Version: 1.0
Author: Ayush Kumar
Date: May 2026

1. Introduction
1.1 Purpose

This Software Requirements Specification (SRS) defines the functional and non-functional requirements for the Closira AI Customer Support Workflow System.

The purpose of this system is to build a modular AI-powered support workflow that:

answers customer questions from predefined SOPs
collects lead qualification information
detects escalation conditions
validates responses through a safety reviewer layer
generates conversation summaries

The system serves as a prototype demonstrating AI orchestration and safe LLM behavior.

1.2 Scope

The system provides a command-line based conversational workflow for SMB customer support.

The software will:

process customer messages
retrieve business SOP information
generate controlled AI responses
collect lead data
determine escalation conditions
validate generated responses
summarize conversations

The application does not include:

frontend interfaces
multi-user support
persistent databases
external retrieval systems
authentication systems
1.3 Intended Audience

This document is intended for:

software developers
AI engineers
reviewers
internship evaluators
AI coding assistants
2. Overall Description
2.1 Product Perspective

The system is a standalone CLI application.

It acts as an orchestration layer over LLM APIs.

The architecture follows a modular multi-agent approach:

User

↓

Conversation Controller

↓

FAQ Agent

↓

Lead Qualification Agent

↓

Escalation Agent

↓

Safety Reviewer Agent

↓

Conversation Summary Agent

Each agent performs a single responsibility.

2.2 Product Functions

Major system functions:

FAQ answering

Respond only using SOP content

Lead qualification

Collect:

business type
team size
current tools
Escalation detection

Detect:

complaint
medical concerns
negotiation attempts
explicit requests
low confidence
repeated unanswered questions
Reviewer validation

Validate generated responses before customer delivery

Conversation summary generation

Generate structured session summaries

2.3 User Characteristics

Users require no technical expertise.

Customers may:

ask simple questions
ask unsupported questions
become frustrated
provide incomplete responses
ask multiple questions
2.4 Constraints

System constraints:

Python implementation required
CLI only
OpenRouter APIs
SOP-driven responses
no frontend
no vector DB
no LangChain
single conversation session
2.5 Assumptions

Assumptions:

API connectivity exists
SOP data is valid JSON
model returns valid outputs
environment variables configured correctly
3. External Interface Requirements
3.1 User Interface

System interface:

CLI terminal interaction

Example:

Customer:
What are your Botox prices?

AI:
Botox services start from £200.
3.2 Hardware Interface

No hardware integration required.

3.3 Software Interface

External software:

Component	Purpose
OpenRouter	LLM API
OpenAI SDK	API wrapper
dotenv	API configuration
JSON	SOP storage
3.4 Communication Interface

Protocol:

HTTPS

Request type:

REST API

Response type:

JSON

4. System Features and Functional Requirements
Feature 1 FAQ Agent
Description

The FAQ Agent answers customer questions using SOP information.

Inputs

Customer message

SOP content

Conversation history

Processing

Inject SOP into system prompt

Generate grounded response

Return structured output

Outputs
{
"answer":"",
"confidence":0.91,
"needs_escalation":false,
"reason":""
}
Functional Requirements

FR-1.1

System shall load SOP from JSON

FR-1.2

System shall answer from SOP only

FR-1.3

System shall not invent unsupported information

FR-1.4

System shall provide confidence score

Feature 2 Lead Qualification Agent
Description

Collect customer information.

Inputs

Conversation state

Questions

Question 1:

What type of business do you run?

Question 2:

How large is your team?

Question 3:

What tools do you currently use?

Outputs
{
"business_type":"",
"team_size":"",
"tools":""
}
Functional Requirements

FR-2.1

System shall ask qualification questions sequentially

FR-2.2

System shall store responses

FR-2.3

System shall skip already answered questions

Feature 3 Escalation Detection Agent
Description

Determine if conversation should be escalated.

Inputs

Customer message

AI confidence score

Conversation history

Detection Conditions

Complaint

Medical question

Pricing negotiation

Human request

Low confidence

Multiple unanswered questions

Outputs
{
"escalate":true,
"reason":"Complaint detected"
}
Functional Requirements

FR-3.1

System shall detect complaint language

FR-3.2

System shall detect medical questions

FR-3.3

System shall detect explicit escalation requests

FR-3.4

System shall detect confidence threshold violations

Feature 4 Safety Reviewer Agent
Description

Validate AI outputs before customer delivery.

Inputs

Customer message

AI response

SOP content

Confidence score

Processing

Check:

SOP consistency
unsupported claims
escalation rules
confidence threshold
Outputs
{
"approved":true,
"reason":"",
"risk":"low"
}
Functional Requirements

FR-4.1

System shall verify SOP grounding

FR-4.2

System shall reject unsupported claims

FR-4.3

System shall identify risk level

FR-4.4

System shall block unsafe responses

Feature 5 Conversation Summary Agent
Description

Generate session summary.

Inputs

Conversation history

Lead information

Escalation logs

Outputs
Intent:

Lead Information:

Conversation Details:

SOP Gaps:

Escalation Reasons:

Recommended Action:
Functional Requirements

FR-5.1

System shall generate summary after session completion

FR-5.2

System shall include escalation details

FR-5.3

System shall include SOP gaps

5. Data Requirements
SOP Data Schema
{
"business":"Bloom Aesthetics Clinic",

"hours":"Mon-Sat 9am-7pm",

"services":{
"Botox":"from £200",
"Fillers":"from £250",
"Consultation":"Free"
},

"booking":"WhatsApp or website",

"cancellation":"24hr required",

"escalate_if":[
"complaint",
"medical question",
"pricing negotiation"
]
}
Lead Data Schema
{
"business_type":"",
"team_size":"",
"tools":""
}
Escalation Log Schema
{
"time":"",
"reason":"",
"message":""
}
6. Non Functional Requirements
Performance

Average API response:

<5 seconds

Reliability

No hallucinated responses permitted

Availability

System should continue operation after API errors

Maintainability

Prompts isolated from business logic

Scalability

Additional agents should be pluggable

Explainability

All escalation decisions require reasons

7. Error Handling Requirements

ER-1

Invalid API key

Expected:

Display configuration error

ER-2

Network timeout

Expected:

Retry or display failure message

ER-3

Malformed model output

Expected:

Use fallback parser

ER-4

Missing SOP data

Expected:

Stop execution and log issue

8. Security Requirements

API keys stored in:

.env

No hardcoded secrets

No storage of customer PII

Logs should exclude sensitive information

9. Logging Requirements

System shall log:

conversation events

escalations

reviewer failures

API errors

summary generation events

Example:

INFO:
Escalated conversation

reason=medical_question

confidence=.42
10. Acceptance Criteria

System passes if:

✓ FAQ answers use SOP only

✓ unsupported questions escalate

✓ complaints escalate

✓ reviewer catches unsafe output

✓ lead information collected

✓ summaries generated

✓ logs created

✓ structured outputs returned