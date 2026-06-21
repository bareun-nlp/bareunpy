# -*- coding: utf-8 -*-
"""Connect RPC 마이그레이션에 대한 오프라인 단위 테스트.

실제 서버 없이(=네트워크 없이) 동작하도록, 공식 connectrpc 스텁의 메서드를 가짜로 교체하여
요청 구성/응답 파싱/에러 변환/스트리밍 처리를 검증한다.
"""

import pytest

import bareunpy
from bareunpy import Tagger, Tokenizer, Corrector, CustomDict
from bareunpy._tagger import _resolve_port
from bareunpy._lang_service_client import (
    is_secure_host,
    build_base_address,
    build_metadata,
    BareunLanguageServiceClient,
)
from bareunpy._custom_dict_client import build_dict_set, CustomDictionaryServiceClient

from connectrpc.client import ConnectClientSync
from connectrpc.code import Code
from connectrpc.errors import ConnectError

import bareun.language_service_pb2 as lpb2
import bareun.lang_common_pb2 as lcpb
import bareun.revision_service_pb2 as rpb
import bareun.custom_dict_pb2 as cdpb
import bareun.dict_common_pb2 as dcpb

APIKEY = "koba-TESTKEY"
HOST = "localhost"
PORT = 5656


# ----------------------------------------------------------------------------
# 가짜 응답 빌더 (실제 protobuf 메시지를 구성)
# ----------------------------------------------------------------------------
def _morph(content, tag, oov=0, prob=0.0):
    return lpb2.Morpheme(
        text=lcpb.TextSpan(content=content), tag=tag, out_of_vocab=oov, probability=prob
    )


def _analyze_response():
    """'오늘은 먹다' 정도의 간단한 형태소 분석 응답(명사/동사 추출 검증용)."""
    t1 = lpb2.Token(
        text=lcpb.TextSpan(content="오늘은"),
        morphemes=[
            _morph("오늘", lpb2.Morpheme.Tag.NNG),
            _morph("은", lpb2.Morpheme.Tag.JX),
        ],
    )
    t2 = lpb2.Token(
        text=lcpb.TextSpan(content="먹다"),
        morphemes=[
            _morph("먹", lpb2.Morpheme.Tag.VV, oov=lpb2.Morpheme.OutOfVocab.OUT_OF_VOCAB, prob=0.9),
            _morph("다", lpb2.Morpheme.Tag.EF),
        ],
    )
    s = lpb2.Sentence(tokens=[t1, t2])
    return lpb2.AnalyzeSyntaxResponse(sentences=[s])


def _tokenize_response():
    tok = lpb2.SegmentToken(
        text=lcpb.TextSpan(content="오늘은"),
        segments=[
            lpb2.Segment(text=lcpb.TextSpan(content="오늘"), hint="N"),
            lpb2.Segment(text=lcpb.TextSpan(content="은"), hint="J"),
        ],
    )
    tok2 = lpb2.SegmentToken(
        text=lcpb.TextSpan(content="춥다"),
        segments=[lpb2.Segment(text=lcpb.TextSpan(content="춥다"), hint="V")],
    )
    s = lpb2.SegmentSentence(tokens=[tok, tok2])
    return lpb2.TokenizeResponse(sentences=[s])


# ----------------------------------------------------------------------------
# 헬퍼 함수
# ----------------------------------------------------------------------------
def test_resolve_port():
    assert _resolve_port("api.bareun.ai", None) == 443
    assert _resolve_port("localhost", None) == 5656
    assert _resolve_port("api.bareun.ai", 9999) == 9999  # 명시 포트 우선


def test_is_secure_host_and_address():
    assert is_secure_host("api.bareun.ai") is True
    assert is_secure_host("API.BAREUN.AI") is True
    assert is_secure_host("localhost") is False
    assert build_base_address("api.bareun.ai", 443) == "https://api.bareun.ai:443"
    assert build_base_address("localhost", 5656) == "http://localhost:5656"


def test_build_metadata_has_apikey_and_user_agent():
    # api-key 와 user-agent 가 모든 요청 헤더로 전달되도록 구성한다.
    md = build_metadata(APIKEY)
    assert md["api-key"] == APIKEY
    assert md["user-agent"] == f"bareunpy/{bareunpy.version}"


