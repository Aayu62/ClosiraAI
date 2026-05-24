import json
import logging
import re
from typing import Any, Dict, Optional


logger = logging.getLogger(__name__)


class Parser:
    """Utility for parsing and validating LLM outputs."""

    @staticmethod
    def parse_json(text: str) -> Optional[Dict[str, Any]]:
        """Parse JSON from potentially malformed text."""
        if not text:
            return None

        text = text.strip()

        # Try to extract JSON block if wrapped in markdown
        json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', text, re.DOTALL)
        if json_match:
            text = json_match.group(1).strip()

        # Try to find JSON object/array in the text
        if not (text.startswith('{') or text.startswith('[')):
            # Look for first { or [
            brace_idx = text.find('{') if '{' in text else -1
            bracket_idx = text.find('[') if '[' in text else -1
            candidates = [i for i in (brace_idx, bracket_idx) if i > -1]
            start_idx = min(candidates) if candidates else -1
            if start_idx > -1:
                text = text[start_idx:]

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to extract the outermost complete JSON object
            try:
                start = text.index('{')
                depth = 0
                for i, ch in enumerate(text[start:], start):
                    if ch == '{':
                        depth += 1
                    elif ch == '}':
                        depth -= 1
                        if depth == 0:
                            return json.loads(text[start:i + 1])
            except (ValueError, json.JSONDecodeError):
                pass
            logger.debug(f"Failed to parse JSON: {text[:100]}")
            return None

    @staticmethod
    def safe_extract(data: Dict[str, Any], key: str, default: Any = None) -> Any:
        """Safely extract value from dict with default fallback."""
        return data.get(key, default)

    @staticmethod
    def validate_faq_response(data: Dict[str, Any]) -> bool:
        """Validate FAQ agent response structure."""
        required_keys = {"answer", "confidence", "needs_escalation", "reason"}
        return all(key in data for key in required_keys)

    @staticmethod
    def validate_qualification_response(data: Dict[str, Any]) -> bool:
        """Validate qualification agent response structure."""
        required_keys = {"question", "answer_received"}
        return all(key in data for key in required_keys)

    @staticmethod
    def validate_escalation_response(data: Dict[str, Any]) -> bool:
        """Validate escalation agent response structure."""
        required_keys = {"escalate", "reason"}
        return all(key in data for key in required_keys)

    @staticmethod
    def validate_review_response(data: Dict[str, Any]) -> bool:
        """Validate reviewer agent response structure."""
        required_keys = {"approved", "risk", "reason"}
        return all(key in data for key in required_keys)

    @staticmethod
    def validate_summary_response(data: Dict[str, Any]) -> bool:
        """Validate summary agent response structure."""
        required_keys = {
            "intent", "resolved", "resolution_type", "recommended_action",
            "services_discussed", "sop_gaps", "escalation_reasons",
            "conversation_details", "customer_sentiment", "booking_interest",
            "lead_info",
        }
        return all(key in data for key in required_keys)
