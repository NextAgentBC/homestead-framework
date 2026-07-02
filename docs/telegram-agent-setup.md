# 用手机聊天管网站:从零搭链路 · Manage your site by chatting on your phone (from scratch)

> 目标:让店主 / 运营者用 **Telegram 发一句话**就能改网站——换首页标题、发博客、换模板、翻译成中文。
> 本文把这条链路**从零**讲清:装什么、怎么装、怎么安全交付、怎么冒烟验证。
>
> 前提:你已经用 [`AGENT-DEPLOY.md`](../AGENT-DEPLOY.md) 部署好至少一个 Homestead 实例(能打开
> `https://your-site.example.com`,`GET https://your-api.example.com/api/health` 返回 `ok`)。
> 本文只讲**「手机聊天层」**,不重复部署本身。

本文中英双语,标题双语,正文以中文为主。术语第一次出现给出英文对照。

---

## 1. 这条链路由三个部件组成 · The three moving parts

```
店主/运营者 ── Telegram bot ── OpenClaw agent(宿主机) ── Homestead 实例(已部署)
 operator      前门/入口          运行技能的大脑              网站的后端 API
              (BotFather 建)     (装在 server 上)          (docker compose)
```

1. **Homestead 实例(已部署)** — 你的网站。所有改动最终都是调它的 HTTP API
   (`$HOMESTEAD_SITE_API`,即 `https://your-api.example.com/api`)。见 `skills/homestead-site-shared/SKILL.md`。
2. **OpenClaw agent(宿主机 host)** — 跑在服务器上的 agent 运行时(gateway)。它把
   `skills/` 里的每个技能**自动暴露成一个 Telegram 斜杠命令**,并在收到消息时读技能、调 Homestead API。
3. **Telegram bot(入口)** — 店主/运营者在手机上用的那个 bot,用 BotFather 创建、拿 token,
   绑定到 OpenClaw gateway。

**另有一条独立的链路:在线客服桥(webchat-bridge)。** 方向相反——是**网站访客**在网页聊天框里说话,
镜像到**运营者的 Telegram**,运营者可以一句话接管回复。它跟上面的「管网站」链路是两回事,详见 §3-⑤ 和
`ops/webchat-bridge/README.md`。

```
访客 → 网页聊天框 → backend /api/chat → webchat-bridge(宿主) → 镜像到运营者 Telegram
visitor            (无工具沙箱回复)                            (可接管)
```

---

## 2. 三种交付形态怎么选 · Delivery models (决策表)

这是买家最先要拍板的事:**这个 bot 到底谁来管、管几个站。**

| 形态 | 谁在跑 OpenClaw | 一个 bot 管几个站 | 成本 | 隔离性 | 谁有权限 | 适合谁 |
|---|---|---|---|---|---|---|
| **A. 运营者代管**(推荐 $100 档) | 运营者自己的一台服务器 | **一个 bot 管多个客户站** | 最低(一份 gateway 摊到多个客户) | 靠命令区分实例(见下方多实例说明);买家**不碰**服务器 | 只有运营者 | 卖 $100 站给一堆小生意、集中代运营 |
| **B. 客户进共享 bot** | 运营者的服务器 | 一个 bot,客户也在群里 | 低 | 弱——同一 bot 里多个客户,得靠对话纪律/群隔离 | 运营者 + 该客户(受限技能) | 想让客户自己也能改点文案、但你仍托底 |
| **C. 每客户独立 bot** | 每个客户一台(或一份)gateway | 一个 bot 只管自己那个站 | 最高(每客户一份 gateway + token) | 最强——进程/服务器级隔离 | 该客户 | 客户要完全自主、数据强隔离、或愿意多付钱 |

要点:
- **$100 网站的默认答案是 A**:运营者一台服务器、一个 bot,用 [`docs/multi-instance.md`](./multi-instance.md)
  的约定同机跑多个客户实例(每客户一个独立 clone 目录 / 独立数据库 / 独立 `$HOMESTEAD_SITE_API`)。
  切换「现在管哪个站」= 切 `HOMESTEAD_SITE_API` / `HOMESTEAD_SITE_TOKEN` 指向哪个实例。
