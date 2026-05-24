import json
import logging
from typing import Any, Dict, List
from utils.llm import LLMClient
from utils.parser import Parser
from utils.config import Config


logger = logging.getLogger(__name__)


class SummaryAgent:
    """Generates conversation summaries."""

    def __init__(self, llm_client: LLMClient, config: Config):
        self.llm = llm_client
        self.config = config
        self.parser = Parser()
        self.sop_data: Dict[str, Any] = {}
        self._load_sop()

    def _load_sop(self) -> None:
        """Load SOP data from JSON file."""
        try:
            sop_path = self.config.get_sop_path()
            with open(sop_path, "r") as f:
                self.sop_data = json.load(f)
            logger.info("SOP data loaded for summary agent")
        except FileNotFoundError:
            logger.error(f"SOP file not found at {self.config.get_sop_path()}")
            raise
        except json.JSONDecodeError:
            logger.error("Failed to parse SOP JSON")
            raise

    def _load_prompt_template(self) -> str:
        """Load summary prompt template."""
        try:
            prompt_path = self.config.get_prompt_path("summary_prompt")
            with open(prompt_path, "r") as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"Summary prompt not found at {prompt_path}")
            raise

    def generate(self, conversation_history: str, lead_info: Dict[str, Any],
                 escalation_logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate conversation summary.

        Args:
            conversation_history: Full conversation text
            lead_info: Collected lead information
            escalation_logs: List of escalation events

        Returns:
            Structured summary
        """
        try:
            prompt_template = self._load_prompt_template()
            sop_text = self._format_sop(self.sop_data)
            escalation_text = self._format_escalations(escalation_logs)
            lead_text = json.dumps(lead_info, indent=2)

            system_prompt = prompt_template.format(
                conversation_history=conversation_history,
                lead_info=lead_text,
                escalation_logs=escalation_text,
                sop_data=sop_text
            )

            response_text = self.llm.call(
                system_prompt=system_prompt,
                user_message="Generate a summary of this conversation",
                temperature=0.3
            )

            if not response_text:
                logger.error("LLM call failed in summary agent")
                return self._default_summary(conversation_history, lead_info, escalation_logs)

            parsed = self.parser.parse_json(response_text)
            if not parsed:
                logger.warning(f"Failed to parse summary response: {response_text[:100]}")
                return self._default_summary(conversation_history, lead_info, escalation_logs)

            if not self.parser.validate_summary_response(parsed):
                logger.warning(f"Invalid summary response structure: {parsed}")
                return self._default_summary(conversation_history, lead_info, escalation_logs)

            logger.info("Summary generated successfully")
            return parsed

        except Exception as e:
            logger.error(f"Error in summary agent: {str(e)}")
            return self._default_summary(conversation_history, lead_info, escalation_logs)

    @staticmethod
    def _format_sop(sop_data: Dict[str, Any]) -> str:
        """Format SOP data as readable text."""
        lines = []
        lines.append(f"Business: {sop_data.get('business', 'N/A')}")
        lines.append(f"Hours: {sop_data.get('hours', 'N/A')}")
        lines.append("\nServices:")
        for service, price in sop_data.get('services', {}).items():
            lines.append(f"  - {service}: {price}")
        lines.append(f"\nBooking: {sop_data.get('booking', 'N/A')}")
        lines.append(f"Cancellation: {sop_data.get('cancellation', 'N/A')}")
        return "\n".join(lines)

    @staticmethod
    def _format_escalations(escalation_logs: List[Dict[str, Any]]) -> str:
        """Format escalation logs as readable text."""
        if not escalation_logs:
            return "No escalations"
        lines = []
        for esc in escalation_logs:
            lines.append(f"- {esc.get('reason', 'Unknown')}: {esc.get('message', 'N/A')}")
        return "\n".join(lines)

    @staticmethod
    def _default_summary(conversation_history: str, lead_info: Dict[str, Any],
                        escalation_logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate default summary if LLM fails."""
        details = (
            conversation_history[:500] + "..."
            if len(conversation_history) > 500
            else conversation_history
        )
        return {
            "intent": "Customer inquiry",
            "resolved": not bool(escalation_logs),
            "resolution_type": "Escalated" if escalation_logs else "Self-service",
            "recommended_action": "Human review needed" if escalation_logs else "Standard follow-up",
            "services_discussed": [],
            "pricing_discussed": [],
            "kb_topics_used": [],
            "sop_items_used": [],
            "sop_gaps": [],
            "escalation_reasons": [esc.get("reason", "Unknown") for esc in escalation_logs],
            "conversation_details": details,
            "customer_sentiment": "Neutral",
            "booking_interest": False,
            "lead_info": lead_info,
        }
