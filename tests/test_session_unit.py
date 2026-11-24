# -*- coding: utf-8 -*-
"""교정 세션(open·correct·events·close) 오프라인 단위 테스트.

서버 없이 connectrpc 스텁의 메서드를 가짜로 바꿔 요청 구성과 응답 처리를 검증한다.
"""

import pytest
from connectrpc.code import Code
from connectrpc.errors import ConnectError

from bareunpy import Corrector, RevisionSession
from bareunpy._truncation import truncation_of

import bareunpy.bareun.lang_common_pb2 as lcpb
import bareunpy.bareun.revision_service_pb2 as rpb

APIKEY = "koba-TESTKEY"


def _corrector():
    return Corrector(apikey=APIKEY, host="localhost", port=5656)


def _opened(sid="sess-1"):
    return rpb.OpenSessionResponse(
        session_id=sid, session_revision=0, idle_timeout_seconds=600, max_lifetime_seconds=3600)


def test_open_session_sends_dicts_and_config(monkeypatch):
    c = _corrector()
    seen = {}

    def fake_open(request, headers=None, timeout_ms=None):
        seen["req"], seen["headers"] = request, headers
        return _opened()

    monkeypatch.setattr(c.client.stub, "open_session", fake_open)
    cfg = rpb.RevisionConfig(disable_typo_correction=True)
    s = c.open_session(custom_dicts=["law"], config=cfg)
    assert isinstance(s, RevisionSession)
    assert (s.session_id, s.session_revision) == ("sess-1", 0)
    assert (s.idle_timeout_seconds, s.max_lifetime_seconds) == (600, 3600)
    assert list(seen["req"].custom_dict_names) == ["law"]
    assert seen["req"].config.disable_typo_correction is True
    assert seen["headers"]["api-key"] == APIKEY


def test_open_session_defaults(monkeypatch):
    c = _corrector()
    seen = {}
    monkeypatch.setattr(c.client.stub, "open_session",
                        lambda request, headers=None, timeout_ms=None: seen.setdefault("req", request) and _opened())
    c.open_session()
    assert list(seen["req"].custom_dict_names) == []
    assert not seen["req"].HasField("config")


def test_session_correct_error_carries_session_id(monkeypatch):
    c = _corrector()
    monkeypatch.setattr(c.client.stub, "open_session", lambda r, headers=None, timeout_ms=None: _opened("abc"))
    seen = []

    def fake_correct(request, headers=None, timeout_ms=None):
        seen.append(request)
        return rpb.CorrectErrorResponse(origin=request.document.content, revised="교정")

    monkeypatch.setattr(c.client.stub, "correct_error", fake_correct)
    s = c.open_session()
    res = s.correct_error("고은 꽃")
    assert res.revised == "교정"
    assert seen[0].session_id == "abc"
    assert seen[0].document.content == "고은 꽃"
    assert seen[0].encoding_type == lcpb.EncodingType.UTF32


def test_session_long_document_loop(monkeypatch):
    # 잘린 응답의 dropped_text 로 나머지를 이어 보내는 README 예제와 같은 흐름.
    c = _corrector()
    monkeypatch.setattr(c.client.stub, "open_session", lambda r, headers=None, timeout_ms=None: _opened())

    def fake_correct(request, headers=None, timeout_ms=None):
        text = request.document.content
        if len(text) <= 4:
            return rpb.CorrectErrorResponse(origin=text, revised=text)
        return rpb.CorrectErrorResponse(
            origin=text[:4], revised=text[:4],
            truncation=lcpb.Truncation(original_chars=len(text), processed_chars=4,
                                       dropped_chars=len(text) - 4, dropped_begin_offset=4))

    monkeypatch.setattr(c.client.stub, "correct_error", fake_correct)
    s = c.open_session()
    text, out = "가나다라마바사아자", []
    while text:
        res = s.correct_error(text)
        out.append(res.revised)
        t = truncation_of(res)
        text = t.dropped_text(text) if t else ""
    assert "".join(out) == "가나다라마바사아자"
    assert out == ["가나다라", "마바사아", "자"]


