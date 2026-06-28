# -*- coding: utf-8 -*-
"""Connect RPC 마이그레이션에 대한 오프라인 단위 테스트.

실제 서버 없이(=네트워크 없이) 동작하도록, 공식 connectrpc 스텁의 메서드를 가짜로 교체하여
요청 구성/응답 파싱/에러 변환/스트리밍 처리를 검증한다.
"""

import io
import os
import tempfile

import pytest

import bareunpy
from bareunpy import Tagger, Tokenizer, Corrector, CustomDict
from bareunpy._tagger import _resolve_port, Tagged
from bareunpy._tokenizer import Tokenized
from bareunpy._lang_service_client import (
    is_secure_host,
    build_base_address,
    build_metadata,
    BareunLanguageServiceClient,
)
from bareunpy._custom_dict import read_dic_file, pb_map_to_set
from bareunpy._custom_dict_client import build_dict_set, CustomDictionaryServiceClient

from connectrpc.client import ConnectClientSync
from connectrpc.code import Code
from connectrpc.errors import ConnectError

import bareunpy.bareun.language_service_pb2 as lpb2
import bareunpy.bareun.lang_common_pb2 as lcpb
import bareunpy.bareun.revision_service_pb2 as rpb
import bareunpy.bareun.custom_dict_pb2 as cdpb
import bareunpy.bareun.dict_common_pb2 as dcpb

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
    t = Tagger(apikey=APIKEY, host=HOST, port=PORT, custom_dicts=["law"])
    captured = {}

    def fake_analyze_list(request, headers=None, timeout_ms=None):
        captured["req"] = request
        return lpb2.AnalyzeSyntaxListResponse(sentences=_analyze_response().sentences)

    monkeypatch.setattr(t.client.stub, "analyze_syntax_list", fake_analyze_list)
    tagged = t.taglist(["오늘은 먹다"])
    assert tagged.morphs() == ["오늘", "은", "먹", "다"]
    # custom_dicts 가 analyze_syntax_list 요청에 포함되는지 확인
    assert list(captured["req"].custom_dict_names) == ["law"]


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


def test_tagger_tag_raw(monkeypatch):
    """tag_raw()가 analyze_syntax_raw를 호출하고 결과를 Tagged로 반환한다."""
    t = Tagger(apikey=APIKEY, host=HOST, port=PORT)

    captured = {}

    def fake_raw(request, headers=None, timeout_ms=None):
        # 요청 필드 캡처: document, auto_split_sentence, encoding_type
        captured["req"] = request
        return _analyze_response()

    monkeypatch.setattr(t.client.stub, "analyze_syntax_raw", fake_raw)
    result = t.tag_raw("나는밥을먹었다")

    # auto_split 기본값 False가 요청에 반영되어야 한다
    assert captured["req"].auto_split_sentence is False
    assert captured["req"].document.content == "나는밥을먹었다"
    # 반환된 Tagged는 정상적으로 형태소를 포함한다
    assert result.morphs() == ["오늘", "은", "먹", "다"]

    # auto_split=True 전달 검증
    t.tag_raw("문장1. 문장2.", auto_split=True)
    assert captured["req"].auto_split_sentence is True


def test_tagger_tag_raw_empty():
    """tag_raw()에 빈 문자열을 전달하면 빈 결과를 반환한다."""
    t = Tagger(apikey=APIKEY, host=HOST, port=PORT)
    result = t.tag_raw("")
    assert result.morphs() == []


def test_analyze_syntax_raw_translates_connect_error(monkeypatch):
    """analyze_syntax_raw에서 ConnectError가 발생하면 사람이 읽을 수 있는 예외로 변환된다."""
    cli = BareunLanguageServiceClient(APIKEY, HOST, PORT)

    def raiser(request, headers=None, timeout_ms=None):
        raise ConnectError(Code.UNAUTHENTICATED, "invalid key")

    monkeypatch.setattr(cli.stub, "analyze_syntax_raw", raiser)
    with pytest.raises(Exception) as ei:
        cli.analyze_syntax_raw("테스트")
    assert "API KEY" in str(ei.value)


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


