.PHONY: venv-local venv-pip-upgrade clean \
 venv-upgrade-build venv-pytest test build \
 venv-poetry poetry venv

PIP3=venv/bin/pip3
PY3=venv/bin/python3
POETRY=venv/bin/poetry

all: build

venv-local:
	@test -d venv || python3 -m venv venv

venv-pip-upgrade: venv-local
	@$(PIP3) install --upgrade pip &> /dev/null

venv/req-install.log: requirements.txt venv-pip-upgrade
	@$(PY3) -c "import pkg_resources; pkg_resources.require(open('requirements.txt',mode='r'))" &> /dev/null \
	|| (echo "installing"; $(PIP3) install -r $< --log $@)

venv: venv/req-install.log
	@. venv/bin/activate


clean:
	rm -rf venv
	find . -iname "*.pyc" -delete

venv-poetry: venv
	@$(PY3) -m pip install --upgrade poetry &> /dev/null

build: venv-poetry
	@$(POETRY) build

publish: build
	@$(POETRY) publish

venv-pytest: venv
	@$(PY3) -m pip install --upgrade pytest &> /dev/null

testall: venv
	@$(PY3) -m pytest tests/
