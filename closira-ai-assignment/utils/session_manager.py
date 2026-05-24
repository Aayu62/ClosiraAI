"""
Session Manager — persistent session recording for Closira AI.

Every run of main.py creates a new session_YYYYMMDD_HHMMSS.json file
inside the sessions/ directory. All activity is written to disk after
every interaction so data survives crashes.

Schema (v2):
  session_metadata      — id, status, times, duration
  customer_profile      — intent + lead qualification
  conversation_outcome  — resolved, resolution_type, recommended action
  business_context      — clinic, services/pricing discussed
  escalation_data       — escalated flag, reasons, events
  knowledge_and_sop     — KB topics, SOP items, SOP gaps
  conversation_summary  — narrative summary, sentiment, booking interest
  analytics             — message counts, confidence stats
  transcript            — compact time/role/message list (at bottom)
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Manages persistent session files for the Closira AI workflow.

    All public method signatures are identical to v1 so no call-sites
    in main.py need to change.
    """

    def __init__(self, sessions_dir: Path) -> None:
        """
        Initialise the SessionManager and create a new session file.

        Args:
            sessions_dir: Path to the sessions/ directory.
        """
        self.sessions_dir = sessions_dir
        self._ensure_sessions_dir()

        self.session_id: str = self._generate_session_id()
        self.session_file: Path = self.sessions_dir / f"{self.session_id}.json"
        self.start_time: datetime = datetime.now()

        # Internal raw stores — used to build analytics at close time
        self._confidences: List[float] = []
        self._transcript: List[Dict[str, str]] = []

        self._data: Dict[str, Any] = self._initial_structure()
        self._flush()

        logger.info(f"Session created: {self.session_id}")

    # ------------------------------------------------------------------
    # Public API  (signatures unchanged from v1)
    # ------------------------------------------------------------------

    def save_message(
        self,
        role: str,
        content: str,
        confidence: Optional[float] = None,
    ) -> None:
        """
        Persist a single conversation message immediately.

        Args:
            role: "user" or "assistant"
            content: Message text
            confidence: Optional confidence score (assistant messages only)
        """
        try:
            # Compact transcript entry
            self._transcript.append({
                "time": datetime.now().strftime("%H:%M:%S"),
                "role": role,
                "message": content,
            })

            if confidence is not None:
                self._confidences.append(round(confidence, 4))

            self._data["transcript"] = self._transcript
            self._update_analytics()
            self._flush()
            logger.info("Message persisted")
        except Exception as e:
            logger.error(f"Failed to save message: {e}")

    def save_escalation(self, reason: str, message: str) -> None:
        """
        Persist an escalation event immediately.

        Args:
            reason: Escalation reason string
            message: The customer message that triggered escalation
        """
        try:
            event: Dict[str, Any] = {
                "timestamp": datetime.now().isoformat(),
                "reason": reason,
                "message": message,
            }
            esc = self._data["escalation_data"]
            esc["events"].append(event)

            # Keep reasons list deduplicated
            if reason not in esc["reasons"]:
                esc["reasons"].append(reason)
            esc["escalated"] = True

            self._flush()
            logger.info("Escalation persisted")
        except Exception as e:
            logger.error(f"Failed to save escalation: {e}")

    def save_booking_ref(self, booking_ref: str, support_needed: str = "") -> None:
        """
        Persist booking reference and support description for
        Existing Booking Support sessions.

        Args:
            booking_ref: Booking ID or phone number provided by customer.
            support_needed: Description of what support the customer needs.
        """
        try:
            ec = self._data["customer_profile"]["existing_customer"]
            ec["booking_ref"] = booking_ref or None
            ec["support_needed"] = support_needed or None
            self._flush()
            logger.info("Booking reference persisted")
        except Exception as e:
            logger.error(f"Failed to save booking ref: {e}")

    def save_lead(self, lead_info: Dict[str, Any]) -> None:
        """
        Persist updated lead information immediately.

        Args:
            lead_info: Dict with keys business_type, team_size, tools
        """
        try:
            lq = self._data["customer_profile"]["lead_qualification"]
            lq["customer_type"] = lead_info.get("business_type", lq["customer_type"])
            lq["team_size"] = lead_info.get("team_size", lq["team_size"])
            lq["current_tools"] = lead_info.get("tools", lq["current_tools"])
            self._flush()
            logger.info("Lead information persisted")
        except Exception as e:
            logger.error(f"Failed to save lead info: {e}")

    def save_summary(self, summary: Dict[str, Any]) -> None:
        """
        Populate the structured sections from the SummaryAgent output.

        Args:
            summary: Dict returned by SummaryAgent.generate()
        """
        try:
            # customer_profile — intent
            self._data["customer_profile"]["intent_category"] = summary.get(
                "intent", self._data["customer_profile"]["intent_category"]
            )

            # conversation_outcome
            outcome = self._data["conversation_outcome"]
            outcome["primary_intent"] = summary.get("intent", "")
            outcome["resolved"] = summary.get("resolved", True)
            outcome["resolution_type"] = summary.get("resolution_type", "Self-service")
            outcome["recommended_next_action"] = summary.get("recommended_action", "")

            # business_context
            bc = self._data["business_context"]
            bc["services_discussed"] = summary.get("services_discussed", [])
            bc["pricing_discussed"] = summary.get("pricing_discussed", [])

            # knowledge_and_sop
            ks = self._data["knowledge_and_sop"]
            ks["knowledge_base_topics_used"] = summary.get("kb_topics_used", [])
            ks["sop_items_used"] = summary.get("sop_items_used", [])
            ks["sop_gaps_identified"] = summary.get("sop_gaps", [])

            # conversation_summary
            cs = self._data["conversation_summary"]
            cs["summary"] = summary.get("conversation_details", "")
            cs["customer_sentiment"] = summary.get("customer_sentiment", "Neutral")
            cs["booking_interest"] = summary.get("booking_interest", False)

            # escalation_data — sync reasons from summary if present
            esc_reasons = summary.get("escalation_reasons", [])
            if esc_reasons:
                for r in esc_reasons:
                    if r not in self._data["escalation_data"]["reasons"]:
                        self._data["escalation_data"]["reasons"].append(r)
                self._data["escalation_data"]["escalated"] = True

            self._flush()
            logger.info("Summary persisted")
        except Exception as e:
            logger.error(f"Failed to save summary: {e}")

    def get_session_stats(self) -> Dict[str, Any]:
        """
        Return current session statistics without touching the file.

        Returns:
            Dict with message_count, escalation_count, session_duration,
            lead_information (v1-compatible keys), and session_id.
        """
        elapsed = (datetime.now() - self.start_time).total_seconds()
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)

        lq = self._data["customer_profile"]["lead_qualification"]
        # Return v1-compatible lead_information key so _show_session_info works
        return {
            "session_id": self.session_id,
            "message_count": self._data["analytics"]["total_messages"],
            "escalation_count": len(self._data["escalation_data"]["events"]),
            "session_duration": f"{minutes}m {seconds}s",
            "lead_information": {
                "business_type": lq["customer_type"],
                "team_size": lq["team_size"],
                "tools": lq["current_tools"],
            },
        }

    def close_session(self) -> Path:
        """
        Mark the session as closed, compute final analytics, and flush.

        Returns:
            Path to the saved session file.
        """
        try:
            end_time = datetime.now()
            elapsed = (end_time - self.start_time).total_seconds()

            meta = self._data["session_metadata"]
            meta["status"] = "closed"
            meta["end_time"] = end_time.isoformat()
            meta["duration_seconds"] = int(elapsed)

            self._update_analytics()
            self._flush()
            logger.info(f"Session closed: {self.session_id}")
        except Exception as e:
            logger.error(f"Failed to close session cleanly: {e}")
        return self.session_file

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _generate_session_id(self) -> str:
        return datetime.now().strftime("session_%Y%m%d_%H%M%S")

    def _ensure_sessions_dir(self) -> None:
        try:
            self.sessions_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.error(f"Cannot create sessions directory: {e}")
            raise

    def _update_analytics(self) -> None:
        """Recompute analytics from current transcript and confidence list."""
        user_msgs = [t for t in self._transcript if t["role"] == "user"]
        asst_msgs = [t for t in self._transcript if t["role"] == "assistant"]

        a = self._data["analytics"]
        a["total_messages"] = len(self._transcript)
        a["user_messages"] = len(user_msgs)
        a["assistant_messages"] = len(asst_msgs)

        if self._confidences:
            a["average_confidence"] = round(
                sum(self._confidences) / len(self._confidences), 4
            )
            a["highest_confidence"] = max(self._confidences)
            a["lowest_confidence"] = min(self._confidences)
        else:
            a["average_confidence"] = None
            a["highest_confidence"] = None
            a["lowest_confidence"] = None

    def _initial_structure(self) -> Dict[str, Any]:
        """Return the blank v2 session JSON structure."""
        return {
            "session_metadata": {
                "session_id": self.session_id,
                "status": "active",
                "start_time": self.start_time.isoformat(),
                "end_time": "",
                "duration_seconds": 0,
            },
            "customer_profile": {
                "intent_category": "",
                "existing_customer": {
                    "booking_ref": None,
                    "support_needed": None,
                },
                "lead_qualification": {
                    "customer_type": "",
                    "team_size": "",
                    "current_tools": "",
                },
            },
            "conversation_outcome": {
                "primary_intent": "",
                "resolved": False,
                "resolution_type": "",
                "recommended_next_action": "",
            },
            "business_context": {
                "clinic": "Bloom Aesthetics Clinic",
                "services_discussed": [],
                "pricing_discussed": [],
            },
            "escalation_data": {
                "escalated": False,
                "reasons": [],
                "events": [],
            },
            "knowledge_and_sop": {
                "knowledge_base_topics_used": [],
                "sop_items_used": [],
                "sop_gaps_identified": [],
            },
            "conversation_summary": {
                "summary": "",
                "customer_sentiment": "",
                "booking_interest": False,
            },
            "analytics": {
                "total_messages": 0,
                "assistant_messages": 0,
                "user_messages": 0,
                "average_confidence": None,
                "highest_confidence": None,
                "lowest_confidence": None,
            },
            "transcript": [],
        }

    def _flush(self) -> None:
        """Atomically write session data to disk via tmp-then-rename."""
        tmp_path = self.session_file.with_suffix(".tmp")
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
            tmp_path.replace(self.session_file)
        except OSError as e:
            logger.error(f"Session flush failed: {e}")
            try:
                tmp_path.unlink(missing_ok=True)
            except OSError:
                pass
