#!/usr/bin/env bash

set -e

alembic upgrade head
uvicorn --proxy-headers --host 0.0.0.0 --port $API_PORT src.main:app
