# 多站维护运维手册(fleet maintenance)

一台主机跑 N 个客户站,靠"记忆力"维护迟早翻车。本手册把"维护 N 个客户站"变成有节奏、
可照做的例行动作:**知道状态、安全滚更新、别丢数据**。

配套脚本都在 `ops/fleet/`(健康探测/面板/告警)与 `ops/backup/`(备份/恢复),本手册只讲
"什么时候、按什么顺序、遇到什么按哪个"。脚本自身的参数细节见
[`ops/fleet/README.md`](../ops/fleet/README.md) 与 [`ops/backup/README.md`](../ops/backup/README.md)。

---

## 1. 心智模型:一实例 = 一目录 = 一 compose project

先把这条刻进脑子,后面所有命令都从它推导:

- **一个客户 = 一个 clone 目录 = 一个 compose project(`INSTANCE_NAME`)。**
  目录名 == `INSTANCE_NAME` == `docker compose -p` 的 project 名 == 隧道连接器前缀
  (`<INSTANCE_NAME>-cloudflared`)== 媒体卷前缀(`<INSTANCE_NAME>_media-data`)。约定详见
  [`docs/multi-instance.md`](multi-instance.md)。
- **实例之间只共享一个 `edge` Docker 网络**(给各自的 Cloudflare 隧道用),数据库、`.env`、
  容器、卷全部隔离,互不可见。
- 宿主机端口只绑 `127.0.0.1`(公网走隧道),每实例 +10:`13000/18000` 起(默认 `3000/8000`
  留给本机开发实例)。这些端口就是 `verify`/`status` 在本机探测用的。
- **哪些实例住在这台机器上,唯一的真相是 `ops/fleet/instances.csv`。** 一行一个客户。所有
  fleet 命令都读它。它是运维状态,不是源码 —— 不进 git(仓库里只留
  `instances.example.csv`)。

运维就三件事,本手册按这三件事组织:

| 目标 | 靠什么 |
|---|---|
| **知道状态** | `status.sh` / `all.sh status` / `dashboard.sh` / `notify.sh` |
| **安全滚更新** | `all.sh status` 确认全绿 → 单实例 `update.sh` 验证 → `all.sh update` |
| **别丢数据** | `backup.sh`(timer 自动)+ `restore.sh`(定期演练) |

---

## 2. 日常 / 每周节奏表

维护不是"出事才看",而是固定节奏。下表是最小可行例行:

| 频率 | 做什么 | 命令 / 机制 |
|---|---|---|
| **持续(自动)** | 每 15 分钟刷新健康面板 + 对 WARN/DOWN 推 Telegram | `homestead-fleet-status.timer`(装一次,见 §7 / README) |
| **每天** | 扫一眼面板,收/看告警;有红的按 §5 处理 | 打开 `~/homestead-fleet-status.html`,或手跑 `bash ops/fleet/dashboard.sh ops/fleet/instances.csv` |
| **每天(自动)** | 每实例数据库 + 媒体自动备份 | `homestead-backup@<inst>.timer`(每实例装一次,见 `ops/backup/README.md`) |
| **每周** | 主动全量健康巡检(读所有站的本地+公网+容器+DB+备份新鲜度) | `bash ops/fleet/all.sh status ops/fleet/instances.csv` |
| **每周** | 需要的话滚更新到最新代码(见 §4,别在没确认全绿时更) | `bash ops/fleet/all.sh update ops/fleet/instances.csv` |
| **每季度** | 恢复演练 —— 证明备份真能用(恢复到临时实例名再 verify) | `bash ops/backup/restore.sh …`(见 §5-DB 与 backup README) |
| **接入新客户时** | 部署后把新站纳入 fleet(CSV / 备份 timer / 面板) | 见 §7 |

节奏原则:**自动的(备份、面板、告警)交给 timer,人的注意力只花在"看告警 + 每周巡检 +
更新前确认"上。** 没有告警、面板全绿,就不用动手。

---

## 3. 状态怎么读

健康的单一真相是 `ops/fleet/status.sh`(每实例一个探测),`all.sh status` 把它 fan-out 到
全 fleet,`dashboard.sh` 把结果画成 HTML,`notify.sh` 把异常推 Telegram —— 四者读同一份数据。

### `all.sh status` 表格各列

```
INSTANCE            SITE  API   CONT    PAGES  BACKUP   TUN    OVERALL
```

