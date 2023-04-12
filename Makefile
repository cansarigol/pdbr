lint:
	sh scripts/lint

test:
	sh scripts/test

celery:
	celery -A tasks worker --loglevel=info

build:
	docker build -t pdbr .

act:
	act -r -j test --container-architecture linux/amd64
