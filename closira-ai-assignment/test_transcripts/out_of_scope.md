# Test Transcript: Out-of-Scope Question

## Scenario
Customer asks about services not covered in the SOP.

## Conversation

**Customer:** Do you offer laser treatments?

**AI Response:**
```json
{
  "answer": "This information is not available in our system. Our main services include Botox and Fillers. For questions about additional treatments, please contact us directly via WhatsApp or our website.",
  "confidence": 0.45,
  "needs_escalation": true,
  "reason": "Question not covered in SOP - confidence below threshold, requires escalation"
}
```

**Escalation Check:** ESCALATED - Low confidence (0.45 < 0.70)

**Review Result:** BLOCKED - Risk level HIGH, requires human review

**Escalation Reason:** Low confidence on out-of-scope topic

## Expected Behavior
✓ System recognizes information gap
✓ Confidence score low (<0.70)
✓ Escalation automatically triggered
✓ Review rejects response
✓ Customer notified of escalation

## Outcome
Query escalated to human support for accurate handling.
