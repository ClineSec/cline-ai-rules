QDRANT_IMAGE ?= qdrant/qdrant:v1.20.0
MILVUS_IMAGE ?= milvusdb/milvus:v3.0.2

vectors-up:
	# ruleid: vector-db-published-without-auth-docker-run
	docker run -d --rm --name qdrant -p 6333:6333 $(QDRANT_IMAGE)
	# ruleid: vector-db-published-without-auth-docker-run
	@docker run -d --rm --name milvus -p 19530:19530 $(MILVUS_IMAGE) milvus run standalone

vectors-up-secure:
	# ok: vector-db-published-without-auth-docker-run
	docker run -d --rm --name qdrant -p 6333:6333 -e QDRANT__SERVICE__API_KEY=$(QDRANT_API_KEY) $(QDRANT_IMAGE)
	# ok: vector-db-published-without-auth-docker-run
	docker run -d --rm --name milvus -p 127.0.0.1:19530:19530 $(MILVUS_IMAGE) milvus run standalone

