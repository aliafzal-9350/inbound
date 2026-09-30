"""Offline tests for the sales agent's deterministic logic (no network: LLM + embeddings are stubbed)."""
import asyncio
import datetime
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app import models  # noqa: E402
from app.core.database import Base  # noqa: E402
from app.services import knowledge_retriever, llm_client, sales_agent  # noqa: E402
from app.services.sales_agent import Analysis, apply_updates, decide, load_state  # noqa: E402

TZ = sales_agent._tz(type("T", (), {"default_timezone": "Asia/Karachi"})())
NOW = datetime.datetime(2026, 9, 30, 12, 0, tzinfo=TZ)   # Wednesday noon


def fresh_state(**overrides):
    state = load_state(models.Conversation(tenant_id="t", channel="facebook", contact_external_id="c"))
    state.update(overrides)
    return state


# ---------------------------------------------------------------- validation
@pytest.mark.parametrize("when,said,problem", [
    ("2026-10-01T15:00", "tomorrow 3pm", None),
    ("2026-09-29T17:00", "yesterday 5pm", "time_in_past"),
    ("2026-09-30T12:30", "today 12:30pm", "time_in_past"),        # under an hour's notice
    ("2026-10-01T03:00", "tomorrow 3am", "time_outside_hours"),
    ("2027-03-01T15:00", "1st march 3pm", "time_too_far"),
])
def test_meeting_time_validation(when, said, problem):
    state = fresh_state()
    problems = apply_updates(state, Analysis(lead_updates={"meeting_time": when}), NOW, TZ, said)
    assert problems == ([problem] if problem else [])
    assert (state["lead"].get("meeting_time") is None) == bool(problem)


def test_time_only_change_keeps_the_proposed_day():
    # eval bug: "actually make it 5pm" after "tomorrow 2:30pm" was read as today 5pm (already past)
    state = fresh_state(lead={"meeting_time": "2026-10-01T14:30"})
    apply_updates(state, Analysis(lead_updates={"meeting_time": "2026-09-30T17:00"}), NOW, TZ, "actually make it 5pm")
    assert state["lead"]["meeting_time"] == "2026-10-01T17:00"


def test_bare_time_that_already_passed_today_means_tomorrow():
    state = fresh_state()
    apply_updates(state, Analysis(lead_updates={"meeting_time": "2026-09-30T11:00"}), NOW, TZ, "11am works")
    assert state["lead"]["meeting_time"] == "2026-10-01T11:00"


def test_failed_change_during_confirmation_cannot_book_stale_time():
    state = fresh_state(stage="confirming", lead={"name": "A", "email": "a@x.com", "meeting_time": "2026-10-01T14:30"})
    problems = apply_updates(state, Analysis(lead_updates={"meeting_time": "2026-10-01T03:00"}), NOW, TZ, "tomorrow 3am")
    assert decide(state, Analysis(intents=["change_details"]), problems, False).ask_field == "meeting_time"
    assert state["stage"] == "discovery" and "meeting_time" not in state["lead"]
    assert decide(state, Analysis(intents=["confirm"], confirmation="yes"), [], False).action != "book"


@pytest.mark.parametrize("text,expected", [
    ("tomorrow 2:30 pm", "2026-10-01T14:30"), ("kal shaam 6 baje", "2026-10-01T18:00"),
    ("friday 12pm", "2026-10-02T12:00"), ("next monday 1pm", "2026-10-05T13:00"),
    ("day after tomorrow at 11am", "2026-10-02T11:00"), ("5pm", "2026-09-30T17:00"),
    ("+92 300 1234567", None), ("what is 234*12", None),
])
def test_heuristic_time_parser(text, expected):
    assert sales_agent.parse_time_heuristic(text, NOW) == expected


@pytest.mark.parametrize("text,human", [("I want to talk to a real person", True), ("connect me to your team", True),
                                        ("Are you a real human?", False), ("are u a bot", False)])
def test_heuristic_human_request_vs_are_you_human(text, human):
    assert ("human_request" in sales_agent.heuristic_analysis(text, fresh_state(), NOW).intents) == human


def test_heuristic_scam_question_is_not_a_complaint():
    assert "complaint" not in sales_agent.heuristic_analysis("Is this a scam?", fresh_state(), NOW).intents
    assert "complaint" in sales_agent.heuristic_analysis("this is a scam, refund my money", fresh_state(), NOW).intents


