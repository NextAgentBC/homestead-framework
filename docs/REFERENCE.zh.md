# Homestead 系统参考（分类总览）

> 一句话：这是一套 **「Elementor，但用 Telegram 聊天操作」** 的网站框架——所有外观与结构都是
> **token + block**，组件零硬编码 CSS，OpenClaw通过下面这套 API 即时改站。
> 本文件是「能力面」的权威清单：**API / 字体 / 主题 / 积木 / 其它维度**。改了代码记得同步本文件。

- 基地址：`$HOMESTEAD_SITE_API`（线上 `https://your-api.example.com/api`）
- 鉴权：**公开读**免 token；**管理写**（`/admin/*`）需要 `Authorization: Bearer $HOMESTEAD_SITE_TOKEN`
- 响应约定：单个 `{ "item": {...} }` · 列表 `{ "items": [...] }` · 出错 `{ "error": { "code", "message" } }`
- 改动即时：design / compose / i18n / media 的写操作**无需重部署**，下次加载即生效

---

## 一、API（按域分类）

### 公开读（无 token）

**站点 & 设计**
| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/health` | 健康检查 |
| GET | `/site` | 站点配置（名称、语言等） |
| GET | `/design` `?locale=` | 当前生效的设计档（tokens + sections） |
| GET | `/blocks` | 积木目录（类型 / 变体 / 字段 / 默认值 / 图标库）|
| GET | `/patterns` · `/patterns/{slug}` | 已存板块模式库（截图捕获沉淀） |
| GET | `/i18n/{locale}` | 界面文案（导航 / 页脚 / 按钮） |
| GET | `/media/{filename}` | 自托管图片文件 |
| GET | `/openapi.json` | 机器可读的接口契约 |

**内容**
| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/blogs` `?locale=` · `/blogs/{slug}` | 已发布博客 |
| GET | `/pages` `?locale=` · `/pages/{slug}` | 已发布内容页 |

**互动**
| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/auth/google` | Google 登录 / 注册 |
| POST | `/newsletter/subscribe` | 订阅邮件列表 |
| POST | `/contact` | 联系表单（同时推送到运营 Telegram） |
| POST | `/chat` | 在线聊天：访客消息 `{sessionId?, message}`，由**沙箱无工具客服助手**应答，返回 `{sessionId, reply}`（有限流） |
| GET | `/chat/{sessionId}` | 在线聊天：某会话完整记录 |

### 管理写（需 admin token，前缀 `/admin`）

**设计 design**
| 方法 | 路径 | 说明 |
|---|---|---|
| GET / PATCH | `/admin/design` | 读 / 改主题 tokens（合并） |
| POST | `/admin/design/generate` | 套用预设 `{preset}` 或按行业 `{industry}` 生成 |
| POST | `/admin/design/analyze-competitors` | 喂入竞品观察 → 生成和谐配色 |

**站点级 site（高层操作 —— 把"换行业""查一致性"变成一次调用）**
| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/admin/site/rebrand` | **一键换行业**：重生成首页设计+版块、清掉各语言残留的旧版块（防止"中文页卡在旧站"）、每面快照（一次 `undo` 全量回滚）、返回 `imagery`（模板声明的配图提示词+落点）与一致性审计。`{industry\|preset, competitorUrls?, brandName?, dryRun?}`。是 rebrand 不是微调——会重生成首页、重置本地化文案 |
| GET | `/admin/consistency` | **一致性审计 = "做完"的机器判定**：逐 面×语言 报 `structural_drift`（结构漂移）/ `missing_translation`（缺/未译）/ `language_mismatch`（中英错位）/ `industry_residue`（旧行业残留）→ `{ok, findings[], summary}`。换行业/翻译后循环修到 `ok:true` 才算完 |

**内容 content**
| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/admin/blogs` · PATCH `/admin/blogs/{id}` | 建 / 改博客（`?locale=` 改某语言） |
| POST | `/admin/blogs/generate` | AI 生成博客 |
| POST | `/admin/pages` · PATCH / DELETE `/admin/pages/{id}` | 建 / 改 / 删页面 |

**编排 compose（按 block 改页面）** — `target` = `home` 或页面 slug
| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/admin/surfaces` | 列出所有可编辑面（首页 + 各页）及其 block / 语言 |
| GET / POST | `/admin/compose/{target}/blocks` | 列出 / 新增 block（或插入 `{pattern}`） |
| PATCH / DELETE | `/admin/compose/{target}/blocks/{blockId}` | 改 / 删某 block |
| POST | `…/blocks/{blockId}/move` · `…/duplicate` | 移动 / 复制 |
| POST | `/admin/compose/{target}/batch` | 一次多步、默认原子 |