# ----------------------------------------------------------------------------
# 생성자 / 검증
# ----------------------------------------------------------------------------
def test_clients_construct_with_connect_stub():
    t = Tagger(apikey=APIKEY, host=HOST, port=PORT)
    tok = Tokenizer(apikey=APIKEY, host=HOST, port=PORT)
    c = Corrector(apikey=APIKEY, host=HOST, port=PORT)
    assert isinstance(t.client.stub, ConnectClientSync)
    assert isinstance(tok.client.stub, ConnectClientSync)
    assert isinstance(c.client.stub, ConnectClientSync)
    assert t.client.stub._address == "http://localhost:5656"
    # api-key 가 헤더 메타데이터로 전달되도록 구성되어 있어야 한다.
    assert t.client.metadata["api-key"] == APIKEY


def test_apikey_required():
    with pytest.raises(ValueError):
        Tagger(apikey="", host=HOST, port=PORT)
    with pytest.raises(ValueError):
        Tokenizer(apikey="", host=HOST, port=PORT)
    with pytest.raises(ValueError):
        Corrector(apikey="", host=HOST, port=PORT)


def test_custom_dict_domain_required():
    with pytest.raises(ValueError):
        CustomDict(APIKEY, None, HOST, PORT)


# ----------------------------------------------------------------------------
# Tagger / Tokenizer 분석 결과 파싱 (가짜 응답)
# ----------------------------------------------------------------------------
def test_tagger_pos_and_extractors(monkeypatch):
    t = Tagger(apikey=APIKEY, host=HOST, port=PORT)
    monkeypatch.setattr(
        t.client.stub, "analyze_syntax",
        lambda request, headers=None, timeout_ms=None: _analyze_response(),
    )
    assert t.pos("오늘은 먹다") == [
        ("오늘", "NNG"), ("은", "JX"), ("먹", "VV"), ("다", "EF"),
    ]
    assert t.pos("오늘은 먹다", join=True)[0] == "오늘/NNG"
    # detail=True 는 oov/확률을 포함한다.
    assert t.pos("오늘은 먹다", join=True, detail=True)[2] == "먹/VV:0.900#OUT_OF_VOCAB"
    assert t.morphs("오늘은 먹다") == ["오늘", "은", "먹", "다"]
    assert t.nouns("오늘은 먹다") == ["오늘"]
    assert t.verbs("오늘은 먹다") == ["먹"]


def test_tagger_empty_phrase_returns_empty():
    t = Tagger(apikey=APIKEY, host=HOST, port=PORT)
    # 빈 문자열은 네트워크 호출 없이 빈 결과를 돌려준다.
    assert t.pos("") == []
    assert t.tags([]).pos() == []


def test_tagger_taglist(monkeypatch):
    t = Tagger(apikey=APIKEY, host=HOST, port=PORT)
    monkeypatch.setattr(
        t.client.stub, "analyze_syntax_list",
        lambda request, headers=None, timeout_ms=None: lpb2.AnalyzeSyntaxListResponse(
            sentences=_analyze_response().sentences
        ),
    )
    tagged = t.taglist(["오늘은 먹다"])
    assert tagged.morphs() == ["오늘", "은", "먹", "다"]


def test_tokenizer_seg_and_extractors(monkeypatch):
    tok = Tokenizer(apikey=APIKEY, host=HOST, port=PORT)
    monkeypatch.setattr(
        tok.client.stub, "tokenize",
        lambda request, headers=None, timeout_ms=None: _tokenize_response(),
    )
    assert tok.segments("오늘은 춥다") == ["오늘", "은", "춥다"]
    assert tok.nouns("오늘은 춥다") == ["오늘"]
    assert tok.verbs("오늘은 춥다") == ["춥다"]
    assert tok.seg("오늘은 춥다", join=True, detail=True)[0] == "오늘/N"