# ============================================================================
# Tagged / Tokenized 결과 객체 — None 경로 및 다양한 메서드 커버
# ============================================================================

def _full_analyze_response():
    """nouns/verbs/adverbs 등 다양한 태그를 포함한 응답."""
    t1 = lpb2.Token(
        text=lcpb.TextSpan(content="오늘은"),
        morphemes=[
            _morph("오늘", lpb2.Morpheme.Tag.NNG),
            _morph("은", lpb2.Morpheme.Tag.JX),
        ],
    )
    t2 = lpb2.Token(
        text=lcpb.TextSpan(content="정말"),
        morphemes=[_morph("정말", lpb2.Morpheme.Tag.MAG)],
    )
    t3 = lpb2.Token(
        text=lcpb.TextSpan(content="먹다"),
        morphemes=[
            _morph("먹", lpb2.Morpheme.Tag.VV),
            _morph("다", lpb2.Morpheme.Tag.EF),
        ],
    )
    s = lpb2.Sentence(tokens=[t1, t2, t3])
    return lpb2.AnalyzeSyntaxResponse(sentences=[s])


def _full_tokenize_response():
    """다양한 hint 값을 포함한 분절 응답(S/A/J/E/I/M 포함)."""
    def seg(content, hint):
        return lpb2.Segment(text=lcpb.TextSpan(content=content), hint=hint)
    t1 = lpb2.SegmentToken(
        text=lcpb.TextSpan(content="오늘은"),
        segments=[seg("오늘", "N"), seg("은", "J")],
    )
    t2 = lpb2.SegmentToken(
        text=lcpb.TextSpan(content="정말"),
        segments=[seg("정말", "A")],
    )
    t3 = lpb2.SegmentToken(
        text=lcpb.TextSpan(content="먹는다."),
        segments=[seg("먹", "V"), seg("는", "E"), seg("다", "E"), seg(".", "S")],
    )
    s = lpb2.SegmentSentence(tokens=[t1, t2, t3])
    return lpb2.TokenizeResponse(sentences=[s])


def test_tagged_none_response():
    """r=None 으로 생성하면 빈 AnalyzeSyntaxResponse 를 기본값으로 사용한다."""
    tagged = Tagged("", None)
    assert tagged.r is not None
    assert tagged.phrase == ''
    assert tagged.pos() == []
    assert tagged.morphs() == []
    assert tagged.nouns() == []
    assert tagged.verbs() == []


def test_tagged_msg_sentences_json():
    """msg(), sentences(), as_json(), as_json_str(), print_as_json() 정상 동작."""
    resp = _full_analyze_response()
    tagged = Tagged("오늘은 정말 먹다", resp)

    assert tagged.msg() is resp
    sents = tagged.sentences()
    assert len(sents) == 1

    j = tagged.as_json()
    assert 'sentences' in j

    s = tagged.as_json_str()
    assert '"sentences"' in s

    buf = io.StringIO()
    tagged.print_as_json(out=buf)
    assert len(buf.getvalue()) > 0


def test_tagged_pos_flatten_false():
    """pos(flatten=False) 는 토큰별로 묶인 리스트를 반환한다."""
    resp = _analyze_response()
    tagged = Tagged("오늘은 먹다", resp)
    result = tagged.pos(flatten=False)
    # 2개의 토큰
    assert len(result) == 2
    # 첫 토큰 2개 형태소
    assert len(result[0]) == 2


def test_tagged_pos_detail_not_join():
    """pos(detail=True, join=False) 는 (content, tag, oov, prob) 4-튜플을 반환한다."""
    resp = _analyze_response()
    tagged = Tagged("오늘은 먹다", resp)
    result = tagged.pos(detail=True, join=False)
    # 4-튜플이어야 한다
    assert len(result[0]) == 4


def test_tagger_default_host():
    """host="" 이면 api.bareun.ai 를 기본값으로 사용한다."""
    t = Tagger(apikey=APIKEY, host="", port=5656)
    assert t.host == 'api.bareun.ai'


