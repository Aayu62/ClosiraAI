# Test Transcript: WhatsApp Booking Query

## Scenario
Customer asks how to book through WhatsApp. Answered directly from SOP + Knowledge Base contact data.

## Conversation

**Customer:** How can I book through WhatsApp?

**Expected FAQ Agent Flow:**
1. Layer 0 (Medical Safety): No medical keywords → pass
2. Layer 1a (Booking): "book" + "whatsapp" matched → return booking response immediately

**Expected FAQ Response:**
```json
{
  "answer": "You can book directly through WhatsApp:\n\nhttps://wa.me/917667214728?text=Hi\n\nPhone: +91 7667214728\n\nOr visit our website. Our team will confirm your appointment shortly.",
  "confidence": 0.92,
  "needs_escalation": false,
  "reason": "booking_info_from_sop_and_kb",
  "source": "sop"
}
```

**Escalation Check:** No escalation — confidence 0.92 ≥ threshold 0.70

**Review Result:** APPROVED — Low risk, grounded in SOP booking information

## Expected Behavior
✓ Booking pattern matched immediately (no LLM call needed)
✓ WhatsApp link and phone number returned from service_knowledge.json
✓ Confidence 0.92 (SOP/direct match range: 0.90–0.95)
✓ No escalation triggered
✓ Review approved

## Outcome
Customer receives direct WhatsApp booking link and phone number.
