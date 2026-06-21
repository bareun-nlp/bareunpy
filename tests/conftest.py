# -*- coding: utf-8 -*-
"""pytest 공용 설정.

``tests/test_tagger.py`` / ``tests/test_tokenizer.py`` 는 실제 bareun 서버(api.bareun.ai
또는 사내 호스트)와 유효한 API 키가 필요한 통합(integration) 테스트다. 기본 실행에서는
네트워크가 없으면 실패하므로, 환경변수 ``BAREUN_RUN_INTEGRATION`` 이 설정된 경우에만
수집한다. 오프라인 단위 테스트(``test_connect_unit.py``)는 항상 실행된다.
"""

import os

import pytest

# 통합 테스트로 간주하여 기본 스킵할 테스트 파일들.
_INTEGRATION_FILES = {"test_tagger.py", "test_tokenizer.py"}


def pytest_collection_modifyitems(config, items):
    """네트워크가 필요한 통합 테스트를 기본적으로 스킵한다.

    ``BAREUN_RUN_INTEGRATION`` 환경변수가 있으면 스킵하지 않고 그대로 실행한다.
    """
    if os.environ.get("BAREUN_RUN_INTEGRATION"):
        return
    skip_integration = pytest.mark.skip(
        reason="통합 테스트: BAREUN_RUN_INTEGRATION=1 로 실행하세요(실서버/키 필요)."
    )
    for item in items:
        if os.path.basename(str(item.fspath)) in _INTEGRATION_FILES:
            item.add_marker(skip_integration)