**撤销 / 版本 revisions（每次 compose / design 改动前自动快照，可撤销 / 回滚）**
| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/admin/revisions` `?target=&locale=` | 改动历史（最新在前）；`target`=`home` / 页面 slug / `design`；不给 target 则跨面汇总 |
| POST | `/admin/undo` | 撤销某面最近一次改动 `{target, locale?}`（消费最新快照，可连撤） |
| POST | `/admin/revisions/{id}/restore` | 回到某个历史快照（会先快照当前态，故 restore 本身也可再撤销） |

**捕获 patterns**
| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/admin/patterns` | 把某 block 存成可复用模式（`{spec}` 或 `{target,blockId}`） |
| DELETE | `/admin/patterns/{id}` | 删除模式 |

**双语 i18n**
| 方法 | 路径 | 说明 |
|---|---|---|
| PATCH | `/admin/i18n/{locale}` | 改界面文案（合并；`{replace:true}` 覆盖） |

**媒体 media（仅上传，不生图）**
| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/admin/media` | 列出已托管图片 |
| POST | `/admin/media` | 上传：multipart `file` / `{url}` 抓取 / `{data}` base64 → 返回**绝对 URL** |
| DELETE | `/admin/media/{filename}` | 删除图片 |

> ⚠️ **图片 URL 必须用绝对地址**（`https://homestead-api…/api/media/<file>`）。前端无 `/api` 反代，裸 `/api/media/…` 在前端会 404；上传接口已直接返回绝对 `url`。

