#!env python3
# -*- coding: utf-8 -*-
"""Tagger 통합 테스트.

실제 api.bareun.ai 서버로 호출해 형태소 분석 결과와 사용자 사전 API를 검증한다.
환경변수:
  BAREUN_API_KEY  (필수)  유효한 API 키
  BAREUN_HOST     (선택)  서버 호스트, 기본값 api.bareun.ai
  BAREUN_PORT     (선택)  서버 포트, 기본값 443
"""
import os
import pytest
import bareunpy


def _api_key() -> str:
    """환경변수에서 API 키를 읽는다. 없으면 빈 문자열을 반환한다."""
    return os.environ.get("BAREUN_API_KEY", "")


def _host() -> str:
    return os.environ.get("BAREUN_HOST", "api.bareun.ai")


def _port() -> int:
    return int(os.environ.get("BAREUN_PORT", "443"))


@pytest.fixture
def tagger_instance():
    return bareunpy.Tagger(apikey=_api_key(), host=_host(), port=_port())


@pytest.fixture
def tagger_error_host_instance():
    """호스트에 포트 번호가 섞인 잘못된 형식으로 생성한다(오류 경로 검증용)."""
    host_with_port = f"{_host()}:{_port()}"
    return bareunpy.Tagger(apikey=_api_key(), host=host_with_port, port=_port())


@pytest.fixture
def tagger_error_apikey_instance():
    """의도적으로 짧은(유효하지 않은) API 키로 생성한다(오류 경로 검증용)."""
    return bareunpy.Tagger(apikey="koba-INVALID-KEY", host=_host(), port=_port())


@pytest.fixture
def sample1():
    return '오늘은 정말 추운 날이네요.'


def test_tagger_pos(tagger_instance, sample1):
    assert tagger_instance.pos(sample1) == [
        ('오늘', 'NNG'),
        ('은', 'JX'),
        ('정말', 'MAG'),
        ('춥', 'VA'),
        ('ㄴ', 'ETM'),
        ('날', 'NNG'),
        ('이', 'VCP'),
        ('네', 'EF'),
        ('요', 'JX'),
        ('.', 'SF'),
    ]


def test_tagger_pos_join(tagger_instance, sample1):
    assert tagger_instance.pos(sample1, join=True) == [
        '오늘/NNG', '은/JX', '정말/MAG', '춥/VA', 'ㄴ/ETM',
        '날/NNG', '이/VCP', '네/EF', '요/JX', './SF',
    ]


def test_tagger_pos_detail(tagger_instance, sample1):
    temp = tagger_instance.pos(sample1, detail=True)
    temp2 = [(t[0], t[1], t[2]) for t in temp]
    assert temp2 == [
        ('오늘', 'NNG', 'IN_WORD_EMBEDDING'),
        ('은', 'JX', 'IN_WORD_EMBEDDING'),
        ('정말', 'MAG', 'IN_WORD_EMBEDDING'),
        ('춥', 'VA', 'IN_WORD_EMBEDDING'),
        ('ㄴ', 'ETM', 'IN_WORD_EMBEDDING'),
        ('날', 'NNG', 'IN_WORD_EMBEDDING'),
        ('이', 'VCP', 'IN_WORD_EMBEDDING'),
        ('네', 'EF', 'IN_WORD_EMBEDDING'),
        ('요', 'JX', 'IN_WORD_EMBEDDING'),
        ('.', 'SF', 'IN_WORD_EMBEDDING'),
    ]


def test_tagger_morphs(tagger_instance, sample1):
    assert tagger_instance.morphs(sample1) == [
        '오늘', '은', '정말', '춥', 'ㄴ', '날', '이', '네', '요', '.'
    ]


def test_tagger_nouns(tagger_instance, sample1):
    assert tagger_instance.nouns(sample1) == ['오늘', '날']


def test_tagger_tag_as_json_str(tagger_instance, sample1):
    j = tagger_instance.tag(sample1).as_json()
    assert len(j['sentences']) == 1
    tokens = j['sentences'][0]['tokens']
    assert len(tokens) == 4
    assert len(tokens[0]['morphemes']) == 2
    assert len(tokens[1]['morphemes']) == 1
    assert len(tokens[2]['morphemes']) == 2
    assert len(tokens[3]['morphemes']) == 5


def test_tagger_tag_as_msg(tagger_instance, sample1):
    m = tagger_instance.tag(sample1).msg()
    assert m.sentences[0].tokens[3].tagged == '날/NNG+이/VCP+네/EF+요/JX+./SF'


def test_tagger_tag_print_as_json(tagger_instance, sample1):
    import tempfile
    with tempfile.TemporaryFile('w+') as f:
        tagger_instance.tag(sample1).print_as_json(out=f)
        assert f.tell() > 0


def test_tagger_create_custom_dict(tagger_instance):
    cd = tagger_instance.custom_dict('my')
    assert cd is not None


def test_tagger_update_custom_dict(tagger_instance):
    cd = tagger_instance.custom_dict('my')
    cd.copy_np_set({'유리왕', '근초고왕', '누루하치', '베링거인겔하임'})
    cd.copy_cp_set({'코로나19'})
    cd.copy_cp_caret_set({'인공지능^데이터^학습', '자연어^처리^엔진'})
    cd.update()


def test_tagger_get_custom_dict_np_set(tagger_instance):
    cd = tagger_instance.custom_dict('my')
    dic = cd.get()
    assert len(dic.np_set.items) == 4
    assert '유리왕' in dic.np_set.items
    assert '근초고왕' in dic.np_set.items
    assert '누루하치' in dic.np_set.items
    assert '베링거인겔하임' in dic.np_set.items


def test_tagger_get_custom_dict_cp_set(tagger_instance):
    cd = tagger_instance.custom_dict('my')
    dic = cd.get()
    assert len(dic.cp_set.items) == 1
    assert '코로나19' in dic.cp_set.items


def test_tagger_get_custom_dict_cp_caret_set(tagger_instance):
    cd = tagger_instance.custom_dict('my')
    dic = cd.get()
    assert len(dic.cp_caret_set.items) == 2
    assert '인공지능^데이터^학습' in dic.cp_caret_set.items
    assert '자연어^처리^엔진' in dic.cp_caret_set.items


def test_tagger_pos_and_extractors(tagger_instance):
    """morphs/nouns/verbs/adverbs 추출기를 한 번에 검증한다."""
    sentence = '오늘은 먹다.'
    result = tagger_instance.tag(sentence)
    # verbs() 는 VV 태그 형태소를 추출한다
    verbs = result.verbs()
    assert '먹' in verbs
    # nouns() 는 NN* 태그 형태소를 추출한다
    nouns = result.nouns()
    assert '오늘' in nouns


def test_exception_apikey(tagger_error_apikey_instance, sample1):
    """잘못된 API 키로 호출하면 사람이 읽을 수 있는 오류 메시지를 던진다."""
    with pytest.raises(Exception) as exc_info:
        tagger_error_apikey_instance.pos(sample1)
    assert exc_info.value.args[0][:27] == '\n입력한 API KEY가 정확한지 확인해 주세요.'


def test_exception_host(tagger_error_host_instance, sample1):
    """호스트에 포트가 섞인 잘못된 형식이면 연결 오류 메시지를 던진다."""
    with pytest.raises(Exception) as exc_info:
        tagger_error_host_instance.pos(sample1)
    assert exc_info.value.args[0][:16] == '\n서버에 연결할 수 없습니다.'
