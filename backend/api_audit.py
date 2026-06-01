"""Full API smoke test (in-process, scratch DB — does not touch live data).
Run from backend/:  DATABASE_URL=sqlite:////tmp/audit.db ADMIN_EMAILS=a@test.com \
  SITE_LOCALES=en,zh MEDIA_DIR=/tmp/media python api_audit.py
Exits non-zero if any check fails. pytest ignores it (no test_ prefix)."""
import os, sys
os.environ.setdefault("MEDIA_DIR", "/tmp/media_audit")
from app.main import create_app
from app.extensions import db
from app.models import User
from app.auth import issue_jwt

app = create_app()
with app.app_context():
    db.create_all()
    u = User(email="admin@test.com", google_sub="cli:a", name="A", role="admin")
    db.session.add(u); db.session.commit()
    TOKEN = issue_jwt(u)

c = app.test_client()
H = {"Authorization": f"Bearer {TOKEN}"}
R = []
def chk(name, cond, d=""):
    R.append((bool(cond), name, "" if cond else d))
def j(resp):
    try: return resp.get_json() or {}
    except Exception: return {}

# ---------- PUBLIC ----------
r=c.get("/api/health");            chk("GET /health", r.status_code==200 and j(r).get("status")=="ok", str(r.status_code))
r=c.get("/api/site");             it=j(r).get("item",{}); chk("GET /site", r.status_code==200 and it.get("name") and it.get("locales"), str(r.status_code))
r=c.get("/api/design");           chk("GET /design", r.status_code==200 and "tokens" in j(r).get("item",{}), str(r.status_code))
r=c.get("/api/design?locale=zh"); chk("GET /design?locale=zh", r.status_code==200, str(r.status_code))
r=c.get("/api/blocks");           ty=[b["type"] for b in j(r).get("items",[])]; chk("GET /blocks (15 types)", r.status_code==200 and len(ty)==15 and {"steps","gallery","team","banner","section"} <= set(ty), f"{len(ty)} types")
r=c.get("/api/patterns");         chk("GET /patterns", r.status_code==200 and "items" in j(r), str(r.status_code))
r=c.get("/api/openapi.json");     chk("GET /openapi.json", r.status_code==200 and "paths" in j(r), str(r.status_code))
r=c.get("/api/i18n/zh");          chk("GET /i18n/zh", r.status_code==200 and j(r)["item"]["locale"]=="zh", str(r.status_code))
r=c.post("/api/auth/google", json={}); chk("POST /auth/google (bad)->400", r.status_code==400, str(r.status_code))
r=c.post("/api/newsletter/subscribe", json={"email":"a@b.com"}); chk("POST /newsletter/subscribe", r.status_code==200, str(r.status_code))
r=c.post("/api/contact", json={"email":"a@b.com","message":"hi"}); chk("POST /contact", r.status_code==200, str(r.status_code))
r=c.get("/api/blogs");            chk("GET /blogs (empty)", r.status_code==200 and j(r)["items"]==[], str(r.status_code))
r=c.get("/api/pages");            chk("GET /pages (empty)", r.status_code==200, str(r.status_code))
r=c.get("/api/blogs/nope");       chk("GET /blogs/<missing>->404", r.status_code==404, str(r.status_code))

# media serve: drop a file into the configured MEDIA_DIR, serve it
_MEDIA=app.config["MEDIA_DIR"]; os.makedirs(_MEDIA, exist_ok=True)
open(os.path.join(_MEDIA,"t.png"),"wb").write(b"\x89PNG\r\n\x1a\n"+b"0"*32)
r=c.get("/api/media/t.png");      chk("GET /media/<file>", r.status_code==200, str(r.status_code))
r=c.get("/api/media/missing.png");chk("GET /media/<missing>->404", r.status_code==404, str(r.status_code))

# ---------- ADMIN: auth gate ----------
r=c.get("/api/admin/design");     chk("admin without token -> 401", r.status_code==401, str(r.status_code))
r=c.get("/api/admin/design", headers={"Authorization":"Bearer bad"}); chk("admin bad token -> 401", r.status_code==401, str(r.status_code))

