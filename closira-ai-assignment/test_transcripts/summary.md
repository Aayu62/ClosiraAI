# Test Transcript: Conversation Summary

## Session Overview

**Duration:** ~3 minutes
**Escalations:** 1 (complaint)
**Lead Qualified:** Yes

## Full Conversation

```
Customer: What are Botox prices?
AI: Botox services start from £200...

Customer: Can you do fillers too?
AI: Yes, our Fillers are from £250...

Customer: I'm really disappointed with your availability. I need service this weekend but you're closed!
AI: [ESCALATED] complaint detected. Your concern has been escalated...

(Qualification questions asked and answered)
```

## Generated Summary

```json
{
  "intent": "Customer interested in aesthetic services (Botox/Fillers) with availability concerns",
  "lead_info": {
    "business_type": null,
    "team_size": null,
    "tools": null
  },
  "conversation_details": "Customer asked about Botox pricing (£200), Fillers (£250), then expressed dissatisfaction with weekend availability. Complaint escalated.",
  "sop_gaps": ["Weekend availability information not in SOP"],
  "escalation_reasons": ["complaint_detected"],
  "recommended_action": "Human follow-up required - address availability concerns and retain customer"
}
```

## Expected Behavior
✓ Intent accurately captured
✓ SOP gaps identified (weekend hours)
✓ Escalation reasons documented
✓ Actionable recommendation provided
✓ All required fields present

## Outcome
Support team has complete context for follow-up and can address customer concerns appropriately.
