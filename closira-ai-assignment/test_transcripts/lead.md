# Test Transcript: Lead Qualification Flow

## Scenario
Customer inquires about services and is qualified as potential lead.

## Conversation

**Customer:** Hi, I'm interested in your Botox services for my beauty salon.

**AI:** Botox services at Bloom Aesthetics Clinic start from £200. We also offer Fillers from £250 and free consultations.

**AI (Qualification):** To better assist you, could you tell me what type of business you run?

**Customer:** I run a beauty salon in Manchester.

**AI (Qualification):** Thank you! How large is your team?

**Customer:** We have 5 team members.

**AI (Qualification):** Great! What tools or software do you currently use for bookings?

**Customer:** We use a simple spreadsheet right now.

## Qualification Data Collected

```json
{
  "business_type": "Beauty salon",
  "team_size": "5 team members",
  "tools": "Spreadsheet for bookings"
}
```

## Expected Behavior
✓ Initial FAQ answer accurate and SOP-grounded
✓ Qualification questions asked sequentially
✓ No duplicate questions
✓ Responses captured and stored
✓ Lead data structured and complete

## Outcome
Lead successfully qualified with actionable business information for follow-up.
