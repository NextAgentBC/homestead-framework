# 备份 / 恢复(ops/backup)

给付费客户的数据兜底:**每个实例**的 Postgres 数据库 + 上传媒体(named volume)每日打包
到磁盘,可一键恢复。丢数据 = 商业事故,所以脚本 `set -euo pipefail`、每步回显、失败即
中止(绝不留半份备份)。

- `backup.sh` —— 对一个实例做 pg_dump(gzip)+ media 卷 tarball,按天存,自动保留最近 N 份。
- `restore.sh` —— 从某个快照目录灌回数据库和媒体卷(**会覆盖线上数据**,需二次确认)。
- `homestead-backup.service` / `.timer` —— systemd 模板单元,每日自动跑 `backup.sh`。

## 关键约定(和仓库其它部分一致)

- **实例 = clone 目录名 = compose project 名 = `INSTANCE_NAME`**(见 `docs/multi-instance.md`)。
- 数据库凭据从**该实例目录的 `.env`** 读 `POSTGRES_USER` / `POSTGRES_DB`;读不到时回退到
  `docker-compose.yml` 的默认值 `homestead_site` / `homestead_site`。
- **媒体卷命名 = `<compose project>_media-data`**。因为 `ops/agent/deploy.sh` 用
  `docker compose -p "$INSTANCE_NAME"`,所以卷名就是 `<INSTANCE_NAME>_media-data`。
  本机实测存在的卷:`vanwashpro-preview_media-data`(实例 `vanwashpro-preview`)。
- pg_dump 在 **postgres 容器内**跑(`docker compose -p <inst> exec -T postgres pg_dump …`),
  宿主机无需装 psql 客户端。

产物目录结构:

```
~/backups/<instance>/<YYYY-MM-DD_HHMMSS>/
  ├── db.sql.gz       # pg_dump | gzip
  ├── media.tar.gz    # media 卷内容 tar
  └── MANIFEST.txt    # 实例/时间/user/db/卷名,供恢复核对
```

## 手动备份

```bash
# 在实例的 clone 目录里(自动从 .env 取 INSTANCE_NAME / 凭据):
bash ops/backup/backup.sh

# 或显式指定实例名 + 覆盖默认:
BACKUP_DIR=/data/backups KEEP=14 bash ops/backup/backup.sh vanwashpro-preview
```

可调环境变量:`BACKUP_DIR`(默认 `~/backups`)、`KEEP`(保留份数,默认 `7`)。

## 恢复(演练!)

**恢复会覆盖线上库和媒体卷。** 正式恢复前请先跑一次 `backup.sh` 留一份"当前状态"再操作。

```bash
# <实例名> <快照目录> [--yes]
bash ops/backup/restore.sh vanwashpro-preview ~/backups/vanwashpro-preview/2026-07-02_031500
```

- 不带 `--yes` 会要求你**手动输入实例名**确认;自动化里加 `--yes` 跳过。
- DB 恢复:DROP + CREATE 目标库,再 `gunzip -c db.sql.gz | psql`(`ON_ERROR_STOP=1`)。
- 媒体恢复:先清空卷,再把 `media.tar.gz` 解回去。
- 恢复后若前端未即时看到媒体:`docker compose -p <实例> restart backend`。

**建议每季度做一次恢复演练**(恢复到一个临时实例名,`verify.sh` 过一遍),证明备份真的能用。

## 用 systemd 自动化(每日)

模板单元用 `%i` 参数化实例名。每个实例需要一个环境文件告诉单元 clone 在哪:

```bash
sudo mkdir -p /etc/homestead
# 为实例 vanwashpro-preview 写环境文件(REPO_ROOT 必填;BACKUP_DIR/KEEP 可选):
printf 'REPO_ROOT=%s\nKEEP=7\n' /home/borui/homestead-vanwashpro-preview \
  | sudo tee /etc/homestead/backup-vanwashpro-preview.env
```

### 系统级(推荐,root 有 docker 权限)

```bash
sudo cp ops/backup/homestead-backup.service /etc/systemd/system/homestead-backup@.service
sudo cp ops/backup/homestead-backup.timer   /etc/systemd/system/homestead-backup@.timer
sudo systemctl daemon-reload
sudo systemctl enable --now homestead-backup@vanwashpro-preview.timer

# 检查 / 立刻跑一次 / 看日志:
systemctl list-timers 'homestead-backup@*'
sudo systemctl start homestead-backup@vanwashpro-preview.service   # 手动触发一次
journalctl -u homestead-backup@vanwashpro-preview.service -n 50
```

> 系统级单元里 `%h` = root 家目录、`~/backups` = `/root/backups`。想把备份放到某用户目录,
> 在环境文件里设 `BACKUP_DIR=/home/borui/backups`。

### 用户级(rootless docker,或用户在 docker 组)

```bash
mkdir -p ~/.config/systemd/user
cp ops/backup/homestead-backup.service ~/.config/systemd/user/homestead-backup@.service
cp ops/backup/homestead-backup.timer   ~/.config/systemd/user/homestead-backup@.timer
# 环境文件路径 /etc/homestead/backup-%i.env 仍需 root 建(或把单元里的路径改到 ~/.config)。
systemctl --user daemon-reload
systemctl --user enable --now homestead-backup@vanwashpro-preview.timer
loginctl enable-linger "$USER"     # 关键:没登录时也让 --user 定时器继续跑
```

多实例:每个实例各写一份 `/etc/homestead/backup-<inst>.env`,再 `enable` 对应的
`homestead-backup@<inst>.timer` 即可;timer 带 `RandomizedDelaySec=1800`,避免同机多实例同时 dump。

## 不想用 systemd?一行 cron 替代

```cron
# 每天 03:15 备份 vanwashpro-preview,日志追加到文件
15 3 * * * cd /home/borui/homestead-vanwashpro-preview && BACKUP_DIR=$HOME/backups KEEP=7 bash ops/backup/backup.sh vanwashpro-preview >> $HOME/backups/backup.log 2>&1
```

## 异地备份(可选,强烈建议)

本地磁盘挂了本地备份也没了。用 [`rclone`](https://rclone.org/) 把 `~/backups` 同步到对象存储
(S3 / R2 / B2 / GDrive 等),在 `backup.sh` 之后再跑一步即可:

```bash
# 一次性配置远端: rclone config   (假设远端名叫 offsite)
# 每次备份后同步(可加到 cron 那行末尾,或包一个 wrapper):
rclone sync "$HOME/backups" offsite:homestead-backups --fast-list
```

也可用 `rclone` 的 `--backup-dir` / 版本化桶保留历史;敏感数据建议开 `crypt` 远端做端到端加密。
