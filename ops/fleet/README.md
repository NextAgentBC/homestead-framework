# Fleet ops — run one action across every instance

Once a host carries more than a handful of customer sites, doing `update` / `verify` /
`backup` by hand on each clone stops scaling (and it's how you forget one). `all.sh` reads a
CSV registry of the instances on this host and fans a single action out over all of them,
then prints a pass/fail table.

This builds directly on the per-instance conventions in
[`docs/multi-instance.md`](../../docs/multi-instance.md): one clone dir per customer, dir
name == `INSTANCE_NAME` == compose project, a shared `edge` network, an independent tunnel
per instance, and staggered `127.0.0.1` ports (13000/18000, +10 per instance).

## Quick start

```bash
cp ops/fleet/instances.example.csv ops/fleet/instances.csv   # your real registry
$EDITOR ops/fleet/instances.csv                              # one row per customer

bash ops/fleet/all.sh verify  ops/fleet/instances.csv   # reachability of every site (read-only)
bash ops/fleet/all.sh update  ops/fleet/instances.csv   # git pull + rebuild + retunnel + verify, each
bash ops/fleet/all.sh backup  ops/fleet/instances.csv   # pg dump + media tar, each
bash ops/fleet/all.sh token   ops/fleet/instances.csv   # mint a fresh admin token, each
```

Exit code is non-zero if **any** instance failed the action, but the batch always finishes
every row first (a broken instance never stops the others). Good for an unattended cron/CI
run: it touches all instances and still signals overall health.

## The CSV registry

Header + `#`-comment lines are skipped; every other line is one instance. Columns, in order:

| column | meaning |
|---|---|
| `instance` | compose project name == clone dir name == `INSTANCE_NAME` |
| `dir` | absolute path to that clone directory (`all.sh` `cd`s here) |
| `site_domain` | public site hostname (for `verify`/`update`) |
| `api_domain` | public API hostname (for `verify`/`update`) |
| `tunnel_name` | cloudflared connector prefix (usually == `instance`) |
| `frontend_port` | host-published `127.0.0.1` port (13000+, +10/instance) |
| `backend_port` | host-published `127.0.0.1` port (18000+, +10/instance) |

Maintenance:

- **Add a customer** when you deploy them (`ops/agent/deploy.sh`): append a row with the
  same `INSTANCE_NAME`, ports, and domains you exported for that deploy.
- **Remove a customer** when you decommission the clone. Do a final `backup` first.
- **Keep it out of git.** The domains are fine, but this file is the single list of who
  lives on the box — treat it as ops state, not source. `instances.example.csv` is the only
  version that belongs in the repo.
- Ports must match each instance's `.env` (that's what `verify`/`update` probe on
  `127.0.0.1`); the source of truth is what `make-env.sh` wrote — the CSV just mirrors it.

## What each action runs

`all.sh` doesn't re-implement anything — it `cd`s into each row's `dir` and calls the same
scripts you'd run by hand, with that row's env prefilled:

| action | per-instance call | env passed |
|---|---|---|
| `update` | `ops/agent/update.sh` | `INSTANCE_NAME TUNNEL_NAME SITE_DOMAIN API_DOMAIN FRONTEND_PORT BACKEND_PORT` |
| `verify` | `ops/agent/verify.sh` | `SITE_DOMAIN API_DOMAIN FRONTEND_PORT BACKEND_PORT` |
| `backup` | `ops/backup/backup.sh <instance>` | `INSTANCE_NAME` |
| `token`  | `docker compose -p <instance> exec backend flask … token issue` | — |

`backup` needs the `ops/backup` toolchain present in this clone; if it's missing, `all.sh`
says so up front instead of failing per-row.

> **Serialize the heavy ones.** `next build` peaks at 1.5 GB+, so `update` deliberately runs
> one instance at a time (see the memory note in `docs/multi-instance.md`). Don't wrap
> `all.sh update` in something that parallelizes the rows on a small VM — you'll OOM.

## Topology: one gateway for all sites, or one per customer?

The per-site containers (postgres/backend/frontend/cloudflared) are always isolated per
instance — that part isn't a choice. The decision is about the **OpenClaw gateway** that
answers the live-chat widget (the tool-less brain behind
[`ops/webchat-bridge`](../webchat-bridge/README.md)), which comes in the three forms that
README describes: no chat, shared brain, or dedicated brain. At fleet scale that collapses
to two real topologies:

### A. Single shared gateway (default, cheapest)

One `openclaw` gateway + one `webchat-bridge` on the host; every instance's backend calls
the same `host.docker.internal:18791`. The bridge is tool-less and each turn's prompt is
assembled by that instance's backend from **only that site's public knowledge**, so sites
stay isolated at the prompt level even though they share the model runner.

- **Pros:** one gateway to run/update/watch; lowest RAM; one Telegram operator inbox.
- **Cons:** shared model config (one `WEBCHAT_MODEL`/thinking level for all); one bridge
  restart briefly affects every site's chat; all mirrors land in one operator chat unless
  you set per-instance `WEBCHAT_TG_TARGET`.
- **Use when:** you run all the sites yourself and want the least moving parts.

### B. Per-customer gateway (isolated)

A separate gateway + bridge (own port, own token, own Telegram target) per customer, each
under its own Linux user/linger. Fully independent chat brains.

- **Pros:** blast-radius isolation; per-customer model choice, quotas, and operator inbox;
  a customer can even own their own gateway credentials.
- **Cons:** N gateways to install/update/heal and N services' RAM; more `systemd --user`
  units and firewall rules to keep straight.
- **Use when:** customers need isolated model config/billing, separate operators, or a hard
  data-boundary promise.

`all.sh` is agnostic to this choice — it drives the **website** lifecycle (deploy artifacts,
health, backups, tokens). The gateway/bridge topology is a separate host-service decision;
whichever you pick, the per-site website ops are the same rows in this CSV.
