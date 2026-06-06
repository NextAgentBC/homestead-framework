"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { t, type Messages } from "@/lib/i18n";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api";
const ENABLED = (process.env.NEXT_PUBLIC_WEBCHAT_ENABLED || "true") !== "false";
const STORAGE_KEY = "homestead_chat_session";
const POLL_MS = 5000;

type Msg = { id?: number; role: string; text: string };

export function ChatWidget({ locale, messages, assistantName }: { locale: string; messages: Messages; assistantName?: string }) {
  const [open, setOpen] = useState(false);
  const [sessionId, setSessionId] = useState("");
  const [server, setServer] = useState<Msg[]>([]);
  const [pending, setPending] = useState<string | null>(null);
  const [sending, setSending] = useState(false);
  const [input, setInput] = useState("");
  const logRef = useRef<HTMLDivElement>(null);
  const sendingRef = useRef(false);

  // Restore the session id once on mount.
  useEffect(() => {
    try {
      const sid = window.localStorage.getItem(STORAGE_KEY) || "";
      if (sid) setSessionId(sid);
    } catch {
      /* private mode / blocked storage — chat still works, just no persistence */
    }
  }, []);

  const fetchHistory = useCallback(async (sid: string) => {
    if (!sid) return;
    try {
      const res = await fetch(`${API_BASE}/chat/${encodeURIComponent(sid)}`, { cache: "no-store" });
      if (!res.ok) return;
      const data = await res.json();
      const list: Msg[] = data?.item?.messages || [];
      setServer(list);
    } catch {
      /* transient — next poll retries */
    }
  }, []);

  // Load history when the panel opens with an existing session.
  useEffect(() => {
    if (open && sessionId) fetchHistory(sessionId);
  }, [open, sessionId, fetchHistory]);

  // Poll for operator take-over / mirrored replies while open and idle.
  useEffect(() => {
    if (!open || !sessionId) return;
    const id = window.setInterval(() => {
      if (!sendingRef.current) fetchHistory(sessionId);
    }, POLL_MS);
    return () => window.clearInterval(id);
  }, [open, sessionId, fetchHistory]);

  // Keep the log scrolled to the newest message.
  useEffect(() => {
    const el = logRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [server, pending, sending, open]);

  const send = useCallback(async () => {
    const text = input.trim();
    if (!text || sendingRef.current) return;
    setInput("");
    setPending(text);
    setSending(true);
    sendingRef.current = true;
    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sessionId: sessionId || undefined, message: text, locale, page: window.location?.pathname }),
      });
      if (res.status === 429) {
        setServer((s) => [...s, { role: "agent", text: t(messages, "chat.rateLimited") }]);
      } else if (res.ok) {
        const data = await res.json();
        const sid: string = data?.item?.sessionId || sessionId;
        if (sid && sid !== sessionId) {
          setSessionId(sid);
          try { window.localStorage.setItem(STORAGE_KEY, sid); } catch { /* ignore */ }
        }
        await fetchHistory(sid);
      } else {
        setServer((s) => [...s, { role: "agent", text: t(messages, "chat.error") }]);
      }
    } catch {
      setServer((s) => [...s, { role: "agent", text: t(messages, "chat.error") }]);
    } finally {
      setPending(null);
      setSending(false);
      sendingRef.current = false;
    }
  }, [input, sessionId, locale, messages, fetchHistory]);

  if (!ENABLED) return null;

  const shown: Msg[] = [...server];
  if (pending) shown.push({ role: "visitor", text: pending });

  return (
    <>
      <button
        type="button"
        className="chat-fab"
        aria-label={t(messages, "chat.open")}
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
      >
        {open ? "✕" : "💬"}
      </button>

      {open && (
        <section className="chat-panel" role="dialog" aria-label={t(messages, "chat.title")}>
          <header className="chat-head">
            <span className="chat-head-id">
              <span className="chat-dot" aria-hidden />
              <strong>{t(messages, "chat.title")}</strong>
            </span>
            <button type="button" className="chat-close" aria-label={t(messages, "chat.close")} onClick={() => setOpen(false)}>
              ✕
            </button>
          </header>

          <div className="chat-log" ref={logRef}>
            {shown.length === 0 && <div className="chat-greeting">{t(messages, "chat.greeting", { assistant: assistantName || "" })}</div>}
            {shown.map((m, i) => (
              <div key={m.id ?? `local-${i}`} className={`chat-msg ${m.role === "visitor" ? "is-visitor" : "is-agent"}`}>
                {m.text}
              </div>
            ))}
            {sending && (
              <div className="chat-msg is-agent chat-typing" aria-label={t(messages, "chat.typing")}>
                <span /><span /><span />
              </div>
            )}
          </div>

          <form
            className="chat-form"
            onSubmit={(e) => {
              e.preventDefault();
              void send();
            }}
          >
            <textarea
              className="chat-input"
              rows={1}
              value={input}
              placeholder={t(messages, "chat.placeholder")}
              aria-label={t(messages, "chat.placeholder")}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  void send();
                }
              }}
            />
            <button type="submit" className="chat-send" disabled={!input.trim() || sending} aria-label={t(messages, "chat.send")}>
              ↑
            </button>
          </form>
        </section>
      )}
    </>
  );
}