| 列 | 含义 | 怎么读 |
|---|---|---|
| `INSTANCE` | 实例名(== 目录 == compose project) | CSV 里那一行 |
| `SITE` | 公网站点可达性(`https://<site_domain>/`) | `up` = 200/301/307/308;`down` = 其它/超时;`skip` = CSV 没填域名 |
| `API` | 公网 API 健康(`https://<api_domain>/api/health`) | `up` = 200;`down` = 其它 |
| `CONT` | 该 project 运行/健康的容器数 / 总数 | `4/4` 全好;`3/4` 有容器挂了;`n/a` = 本机没 docker 或读不到 |
| `PAGES` | DB 往返 + `page` 表行数(证明 DB 可达且 schema 在) | 数字 = DB 正常;`?` = DB 探测失败(降级,非致命) |
| `BACKUP` | 最近一次本地备份距今天数 | `0d/1d…` = 正常;`none` = 从没备份过;`>WARN_BACKUP_DAYS`(默认 2)= 过期 |
| `TUN` | 隧道连接器容器 `<tunnel>-cloudflared` 状态 | `up` 运行中;`down` 存在但没跑;`n/a` 没这个容器(可能自管 ingress) |
| `OVERALL` | 该实例总评 | `OK` / `WARN` / `DOWN`(见下) |

### OK / WARN / DOWN 分别代表什么

`status.sh` 的 rollup 规则(直接来自脚本):

- **`DOWN`(红,客户看得见的事故)**:公网站点**或** API 不可达,**或**容器该起的没全起。
  → 立刻按 §5 处理。`all.sh status` / 单实例 `status.sh` 遇 DOWN 退出码非零;`notify.sh` 会推。
- **`WARN`(黄,降级但站还活着)**:站点+API 都通、容器都在,但**备份过期/从没备份**,
  **或** DB 往返失败(`PAGES=?`),**或**隧道容器 down。→ 不是火警,但要尽快消除,别让它拖成事故。
  WARN **不**让批量任务失败(exit 0),因为站还在服务。
- **`OK`(绿)**:全部通过,啥也不用做。

### WARN 该做什么(对症)

| WARN 的原因(看 BACKUP/PAGES/TUN 列) | 处理 |
|---|---|
| `BACKUP = none` 或过期 | 该实例目录里手动补一次:`bash ops/backup/backup.sh`;并确认它的 `homestead-backup@<inst>.timer` 已 enable(见 `ops/backup/README.md`) |
| `PAGES = ?`(DB 往返失败) | 进目录看 postgres:`docker compose -p <inst> ps`;必要时 `docker compose -p <inst> up -d postgres`;仍不行走 §5-DB |
| `TUN = down` | `docker restart <tunnel>-cloudflared`,再 `bash ops/fleet/all.sh verify ops/fleet/instances.csv` 或单实例 status 复查 |

> `SITE`/`API`/`PAGES` 列在表格里显示的是探针值,`--json` 模式给机器读(`dashboard.sh` /
> `notify.sh` 消费):`bash ops/fleet/all.sh status ops/fleet/instances.csv --json`。

---

## 4. 安全滚动更新

更新 = `git pull` → 重建容器 → 重启隧道 → verify。批量更新最容易踩的坑是**在有站已经不健康时
就更**,把小问题放大成全 fleet 事故。铁律顺序:

**① 先确认全绿。**

```bash
bash ops/fleet/all.sh status ops/fleet/instances.csv
```

有 `DOWN` 先按 §5 修好、有 `WARN` 尽量先消,别在带病状态下滚更新。

**② 先在一个实例上验证这次更新。** 挑一个(最好是你自己的预览/低风险实例),进它的目录跑
单实例更新,确认 verify 过:

```bash
cd /path/to/<one-instance>
bash ops/agent/update.sh          # git pull + rebuild + 重启隧道 + verify,全自动
```

`update.sh` 会自己从 `.env` 推导 `INSTANCE_NAME`/端口/域名/隧道名,跑完自动 `verify.sh`
(本地 + 公网)。这一步过了,再放心铺开。

**③ 再滚全 fleet。**

```bash
bash ops/fleet/all.sh update ops/fleet/instances.csv
```

`all.sh update` 逐行 `cd` 进各实例目录调 `ops/agent/update.sh`,per-row 失败不中断、末尾出汇总表、
有失败则整体退出码非零。哪台失败看日志单独处理。

### 关键 gotcha:容器重建后必须重启 cloudflared

每次 `docker compose up -d --build` **重建**容器 → 容器 IP 变,但 cloudflared 缓存旧 IP,
公网会 **502/530**,而本机 `:port` 却仍是 200(所以"本地通"不能证明"公网通")。

**`ops/agent/update.sh` 已经封装了这一步**(重建后 `docker restart <tunnel>-cloudflared`
再 verify),所以只要走 `update.sh` / `all.sh update` 就无需手动重启。只有当你**手动**
`docker compose up` 绕过 update.sh 时,才要自己补:

```bash
docker restart <tunnel>-cloudflared     # <tunnel> 默认 == INSTANCE_NAME
```

> **串行,别并行。** `next build` 峰值 1.5GB+,`all.sh update` 特意一台一台来。别在小 VM 上
> 把它并行化,否则 OOM(见 `docs/multi-instance.md` 内存注意)。

---

## 5. 事故处理 playbook

面板/告警报了 DOWN 或 WARN,按症状对号入座。命令里 `<inst>` = 实例名/目录名/compose project,
`<tunnel>` = 隧道前缀(默认 == `<inst>`)。

### 5.1 站点 502 / 530(本地通、公网挂)

- **症状**:面板 `SITE` 或 `API` = down;`OVERALL=DOWN`;本机 `curl 127.0.0.1:<port>` 却 200。
- **诊断**:典型是隧道连接器缓存了旧容器 IP(刚重建过容器),或连接器没在跑。
- **修复**:

```bash
docker restart <tunnel>-cloudflared
cd /path/to/<inst> && SITE_DOMAIN=<site> API_DOMAIN=<api> bash ops/agent/verify.sh
# 或用 fleet 复查这一台:
bash ops/fleet/all.sh verify ops/fleet/instances.csv
```

  若刚部署/改过域名,可能是 DNS 还在传播,等 ~1 分钟再 verify。

### 5.2 容器挂了(CONT 不满)

- **症状**:面板 `CONT` 显示 `3/4` 之类;`OVERALL=DOWN`。
- **诊断**:进目录看哪个服务没起、为什么。

```bash
cd /path/to/<inst>
docker compose -p <inst> ps
docker compose -p <inst> logs --tail=100 <service>   # backend / frontend / postgres / …
```

- **修复**:把该 project 拉起来(幂等,不重建不丢数据):

```bash
docker compose -p <inst> up -d
docker restart <tunnel>-cloudflared     # 若上一步重建了容器,补隧道重启
```

### 5.3 数据库坏了 / 误删数据(从最近快照恢复)

- **症状**:`PAGES=?` 持续、后台报 DB 错、或客户反馈内容/媒体丢了。
- **诊断**:先确认 postgres 容器在跑(5.2);确认这是数据问题而非容器问题。
- **修复(破坏性,会覆盖线上库和媒体卷)**:先留一份"当前状态"再恢复,然后从最近快照灌回。

```bash
# 0) 先备份当前状态(哪怕已经坏了,也留个现场)
cd /path/to/<inst> && bash ops/backup/backup.sh

# 1) 找最近的快照目录
ls -1dt ~/backups/<inst>/*/ | head

# 2) 从该快照恢复(不带 --yes 会要你手打实例名确认)
bash ops/backup/restore.sh <inst> ~/backups/<inst>/<YYYY-MM-DD_HHMMSS>

# 3) 恢复后前端没即时看到媒体就重启 backend
docker compose -p <inst> restart backend
```

  细节见 [`ops/backup/README.md`](../ops/backup/README.md)。**每季度**用同样流程做一次恢复
  演练(恢复到临时实例名后 `verify.sh` 过一遍),证明备份真的能用。

### 5.4 admin token 过期(需要长效的重发一枚)

- **症状**:`/api/admin/*` 返回 401/403;`homestead-site-*` 技能或后台操作失败。
- **修复**:进该实例目录、在 backend 容器里重发,`--days` 给一个长效期:

```bash
cd /path/to/<inst>
docker compose -p <inst> exec -T backend \
  flask --app app.main token issue --email you@example.com --days 365 | tail -n 1 | tr -d '\r'
```

  email 必须在该实例 `backend/.env` 的 `ADMIN_EMAILS` 里。批量给每台各发一枚可用
  `bash ops/fleet/all.sh token ops/fleet/instances.csv`(不带 `--days`,按需自行加长效)。

### 5.5 磁盘满

- **症状**:备份/构建失败报 no space;`df -h` 快满。
- **诊断**:

```bash
df -h
du -sh ~/backups/*/ | sort -h        # 哪些实例备份占得多
docker system df                     # docker 层/卷/构建缓存占用
```

- **修复**:先清旧备份(`backup.sh` 有 `KEEP` 保留份数,过多是保留期太长),再清 docker 垃圾:

```bash
# 收紧保留份数(下次备份即生效),或手删过老的快照目录
rm -rf ~/backups/<inst>/<老快照目录>

# 清理悬空镜像/停止容器/构建缓存(不动运行中的容器与命名卷)
docker system prune -f
docker builder prune -f
```

  **不要** `docker system prune --volumes`,那会删命名卷(含数据库/媒体)。长期方案:异地备份
  (rclone,见 backup README)+ 收紧 `KEEP`。

