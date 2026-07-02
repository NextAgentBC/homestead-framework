# 从签单到交付的计时操作清单（$100 一单怎么赚）

> **一句话定位**：这是把一个付费客户的 Homestead 站从零部署、灌真实内容、验收发布、交接店主的**逐步计时清单**——既是「$100 能不能赚」的操作证明，也是新代理的培训教材。照着做，不用即兴发挥。

**交付这一单大约要多久**（基于本仓库真实步骤，非承诺）：

| 场景 | 时间区间 | 主要耗时 |
|---|---|---|
| **首站**（第一次给某行业交付） | **30–45 分钟** | `deploy.sh` 构建 + 隧道 + DNS（约 8–15 分钟）、改文案换图（10–20 分钟）、一致性修到全绿（5–10 分钟） |
| **同行业第 2 站起** | **15–25 分钟** | 行业模板熟了、文案有存货、只需换 NAP/店名/照片 |
| **纯换文案不换行业**（复购/改版） | **10 分钟** | 跳过部署，直接 `PATCH settings` + 改 block + 验收 |

时间大头是：① `next build` 前端构建（低配 VM 会更慢，见[常见坑](#常见坑)）；② DNS 传播（隧道后 ~30–60 秒）；③ 把占位图换成客户真图。**部署本身是一条命令**，人工时间几乎都花在内容上。

前置阅读（命令以这些为准）：无头部署总纲 [`../AGENT-DEPLOY.md`](../AGENT-DEPLOY.md)、部署脚本 `ops/agent/deploy.sh`、灌内容 5 步 [`getting-started.zh.md`](getting-started.zh.md)、多实例约定 [`multi-instance.md`](multi-instance.md)。

---

## 0. 签单当场：客户信息表（intake）

**开工前一次性收齐**，缺哪项当场问客户，别开工到一半回头催。复制下面这段，逐行填：

```
【Homestead 客户信息表】
店名 / 品牌名(brandName)：
行业(industry)：            # 例 construction / restaurant / beauty / legal / fitness …
                          #   家政·上门·清洗类都归 construction（别名含 pressure-washing / plumbing /
                          #   electrician / hvac / roofing / window-cleaning / landscaping …）
目标客户(audience)：        # 例「大温地区独立屋业主」
服务城市(serviceAreas)：    # 例 Surrey / Vancouver / Burnaby（可多个）

—— NAP（法定名/电话/地址/营业时间，逐字核对，交付后要一字不差）——
legalName（工商注册名）：
phone：
email：
addressStreet / City / Region / PostalCode / Country：
latitude / longitude（可选，有则填数字）：
businessHours（营业时间）：  # 例 周一到周五 09:00–18:00，周六 10:00–16:00
                           #   数据格式：{days:[...], opens:"09:00", closes:"18:00"}，days 用 Mo/Tu/We/Th/Fr/Sa/Su

—— 素材 ——
logo：                      # 有/无（无就先用占位）
照片：                      # 几张、什么内容（hero 大图 / 作品 before-after / 团队 / 门面）
是否要双语(en + zh)：       # 是/否

—— 域名 & 交接 ——
SITE_DOMAIN（站点域名）：    # 例 acme.example.com
API_DOMAIN（API 域名）：     # 例 acme-api.example.com
域名所在 Cloudflare 账号：   # 必须是你 CF token 能管的 zone
店主 Telegram（用于手机管理/接管客服）：
收款方式 & 金额：
```

> NAP 没有 env 兜底，留空即「未设」。营业时间/服务城市是列表；经纬度是数字或 null。这些字段名与 `PATCH /admin/site/settings` 一一对应（见第 3 步）。

---

## 逐步骤操作（命令 + 预期结果 + 时间预算）

> 约定：`$HOMESTEAD_SITE_API` = `https://$API_DOMAIN/api`；`$TOKEN` = admin token。多实例同主机部署请全程带 `INSTANCE_NAME`（见第 1 步）。

### ① 确定实例名与端口（多实例）— 约 2 分钟

一台主机跑多个客户站时，**每客户一个独立 clone 目录**，目录名 = `INSTANCE_NAME` = compose project 名。端口从 13000/18000 起、每实例 +10，登记好别撞（详见 [`multi-instance.md`](multi-instance.md)）。

```bash
git clone https://github.com/NextAgentBC/homestead-framework.git homestead-acme
cd homestead-acme
export INSTANCE_NAME=homestead-acme            # 与目录名一致
export FRONTEND_PORT=13010 BACKEND_PORT=18010 POSTGRES_PORT=55444   # 查表分配，勿撞
```

- **预期**：进入该客户专属目录；三个端口变量已 export，稍后 `make-env.sh` 会写进本目录 `.env`。
- 只交付**一个**站、这台机没别的实例？可跳过 `INSTANCE_NAME`，退回单实例默认（`homestead-site-*` 别名、默认端口 3000/8000/55433）。

### ② `deploy.sh` 一键部署（含隧道）— 约 8–15 分钟

`deploy.sh` 幂等地跑完 preflight → make-env → edge 网络 → build → 健康检查 → 铸 admin token → 可选 preset → Cloudflare 隧道 → verify。失败修完**直接重跑**即可。

```bash
export SITE_DOMAIN=acme.example.com API_DOMAIN=acme-api.example.com ADMIN_EMAIL=you@example.com
export CF_API_TOKEN=…  CF_ACCOUNT_ID=…          # 建隧道必需；无隧道用 --skip-tunnel
export SITE_INDUSTRY=construction               # 客户行业，首启即 seed 对的模板（可选，也可稍后 rebrand）
bash ops/agent/deploy.sh                        # 自定 ingress 时用：bash ops/agent/deploy.sh --skip-tunnel
```

- **必需 env**：`SITE_DOMAIN` / `API_DOMAIN` / `ADMIN_EMAIL`；建隧道还需 `CF_API_TOKEN` / `CF_ACCOUNT_ID`。域名必须是该 CF 账号下的 zone（脚本自动建隧道+DNS，你不用碰 CF 面板）。
- **预期结尾**：打印 `✅ done.`，含 `site https://…`、`api https://…/api`、**admin token**。verify 不过不算成功。
- 把这个 admin token 存好——它就是后面所有 `/api/admin/*` 调用的 `Authorization: Bearer <token>`：

```bash
export HOMESTEAD_SITE_API="https://$API_DOMAIN/api"
export TOKEN="<deploy.sh 打印的 admin token>"
```

> token 默认较短（见[常见坑](#常见坑)）；要长效重新铸：`docker compose exec -T backend flask --app app.main token issue --email "$ADMIN_EMAIL" --days 30`（多实例加 `-p "$INSTANCE_NAME"`）。

### ③ `PATCH /admin/site/settings` 写 NAP — 约 3–5 分钟

把 intake 里的电话/地址/营业时间/服务城市逐字写进去。**runtime 生效、无需重建**。

```bash
curl -s -X PATCH "$HOMESTEAD_SITE_API/admin/site/settings" -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" -d '{
    "legalName":"Acme Pressure Washing Ltd.",
    "phone":"+1 604-555-0142",
    "email":"hello@acme.com",
    "addressStreet":"123 Main St","addressCity":"Surrey","addressRegion":"BC",
    "addressPostalCode":"V3T 0A1","addressCountry":"CA",
    "latitude":49.19,"longitude":-122.85,
    "businessHours":[{"days":["Mo","Tu","We","Th","Fr"],"opens":"09:00","closes":"18:00"},
                     {"days":["Sa"],"opens":"10:00","closes":"16:00"}],
    "serviceAreas":["Surrey","Vancouver","Burnaby"]
  }'
```

- **预期**：返回 `{"item":{"stored":…,"effective":…,"changed":[...]}}`，`changed` 列出你刚写的字段名。
- **读回核对**：`curl -s "$HOMESTEAD_SITE_API/site" -H "Authorization: Bearer $TOKEN" | jq '.item.nap'`（`GET /api/site` 的 `item.nap`）。这些数据会喂给 SEO 的 LocalBusiness JSON-LD。

### ④ `rebrand` 到客户行业带 brandName — 约 2 分钟

一次调用把**整站**换成客户行业：重建首页 9 块结构 + About/Services 内页，同步店名/导航/页脚/博客副标题/SEO/客服名，**无需重建**。

```bash
curl -s -X POST "$HOMESTEAD_SITE_API/admin/site/rebrand" -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" -d '{
    "industry":"construction",
    "brandName":"Acme Pressure Washing",
    "audience":"大温地区独立屋业主"
  }'
```

- 用内置主题风格也可传 `preset` 代替 `industry`；先看效果不落地加 `"dryRun":true`。
- **预期**：返回 `{"item":…, "pagesTouched":N, "site":…, "imagery":…, "audit":…}`，`audit` 就是随后要修到全绿的一致性清单。每个图位是**带提示词的占位图**。
- 换错了：`POST /admin/undo {"target":"home"}` 可撤销（rebrand 有快照）。
- 若步骤 ② 已用 `SITE_INDUSTRY` seed 对了行业且不改店名，可跳过本步——但带 `brandName` 的 rebrand 是把店名一次性铺满全站最省事的做法。

### ⑤ 改文案 / 换图（照 getting-started.zh.md）— 约 10–20 分钟

按 [`getting-started.zh.md`](getting-started.zh.md) 的方式做。核心三件事：

1. **看有哪些面和 block**：`GET /admin/surfaces`（拿 target 和 block id）。
2. **改文字**：`PATCH /admin/compose/<target>/blocks/<id>`（改 headline/正文等）；改店名/受众等身份字段直接 `PATCH /admin/site/settings`。
3. **换图**：上传得绝对 URL，再填进对应 block——

```bash
URL=$(curl -s -X POST "$HOMESTEAD_SITE_API/admin/media" -H "Authorization: Bearer $TOKEN" \
        -F "file=@hero.jpg" | jq -r .item.url)          # 也支持 {url} 外链 / {data} base64
curl -s -X PATCH "$HOMESTEAD_SITE_API/admin/compose/home/blocks/<blockId>" -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" -d "{\"content\":{\"image\":\"$URL\"}}"
```

- **填了真图，占位图自动消失。** 每个空图位上写着「该放什么照片」的提示词。
- **要双语**：写操作加 `?locale=zh` 即写中文版（在相同 block id 上原地翻译，别改结构）；整页翻译用 `homestead-site-i18n` 技能最省事。
- **落地页（服务城市页）**：`POST /admin/pages`（`title` + `sections|body_markdown|template`），可带 `local_business_overrides {"service_areas":["Surrey"],"service_type":"Pressure Washing"}`；改用 `PATCH /admin/pages/<id>`，meta 用 `meta_title`/`meta_description`。

### ⑥ `GET /admin/consistency` 循环到 `ok:true`（硬验收门）— 约 5–10 分钟

这是「完成的定义」。换行业/翻译后一定有残留，修到全绿为止。

```bash
curl -s "$HOMESTEAD_SITE_API/admin/consistency" -H "Authorization: Bearer $TOKEN" \
  | jq '.item.ok, .item.summary, .item.findings'
```

- **预期**：`ok:true`，`findings` 为空。`false` 时逐条按 `findings` 修（中英错位 / 缺翻译 / 结构发散 / 旧行业残留），改完**再查**，循环到 `ok:true`。
- **不到 `ok:true` 不发布。** 全绿后打开 `/en` 与 `/zh` 各扫一眼。

### ⑦ 配 Telegram bot / webchat 交接 — 约 3–5 分钟

让店主能用手机管站、并能接管访客客服。按 [`telegram-agent-setup.md`](telegram-agent-setup.md) 配置：OpenClaw agent 暴露为 Telegram bot（技能在 `skills/`，`website` 为前门菜单）；在线客服桥在 `ops/webchat-bridge/`（`bridge.py` + README，访客消息镜像到运营 Telegram，可一句话接管）。

> **权限红线**：`homestead-site-ops` 技能需要服务器 shell 权限——**绝不能**给买家/店主装。店主只给内容类技能（rebrand/compose/media/i18n/blog/pages 等）。

### ⑧ 交付店主手册 + 收款 — 约 2 分钟

- 把店主手册 [`owner-manual.zh.md`](owner-manual.zh.md) 发给客户（怎么用 Telegram 改文案/换图/看客服）。
- 过一遍下面的[验收清单](#验收清单)，全绿 → 交付站点地址 + 手册 → **收款**。

---

## 验收清单

发布前逐项打勾，缺一不发：

- [ ] **每页 meta 已填**：首页 + 每个内页都有 `meta_title` / `meta_description`（`PATCH /admin/pages/<id>` 补）。
- [ ] **无占位图残留**：所有图位已换真图（占位图会自动消失；`GET /admin/surfaces` 逐面确认没有占位提示词图）。
- [ ] **NAP 逐字一致**：`GET /api/site` 的 `item.nap` 与 intake 表逐字核对——店名、电话、地址、营业时间、服务城市一字不差。
- [ ] **sitemap / robots / llms.txt 正常**：`curl -s https://$SITE_DOMAIN/sitemap.xml | head`（含所有页面）；`curl -sI https://$SITE_DOMAIN/robots.txt`；`curl -s https://$SITE_DOMAIN/llms.txt | head`。
- [ ] **rich results 可测**：把某页 URL 丢进 Google Rich Results Test，确认 LocalBusiness / Service / FAQPage / BreadcrumbList 被识别。（注意：本站**不输出** AggregateRating/Review——Google 禁止自托管评价评分，别期待星级。）
- [ ] **一致性全绿**：`GET /admin/consistency` → `ok:true`（第 ⑥ 步的硬门）。
- [ ] **生产站正常**：`SITE_DOMAIN=$SITE_DOMAIN API_DOMAIN=$API_DOMAIN bash ops/agent/verify.sh` 通过（本地 origin + 公网隧道全 OK）；浏览器打开 `/en` 与 `/zh` 目视无误。

---

## 常见坑

- **cloudflared 容器重建后要 restart**：任何 `docker compose up -d --build` 重建了 app 容器，容器换了新 IP，隧道会 502/530。**重启该实例的连接器**：`docker restart ${INSTANCE_NAME:-homestead}-cloudflared`（`update.sh` 已内含）。verify 若本地 OK 公网挂，先等 ~1 分钟 DNS，再重启连接器重跑 verify。
- **admin token 会过期**：默认按 `JWT_EXPIRES_HOURS`（较短），交付/维护期反复失效很烦。铸长效 token：`docker compose exec -T backend flask --app app.main token issue --email "$ADMIN_EMAIL" --days 30`（多实例加 `-p "$INSTANCE_NAME"`）。前提：该邮箱在 `ADMIN_EMAILS` 里。
- **低配 VM 前端构建吃内存**：`next build` 峰值 1.5GB+，1–2GB 的 VM 容易 OOM 卡死。建议 **2GB 内存 + 2GB swap** 起步；多实例**串行**部署/更新，别同时 build 两个前端。
- **域名不在 CF 账号会建隧道失败**：`SITE_DOMAIN`/`API_DOMAIN` 必须是 CF token 能管的 zone。用自管 ingress（自己的 nginx / cert.pem 隧道）就 `deploy.sh --skip-tunnel`，公网检查降为警告。
- **rebrand 会重置本地化文案**：`rebrand` 会重建首页、清掉旧行业的 per-locale section 覆盖。**先 rebrand，再翻译/精修文案**，别反过来白干。

---

相关文档：无头部署总纲 [`../AGENT-DEPLOY.md`](../AGENT-DEPLOY.md) · 灌内容 5 步 [`getting-started.zh.md`](getting-started.zh.md) · 多实例 [`multi-instance.md`](multi-instance.md) · 手机管理 [`telegram-agent-setup.md`](telegram-agent-setup.md) · 店主手册 [`owner-manual.zh.md`](owner-manual.zh.md)。
