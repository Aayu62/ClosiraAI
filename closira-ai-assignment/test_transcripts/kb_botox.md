# Test Transcript: Knowledge Base — What is Botox?

## Scenario
Customer asks an educational question about Botox that is not a pricing question (SOP) but is covered in the Knowledge Base.

## Conversation

**Customer:** What is Botox?

**Expected FAQ Agent Flow:**
1. Layer 0 (Medical Safety): No medical safety keywords → pass
2. Layer 1 (SOP): No direct SOP match for "what is Botox" → continue
3. Layer 2 (Knowledge Base): "botox" matched in KB → return educational response

**Expected FAQ Response:**
```json
{
  "answer": "Botox is a cosmetic treatment using purified botulinum toxin to temporarily reduce wrinkles and relax facial muscles. Common uses: Forehead lines, Crow's feet, Frown lines. Results usually last 3–4 months. Note: Medical suitability questions require consultation with a specialist.",
  "confidence": 0.85,
  "needs_escalation": false,
  "reason": "knowledge_base_match_Botox",
  "source": "knowledge_base"
}
```

**Escalation Check:** No escalation — confidence 0.85 ≥ threshold 0.70

**Review Result:** APPROVED — Low risk, grounded in Knowledge Base

## Expected Behavior
✓ SOP layer checked first, no pricing match
✓ Knowledge Base layer returns educational description
✓ Confidence 0.85 (KB range: 0.80–0.88)
✓ No escalation triggered
✓ Review approved

## Outcome
Customer receives educational information about Botox from the Knowledge Base.
