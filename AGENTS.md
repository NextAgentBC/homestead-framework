# Codex Agent Instructions

Use this file when operating inside this repository.

- Prefer PostgreSQL for all real tests.
- Keep frontend and backend separated.
- Keep public API changes documented in `docs/api-contract.md` and `backend/app/openapi.json`.
- Keep UI/UX personalization API-driven through `/api/design`; do not bake one permanent industry style into components.
- If asked to customize by industry or competitor, update `DesignProfile` through backend routes and CSS variables first.
- For competitor-informed design, use `/api/admin/design/analyze-competitors` and document visual observations. Never copy exact competitor branding.
- Do not commit `.env`, `.env.local`, `.venv`, `.next`, `node_modules`, or local databases.
- Before saying the project works, run backend route/migration checks and frontend typecheck/build.
- Run `pytest -q` from `backend/` before reporting backend changes as complete.
- For deployment, target `oracle-server:/home/ubuntu/projects/oracle-site` unless the human gives another path.
- Prefer Cloudflare Tunnel over direct public Nginx exposure.
