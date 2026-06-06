---
name: homestead-site-newsletter
description: "Homestead audience capture over its API: newsletter subscribe + contact form (public). Triggers: '订阅 / 加订阅者 / subscribe', '订阅 newsletter', '提交联系表单 / 联系我们 / contact form', '加个订阅'."
metadata:
  version: 0.1.0
  openclaw:
    category: "website"
    requires:
      bins:
        - curl
---

# Homestead — Newsletter & Contact

> Prerequisite: read `../homestead-site-shared/SKILL.md` for `$HOMESTEAD_SITE_API`.

Both endpoints are public (no token).

```bash
# Subscribe an email to the newsletter (name optional)
curl -s -X POST "$HOMESTEAD_SITE_API/newsletter/subscribe" \
  -H "Content-Type: application/json" \
  -d '{"email": "reader@example.com", "name": "Reader"}'

# Submit a contact-form message (email + message required)
curl -s -X POST "$HOMESTEAD_SITE_API/contact" \
  -H "Content-Type: application/json" \
  -d '{"email": "reader@example.com", "message": "Hello, I have a question."}'
```

Delivery uses the backend's SMTP settings (`SMTP_*`, `EMAIL_FROM`). If SMTP is unset, submissions are still recorded but no email is sent.
