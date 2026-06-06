#!/bin/sh
set -eu

flask --app app.main db upgrade

# First-boot demo seed: populate a complete industry home + starter pages on an
# empty DB so a fresh deploy is a real multi-page site. Idempotent (skips once
# content exists) and non-fatal, so it's safe to run on every boot.
if [ "${SITE_SEED_DEMO:-true}" = "true" ]; then
  flask --app app.main site seed || echo "entrypoint: site seed skipped (non-fatal)"
fi

exec "$@"

