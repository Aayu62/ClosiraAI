import json
import logging
import re
from typing import Any, Dict, Optional
from utils.llm import LLMClient
from utils.parser import Parser
from utils.config import Config


logger = logging.getLogger(__name__)

# Keywords that must immediately escalate — no KB answer allowed
MEDICAL_SAFETY_PATTERNS = [
    r"\bside effect", r"\bpregnant\b", r"\bpregnancy\b", r"\bbreastfeed",
    r"\bmedical suitab", r"\btreatment risk", r"\ballerg", r"\bcontraindic",
    r"\bsafe for me\b", r"\bcan i (use|get|have|take)\b", r"\bshould i\b",
    r"\bam i (suitable|eligible|a candidate)\b"
]

# Keywords that indicate a booking/contact intent
BOOKING_PATTERNS = [
    r"\bbook\b", r"\bbooking\b", r"\bwhatsapp\b", r"\bcontact\b",
    r"\bphone\b", r"\bnumber\b", r"\bappointment\b", r"\bschedule\b",
    r"\bwhats.?app\b", r"\bhow (can|do) i (book|contact|reach)\b"
]

# Keywords that indicate a location intent
LOCATION_PATTERNS = [
    r"\bwhere\b.*\b(you|clinic|located|location|address|find)\b",
    r"\blocation\b", r"\baddress\b", r"\bdirections?\b",
    r"\bwhere are you\b", r"\bhow (to|do i) (get|find|reach|visit)\b",
    r"\bgoogle maps?\b", r"\bmap\b"
]

# Keywords that indicate the user wants pricing — KB educational answer should be skipped
PRICING_PATTERNS = [
    r"\bpric(e|es|ing)\b", r"\bcost\b", r"\bhow much\b",
    r"\bfee\b", r"\bcharge\b", r"\brate\b", r"\bexpensive\b",
    r"\baffordable\b", r"\bpay\b", r"\bpayment\b"
]


def _matches_any(text: str, patterns: list) -> bool:
    t = text.lower()
    return any(re.search(p, t) for p in patterns)