def test_tagger_set_domain_and_custom_dicts(monkeypatch):
    """set_domain(), set_custom_dicts() 가 정상 동작한다."""
    t = Tagger(apikey=APIKEY, host=HOST, port=PORT)
    captured = {}

    def fake_analyze(request, headers=None, timeout_ms=None):
        captured["req"] = request
        return _analyze_response()

    monkeypatch.setattr(t.client.stub, "analyze_syntax", fake_analyze)
    # set_domain: 한 항목 추가
    t.set_domain("law")
    assert "law" in t.custom_dicts
    # custom_dicts 가 요청에 포함되는지 확인 (if custom_dicts: 분기 커버)
    t.tag("오늘은 먹다")
    assert list(captured["req"].custom_dict_names) == ["law"]
    # set_custom_dicts: 교체
    t.set_custom_dicts(["news", "medical"])
    assert t.custom_dicts == ["news", "medical"]
    # 빈 리스트로 교체
    t.set_custom_dicts([])
    assert t.custom_dicts == []


def test_tagger_tags_empty():
    """tags([]) 는 네트워크 호출 없이 빈 Tagged 를 돌려준다."""
    t = Tagger(apikey=APIKEY, host=HOST, port=PORT)
    result = t.tags([])
    assert result.pos() == []


def test_tagger_taglist_empty():
    """taglist([]) 는 네트워크 호출 없이 빈 Tagged 를 돌려준다."""
    t = Tagger(apikey=APIKEY, host=HOST, port=PORT)
    result = t.taglist([])
    assert result.pos() == []


def test_tokenized_none_response():
    """r=None 으로 생성하면 빈 TokenizeResponse 를 기본값으로 사용한다."""
    tok = Tokenized("", None)
    assert tok.r is not None
    assert tok.phrase == ''
    assert tok.seg() == []


def test_tokenized_msg_sentences_json():
    """Tokenized 의 msg/sentences/as_json/as_json_str/print_as_json."""
    resp = _full_tokenize_response()
    tok = Tokenized("오늘은 정말 먹는다.", resp)

    assert tok.msg() is resp
    sents = tok.sentences()
    assert len(sents) == 1

    j = tok.as_json()
    assert 'sentences' in j

    s = tok.as_json_str()
    assert '"sentences"' in s

    buf = io.StringIO()
    tok.print_as_json(out=buf)
    assert len(buf.getvalue()) > 0


def test_tokenized_seg_flatten_false():
    """seg(flatten=False) 는 토큰별로 묶인 리스트를 반환한다."""
    resp = _full_tokenize_response()
    tok = Tokenized("오늘은 정말 먹는다.", resp)
    result = tok.seg(flatten=False)
    assert len(result) == 3  # 3개의 토큰


def test_tokenized_segment_detail_no_join():
    """seg(detail=True, join=False) 는 (content, hint) 튜플을 반환한다."""
    resp = _full_tokenize_response()
    tok = Tokenized("오늘은 정말 먹는다.", resp)
    result = tok.seg(detail=True, join=False)
    assert isinstance(result[0], tuple) and len(result[0]) == 2


def test_tokenized_extractors():
    """Tokenized 의 segments/nouns/verbs/predicates/substantives/symbols/adverbs/endings."""
    resp = _full_tokenize_response()
    tok = Tokenized("오늘은 정말 먹는다.", resp)

    assert "오늘" in tok.segments()
    assert "오늘" in tok.nouns()
    assert "먹" in tok.verbs()
    assert "먹" in tok.predicates()
    assert "오늘" in tok.substantives()
    assert "." in tok.symbols()
    assert "정말" in tok.adverbs()
    assert "는" in tok.endings()


