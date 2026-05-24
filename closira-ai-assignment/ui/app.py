"""
Closira TUI — split-pane terminal UI built with Textual 8.

Left pane  : clean customer-facing chat + input bar at bottom
Right pane : live system log
"""

from __future__ import annotations

import logging
import queue
import threading

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Input, RichLog, Static

from ui.log_handler import TUILogHandler

# ---------------------------------------------------------------------------
# Module-level log handler — attached to root logger immediately so every
# log record anywhere in the project is captured.
# ---------------------------------------------------------------------------
tui_log_handler = TUILogHandler()
logging.getLogger().addHandler(tui_log_handler)


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------
CSS = """
Screen {
    background: #0d1117;
    layout: horizontal;
}

/* ── Left pane ─────────────────────────────────────────────────── */
#chat-pane {
    width: 55%;
    height: 100%;
    layout: vertical;
    border: solid #30363d;
}

#chat-title {
    height: 1;
    background: #161b22;
    color: #58a6ff;
    text-align: center;
    padding: 0 1;
}

#chat-log {
    height: 1fr;
    padding: 0 1;
}

#hint-bar {
    height: 1;
    background: #161b22;
    color: #6e7681;
    padding: 0 1;
}

/* Input default height is 3 (tall border). Keep it. */
#user-input {
    height: 3;
    background: #0d1117;
    color: #e6edf3;
    border: tall #58a6ff;
    padding: 0 1;
}

/* ── Right pane ─────────────────────────────────────────────────── */
#log-pane {
    width: 45%;
    height: 100%;
    layout: vertical;
    border: solid #30363d;
}

#log-title {
    height: 1;
    background: #161b22;
    color: #3fb950;
    text-align: center;
    padding: 0 1;
}

#sys-log {
    height: 1fr;
    padding: 0 1;
}
"""


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
class ClosiraApp(App):
    """
    Two-pane Textual application.

    Worker thread  ──► _output_q ──► UI (drain every 50 ms)
    UI (Input)     ──► _input_q  ──► worker thread (blocking get)
    """

    TITLE = "Bloom Aesthetics Clinic — AI Support"
    # Hide all default bindings from any footer / palette
    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=False),
    ]
    ENABLE_COMMAND_PALETTE = False

    CSS = CSS

    def __init__(self) -> None:
        super().__init__()
        self._output_q: queue.Queue[tuple[str, str]] = queue.Queue()
        self._input_q: queue.Queue[str] = queue.Queue()
        self._worker_thread: threading.Thread | None = None

    # ------------------------------------------------------------------
    # Compose
    # ------------------------------------------------------------------

    def compose(self) -> ComposeResult:
        with Vertical(id="chat-pane"):
            yield Static("  💬  Customer Chat", id="chat-title")
            yield RichLog(id="chat-log", highlight=False, markup=True, wrap=True)
            yield Static(
                "  start = restart  |  quit = exit",
                id="hint-bar",
            )
            yield Input(
                placeholder="Type your message and press Enter…",
                id="user-input",
            )
        with Vertical(id="log-pane"):
            yield Static("  ⚙  System Log", id="log-title")
            yield RichLog(id="sys-log", highlight=False, markup=True, wrap=True)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def on_mount(self) -> None:
        # Attach log handler to the sys-log widget
        tui_log_handler.attach(self.query_one("#sys-log", RichLog))

        # Focus input immediately
        self.query_one("#user-input", Input).focus()

        # Start worker
        self._worker_thread = threading.Thread(
            target=self._run_conversation_worker,
            daemon=True,
        )
        self._worker_thread.start()

        # Drain output queue every 50 ms
        self.set_interval(0.05, self._drain_output_queue)

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------

    def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        if not text:
            return
        event.input.clear()
        self.query_one("#chat-log", RichLog).write(
            f"[bold #58a6ff]You:[/]  {text}"
        )
        self._input_q.put(text)

    # ------------------------------------------------------------------
    # Output queue drain
    # ------------------------------------------------------------------

    def _drain_output_queue(self) -> None:
        chat = self.query_one("#chat-log", RichLog)
        while not self._output_q.empty():
            try:
                role, text = self._output_q.get_nowait()
            except queue.Empty:
                break
            if role == "ai":
                chat.write(f"\n[bold #3fb950]AI:[/]  {text}\n")
            elif role == "system":
                if text.strip():
                    chat.write(f"[#8b949e]{text}[/]")
            elif role == "quit":
                self.exit()

    # ------------------------------------------------------------------
    # Worker thread
    # ------------------------------------------------------------------

    def _run_conversation_worker(self) -> None:
        import builtins

        original_print = builtins.print
        original_input = builtins.input

        def tui_print(*args, sep=" ", end="\n", **kwargs) -> None:
            text = sep.join(str(a) for a in args)
            if text.strip():
                self._output_q.put(("system", text))

        def tui_input(prompt: str = "") -> str:
            if prompt.strip():
                self._output_q.put(("system", prompt))
            return self._input_q.get()

        builtins.print = tui_print
        builtins.input = tui_input

        try:
            from dotenv import load_dotenv
            load_dotenv()

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

            config = Config()
            config.validate()

            logger = setup_logger("closira", config.logs_dir, config.log_level)
            # Strip StreamHandlers so logs go only to the TUI right pane
            for h in list(logging.getLogger("closira").handlers):
                if isinstance(h, logging.StreamHandler) and not isinstance(
                    h, TUILogHandler
                ):
                    logging.getLogger("closira").removeHandler(h)

            llm_client = LLMClient(
                api_key=config.openrouter_api_key,
                base_url=config.base_url,
                model=config.model,
            )

            faq_agent        = FAQAgent(llm_client, config)
            qual_agent       = QualificationAgent(llm_client, config)
            escalation_agent = EscalationAgent(config)
            review_agent     = ReviewAgent(llm_client, config)
            summary_agent    = SummaryAgent(llm_client, config)
            memory           = Memory()
            session          = SessionManager(config.sessions_dir)
            intent           = ""

            # ── process one message ──────────────────────────────────
            def process_message(msg: str) -> str:
                logger.info(f"Processing: {msg[:50]}...")
                session.save_message(role="user", content=msg)
                memory.add_message("customer", msg)

                logger.info("Step 1: FAQ Agent processing")
                faq = faq_agent.respond(msg, memory.get_conversation_text())
                conf = faq.get("confidence", 0.0)

                if faq.get("needs_escalation"):
                    memory.add_escalation(
                        reason="faq_escalation", message=msg, confidence=conf
                    )

                logger.info("Step 2: Escalation Agent processing")
                esc = escalation_agent.detect(
                    customer_message=msg, confidence=conf, unanswered_count=0
                )
                if esc.get("escalate"):
                    reason = esc.get("reason", "unknown")
                    logger.info(f"Escalation detected: {reason}")
                    memory.add_escalation(
                        reason=reason, message=msg, confidence=conf
                    )
                    session.save_escalation(reason=reason, message=msg)
                    resp = (
                        f"[ESCALATED] {reason}. Your concern has been escalated "
                        "to our support team. We'll follow up shortly."
                    )
                    session.save_message(
                        role="assistant", content=resp, confidence=conf
                    )
                    memory.add_message("assistant", resp)
                    return resp

                logger.info("Step 3: Safety Reviewer Agent processing")
                review = review_agent.validate(
                    customer_message=msg,
                    generated_response=faq.get("answer", ""),
                    confidence=conf,
                    source=faq.get("source", "llm_sop"),
                )
                if not review.get("approved"):
                    logger.warning(f"Review failed: {review.get('reason')}")
                    memory.add_escalation(
                        reason="review_failed", message=msg, confidence=conf
                    )
                    session.save_escalation(reason="review_failed", message=msg)
                    resp = (
                        "[ESCALATED] Safety check failed. "
                        "Your inquiry has been escalated to our support team."
                    )
                    session.save_message(
                        role="assistant", content=resp, confidence=conf
                    )
                    memory.add_message("assistant", resp)
                    return resp

                resp = faq.get("answer", "I could not generate a response.")
                session.save_message(role="assistant", content=resp, confidence=conf)
                memory.add_message("assistant", resp)
                logger.info(f"Response approved and sent (confidence: {conf})")
                return resp

            # ── intake flow ──────────────────────────────────────────
            def run_intake() -> None:
                nonlocal intent
                agent = IntakeAgent()
                result = agent.run()
                intent = result["intent"]
                lead   = result["lead_data"]
                complaint        = result.get("complaint_text", "")
                booking_ref      = result.get("booking_ref", "")
                booking_support  = result.get("booking_support_needed", "")

                session._data["customer_profile"]["intent_category"] = intent
                session._flush()

                qual_agent.set_answers(
                    business_type=lead.get("business_type", ""),
                    team_size=lead.get("team_size", ""),
                    tools=lead.get("tools", ""),
                )
                memory.store_lead_info(lead)
                session.save_lead(lead)

                if intent == "Raise Complaint" and complaint:
                    memory.add_message("customer", complaint)
                    session.save_message(role="user", content=complaint)
                    esc_msg = (
                        "I've flagged this for our support team and marked it "
                        "for priority review. A team member will follow up shortly."
                    )
                    memory.add_message("assistant", esc_msg)
                    session.save_message(role="assistant", content=esc_msg)
                    memory.add_escalation(
                        reason="complaint_intake", message=complaint
                    )
                    session.save_escalation(
                        reason="complaint_intake", message=complaint
                    )
                    self._output_q.put(("ai", esc_msg))

                if intent == "Existing Booking Support" and booking_ref:
                    session.save_booking_ref(booking_ref, booking_support)
                    support_msg = booking_support or booking_ref
                    memory.add_message(
                        "customer",
                        f"Booking ref: {booking_ref}. Need: {support_msg}",
                    )
                    session.save_message(
                        role="user",
                        content=f"Booking ref: {booking_ref}. Support needed: {support_msg}",
                    )
                    esc_msg = (
                        "I've escalated your booking query to our support team. "
                        "A team member will follow up shortly."
                    )
                    memory.add_message("assistant", esc_msg)
                    session.save_message(role="assistant", content=esc_msg)
                    memory.add_escalation(
                        reason="booking_support_escalation", message=support_msg
                    )
                    session.save_escalation(
                        reason="booking_support_escalation", message=support_msg
                    )
                    self._output_q.put(("ai", esc_msg))

                logger.info(f"Intake complete — intent={intent}, lead={lead}")

            # ── show session stats ───────────────────────────────────
            def show_session_info() -> None:
                stats = session.get_session_stats()
                lead  = stats.get("lead_information", {})
                for line in [
                    "=" * 44,
                    "Current Session Info",
                    "=" * 44,
                    f"Session ID:   {stats['session_id']}",
                    f"Intent:       {intent or 'Not set'}",
                    f"Messages:     {stats['message_count']}",
                    f"Escalations:  {stats['escalation_count']}",
                    f"Duration:     {stats['session_duration']}",
                    "",
                    "Lead Data:",
                    f"  Customer Type: {lead.get('business_type') or 'Not collected'}",
                    f"  Team Size:     {lead.get('team_size') or 'Not collected'}",
                    f"  Tools:         {lead.get('tools') or 'Not collected'}",
                    "=" * 44,
                ]:
                    self._output_q.put(("system", line))

            # ── end session ──────────────────────────────────────────
            def end_session() -> None:
                self._output_q.put(("system", "Preparing conversation summary…"))
                summary = summary_agent.generate(
                    conversation_history=memory.get_conversation_text(),
                    lead_info=memory.get_lead_info(),
                    escalation_logs=memory.get_escalations(),
                )
                session.save_summary(summary)
                logger.info("Summary generated")

                lead        = summary.get("lead_info") or memory.get_lead_info()
                sop_gaps    = summary.get("sop_gaps", [])
                esc_reasons = summary.get("escalation_reasons", [])
                services    = summary.get("services_discussed", [])

                lines = [
                    "",
                    "=" * 48,
                    "SESSION SUMMARY",
                    "=" * 48,
                    f"Intent:             {summary.get('intent', intent or 'N/A')}",
                    f"Resolved:           {summary.get('resolved', 'N/A')}",
                    f"Resolution Type:    {summary.get('resolution_type', 'N/A')}",
                    f"Customer Sentiment: {summary.get('customer_sentiment', 'N/A')}",
                    f"Booking Interest:   {summary.get('booking_interest', False)}",
                    "",
                    "Lead Information:",
                    f"  Customer Type: {lead.get('business_type') or 'N/A'}",
                    f"  Team Size:     {lead.get('team_size') or 'N/A'}",
                    f"  Tools:         {lead.get('tools') or 'N/A'}",
                ]
                if services:
                    lines.append(f"Services Discussed: {', '.join(services)}")
                lines += [
                    f"SOP Gaps:    {', '.join(sop_gaps) if sop_gaps else 'None'}",
                    f"Escalations: {', '.join(esc_reasons) if esc_reasons else 'None'}",
                    f"Conversation: {summary.get('conversation_details', 'N/A')}",
                    f"Recommended Action: {summary.get('recommended_action', 'N/A')}",
                    "=" * 48,
                    "",
                ]
                for line in lines:
                    self._output_q.put(("system", line))

                path = session.close_session()
                self._output_q.put(("system", f"Session saved: {path}"))
                self._output_q.put(
                    ("system", "Thank you for contacting Bloom Aesthetics Clinic.")
                )
                logger.info(f"Session ended — file: {path}")

            # ── main flow ────────────────────────────────────────────
            run_intake()

            while True:
                text = self._input_q.get().strip()
                if not text:
                    continue

                if text.lower() == "show session":
                    show_session_info()
                    continue

                if text.lower() == "start":
                    self._output_q.put(("system", "-" * 44))
                    self._output_q.put(
                        ("system", "Restarting — taking you back to the beginning.")
                    )
                    self._output_q.put(("system", "-" * 44))
                    logger.info("Intake restarted by user")
                    run_intake()
                    continue

                if text.lower() in ("quit", "exit", "bye"):
                    end_session()
                    self._output_q.put(("quit", ""))
                    break

                response = process_message(text)
                self._output_q.put(("ai", response))

        except Exception as exc:
            logging.getLogger("closira").error(
                f"Worker error: {exc}", exc_info=True
            )
            self._output_q.put(("system", f"[ERROR] {exc}"))
            self._output_q.put(("quit", ""))
        finally:
            builtins.print = original_print
            builtins.input = original_input
