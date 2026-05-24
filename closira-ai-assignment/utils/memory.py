import json
from datetime import datetime
from typing import Any, Dict, List, Optional


class Memory:
    """Manages conversation memory and state."""

    def __init__(self):
        self.conversation: List[Dict[str, str]] = []
        self.lead_info: Dict[str, Any] = {}
        self.escalations: List[Dict[str, Any]] = []
        self.session_start: datetime = datetime.now()

    def add_message(self, role: str, content: str) -> None:
        """Add message to conversation history."""
        self.conversation.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })

    def get_history(self) -> List[Dict[str, str]]:
        """Get conversation history."""
        return self.conversation

    def get_conversation_text(self) -> str:
        """Get conversation history as formatted text."""
        text = ""
        for msg in self.conversation:
            role = msg["role"].upper()
            content = msg["content"]
            text += f"{role}: {content}\n\n"
        return text

    def store_lead_info(self, data: Dict[str, Any]) -> None:
        """Store lead qualification information."""
        self.lead_info.update(data)

    def get_lead_info(self) -> Dict[str, Any]:
        """Get lead information."""
        return self.lead_info

    def add_escalation(self, reason: str, message: str, confidence: Optional[float] = None) -> None:
        """Record escalation event."""
        escalation = {
            "timestamp": datetime.now().isoformat(),
            "reason": reason,
            "message": message,
            "confidence": confidence
        }
        self.escalations.append(escalation)

    def get_escalations(self) -> List[Dict[str, Any]]:
        """Get escalation history."""
        return self.escalations

    def get_session_duration(self) -> float:
        """Get session duration in seconds."""
        return (datetime.now() - self.session_start).total_seconds()

    def clear(self) -> None:
        """Clear all memory."""
        self.conversation = []
        self.lead_info = {}
        self.escalations = []
        self.session_start = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Export memory state as dictionary."""
        return {
            "conversation": self.conversation,
            "lead_info": self.lead_info,
            "escalations": self.escalations,
            "session_duration": self.get_session_duration()
        }
