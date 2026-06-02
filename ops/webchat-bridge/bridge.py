#!/usr/bin/env python3
"""Webchat bridge — the host-side glue between the (containerized) website backend
and the OpenClaw gateway.

Why it exists: the Flask backend runs in Docker; the `openclaw` CLI + gateway live
on the host. This tiny service is the bridge the container calls (over
host.docker.internal) to (a) get a reply from a SANDBOXED, TOOL-LESS model turn and
(b) mirror each visitor exchange to the operator's Telegram.

Security model — the chat brain is `openclaw infer model run` (a one-shot model
completion), NOT the agent harness. There is therefore **no tool surface at all**:
shell, file, message-send, money skills are simply not reachable. A visitor can type
anything; the worst case is the model emits some text. The prompt (assembled by the
backend) contains only public site knowledge + this visitor's own conversation — no
private memory or files. Access to this service is gated by a shared bearer token.

Stdlib only (no pip deps) so it can run straight off the host Python.
"""
import json
import os
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.environ.get("WEBCHAT_BRIDGE_PORT", "18791"))
BRIDGE_TOKEN = os.environ.get("WEBCHAT_BRIDGE_TOKEN", "")
MODEL = os.environ.get("WEBCHAT_MODEL", "gpt-5.4-mini")
THINKING = os.environ.get("WEBCHAT_THINKING", "minimal")
TIMEOUT = int(os.environ.get("WEBCHAT_TIMEOUT", "90"))
TG_TARGET = os.environ.get("WEBCHAT_TG_TARGET", "")  # operator chat id; "" disables mirror
MIRROR = os.environ.get("WEBCHAT_MIRROR", "1") not in ("0", "false", "")
OPENCLAW = os.environ.get("OPENCLAW_BIN", "openclaw")

MAX_PROMPT = 24000  # hard cap on assembled prompt chars (defense-in-depth)
MAX_MSG = 2000


def run_model(prompt: str) -> str:
    """One-shot, tool-less completion via the gateway (uses gateway provider creds)."""
    args = [OPENCLAW, "infer", "model", "run", "--gateway", "--json"]
    # The gateway restricts model overrides per agent; "default"/"" => use the
    # gateway's default model (no --model). Set a specific id only if allowed.
    if MODEL and MODEL != "default":
        args += ["--model", MODEL]
    if THINKING:
        args += ["--thinking", THINKING]
    args += ["--prompt", prompt[:MAX_PROMPT]]
    proc = subprocess.run(args, capture_output=True, text=True, timeout=TIMEOUT)
    if proc.returncode != 0:
        raise RuntimeError(f"infer exited {proc.returncode}: {proc.stderr[:300]}")
    data = json.loads(proc.stdout)
    outs = data.get("outputs") or []
    text = (outs[0].get("text") if outs else "") or ""
    return text.strip()


def mirror_telegram(session: str, message: str, reply: str) -> None:
    if not (MIRROR and TG_TARGET):
        return
    note = (f"🌐 网站访客\n"
            f"👤 {message[:600]}\n\n"
            f"🤖 小爪：{reply[:1200]}\n\n"
            f"↩️ 接管回复用 session：{session}")
    subprocess.run(
        [OPENCLAW, "message", "send", "--channel", "telegram", "--target", TG_TARGET, "--message", note],
        capture_output=True, text=True, timeout=30,
    )


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, obj: dict) -> None:
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            return self._send(200, {"ok": True, "model": MODEL, "mirror": bool(MIRROR and TG_TARGET)})
        self._send(404, {"error": "not found"})

    def do_POST(self):
        if self.path not in ("/chat", "/notify"):
            return self._send(404, {"error": "not found"})
        if BRIDGE_TOKEN and self.headers.get("X-Bridge-Token") != BRIDGE_TOKEN:
            return self._send(401, {"error": "unauthorized"})
        try:
            length = int(self.headers.get("Content-Length") or 0)
            data = json.loads(self.rfile.read(length) or b"{}")
        except Exception:
            return self._send(400, {"error": "bad json"})

        # /notify — mirror-only Telegram ping (no model turn); used by the contact form.
        if self.path == "/notify":
            text = (data.get("text") or "").strip()
            if not text:
                return self._send(400, {"error": "text required"})
            ok = True
            try:
                if MIRROR and TG_TARGET:
                    subprocess.run(
                        [OPENCLAW, "message", "send", "--channel", "telegram",
                         "--target", TG_TARGET, "--message", text[:3500]],
                        capture_output=True, text=True, timeout=30,
                    )
            except Exception as exc:
                ok = False
                self.log_error("notify error: %s", str(exc)[:200])
            return self._send(200, {"ok": ok})

        prompt = (data.get("prompt") or "").strip()
        session = (str(data.get("sessionId") or "anon"))[:64]
        visitor_message = (data.get("visitorMessage") or "")[:MAX_MSG]
        if not prompt:
            return self._send(400, {"error": "prompt required"})

        try:
            reply = run_model(prompt)
        except subprocess.TimeoutExpired:
            return self._send(200, {"reply": "抱歉，我这边响应有点慢，请再发一次或稍后重试 🙏", "degraded": True})
        except Exception as exc:
            self.log_error("model error: %s", str(exc)[:200])
            return self._send(200, {"reply": "抱歉，我暂时无法回复。你可以留下邮箱，我们会尽快联系你。", "degraded": True})

        if not reply:
            reply = "抱歉，我没太理解，可以换种说法吗？或者留下邮箱让我们联系你。"

        try:
            mirror_telegram(session, visitor_message or "(无文本)", reply)
        except Exception as exc:
            self.log_error("mirror error: %s", str(exc)[:200])

        self._send(200, {"reply": reply})

    def log_message(self, *args):  # quiet; systemd captures stderr only
        pass


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"webchat-bridge listening on :{PORT} model={MODEL} mirror={bool(MIRROR and TG_TARGET)}", flush=True)
    server.serve_forever()
