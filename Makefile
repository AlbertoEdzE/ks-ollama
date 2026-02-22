PYTHON_VERSION=3.11.10
VENV=.venv
PIP=$(VENV)/bin/pip
PY=$(VENV)/bin/python
PYTEST=$(VENV)/bin/pytest

.PHONY: pyenv venv install dev-install format lint test unit integration e2e run migrate upgrade downgrade revision seed

pyenv:
	pyenv install -s $(PYTHON_VERSION)
	pyenv local $(PYTHON_VERSION)

venv:
	python -m venv $(VENV)
	$(PIP) install --upgrade pip

install: venv
	$(PIP) install -r requirements.txt

dev-install: install
	$(PIP) install -r requirements-dev.txt

format:
	$(VENV)/bin/black app tests
	$(VENV)/bin/isort app tests

lint:
	$(VENV)/bin/ruff check app tests
	$(VENV)/bin/mypy app
	$(VENV)/bin/bandit -r app -s B105

test:
	$(PYTEST) -q --cov=app --cov-report=term-missing

unit:
	$(PYTEST) -q tests/unit

integration:
	$(PYTEST) -q tests/integration

e2e:
	$(PYTEST) -q tests/e2e

run:
	$(PY) -m gunicorn -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8080 app.main:app

migrate:
	alembic revision --autogenerate -m "auto"

upgrade:
	alembic upgrade head

downgrade:
	alembic downgrade -1

revision:
	alembic revision -m "$(m)"

seed:
	$(PY) -m app.db.seed
