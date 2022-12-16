#!env python3
# -*- coding: utf-8 -*-
import pytest


@pytest.fixture
def tagger_instance():
    import bareunpy
    ## FIXME change it nlp.bareun.ai
    t = bareunpy.Tagger("10.3.8.44")
    return t

@pytest.fixture
def sample1():
    return '오늘은 정말 추운 날이네요.'


def test_tagger_pos(tagger_instance, sample1):
    assert tagger_instance.pos(sample1) == \
           [('오늘', 'NNG'),
            ('은', 'JX'),
            ('정말', 'MAG'),
            ('춥', 'VA'),
            ('ㄴ', 'ETM'),
            ('날', 'NNG'),
            ('이', 'VCP'),
            ('네', 'EF'),
            ('요', 'JX'),
            ('.', 'SF')
            ]


def test_tagger_pos_join(tagger_instance, sample1):
    assert tagger_instance.pos(sample1, join=True) == \
           ['오늘/NNG',
            '은/JX',
            '정말/MAG',
            '춥/VA',
            'ㄴ/ETM',
            '날/NNG',
            '이/VCP',
            '네/EF',
            '요/JX',
            './SF'
            ]


def test_tagger_pos_detail(tagger_instance, sample1):
    temp = tagger_instance.pos(sample1, detail=True)
    temp2 = [(t[0], t[1], t[2]) for t in temp]
    assert (temp2 == [('오늘', 'NNG', 'IN_WORD_EMBEDDING'),
                      ('은', 'JX', 'IN_WORD_EMBEDDING'),
                      ('정말', 'MAG', 'IN_WORD_EMBEDDING'),
                      ('춥', 'VA', 'IN_WORD_EMBEDDING'),
                      ('ㄴ', 'ETM', 'IN_WORD_EMBEDDING'),
                      ('날', 'NNG', 'IN_WORD_EMBEDDING'),
                      ('이', 'VCP', 'IN_WORD_EMBEDDING'),
                      ('네', 'EF', 'IN_WORD_EMBEDDING'),
                      ('요', 'JX', 'IN_WORD_EMBEDDING'),
                      ('.', 'SF', 'IN_WORD_EMBEDDING')])


def test_tagger_morphs(tagger_instance, sample1):
    assert tagger_instance.morphs(sample1) == \
           ['오늘',
            '은',
            '정말',
            '춥',
            'ㄴ',
            '날',
            '이',
            '네',
            '요',
            '.']


def test_tagger_nouns(tagger_instance, sample1):
    assert tagger_instance.nouns(sample1) == \
           ['오늘', '날']


def test_tagger_tag_as_json_str(tagger_instance, sample1):
    j = tagger_instance.tag(sample1).as_json()
    assert len(j['sentences']) == 1
    assert len(j['sentences'][0]['tokens']) == 4
    assert len(j['sentences'][0]['tokens'][0]['morphemes']) == 2
    assert len(j['sentences'][0]['tokens'][1]['morphemes']) == 1
    assert len(j['sentences'][0]['tokens'][2]['morphemes']) == 2
    assert len(j['sentences'][0]['tokens'][3]['morphemes']) == 5
    assert len(j['sentences'][0]['tokens'][3]['morphemes']) == 5


def test_tagger_tag_as_msg(tagger_instance, sample1):
    m = tagger_instance.tag(sample1).msg()
    assert m.sentences[0].tokens[3].tagged == '날/NNG+이/VCP+네/EF+요/JX+./SF'


def test_tagger_tag_print_as_json(tagger_instance, sample1):
    import tempfile
    with tempfile.TemporaryFile('w+') as f:
        tagger_instance.tag(sample1).print_as_json(out=f)
        assert f.tell() > 0


def test_tagger_create_custom_dict(tagger_instance):
    try:
        cd = tagger_instance.custom_dict('my')
        assert cd is not None
    except TypeError as e:
        assert False


def test_tagger_update_custom_dict(tagger_instance):
    try:
        cd = tagger_instance.custom_dict('my')
        cd.copy_np_set({'유리왕', '근초고왕', '누루하치', '베링거인겔하임'})
        cd.copy_cp_set({'코로나19'})
        cd.copy_cp_caret_set({'인공지능^데이터^학습', '자연어^처리^엔진'})
        cd.update()
        assert True
    except TypeError as e:
        assert False


def test_tagger_get_custom_dict_np_set(tagger_instance):
    try:
        cd = tagger_instance.custom_dict('my')
        dic = cd.get()
        assert len(dic.np_set.items) == 4
        assert '유리왕' in dic.np_set.items
        assert '근초고왕' in dic.np_set.items
        assert '누루하치' in dic.np_set.items
        assert '베링거인겔하임' in dic.np_set.items
    except TypeError as e:
        assert False


def test_tagger_get_custom_dict_cp_set(tagger_instance):
    try:
        cd = tagger_instance.custom_dict('my')
        dic = cd.get()
        assert len(dic.cp_set.items) == 1
        assert '코로나19' in dic.cp_set.items
    except TypeError as e:
        assert False


def test_tagger_get_custom_dict_cp_caret_set(tagger_instance):
    try:
        cd = tagger_instance.custom_dict('my')
        dic = cd.get()
        assert len(dic.cp_caret_set.items) == 2
        assert '인공지능^데이터^학습' in dic.cp_caret_set.items
        assert '자연어^처리^엔진' in dic.cp_caret_set.items
    except TypeError as e:
        assert False
