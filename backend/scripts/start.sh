#! /usr/bin/env bash

set -e
set -x

bash scripts/prestart.sh

exec fastapi run --host 0.0.0.0 --port "$PORT" --workers "${WEB_CONCURRENCY:-1}"
