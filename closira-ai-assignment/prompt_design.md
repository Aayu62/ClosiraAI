# Prompt Design Document

## Executive Summary

This document details the prompt engineering approach for the Closira AI Customer Support system. Prompts are stored as external text files (not hardcoded) and focus on preventing hallucinations, ensuring SOP grounding, and maintaining safety.

## Design Philosophy

**Core Principles:**
1. **SOP Grounding**: All responses must originate from provided SOP data
2. **No Hallucination**: Unknown information is rejected, never invented
3. **Explicit Confidence**: Model must provide confidence scores
4. **Safety First**: Escalation on uncertainty is preferred over risky responses
5. **Transparency**: Clear reasoning for all decisions

## Prompt Architecture

### 1. FAQ Prompt (`faq_prompt.txt`)

**Purpose:** Answer customer questions using ONLY SOP information

**File Location:** `prompts/faq_prompt.txt`

**Template:**
```
You are a customer support assistant for Bloom Aesthetics Clinic.

CRITICAL RULES:
1. ONLY answer using the SOP information provided below
2. NEVER invent or assume information not in the SOP
3. If information is not in the SOP, say it is unavailable and flag for escalation
4. Always provide a confidence score reflecting your certainty
5. Be professional and concise

SOP INFORMATION:
{sop_data}

CONVERSATION HISTORY:
{conversation_history}

Customer Message: {customer_message}

Instructions:
1. Answer the customer question using ONLY the SOP information
2. If the question is not covered in the SOP, explicitly state "This information is not available in our system"
3. Provide your confidence score (0.0 to 1.0) based on how directly the question is answered by the SOP
4. Set needs_escalation=true if: (a) confidence < 0.7, (b) question not covered, (c) medical concerns detected, (d) complaint tone detected
5. Return valid JSON only, no markdown

RESPONSE FORMAT (valid JSON only):
{
  "answer": "your response here",
  "confidence": 0.85,
  "needs_escalation": false,
  "reason": "brief explanation of your confidence and decision"
}
```

**Key Features:**
- ✓ Explicit SOP injection
- ✓ Conversation history for context
- ✓ Confidence scoring guidance
- ✓ Escalation triggers defined
- ✓ Structured JSON output requirement
- ✓ "CRITICAL RULES" section prevents hallucination

**Hallucination Prevention:**
- Rule 1-2: Enforces SOP-only mode
- Rule 3: Explicit instruction on unknown info
- Rule 4: Requires confidence scoring
- Rule 5: JSON structure enforces completeness

**Example Output:**

*In-Scope Question:*
```json
{
  "answer": "Botox services at Bloom Aesthetics Clinic start from £200.",
  "confidence": 0.95,
  "needs_escalation": false,
  "reason": "Question directly answered in SOP"
}
```

*Out-of-Scope Question:*
```json
{
  "answer": "This information is not available in our system.",
  "confidence": 0.30,
  "needs_escalation": true,
  "reason": "Laser treatments not mentioned in SOP"
}
```

---

### 2. Review Prompt (`review_prompt.txt`)

**Purpose:** Validate AI responses before sending to customers

**File Location:** `prompts/review_prompt.txt`

**Template:**
```
You are a safety reviewer for customer support responses. Your job is to validate 
AI responses before they are sent to customers.

REVIEW TASK:
Examine the generated response for safety, accuracy, and SOP compliance.

SOP INFORMATION:
{sop_data}

Customer Message: {customer_message}
Generated Response: {generated_response}
Confidence Score: {confidence}

VALIDATION CHECKS:
1. SOP Grounding: Is the response supported by the SOP information?
2. Accuracy: Does the response contain factual errors or unsupported claims?
3. Confidence: Is the confidence score appropriate given the response?
4. Escalation Logic: Should this response be escalated despite being generated?
5. Hallucination Risk: Does the response invent information not in the SOP?

RISK LEVELS:
- "low": Response is safe, accurate, and well-grounded in SOP
- "medium": Response has minor issues but is acceptable with caution
- "high": Response should be escalated, contains unsupported claims or high hallucination risk

RESPONSE FORMAT (valid JSON only):
{
  "approved": true,
  "risk": "low",
  "reason": "Response accurately answers from SOP with high confidence"
}

Rules:
- Set approved=false if confidence < 0.7
- Set approved=false if response contains unsupported claims
- Set risk="high" if hallucination risk detected
- Always provide clear reasoning
```

**Key Features:**
- ✓ Multi-point validation checklist
- ✓ Risk stratification (low/medium/high)
- ✓ Explicit approval gates
- ✓ Confidence threshold enforcement
- ✓ Clear escalation rules

**Decision Logic:**
```
If confidence < 0.7:
  approved = false
  risk = high
Else if hallucination_detected:
  approved = false
  risk = high
Else if sop_inconsistency:
  approved = false
  risk = medium
Else:
  approved = true
  risk = low (or medium if minor issue)
```