def test_hindi_script_reply_is_rejected_for_roman_urdu_customers():
    # Groq's GPT-OSS models answered Roman Urdu in Devanagari in testing
    assert not sales_agent.script_matches("आपके कपड़ों के ऑनलाइन स्टोर के लिए", "roman_urdu")
    assert sales_agent.script_matches("Ji bilkul, aap ka business kya hai?", "roman_urdu")
    assert sales_agent.script_matches("آپ کا کاروبار کیا ہے؟", "urdu")
    assert not sales_agent.script_matches("What does your business do?", "urdu")


def test_language_script_is_objective_and_neutral_replies_keep_language():
    assert sales_agent.normalize_language("roman_urdu", "میرا ریسٹورنٹ ہے") == "urdu"
    assert sales_agent.normalize_language("english", "ahmed.khan@gmail.com", "roman_urdu") == "roman_urdu"
    assert sales_agent.normalize_language("english", "Can you reply in English please?", "roman_urdu") == "english"


@pytest.mark.parametrize("email,ok", [("omar@gmail.com", True), ("omar@gmail", False), ("a b@x.com", False),
                                      ("Sara.Khan+x@Example.co.uk", True)])
def test_email_validation(email, ok):
    state = fresh_state()
    problems = apply_updates(state, Analysis(lead_updates={"email": email}), NOW, TZ)
    assert bool(state["lead"].get("email")) == ok
    assert ("invalid_email" in problems) == (not ok)


def test_model_completed_email_is_rejected():
    # live eval: customer typed "omar@gmail", the model returned "omar@gmail.com"
    state = fresh_state()
    problems = apply_updates(state, Analysis(lead_updates={"email": "omar@gmail.com"}), NOW, TZ, "omar@gmail")
    assert "email" not in state["lead"] and problems == ["invalid_email"]


def test_vague_time_is_flagged():
    state = fresh_state()
    assert apply_updates(state, Analysis(lead_updates={"meeting_time_text": "tomorrow evening"}), NOW, TZ) == ["time_vague"]


def test_greeting_is_not_taken_as_name():
    state = fresh_state()
    apply_updates(state, Analysis(lead_updates={"name": "hi"}), NOW, TZ)
    assert "name" not in state["lead"]


# ---------------------------------------------------------------- decisions
def test_asks_one_field_at_a_time_in_playbook_order():
    state = fresh_state()
    order = []
    for key, value in [("business", "perfume reselling"), ("goal", "instagram DMs"), ("name", "Ali"),
                       ("email", "ali@x.com")]:
        order.append(decide(state, Analysis(intents=["share_info"]), [], False).ask_field)
        state["lead"][key] = value
    order.append(decide(state, Analysis(intents=["share_info"]), [], False).ask_field)
    assert order == ["business", "goal", "name", "email", "meeting_time"]


def test_skippable_fields_stop_being_asked_after_two_tries():
    state = fresh_state(asked={"business": 2, "goal": 2})
    assert decide(state, Analysis(intents=["share_info"]), [], False).ask_field == "name"


def test_booking_needs_explicit_confirmation():
    lead = {"name": "Ali", "email": "ali@x.com", "business": "shop", "goal": "DMs", "meeting_time": "2026-10-01T15:00"}
    state = fresh_state(lead=dict(lead))
    assert decide(state, Analysis(intents=["share_info"]), [], False).action == "confirm"
    assert state["stage"] == "confirming"
    assert decide(state, Analysis(intents=["smalltalk"]), [], False).action == "confirm"   # no yes -> ask again
    assert decide(state, Analysis(intents=["confirm"], confirmation="yes"), [], False).action == "book"


def test_no_during_confirmation_asks_what_to_change():
    state = fresh_state(stage="confirming", lead={"name": "A", "email": "a@x.com", "meeting_time": "2026-10-01T15:00"})
    assert decide(state, Analysis(intents=["decline"], confirmation="no"), [], False).action == "ask_change"


def test_whatsapp_email_is_optional_after_one_ask():
    state = fresh_state(lead={"business": "b", "goal": "g", "name": "A"}, asked={"email": 1})
    assert decide(state, Analysis(intents=["share_info"]), [], True).ask_field == "meeting_time"


def test_declined_email_falls_back_to_phone_unless_whatsapp_number_known():
    state = fresh_state(lead={"business": "b", "goal": "g", "name": "A"}, declined=["email"])
    assert decide(state, Analysis(intents=["decline"]), [], False).ask_field == "phone"
    assert decide(fresh_state(lead=dict(state["lead"]), declined=["email"]),
                  Analysis(intents=["decline"]), [], True).ask_field == "meeting_time"


def test_customer_can_change_their_mind_about_a_call():
    state = fresh_state(lead={"business": "b", "goal": "g", "name": "A", "email": "a@x.com"},
                        awaiting="meeting_time")
    assert decide(state, Analysis(intents=["decline"]), [], False).action == "close"
    assert decide(state, Analysis(intents=["wants_meeting"]), [], False).ask_field == "meeting_time"


