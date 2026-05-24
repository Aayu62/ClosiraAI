import logging
from typing import Any, Dict, Optional
from utils.config import Config


logger = logging.getLogger(__name__)


class EscalationAgent:
    """Detects escalation conditions through rule-based and LLM analysis."""

    # Rule-based escalation keywords
    COMPLAINT_KEYWORDS = ["terrible", "awful", "bad", "frustrated", "angry", "upset",
                          "disappointed", "unhappy", "refund", "complain", "worst", "horrible"]
    MEDICAL_KEYWORDS = ["pain", "side effect", "medical", "doctor", "hospital", "health",
                        "allergy", "medication", "condition", "symptom", "pregnant",
                        "pregnancy", "breastfeed", "breastfeeding", "contraindic",
                        "treatment risk", "safe for me", "suitable for", "am i eligible"]
    NEGOTIATION_KEYWORDS = ["discount", "cheaper", "special price", "deal", "negotiate", "bargain"]
    HUMAN_KEYWORDS = ["human", "agent", "support person", "representative", "talk to someone",
                      "speak to", "manager"]

    def __init__(self, config: Config):
        self.config = config
        self.confidence_threshold = config.confidence_threshold

    def detect(self, customer_message: str, confidence: Optional[float] = None,
               unanswered_count: int = 0) -> Dict[str, Any]:
        """
        Detect escalation conditions.

        Args:
            customer_message: Customer input
            confidence: FAQ confidence score
            unanswered_count: Number of unanswered questions

        Returns:
            Escalation decision and reason
        """
        reasons = []
        escalate = False

        # Check confidence threshold
        if confidence is not None and confidence < self.confidence_threshold:
            reasons.append(f"low_confidence ({confidence:.2f})")
            escalate = True
            logger.info(f"Escalation: confidence {confidence:.2f} below threshold {self.confidence_threshold}")

        # Check unanswered questions
        if unanswered_count > 2:
            reasons.append(f"multiple_unanswered_questions ({unanswered_count})")
            escalate = True
            logger.info(f"Escalation: {unanswered_count} unanswered questions")

        # Check complaint keywords
        message_lower = customer_message.lower()
        if any(keyword in message_lower for keyword in self.COMPLAINT_KEYWORDS):
            reasons.append("complaint_detected")
            escalate = True
            logger.info("Escalation: complaint keywords detected")

        # Check medical keywords
        if any(keyword in message_lower for keyword in self.MEDICAL_KEYWORDS):
            reasons.append("medical_question_detected")
            escalate = True
            logger.info("Escalation: medical keywords detected")

        # Check negotiation keywords
        if any(keyword in message_lower for keyword in self.NEGOTIATION_KEYWORDS):
            reasons.append("pricing_negotiation_detected")
            escalate = True
            logger.info("Escalation: negotiation keywords detected")

        # Check human request keywords
        if any(keyword in message_lower for keyword in self.HUMAN_KEYWORDS):
            reasons.append("human_request_detected")
            escalate = True
            logger.info("Escalation: human request detected")

        return {
            "escalate": escalate,
            "reason": ", ".join(reasons) if reasons else "no escalation needed",
            "reasons": reasons
        }