### 5.6 consistency 不 ok(通常是 rebrand / 导入后)

- **症状**:`GET /api/admin/consistency` 返回 `ok:false`,`findings` 里列出不一致
  (常见于换行业 rebrand 或导入 site pack 后)。
- **诊断**:带 admin token 查(token 见 5.4):

```bash
cd /path/to/<inst>
TOKEN=$(docker compose -p <inst> exec -T backend flask --app app.main token issue --email you@example.com | tail -n1 | tr -d '\r')
curl -s http://127.0.0.1:<backend_port>/api/admin/consistency -H "Authorization: Bearer $TOKEN"
# -> {"ok":false,"findings":[...],"summary":{...}}
```

- **修复**:按 `findings` 逐项修(rebrand 后按提示补齐 NAP / 图片占位 / 缺失段落等),
  **循环修到 `ok:true`**:每修一轮就重查一次 consistency,直到 `ok:true` 且 `findings` 为空。

---

## 6. 容量规划:一台主机能跑几个实例

粗略拍板(数据来自 `docs/multi-instance.md`,按你机器实际内存收紧):

- **常驻内存**:每实例约 **500MB**(postgres + backend + frontend + cloudflared)。
- **构建内存**:`next build` 峰值 **1.5GB+**,而且**同一时刻只应有一个前端在 build**
  (`all.sh update` 已串行)。所以要给"构建余量"留出 **~1.5–2GB** 不被常驻占满。
- **端口**:每实例占一组 `127.0.0.1` 端口,`13000/18000` 起 +10;够用不是瓶颈,但 CSV 要登记
  别撞。

**粗算上限**:`可跑实例数 ≈ (总内存 − 构建余量 ~2GB) / 0.5GB`,再往下砍留安全边际。例如一台
4GB 机:`(4 − 2) / 0.5 = 4`,保守跑 **2–3 个**实例较稳;8GB 机保守 **6–8 个**。低配
1–2GB 机基本只够 1 个 + swap。

**超了怎么办 —— 加机器,fleet 天然跨主机。** `instances.csv` 只是"这台机器上有哪些站"的清单:

- 每台主机各自维护自己的 `instances.csv`,只列住在本机的实例;
- fleet 命令(`status`/`update`/`backup`/…)**在每台机器上各跑一遍**(逐台 ssh 进去跑,或各机
  各装自己的 timer);
- 备份/面板/告警也各机独立装。没有中央调度,横向扩展就是"多几台、每台一份 CSV + 一套 timer"。

---

## 7. 新站接入 fleet

部署一个新客户(`ops/agent/deploy.sh`,见 [`AGENT-DEPLOY.md`](../AGENT-DEPLOY.md) /
[`docs/deploy-new-instance.md`](deploy-new-instance.md))之后,**三步**把它纳入日常维护,别让它
成为"没人管的站":

**① 加进 fleet 注册表 `instances.csv`。** 用部署时导出的同一批值追加一行(列顺序:
`instance,dir,site_domain,api_domain,tunnel_name,frontend_port,backend_port`):

```csv
homestead-acme,/home/borui/homestead-acme,acme.example.com,acme-api.example.com,homestead-acme,13010,18010
```

端口必须和该实例 `.env` 里 `make-env.sh` 写的一致(那是 `verify`/`status` 探测的对象)。
加完立刻验证它进了 fleet 视野:

```bash
bash ops/fleet/all.sh status ops/fleet/instances.csv     # 新行应出现,OVERALL 应为 OK
```

**② 纳入每日备份 timer。** 给它写一份环境文件并 enable 对应 timer(细节见
[`ops/backup/README.md`](../ops/backup/README.md)):

```bash
printf 'REPO_ROOT=%s\nKEEP=7\n' /home/borui/homestead-acme \
  | sudo tee /etc/homestead/backup-homestead-acme.env
sudo systemctl enable --now homestead-backup@homestead-acme.timer
```

**③ 纳入面板 / 告警。** 面板与告警是**host 级、读整份 CSV**的一个 job —— 只要新站已经在
`instances.csv` 里(第①步),`homestead-fleet-status.timer` 下一轮就会自动带上它,**无需**为
新站单独装什么。若这台机器还没装过 fleet 面板/告警 timer,按 §2 / `ops/fleet/README.md` 装一次
即可(整台机器只装一次)。

至此新站进入日常节奏:面板会盯它、告警会报它、备份会护它、下次 `all.sh update` 会更它。