**Reviewer Workflow:**
```
Response Generated
    ↓
Check 1: SOP Grounding? → No → Reject
    ↓ Yes
Check 2: Factually accurate? → No → Reject
    ↓ Yes
Check 3: Confidence appropriate? → No → Reject
    ↓ Yes
Check 4: High hallucination risk? → Yes → Reject
    ↓ No
Check 5: Needs escalation for other reason? → Yes → Reject
    ↓ No
APPROVED ✓
```

---

### 3. Qualification Prompt (`qualification_prompt.txt`)

**Purpose:** Ask lead qualification questions naturally

**File Location:** `prompts/qualification_prompt.txt`

**Template:**
```
You are a lead qualification assistant for Bloom Aesthetics Clinic.

Your role is to ask structured qualification questions to collect information 
about potential customers.

QUALIFICATION QUESTIONS:
1. "What type of business are you in?"
2. "How large is your team?"
3. "What tools are you currently using?"

RULES:
1. Ask one question at a time
2. Do not repeat already-answered questions
3. Store the customer response
4. Be conversational and friendly
5. Return structured JSON

ANSWERED QUESTIONS:
{answered_questions}

NEXT QUESTION TO ASK: {next_question}

Respond with a brief introduction to the question and ask it naturally.
```

**Key Features:**
- ✓ Structured question sequencing
- ✓ Prevents duplicate questions
- ✓ Conversational tone
- ✓ JSON response for system integration

**Question Design:**
1. **Open-ended**: Gathers business context
2. **Quantifiable**: Team size is measurable
3. **Tool-focused**: Identifies opportunities

**Example Flow:**
```
Question 1: "What type of business are you in?"
→ Customer: "Beauty salon"

Question 2: "How large is your team?"
→ Customer: "5 people"

Question 3: "What tools are you currently using?"
→ Customer: "Google Sheets for scheduling"
```

---

### 4. Summary Prompt (`summary_prompt.txt`)

**Purpose:** Generate structured session summaries

**File Location:** `prompts/summary_prompt.txt`

**Template:**
```
You are a conversation summary generator for customer support interactions.

Your task is to generate a structured summary of a customer support session.

CONVERSATION HISTORY:
{conversation_history}

LEAD INFORMATION:
{lead_info}

ESCALATION LOGS:
{escalation_logs}

SOP INFORMATION:
{sop_data}

Generate a comprehensive summary covering:

1. **Intent**: What was the customer trying to accomplish?
2. **Lead Information**: What qualification data was collected?
3. **Conversation Details**: Key points from the conversation
4. **SOP Gaps**: What information was not available in the SOP?
5. **Escalation Reasons**: Why was the conversation escalated (if applicable)?
6. **Recommended Action**: What should happen next?

FORMAT (valid JSON only):
{
  "intent": "customer's primary goal",
  "lead_info": {...},
  "conversation_details": "summary of key discussion points",
  "sop_gaps": ["question 1"],
  "escalation_reasons": ["reason 1"],
  "recommended_action": "next step"
}

Be concise and factual. Focus on actionable information for the support team.
```

**Key Features:**
- ✓ Comprehensive context coverage
- ✓ Gap analysis for SOP improvements
- ✓ Actionable recommendations
- ✓ Structured output for automation

**Summary Components:**
| Field | Purpose | Example |
|-------|---------|---------|
| intent | Customer goal | "Inquire about Botox pricing" |
| lead_info | Captured data | {business_type, team_size, tools} |
| conversation_details | Key points | "Asked about prices, worried about availability" |
| sop_gaps | Missing info | ["Weekend hours"] |
| escalation_reasons | Triggers | ["complaint_detected"] |
| recommended_action | Next steps | "Send pricing sheet, address hours concern" |

---

## Prompt Template Variables

### FAQ Prompt Variables
- `{sop_data}`: Formatted SOP information
- `{conversation_history}`: Previous messages in session
- `{customer_message}`: Current customer input

### Review Prompt Variables
- `{sop_data}`: Formatted SOP information
- `{customer_message}`: Original customer query
- `{generated_response}`: FAQ agent response
- `{confidence}`: Confidence score (0.0-1.0)

### Qualification Prompt Variables
- `{answered_questions}`: List of completed Q&A pairs
- `{next_question}`: Next question to ask

### Summary Prompt Variables
- `{conversation_history}`: Full conversation text
- `{lead_info}`: Collected lead data (JSON)
- `{escalation_logs}`: Escalation events (JSON)
- `{sop_data}`: Formatted SOP information

---

## Hallucination Prevention Strategies

### 1. SOP Injection
**What:** Include full SOP in every prompt
**Why:** Model has source of truth in context
**How:** Load and format SOP JSON, pass as template variable

### 2. Explicit Constraints
**What:** CRITICAL RULES section in prompts
**Why:** Direct instructions reduce LLM autonomy
**How:** List "NEVER" instructions before guidelines

