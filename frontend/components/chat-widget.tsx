"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { t, type Messages } from "@/lib/i18n";
import type { Industry } from "@/lib/api";
import { setPreview, clearPreview } from "./preview-banner";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api";
const ENABLED = (process.env.NEXT_PUBLIC_WEBCHAT_ENABLED || "true") !== "false";
const STORAGE_KEY = "homestead_chat_session";
const POLL_MS = 5000;

type Msg = { id?: number; role: string; text: string };

// Short, friendly labels for the preview chips (the API gives keys + full preset names).
const CHIP: Record<string, { zh: string; en: string; emoji: string }> = {
  beauty: { zh: "美容 / 医美", en: "Beauty", emoji: "💆" },
  education: { zh: "教育", en: "Education", emoji: "📚" },
  restaurant: { zh: "餐厅", en: "Restaurant", emoji: "🍽️" },
  healthcare: { zh: "诊所 / 医疗", en: "Clinic", emoji: "🩺" },
  fitness: { zh: "健身", en: "Fitness", emoji: "🏋️" },
  legal: { zh: "律所", en: "Legal", emoji: "⚖️" },
  realestate: { zh: "房产", en: "Real estate", emoji: "🏠" },
  creative: { zh: "创意工作室", en: "Studio", emoji: "🎨" },
  tech: { zh: "科技 / SaaS", en: "Tech", emoji: "💻" },
  finance: { zh: "金融", en: "Finance", emoji: "📈" },
  nonprofit: { zh: "公益", en: "Nonprofit", emoji: "🤝" }
};
function chipLabel(key: string, name: string, locale: string): string {
  const c = CHIP[key];
  return c ? `${c.emoji} ${locale === "zh" ? c.zh : c.en}` : name;
}

// Typed "switch industry" intent: require a switch verb AND an industry word, so a
// genuine question that merely mentions an industry doesn't trigger a preview.
const SWITCH_INTENT = /换|试|切换|变成|做成|看看|预览|演示|switch|try|show|preview|turn it into|make it|as an?\b/i;
const INDUSTRY_RULES: [RegExp, string][] = [
  [/医美|美容|护肤|spa|beauty|skincare|salon|cosmetic/i, "beauty"],
  [/教育|培训|补习|辅导|tutor|education|school|course|teaching/i, "education"],
  [/餐厅|餐馆|饭店|咖啡|烘焙|cafe|restaurant|food|bakery|dining/i, "restaurant"],
  [/诊所|医疗|医院|牙科|康复|clinic|health|dental|medical|therapy/i, "healthcare"],
  [/健身|健身房|瑜伽|运动|gym|fitness|yoga|sport|trainer/i, "fitness"],
  [/律所|律师|法律|法务|law|legal|attorney|advisory/i, "legal"],
  [/房产|地产|房地产|楼盘|real ?estate|property|realty|architecture/i, "realestate"],
  [/创意|设计|工作室|品牌|agency|studio|creative|design|portfolio/i, "creative"],
  [/科技|软件|互联网|saas|tech|software|startup/i, "tech"],
  [/金融|理财|财富|投资|银行|finance|wealth|invest/i, "finance"],
  [/公益|非营利|慈善|基金会|nonprofit|charity|ngo/i, "nonprofit"]
];
function detectSwitch(text: string): string {
  if (!SWITCH_INTENT.test(text)) return "";
  for (const [re, key] of INDUSTRY_RULES) if (re.test(text)) return key;
  return "";
}

export function ChatWidget({
  locale,
  messages,
  assistantName,
  demoPreview,
  industries = [],
  previewing
}: {
  locale: string;
  messages: Messages;
  assistantName?: string;
  demoPreview?: boolean;
  industries?: Industry[];
  previewing?: boolean;
}) {
  const router = useRouter();
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

  useEffect(() => {
    if (open && sessionId) fetchHistory(sessionId);
  }, [open, sessionId, fetchHistory]);

  useEffect(() => {
    if (!open || !sessionId) return;
    const id = window.setInterval(() => {
      if (!sendingRef.current) fetchHistory(sessionId);
    }, POLL_MS);
    return () => window.clearInterval(id);
  }, [open, sessionId, fetchHistory]);

  useEffect(() => {
    const el = logRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [server, pending, sending, open]);

  // Apply a per-visitor industry preview: set the cookie, drop a confirmation note,
  // and refresh the (server-rendered) page so it re-renders as that industry.
  const applyPreview = useCallback(
    (key: string) => {
      setPreview(key);
      const label = chipLabel(key, industries.find((i) => i.key === key)?.name || key, locale);
      setServer((s) => [...s, { role: "agent", text: t(messages, "preview.switched", { label }) }]);
      router.refresh();
    },
    [industries, locale, messages, router]
  );

  const resetPreview = useCallback(() => {
    clearPreview();
    router.refresh();
  }, [router]);

  const send = useCallback(async () => {
    const text = input.trim();
    if (!text || sendingRef.current) return;
    // Demo: "show me a restaurant / 换成餐厅" previews that industry instead of chatting.
    const switched = demoPreview ? detectSwitch(text) : "";
    if (switched) {
      setInput("");
      applyPreview(switched);
      return;
    }
    setInput("");
    setPending(text);
    setSending(true);
    sendingRef.current = true;
    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sessionId: sessionId || undefined, message: text, locale, page: window.location?.pathname })
      });
      if (res.status === 429) {
        setServer((s) => [...s, { role: "agent", text: t(messages, "chat.rateLimited") }]);
      } else if (res.ok) {
        const data = await res.json();
        const sid: string = data?.item?.sessionId || sessionId;
        if (sid && sid !== sessionId) {
          setSessionId(sid);
          try {
            window.localStorage.setItem(STORAGE_KEY, sid);
          } catch {
            /* ignore */
          }
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
  }, [input, sessionId, locale, messages, fetchHistory, demoPreview, applyPreview]);

  if (!ENABLED) return null;

  const shown: Msg[] = [...server];
  if (pending) shown.push({ role: "visitor", text: pending });
  const showChips = !!demoPreview && industries.length > 0;

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

            {showChips && (
              <div className="chat-tryrow">
                <span className="chat-tryrow-label">{t(messages, "chat.tryIndustries")}</span>
                <div className="chat-chips">
                  {industries.map((ind) => (
                    <button key={ind.key} type="button" className="chat-chip" onClick={() => applyPreview(ind.key)}>
                      {chipLabel(ind.key, ind.name, locale)}
                    </button>
                  ))}
                  {previewing && (
                    <button type="button" className="chat-chip chat-chip-reset" onClick={resetPreview}>
                      ↩︎ {t(messages, "preview.reset")}
                    </button>
                  )}
                </div>
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