def test_tokenized_prenouns_postpositions_interjections():
    """prenouns(M)/postpositions(J)/interjections(I) 추출기 커버."""
    def seg(content, hint):
        return lpb2.Segment(text=lcpb.TextSpan(content=content), hint=hint)
    tok_token = lpb2.SegmentToken(
        text=lcpb.TextSpan(content="그"),
        segments=[seg("그", "M")],
    )
    tok_j = lpb2.SegmentToken(
        text=lcpb.TextSpan(content="는"),
        segments=[seg("는", "J")],
    )
    tok_i = lpb2.SegmentToken(
        text=lcpb.TextSpan(content="와"),
        segments=[seg("와", "I")],
    )
    resp = lpb2.TokenizeResponse(
        sentences=[lpb2.SegmentSentence(tokens=[tok_token, tok_j, tok_i])]
    )
    tok = Tokenized("그는 와", resp)
    assert "그" in tok.prenouns()
    assert "는" in tok.postpositions()
    assert "와" in tok.interjections()


def test_tokenizer_default_host():
    """host="" 이면 api.bareun.ai 를 기본값으로 사용한다."""
    t = Tokenizer(apikey=APIKEY, host="", port=5656)
    assert t.host == 'api.bareun.ai'


def test_tokenizer_empty_phrase():
    """tokenize("") 는 네트워크 없이 빈 Tokenized 를 돌려준다."""
    t = Tokenizer(apikey=APIKEY, host=HOST, port=PORT)
    result = t.tokenize("")
    assert result.seg() == []


def test_tokenizer_empty_list():
    """tokenize_list([]) 는 네트워크 없이 빈 Tokenized 를 돌려준다."""
    t = Tokenizer(apikey=APIKEY, host=HOST, port=PORT)
    result = t.tokenize_list([])
    assert result.seg() == []


# ============================================================================
# Corrector — 미커버 분기 (기본 호스트, 빈 custom_dicts/config, print_as_json)
# ============================================================================

def test_corrector_default_host():
    """host 생략 또는 host="" 이면 api.bareun.ai 가 기본값으로 적용된다."""
    c1 = Corrector(apikey=APIKEY)
    assert c1.host == 'api.bareun.ai'
    c2 = Corrector(apikey=APIKEY, host="")
    assert c2.host == 'api.bareun.ai'


def test_corrector_correct_error_no_dicts_no_config(monkeypatch):
    """custom_dicts=[] / config=None 은 요청에 해당 필드를 채우지 않는다."""
    c = Corrector(apikey=APIKEY, host=HOST, port=PORT)
    captured = {}

    def fake(request, headers=None, timeout_ms=None):
        captured["req"] = request
        return _correct_response()

    monkeypatch.setattr(c.client.stub, "correct_error", fake)
    c.correct_error("고은 꽃")  # custom_dicts=[], config=None (기본값)
    assert len(captured["req"].custom_dict_names) == 0
    assert not captured["req"].HasField("config")


def test_corrector_stream_no_req_id_no_config(monkeypatch):
    """req_id=0/config=None 은 스트리밍 요청에 해당 필드를 채우지 않는다."""
    c = Corrector(apikey=APIKEY, host=HOST, port=PORT)
    captured = {}

    def fake_stream(request, headers=None, timeout_ms=None):
        captured["req"] = request
        return iter([rpb.StreamCorrectErrorResponse(
            first=rpb.StreamFirstCorrectError(origin="고은 꽃", revised="고운 꽃")
        )])

    monkeypatch.setattr(c.client.stub, "stream_correct_error", fake_stream)
    list(c.correct_error_stream("고은 꽃"))  # req_id=0, config=None (기본값)
    assert captured["req"].req_id == 0
    assert not captured["req"].HasField("config")