- **无论哪种形态,买家/店主都不该拿到服务器 shell 权限**(§4 安全边界)。
- **形态 C 也不等于把服务器交给客户**——仍由懂运维的人装 gateway;客户只用 Telegram。

---

## 3. 从零搭建步骤 · Step-by-step

以下步骤在**宿主机(host)**上做,不在容器里。假设 Homestead 实例已部署在同一台机器。

### ① 在服务器装 OpenClaw gateway

> ⚠️ **本仓库不含 OpenClaw 的安装脚本。** OpenClaw 是独立项目,安装/升级请**以 OpenClaw 官方文档为准**。
> 本仓库只提供**装好之后**如何接 Homestead 的部分(技能安装、token、bridge)。

装完后你应当具备:
- `openclaw` CLI 可用(`openclaw --version` 能跑)。
- 一个作为 **user service** 运行、开机自启的 gateway(本仓库其它文档按
  `systemctl --user restart openclaw-gateway` 这个惯例引用它;实际服务名以你的安装为准)。
- gateway 常驻需要 **linger**(否则退出 SSH 后服务被杀):`loginctl enable-linger <你的用户>`
  (与 webchat-bridge 同一要求,见 `ops/webchat-bridge/README.md`)。

安装命令、gateway 配置、模型/密钥设置一律见 **OpenClaw 官方文档**,不要照抄别处臆造的命令。

### ② 用 BotFather 建 Telegram bot、拿 token、绑定

在 Telegram 里:
1. 找 **@BotFather** → `/newbot` → 起名字 → 拿到 **bot token**(形如 `123456:ABC-...`)。
2. 把这个 token 配给 OpenClaw gateway 作为 Telegram 入口(**具体配置项/字段以 OpenClaw 官方文档为准**)。
3. 绑定你要接收命令的 channel / chat(私聊或群)。
4. (可选)`/setcommands` 给 bot 设置命令菜单——不过 OpenClaw 会**自动**把每个已装技能暴露成命令,
   通常不必手工维护。

> 想知道自己的 chat id(形态 B/C 或 bridge 镜像会用到):给 bot 发条消息后,用 OpenClaw 侧的
> 消息日志 / 官方文档给出的方式读取。

### ③ 安装 Homestead 技能(显式白名单,**排除 homestead-site-ops**)

技能都在本仓库 `skills/` 下,是对 Homestead HTTP API 的封装。OpenClaw **把每个已装技能自动变成一个
Telegram 斜杠命令**(`homestead-site-blog` → `/homestead_site_blog`,`website` → `/website`)。

**绝对不要给买家/店主装 `homestead-site-ops`。** 它要在服务器上跑 `docker compose`(redeploy / restart /
看日志),需要**服务器 shell 权限**——只能运营者自己用,不能进交付给客户的 bot。见其 SKILL:
`skills/homestead-site-ops/SKILL.md`(`requires.bins: docker`)。

**推荐的白名单(店主/运营者日常够用,全部只调 HTTP API、无需服务器权限):**

| 技能 | 命令 | 作用 |
|---|---|---|
| `website` | `/website` | 分类命令菜单(前门),路由到下面各技能 |
| `homestead-site-shared` | — | 基础/鉴权约定,**先读**(不是命令) |
| `homestead-site-blog` | `/homestead_site_blog` | 写/生成/发布/改博客 |
| `homestead-site-pages` | `/homestead_site_pages` | 新建/改页面(关于、服务、隐私…) |
| `homestead-site-design` | `/homestead_site_design` | 换模板(18 套)/配色/字体/hero |
| `homestead-site-rebrand` | `/homestead_site_rebrand` | 一键切整站行业 + 一致性审计循环 |
| `homestead-site-compose` | `/homestead_site_compose` | 给某页加/改/移/删板块 |
| `homestead-site-capture` | `/homestead_site_capture` | 发截图 → 重建成板块 |
| `homestead-site-i18n` | `/homestead_site_i18n` | 翻译内容 + UI(路径式 `/zh`) |
| `homestead-site-media` | `/homestead_site_media` | 上传图片 → 用到图库/团队/博客 |
| `homestead-site-newsletter` | `/homestead_site_newsletter` | 订阅者 / 联系表单 |
| `homestead-site-history` | `/homestead_site_history` | 撤销/回上一版/改动历史 |
| `homestead-site-chat` | `/homestead_site_chat` | 网站在线聊天:看会话、接管回复 |