def test_tokenizer_request_reflects_current_protos(monkeypatch):
    """현재 protos 반영: TokenizeRequest.auto_spacing 전달, auto_split 패스스루."""
    tok = Tokenizer(apikey=APIKEY, host=HOST, port=PORT)
    captured = {}

    def fake(request, headers=None, timeout_ms=None):
        captured["req"] = request
        return _tokenize_response()

    monkeypatch.setattr(tok.client.stub, "tokenize", fake)
    tok.tokenize("오늘은 춥다")  # 기본값
    assert captured["req"].auto_spacing is True
    assert captured["req"].auto_split_sentence is False
    tok.tokenize("오늘은 춥다", auto_split=True, auto_spacing=False)
    assert captured["req"].auto_spacing is False
    assert captured["req"].auto_split_sentence is True
    tok.tokenize_list(["오늘은 춥다"], auto_spacing=False)
    assert captured["req"].auto_spacing is False


# ----------------------------------------------------------------------------
# Corrector (단발 + 스트리밍)
# ----------------------------------------------------------------------------
def _correct_response():
    return rpb.CorrectErrorResponse(
        origin="고은 꽃", revised="고운 꽃",
        revised_sentences=[rpb.RevisedSentence(origin="고은 꽃", revised="고운 꽃")],
    )


def test_corrector_correct_error(monkeypatch):
    c = Corrector(apikey=APIKEY, host=HOST, port=PORT)
    captured = {}

    def fake(request, headers=None, timeout_ms=None):
        captured["req"] = request
        captured["headers"] = headers
        return _correct_response()

    monkeypatch.setattr(c.client.stub, "correct_error", fake)
    cfg = rpb.RevisionConfig(disable_typo_correction=True)
    res = c.correct_error("고은 꽃", custom_dicts=["law"], config=cfg)
    assert res.revised == "고운 꽃"
    # 요청에 사용자 사전/설정/문서가 제대로 담겼는지 확인
    assert list(captured["req"].custom_dict_names) == ["law"]
    assert captured["req"].config.disable_typo_correction is True
    assert captured["req"].document.content == "고은 꽃"
    assert captured["headers"]["api-key"] == APIKEY
    # JSON 변환 헬퍼
    assert c.as_json(res)["revised"] == "고운 꽃"
    assert '"revised": "고운 꽃"' in c.as_json_str(res)


def test_corrector_stream(monkeypatch):
    c = Corrector(apikey=APIKEY, host=HOST, port=PORT)
    captured = {}

    def fake_stream(request, headers=None, timeout_ms=None):
        captured["req_id"] = request.req_id
        first = rpb.StreamCorrectErrorResponse(
            first=rpb.StreamFirstCorrectError(origin="고은 꽃", revised="고운 꽃")
        )
        progress = rpb.StreamCorrectErrorResponse(
            progress=rpb.ProgressRevision(req_id=request.req_id, thinking_id=1, thinking_msg="검토중")
        )
        return iter([first, progress])

    monkeypatch.setattr(c.client.stub, "stream_correct_error", fake_stream)
    out = list(c.correct_error_stream("고은 꽃", req_id=42))
    assert captured["req_id"] == 42
    assert out[0].WhichOneof("res") == "first"
    assert out[0].first.revised == "고운 꽃"
    assert out[1].WhichOneof("res") == "progress"


def test_corrector_stream_error_is_translated(monkeypatch):
    c = Corrector(apikey=APIKEY, host=HOST, port=PORT)

    def fake_stream(request, headers=None, timeout_ms=None):
        def gen():
            raise ConnectError(Code.PERMISSION_DENIED, "bad key")
            yield  # generator 로 만들기 위한 도달 불가 코드
        return gen()

    monkeypatch.setattr(c.client.stub, "stream_correct_error", fake_stream)
    with pytest.raises(Exception) as ei:
        list(c.correct_error_stream("고은 꽃"))
    assert "API KEY" in str(ei.value)


# ----------------------------------------------------------------------------
# 에러 변환
# ----------------------------------------------------------------------------
@pytest.mark.parametrize("code,needle", [
    (Code.PERMISSION_DENIED, "API KEY"),
    (Code.UNAUTHENTICATED, "API KEY"),
    (Code.UNAVAILABLE, "연결할 수 없습니다"),
    (Code.INVALID_ARGUMENT, "잘못된 요청"),
])
def test_handle_connect_error_mapped(code, needle):
    cli = BareunLanguageServiceClient(APIKEY, HOST, PORT)
    with pytest.raises(Exception) as ei:
        cli._handle_connect_error(ConnectError(code, "msg"))
    assert needle in str(ei.value)


