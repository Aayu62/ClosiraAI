# Test Transcript: In-Scope FAQ Question

## Scenario
Customer asks a pricing question that is fully covered in the SOP.

## Conversation

**Customer:** What are your Botox prices?

**AI Response:**
```json
{
  "answer": "Botox services at Bloom Aesthetics Clinic start from £200. For more details or to book a consultation, you can reach us via WhatsApp or our website.",
  "confidence": 0.95,
  "needs_escalation": false,
  "reason": "Question directly answered in SOP with specific pricing information"
}
```

**Escalation Check:** No escalation needed - high confidence, information from SOP

**Review Result:** APPROVED - Low risk, accurate SOP grounding

## Expected Behavior
✓ Answer sourced from SOP
✓ Confidence score high (>0.90)
✓ No escalation triggered
✓ Review approved

## Outcome
Customer receives immediate, accurate response.