### 3. Confidence Scoring
**What:** Require 0.0-1.0 confidence in every response
**Why:** Quantifies uncertainty, triggers escalation
**How:** Model provides score; system checks threshold

### 4. Structured Output
**What:** JSON schema enforcement
**Why:** Validates response completeness
**How:** Parser checks required fields, rejects malformed output

### 5. Safety Review Layer
**What:** Additional LLM validation
**Why:** Second pass catches LLM mistakes
**How:** Reviewer agent validates before delivery

### 6. Keyword Escalation
**What:** Rule-based triggers for sensitive topics
**Why:** Doesn't rely on LLM judgment alone
**How:** Check message for complaint/medical/negotiation keywords

### 7. Confidence Thresholds
**What:** Auto-escalate low-confidence responses
**Why:** Uncertain answers dangerous
**How:** If confidence < 0.70, escalate automatically

### 8. Conversation History
**What:** Include full context in prompts
**Why:** Prevents inconsistent responses
**How:** Pass formatted conversation to all agents

---

## Confidence Scoring Rationale

**Score Range Meaning:**

| Range | Interpretation | Action |
|-------|-----------------|--------|
| 0.90-1.0 | Directly answered in SOP | Send response |
| 0.70-0.89 | Inferred from SOP | Send with caution |
| 0.50-0.69 | Partially answered | Review before sending |
| 0.20-0.49 | Uncertain, needs context | Escalate |
| 0.0-0.19 | Not in SOP, invented | Reject, escalate |

**Scoring Rules:**
- +0.15 for direct SOP match
- +0.10 for implied answer from multiple SOP fields
- -0.20 for unsupported claim
- -0.40 for potential hallucination
- -0.30 if medical/complaint keywords detected

---

## Escalation Logic

### Automatic Escalation Triggers

```python
Escalate if:
  (1) confidence < 0.70
  (2) complaint keywords detected
  (3) medical keywords detected
  (4) pricing negotiation detected
  (5) human request detected
  (6) > 2 unanswered questions
  (7) review agent rejects response
```

### Complaint Keywords
`terrible, awful, bad, frustrated, angry, upset, disappointed, 
refund, complain, worst, horrible`

### Medical Keywords
`pain, side effect, medical, doctor, hospital, health, allergy, 
medication, condition, symptom`

### Negotiation Keywords
`discount, cheaper, special price, deal, negotiate, bargain`

### Human Request Keywords
`human, agent, support person, representative, talk to, speak to`

---

## Tone & Persona

**Brand Voice:** Professional, helpful, empathetic
- Never robotic or overly formal
- Acknowledge customer concerns
- Provide clear, concise answers
- Set appropriate expectations

**Example:**
```
✗ "Botox costs £200. Fillers cost £250."
✓ "Our Botox services start from £200, and Fillers from £250. 
   I'd recommend a free consultation to discuss what's right for you."
```

---

## Testing Prompts

### Test Case 1: In-Scope Answer
```
Input: "What are Botox prices?"
Expected: confidence 0.95+, direct SOP quote
Result: PASS if answer accurate, confident, not escalated
```

### Test Case 2: Out-of-Scope Answer
```
Input: "Do you offer laser treatments?"
Expected: confidence <0.50, escalation=true
Result: PASS if escalated (not invented)
```

### Test Case 3: Complaint Handling
```
Input: "I'm frustrated with your prices!"
Expected: escalation=true, no attempt to defend
Result: PASS if escalated to human
```

### Test Case 4: Review Validation
```
Input: FAQ response with confidence=0.65
Expected: Review rejects (below 0.70 threshold)
Result: PASS if escalated
```

---

## Future Prompt Improvements

1. **Few-shot Examples**: Add example Q&As in prompts
2. **Chain-of-Thought**: Request step-by-step reasoning
3. **Temperature Control**: Lower temp for consistency, higher for creativity
4. **Model-Specific**: Optimize for different LLM architectures
5. **A/B Testing**: Compare prompt variations on metrics
6. **Prompt Caching**: Cache SOP in system message for speed
7. **Domain Fine-tuning**: Fine-tune model on support interactions
8. **Multilingual**: Translate prompts for international support

---

## Prompt Versioning

Current Version: 1.0  
Last Updated: May 2026

### Version History
- **1.0**: Initial production release
  - SOP-grounded FAQ answering
  - Multi-point review validation
  - Structured lead qualification
  - Comprehensive summarization

### Breaking Changes
None (initial version)

---

## Performance Metrics

### Target Metrics
- FAQ answer accuracy: >95%
- Hallucination rate: 0%
- Escalation accuracy: >90%
- Summary completeness: 100%
- Average response time: <5 seconds

### Current Performance
(To be measured in production)

---

## Support

For prompt issues:
1. Check `logs/system.log` for LLM errors
2. Review example transcripts in `test_transcripts/`
3. Compare actual output to expected format
4. Check confidence scores align with accuracy
5. Verify SOP data formatting in prompts

---

**End of Document**
