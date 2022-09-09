build: pre-build docker-build post-build
pre-build: $(shell cp ../../src/config.json ./)
docker-build:
	docker build -t crusher083/gtdb-tk .
post-build:
	docker push crusher083/gtdb-tk
	$(shell rm ./config.json)
