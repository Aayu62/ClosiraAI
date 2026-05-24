import logging
from typing import Any, Dict, Optional
from utils.llm import LLMClient
from utils.parser import Parser
from utils.config import Config


logger = logging.getLogger(__name__)


class QualificationAgent:
    """Handles lead qualification through structured questions."""

    QUESTIONS = [
        "What type of business are you in?",
        "How large is your team?",
        "What tools are you currently using?"
    ]

    def __init__(self, llm_client: LLMClient, config: Config):
        self.llm = llm_client
        self.config = config
        self.parser = Parser()
        self.answered_questions: Dict[str, str] = {}

    def _load_prompt_template(self) -> str:
        """Load qualification prompt template."""
        try:
            prompt_path = self.config.get_prompt_path("qualification_prompt")
            with open(prompt_path, "r") as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"Qualification prompt not found at {prompt_path}")
            raise

    def get_next_question(self) -> Optional[str]:
        """Get the next unanswered question."""
        for i, question in enumerate(self.QUESTIONS):
            if i not in self.answered_questions:
                return question
        return None

    def ask_next(self) -> Dict[str, Any]:
        """
        Ask the next qualification question.

        Returns:
            Question message to display to customer
        """
        try:
            next_q = self.get_next_question()
            if not next_q:
                logger.info("All qualification questions answered")
                return {"message": "Thank you for providing that information!", "complete": True}

            prompt_template = self._load_prompt_template()
            answered_list = ", ".join(
                [f"{i}. {self.QUESTIONS[i]}: {self.answered_questions[i]}"
                 for i in sorted(self.answered_questions.keys())]
            ) or "None yet"

            system_prompt = prompt_template.format(
                answered_questions=answered_list,
                next_question=next_q
            )

            response_text = self.llm.call(
                system_prompt=system_prompt,
                user_message=next_q,
                temperature=0.3
            )

            if not response_text:
                logger.error("LLM call failed in qualification agent")
                return {"message": next_q, "complete": False}

            parsed = self.parser.parse_json(response_text)
            if not parsed:
                logger.warning(f"Failed to parse qualification response: {response_text[:100]}")
                return {"message": next_q, "complete": False}

            logger.info(f"Asked qualification question: {next_q}")
            return {
                "message": parsed.get("message", next_q),
                "question": next_q,
                "complete": False
            }

        except Exception as e:
            logger.error(f"Error in qualification agent: {str(e)}")
            next_q = self.get_next_question()
            return {"message": next_q or "Thank you for your information.", "complete": next_q is None}

    def save_response(self, answer: str) -> None:
        """Save customer response to current question."""
        try:
            next_q = self.get_next_question()
            if next_q:
                q_index = self.QUESTIONS.index(next_q)
                self.answered_questions[q_index] = answer
                logger.info(f"Saved answer for question {q_index + 1}")
        except Exception as e:
            logger.error(f"Error saving qualification response: {str(e)}")

    def is_complete(self) -> bool:
        """Check if all qualification questions are answered."""
        return len(self.answered_questions) == len(self.QUESTIONS)

    def set_answers(self, business_type: str, team_size: str, tools: str) -> None:
        """
        Pre-populate answers from the intake flow so the qualification
        agent is considered complete without running its own question loop.

        Args:
            business_type: Customer/business type answer.
            team_size: Team size answer.
            tools: Tools currently used answer.
        """
        self.answered_questions[0] = business_type
        self.answered_questions[1] = team_size
        self.answered_questions[2] = tools
        logger.info("Qualification answers pre-populated from intake flow")

    def get_qualification_data(self) -> Dict[str, str]:
        """Get collected qualification data in structured format."""
        return {
            "business_type": self.answered_questions.get(0, ""),
            "team_size": self.answered_questions.get(1, ""),
            "tools": self.answered_questions.get(2, "")
        }
