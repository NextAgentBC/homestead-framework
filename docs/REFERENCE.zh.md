# Homestead 系统参考（分类总览）

> 一句话：这是一套 **「Elementor，但用 Telegram 聊天操作」** 的网站框架——所有外观与结构都是
> **token + block**，组件零硬编码 CSS，小爪（OpenClaw）通过下面这套 API 即时改站。
> 本文件是「能力面」的权威清单：**API / 字体 / 主题 / 积木 / 其它维度**。改了代码记得同步本文件。

- 基地址：`$ORACLE_SITE_API`（线上 `https://homestead-api.nextagent.ca/api`）
- 鉴权：**公开读**免 token；**管理写**（`/admin/*`）需要 `Authorization: Bearer $ORACLE_SITE_TOKEN`
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
| POST | `/contact` | 联系表单 |

### 管理写（需 admin token，前缀 `/admin`）

**设计 design**
| 方法 | 路径 | 说明 |
|---|---|---|
| GET / PATCH | `/admin/design` | 读 / 改主题 tokens（合并） |
| POST | `/admin/design/generate` | 套用预设 `{preset}` 或按行业 `{industry}` 生成 |
| POST | `/admin/design/analyze-competitors` | 喂入竞品观察 → 生成和谐配色 |

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
| `hero` | Hero | split · centered · fullbleed | badge, kicker, headline, headlineAccent, subhead, cta, secondaryCta | |
| `stats` | Stats / KPI | default | items{value,label} | |
| `logos` | Logo / 信任条 | default | heading, items{label} | |
| `features` | Features | cards · minimal | heading, subhead, items{icon,title,body} | |
| `problem` | 痛点 | cards | heading, subhead, items{icon,title,body} | |
| `comparison` | 对比（我们 vs 他们） | default | heading, left, right | |
| `testimonials` | 用户证言 | default | heading, items{quote,author,role,**image**,href} | ✅头像 |
| `pricing` | 价格档 | default | heading, subhead, items{name,price,period,features,featured,cta} | |
| `faq` | 常见问答 | default | heading, items{q,a} | |
| `cta` | 行动号召 | banner | headline, subhead, cta | |
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

> 新增**一种全新 block 类型**或**一套全新预设**仍是代码改动（`block_service.py` + `sections.tsx` / `design_service.py`）；其余日常操作都是聊天即时。

---

## 四、其它维度

- **语言**：`en`（默认）· `zh`，路径式 `/zh`（利于 SEO）。内容译文存各模型的 `i18n` JSON 列，界面文案走 `/i18n`。
- **媒体**：仅上传，`png/jpg/gif/webp`，≤ 10MB；魔术字节校验；存 `media-data` 卷；返回绝对 URL；CDN 缓存 24h（文件名唯一不可变）。
- **每种 block 各有一个轻量触发技能**（`oracle-site-block-*`，opt-in 默认不装），让「加个价格表 / add an FAQ」精准路由，最终都委托 compose 引擎。

---

## 五、小爪技能 ↔ API（OpenClaw 命令地图）

| 域 | 技能（Telegram 命令） | 主要 API |
|---|---|---|
| 入口 | `website`（`/website`） | 路由到下面各技能 |
| 基础 | `oracle-site-shared`（先读） | `$ORACLE_SITE_API` + token |
| 设计 | `oracle-site-design`（`/oracle_site_design`） | `/admin/design*`、`/design` |
| 编排 | `oracle-site-compose`（`/oracle_site_compose`） | `/admin/compose/*`、`/blocks`、`/admin/surfaces` |
| 捕获 | `oracle-site-capture`（`/oracle_site_capture`） | `/admin/compose/*`、`/admin/patterns`、`/patterns` |
| 内容·博客 | `oracle-site-blog`（`/oracle_site_blog`） | `/admin/blogs*`、`/blogs` |
| 内容·页面 | `oracle-site-pages`（`/oracle_site_pages`） | `/admin/pages*`、`/pages` |
| 双语 | `oracle-site-i18n`（`/oracle_site_i18n`） | `/admin/i18n`、`?locale=` 系列、`/i18n` |
| 媒体 | `oracle-site-media`（`/oracle_site_media`） | `/admin/media*`、`/media` |
| 互动 | `oracle-site-newsletter`（`/oracle_site_newsletter`） | `/newsletter/subscribe`、`/contact` |
| 运维 | `oracle-site-ops`（`/oracle_site_ops`） | `/health`、docker / 部署 |

---
*自检：`backend/api_audit.py`（进程内 62/62，覆盖全部端点 + 鉴权 + 错误分支）。接口契约见 `backend/app/openapi.json`。*
