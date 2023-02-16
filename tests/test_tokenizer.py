#!env python3
# -*- coding: utf-8 -*-
import pytest
from bareunpy import Tokenized

@pytest.fixture
def tokenizer_instance():
    import bareunpy
    ## FIXME change it nlp.bareun.ai
    t = bareunpy.Tokenizer(
        apikey="koba-42CXULQ-SDPU6ZA-RQ6QPBQ-4BMZCOA",
        host="10.3.8.44",
        port=5757)
    return t

TEST_STR='오늘은 정말 추운 날이네요.'
@pytest.fixture
def sample1():
    return TEST_STR


def test_tokenizer_seg_not_flatten(tokenizer_instance, sample1):
    assert tokenizer_instance.seg(sample1, flatten=False) == \
           [[('오늘'), ('은')],
            [('정말')],
            [('춥'), ('ㄴ')],
            [('날'), ('이'), ('네'), ('요'), ('.')]
            ]


def test_tokenizer_seg_join(tokenizer_instance, sample1):
    assert tokenizer_instance.seg(sample1, join=True, detail=True) == \
           ['오늘/N',
            '은/J',
            '정말/A',
            '춥/V',
            'ㄴ/E',
            '날/N',
            '이/V',
            '네/E',
            '요/J',
            './S'
            ]


def test_tokenizer_seg_detail(tokenizer_instance, sample1):
    temp = tokenizer_instance.seg(sample1, detail=True)
    temp2 = [(t[0], t[1]) for t in temp]
    assert (temp2 == [('오늘', 'N'),
                      ('은', 'J'),
                      ('정말', 'A'),
                      ('춥', 'V'),
                      ('ㄴ', 'E'),
                      ('날', 'N'),
                      ('이', 'V'),
                      ('네', 'E'),
                      ('요', 'J'),
                      ('.', 'S')])


def test_tokenizer_seg(tokenizer_instance, sample1):
    assert tokenizer_instance.seg(sample1) == \
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


def test_tokenizer_nouns(tokenizer_instance, sample1):
    assert tokenizer_instance.nouns(sample1) == \
           ['오늘', '날']


def test_tokenizer_tokenize_as_json_str(tokenizer_instance, sample1):
    j = tokenizer_instance.tokenize(sample1).as_json()
    assert len(j['sentences']) == 1
    assert len(j['sentences'][0]['tokens']) == 4
    assert len(j['sentences'][0]['tokens'][0]['segments']) == 2
    assert len(j['sentences'][0]['tokens'][1]['segments']) == 1
    assert len(j['sentences'][0]['tokens'][2]['segments']) == 2
    assert len(j['sentences'][0]['tokens'][3]['segments']) == 5
    assert len(j['sentences'][0]['tokens'][3]['segments']) == 5


def test_tokenizer_tokenize_as_msg(tokenizer_instance, sample1):
    m = tokenizer_instance.tokenize(sample1).msg()
    assert m.sentences[0].tokens[3].tagged == '날/N+이/V+네/E+요/J+./S'


def test_tokenizer_tokenize_print_as_json(tokenizer_instance, sample1):
    import tempfile
    with tempfile.TemporaryFile('w+') as f:
        tokenizer_instance.tokenize(sample1).print_as_json(out=f)
        assert f.tell() > 0

def test_tokenized_nouns(tokenized: Tokenized):
    assert tokenized.nouns() == \
           ['오늘',
            '날']


@pytest.fixture
def tokenized() -> Tokenized:
    import bareunpy
    # FIXME change it nlp.bareun.ai
    t = bareunpy.Tokenizer(
        apikey="koba-42CXULQ-SDPU6ZA-RQ6QPBQ-4BMZCOA",
        host="10.3.8.44",
        port=5757)

    return t.tokenize(TEST_STR)

def test_tokenized_verbs(tokenized: Tokenized):
    assert tokenized.predicates() == \
           ['춥',
            '이']

def test_tokenized_symbols(tokenized: Tokenized):
    assert tokenized.symbols() == \
           ['.']

def test_tokenized_adverbs(tokenized: Tokenized):
    assert tokenized.adverbs() == \
           ['정말']

def test_tokenized_endings(tokenized: Tokenized):
    assert tokenized.endings() == \
           ['ㄴ','네']

def test_tokenized_postpositions(tokenized: Tokenized):
    assert tokenized.postpositions() == \
           ['은','요',]
