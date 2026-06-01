# 课前预习 · Student Pre-Lecture Prep

> Beginner onboarding for **Homestead** (the website framework). Complete this **before** the lecture so class time goes to building, not account signups and DNS waits.

## 怎么用这份文档

把这个 repo 交给你的 **Codex**，让它读这份文档帮你一起完成。每个步骤都标了角色：

- 🤖 **可以让 Codex 帮你做**：跑命令、验证、通过 `ssh oracle-server` 在服务器上执行。
- 🧑 **必须你本人在浏览器里操作**：买域名、注册账号、Google 控制台点选、生成密码。Codex 只能指导，不能替你点。

> ⏰ **至少提前 3 天开始**，第 1 步（域名）务必最先做——DNS 生效要等几小时到一天。
> 🔒 所有密钥/密码都是私密的：别发群里、别提交到 GitHub。课上私下填进 `.env` 即可。

你应该已经具备：本地装好 **Codex**、能 `ssh oracle-server`、服务器上装了 **OpenClaw** 和 **gws**、有 **DeepSeek API Key**。下面第 0 步会逐项验证。

---

## 第 0 步 · 验证你已有的工具 🤖

把这些交给 Codex 逐条跑（它会通过 `ssh` 在 `oracle-server` 上执行）。

**① SSH + Docker**
```bash
ssh oracle-server "echo OK && docker --version && docker compose version"
```
看到 `OK` + 两个版本号 = 通过。报错就记下来问老师，别自己装。

**② 本地 Codex**
```bash
codex --version
```

**③ DeepSeek Key 有效**（把 `你的KEY` 换成真实 key）
```bash
curl https://api.deepseek.com/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer 你的KEY" \
  -d '{"model":"deepseek-chat","messages":[{"role":"user","content":"ping"}],"max_tokens":5}'
```
返回带 `"content"` 的 JSON = 通过；`401` = key 不对。

**④ OpenClaw** 能在 `oracle-server` 上启动（按你装好的方式确认）。

**⑤ gws（Google Workspace CLI）** —— 在装了 gws 的机器（通常是 `oracle-server`）上：
```bash
gws auth status     # 记下输出里的 project_id（第 2 步要用）
```
- gws 的登录 token 默认会过期。**建议**重新授权一次，这样课堂上 OpenClaw 的 gws 技能（读写邮件/文档等）能用：
  ```bash
  gws auth login      # 按提示在浏览器完成；完成后 status 里 token_valid 应为 true
  ```
  > 在无桌面的服务器上授权遇阻时，让 Codex 协助（SSH 端口转发或设备码方式）。
- 注意：**就算 token 现在是过期的，`gws auth status` 仍能显示 `project_id`**——本预习的第 2 步只需要这个 project_id。

---

## 第 1 步 · 域名 + Cloudflare 🧑（最先做，约 30 分钟 + 等待生效）

**目标**：你拥有一个域名，并且它已挂在你自己的 Cloudflare 账号下、状态是 **Active**。

1. **注册域名**：去 Cloudflare、或 Porkbun / Namecheap。便宜就行（`.xyz`/`.site` 首年常 <¥20，`.com` 约 ¥70/年）。下面用 `你的域名.com` 代指。
2. **注册免费 Cloudflare 账号**：<https://dash.cloudflare.com/sign-up>
3. **把域名加入 Cloudflare**：控制台 **Add a site** → 选 **Free** 套餐 → 如果域名在别处注册，把注册商处的 **nameserver** 改成 Cloudflare 给你的那两个。
4. **验证**（🤖 这步可让 Codex 跑）：等域名状态变 **Active**（会发邮件）。也可命令行查：
   ```bash
   dig +short NS 你的域名.com   # 看到两个 xxx.ns.cloudflare.com = 通过
   ```

> 只需要域名变 **Active**。DNS 记录和 Cloudflare Tunnel **课堂上一起配**。
> 💡 先想好两个网址：主站 `你的域名.com`、后端 `api.你的域名.com`。

---

## 第 2 步 · Google 登录：加一个 Web 客户端 🧑（约 5 分钟）

好消息：**GCP 项目和 OAuth 同意屏幕，gws 已经帮你建好了**。你不用从零建项目，只要在同一个项目里**加一个 Web 客户端**。

1. 拿到第 0 步 ⑤ 里的 `project_id`。
2. 打开 <https://console.cloud.google.com> ，右上角**项目选择器选中那个 `project_id`**。
3. 左侧 **APIs & Services → Credentials → Create Credentials → OAuth client ID**：
   - Application type = **Web application**
   - **Authorized JavaScript origins** 加两条：`https://你的域名.com`、`http://localhost:3000`
   - **Authorized redirect URIs** 加一条备用：`https://你的域名.com`
4. 复制这个新 **Web** 客户端的 **Client ID**（`...apps.googleusercontent.com`）——这就是网站登录用的 `GOOGLE_CLIENT_ID`（前端 `NEXT_PUBLIC_GOOGLE_CLIENT_ID` 用同一个）。
5. 同意屏幕若是 **Testing** 模式：确认要登录的人（至少你自己）在 **Test users** 里；想让任何人都能登录就把它设为 **In production**。