def test_session_stream_carries_session_id(monkeypatch):
    c = _corrector()
    monkeypatch.setattr(c.client.stub, "open_session", lambda r, headers=None, timeout_ms=None: _opened("st"))
    seen = {}

    def fake_stream(request, headers=None, timeout_ms=None):
        seen["req"] = request
        yield rpb.StreamCorrectErrorResponse(
            session_correction=rpb.SessionCorrection(req_id=7, session_revision=2))

    monkeypatch.setattr(c.client.stub, "stream_correct_error", fake_stream)
    s = c.open_session()
    res = list(s.correct_error_stream("글", req_id=7))
    assert res[0].WhichOneof("res") == "session_correction"
    assert seen["req"].session_id == "st" and seen["req"].req_id == 7
    list(s.correct_error_stream("글"))
    assert seen["req"].req_id == 0


def test_session_events_and_close(monkeypatch):
    c = _corrector()
    monkeypatch.setattr(c.client.stub, "open_session", lambda r, headers=None, timeout_ms=None: _opened("ev"))
    calls = {}

    def fake_events(request, headers=None, timeout_ms=None):
        calls["events"] = request
        return rpb.GetSessionEventsResponse(
            session_revision=1,
            events=[rpb.SessionEvent(revision=1, kind=rpb.SESSION_EVENT_KIND_WORD_CONFIRMED, word="바른")])

    def fake_close(request, headers=None, timeout_ms=None):
        calls["close"] = request
        return rpb.CloseSessionResponse(session_revision=1)

    monkeypatch.setattr(c.client.stub, "get_session_events", fake_events)
    monkeypatch.setattr(c.client.stub, "close_session", fake_close)
    s = c.open_session()
    ev = s.events(since_revision=0)
    assert ev.session_revision == 1 and ev.events[0].word == "바른"
    assert calls["events"].session_id == "ev" and calls["events"].since_revision == 0
    assert s.close().session_revision == 1
    assert calls["close"].session_id == "ev"


def test_session_context_manager_closes_even_on_error(monkeypatch):
    c = _corrector()
    monkeypatch.setattr(c.client.stub, "open_session", lambda r, headers=None, timeout_ms=None: _opened("cm"))
    closed = []
    monkeypatch.setattr(c.client.stub, "close_session",
                        lambda r, headers=None, timeout_ms=None: closed.append(r.session_id) or rpb.CloseSessionResponse())
    with c.open_session() as s:
        assert s.session_id == "cm"
    assert closed == ["cm"]
    with pytest.raises(RuntimeError):
        with c.open_session():
            raise RuntimeError("중간에 실패")
    assert closed == ["cm", "cm"]


@pytest.mark.parametrize("method,call", [
    ("open_session", lambda c: c.open_session()),
    ("close_session", lambda c: c.client.close_session(rpb.CloseSessionRequest(session_id="x"))),
    ("get_session_events", lambda c: c.client.get_session_events(rpb.GetSessionEventsRequest(session_id="x"))),
])
def test_session_rpc_errors_are_translated(monkeypatch, method, call):
    c = _corrector()

    def boom(request, headers=None, timeout_ms=None):
        raise ConnectError(Code.UNAVAILABLE, "down")

    monkeypatch.setattr(c.client.stub, method, boom)
    with pytest.raises(Exception, match="서버에 연결할 수 없습니다"):
        call(c)


def test_session_not_found_error_keeps_original(monkeypatch):
    # 세션 오류(NOT_FOUND 등)는 원본 ConnectError 로 전파되어 reason 을 읽을 수 있다.
    c = _corrector()
    monkeypatch.setattr(c.client.stub, "open_session", lambda r, headers=None, timeout_ms=None: _opened())

    def boom(request, headers=None, timeout_ms=None):
        raise ConnectError(Code.NOT_FOUND, "SESSION_EXPIRED")

    monkeypatch.setattr(c.client.stub, "correct_error", boom)
    s = c.open_session()
    with pytest.raises(ConnectError) as ei:
        s.correct_error("글")
    assert ei.value.code == Code.NOT_FOUND