def test_corrector_print_results_with_blocks(monkeypatch):
    """print_results 는 revised_blocks 와 whitespace_cleanup_ranges 를 출력한다."""
    c = Corrector(apikey=APIKEY, host=HOST, port=PORT)

    resp = rpb.CorrectErrorResponse(
        origin="고은 꽃에물을",
        revised="고운 꽃에 물을",
        revised_sentences=[rpb.RevisedSentence(origin="고은 꽃에물을", revised="고운 꽃에 물을")],
        revised_blocks=[
            rpb.RevisedBlock(
                # RevisedBlock.origin 은 lang_common_pb2.TextSpan 타입이다
                origin=lcpb.TextSpan(content="고은", begin_offset=0, length=2),
                revised="고운",
                revisions=[
                    rpb.Revision(
                        revised="고운",
                        category="GRAMMER",
                        help_id="h1",
                    )
                ],
            )
        ],
        # helps 맵의 값 타입은 ReviseHelp 이다 (Help 가 아님)
        helps={"h1": rpb.ReviseHelp(comment="맞춤법 교정 규칙")},
        whitespace_cleanup_ranges=[
            # CleanUpRange: offset, length, position
            rpb.CleanUpRange(offset=4, length=0, position=1)
        ],
    )

    buf = io.StringIO()
    c.print_results(resp, out=buf)
    output = buf.getvalue()
    assert "고은" in output
    assert "고운" in output


def test_corrector_print_as_json(monkeypatch):
    """print_as_json 은 파일로 JSON 을 출력한다."""
    c = Corrector(apikey=APIKEY, host=HOST, port=PORT)
    buf = io.StringIO()
    c.print_as_json(_correct_response(), out=buf)
    assert '"revised"' in buf.getvalue()


# ============================================================================
# CustomDict — 파일 읽기, pb_map_to_set, read_*/copy_* 메서드
# ============================================================================

def test_read_dic_file():
    """read_dic_file 은 '#' 주석과 빈 줄을 무시하고 단어를 set 으로 반환한다."""
    content = "# 주석 줄\n사과\n바나나\n\n# 또 주석\n포도\n"
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(content)
        fname = f.name
    try:
        result = read_dic_file(fname)
        assert result == {'사과', '바나나', '포도'}
    finally:
        os.unlink(fname)


def test_pb_map_to_set():
    """pb_map_to_set 은 DictSet 의 items 키를 set 으로 변환한다."""
    ds = dcpb.DictSet(items={"사과": 1, "바나나": 1})
    result = pb_map_to_set(ds)
    assert result == {"사과", "바나나"}


def test_custom_dict_read_from_files():
    """read_*_from_file 메서드들이 파일을 읽어 해당 set 을 채운다."""
    content = "가\n나\n다\n"
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(content)
        fname = f.name
    try:
        cd = CustomDict(APIKEY, "test", HOST, PORT)
        cd.read_np_set_from_file(fname)
        assert cd.np_set == {"가", "나", "다"}
        cd.read_cp_set_from_file(fname)
        assert cd.cp_set == {"가", "나", "다"}
        cd.read_cp_caret_set_from_file(fname)
        assert cd.cp_caret_set == {"가", "나", "다"}
        cd.read_vv_set_from_file(fname)
        assert cd.vv_set == {"가", "나", "다"}
        cd.read_va_set_from_file(fname)
        assert cd.va_set == {"가", "나", "다"}
    finally:
        os.unlink(fname)


def test_custom_dict_copy_all_sets():
    """copy_np/cp_caret/va_set 이 해당 set 을 교체한다."""
    cd = CustomDict(APIKEY, "test", HOST, PORT)
    cd.copy_np_set({"누루하치"})
    assert cd.np_set == {"누루하치"}
    cd.copy_cp_caret_set({"인공지능^데이터"})
    assert cd.cp_caret_set == {"인공지능^데이터"}
    cd.copy_va_set({"드라마틱하"})
    assert cd.va_set == {"드라마틱하"}


def test_custom_dict_get(monkeypatch):
    """get() 은 서버에서 사용자 사전 전체를 가져온다."""
    cd = CustomDict(APIKEY, "law", HOST, PORT)
    expected = cdpb.CustomDictionary()
    monkeypatch.setattr(
        cd.stub.stub, "get_custom_dictionary",
        lambda req, headers=None, timeout_ms=None: cdpb.GetCustomDictionaryResponse(dict=expected),
    )
    result = cd.get()
    assert result == expected


