# Documentation index — by reader

Homestead is a $100 website for local small businesses (Next.js + Flask + Postgres),
operated over chat/API. This index groups the docs by **who you are**. Each row notes
the language (`en`/`zh`) and a one-line purpose.

> Not sure where to start? Buyers/agents read [`../README.md`](../README.md) first;
> deploy agents read [`../AGENT-DEPLOY.md`](../AGENT-DEPLOY.md) first; developers read
> [`DEVELOPMENT.md`](DEVELOPMENT.md) first.

## Buyer / agent (you bought a site, or you're selling/delivering one)

| Doc | Lang | What it's for |
| --- | --- | --- |
| [`../README.md`](../README.md) | en | Product overview: what Homestead is, what you get for $100, how it works. |
| [`runbook-client-delivery.md`](runbook-client-delivery.md) | en | End-to-end delivery runbook: take a raw instance to a finished client site. |
| Gallery | — | Screenshots / live examples of finished sites. **Planned — not yet in the repo.** |

## Business owner (you own the site day-to-day)

| Doc | Lang | What it's for |
| --- | --- | --- |
| [`owner-manual.zh.md`](owner-manual.zh.md) | zh | 店主手册：用聊天改文案、换图、发博客、看站点。**本批在建。** |
| [`webchat-for-owners.zh.md`](webchat-for-owners.zh.md) | zh | 在线客服桥：访客消息如何镜像到 Telegram，一句话接管对话。**本批在建。** |

## Deploy / operations agent (you stand up and run instances)

| Doc | Lang | What it's for |
| --- | --- | --- |
| [`../AGENT-DEPLOY.md`](../AGENT-DEPLOY.md) | en | Headless deploy runbook (TL;DR up top). Driven by `ops/agent/deploy.sh`. |
| [`telegram-agent-setup.md`](telegram-agent-setup.md) | en | Wire the OpenClaw agent to a Telegram bot so the site is managed from a phone. |
| [`multi-instance.md`](multi-instance.md) | zh | Run N client instances on one host: one clone dir per client, no shared DB. |
| [`getting-started.zh.md`](getting-started.zh.md) | zh | 灌客户内容 5 步走：换行业 → 换图 → 改文案 → 双语 → 一致性验收。 |
| [`deployment.md`](deployment.md) | en | Docker Compose deployment guide for this instance. |
| [`deploy-new-instance.md`](deploy-new-instance.md) | en | Stand up a fresh, fully independent Homestead on a new server. |

## Developer (you change the code)

| Doc | Lang | What it's for |
| --- | --- | --- |
| [`DEVELOPMENT.md`](DEVELOPMENT.md) | en | Full engineering reference: architecture, local dev, env vars, self-checks. |
| [`api-contract.md`](api-contract.md) | en | The JSON API surface (resources grouped by domain, kept small and stable). |
| [`REFERENCE.zh.md`](REFERENCE.zh.md) | zh | 系统参考总览：「Elementor，但用 Telegram 聊天操作」的分类地图。 |
| [`design-system.md`](design-system.md) | en | Design system & section composition spec (themes, CSS variables, blocks). |
| [`capture-and-i18n.md`](capture-and-i18n.md) | en | Architecture of content capture and bilingual (i18n) generation. |
| [`openclaw-maintenance.md`](openclaw-maintenance.md) | en | Maintenance boundaries to respect when evolving the project. |
| [`openclaw-competitor-analyzer.md`](openclaw-competitor-analyzer.md) | en | Workflow for an agent with browser access to analyze competitor sites. |

## Teaching material (historical)

Classroom material from earlier lectures. Kept for reference; not part of the delivery
or ops flow.

| Doc | Lang | What it's for |
| --- | --- | --- |
| [`lecture-outline.md`](lecture-outline.md) | en | Lecture outline: the server as the student's personal internet home. |
| [`student-prep.md`](student-prep.md) | en/zh | Pre-lecture setup (accounts, DNS) so class time goes to building. |
