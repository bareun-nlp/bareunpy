# bareunpy

**bareunpy**는 한국어 자연어 처리(NLP) 엔진 **[Bareun](https://bareun.ai/)** 의 Python 3 클라이언트 라이브러리입니다.

형태소 분석(POS tagging), 토크나이징(tokenizing), 맞춤법 검사(spelling correction) 기능을 제공합니다.

---

## 설치 (Installation)

```shell
pip3 install bareunpy
```

## API KEY 발급

1. https://bareun.ai/ 에 접속하여 회원가입 후 이메일 인증을 완료하면 자동 발급됩니다.
2. **로그인 → 내정보 확인**에서 API KEY(`koba-...`)를 조회합니다.

> 발급받은 API KEY로 `api.bareun.ai` 호스팅 서버에 바로 연결하거나,
> 자체 서버에 Bareun을 설치하여 사용할 수도 있습니다.

## 서버 연결 방식

```python
from bareunpy import Tagger

API_KEY = "koba-ABCDEFG-1234567-LMNOPQR-7654321"  # 본인의 API KEY로 교체

# 1) 호스팅 API 사용 (가장 간편한 방법, host 생략 시 기본값)
tagger = Tagger(API_KEY)
# 또는 명시적으로 지정
tagger = Tagger(API_KEY, 'api.bareun.ai', 443)

# 2) 로컬 서버 사용
tagger = Tagger(API_KEY, 'localhost', 5656)

# 3) 원격 자체 서버 사용 (예: 10.8.3.211:15656)
tagger = Tagger(API_KEY, '10.8.3.211', 15656)
```

> 자체 서버 설치는 Docker 이미지로 간편하게 할 수 있습니다.
> ```shell
> docker pull bareunai/bareun:latest
> ```
> 자세한 내용은 [Docker Hub](https://hub.docker.com/r/bareunai/bareun)를 참고하세요.

---

## 형태소 분석 (Tagger)

### 기본 사용법

```python
from bareunpy import Tagger

API_KEY = "koba-ABCDEFG-1234567-LMNOPQR-7654321"  # 본인의 API KEY로 교체
tagger = Tagger(API_KEY)

# POS 태깅
print(tagger.pos('햇빛이 선명하게 나뭇잎을 핥고 있었다.'))
# [('햇빛', 'NNG'), ('이', 'JKS'), ('선명', 'NNG'), ('하', 'XSA'), ('게', 'EC'),
#  ('나뭇잎', 'NNG'), ('을', 'JKO'), ('핥', 'VV'), ('고', 'EC'), ('있', 'VX'),
#  ('었', 'EP'), ('다', 'EF'), ('.', 'SF')]

# 형태소 추출
print(tagger.morphs('안녕하세요, 반가워요.'))
# ['안녕', '하', '시', '어요', ',', '반갑', '어요', '.']

# 명사 추출
print(tagger.nouns('나비 허리에 새파란 초생달이 시리다.'))
# ['나비', '허리', '초생달']

# 동사 추출
print(tagger.verbs('햇빛이 선명하게 나뭇잎을 핥고 있었다.'))
# ['핥']
```

### 여러 문장 분석

```python
# tags(): 여러 문장을 한 번에 분석 (문장 분할 적용)
res = tagger.tags(["안녕하세요.", "반가워요!"])

# taglist(): 입력된 문장 단위를 그대로 유지하여 분석 (문장 분할 없음)
res = tagger.taglist(["안녕하세요.", "반가워요!"])
```

### 분석 옵션

`tag()`, `tags()`, `taglist()` 메서드에서 다음 옵션을 사용할 수 있습니다.

| 파라미터 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `auto_split` | bool | `False` | 문장 자동 분리 (`tag`, `tags`만 해당) |
| `auto_spacing` | bool | `True` | 띄어쓰기 보정 |
| `auto_jointing` | bool | `True` | 붙여쓰기 보정 |

```python
res = tagger.tag('햇빛이선명하게나뭇잎을핥고있었다', auto_spacing=True, auto_jointing=True)
print(res.pos())
```

### 결과 활용

```python
res = tagger.tags(["안녕하세요.", "반가워요!"])

# protobuf 메시지 원본
m = res.msg()

# JSON 변환
print(res.as_json())
print(res.as_json_str())

# 형태소, POS 태그, 명사, 동사 추출
print(res.morphs())
print(res.pos())
print(res.nouns())
print(res.verbs())
```

### 상세 결과 탐색 (Advanced)

```python
import sys
import google.protobuf.text_format as tf

m = res.msg()
tf.PrintMessage(m, out=sys.stdout, as_utf8=True)

for sent in m.sentences:
    for token in sent.tokens:
        for morph in token.morphemes:
            print(f'{morph.text.content}/{morph.tag}:{morph.probability}:{morph.out_of_vocab}')
```

---

## 토크나이저 (Tokenizer)

```python
from bareunpy import Tokenizer

API_KEY = "koba-ABCDEFG-1234567-LMNOPQR-7654321"  # 본인의 API KEY로 교체
tokenizer = Tokenizer(API_KEY)

# 토크나이징
tokenized = tokenizer.tokenize_list(["안녕하세요.", "반가워요!"])

# 다양한 추출 메서드
print(tokenized.segments())       # 전체 세그먼트
print(tokenized.nouns())          # 명사
print(tokenized.verbs())          # 동사
print(tokenized.postpositions())  # 조사
print(tokenized.adverbs())        # 부사
print(tokenized.symbols())        # 기호
```

### 상세 결과 탐색

```python
m = tokenized.msg()
for sent in m.sentences:
    for token in sent.tokens:
        for seg in token.segments:
            print(f'{seg.text.content}/{seg.hint}')
```

---

## 맞춤법 검사 (Corrector)

> **참고:** 맞춤법 검사는 `api.bareun.ai` 호스팅 API에서만 사용 가능합니다. 로컬 서버에서는 지원되지 않습니다.

```python
from bareunpy import Corrector

API_KEY = "koba-ABCDEFG-1234567-LMNOPQR-7654321"  # 본인의 API KEY로 교체
corrector = Corrector(API_KEY)

response = corrector.correct_error("영수 도 줄기가 얇어서 시들을 것 같은 꽃에물을 주었다.")
print(f"원문:   {response.origin}")
print(f"교정문: {response.revised}")

# 상세 결과 출력
corrector.print_results(response)
```

---

## 사용자 사전 (Custom Dictionary)

사용자 사전을 등록하면 도메인 특화 용어의 분석 정확도를 높일 수 있습니다.

### 사전 등록 및 업데이트

```python
# 사용자 사전 생성/수정
cust_dic = tagger.custom_dict("my")
cust_dic.copy_np_set({'내고유명사', '우리집고유명사'})    # 고유명사
cust_dic.copy_cp_set({'코로나19'})                       # 복합명사
cust_dic.copy_cp_caret_set({'코로나^백신', '독감^백신'})  # 복합명사 (분리 위치 지정)
cust_dic.update()
```

### 사전 불러오기 및 적용

```python
# 기존 사전 불러오기
cust_dic2 = tagger.custom_dict("my")
cust_dic2.load()

# 분석 시 사용자 사전 적용
tagger.set_custom_dicts(["my"])
tagger.pos('코로나19는 언제 끝날까요?')
```