def test_custom_dict_load(monkeypatch):
    """load() 는 서버에서 np_set/cp_caret_set/cp_set 을 받아 내부 set 을 채운다."""
    cd = CustomDict(APIKEY, "law", HOST, PORT)
    server_dict = cdpb.CustomDictionary(
        np_set=dcpb.DictSet(items={"유리왕": 1}),
        cp_set=dcpb.DictSet(items={"코로나19": 1}),
        cp_caret_set=dcpb.DictSet(items={"인공지능^학습": 1}),
    )
    monkeypatch.setattr(
        cd.stub.stub, "get_custom_dictionary",
        lambda req, headers=None, timeout_ms=None: cdpb.GetCustomDictionaryResponse(dict=server_dict),
    )
    cd.load()
    assert "유리왕" in cd.np_set
    assert "코로나19" in cd.cp_set
    assert "인공지능^학습" in cd.cp_caret_set


def test_custom_dict_clear(monkeypatch):
    """clear() 는 내부 set 을 비우고 서버에서 삭제된 도메인 이름을 반환한다."""
    cd = CustomDict(APIKEY, "law", HOST, PORT)
    cd.copy_np_set({"유리왕"})
    cd.copy_cp_set({"코로나19"})

    monkeypatch.setattr(
        cd.stub.stub, "remove_custom_dictionaries",
        lambda req, headers=None, timeout_ms=None: cdpb.RemoveCustomDictionariesResponse(
            deleted_domain_names={"law": True}
        ),
    )
    deleted = cd.clear()
    assert "law" in deleted
    assert len(cd.np_set) == 0
    assert len(cd.cp_set) == 0


# ============================================================================
# CustomDictionaryServiceClient.get() — 미커버 라인 95-98
# ============================================================================

def test_custom_dict_client_get(monkeypatch):
    """get() 은 GetCustomDictionaryRequest 를 보내고 dict 를 반환한다."""
    cli = CustomDictionaryServiceClient(APIKEY, HOST, PORT)
    expected_dict = cdpb.CustomDictionary()
    captured = {}

    def fake_get(request, headers=None, timeout_ms=None):
        captured["domain"] = request.domain_name
        captured["headers"] = headers
        return cdpb.GetCustomDictionaryResponse(dict=expected_dict)

    monkeypatch.setattr(cli.stub, "get_custom_dictionary", fake_get)
    result = cli.get("law")
    assert result == expected_dict
    assert captured["domain"] == "law"
    assert captured["headers"]["api-key"] == APIKEY


# ============================================================================
# BareunRevisionServiceClient.correct_error ConnectError 처리 — 라인 67-68
# ============================================================================

def test_revision_client_correct_error_connect_error(monkeypatch):
    """correct_error 에서 ConnectError 가 발생하면 사용자 친화적 예외로 변환된다."""
    from bareunpy._revision_service_client import BareunRevisionServiceClient
    cli = BareunRevisionServiceClient(APIKEY, HOST, PORT)

    def raiser(request, headers=None, timeout_ms=None):
        raise ConnectError(Code.PERMISSION_DENIED, "bad key")

    monkeypatch.setattr(cli.stub, "correct_error", raiser)
    with pytest.raises(Exception) as ei:
        cli.correct_error(rpb.CorrectErrorRequest())
    assert "API KEY" in str(ei.value)


# ============================================================================
# BareunLanguageServiceClient — analyze_syntax_list/tokenize ConnectError 라인 197-198, 226-227
# ============================================================================

def test_analyze_syntax_list_connect_error(monkeypatch):
    """analyze_syntax_list 에서 ConnectError 가 발생하면 변환된다."""
    cli = BareunLanguageServiceClient(APIKEY, HOST, PORT)

    def raiser(request, headers=None, timeout_ms=None):
        raise ConnectError(Code.UNAVAILABLE, "down")

    monkeypatch.setattr(cli.stub, "analyze_syntax_list", raiser)
    with pytest.raises(Exception) as ei:
        cli.analyze_syntax_list(["안녕"], [])
    assert "연결할 수 없습니다" in str(ei.value)


