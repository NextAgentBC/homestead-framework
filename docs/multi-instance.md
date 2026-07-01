# 同一主机跑多个客户实例(multi-instance)

一台服务器交付 N 个客户站的约定。核心思路:**每个客户一个独立 clone 目录**,互不共享数据库、
env 和容器;只共享一个 `edge` Docker 网络(给各自的 Cloudflare 隧道用)。

## 约定

### 1. 每客户一个 clone,目录名 = INSTANCE_NAME = compose project 名

```bash
git clone https://github.com/NextAgentBC/homestead-framework.git homestead-acme
cd homestead-acme
export INSTANCE_NAME=homestead-acme    # 与目录名一致,好记好查
```

`INSTANCE_NAME` 同时决定:

| 用途 | 值 |
|---|---|
| compose project(deploy.sh 自动传 `-p`) | `$INSTANCE_NAME` |
| `edge` 网络上的服务别名 | `$INSTANCE_NAME-frontend` / `$INSTANCE_NAME-backend` |
| 隧道名与连接器容器名(默认) | `$INSTANCE_NAME` / `$INSTANCE_NAME-cloudflared` |

不设 `INSTANCE_NAME` 时一切退回单实例默认值(`homestead-site-*` 别名、目录名做 project),
老部署不受影响。

### 2. 端口分配:13000/18000 起,每实例 +10

宿主机端口只绑 `127.0.0.1`(公网走隧道),仅供本机调试,但仍不能撞。建议按表登记:

| 实例 | FRONTEND_PORT | BACKEND_PORT | POSTGRES_PORT |
|---|---|---|---|
| 第 1 个客户 | 13000 | 18000 | 55434 |
| 第 2 个客户 | 13010 | 18010 | 55444 |
| 第 3 个客户 | 13020 | 18020 | 55454 |
| …每实例 | +10 | +10 | +10 |

(默认 3000/8000/55433 留给本机开发实例。)三个端口变量 export 后由
`make-env.sh` 写进各自目录的 `.env`,`verify.sh`/`deploy.sh` 会读同名变量。

### 3. `edge` 网络共享,隧道每实例独立

- `docker network create edge` 全机只建一次(deploy.sh 幂等处理)。
- 每个实例自己的 cloudflared 连接器(`<INSTANCE_NAME>-cloudflared`)也挂在 `edge` 上,
  按别名路由到自己的 frontend/backend——别名含实例名,不会串站。
- 老 gotcha 不变:某实例 `compose up` 重建容器后,重启**该实例**的连接器即可
  (`bash ops/agent/update.sh` 已包含)。

### 4. 一条命令部署第 N 个客户

```bash
cd homestead-acme
export SITE_DOMAIN=acme.example.com API_DOMAIN=acme-api.example.com ADMIN_EMAIL=you@example.com
export CF_API_TOKEN=… CF_ACCOUNT_ID=…
export INSTANCE_NAME=homestead-acme FRONTEND_PORT=13010 BACKEND_PORT=18010 POSTGRES_PORT=55444
export SITE_INDUSTRY=construction     # 客户行业,首启即 seed 对的模板
bash ops/agent/deploy.sh
```

## 机器资源注意

- **前端构建吃内存**:`next build` 峰值 1.5GB+,低配 VM(1–2GB)容易 OOM 卡死。
  建议 2GB 内存 + 2GB swap 起步;多实例**串行**部署/更新,不要同时 build 两个前端。
- 每实例常驻约 500MB(postgres + backend + frontend + cloudflared);按机器内存算上限,
  留 1GB 余量给构建。
- 数据库和上传媒体在每实例自己的 named volume(project 名做前缀),互不可见;
  备份也按实例目录分开做。
