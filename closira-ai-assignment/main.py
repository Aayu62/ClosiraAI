#!/usr/bin/env python3
"""
Closira AI Customer Support Workflow System

Multi-agent system for intelligent customer support including:
- Guided intake flow (intent selection + early lead qualification)
- FAQ answering from SOP + Knowledge Base
- Escalation detection
- Safety review
- Conversation summarization
- Persistent session recording
"""

import sys
from dotenv import load_dotenv

from utils.config import Config
from utils.logger import setup_logger
from utils.llm import LLMClient
from utils.memory import Memory
from utils.session_manager import SessionManager
from agents.intake_agent import IntakeAgent
from agents.faq_agent import FAQAgent
from agents.qualification_agent import QualificationAgent
from agents.escalation_agent import EscalationAgent
from agents.review_agent import ReviewAgent
from agents.summary_agent import SummaryAgent


class ConversationManager:
    """Orchestrates the guided intake + multi-agent conversation workflow."""

    def __init__(self) -> None:
        load_dotenv()

        self.config = Config()
        self.config.validate()

        self.logger = setup_logger(
            "closira",
            self.config.logs_dir,
            self.config.log_level,
        )

        self.logger.info("=" * 60)
        self.logger.info("Starting Closira AI Customer Support Workflow")
        self.logger.info("=" * 60)

        self.llm_client = LLMClient(
            api_key=self.config.openrouter_api_key,
            base_url=self.config.base_url,
            model=self.config.model,
        )

        self.intake_agent = IntakeAgent()
        self.faq_agent = FAQAgent(self.llm_client, self.config)
        self.qualification_agent = QualificationAgent(self.llm_client, self.config)
        self.escalation_agent = EscalationAgent(self.config)
        self.review_agent = ReviewAgent(self.llm_client, self.config)
        self.summary_agent = SummaryAgent(self.llm_client, self.config)

        self.memory = Memory()
        self.session = SessionManager(self.config.sessions_dir)

        # Populated by intake flow
        self._intent: str = ""
        self._intake_skipped: bool = False

        self.logger.info("All agents initialized successfully")

    # ------------------------------------------------------------------
    # Intake flow
    # ------------------------------------------------------------------

    def run_intake(self) -> bool:
        """
        Run the guided intake flow before the main conversation loop.

        Collects intent and lead qualification data, persists them to
        the session, and pre-populates the QualificationAgent so the
        summary agent has complete lead data.

        Returns:
            True if the conversation should continue.
            False if the user should be exited immediately (e.g. complaint
            that needs no further chat).
        """
        intake_result = self.intake_agent.run()

        self._intent = intake_result["intent"]
        self._intake_skipped = intake_result["skipped"]
        lead_data = intake_result["lead_data"]
        complaint_text = intake_result.get("complaint_text", "")
        booking_ref = intake_result.get("booking_ref", "")
        booking_support_needed = intake_result.get("booking_support_needed", "")

        # Persist intent to session
        self.session._data["customer_profile"]["intent_category"] = self._intent
        self.session._flush()

        # Pre-populate qualification agent with intake answers
        self.qualification_agent.set_answers(
            business_type=lead_data.get("business_type", ""),
            team_size=lead_data.get("team_size", ""),
            tools=lead_data.get("tools", ""),
        )
        self.memory.store_lead_info(lead_data)
        self.session.save_lead(lead_data)

        # Handle complaint intake — escalate immediately
        if self._intent == "Raise Complaint" and complaint_text:
            self.memory.add_message("customer", complaint_text)
            self.session.save_message(role="user", content=complaint_text)

            escalation_msg = (
                "I've flagged this for our support team and marked it "
                "for priority review. A team member will follow up with "
                "you shortly."
            )
            self.memory.add_message("assistant", escalation_msg)
            self.session.save_message(role="assistant", content=escalation_msg)
            self.memory.add_escalation(
                reason="complaint_intake", message=complaint_text
            )
            self.session.save_escalation(
                reason="complaint_intake", message=complaint_text
            )
            self.logger.info("Complaint escalated from intake")

        # Handle booking support intake — persist ref and escalate
        if self._intent == "Existing Booking Support" and booking_ref:
            self.session.save_booking_ref(booking_ref, booking_support_needed)

            support_msg = booking_support_needed or booking_ref
            self.memory.add_message("customer", f"Booking ref: {booking_ref}. Need: {support_msg}")
            self.session.save_message(
                role="user",
                content=f"Booking ref: {booking_ref}. Support needed: {support_msg}"
            )

            escalation_msg = (
                "I've escalated your booking query to our support team. "
                "A team member will follow up with you shortly."
            )
            self.memory.add_message("assistant", escalation_msg)
            self.session.save_message(role="assistant", content=escalation_msg)
            self.memory.add_escalation(
                reason="booking_support_escalation", message=support_msg
            )
            self.session.save_escalation(
                reason="booking_support_escalation", message=support_msg
            )
            self.logger.info(f"Booking support escalated — ref: {booking_ref}")

        self.logger.info(
            f"Intake complete — intent={self._intent}, "
            f"skipped={self._intake_skipped}, lead={lead_data}"
        )
        return True

    # ------------------------------------------------------------------
    # Core message processing
    # ------------------------------------------------------------------

    def process_message(self, customer_message: str) -> str:
        """
        Process a customer message through the full agent workflow.

        Args:
            customer_message: Raw user input string.

        Returns:
            Response text to display to the customer.
        """
        self.logger.info(f"Processing: {customer_message[:50]}...")

        self.session.save_message(role="user", content=customer_message)
        self.memory.add_message("customer", customer_message)

        # Step 1: FAQ Agent
        self.logger.info("Step 1: FAQ Agent processing")
        conversation_text = self.memory.get_conversation_text()
        faq_response = self.faq_agent.respond(customer_message, conversation_text)
        confidence = faq_response.get("confidence", 0.0)

        if faq_response.get("needs_escalation", False):
            self.logger.info(
                f"FAQ agent escalation triggered: {faq_response.get('reason')}"
            )
            self.memory.add_escalation(
                reason="faq_escalation",
                message=customer_message,
                confidence=confidence,
            )

        # Step 2: Escalation Agent
        self.logger.info("Step 2: Escalation Agent processing")
        escalation_result = self.escalation_agent.detect(
            customer_message=customer_message,
            confidence=confidence,
            unanswered_count=0,
        )

        if escalation_result.get("escalate"):
            reason = escalation_result.get("reason", "unknown")
            self.logger.info(f"Escalation detected: {reason}")
            self.memory.add_escalation(
                reason=reason, message=customer_message, confidence=confidence
            )
            self.session.save_escalation(reason=reason, message=customer_message)

            response_text = (
                f"[ESCALATED] {reason}. "
                "Your concern has been escalated to our support team. "
                "We'll follow up shortly."
            )
            self.session.save_message(
                role="assistant", content=response_text, confidence=confidence
            )
            self.memory.add_message("assistant", response_text)
            return response_text

        # Step 3: Safety Reviewer Agent
        self.logger.info("Step 3: Safety Reviewer Agent processing")
        review_result = self.review_agent.validate(
            customer_message=customer_message,
            generated_response=faq_response.get("answer", ""),
            confidence=confidence,
            source=faq_response.get("source", "llm_sop"),
        )

        if not review_result.get("approved", False):
            self.logger.warning(f"Review failed: {review_result.get('reason')}")
            self.memory.add_escalation(
                reason="review_failed",
                message=customer_message,
                confidence=confidence,
            )
            self.session.save_escalation(
                reason="review_failed", message=customer_message
            )
            response_text = (
                "[ESCALATED] Safety check failed. "
                "Your inquiry has been escalated to our support team."
            )
            self.session.save_message(
                role="assistant", content=response_text, confidence=confidence
            )
            self.memory.add_message("assistant", response_text)
            return response_text

        # Step 4: Approved
        response_text = faq_response.get("answer", "I could not generate a response.")
        self.session.save_message(
            role="assistant", content=response_text, confidence=confidence
        )
        self.memory.add_message("assistant", response_text)
        self.logger.info(f"Response approved and sent (confidence: {confidence})")
        return response_text

    # ------------------------------------------------------------------
    # Session info display (no LLM)
    # ------------------------------------------------------------------

    def _show_session_info(self) -> None:
        """Display current session statistics without invoking any LLM."""
        stats = self.session.get_session_stats()
        lead = stats.get("lead_information", {})

        print("\n" + "=" * 45)
        print("Current Session Info")
        print("=" * 45)
        print(f"Session ID:   {stats['session_id']}")
        print(f"Intent:       {self._intent or 'Not set'}")
        print(f"Messages:     {stats['message_count']}")
        print(f"Escalations:  {stats['escalation_count']}")
        print(f"Duration:     {stats['session_duration']}")
        print("\nLead Data:")
        print(f"  Business Type: {lead.get('business_type') or 'Not collected'}")
        print(f"  Team Size:     {lead.get('team_size') or 'Not collected'}")
        print(f"  Tools:         {lead.get('tools') or 'Not collected'}")
        print("=" * 45 + "\n")

    # ------------------------------------------------------------------
    # Restart intake
    # ------------------------------------------------------------------

    def _restart_intake(self) -> None:
        """
        Re-run the intake flow from the beginning without ending the session.

        A fresh IntakeAgent is created so all previous intake state is
        cleared. Lead data, intent, and any new escalations are persisted
        to the existing session file.
        """
        print("\n" + "-" * 52)
        print("Restarting intake — taking you back to the beginning.")
        print("-" * 52 + "\n")
        self.logger.info("Intake restarted by user")

        self.intake_agent = IntakeAgent()
        intake_result = self.intake_agent.run()

        self._intent = intake_result["intent"]
        self._intake_skipped = intake_result["skipped"]
        lead_data = intake_result["lead_data"]
        complaint_text = intake_result.get("complaint_text", "")
        booking_ref = intake_result.get("booking_ref", "")
        booking_support_needed = intake_result.get("booking_support_needed", "")

        # Update session intent
        self.session._data["customer_profile"]["intent_category"] = self._intent
        self.session._flush()

        # Update qualification agent and memory with new answers
        self.qualification_agent.set_answers(
            business_type=lead_data.get("business_type", ""),
            team_size=lead_data.get("team_size", ""),
            tools=lead_data.get("tools", ""),
        )
        self.memory.store_lead_info(lead_data)
        self.session.save_lead(lead_data)

        if self._intent == "Raise Complaint" and complaint_text:
            self.memory.add_message("customer", complaint_text)
            self.session.save_message(role="user", content=complaint_text)
            escalation_msg = (
                "I've flagged this for our support team and marked it "
                "for priority review. A team member will follow up with you shortly."
            )
            self.memory.add_message("assistant", escalation_msg)
            self.session.save_message(role="assistant", content=escalation_msg)
            self.memory.add_escalation(reason="complaint_intake", message=complaint_text)
            self.session.save_escalation(reason="complaint_intake", message=complaint_text)

        if self._intent == "Existing Booking Support" and booking_ref:
            self.session.save_booking_ref(booking_ref, booking_support_needed)
            support_msg = booking_support_needed or booking_ref
            self.memory.add_message("customer", f"Booking ref: {booking_ref}. Need: {support_msg}")
            self.session.save_message(
                role="user",
                content=f"Booking ref: {booking_ref}. Support needed: {support_msg}"
            )
            escalation_msg = (
                "I've escalated your booking query to our support team. "
                "A team member will follow up with you shortly."
            )
            self.memory.add_message("assistant", escalation_msg)
            self.session.save_message(role="assistant", content=escalation_msg)
            self.memory.add_escalation(reason="booking_support_escalation", message=support_msg)
            self.session.save_escalation(reason="booking_support_escalation", message=support_msg)

        self.logger.info(f"Intake restarted — new intent={self._intent}, lead={lead_data}")

    # ------------------------------------------------------------------
    # Main conversation loop
    # ------------------------------------------------------------------

    def start_conversation(self) -> None:
        """
        Run the main free-form conversation loop.

        Called after intake is complete. Supports 'show session', 'start',
        and 'quit' / 'exit' / 'bye' as built-in commands.
        """
        print("Type 'quit' to end  |  Type 'start' to restart intake\n")
        print("-" * 52 + "\n")

        try:
            while True:
                try:
                    customer_input = input("You: ").strip()

                    if not customer_input:
                        continue

                    if customer_input.lower() == "show session":
                        self._show_session_info()
                        continue

                    if customer_input.lower() == "start":
                        self._restart_intake()
                        continue

                    if customer_input.lower() in ("quit", "exit", "bye"):
                        print("\nPreparing conversation summary...")
                        break

                    response = self.process_message(customer_input)
                    print(f"\nAI: {response}\n")

                except KeyboardInterrupt:
                    print("\n[Session interrupted]")
                    break

        except Exception as e:
            self.logger.error(f"Conversation error: {str(e)}")
            print(f"Error: {str(e)}")

    # ------------------------------------------------------------------
    # Summary + exit
    # ------------------------------------------------------------------

    def end_session(self) -> None:
        """Generate summary, display it, persist it, and close the session."""
        print("\n" + "=" * 52)
        print("Generating Session Summary...")
        print("=" * 52 + "\n")

        conversation_text = self.memory.get_conversation_text()
        lead_info = self.memory.get_lead_info()
        escalations = self.memory.get_escalations()

        summary = self.summary_agent.generate(
            conversation_history=conversation_text,
            lead_info=lead_info,
            escalation_logs=escalations,
        )
        self.session.save_summary(summary)
        self.logger.info("Summary generated")

        # ---- Display ----
        print("=" * 52)
        print("SESSION SUMMARY")
        print("=" * 52)

        intent = summary.get("intent") or self._intent or "N/A"
        print(f"Intent:             {intent}")
        print(f"Resolved:           {summary.get('resolved', 'N/A')}")
        print(f"Resolution Type:    {summary.get('resolution_type', 'N/A')}")
        print(f"Customer Sentiment: {summary.get('customer_sentiment', 'N/A')}")
        print(f"Booking Interest:   {summary.get('booking_interest', False)}")

        print("\nLead Information:")
        lead = summary.get("lead_info") or lead_info
        print(f"  Customer Type: {lead.get('business_type') or 'N/A'}")
        print(f"  Team Size:     {lead.get('team_size') or 'N/A'}")
        print(f"  Tools:         {lead.get('tools') or 'N/A'}")

        services = summary.get("services_discussed", [])
        if services:
            print(f"\nServices Discussed: {', '.join(services)}")

        sop_gaps = summary.get("sop_gaps", [])
        print(f"\nSOP Gaps:    {', '.join(sop_gaps) if sop_gaps else 'None'}")

        esc_reasons = summary.get("escalation_reasons", [])
        print(f"Escalations: {', '.join(esc_reasons) if esc_reasons else 'None'}")

        print(f"\nConversation: {summary.get('conversation_details', 'N/A')}")
        print(f"\nRecommended Action: {summary.get('recommended_action', 'N/A')}")
        print("=" * 52)

        session_path = self.session.close_session()
        print(f"\nSession saved successfully: {session_path}")
        print("Thank you for contacting Bloom Aesthetics Clinic.")

        self.logger.info("Session ended")
        self.logger.info(f"Session file: {session_path}")


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------

def _run_cli() -> None:
    """Original plain-terminal entry point (--no-ui fallback)."""
    try:
        manager = ConversationManager()
        manager.run_intake()
        manager.start_conversation()
        manager.end_session()
    except KeyboardInterrupt:
        print("\n\n[Application terminated by user]")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        sys.exit(1)


def main() -> None:
    """Main entry point — launches TUI by default, CLI with --no-ui."""
    if "--no-ui" in sys.argv:
        _run_cli()
    else:
        from ui.app import ClosiraApp
        ClosiraApp().run()


if __name__ == "__main__":
    main()
