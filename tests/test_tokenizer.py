#!env python3
# -*- coding: utf-8 -*-
"""Tokenizer 통합 테스트.

실제 api.bareun.ai 서버로 호출해 분절(tokenize) 결과를 검증한다.
환경변수:
  BAREUN_API_KEY  (필수)  유효한 API 키
  BAREUN_HOST     (선택)  서버 호스트, 기본값 api.bareun.ai
  BAREUN_PORT     (선택)  서버 포트, 기본값 443
"""
import os
import pytest
from bareunpy import Tokenized
import bareunpy


def _api_key() -> str:
    return os.environ.get("BAREUN_API_KEY", "")


def _host() -> str:
    return os.environ.get("BAREUN_HOST", "api.bareun.ai")


def _port() -> int:
    return int(os.environ.get("BAREUN_PORT", "443"))


TEST_STR = '오늘은 정말 추운 날이네요.'


@pytest.fixture
def tokenizer_instance():
    return bareunpy.Tokenizer(apikey=_api_key(), host=_host(), port=_port())


@pytest.fixture
def tokenizer_error_host_instance():
    """호스트에 포트 번호가 섞인 잘못된 형식(오류 경로 검증용)."""
    host_with_port = f"{_host()}:{_port()}"
    return bareunpy.Tokenizer(apikey=_api_key(), host=host_with_port, port=_port())


@pytest.fixture
def tokenizer_error_apikey_instance():
    """유효하지 않은 API 키(오류 경로 검증용)."""
    return bareunpy.Tokenizer(apikey="koba-INVALID-KEY", host=_host(), port=_port())


@pytest.fixture
def sample1():
    return TEST_STR


@pytest.fixture
def tokenized(tokenizer_instance) -> Tokenized:
    """실서버 호출 결과를 반환하는 fixture."""
    return tokenizer_instance.tokenize(TEST_STR)


def test_tokenizer_seg_not_flatten(tokenizer_instance, sample1):
    assert tokenizer_instance.seg(sample1, flatten=False) == [
        [('오늘'), ('은')],
        [('정말')],
        [('춥'), ('ㄴ')],
        [('날'), ('이'), ('네'), ('요'), ('.')],
    ]


def test_tokenizer_seg_join(tokenizer_instance, sample1):
    assert tokenizer_instance.seg(sample1, join=True, detail=True) == [
        '오늘/N', '은/J', '정말/A', '춥/V', 'ㄴ/E',
        '날/N', '이/V', '네/E', '요/J', './S',
    ]


def test_tokenizer_seg_detail(tokenizer_instance, sample1):
    temp = tokenizer_instance.seg(sample1, detail=True)
    temp2 = [(t[0], t[1]) for t in temp]
    assert temp2 == [
        ('오늘', 'N'), ('은', 'J'), ('정말', 'A'), ('춥', 'V'), ('ㄴ', 'E'),
        ('날', 'N'), ('이', 'V'), ('네', 'E'), ('요', 'J'), ('.', 'S'),
    ]


def test_tokenizer_seg(tokenizer_instance, sample1):
    assert tokenizer_instance.seg(sample1) == [
        '오늘', '은', '정말', '춥', 'ㄴ', '날', '이', '네', '요', '.'
    ]


def test_tokenizer_nouns(tokenizer_instance, sample1):
    assert tokenizer_instance.nouns(sample1) == ['오늘', '날']


def test_tokenizer_tokenize_as_json_str(tokenizer_instance, sample1):
    j = tokenizer_instance.tokenize(sample1).as_json()
    assert len(j['sentences']) == 1
    tokens = j['sentences'][0]['tokens']
    assert len(tokens) == 4
    assert len(tokens[0]['segments']) == 2
    assert len(tokens[1]['segments']) == 1
    assert len(tokens[2]['segments']) == 2
    assert len(tokens[3]['segments']) == 5


def test_tokenizer_tokenize_as_msg(tokenizer_instance, sample1):
    m = tokenizer_instance.tokenize(sample1).msg()
    assert m.sentences[0].tokens[3].tagged == '날/N+이/V+네/E+요/J+./S'


def test_tokenizer_tokenize_print_as_json(tokenizer_instance, sample1):
    import tempfile
    with tempfile.TemporaryFile('w+') as f:
        tokenizer_instance.tokenize(sample1).print_as_json(out=f)
        assert f.tell() > 0


def test_tokenized_nouns(tokenized: Tokenized):
    assert tokenized.nouns() == ['오늘', '날']


def test_tokenized_verbs(tokenized: Tokenized):
    assert tokenized.predicates() == ['춥', '이']


def test_tokenized_symbols(tokenized: Tokenized):
    assert tokenized.symbols() == ['.']


def test_tokenized_adverbs(tokenized: Tokenized):
    assert tokenized.adverbs() == ['정말']


def test_tokenized_endings(tokenized: Tokenized):
    assert tokenized.endings() == ['ㄴ', '네']


def test_tokenized_postpositions(tokenized: Tokenized):
    assert tokenized.postpositions() == ['은', '요']


def test_tokenizer_auto_spacing(tokenizer_instance):
    """auto_spacing 파라미터(TokenizeRequest 필드 5)가 정상 전달되는지 확인한다."""
    result = tokenizer_instance.tokenize(TEST_STR, auto_spacing=False)
    assert result is not None


def test_exception_apikey_tokenizer(tokenizer_error_apikey_instance, sample1):
    """잘못된 API 키로 호출하면 사람이 읽을 수 있는 오류 메시지를 던진다."""
    with pytest.raises(Exception) as exc_info:
        tokenizer_error_apikey_instance.tokenize(sample1).msg()
    assert exc_info.value.args[0][:27] == '\n입력한 API KEY가 정확한지 확인해 주세요.'


def test_exception_host_tokenizer(tokenizer_error_host_instance, sample1):
    """호스트에 포트가 섞인 잘못된 형식이면 연결 오류 메시지를 던진다."""
    with pytest.raises(Exception) as exc_info:
        tokenizer_error_host_instance.tokenize(sample1).msg()
    assert exc_info.value.args[0][:16] == '\n서버에 연결할 수 없습니다.'
