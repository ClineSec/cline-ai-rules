#!/usr/bin/env bash
# Starts the vector stores on the forecasting VM, which has Docker but no compose plugin.
# Usage: deploy/vector-stores.sh [qdrant|milvus|all]
set -euo pipefail

QDRANT_VERSION="v1.20.0"
MILVUS_IMAGE="milvusdb/milvus:v3.0.2"
DATA_DIR="${DATA_DIR:-/srv/insights}"

start_qdrant() {
  if [[ -n "${QDRANT_API_KEY:-}" ]]; then
    docker run -d --name qdrant --restart unless-stopped -p 6333:6333 \
      -e QDRANT__SERVICE__API_KEY="$QDRANT_API_KEY" \
      -v "$DATA_DIR/qdrant:/qdrant/storage" "qdrant/qdrant:${QDRANT_VERSION}"
  else
    echo "QDRANT_API_KEY is not set; starting the local-only Qdrant" >&2
    docker run -d --name qdrant --restart unless-stopped -p 127.0.0.1:6333:6333 \
      -v "$DATA_DIR/qdrant:/qdrant/storage" "qdrant/qdrant:${QDRANT_VERSION}"
  fi
}

start_milvus() {
  docker start milvus 2>/dev/null || \
    docker run -d --name milvus --security-opt seccomp:unconfined \
      -e ETCD_USE_EMBED=true -e COMMON_STORAGETYPE=local \
      -v "$DATA_DIR/milvus:/var/lib/milvus" \
      -p 19530:19530 -p 9091:9091 \
      "$MILVUS_IMAGE" milvus run standalone
}

case "${1:-all}" in
  qdrant) start_qdrant ;;
  milvus) start_milvus ;;
  all) start_qdrant; start_milvus ;;
  *) echo "usage: $0 [qdrant|milvus|all]" >&2; exit 2 ;;
esac
