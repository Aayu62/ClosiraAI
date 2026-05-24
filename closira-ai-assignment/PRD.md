Product Requirements Document (PRD)
Project Title

Closira AI Customer Support Workflow System

Version: 1.0
Author: Ayush Kumar
Date: May 2026

1. Product Overview

Closira is an AI-powered customer communication platform designed for Small and Medium Businesses (SMBs). Businesses receive customer inquiries through multiple channels and need intelligent systems that can answer questions accurately, qualify leads, detect situations requiring human intervention, and summarize customer interactions.

This project aims to build a lightweight AI workflow prototype demonstrating a reliable, safe, and modular customer support system.

The system will simulate an end-to-end customer support conversation using Large Language Models (LLMs) integrated through OpenRouter APIs.

The workflow will:

Answer customer questions using business SOP information only
Ask structured lead qualification questions
Detect escalation conditions
Validate AI responses through an additional safety/reviewer layer
Generate conversation summaries

The implementation will run as a Python CLI application.

No frontend interface is required.

2. Problem Statement

Traditional customer support systems often suffer from:

Hallucinated AI responses
Lack of control over business-specific information
Poor escalation handling
Inconsistent lead collection
Limited transparency into AI decision-making

Businesses require systems that prioritize reliability over creativity.

The proposed system addresses these concerns by introducing structured prompts, SOP grounding, confidence-based escalation, and an additional reviewer agent.

3. Product Goals
Primary Goals

Build a modular AI workflow that:

Responds strictly from SOP knowledge
Prevents hallucinations
Qualifies leads
Escalates uncertain situations safely
Generates structured conversation summaries
Secondary Goals

Demonstrate:

Prompt engineering ability
Multi-agent workflow design
Reliability and safety thinking
Modular software architecture
AI orchestration skills
4. Success Metrics

The system will be considered successful if:

Metric	Target
SOP answer accuracy	>95%
Hallucinated responses	0
Escalation detection accuracy	>90%
Required lead fields collected	100%
Summary generation success	100%
Structured output generation	100%
5. Target Users

Primary user:

Customer support representatives and SMB businesses.

Simulated user:

Potential customers interacting with Bloom Aesthetics Clinic.

Example customer intents:

Asking pricing information
Asking booking details
Asking operational questions
Expressing complaints
Requesting unavailable services
Seeking medical advice
Negotiating pricing
6. User Stories
FAQ Interaction

As a customer,

I want to ask service questions,

So that I can receive business information immediately.

Lead Qualification

As a business,

I want customer details collected,

So that future follow-ups become easier.

Escalation

As a customer,

I want sensitive concerns redirected to a human,

So that important issues receive appropriate handling.

Reliability

As a business owner,

I want the AI to avoid making up information,

So that customer trust is maintained.

Summary

As a support team member,

I want a concise conversation summary,

So that handoffs become efficient.

7. Functional Requirements
FR-1 FAQ Answering

System shall:

Load SOP data from JSON
Restrict responses to SOP content
Reject unsupported information
return confidence scores
identify unanswered questions

Example:

Customer:

"What are Botox prices?"

Expected:

"Botox services start from £200."

FR-2 Lead Qualification

System shall ask:

Question 1:

What type of business are you in?

Question 2:

How large is your team?

Question 3:

What tools are you currently using?

Responses must be stored.

FR-3 Escalation Detection

System shall escalate if:

Complaint detected

Examples:

terrible service
unhappy
frustrated
Medical question detected

Examples:

side effects
medical advice
Pricing negotiation detected

Examples:

discount
cheaper option
User requests human

Examples:

human please
talk to support
Low confidence score

confidence < threshold

Multiple unanswered questions

greater than 2

FR-4 Reviewer Agent

An additional validation agent will inspect generated responses before delivery.

Purpose:

Improve reliability and reduce hallucinations.

Reviewer agent responsibilities:

Verify SOP consistency
Verify confidence threshold
Verify escalation rules
Detect unsupported claims

Reviewer outputs:

{
"approved":true,
"reason":"",
"risk":"low"
}

If approval fails:

System escalates conversation.

FR-5 Conversation Summary

Generate:

Customer Intent

Collected Details

Lead Information

SOP gaps

Escalation reasons

Recommended next action

Example:

Intent:
Botox inquiry

Lead:
Clinic owner
Team size:10

SOP gaps:
Asked about laser treatment

Next Action:
Human follow-up
8. Non Functional Requirements
Reliability

System must avoid fabricated information.

Safety

System must fail safely.

Unknown information should escalate.

Modularity

Components should be independently replaceable.

Maintainability

Prompts and agents should remain isolated.

Extensibility

Additional SOPs should require minimal code changes.

Explainability

Escalation decisions should include reasons.

9. Assumptions
SOP data will exist in JSON format
OpenRouter API availability assumed
Customer interaction simulated through CLI
Single-user session
English language only
10. Constraints

No frontend UI

No database

No vector database

No external retrieval systems

No LangChain dependency

Must use Python

Must use LLM APIs through OpenRouter

11. Dependencies

Python 3.11+

OpenRouter API key

OpenAI SDK

python-dotenv

JSON SOP files

12. Risks
Risk	Mitigation
Model hallucination	SOP grounding
Incorrect escalation	Hybrid rule + LLM checks
Low quality model output	Reviewer agent
API failures	Error handling
Missing SOP coverage	Human escalation
13. Future Improvements

Multi-channel support

WhatsApp integration

Conversation database

RAG retrieval

Vector search

Admin dashboard

Analytics

Multilingual support

14. Product Workflow
Customer Message

↓

FAQ Agent

↓

Lead Qualification Agent

↓

Escalation Detection

↓

Reviewer Agent

↓

Pass?
     /      \
   Yes      No
    |         |
 Send      Escalate

↓

Conversation Summary
15. Deliverables

GitHub repository

Prompt Design document

Test transcripts

README

CLI implementation

Video walkthrough

PRD

SRS

Technical Specification Document