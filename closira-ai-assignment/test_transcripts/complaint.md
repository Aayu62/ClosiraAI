# Test Transcript: Complaint Escalation

## Scenario
Customer expresses dissatisfaction/complaint.

## Conversation

**Customer:** I'm really frustrated with the pricing! These prices are terrible and I'm not happy.

**AI Response:**
```json
{
  "answer": "I understand this isn't what you wanted to hear.",
  "confidence": 0.50,
  "needs_escalation": true,
  "reason": "Complaint sentiment detected - keywords: frustrated, terrible, not happy"
}
```

**Escalation Check:** ESCALATED - Multiple triggers:
- Complaint keywords detected: "frustrated", "terrible", "not happy"
- Low confidence (0.50 < 0.70)

**Escalation Reason:** complaint_detected

**Review Result:** BLOCKED - Risk level HIGH, complaint requires human handling

## Expected Behavior
✓ Complaint keywords detected by rule engine
✓ Escalation triggered immediately
✓ Review agent rejects response
✓ System escalates to human

## Outcome
Customer complaint immediately escalated to support team for empathetic handling.
