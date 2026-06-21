#!env python3
# -*- coding: utf-8 -*-
"""Corrector 통합 테스트.

실제 api.bareun.ai 서버로 호출해 맞춤법 교정(단발·스트리밍) 결과를 검증한다.
환경변수:
  BAREUN_API_KEY  (필수)  유효한 API 키
  BAREUN_HOST     (선택)  서버 호스트, 기본값 api.bareun.ai
  BAREUN_PORT     (선택)  서버 포트, 기본값 443
"""
import os
import tempfile
import pytest
import bareunpy
from bareunpy import Corrector
import bareun.revision_service_pb2 as pb


def _api_key() -> str:
    return os.environ.get("BAREUN_API_KEY", "")


def _host() -> str:
    return os.environ.get("BAREUN_HOST", "api.bareun.ai")


def _port() -> int:
    return int(os.environ.get("BAREUN_PORT", "443"))


SAMPLE = '영수 도 줄기가 얇어서 시들을 것 같은 꽃에물을 주었더니 고은 꽃이 피었다.'


@pytest.fixture
def corrector_instance():
    return Corrector(apikey=_api_key(), host=_host(), port=_port())


@pytest.fixture
def corrector_error_apikey():
    return Corrector(apikey="koba-INVALID-KEY", host=_host(), port=_port())


def test_corrector_correct_error_returns_response(corrector_instance):
    """단발 교정 호출이 CorrectErrorResponse 를 반환한다."""
    resp = corrector_instance.correct_error(SAMPLE)
    assert isinstance(resp, pb.CorrectErrorResponse)
    # 원문이 응답에 포함되어 있어야 한다
    assert resp.origin == SAMPLE


def test_corrector_correct_error_revised(corrector_instance):
    """교정 결과가 원문과 다른 교정문을 포함한다."""
    resp = corrector_instance.correct_error(SAMPLE)
    # 오류가 많은 문장이므로 교정문은 원문과 달라야 한다
    assert resp.revised != ''
    assert resp.revised != SAMPLE


def test_corrector_print_results(corrector_instance):
    """print_results 가 예외 없이 출력한다."""
    resp = corrector_instance.correct_error(SAMPLE)
    with tempfile.TemporaryFile('w+') as f:
        corrector_instance.print_results(resp, out=f)
        assert f.tell() > 0


def test_corrector_as_json(corrector_instance):
    """as_json 이 dict 를 반환하며 origin 키를 포함한다."""
    resp = corrector_instance.correct_error(SAMPLE)
    j = corrector_instance.as_json(resp)
    assert isinstance(j, dict)
    assert 'origin' in j


def test_corrector_as_json_str(corrector_instance):
    """as_json_str 이 JSON 문자열을 반환한다."""
    import json
    resp = corrector_instance.correct_error(SAMPLE)
    s = corrector_instance.as_json_str(resp)
    parsed = json.loads(s)
    assert 'origin' in parsed


def test_corrector_print_as_json(corrector_instance):
    """print_as_json 이 파일에 JSON 을 출력한다."""
    resp = corrector_instance.correct_error(SAMPLE)
    with tempfile.TemporaryFile('w+') as f:
        corrector_instance.print_as_json(resp, out=f)
        assert f.tell() > 0


def test_corrector_stream_yields_responses(corrector_instance):
    """server-streaming 교정이 최소 하나 이상의 응답을 산출한다."""
    responses = list(corrector_instance.correct_error_stream(SAMPLE))
    assert len(responses) > 0
    for resp in responses:
        assert isinstance(resp, pb.StreamCorrectErrorResponse)
        # oneof 필드 중 하나가 설정되어 있어야 한다
        kind = resp.WhichOneof("res")
        assert kind in ("first", "progress", "post", "cancelled")


def test_corrector_stream_first_response(corrector_instance):
    """스트리밍 첫 응답에는 first 필드가 포함되어 있어야 한다."""
    for resp in corrector_instance.correct_error_stream(SAMPLE):
        kind = resp.WhichOneof("res")
        if kind == "first":
            first = resp.first
            assert first.origin == SAMPLE
            break
    else:
        pytest.fail("스트리밍에서 first 응답을 받지 못했습니다.")


def test_corrector_stream_with_req_id(corrector_instance):
    """req_id 를 지정하면 스트리밍이 정상 동작한다."""
    responses = list(corrector_instance.correct_error_stream(SAMPLE, req_id=42))
    assert len(responses) > 0


def test_corrector_stream_with_custom_dicts(corrector_instance):
    """custom_dicts 파라미터가 전달되어도 예외 없이 스트리밍이 동작한다."""
    responses = list(corrector_instance.correct_error_stream(SAMPLE, custom_dicts=['my']))
    assert len(responses) > 0


def test_corrector_close(corrector_instance):
    """close() 가 예외 없이 실행된다."""
    corrector_instance.close()


def test_corrector_constructor_defaults():
    """host 를 생략하면 api.bareun.ai 를 기본값으로 사용한다."""
    c = Corrector(apikey=_api_key())
    assert c.host == 'api.bareun.ai'
    assert c.port == 443


def test_corrector_constructor_no_apikey():
    """API 키 없이 생성하면 ValueError 가 발생한다."""
    with pytest.raises(ValueError):
        Corrector(apikey="")


def test_corrector_exception_apikey(corrector_error_apikey):
    """잘못된 API 키로 호출하면 사람이 읽을 수 있는 오류 메시지를 던진다."""
    with pytest.raises(Exception) as exc_info:
        corrector_error_apikey.correct_error(SAMPLE)
    assert exc_info.value.args[0][:27] == '\n입력한 API KEY가 정확한지 확인해 주세요.'