# ---------- ADMIN: design ----------
r=c.get("/api/admin/design", headers=H); chk("GET /admin/design", r.status_code==200, str(r.status_code))
r=c.post("/api/admin/design/generate", json={"preset":"neon"}, headers=H); chk("POST /admin/design/generate {neon}", r.status_code==200 and "neon" in j(r)["item"]["source"], str(r.status_code))
r=c.patch("/api/admin/design", json={"tokens":{"colors":{"primary":"#123456"}}}, headers=H); chk("PATCH /admin/design (token merge)", r.status_code==200 and j(r)["item"]["tokens"]["colors"]["primary"]=="#123456", str(r.status_code))
r=c.post("/api/admin/design/analyze-competitors", json={"industry":"tech","competitorUrls":["https://example.com"],"observations":[{"url":"https://example.com","colors":["#0f172a"],"fonts":["Inter"]}],"notes":"test"}, headers=H); chk("POST /admin/design/analyze-competitors", r.status_code==200, str(r.status_code))

# ---------- ADMIN: blogs ----------
r=c.post("/api/admin/blogs", json={"title":"Audit Post","body_markdown":"# Audit\n\nbody","status":"published"}, headers=H)
bid=j(r).get("item",{}).get("id"); bslug=j(r).get("item",{}).get("slug"); chk("POST /admin/blogs", r.status_code==201 and bid, str(r.status_code))
r=c.patch(f"/api/admin/blogs/{bid}", json={"excerpt":"new excerpt"}, headers=H); chk("PATCH /admin/blogs/{id}", r.status_code==200, str(r.status_code))
r=c.patch(f"/api/admin/blogs/{bid}?locale=zh", json={"title":"中文标题"}, headers=H); chk("PATCH /admin/blogs/{id}?locale=zh", r.status_code==200, str(r.status_code))
r=c.get(f"/api/blogs/{bslug}?locale=zh"); chk("blog zh reflects translation", r.status_code==200 and j(r)["item"]["title"]=="中文标题", str(j(r).get('item',{}).get('title')))
r=c.post("/api/admin/blogs/generate", json={"topic":"education"}, headers=H); chk("POST /admin/blogs/generate (fallback)", r.status_code==200 and j(r)["item"]["title"], str(r.status_code))

# ---------- ADMIN: pages ----------
r=c.post("/api/admin/pages", json={"title":"About","slug":"about","sections":[{"type":"hero","content":{"headline":"Hi"}}],"status":"published"}, headers=H)
pid=j(r).get("item",{}).get("id"); chk("POST /admin/pages", r.status_code==201 and pid, str(r.status_code))
r=c.patch(f"/api/admin/pages/{pid}", json={"nav_label":"About us"}, headers=H); chk("PATCH /admin/pages/{id}", r.status_code==200, str(r.status_code))
r=c.get("/api/pages/about"); chk("GET /pages/about (published)", r.status_code==200, str(r.status_code))
r=c.post("/api/admin/pages", json={"title":"Bad","slug":"blog"}, headers=H); chk("POST /admin/pages reserved slug -> 400", r.status_code==400, str(r.status_code))

# ---------- ADMIN: compose ----------
r=c.get("/api/admin/surfaces", headers=H); chk("GET /admin/surfaces", r.status_code==200 and "items" in j(r), str(r.status_code))
r=c.get("/api/admin/compose/home/blocks", headers=H); chk("GET compose/home/blocks", r.status_code==200, str(r.status_code))
ids={}
for t in ["steps","gallery","team","banner"]:
    r=c.post("/api/admin/compose/home/blocks", json={"type":t}, headers=H)
    ids[t]=j(r).get("item",{}).get("id"); chk(f"compose add '{t}'", r.status_code==201 and j(r)["item"]["type"]==t, str(r.status_code))
r=c.patch(f"/api/admin/compose/home/blocks/{ids['steps']}", json={"content":{"heading":"X"}}, headers=H); chk("compose update", r.status_code==200, str(r.status_code))
r=c.post(f"/api/admin/compose/home/blocks/{ids['steps']}/move", json={"position":"start"}, headers=H); chk("compose move", r.status_code==200, str(r.status_code))
r=c.post(f"/api/admin/compose/home/blocks/{ids['team']}/duplicate", headers=H); chk("compose duplicate", r.status_code==201, str(r.status_code))
r=c.post("/api/admin/compose/home/batch", json={"ops":[{"op":"add","type":"banner"},{"op":"add","type":"faq"}]}, headers=H); chk("compose batch (atomic)", r.status_code==200 and j(r)["item"]["applied"]==2, str(r.status_code))
r=c.post("/api/admin/compose/home/blocks?locale=zh", json={"type":"hero"}, headers=H); chk("compose add ?locale=zh", r.status_code==201 and j(r)["page"]["locale"]=="zh", str(r.status_code))
r=c.delete(f"/api/admin/compose/home/blocks/{ids['banner']}", headers=H); chk("compose remove", r.status_code==200, str(r.status_code))
r=c.post("/api/admin/compose/home/blocks", json={"type":"nonsense"}, headers=H); chk("compose bad type -> 400", r.status_code==400, str(r.status_code))
r=c.post("/api/admin/compose/nope/blocks", json={"type":"hero"}, headers=H); chk("compose bad target -> 404", r.status_code==404, str(r.status_code))