class FAQAgent:
    """Handles FAQ answering from SOP (Layer 1) and Knowledge Base (Layer 2)."""

    def __init__(self, llm_client: LLMClient, config: Config):
        self.llm = llm_client
        self.config = config
        self.parser = Parser()
        self.sop_data: Dict[str, Any] = {}
        self.kb_data: Dict[str, Any] = {}
        self._load_sop()
        self._load_knowledge_base()

    def _load_sop(self) -> None:
        sop_path = self.config.get_sop_path()
        with open(sop_path, "r") as f:
            self.sop_data = json.load(f)
        logger.info("SOP data loaded successfully")

    def _load_knowledge_base(self) -> None:
        kb_path = self.config.get_knowledge_base_path()
        try:
            with open(kb_path, "r") as f:
                self.kb_data = json.load(f)
            logger.info("Knowledge base loaded successfully")
        except FileNotFoundError:
            logger.warning(f"Knowledge base not found at {kb_path}, KB layer disabled")
            self.kb_data = {}

    def _load_prompt_template(self) -> str:
        prompt_path = self.config.get_prompt_path("faq_prompt")
        with open(prompt_path, "r") as f:
            return f.read()

    # ------------------------------------------------------------------
    # Layer 0: Medical safety — immediate escalation, no LLM needed
    # ------------------------------------------------------------------
    def _check_medical_safety(self, message: str) -> Optional[Dict[str, Any]]:
        if _matches_any(message, MEDICAL_SAFETY_PATTERNS):
            logger.info("Medical safety escalation triggered")
            return {
                "answer": "Medical questions require specialist guidance and have been escalated.",
                "confidence": 0.0,
                "needs_escalation": True,
                "reason": "medical_safety",
                "source": "safety_rule"
            }
        return None

    # ------------------------------------------------------------------
    # Layer 1: SOP direct-match helpers
    # ------------------------------------------------------------------
    def _check_sop_booking(self, message: str) -> Optional[Dict[str, Any]]:
        if not _matches_any(message, BOOKING_PATTERNS):
            return None
        info = self.kb_data.get("clinic_information", {})
        wb = info.get("whatsapp_booking", {})
        link = wb.get("booking_link", self.sop_data.get("booking", ""))
        phone = wb.get("phone", self.sop_data.get("phone", ""))
        answer = (
            f"You can book directly through WhatsApp:\n\n"
            f"{link}\n\n"
            f"Phone: {phone}\n\n"
            f"Or visit our website. Our team will confirm your appointment shortly."
        )
        return {"answer": answer, "confidence": 0.92, "needs_escalation": False,
                "reason": "booking_info_from_sop_and_kb", "source": "sop"}

    def _check_sop_location(self, message: str) -> Optional[Dict[str, Any]]:
        if not _matches_any(message, LOCATION_PATTERNS):
            return None
        info = self.kb_data.get("clinic_information", {})
        address = info.get("address", self.sop_data.get("location", ""))
        maps = info.get("google_maps", "")
        answer = (
            f"Bloom Aesthetics Clinic\n\n"
            f"{address}\n\n"
            f"Google Maps: {maps}"
        )
        return {"answer": answer, "confidence": 0.93, "needs_escalation": False,
                "reason": "location_info_from_kb", "source": "sop"}

    # ------------------------------------------------------------------
    # Layer 2: Knowledge Base lookup
    # ------------------------------------------------------------------
    def _search_knowledge_base(self, message: str) -> Optional[Dict[str, Any]]:
        """Returns KB educational answer only when the user is NOT asking about pricing."""
        if not self.kb_data:
            return None

        # If the user is asking about price/cost, defer to SOP via LLM
        if _matches_any(message, PRICING_PATTERNS):
            logger.debug("KB skipped — pricing intent detected, deferring to SOP")
            return None

        msg_lower = message.lower()

        # Match treatment entries (Botox, Fillers, Consultation)
        treatment_keys = ["Botox", "Fillers", "Consultation"]
        for key in treatment_keys:
            if key.lower() in msg_lower:
                entry = self.kb_data.get(key)
                if not entry:
                    continue
                parts = [entry.get("description", "")]
                uses = entry.get("common_uses")
                if uses:
                    parts.append("Common uses: " + ", ".join(uses) + ".")
                duration = entry.get("duration")
                if duration:
                    parts.append(duration)
                cost = entry.get("cost")
                if cost:
                    parts.append(f"Cost: {cost}.")
                includes = entry.get("includes")
                if includes:
                    parts.append("Includes: " + ", ".join(includes) + ".")
                disclaimer = entry.get("disclaimer")
                if disclaimer:
                    parts.append(f"Note: {disclaimer}")
                answer = " ".join(p for p in parts if p)
                return {
                    "answer": answer,
                    "confidence": 0.85,
                    "needs_escalation": False,
                    "reason": f"knowledge_base_match_{key}",
                    "source": "knowledge_base"
                }

        return None

    # ------------------------------------------------------------------
    # LLM call with SOP + KB context
    # ------------------------------------------------------------------
    def _llm_respond(self, message: str, conversation_history: str) -> Dict[str, Any]:
        prompt_template = self._load_prompt_template()
        sop_text = self._format_sop(self.sop_data)
        kb_text = self._format_kb(self.kb_data)

        system_prompt = prompt_template.format(
            sop_data=sop_text,
            kb_data=kb_text,
            conversation_history=conversation_history,
            customer_message=message
        )

        response_text = self.llm.call(
            system_prompt=system_prompt,
            user_message=message,
            temperature=0.2
        )

        if not response_text:
            logger.error("LLM call failed in FAQ agent")
            return self._error_response("LLM unavailable")

        parsed = self.parser.parse_json(response_text)
        if not parsed or not self.parser.validate_faq_response(parsed):
            logger.error(f"Failed to parse FAQ LLM response: {response_text[:200]}")
            return self._error_response("Failed to parse LLM response")

        # Clamp confidence — never allow 1.0
        raw_conf = float(parsed.get("confidence", 0.5))
        parsed["confidence"] = min(raw_conf, 0.95)
        parsed["source"] = "llm_sop"
        return parsed

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------
    def respond(self, customer_message: str, conversation_history: str = "") -> Dict[str, Any]:
        try:
            # Layer 0: medical safety gate
            safety = self._check_medical_safety(customer_message)
            if safety:
                return safety

            # Layer 1a: booking intent (SOP + KB contact data)
            booking = self._check_sop_booking(customer_message)
            if booking:
                return booking

            # Layer 1b: location intent (KB address data)
            location = self._check_sop_location(customer_message)
            if location:
                return location

            # Layer 2: Knowledge Base lookup (before LLM — avoids unnecessary API call)
            kb_result = self._search_knowledge_base(customer_message)
            if kb_result:
                logger.info(f"Knowledge base layer answered: {kb_result.get('reason')}")
                return kb_result

            # Layer 1c: LLM with SOP context
            llm_result = self._llm_respond(customer_message, conversation_history)

            # If LLM answered with reasonable confidence, return it
            if not llm_result.get("needs_escalation") and llm_result.get("confidence", 0) >= self.config.confidence_threshold:
                logger.info(f"SOP layer answered (confidence {llm_result.get('confidence')})")
                return llm_result

            # Layer 3: Escalate — nothing found
            logger.info("No layer answered — escalating")
            return {
                "answer": "This information is not available in our system. Your query has been escalated to our support team.",
                "confidence": 0.20,
                "needs_escalation": True,
                "reason": "not_in_sop_or_kb",
                "source": "escalation"
            }

        except Exception as e:
            logger.error(f"Error in FAQ agent: {str(e)}")
            return self._error_response(str(e))

    # ------------------------------------------------------------------
    # Formatters
    # ------------------------------------------------------------------
    @staticmethod
    def _format_sop(sop_data: Dict[str, Any]) -> str:
        lines = [
            f"Business: {sop_data.get('business', 'N/A')}",
            f"Hours: {sop_data.get('hours', 'N/A')}",
            f"Phone: {sop_data.get('phone', 'N/A')}",
            f"Location: {sop_data.get('location', 'N/A')}",
            "\nServices:"
        ]
        for service, price in sop_data.get("services", {}).items():
            lines.append(f"  - {service}: {price}")
        lines.append(f"\nBooking: {sop_data.get('booking', 'N/A')}")
        lines.append(f"Cancellation: {sop_data.get('cancellation', 'N/A')}")
        return "\n".join(lines)

    @staticmethod
    def _format_kb(kb_data: Dict[str, Any]) -> str:
        if not kb_data:
            return "No knowledge base available."
        lines = []
        for key, value in kb_data.items():
            if key == "clinic_information":
                continue
            if isinstance(value, dict):
                desc = value.get("description") or value.get("booking") or value.get("location") or ""
                if desc:
                    lines.append(f"{key}: {desc}")
            elif isinstance(value, str):
                lines.append(f"{key}: {value}")
        return "\n".join(lines) if lines else "No additional knowledge available."

    @staticmethod
    def _error_response(reason: str) -> Dict[str, Any]:
        return {
            "answer": "I encountered an error processing your request. Please contact support.",
            "confidence": 0.0,
            "needs_escalation": True,
            "reason": reason,
            "source": "error"
        }
