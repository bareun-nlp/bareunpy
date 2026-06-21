# -*- coding: utf-8 -*-
"""pytest 공용 설정.

``tests/test_tagger.py`` / ``tests/test_tokenizer.py`` / ``tests/test_corrector.py`` 는
실서버(api.bareun.ai)와 유효한 API 키가 필요한 통합(integration) 테스트다.

실행 조건:
  - 환경변수 ``BAREUN_API_KEY`` 에 유효한 API 키를 넣으면 자동으로 통합 테스트가 활성화된다.
  - 또는 ``BAREUN_RUN_INTEGRATION=1`` 을 설정해도 된다(이전 방식과 하위 호환).
  - 두 환경변수가 모두 없으면 통합 테스트는 스킵된다.

서버/포트 커스텀:
  - ``BAREUN_HOST`` (기본값: api.bareun.ai)
  - ``BAREUN_PORT`` (기본값: 443)

오프라인 단위 테스트(``test_connect_unit.py``)는 항상 실행된다.
"""

import os

import pytest

# 통합 테스트로 간주할 테스트 파일들
_INTEGRATION_FILES = {"test_tagger.py", "test_tokenizer.py", "test_corrector.py"}


def _integration_enabled() -> bool:
    """BAREUN_API_KEY 또는 BAREUN_RUN_INTEGRATION 이 설정되어 있으면 True."""
    return bool(
        os.environ.get("BAREUN_API_KEY")
        or os.environ.get("BAREUN_RUN_INTEGRATION")
    )


def pytest_collection_modifyitems(config, items):
    """네트워크가 필요한 통합 테스트를 조건부로 스킵한다.

    BAREUN_API_KEY 또는 BAREUN_RUN_INTEGRATION 환경변수가 있으면 스킵하지 않는다.
    """
    if _integration_enabled():
        return
    skip_integration = pytest.mark.skip(
        reason=(
            "통합 테스트: BAREUN_API_KEY=<key> 환경변수를 설정하거나 "
            "BAREUN_RUN_INTEGRATION=1 로 실행하세요(실서버/키 필요)."
        )
    )
    for item in items:
        if os.path.basename(str(item.fspath)) in _INTEGRATION_FILES:
            item.add_marker(skip_integration)
