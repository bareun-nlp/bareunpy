.PHONY: all clean venv venv-local venv-pip-upgrade \
 build publish test testall proto

PIP3=venv/bin/pip3
PY3=venv/bin/python3
POETRY=venv/bin/poetry

all: build

venv-local:
	@test -d venv || python3 -m venv venv

venv-pip-upgrade: venv-local
	@$(PIP3) install --upgrade pip 2> /dev/null

# requirements.txt 가 바뀌면 다시 설치한다. (구버전의 pkg_resources.require 검사 제거 —
# pkg_resources 는 setuptools 81+ 에서 제거되었고 Python 3.12+ 에는 기본 포함되지 않는다.)
venv/req-install.log: requirements.txt venv-pip-upgrade
	@$(PIP3) install -r $< --log $@

venv: venv/req-install.log

clean:
	rm -rf venv dist build *.egg-info
	find . -iname "*.pyc" -delete
	find . -iname "__pycache__" -type d -exec rm -rf {} +

venv-poetry: venv
	@$(PY3) -m pip install --upgrade poetry 2> /dev/null

build: venv-poetry
	@$(POETRY) build

publish: build
	@$(POETRY) publish

# 오프라인 단위 테스트 실행(통합 테스트는 conftest 가 기본 스킵).
test: venv
	@$(PY3) -m pip install --upgrade pytest >/dev/null 2>&1
	@$(PY3) -m pytest tests/

testall: test

# 현재 bareun protos 에서 bareun/ 패키지(메시지 + Connect 스텁)를 재생성한다.
# baikal-nlp 모노레포 경로는 BAREUN_PROTOS 로 지정(기본값 ../bareun/protos).
proto:
	@tools/gen_proto.sh
