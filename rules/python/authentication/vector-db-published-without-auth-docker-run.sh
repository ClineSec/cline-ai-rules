#!/usr/bin/env bash
# Local vector stores for the insights pipeline.
set -euo pipefail

QDRANT_IMAGE="qdrant/qdrant:v1.20.0"

start_stores() {
  # ruleid: vector-db-published-without-auth-docker-run
  docker run -d --name qdrant -p 6333:6333 -p 6334:6334 -v "$PWD/qdrant_storage:/qdrant/storage" qdrant/qdrant
  # ruleid: vector-db-published-without-auth-docker-run
  docker run -d --name chroma -p 8000:8000 chromadb/chroma:1.5.9
  # ruleid: vector-db-published-without-auth-docker-run
  sudo docker run -d \
    --name weaviate \
    -p 8080:8080 -p 50051:50051 \
    -e AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true \
    -e PERSISTENCE_DATA_PATH=/var/lib/weaviate \
    cr.weaviate.io/semitechnologies/weaviate:1.40.2
  # ruleid: vector-db-published-without-auth-docker-run
  podman run -d --name weaviate-default --publish 8081:8080 semitechnologies/weaviate:1.40.2
  # ruleid: vector-db-published-without-auth-docker-run
  docker run -d --name milvus --security-opt seccomp:unconfined -e ETCD_USE_EMBED=true \
    -e COMMON_STORAGETYPE=local -v "$PWD/volumes/milvus:/var/lib/milvus" \
    -p 19530:19530 -p 9091:9091 milvusdb/milvus:v3.0.2 milvus run standalone
  # ruleid: vector-db-published-without-auth-docker-run
  docker run -d --network host "${QDRANT_IMAGE}"
  # ruleid: vector-db-published-without-auth-docker-run
  docker run -d -p 0.0.0.0:8002:8000 -e CHROMA_SERVER_AUTHN_PROVIDER=chromadb.auth.token_authn.TokenAuthenticationServerProvider chromadb/chroma
  # ruleid: vector-db-published-without-auth-docker-run
  docker run -d -p 8003:8000 ghcr.io/chroma-core/chroma:0.6.3
}

start_protected() {
  # ok: vector-db-published-without-auth-docker-run
  docker run -d --name qdrant -p 6333:6333 -e QDRANT__SERVICE__API_KEY="$QDRANT_API_KEY" qdrant/qdrant:v1.20.0
  # ok: vector-db-published-without-auth-docker-run
  docker run -d --name qdrant-pass -p 6333:6333 -e QDRANT__SERVICE__API_KEY qdrant/qdrant:v1.20.0
  # ok: vector-db-published-without-auth-docker-run
  docker run -d --name qdrant-local -p 127.0.0.1:6333:6333 qdrant/qdrant:v1.20.0
  # ok: vector-db-published-without-auth-docker-run
  docker run -d --name qdrant-cfg -p 6333:6333 -v "$PWD/config/production.yaml:/qdrant/config/production.yaml" qdrant/qdrant:v1.20.0
  # ok: vector-db-published-without-auth-docker-run
  docker run -d --name qdrant-env -p 6333:6333 --env-file .env.qdrant qdrant/qdrant:v1.20.0
  # ok: vector-db-published-without-auth-docker-run
  docker run -d --name qdrant-internal --network vectors qdrant/qdrant:v1.20.0
  # ok: vector-db-published-without-auth-docker-run
  docker run -d -p 8000:8000 -e CHROMA_SERVER_AUTHN_PROVIDER=chromadb.auth.token_authn.TokenAuthenticationServerProvider chromadb/chroma:0.5.23
  # ok: vector-db-published-without-auth-docker-run
  docker run -d -p 127.0.0.1:8000:8000 chromadb/chroma:1.5.9
  # ok: vector-db-published-without-auth-docker-run
  docker run -d -p 8080:8080 -e AUTHENTICATION_APIKEY_ENABLED=true -e AUTHENTICATION_APIKEY_ALLOWED_KEYS="$WEAVIATE_KEYS" semitechnologies/weaviate:1.40.2
  # ok: vector-db-published-without-auth-docker-run
  docker run -d -p 8080:8080 -v "$PWD/weaviate.conf.yaml:/config/conf.yaml:ro" semitechnologies/weaviate:1.40.2 --host 0.0.0.0 --port 8080 --scheme http --config-file /config/conf.yaml
  # ruleid: vector-db-published-without-auth-docker-run
  docker run -d -p 8080:8080 -e AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true semitechnologies/weaviate:1.40.2 --host 0.0.0.0 --port 8080 --scheme http --config-file /config/conf.yaml
  # ok: vector-db-published-without-auth-docker-run
  docker run -d -p 19530:19530 -e COMMON_SECURITY_AUTHORIZATIONENABLED=true milvusdb/milvus:v3.0.2 milvus run standalone
  # ok: vector-db-published-without-auth-docker-run
  docker run -d -p 19530:19530 -v "$PWD/user.yaml:/milvus/configs/user.yaml" milvusdb/milvus:v3.0.2 milvus run standalone
  # ok: vector-db-published-without-auth-docker-run
  docker run -d -p 5432:5432 pgvector/pgvector:pg17
  # ok: vector-db-published-without-auth-docker-run
  echo "run: docker run -p 6333:6333 qdrant/qdrant"
}