def test_tokenize_connect_error(monkeypatch):
    """tokenize 에서 ConnectError 가 발생하면 변환된다."""
    cli = BareunLanguageServiceClient(APIKEY, HOST, PORT)

    def raiser(request, headers=None, timeout_ms=None):
        raise ConnectError(Code.UNAVAILABLE, "down")

    monkeypatch.setattr(cli.stub, "tokenize", raiser)
    with pytest.raises(Exception) as ei:
        cli.tokenize("안녕")
    assert "연결할 수 없습니다" in str(ei.value)


# ============================================================================
# 나머지 98% → 100% 커버 — 이전 라운드에서 남은 분기들
# ============================================================================

def test_tagger_tags_nonempty(monkeypatch):
    """tags(["문장"]) 는 non-empty 분기(lines 239-241)를 실행한다."""
    t = Tagger(apikey=APIKEY, host=HOST, port=PORT)
    monkeypatch.setattr(
        t.client.stub, "analyze_syntax",
        lambda request, headers=None, timeout_ms=None: _analyze_response(),
    )
    # tags() 는 내부적으로 '\n'.join 후 analyze_syntax 를 호출한다.
    result = t.tags(["오늘은 먹다"])
    assert result.morphs() == ["오늘", "은", "먹", "다"]


def test_tagger_set_domain_appends_when_nonempty():
    """set_domain() 은 custom_dicts 가 이미 있을 때도 항목을 추가한다(line 194->196 False 경로)."""
    import warnings
    t = Tagger(apikey=APIKEY, host=HOST, port=PORT, custom_dicts=["law"])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        t.set_domain("news")
    # 기존 항목이 유지되고 새 항목이 추가되어야 한다
    assert "law" in t.custom_dicts
    assert "news" in t.custom_dicts


def test_tokenized_seg_join_no_detail():
    """seg(join=True, detail=False) 는 'content' 문자열만 반환한다(line 77)."""
    resp = _full_tokenize_response()
    tok = Tokenized("오늘은 정말 먹는다.", resp)
    result = tok.seg(join=True, detail=False)
    # join=True, detail=False: 내용만 반환('오늘/N' 아닌 '오늘')
    assert result[0] == "오늘"
    # detail=True 면 hint 포함
    result_detail = tok.seg(join=True, detail=True)
    assert result_detail[0] == "오늘/N"


def test_corrector_stream_with_custom_dicts_and_config(monkeypatch):
    """스트리밍 교정에서 custom_dicts와 config 가 요청에 포함된다(lines 135, 137)."""
    c = Corrector(apikey=APIKEY, host=HOST, port=PORT)
    captured = {}

    def fake_stream(request, headers=None, timeout_ms=None):
        captured["req"] = request
        return iter([rpb.StreamCorrectErrorResponse(
            first=rpb.StreamFirstCorrectError(origin="고은 꽃", revised="고운 꽃")
        )])

    monkeypatch.setattr(c.client.stub, "stream_correct_error", fake_stream)
    cfg = rpb.RevisionConfig(disable_typo_correction=True)
    list(c.correct_error_stream("고은 꽃", custom_dicts=["law"], config=cfg))
    # custom_dict_names 가 채워졌는지
    assert list(captured["req"].custom_dict_names) == ["law"]
    # config 가 채워졌는지
    assert captured["req"].config.disable_typo_correction is True


def test_custom_dict_load_exception(monkeypatch):
    """load() 에서 ConnectError 가 발생하면 조용히 무시한다."""
    cd = CustomDict(APIKEY, "law", HOST, PORT)

    def raise_error(req, headers=None, timeout_ms=None):
        raise ConnectError(Code.UNAVAILABLE, "server error")

    monkeypatch.setattr(cd.stub.stub, "get_custom_dictionary", raise_error)
    # ConnectError 는 전파되지 않아야 한다
    cd.load()
    assert len(cd.np_set) == 0