> ⚠️ 别拿 `~/.config/gws/client_secret.json` 里那个 client_id 当登录用——那是 **desktop 类型**（redirect `http://localhost`、无 JS origins），浏览器登录按钮用不了，必须是上面新建的 **Web** 客户端。
> 如果 console 里找不到那个项目 / 没权限：说明你的 gws 用的是共享项目，改走"自己新建项目 + 配同意屏幕 + 建 Web 客户端"的完整流程（问老师拿步骤）。

---

## 第 3 步 · 发邮件：SMTP App Password 🧑（约 15 分钟）

网站发订阅/联系邮件靠 SMTP。最简单是用 **Gmail / Workspace 应用专用密码**（永不过期、网站独立发信、零代码改动）。

1. 在要用来发信的 Google 账号里**开启两步验证**：<https://myaccount.google.com/security>
2. 生成**应用专用密码**：<https://myaccount.google.com/apppasswords> → 得到一串 **16 位密码**。
3. 记录这 5 项：

   | 变量 | 值 |
   |---|---|
   | `SMTP_HOST` | `smtp.gmail.com` |
   | `SMTP_PORT` | `587` |
   | `SMTP_USERNAME` | 你的完整邮箱 |
   | `SMTP_PASSWORD` | 那串 16 位应用专用密码（**不是**登录密码） |
   | `EMAIL_FROM` | 你的完整邮箱 |

> ⚠️ 如果是 **Workspace** 账号且找不到"应用专用密码"入口：需要管理员在 **Admin console → Security** 里允许（你若是自己域名的管理员，自行打开即可）。用个人 Gmail 也完全可以。

---

## 第 4 步 · 想清楚网站做什么 🧑（约 15 分钟，最有意思）

框架是"主题即配置"，提前想好这些，课上你的站立刻有灵魂：

- **行业** `SITE_INDUSTRY`：教育 / 会计 / 餐饮 / 零售 / 房产 / 医疗……
- **受众** `SITE_AUDIENCE`：给谁看（如"温哥华准备留学的高中生家长"）
- **地区** `SITE_REGION`、**网站名** `SITE_NAME`
- **管理员邮箱** `ADMIN_EMAILS`：填你**用来 Google 登录的那个邮箱**，登录后才有后台权限
- **2–3 个同行网址**：课上 AI 会参考它们风格（不抄袭）自动生成你网站的配色/字体/排版

---

## 第 5 步 · 汇总成一张"凭据表"带到课堂 🧑

新建一个**私密**文档填好（不要上传任何公开地方）：

```text
# 我的建站凭据（私密）
域名:               你的域名.com        （Cloudflare 状态 = Active ✅）
DeepSeek API Key:   sk-...
GOOGLE_CLIENT_ID:   ....apps.googleusercontent.com   （Web 类型，第2步新建的）
SMTP_HOST:          smtp.gmail.com
SMTP_PORT:          587
SMTP_USERNAME:      你的邮箱
SMTP_PASSWORD:      16位应用专用密码
EMAIL_FROM:         你的邮箱
ADMIN_EMAILS:       你的登录邮箱
SITE_NAME / 行业 / 受众 / 地区:  ……
参考同行网址:        https://...  https://...
```

> 这些值课堂上会填进 `backend/.env` 和 `frontend/.env.local`（见根目录 `README.md` 的「Required Environment Variables」）。

---

## ✅ 来上课前，确认每一项都能勾上

- [ ] `ssh oracle-server` 能连，服务器有 Docker + Compose
- [ ] 本地 `codex` 能用
- [ ] DeepSeek key 测试返回正常（非 401）
- [ ] OpenClaw 能启动
- [ ] `gws auth status` 能看到 `project_id`（并已 `gws auth login` 让 `token_valid: true`）
- [ ] 域名已注册且 Cloudflare 状态 **Active**
- [ ] 在 gws 的 GCP 项目里加了一个 **Web** 客户端，拿到 `GOOGLE_CLIENT_ID`
- [ ] 备好 SMTP 五项（开了两步验证 + 应用专用密码）
- [ ] 想好行业/受众/网站名 + 2–3 个同行网址
- [ ] 全部填进了那张私密凭据表

---

## ⚠️ 最容易踩的坑

1. **域名没生效就来上课** → 第 1 步最先做。
2. **gws token 失效**（`invalid_rapt`）→ 课前 `gws auth login` 重新授权。
3. **拿 desktop client_id 当登录用** → 登录按钮起不来，必须用第 2 步新建的 **Web** 客户端。
4. **OAuth 同意屏幕没把自己加进 Test users** → 登录被 Google 拒。
5. **找不到应用专用密码入口** → 先开两步验证；Workspace 还要管理员允许。
6. **JS origins 写错** → 必须 `https://`、结尾**别加斜杠** `/`。
7. **把密钥发群里 / 提交 GitHub** → 立刻泄露。
