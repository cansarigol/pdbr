.PHONY: install lint test

install:
	poetry install --with dev --all-extras
	poetry run pre-commit install

lint:
	poetry run pre-commit run --all-files

test:
	poetry run pytest
