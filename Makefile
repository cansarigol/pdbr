lint:
	poetry run nox --sessions lint

test:
	poetry run nox --sessions check test django_test

celery:
	celery -A tasks worker --loglevel=info

build:
	docker build -t pdbr .

act:
	act -r -j test --container-architecture linux/amd64
