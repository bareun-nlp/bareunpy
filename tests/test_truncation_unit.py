# -*- coding: utf-8 -*-
"""긴 요청의 잘림(truncation) 응답 처리에 대한 오프라인 단위 테스트.

서버 없이 실제 protobuf 응답을 구성해 ``TruncationInfo`` 변환, ``Tagged``·``Tokenized``·
``Corrector`` 의 조회 메서드, 옛 응답(필드 없음)과의 호환을 검증한다.
"""

import io

import bareunpy
from bareunpy import Corrector, Tagger, Tokenizer, TruncationInfo
from bareunpy._tagger import Tagged
from bareunpy._tokenizer import Tokenized
from bareunpy._truncation import truncation_of

import bareunpy.bareun.lang_common_pb2 as lcpb
import bareunpy.bareun.language_service_pb2 as lpb2
import bareunpy.bareun.revision_service_pb2 as rpb

APIKEY = "koba-TESTKEY"
HOST = "localhost"
PORT = 5656

MSG = "요청 글이 너무 길어 앞 4991자만 처리했습니다. (request too long)"


def _trunc(**kw):
    base = dict(original_chars=9001, processed_chars=4991, dropped_chars=4010,
                dropped_begin_offset=4991, message=MSG, cut_mid_word=False)
    base.update(kw)
    return lcpb.Truncation(**base)


# ----------------------------------------------------------------------------
# truncation_of
# ----------------------------------------------------------------------------
def test_truncation_of_none_when_not_truncated():
    assert truncation_of(lpb2.AnalyzeSyntaxResponse()) is None
    assert truncation_of(rpb.CorrectErrorResponse()) is None


def test_truncation_of_none_for_message_without_field():
    # 스트림의 진행 응답처럼 truncation 필드가 없는 메시지, 메시지가 아닌 값.
    assert truncation_of(rpb.StreamCorrectErrorResponse()) is None
    assert truncation_of(lcpb.TextSpan()) is None
    assert truncation_of(None) is None
    assert truncation_of("문자열") is None


def test_truncation_of_all_fields():
    res = lpb2.AnalyzeSyntaxResponse(truncation=_trunc(cut_mid_word=True))
    t = truncation_of(res)
    assert t == TruncationInfo(
        original_chars=9001, processed_chars=4991, dropped_chars=4010,
        dropped_begin_offset=4991, message=MSG, cut_mid_word=True,
        dropped_begin_sentence_index=None,
    )
    assert bareunpy.TruncationInfo is TruncationInfo


def test_truncation_of_list_response_has_sentence_index():
    res = lpb2.AnalyzeSyntaxListResponse(
        truncation=_trunc(dropped_begin_offset=30), dropped_begin_sentence_index=0)
    # 0 도 '있는 값'이다(HasField 로 확인하므로 None 과 구별된다).
    assert truncation_of(res).dropped_begin_sentence_index == 0

    res = lpb2.AnalyzeSyntaxListResponse(truncation=_trunc())
    assert truncation_of(res).dropped_begin_sentence_index is None


# ----------------------------------------------------------------------------
# TruncationInfo.dropped_text
# ----------------------------------------------------------------------------
def test_dropped_text_string():
    t = TruncationInfo(10, 4, 6, 4, "m", False)
    assert t.dropped_text("가나다라마바사아자차") == "마바사아자차"


def test_dropped_text_sentence_list():
    t = TruncationInfo(0, 0, 0, 2, "m", False, dropped_begin_sentence_index=1)
    # 1번 문장의 2번째 글자부터 + 이후 문장 전부(문장 사이는 줄바꿈).
    assert t.dropped_text(["가나다", "라마바사", "아자"]) == "바사\n아자"
    # index 가 None 이면 0번 문장부터, 범위를 넘으면 빈 문자열.
    t0 = TruncationInfo(0, 0, 0, 1, "m", False)
    assert t0.dropped_text(["가나다", "라"]) == "나다\n라"
    t9 = TruncationInfo(0, 0, 0, 1, "m", False, dropped_begin_sentence_index=9)
    assert t9.dropped_text(["가나다"]) == ""


# ----------------------------------------------------------------------------
# Tagged / Tokenized
# ----------------------------------------------------------------------------
def test_tagged_not_truncated_by_default():
    tagged = Tagged("짧은 글", lpb2.AnalyzeSyntaxResponse())
    assert tagged.is_truncated() is False
    assert tagged.truncation() is None
    assert tagged.dropped_text() == ""
    # 빈 응답(None)도 안전하다.
    assert Tagged("x", None).is_truncated() is False


def test_tagged_truncated():
    text = "가" * 9001
    tagged = Tagged(text, lpb2.AnalyzeSyntaxResponse(truncation=_trunc()))
    assert tagged.is_truncated() is True
    t = tagged.truncation()
    assert (t.original_chars, t.processed_chars, t.dropped_chars) == (9001, 4991, 4010)
    assert t.message == MSG
    assert tagged.dropped_text() == "가" * 4010
    # 잘림 정보도 JSON 변환에 그대로 실린다.
    assert tagged.as_json()["truncation"]["processedChars"] == 4991


