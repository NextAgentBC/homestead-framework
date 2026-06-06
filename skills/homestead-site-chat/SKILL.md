---
name: homestead-site-chat
description: "Review website live-chat conversations and take over a thread — reply to a website visitor as the site assistant. The site has an AI chat widget that the assistant answers automatically; threads waiting for a human show in the take-over inbox (GET /admin/chat?status=open&awaiting=1) — or your Telegram if configured. Use this when you want to step in. Triggers: '回复网站访客 / 替我回他', '接管这个聊天', '看看网站的聊天 / 网站客服消息', 'reply to the website visitor', 'show website chats', '关闭这个会话'."
metadata:
  version: 0.1.0
  openclaw:
    category: "website"
    requires:
      bins:
        - curl
---

# Homestead — Website live chat (operator console + take-over)

> Prerequisite: `../homestead-site-shared/SKILL.md` for `$HOMESTEAD_SITE_API` + `$HOMESTEAD_SITE_TOKEN`.

The website has a floating chat widget. If the optional live-chat bridge is configured,
visitors are answered automatically by a sandboxed, tool-less assistant brain (a one-shot
model turn on the host `webchat-bridge`); if it isn't, the widget still captures every
message for a human to answer. **Either way you can take over any thread** — your reply
lands in the visitor's widget within ~5 seconds (it polls) and becomes context for the AI.

Find threads waiting for a human two ways:

- **Poll the inbox** (works with no Telegram): `GET /admin/chat?status=open&awaiting=1`
  returns only threads **no human operator has answered yet** — the visitor's message, or one
  the AI / auto-fallback replied to (with the bridge off, that's every visitor message). This is
  the reliable way for an OpenClaw/agent loop to pick up and reply.
- **Telegram** (optional): if you set `WEBCHAT_TG_TARGET`, each exchange is mirrored there
  and ends with `↩️ 接管回复用 session：web_xxxx` — that `session` is the id to reply to.

## Review (admin token)

```bash
# 📥 Take-over inbox — threads no human has answered yet (visitor's, or only AI/fallback replied):
curl -s "$HOMESTEAD_SITE_API/admin/chat?status=open&awaiting=1" -H "Authorization: Bearer $HOMESTEAD_SITE_TOKEN"

# All open conversations, newest activity first (cards: sessionId, last message, email…)
curl -s "$HOMESTEAD_SITE_API/admin/chat?status=open" -H "Authorization: Bearer $HOMESTEAD_SITE_TOKEN"

# Full transcript of one thread (messages: role visitor|agent|operator)
curl -s "$HOMESTEAD_SITE_API/admin/chat/<session>" -H "Authorization: Bearer $HOMESTEAD_SITE_TOKEN"
```

## Take over — reply as a human / the assistant

```bash
# Push a reply into the visitor's widget (role defaults to "operator")
curl -s -X POST "$HOMESTEAD_SITE_API/admin/chat/<session>/reply" \
  -H "Authorization: Bearer $HOMESTEAD_SITE_TOKEN" -H "Content-Type: application/json" \
  -d '{"message": "你好！周一上午我们有空，方便的话留个电话我们联系你 🙂"}'
```

- Find `<session>` from the `接管回复用 session：…` line in the Telegram mirror, or from the
  list above (match the visitor's last message). The 8-char prefix shown elsewhere is not enough.
- After you reply, the AI won't auto-answer that turn (it only answers when the **visitor** sends);
  your message simply appears, and the assistant sees it as context next time the visitor writes.

## Close / reopen

```bash
curl -s -X POST "$HOMESTEAD_SITE_API/admin/chat/<session>/close" \
  -H "Authorization: Bearer $HOMESTEAD_SITE_TOKEN" -H "Content-Type: application/json" -d '{}'
# reopen: add -d '{"reopen": true}'
```

Notes:
- You don't need to do anything for normal Q&A — the widget AI handles it. This skill is only
  for when you want to step in, or to review what visitors are asking.
- The contact form also pings you on Telegram (📨 网站留言) with the visitor's email — reply by
  email, not here (that's a one-shot form, not a live chat thread).