def test_human_request_escalates():
    state = fresh_state()
    plan = decide(state, Analysis(intents=["human_request"]), [], False)
    assert plan.action == "escalate" and state["escalated"]


def test_booked_conversation_can_cancel_and_is_not_re_qualified():
    state = fresh_state(stage="booked", lead={"name": "A", "email": "a@x.com", "meeting_time": "2026-10-01T15:00"})
    assert decide(state, Analysis(intents=["question"], question="where are you?"), [], False).action == "booked"
    assert decide(state, Analysis(intents=["cancel_meeting"]), [], False).action == "cancelled"


# ---------------------------------------------------------------- reply hygiene
def test_sanitize_strips_faq_labels_and_markdown():
    raw = 'Question: Can you help?\nAnswer: **Yes**, we can.'
    assert sales_agent.sanitize_reply(raw, "facebook") == "Can you help?\nYes, we can."
    assert sales_agent.sanitize_reply("**Yes**", "whatsapp") == "*Yes*"


# ---------------------------------------------------------------- retrieval pieces
def test_bm25_prefers_matching_terms():
    docs = {"a": knowledge_retriever._tokens("Where are you located? Office at McLeod Road Lahore"),
            "b": knowledge_retriever._tokens("How much does it cost? Custom quote after consultation")}
    assert knowledge_retriever._bm25_rank("office location lahore", docs, 5)[0] == "a"


def test_keyword_only_mode_when_embeddings_unavailable():
    hit = knowledge_retriever.KnowledgeHit(id="x", question="q", answer="a", lexical_rank=0, dense_available=False)
    assert hit.is_relevant
    hit.lexical_rank = 5
    assert not hit.is_relevant


# ---------------------------------------------------------------- full turns, LLM down
@pytest.fixture()
def db():
    engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    session.add(models.Tenant(id="t1", business_name="RAVISN UK", slug="t1", api_key="k", default_timezone="Asia/Karachi"))
    session.add(models.KnowledgeEntry(tenant_id="t1", question="How much does it cost?",
                                      answer="Pricing is custom; we share a quote after a free consultation."))
    session.commit()
    yield session
    session.close()


@pytest.fixture()
def offline(monkeypatch):
    async def down(*args, **kwargs):
        raise llm_client.LLMUnavailable("offline test")
    monkeypatch.setattr(llm_client, "generate", down)
    monkeypatch.setattr(llm_client, "generate_json", down)
    monkeypatch.setattr(knowledge_retriever, "embed_texts", down)

    async def no_vectors(queries):
        return [None for _ in queries]
    monkeypatch.setattr(knowledge_retriever, "embed_queries", no_vectors)


def turn(db, convo, text, history):
    tenant = db.query(models.Tenant).one()
    result = asyncio.run(sales_agent.handle_turn(db, tenant, convo, "facebook", text, history,
                                                 now_utc=NOW.astimezone(datetime.timezone.utc)))
    history += [{"role": "user", "content": text}, {"role": "assistant", "content": result.reply}]
    return result


def test_llm_outage_still_answers_from_knowledge_and_asks_next_question(db, offline):
    convo = models.Conversation(tenant_id="t1", channel="facebook", contact_external_id="c1")
    db.add(convo)
    db.commit()
    result = turn(db, convo, "How much does it cost?", [])
    assert "custom" in result.reply.lower()
    assert "question:" not in result.reply.lower() and "answer:" not in result.reply.lower()
    assert "business" in result.reply.lower()          # moves the conversation forward


def test_llm_outage_booking_flow_books_only_after_yes(db, offline):
    convo = models.Conversation(tenant_id="t1", channel="facebook", contact_external_id="c2")
    db.add(convo)
    db.commit()
    history = []
    convo.agent_state = {"lead": {"business": "shop", "goal": "DMs", "name": "Ali", "email": "ali@x.com",
                                  "meeting_time": "2026-10-01T15:00"}, "stage": "confirming", "awaiting": "confirmation"}
    db.commit()
    assert db.query(models.Booking).count() == 0
    result = turn(db, convo, "yes", history)
    assert result.booking_created and result.stage == "booked"
    booking = db.query(models.Booking).one()
    assert booking.status == "pending"                    # no calendar configured -> team confirms
    assert booking.booking_start_time == datetime.datetime(2026, 10, 1, 10, 0)  # 15:00 PKT stored as UTC
    assert "ali@x.com" in (booking.customer_email or "")