def test_tagger_tag_returns_truncation(monkeypatch):
    t = Tagger(apikey=APIKEY, host=HOST, port=PORT)
    monkeypatch.setattr(
        t.client.stub, "analyze_syntax",
        lambda request, headers=None, timeout_ms=None:
            lpb2.AnalyzeSyntaxResponse(truncation=_trunc()),
    )
    tagged = t.tag("나" * 9001)
    assert tagged.is_truncated()
    assert tagged.truncation().dropped_chars == 4010
    # tags() 는 문장을 줄바꿈으로 이은 글을 보내므로 dropped_text 도 그 글 기준이다.
    tagged = t.tags(["가" * 5000, "나" * 4001])
    assert tagged.dropped_text() == ("가" * 5000 + "\n" + "나" * 4001)[4991:]


def test_tagger_taglist_truncation(monkeypatch):
    t = Tagger(apikey=APIKEY, host=HOST, port=PORT)
    monkeypatch.setattr(
        t.client.stub, "analyze_syntax_list",
        lambda request, headers=None, timeout_ms=None: lpb2.AnalyzeSyntaxListResponse(
            truncation=_trunc(dropped_begin_offset=2), dropped_begin_sentence_index=1),
    )
    tagged = t.taglist(["가나다", "라마바사", "아자"])
    info = tagged.truncation()
    assert info.dropped_begin_sentence_index == 1
    assert tagged.dropped_text() == "바사\n아자"


def test_tokenized_truncated(monkeypatch):
    assert Tokenized("짧다", lpb2.TokenizeResponse()).is_truncated() is False
    assert Tokenized("짧다", None).truncation() is None

    tk = Tokenizer(apikey=APIKEY, host=HOST, port=PORT)
    monkeypatch.setattr(
        tk.client.stub, "tokenize",
        lambda request, headers=None, timeout_ms=None:
            lpb2.TokenizeResponse(truncation=_trunc()),
    )
    tokenized = tk.tokenize("다" * 9001)
    assert tokenized.is_truncated()
    assert tokenized.truncation().processed_chars == 4991
    assert tokenized.dropped_text() == "다" * 4010


# ----------------------------------------------------------------------------
# Corrector
# ----------------------------------------------------------------------------
def test_corrector_truncation(monkeypatch):
    c = Corrector(apikey=APIKEY, host=HOST, port=PORT)
    text = "라" * 9001
    monkeypatch.setattr(
        c.client.stub, "correct_error",
        lambda request, headers=None, timeout_ms=None: rpb.CorrectErrorResponse(
            origin="라" * 4991, revised="라" * 4991, truncation=_trunc()),
    )
    res = c.correct_error(text)
    assert Corrector.is_truncated(res) is True
    t = Corrector.truncation(res)
    assert t.dropped_chars == 4010
    assert t.dropped_text(text) == "라" * 4010


def test_corrector_not_truncated():
    res = rpb.CorrectErrorResponse(origin="짧다", revised="짧다")
    assert Corrector.is_truncated(res) is False
    assert Corrector.truncation(res) is None


def test_corrector_stream_first_truncation():
    first = rpb.StreamFirstCorrectError(origin="가", revised="가", truncation=_trunc())
    assert Corrector.is_truncated(first)
    # 스트림 래퍼(oneof)에서 first 를 꺼내 넘긴다.
    wrapper = rpb.StreamCorrectErrorResponse(first=first)
    assert Corrector.truncation(wrapper.first).processed_chars == 4991


def test_corrector_print_results_shows_truncation_notice():
    c = Corrector(apikey=APIKEY, host=HOST, port=PORT)
    out = io.StringIO()
    c.print_results(
        rpb.CorrectErrorResponse(origin="가", revised="가", truncation=_trunc()), out=out)
    assert f"[주의] {MSG}" in out.getvalue()

    out = io.StringIO()
    c.print_results(rpb.CorrectErrorResponse(origin="가", revised="가"), out=out)
    assert "[주의]" not in out.getvalue()


# ----------------------------------------------------------------------------
# 옛 서버·옛 클라이언트 호환(바이트 수준)
# ----------------------------------------------------------------------------
def test_old_response_bytes_parse_without_truncation():
    # 새 필드가 없는 응답(옛 서버)을 읽어도 잘림 정보는 None 이다.
    raw = lpb2.AnalyzeSyntaxResponse(language="ko-KR", tokens_count=3).SerializeToString()
    parsed = lpb2.AnalyzeSyntaxResponse.FromString(raw)
    assert truncation_of(parsed) is None
    assert parsed.tokens_count == 3


def test_truncation_round_trip_bytes():
    raw = lpb2.AnalyzeSyntaxResponse(truncation=_trunc()).SerializeToString()
    assert truncation_of(lpb2.AnalyzeSyntaxResponse.FromString(raw)).message == MSG
