lint:
	poetry run nox --sessions lint

test:
	poetry run nox --sessions check && poetry run nox --sessions test

celery:
	celery -A tasks worker --loglevel=info