安装方式见 `skills/README.md`(仓库是唯一真源,`install` 把技能**复制**进
`~/.openclaw/workspace/skills/`;OpenClaw **拒绝逃逸 skills 根的 symlink**,所以要装成真实目录)。
显式白名单式安装——**逐个列出要装的技能,不要 `for` 全装**,这样天然把 `homestead-site-ops` 排除掉:

```bash
cd /path/to/homestead-framework
for name in website homestead-site-shared homestead-site-blog homestead-site-pages \
            homestead-site-design homestead-site-rebrand homestead-site-compose \
            homestead-site-capture homestead-site-i18n homestead-site-media \
            homestead-site-newsletter homestead-site-history homestead-site-chat; do
  openclaw skills install "skills/$name" --force
done
openclaw skills check                       # 每个应显示 "ready"
systemctl --user restart openclaw-gateway   # gateway 启动时快照技能,装完要重启
```

> 说明:
> - **不要**装 `skills/homestead-site-ops`(需要服务器 shell,只给运营者)。
> - 每块 block 的 `homestead-site-block-*` 是**可选**的触发技能——`compose`/`capture` 已覆盖所有 block
>   类型,默认跳过以保持命令菜单干净(见 `skills/README.md`)。
> - 编辑过技能后要 `--force` 重装再重启 gateway。

### ④ 指向该实例的 API + 铸长效 admin token

技能靠两个环境变量找到并写入网站(见 `skills/homestead-site-shared/SKILL.md`):

- `HOMESTEAD_SITE_API` — 该实例的 API 基址,**带 `/api`**,如 `https://your-api.example.com/api`。
- `HOMESTEAD_SITE_TOKEN` — admin bearer token(写操作必需;只读/公开路由不需要)。

**非交互铸 token(agent 无浏览器):在 backend 所在处跑** `flask ... token issue`。它用后端配置的
`ADMIN_EMAILS` 第一个(即管理员),最稳:

```bash
export HOMESTEAD_SITE_API="https://your-api.example.com/api"

# 在部署目录里,用 backend 容器铸一个长效 token(--days 覆盖默认 168h,如给 365 天)
export HOMESTEAD_SITE_TOKEN="$(docker compose exec -T backend \
  flask --app app.main token issue --days 365)"
```

要点(均来自 `homestead-site-shared/SKILL.md`):
- **不带 `--email`** 就用管理员那条,最稳;只有当 `<x>` 确实在后端 `ADMIN_EMAILS` 里才用 `--email <x>`。
- `--days N` 覆盖有效期(默认 168 小时 = 7 天),给长效交付可给较大值(注意越长泄露风险越大,见 §4)。
- **形态 A(一 bot 多站)**:每个客户实例一套 `HOMESTEAD_SITE_API` + `HOMESTEAD_SITE_TOKEN`;
  切换「现在管哪个站」就是切这两个变量指向对应实例。多实例约定见 `docs/multi-instance.md`。

### ⑤ (可选)启用在线客服桥 webchat-bridge

这条是**另一方向**:网站访客在网页聊天框说话 → 镜像到**运营者 Telegram** → 运营者可一句话接管。
它是宿主机上一个 stdlib-only 的小 HTTP 服务,由 backend 容器通过 `host.docker.internal:18791` 调用。

安装、systemd、Oracle 防火墙放行、`.env` 字段(`WEBCHAT_BRIDGE_TOKEN` 必须与
`backend/.env` 一致、`WEBCHAT_TG_TARGET` = 运营者 chat id 等)**全部见**
[`ops/webchat-bridge/README.md`](../ops/webchat-bridge/README.md),此处不重复。

> 桥的聊天大脑用的是 `openclaw infer model run` ——**一次性模型补全,不是 agent harness,没有任何工具面**
> (无 shell、无文件、无发消息、无技能)。见 §4。

---

## 4. 安全边界 · Security boundaries

