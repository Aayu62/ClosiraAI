# Test Transcript: Location Query

## Scenario
Customer asks where the clinic is located. Answered directly from Knowledge Base clinic_information without LLM call.

## Conversation

**Customer:** Where are you located?

**Expected FAQ Agent Flow:**
1. Layer 0 (Medical Safety): No medical keywords → pass
2. Layer 1a (Booking): No booking keywords → pass
3. Layer 1b (Location): "where" + "located" matched → return location response immediately

**Expected FAQ Response:**
```json
{
  "answer": "Bloom Aesthetics Clinic\n\nBloom Aesthetics Clinic, KIIT Road, Patia, Bhubaneswar, Odisha, India\n\nGoogle Maps: https://maps.app.goo.gl/f4D9nZFZfXGmBhLd8?g_st=aw",
  "confidence": 0.93,
  "needs_escalation": false,
  "reason": "location_info_from_kb",
  "source": "sop"
}
```

**Escalation Check:** No escalation — confidence 0.93 ≥ threshold 0.70

**Review Result:** APPROVED — Low risk, grounded in clinic information

## Expected Behavior
✓ Location pattern matched immediately (no LLM call needed)
✓ Address and Google Maps link returned from service_knowledge.json
✓ Confidence 0.93 (SOP/direct match range: 0.90–0.95)
✓ No escalation triggered
✓ Review approved

## Outcome
Customer receives full clinic address and Google Maps link.