def test_handle_connect_error_passthrough():
    cli = BareunLanguageServiceClient(APIKEY, HOST, PORT)
    # 매핑되지 않은 코드는 원본 ConnectError 을 그대로 전파한다.
    with pytest.raises(ConnectError):
        cli._handle_connect_error(ConnectError(Code.INTERNAL, "boom"))


def test_analyze_syntax_translates_connect_error(monkeypatch):
    cli = BareunLanguageServiceClient(APIKEY, HOST, PORT)

    def raiser(request, headers=None, timeout_ms=None):
        raise ConnectError(Code.UNAVAILABLE, "down")

    monkeypatch.setattr(cli.stub, "analyze_syntax", raiser)
    with pytest.raises(Exception) as ei:
        cli.analyze_syntax("안녕")
    assert "연결할 수 없습니다" in str(ei.value)


# ----------------------------------------------------------------------------
# 사용자 사전
# ----------------------------------------------------------------------------
def test_build_dict_set():
    ds = build_dict_set("law", "np-set", {"가", "나"})
    assert ds.name == "law-np-set"
    assert ds.type == dcpb.DictType.WORD_LIST
    assert set(ds.items.keys()) == {"가", "나"}
    assert all(v == 1 for v in ds.items.values())


def test_custom_dict_update(monkeypatch):
    cd = CustomDict(APIKEY, "law", HOST, PORT)
    captured = {}

    def fake_update(request, headers=None, timeout_ms=None):
        captured["req"] = request
        captured["headers"] = headers
        return cdpb.UpdateCustomDictionaryResponse(updated_domain_name="law")

    monkeypatch.setattr(cd.stub.stub, "update_custom_dictionary", fake_update)
    cd.copy_cp_set({"코로나19", "K방역"})
    cd.copy_vv_set({"카톡하"})
    assert cd.update() is True
    assert captured["req"].domain_name == "law"
    assert captured["headers"]["api-key"] == APIKEY
    # cp_set 이 요청에 반영되었는지
    assert set(captured["req"].dict.cp_set.items.keys()) == {"코로나19", "K방역"}


def test_custom_dict_client_list_and_remove(monkeypatch):
    cli = CustomDictionaryServiceClient(APIKEY, HOST, PORT)
    monkeypatch.setattr(
        cli.stub, "get_custom_dictionary_list",
        lambda request, headers=None, timeout_ms=None: cdpb.GetCustomDictionaryListResponse(
            domain_dicts=[cdpb.CustomDictionaryMeta(domain_name="law")]
        ),
    )
    metas = cli.get_list()
    assert metas[0].domain_name == "law"

    def fake_remove(request, headers=None, timeout_ms=None):
        # all=True 면 전체 삭제로 동작
        return cdpb.RemoveCustomDictionariesResponse(deleted_domain_names={"law": True})

    monkeypatch.setattr(cli.stub, "remove_custom_dictionaries", fake_remove)
    assert list(cli.remove_all()) == ["law"]
    assert list(cli.remove(["law"])) == ["law"]


def test_tagger_custom_dict_helper(monkeypatch):
    t = Tagger(apikey=APIKEY, host=HOST, port=PORT)
    cd = t.custom_dict("law")
    assert isinstance(cd, CustomDict)
    # 같은 이름은 캐시된 동일 객체를 돌려준다.
    assert t.custom_dict("law") is cd
    with pytest.raises(ValueError):
        t.custom_dict("")


def test_close_methods():
    """close() 가 예외 없이 동작한다(오프라인)."""
    c = Corrector(apikey=APIKEY, host=HOST, port=PORT)
    c.close()
    cli = BareunLanguageServiceClient(APIKEY, HOST, PORT)
    cli.close()
    cdc = CustomDictionaryServiceClient(APIKEY, HOST, PORT)
    cdc.close()