# ---------- ADMIN: patterns ----------
r=c.post("/api/admin/patterns", json={"name":"Audit Pattern","spec":{"type":"steps","content":{"heading":"Steps"}},"tags":["t"]}, headers=H)
pslug=j(r).get("item",{}).get("slug"); patid=j(r).get("item",{}).get("id"); chk("POST /admin/patterns", r.status_code==201 and pslug, str(r.status_code))
r=c.get(f"/api/patterns/{pslug}"); chk("GET /patterns/{slug}", r.status_code==200 and j(r)["item"]["spec"]["type"]=="steps", str(r.status_code))
r=c.post("/api/admin/compose/home/blocks", json={"pattern":pslug}, headers=H); chk("compose insert {pattern}", r.status_code==201 and j(r)["item"]["type"]=="steps", str(r.status_code))
r=c.delete(f"/api/admin/patterns/{patid}", headers=H); chk("DELETE /admin/patterns/{id}", r.status_code==200, str(r.status_code))

# ---------- ADMIN: i18n ----------
r=c.patch("/api/admin/i18n/zh", json={"messages":{"nav.blog":"博客"}}, headers=H); chk("PATCH /admin/i18n/zh", r.status_code==200, str(r.status_code))
r=c.get("/api/i18n/zh"); chk("i18n reflects write", r.status_code==200 and j(r)["item"]["messages"].get("nav.blog")=="博客", str(r.status_code))
r=c.patch("/api/admin/i18n/fr", json={"messages":{}}, headers=H); chk("i18n bad locale -> 400", r.status_code==400, str(r.status_code))

# ---------- ADMIN: media upload (upload-only image hosting) ----------
import io as _io, base64 as _b64
_PNG=b"\x89PNG\r\n\x1a\n"+b"0"*64
r=c.post("/api/admin/media", data={"file":(_io.BytesIO(_PNG),"My Shot.png")}, content_type="multipart/form-data", headers=H)
murl=j(r).get("item",{}).get("url",""); mname=j(r).get("item",{}).get("filename",""); chk("POST /admin/media (multipart, absolute url)", r.status_code==201 and "/api/media/" in murl and murl.endswith(".png") and murl.startswith("http"), str(r.status_code))
r=c.get(f"/api/media/{mname}"); chk("uploaded image is served", r.status_code==200, str(r.status_code))
r=c.post("/api/admin/media", json={"data":_b64.b64encode(_PNG).decode(),"filename":"inline.png"}, headers=H); chk("POST /admin/media (base64)", r.status_code==201 and j(r)["item"]["url"].endswith(".png"), str(r.status_code))
r=c.post("/api/admin/media", json={"data":_b64.b64encode(b"not an image").decode()}, headers=H); chk("POST /admin/media non-image -> 400", r.status_code==400, str(r.status_code))
r=c.post("/api/admin/media", json={}, headers=H); chk("POST /admin/media empty -> 400", r.status_code==400, str(r.status_code))
r=c.post("/api/admin/media", data={"file":(_io.BytesIO(_PNG),"x.png")}, content_type="multipart/form-data"); chk("POST /admin/media no token -> 401", r.status_code==401, str(r.status_code))
r=c.get("/api/admin/media", headers=H); chk("GET /admin/media (list)", r.status_code==200 and any(i["filename"]==mname for i in j(r).get("items",[])), str(r.status_code))
r=c.delete(f"/api/admin/media/{mname}", headers=H); chk("DELETE /admin/media/<file>", r.status_code==200, str(r.status_code))
r=c.delete("/api/admin/media/missing.png", headers=H); chk("DELETE /admin/media/<missing> -> 404", r.status_code==404, str(r.status_code))

# ---------- cleanup write ----------
r=c.delete(f"/api/admin/pages/{pid}", headers=H); chk("DELETE /admin/pages/{id}", r.status_code==200, str(r.status_code))

# ---------- report ----------
ok=sum(1 for x in R if x[0]); bad=[x for x in R if not x[0]]
for cond,name,d in R: print(("  PASS " if cond else "  FAIL ")+name+(("  -> "+d) if d else ""))
print(f"\n  === {ok}/{len(R)} passed ===")
sys.exit(1 if bad else 0)
