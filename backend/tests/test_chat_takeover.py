"""Human/OpenClaw take-over of website live chat: the `awaiting=1` inbox surfaces
threads no human has answered yet (the visitor's message, or one only the AI/auto-
fallback replied to), and an operator reply injects into the thread and clears it
from the inbox — no Telegram required."""
from app.extensions import db
from app.models import ChatConversation, ChatMessage


def _convo(session_id, *roles):
    c = ChatConversation(session_id=session_id, status="open")
    db.session.add(c)
    db.session.flush()
    for r in roles:
        db.session.add(ChatMessage(conversation_id=c.id, role=r, text=f"{r} message"))
    db.session.commit()
    return c


def test_awaiting_inbox_lists_threads_needing_a_human(client, auth, app):
    _convo("web_waiting", "visitor")                 # visitor's message is last → needs a human
    _convo("web_aifallback", "visitor", "agent")     # only the AI/auto-fallback replied → still needs a human
    _convo("web_answered", "visitor", "operator")    # a human operator replied → handled
    body = client.get("/api/admin/chat?status=open&awaiting=1", headers=auth).get_json()
    sids = {c["sessionId"] for c in body["items"]}
    assert "web_waiting" in sids
    assert "web_aifallback" in sids
    assert "web_answered" not in sids
    assert body["meta"]["awaiting"] is True


def test_operator_reply_injects_and_clears_inbox(client, auth, app):
    _convo("web_t", "visitor")
    res = client.post("/api/admin/chat/web_t/reply", headers=auth, json={"message": "Hi — we'll help you!"})
    assert res.status_code == 201
    # The reply is now part of the thread the visitor's widget polls.
    msgs = client.get("/api/admin/chat/web_t", headers=auth).get_json()["item"]["messages"]
    assert any(m["role"] == "operator" and "help" in m["text"] for m in msgs)
    # And the thread is no longer "awaiting a human".
    inbox = client.get("/api/admin/chat?status=open&awaiting=1", headers=auth).get_json()["items"]
    assert "web_t" not in {c["sessionId"] for c in inbox}