**在线聊天 chat（运营台 + 接管）**
| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/admin/chat` `?status=` · `/admin/chat/{sessionId}` | 列出会话 / 读某会话完整记录 |
| POST | `/admin/chat/{sessionId}/reply` | 人工 / 客服助手**接管**，回复直接进访客聊天窗 |
| POST | `/admin/chat/{sessionId}/close` | 关闭（`{reopen:true}` 重开）会话 |

> 💬 **聊天大脑是无工具的一次性模型调用**（host `webchat-bridge`）：没有 shell / 文件 / 工具面，注入也无法执行；prompt 只含公开站点知识 + 本访客对话，不碰私有记忆。每段对话镜像到运营 Telegram，可随时接管。

---

## 二、设计系统

### 1) 字体（6 档，全是 token，组件零硬编码）

| 后端常量 | 实际字体 | CSS 变量 | 典型用途 |
|---|---|---|---|
| `SANS` | Inter | `--font-sans` | 正文默认无衬线 |
| `GROTESK` | Space Grotesk | `--font-grotesk` | 几何感标题（tech / bold-dark / corporate / creative） |
| `SERIF` | Spectral | `--font-display` | 衬线展示（editorial / legal / realestate） |
| `FRAUNCES` | Fraunces | `--font-fraunces` | 优雅高级衬线（beauty / restaurant / luxe） |
| `CONDENSED` | Oswald | `--font-condensed` | 高能压缩体（fitness） |
| `MONO` | 系统等宽栈 | `ui-monospace…` | 代码 / 数字 |

排版 token：`typography.body` 与 `typography.heading`，各引用上面的字体栈 → 切主题即换字体对。

### 2) 主题预设（18 套，一键 `generate {preset}`，即时渲染）

每套 = 配色 + 明/暗 + 字体对 + hero 风格 + 段落编排（不只是换色）。

| key | 名字 | 气质 | hero | 模式 | 字体 |
|---|---|---|---|---|---|
| `minimal` | Aurora | Apple / Linear / Stripe，沉静高级 | centered | 浅 | Inter |
| `bold-dark` | Eclipse | Tesla / Vercel，戏剧高对比、电光紫 | fullbleed | 暗 | Space Grotesk |
| `editorial` | Atelier | 温暖文学、衬线展示、首字下沉长文 | split | 浅 | Spectral |
| `corporate` | Meridian | 可信 B2B、结构化藏青、价格档 | split | 浅 | Space Grotesk |
| `tech` | Nimbus | 现代 SaaS / 创业，靛蓝 + 青 | centered | 浅 | Space Grotesk |
| `healthcare` | Vitalis | 诊所 / 健康，青绿、圆润可信 | split | 浅 | Inter |
| `restaurant` | Saffron | 餐厅 / 咖啡，红椒 + 橄榄 | fullbleed | 浅 | Fraunces |
| `realestate` | Cornerstone | 高端地产 / 建筑，石板灰 + 黄铜 | split | 浅 | Spectral |
| `fitness` | Ignite | 高能健身 / 运动，暗 + 荧光 | fullbleed | 暗 | Oswald |
| `beauty` | Lumière | 优雅沙龙 / 水疗，腮红 + 藕荷 | centered | 浅 | Fraunces |
| `legal` | Sterling | 权威律所 / 顾问，藏青 + 金 | split | 浅 | Spectral |
| `creative` | Kinetic | 大胆工作室 / 代理，近黑 + 荧光重点 | centered | 浅 | Space Grotesk |
| `luxe` | Onyx | 奢华 / 高定，近黑 + 金、衬线、留白 | centered | 暗 | Fraunces |
| `education` | Scholar | 学校 / 辅导，友好蓝 + 琥珀、圆润 | split | 浅 | Inter |
| `nonprofit` | Grove | 公益 / 慈善，暖绿 + 琥珀、人文 | centered | 浅 | Inter |
| `finance` | Vault | 金融 / 顾问，翡翠 + 信任蓝、结构化 | split | 浅 | Inter |
| `playful` | Pop | 趣味 / 儿童 / DTC，紫 + 粉 + 黄、超圆 | centered | 浅 | Space Grotesk |
| `neon` | Pulse | 未来 / 游戏，近黑 + 青/品红霓虹 | fullbleed | 暗 | Space Grotesk |

**行业自动映射**：`generate {"industry":"<名>"}` 不给 preset 时，自动选模板——
- → `tech`：tech / saas / software / startup / ai
- → `healthcare`：health / medical / clinic / dental / wellness / therapy
- → `restaurant`：food / cafe / coffee / bakery / catering / bar
- → `realestate`：property / realty / architecture / interior
- → `fitness`：gym / sport(s) / trainer / yoga
- → `beauty`：salon / spa / cosmetics / skincare / hair
- → `legal`：law / lawyer / attorney / advisory / consulting
- → `creative`：agency / studio / design / portfolio / marketing / photography
- 其它行业（教育 / 会计 / 零售…）→ 在默认版式上套一层定制配色。

> **图文完整模板**：`beauty · restaurant · healthcare · legal · fitness` 已升级为「9 块完整 + 自带配图声明」的一等模板（全幅大图 hero · 服务 · 作品集 · 流程 · 口碑 · 价格 · FAQ · 图文 CTA，每个图槽都带 `imagePrompt`）。`rebrand`/`generate` 到这些行业即出完整专业结构。**新增一个行业**只需在 `design_service.py` 的 `_RICH_INDUSTRY_SPECS` 加一条几行的 spec（行业文案 + 6 个配图提示词）——这就是「自己加模板」的快路径。

### 3) Design tokens（改这些 = 改主题，PATCH `/admin/design` 即时）

| 组 | 键 |
|---|---|
| `colors`（12） | ink · muted · paper · surface · line · primary · accent · highlight · link · **surfaceInverse** · **inkInverse** · **onPrimary** |
| `typography` | body · heading |
| `radius` | card · control · pill |
| `layout` | density · heroMinHeight · sectionGap · contentMaxWidth · cardPadding |
| `voice` | headlineStyle · tone |

> 暗对比带三件套（`surfaceInverse` 带背景 / `inkInverse` 其上文字 / `onPrimary` 主色按钮上的文字）让全屏 hero、CTA 带在浅色主题里也能放一段暗色——这是「深色主题不再硬编码」的关键。

---

## 三、Blocks（15 种；页面 = 有序 block 列表）

| type | 名字 | 变体 variants | 内容字段 | 带图 |
|---|---|---|---|---|
| `hero` | Hero | split · centered · fullbleed | badge, kicker, headline, headlineAccent, subhead, **image, imageFocal, imageAlt, imagePrompt**, cta, secondaryCta | ✅大图（fullbleed/centered 全幅背景；split 并排） |
| `stats` | Stats / KPI | default | items{value,label} | |
| `logos` | Logo / 信任条 | default | heading, items{label} | |
| `features` | Features | cards · minimal | heading, subhead, items{icon,title,body} | |
| `problem` | 痛点 | cards | heading, subhead, items{icon,title,body} | |
| `comparison` | 对比（我们 vs 他们） | default | heading, left, right | |
| `testimonials` | 用户证言 | default | heading, items{quote,author,role,**image**,href} | ✅头像 |
| `pricing` | 价格档 | default | heading, subhead, items{name,price,period,features,featured,cta} | |
| `faq` | 常见问答 | default | heading, items{q,a} | |
| `cta` | 行动号召 | banner | headline, subhead, **image, imagePrompt**, cta | ✅背景图 |
| `section` | **柔性自定义** | grid · split · stack · banner | eyebrow, heading, subhead, layout, items, cta | ✅media |
| `steps` | 步骤 / 流程 | default | heading, subhead, items{title,body} | |
| `gallery` | 图库 | grid | heading, subhead, items{**image**,caption} | ✅ |
| `team` | 团队 | cards | heading, subhead, items{**image**,name,role,body} | ✅ |
| `banner` | 高亮横幅 | default · tint | icon, text, cta | |

**柔性 `section`（无代码加新版式的入口）**
- 变体：`grid` / `split` / `stack` / `banner`
- `layout`：columns 1–4 · align left/center · media none/left/right/top · tone plain/tint/inverse
- item `kind`：feature / stat / quote / step / media / text / button

**icon 库（8）**：`sparkles` · `mail` · `shield` · `gauge` · `layers` · `zap` · `book` · `cloud`

> **配图策略（学员无需任何生成器）**：模板的图槽默认**留空**并带 `imagePrompt`。前端把空图槽渲染成**带提示词的设计占位图**（作品集格 = 相机图标+提示词；hero/cta = 一个提示词胶囊）——页面看着是成品、并明确告诉你每处该放什么图。上传真图（`/admin/media`）后占位图自动消失。**生成真图是可选增强**（有 openart 等生成器时，`rebrand` 按 `imagery` 提示词自动出图）。

> **只有这些才需要改代码**：新增一种全新 block 类型（`block_service.py` + `sections.tsx`），或新增主题/行业模板（`design_service.py` 的 `STYLE_PRESETS` / `_RICH_INDUSTRY_SPECS` 加一条）。其余日常操作（设计 / 编排 / 翻译 / 媒体 / 换行业 / 审计）都是聊天即时、无需重部署。

---

## 四、其它维度

- **语言**：`en`（默认）· `zh`，路径式 `/zh`（利于 SEO）。内容译文存各模型的 `i18n` JSON 列，界面文案走 `/i18n`。
- **媒体**：仅上传，`png/jpg/gif/webp`，≤ 10MB；魔术字节校验；存 `media-data` 卷；返回绝对 URL；CDN 缓存 24h（文件名唯一不可变）。
- **每种 block 各有一个轻量触发技能**（`homestead-site-block-*`，opt-in 默认不装），让「加个价格表 / add an FAQ」精准路由，最终都委托 compose 引擎。
- **在线聊天**：右下角气泡，由**沙箱无工具客服助手**实时应答（host `webchat-bridge` → `openclaw infer`，零工具面、防注入），中英文自适应；每段对话镜像到运营 Telegram，可随时接管；contact 表单也会推送线索到 Telegram。

---

## 五、OpenClaw 技能 ↔ API（命令地图）

| 域 | 技能（Telegram 命令） | 主要 API |
|---|---|---|
| 入口 | `website`（`/website`） | 路由到下面各技能 |
| 基础 | `homestead-site-shared`（先读） | `$HOMESTEAD_SITE_API` + token |
| 设计 | `homestead-site-design`（`/homestead_site_design`） | `/admin/design*`、`/design` |
| 换行业 | `homestead-site-rebrand`（`/homestead_site_rebrand`） | `/admin/site/rebrand`、`/admin/consistency`（循环修到 `ok:true`） |
| 编排 | `homestead-site-compose`（`/homestead_site_compose`） | `/admin/compose/*`、`/blocks`、`/admin/surfaces` |
| 捕获 | `homestead-site-capture`（`/homestead_site_capture`） | `/admin/compose/*`、`/admin/patterns`、`/patterns` |
| 内容·博客 | `homestead-site-blog`（`/homestead_site_blog`） | `/admin/blogs*`、`/blogs` |
| 内容·页面 | `homestead-site-pages`（`/homestead_site_pages`） | `/admin/pages*`、`/pages` |
| 双语 | `homestead-site-i18n`（`/homestead_site_i18n`） | `/admin/i18n`、`?locale=` 系列、`/i18n` |
| 媒体 | `homestead-site-media`（`/homestead_site_media`） | `/admin/media*`、`/media` |
| 互动 | `homestead-site-newsletter`（`/homestead_site_newsletter`） | `/newsletter/subscribe`、`/contact` |
| 在线客服 | `homestead-site-chat`（接管网站聊天） | `/admin/chat*`、`/chat` |
| 运维 | `homestead-site-ops`（`/homestead_site_ops`） | `/health`、docker / 部署 |

---
*自检：`backend/api_audit.py`（进程内 64/64，覆盖全部端点 + 鉴权 + 错误分支）。接口契约见 `backend/app/openapi.json`。*
