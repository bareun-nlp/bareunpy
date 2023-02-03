# What is this?

`bareunpy` is the python 3 library for bareun.

Bareun is a Korean NLP,
which provides tokenizing, POS tagging for Korean.

## How to install

```shell
pip3 install bareunpy
```

## How to get bareun
- Go to https://bareun.ai/.
  - With registration, for the first time, you can get a API-KEY to use it freely.
  - With API-KEY, you can install the `bareun1` server.
  - Or you can make a call to use this `bareunpy` library to any servers.
- Or use docker image. See https://hub.docker.com/r/bareunai/bareun
```shell
docker pull bareunai/bareun:latest
```

## How to use, tagger

```python
import sys
import google.protobuf.text_format as tf
from bareunpy import Tagger

#
# you can API-KEY from https://bareun.ai/
#
API_KEY="koba-42CXULQ-SDPU6ZA-RQ6QPBQ-4BMZCOA"

# If you have your own localhost bareun.
my_tagger = Tagger(API_KEY, 'localhost')
# or if you have your own bareun which is running on 10.8.3.211:15656.
my_tagger = Tagger(API_KEY, '10.8.3.211', 15656)


# print results. 
res = tagger.tags(["안녕하세요.", "반가워요!"])

# get protobuf message.
m = res.msg()
tf.PrintMessage(m, out=sys.stdout, as_utf8=True)
print(tf.MessageToString(m, as_utf8=True))
print(f'length of sentences is {len(m.sentences)}')
## output : 2
print(f'length of tokens in sentences[0] is {len(m.sentences[0].tokens)}')
print(f'length of morphemes of first token in sentences[0] is {len(m.sentences[0].tokens[0].morphemes)}')
print(f'lemma of first token in sentences[0] is {m.sentences[0].tokens[0].lemma}')
print(f'first morph of first token in sentences[0] is {m.sentences[0].tokens[0].morphemes[0]}')
print(f'tag of first morph of first token in sentences[0] is {m.sentences[0].tokens[0].morphemes[0].tag}')

## Advanced usage.
for sent in m.sentences:
    for token in sent.tokens:
        for m in token.morphemes:
            print(f'{m.text.content}/{m.tag}:{m.probability}:{m.out_of_vocab})

# get json object
jo = res.as_json()
print(jo)

# get tuple of pos tagging.
pa = res.pos()
print(pa)
# another methods
ma = res.morphs()
print(ma)
na = res.nouns()
print(na)
va = res.verbs()
print(va)

# custom dictionary
cust_dic = tagger.custom_dict("my")
cust_dic.copy_np_set({'내고유명사', '우리집고유명사'})
cust_dic.copy_cp_set({'코로나19'})
cust_dic.copy_cp_caret_set({'코로나^백신', '"독감^백신'})
cust_dic.update()

# laod prev custom dict
cust_dict2 = tagger.custom_dict("my")
cust_dict2.load()

tagger.set_domain('my')
tagger.pos('코로나19는 언제 끝날까요?')
```


## How to use, tokenizer

```python
import sys
import google.protobuf.text_format as tf
from bareunpy import Tokenizer

# If you have your own localhost bareun.
my_tokenizer = Tokenizer(API_KEY, 'localhost')
# or if you have your own bareun which is running on 10.8.3.211:15656.
my_tokenizer = Tagger(API_KEY, '10.8.3.211', 15656)


# print results. 
tokenized = tokenizer.tokenize_list(["안녕하세요.", "반가워요!"])

# get protobuf message.
m = tokenized.msg()
tf.PrintMessage(m, out=sys.stdout, as_utf8=True)
print(tf.MessageToString(m, as_utf8=True))
print(f'length of sentences is {len(m.sentences)}')
## output : 2
print(f'length of tokens in sentences[0] is {len(m.sentences[0].tokens)}')
print(f'length of segments of first token in sentences[0] is {len(m.sentences[0].tokens[0].segments)}')
print(f'tagged of first token in sentences[0] is {m.sentences[0].tokens[0].tagged}')
print(f'first segment of first token in sentences[0] is {m.sentences[0].tokens[0].segments[0]}')
print(f'hint of first morph of first token in sentences[0] is {m.sentences[0].tokens[0].segments[0].hint}')

## Advanced usage.
for sent in m.sentences:
    for token in sent.tokens:
        for m in token.segments:
            print(f'{m.text.content}/{m.hint})

# get json object
jo = tokenized.as_json()
print(jo)

# get tuple of segments
ss = tokenized.segments()
print(ss)
ns = tokenized.nouns()
print(ns)
vs = tokenized.verbs()
print(vs)
# postpositions: 조사
ps = tokenized.postpositions()
print(ps)
# Adverbs, 부사
ass = tokenized.adverbs()
print(ass)
ss = tokenized.symbols()
print(ss)

```
