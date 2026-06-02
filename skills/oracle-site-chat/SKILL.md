---
name: oracle-site-chat
description: "Review website live-chat conversations and take over a thread — reply to a website visitor as 小爪. The site has an AI chat widget that 小爪 answers automatically; each visitor exchange is mirrored to your Telegram. Use this when you want to step in. Triggers: '回复网站访客 / 替我回他', '接管这个聊天', '看看网站的聊天 / 网站客服消息', 'reply to the website visitor', 'show website chats', '关闭这个会话'."
metadata:
  version: 0.1.0
  openclaw:
    category: "website"
    requires:
      bins:
        - curl
---

# Oracle Site — Website live chat (operator console + take-over)

> Prerequisite: `../oracle-site-shared/SKILL.md` for `$ORACLE_SITE_API` + `$ORACLE_SITE_TOKEN`.

The website has a floating chat widget. Visitors are answered **automatically** by the
sandboxed, tool-less 小爪 brain (a one-shot model turn on the host `webchat-bridge`).
Every visitor↔小爪 exchange is **mirrored to your Telegram**, and each mirror ends with:

```
↩️ 接管回复用 session：web_xxxxxxxxxxxx
```

That `session` is what you pass below to **take over** — your reply lands in the visitor's
chat widget within ~5 seconds and is included in the AI's future context for that thread.

## Review (admin token)

```bash
# Open conversations, newest activity first (cards: sessionId, last message, email…)
curl -s "$ORACLE_SITE_API/admin/chat?status=open" -H "Authorization: Bearer $ORACLE_SITE_TOKEN"

# Full transcript of one thread (messages: role visitor|agent|operator)
curl -s "$ORACLE_SITE_API/admin/chat/<session>" -H "Authorization: Bearer $ORACLE_SITE_TOKEN"
```

## Take over — reply as a human/小爪

```bash
# Push a reply into the visitor's widget (role defaults to "operator")
curl -s -X POST "$ORACLE_SITE_API/admin/chat/<session>/reply" \
  -H "Authorization: Bearer $ORACLE_SITE_TOKEN" -H "Content-Type: application/json" \
  -d '{"message": "你好！周一上午我们有空，方便的话留个电话我们联系你 🙂"}'
```

- Find `<session>` from the `接管回复用 session：…` line in the Telegram mirror, or from the
  list above (match the visitor's last message). The 8-char prefix shown elsewhere is not enough.
- After you reply, the AI won't auto-answer that turn (it only answers when the **visitor** sends);
  your message simply appears, and 小爪 sees it as context next time the visitor writes.

## Close / reopen

```bash
curl -s -X POST "$ORACLE_SITE_API/admin/chat/<session>/close" \
  -H "Authorization: Bearer $ORACLE_SITE_TOKEN" -H "Content-Type: application/json" -d '{}'
# reopen: add -d '{"reopen": true}'
```

Notes:
- You don't need to do anything for normal Q&A — the widget AI handles it. This skill is only
  for when Yao wants to step in, or to review what visitors are asking.
- The contact form also pings you on Telegram (📨 网站留言) with the visitor's email — reply by
  email, not here (that's a one-shot form, not a live chat thread).
