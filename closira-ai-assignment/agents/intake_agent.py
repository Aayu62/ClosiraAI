"""
Intake Agent — guided intake flow for Closira AI.

Runs before the main conversation loop. Presents an intent menu,
then runs intent-appropriate qualification questions using lettered
multiple-choice options. No LLM calls are made here — all logic is
deterministic so the flow is instant and reliable.
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Intent menu
# ---------------------------------------------------------------------------

INTENT_MENU = {
    "A": "General Information",
    "B": "Existing Booking Support",
    "C": "Raise Complaint",
    "D": "Pricing & Services",
    "E": "Other",
    "S": "Skip",
}

# ---------------------------------------------------------------------------
# Service pricing pulled from SOP (single source of truth)
# ---------------------------------------------------------------------------

SERVICE_PRICING = {
    "Botox":        "from £200",
    "Fillers":      "from £250",
    "Consultation": "Free",
}

# ---------------------------------------------------------------------------
# Qualification question definitions
# Each entry: (display_text, {letter: value})
# ---------------------------------------------------------------------------

Q_CUSTOMER_TYPE = (
    "What best describes you?",
    {"A": "Individual customer", "B": "Small business", "C": "Clinic", "D": "Other"},
)

Q_TEAM_SIZE = (
    "Team size?",
    {"A": "2-10", "B": "11-50", "C": "50+", "D": "Other"},
)

Q_PLATFORM = (
    "Which platform are you contacting us from?",
    {
        "A": "Closira website",
        "B": "WhatsApp",
        "C": "Booking software",
        "D": "Other",
    },
)

Q_SERVICE = (
    "Which service interests you?",
    {"A": "Botox", "B": "Fillers", "C": "Consultation", "D": "Not sure yet"},
)


class IntakeAgent:
    """
    Runs the guided intake flow at session start.

    Presents an intent menu, then asks intent-appropriate questions.
    Returns structured intake data that is immediately persisted to
    the session file.
    """

    def __init__(self) -> None:
        self.intent: str = ""
        self.lead_data: Dict[str, str] = {
            "business_type": "",
            "team_size": "",
            "tools": "",
        }
        self.intake_complete: bool = False
        self.complaint_text: str = ""
        self.booking_ref: str = ""
        self.booking_support_needed: str = ""

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def run(self) -> Dict[str, Any]:
        """
        Execute the full intake flow interactively.

        Returns:
            Dict with keys: intent, lead_data, complaint_text,
            booking_ref, booking_support_needed, skipped.
        """
        self._print_greeting()

        while True:
            intent_key = self._ask_intent()
            self.intent = INTENT_MENU[intent_key]
            logger.info(f"Intent selected: {self.intent}")

            if intent_key == "S":
                print("\nNo problem — how can I help you today?\n")
                self.intake_complete = True
                return self._result(skipped=True)

            if intent_key == "C":
                self._handle_complaint()
                break

            elif intent_key == "B":
                self._handle_booking_support()
                break

            elif intent_key == "D":
                # Pricing flow loops back to intent menu after showing price
                should_continue = self._handle_pricing()
                if should_continue:
                    # Customer wants to ask something else — re-show menu
                    print(
                        "\nTo help me assist you better, please choose the"
                        "\npurpose of your visit:\n"
                    )
                    continue
                break

            elif intent_key == "A":
                self._run_general_qualification()
                break

            else:  # E — Other
                self._run_other_qualification()
                break

        self.intake_complete = True
        return self._result(skipped=False)

    # ------------------------------------------------------------------
    # Intent-specific handlers
    # ------------------------------------------------------------------

    def _run_general_qualification(self) -> None:
        """
        General Information qualification.

        Asks customer type. Only asks team size if the customer is NOT
        an individual (individuals have no team). Always asks platform.
        """
        print(
            "\nGreat — you'd like General Information.\n"
            "Before we continue, I'd like to ask a few quick questions.\n"
        )

        # Q1 — customer type
        customer_type = self._ask_choice(f"1/2 — {Q_CUSTOMER_TYPE[0]}", Q_CUSTOMER_TYPE[1])
        self.lead_data["business_type"] = customer_type

        # Q2 — team size only for non-individual
        if customer_type != "Individual customer":
            team_size = self._ask_choice(f"2/3 — {Q_TEAM_SIZE[0]}", Q_TEAM_SIZE[1])
            self.lead_data["team_size"] = team_size
            platform = self._ask_choice(f"3/3 — {Q_PLATFORM[0]}", Q_PLATFORM[1])
        else:
            platform = self._ask_choice(f"2/2 — {Q_PLATFORM[0]}", Q_PLATFORM[1])

        self.lead_data["tools"] = platform
        print("\nPerfect — thanks. How can I help you today?\n")
        logger.info(f"General qualification complete: {self.lead_data}")

    def _run_other_qualification(self) -> None:
        """Other intent — ask customer type and platform."""
        print(
            "\nGreat — let me ask a couple of quick questions.\n"
        )
        customer_type = self._ask_choice(f"1/2 — {Q_CUSTOMER_TYPE[0]}", Q_CUSTOMER_TYPE[1])
        self.lead_data["business_type"] = customer_type

        if customer_type != "Individual customer":
            team_size = self._ask_choice(f"2/3 — {Q_TEAM_SIZE[0]}", Q_TEAM_SIZE[1])
            self.lead_data["team_size"] = team_size
            platform = self._ask_choice(f"3/3 — {Q_PLATFORM[0]}", Q_PLATFORM[1])
        else:
            platform = self._ask_choice(f"2/2 — {Q_PLATFORM[0]}", Q_PLATFORM[1])

        self.lead_data["tools"] = platform
        print("\nPerfect — thanks. How can I help you today?\n")
        logger.info(f"Other qualification complete: {self.lead_data}")

    def _handle_pricing(self) -> bool:
        """
        Pricing & Services flow.

        Shows service price immediately after selection, then asks if
        the customer wants to explore another option or continue to chat.

        Returns:
            True  → customer wants to go back to the intent menu.
            False → customer is done with pricing, proceed to chat.
        """
        print("\nGreat — let me show you our pricing.\n")

        service = self._ask_choice(f"— {Q_SERVICE[0]}", Q_SERVICE[1])

        if service == "Not sure yet":
            print(
                "\nHere is a summary of our services:\n"
                f"  • Botox        — {SERVICE_PRICING['Botox']}\n"
                f"  • Fillers      — {SERVICE_PRICING['Fillers']}\n"
                f"  • Consultation — {SERVICE_PRICING['Consultation']}\n"
            )
        else:
            price = SERVICE_PRICING.get(service, "Please contact us for pricing")
            print(f"\n{service} at Bloom Aesthetics Clinic starts {price}.\n")

        # Store the service interest in lead_data
        self.lead_data["business_type"] = service

        print(
            "Would you like to:\n"
            "  A) Explore another service\n"
            "  B) Continue to chat / ask a question\n"
        )
        choice = self._get_choice({"A", "B"})
        return choice == "A"  # True = loop back to intent menu

    def _handle_complaint(self) -> None:
        """Collect complaint text and flag for escalation."""
        print(
            "\nI'm sorry to hear you're facing an issue.\n"
            "Please briefly describe your complaint:\n"
        )
        try:
            self.complaint_text = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            self.complaint_text = ""
        print(
            "\nThank you. I've flagged this for our support team "
            "and marked it for priority review.\n"
        )
        logger.info("Complaint intake collected")

    def _handle_booking_support(self) -> None:
        """
        Collect booking reference, ask what support is needed,
        then escalate to human support.
        """
        print(
            "\nPlease share your:\n"
            "  • Booking ID\n"
            "  OR\n"
            "  • Phone number used during booking\n"
        )
        try:
            self.booking_ref = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            self.booking_ref = ""

        print("\nThank you. What support do you need regarding this booking?\n")
        try:
            self.booking_support_needed = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            self.booking_support_needed = ""

        print(
            "\nUnderstood. I've escalated your booking query to our support team. "
            "A team member will follow up with you shortly.\n"
        )
        logger.info(
            f"Booking support collected — ref: {self.booking_ref}, "
            f"need: {self.booking_support_needed}"
        )

    # ------------------------------------------------------------------
    # UI helpers
    # ------------------------------------------------------------------

    def _print_greeting(self) -> None:
        print("\n" + "=" * 52)
        print("Welcome to Bloom Aesthetics Clinic")
        print("=" * 52)
        print(
            "\nHello and welcome to Bloom Aesthetics Clinic 👋\n\n"
            "To help me assist you better, please choose the\n"
            "purpose of your visit:\n"
        )

    def _ask_intent(self) -> str:
        """Display intent menu and return validated letter choice."""
        for key, label in INTENT_MENU.items():
            print(f"  {key}) {label}")
        print()
        return self._get_choice(set(INTENT_MENU.keys()), "Please type A, B, C, D, E or S: ")

    def _ask_choice(self, prompt: str, options: Dict[str, str]) -> str:
        """Display a multiple-choice question and return the chosen value."""
        print(f"\n{prompt}\n")
        for key, label in options.items():
            print(f"  {key}) {label}")
        print()
        letter = self._get_choice(set(options.keys()))
        return options[letter]

    @staticmethod
    def _get_choice(valid: set, prompt: str = "Your choice: ") -> str:
        """Loop until the user enters a valid single-letter choice."""
        while True:
            try:
                raw = input(prompt).strip().upper()
            except (KeyboardInterrupt, EOFError):
                return next(iter(sorted(valid)))
            if raw in valid:
                return raw
            print(f"  Please enter one of: {', '.join(sorted(valid))}")

    # ------------------------------------------------------------------
    # Result builder
    # ------------------------------------------------------------------

    def _result(self, skipped: bool) -> Dict[str, Any]:
        return {
            "intent": self.intent,
            "lead_data": self.lead_data,
            "complaint_text": self.complaint_text,
            "booking_ref": self.booking_ref,
            "booking_support_needed": self.booking_support_needed,
            "skipped": skipped,
        }