这套东西默认是**可以安全交付给不懂技术的店主**的,前提是守住下面几条线:

1. **聊天大脑无工具、防注入(仅指访客侧的 webchat-bridge)。**
   访客侧的对话跑在 `openclaw infer model run`——**一次性模型补全,没有工具面**:没有 shell、没有文件访问、
   不能发消息、不接技能。访客随便输入,最坏也只是模型吐一段文本。喂给它的 prompt 由 backend 组装,**只含
   公开站点知识 + 该访客自己的对话**,永不含私有记忆或文件。端口不对公网开放。(见 `ops/webchat-bridge/README.md`)

2. **店主能改内容,不能碰服务器。**
   给买家/店主的 bot **只装内容/设计/翻译/媒体类技能**(§3-③ 白名单),**绝不装 `homestead-site-ops`**——
   它是唯一需要服务器 shell(`docker`)的技能。这样店主能改标题、发博客、换模板,但碰不到部署、日志、容器。
   redeploy / restart / 看日志一律由运营者用自己的 ops 通道做。

3. **token 泄露怎么轮换。**
   `HOMESTEAD_SITE_TOKEN` 是长效 admin JWT,泄露 = 别人能改你的站。轮换很简单——**重新铸一个新 token,
   把 gateway 环境里的旧值替换掉、重启 gateway 即可**:

   ```bash
   export HOMESTEAD_SITE_TOKEN="$(docker compose exec -T backend \
     flask --app app.main token issue --days 365)"     # 铸新的,覆盖旧的
   systemctl --user restart openclaw-gateway            # 让 gateway 用上新值
   ```

   - 交付时倾向**较短有效期 + 到期再铸**,而不是一发一个几年不换的 token。
   - `WEBCHAT_BRIDGE_TOKEN`(桥)同理:改 `ops/webchat-bridge/.env` 与 `backend/.env`(两处必须一致),
     重启 bridge 与 backend。
   - 只读/公开路由(`/site`、`/health`、`/blogs`…)本就不需要 token,验证链路可先用它们。

---

## 5. 冒烟测试 · Smoke test

链路通不通,发一句话就知道。

**前置(可选)自检**,先确认 API 和 token 就绪:

```bash
curl -s "$HOMESTEAD_SITE_API/health"        # 期望 {"database":"ok","status":"ok"}
curl -s "$HOMESTEAD_SITE_API/site"          # 期望回站点信息(name/industry/url…)
```

**真正的端到端测试:在 Telegram 里对 bot 说一句话。**

1. 给 bot 发:**「把首页标题改成 X」**(或英文 `change the homepage title to X`)。
   - `/website` 会路由,或直接触发 `homestead-site-compose` / `homestead-site-design`。
2. 期望:bot 回一句「已改」之类的确认(edits 是**即时的,无需重新部署**)。
3. **在浏览器打开** `https://your-site.example.com`,刷新,确认首页标题真的变成了 X。

通过 = 三个部件(Telegram bot → OpenClaw gateway → Homestead API)已经打通。
如果 bot 无反应,顺序排查:gateway 是否在跑(`openclaw skills check`、gateway 服务状态)→ Telegram token/绑定 →
`HOMESTEAD_SITE_API` / `HOMESTEAD_SITE_TOKEN` 是否正确、token 是否过期(重铸,见 §4)。

---

## 相关文档 · See also

- [`AGENT-DEPLOY.md`](../AGENT-DEPLOY.md) — 从零无头部署一个 Homestead 实例(本文的前提)。
- [`docs/multi-instance.md`](./multi-instance.md) — 同一台机器跑多个客户实例(形态 A 的基础)。
- [`skills/README.md`](../skills/README.md) — 技能清单、安装/激活方式(唯一真源)。
- [`skills/homestead-site-shared/SKILL.md`](../skills/homestead-site-shared/SKILL.md) — API 基址、鉴权、token 铸法(先读)。
- [`ops/webchat-bridge/README.md`](../ops/webchat-bridge/README.md) — 在线客服桥的安装与配置。
- **OpenClaw 官方文档** — gateway 安装、Telegram 入口配置、模型/密钥(本仓库不含,以官方为准)。
