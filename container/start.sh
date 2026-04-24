#!/bin/sh
set -e
BACKEND_URI="postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}"
mlflow server \
  --host 0.0.0.0 \
  --port 5000 \
  --backend-store-uri "$BACKEND_URI" \
  --artifacts-destination "$MLFLOW_ARTIFACT_ROOT"