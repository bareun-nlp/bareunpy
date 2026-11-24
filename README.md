# bareunpy

**bareunpy**는 한국어 자연어 처리(NLP) 엔진 **[Bareun](https://bareun.ai/)** 의 Python 3 클라이언트 라이브러리입니다.

형태소 분석(POS tagging), 토크나이징(tokenizing), 맞춤법 검사(spelling correction) 기능을 제공합니다.

---

## 변경사항

### 2.2.0

- **교정 세션 지원**: 긴 문서를 여러 번에 나눠 교정할 때 `corrector.open_session()` 으로 세션을 엽니다. 서버가 같은 문서임을 알고 동작해, 앞 호출에서 두 번 이상 나온 미등록 단어를 뒤 호출에서 고치지 않습니다.
  - `RevisionSession`: `correct_error()`, `correct_error_stream()`, `events()`, `close()`, `with` 문 지원
  - 서버가 세션을 지원해야 합니다(바른 3.3.1 이상).
- **긴 글 요청의 잘림(truncation) 응답 지원**: 서버는 요청 글이 기준(운영 서버 `api.bareun.ai` 는 5,000자)을 넘으면 거절하지 않고 앞부분(5,000자 안쪽)만 처리하고, 버린 부분을 응답으로 알립니다. 이제 이 정보를 읽을 수 있습니다.
  - `Tagged` / `Tokenized`: `is_truncated()`, `truncation()`, `dropped_text()`
  - `Corrector`: `Corrector.is_truncated(res)`, `Corrector.truncation(res)`, `print_results()` 가 안내 문구를 함께 출력
  - `TruncationInfo`: 요청 글 전체·처리한·버린 글자 수, 버린 구간의 시작 위치, 안내 문구, 글자 중간에서 잘랐는지
  - 새 메서드만 더했습니다. **기존 코드의 동작은 그대로**이고, 잘리지 않은 응답에는 정보가 없습니다(`None`).
  - 서버 쪽에서 긴 요청 자르기를 지원해야 정보가 옵니다. 지원하지 않는 서버는 길면 거절하거나 그대로 처리합니다(`None`).

### 2.1.0

- **동형이의어 의미 구분(WSD) API 추가 — 베타**: 표기·품사가 같은데 뜻이 다른 단어(`다리`(橋)/`다리`(脚))를 문맥으로 구분합니다.
  - `tagger.senses('다리를 건넜다.')` — 의미가 부여된 형태소만 `SenseInfo`(어깨번호·뜻풀이·우리말샘 번호·선택 확률) 목록으로 반환
  - `tagger.tag(..., with_sense=True)` / `tags` / `taglist` / `tag_raw` — 분석 결과에 의미를 함께 요청
  - `res.senses()`, `res.pos(sense=True)` — 결과에서 의미 꺼내기(`다리__005/NNG`)
  - 기본값은 모두 `False` 라 **기존 코드의 동작·응답은 그대로**입니다.
  - 베타 기능이며 **바른 3.1.0** 이상 서버가 필요합니다(현재는 api.bareun.ai 에서 사용 가능).

### 2.0.1

- **AnalyzeSyntaxRaw API 추가**: `tagger.tag_raw()` — seg+tag 모델 추론만 수행, 복합명사·동사 분해/사용자 사전/자동 띄어쓰기 후처리 없이 순수 모델 출력 반환

### 2.0

- **Connect RPC 전환**: `grpcio` 의존성 제거. 공식 [`connectrpc`](https://github.com/connectrpc/connect-python) 라이브러리로 교체
- **경량화**: 의존성 2개(`connectrpc`, `protobuf`)만 필요 — 기존 `grpcio` / `connecpy` 설치 불필요
- **버그 수정**: 스트리밍 응답 처리, 빈 입력 처리 안정성 개선, 에러 메시지 한글화
- Python 3.10+ 지원 유지, 기존 API와 호환

---

## 설치 (Installation)

```shell
pip3 install bareunpy
```

> **요구사항**: Python 3.10 이상.
> 서버와의 통신은 공식 [Connect RPC](https://connectrpc.com/) 파이썬 라이브러리
> (`connectrpc`, [connect-python](https://github.com/connectrpc/connect-python)) 위에서 동작합니다.
> (2.0.0 부터 기존 gRPC 직접 연결에서 Connect RPC 로 전환되었습니다.)

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

### 원시(Raw) 형태소 분석

`tag_raw()`는 seg+tag 모델 추론 결과를 후처리 없이 반환합니다. 복합명사·동사 분해, 자동 띄어쓰기·붙여쓰기 보정, 사용자 사전을 적용하지 않아 **순수 모델 출력**을 확인할 때 사용합니다.

```python
# tag_raw(): 후처리 없는 순수 모델 출력
res = tagger.tag_raw('나는밥을먹었다')
print(res.pos())

# 문장 자동 분리 적용 가능
res = tagger.tag_raw('나는밥을먹었다. 그리고잤다.', auto_split=True)
```

### 동형이의어 의미 구분 (WSD, 베타)

한국어에는 표기가 같고 뜻이 전혀 다른 단어가 많습니다. `다리`는 건너는 다리(橋)일 수도, 몸의 다리(脚)일 수도 있고 품사는 둘 다 `NNG` 입니다. `senses()` 는 문맥을 보고 **어느 뜻인지**를 어깨번호(사전 의미 번호)와 뜻풀이로 돌려줍니다.

```python
for s in tagger.senses('다리를 건넜다.'):
    print(s.content, s.tag, s.sense_no, s.meaning)
# 다리 NNG 5 물을 건너거나 … 건너다닐 수 있도록 만든 시설물.
# 건너 VV 1 무엇을 사이에 두고 한편에서 맞은편으로 가다.

for s in tagger.senses('다리가 저리다.'):
    print(s.content, s.sense_no, s.meaning)
# 다리 1 사람이나 동물의 몸통 아래 붙어 있는 신체의 부분. …
```

`SenseInfo` 는 다음 값을 담습니다.

| 필드 | 설명 |
|---|---|
| `content` / `tag` | 형태소의 표층형과 품사 |
| `sense_no` | 어깨번호(우리말샘 기준 의미 번호). 사전 표기로는 3자리 0채움(`005`) |
| `meaning` | 한국어 뜻풀이. **빈 문자열일 수 있습니다**(우리말샘에 표제어가 없는 1% 미만) |
| `urimal_target_id` / `urimal_url` | 우리말샘 표제어 번호와 그 사전 화면 주소(없으면 0 / 빈 문자열) |
| `probability` | 후보 의미 중 이 의미를 고른 확률 `[0,1]`. 후보가 하나뿐이면 항상 1.0 |

기존 메서드에 옵션으로 켤 수도 있습니다.

```python
# 분석 결과 전체를 받고, 그 안에서 의미만 꺼내기
res = tagger.tag('다리를 건넜다.', with_sense=True)
print(res.senses())                      # SenseInfo 목록
print(res.pos(join=True, sense=True))    # ['다리__005/NNG', '를/JKO', '건너__001/VV', ...]
print(res.pos(sense=True))               # [('다리','NNG',5), ('를','JKO',0), ...]

# 여러 문장·원시 분석에서도 동일하게 동작합니다.
tagger.tags(['다리를 건넜다.', '다리가 저리다.'], with_sense=True)
tagger.taglist(['다리를 건넜다.'], with_sense=True)
tagger.tag_raw('다리를건넜다', with_sense=True)
```

> **베타 안내** — 의미 구분은 베타 기능이며 **바른 3.1.0** 이상 서버가 필요합니다(현재 api.bareun.ai 에서 사용 가능).
> 명사와 문맥 단서가 분명한 문장에서 잘 동작하고, 동사·형용사나 한 문장에 같은 표기가 여러 번 나오는 경우에는 오류가 있을 수 있습니다.
> 의미가 없는 형태소(조사·어미 등)는 `senses()` 결과에 나오지 않으며, `with_sense` 를 켜지 않으면 응답·처리 시간이 종전과 동일합니다.

### 분석 옵션

`tag()`, `tags()`, `taglist()` 메서드에서 다음 옵션을 사용할 수 있습니다.

| 파라미터 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `auto_split` | bool | `False` | 문장 자동 분리 (`tag`, `tags`만 해당) |
| `auto_spacing` | bool | `True` | 띄어쓰기 보정 |
| `auto_jointing` | bool | `True` | 붙여쓰기 보정 |
| `with_sense` | bool | `False` | 동형이의어 의미 구분(WSD, 베타) 결과 포함 — `tag_raw()` 에서도 사용 가능 |

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

### 실시간 교정 (Streaming)

`correct_error_stream()` 은 교정 결과를 한 번에 받지 않고, 서버가 보내는 대로
여러 개의 응답으로 나눠 받는 server-streaming 방식입니다. AI 기반 교정처럼 결과가
점진적으로 확정되는 경우에 유용합니다.

```python
from bareunpy import Corrector

corrector = Corrector(API_KEY)

for res in corrector.correct_error_stream("영수 도 줄기가 얇어서 시들을 것 같다."):
    # 각 응답은 res(oneof) 로 다음 중 하나를 담습니다:
    #  - first    : 첫 번째 기본 교정 결과
    #  - progress : AI 가 추가 검토 중인 항목의 진행 상태
    #  - post     : 추가 검토가 끝나 확정된 교정 결과
    #  - cancelled: 이전에 제안한 교정이 취소됨
    kind = res.WhichOneof("res")
    if kind == "first":
        print("교정문:", res.first.revised)
    elif kind == "progress":
        print("진행중:", res.progress.thinking_msg)
    elif kind == "post":
        print("확정:", res.post.revision.revised)
    elif kind == "cancelled":
        print("취소:", res.cancelled.thinking_id)
```

### 긴 글 처리와 잘림 확인

한 번에 보낼 수 있는 글이 서버 기준(운영 서버 `api.bareun.ai` 는 **5,000자**)을 넘으면 서버는
요청을 거절하지 않고 **앞부분(5,000자 안쪽, 문장 끝 → 공백 순으로 끊을 자리를 찾아 최대 500자 짧게)만 처리**합니다.
뒷부분은 처리되지 않으며, 형태소 분석·토크나이징·맞춤법 교정 모두 같습니다. 글자 수는 한글 한 글자,
영문 한 자, 공백, 줄바꿈이 각각 한 글자입니다. 5,000자까지는 전부 처리되고 5,001자부터 잘립니다.
자체 서버는 설정에 따라 기준이 다르거나 자르지 않을 수 있습니다.

응답 좌표(`begin_offset` 등)는 잘려도 요청 글의 처음 기준 그대로입니다. 잘렸는지는 응답으로 확인합니다.

```python
from bareunpy import Corrector, Tagger, Tokenizer

text = "..."  # 5,001자 이상의 긴 글

tagged = Tagger(API_KEY).tag(text)
if tagged.is_truncated():
    t = tagged.truncation()
    print(t.original_chars)    # 요청 글 전체 글자 수
    print(t.processed_chars)   # 처리한 글자 수
    print(t.dropped_chars)     # 버린 글자 수
    print(t.message)           # 서버 안내 문구
    print(t.cut_mid_word)      # True 면 글자 중간에서 잘라 마지막 어절을 믿기 어려움
    rest = tagged.dropped_text()   # 처리되지 않은 뒷부분 원문

# 토크나이저도 같습니다: Tokenizer(API_KEY).tokenize(text).truncation()

# 교정기는 응답을 넘깁니다. 스트리밍이면 first 응답을 넘깁니다.
res = Corrector(API_KEY).correct_error(text)
t = Corrector.truncation(res)          # 잘리지 않았으면 None
if t:
    rest = t.dropped_text(text)        # 교정되지 않은 뒷부분
```

뒷부분까지 처리하려면 `dropped_text()` 로 받은 나머지를 다시 요청하면 됩니다. `taglist()` 는
문장 목록 요청이라 `t.dropped_begin_sentence_index` 번째 문장부터 처리되지 않았고, 그보다 앞
문장은 모두 처리됩니다(응답의 문장 수는 요청과 같고, 처리되지 않은 문장은 빈 문장으로 채워집니다).

### 긴 문서는 세션으로 나눠 보내기

**긴 글은 세션(`open_session`, 끝나면 `close`)을 열고 문단 단위로 나눠 보내는 방식을 권합니다.** 세션 안의 요청들은 한 문서로 이어진 것으로 다뤄집니다. 앞 문단의 미등록 단어(인명, 신조어 등)와 문맥, 사용자 사전, 교정 설정이 뒤 문단에도 이어집니다. 앞 호출에서 두 번 이상 나온 미등록 단어는 알려진 말로 확정되어 뒤 호출에서 고치지 않습니다. 사용자 사전과 교정 설정은 세션을 열 때 정하고 닫을 때까지 바뀌지 않습니다.

서버 기준(5,000자)은 세션 안의 각 요청에도 똑같이 걸리므로, 한 번에 보내는 조각이 5,000자를 넘지 않게 나눕니다. 세션은 마지막 호출 뒤 10분이 지나거나 열린 지 1시간이 지나면 서버가 닫고, 키당 동시에 열 수 있는 수에 상한이 있으니 끝나면 닫습니다(`with` 문이 알아서 닫습니다).

```python
from bareunpy import Corrector

corrector = Corrector(API_KEY)
text = "..."  # 아주 긴 문서

revised = []
with corrector.open_session(custom_dicts=["my_dict"]) as session:
    while text:
        res = session.correct_error(text)
        revised.append(res.revised)
        t = Corrector.truncation(res)               # 잘리지 않았으면 None
        text = t.dropped_text(text) if t else ""    # 교정되지 않은 뒷부분을 이어서 보냄
print("".join(revised))
```

위 예시는 서버가 잘라 알려 주는 뒷부분을 이어 보냅니다. 문서를 직접 문단 단위(5,000자 이하)로 나눠 호출해도 됩니다. 단발 호출(`session.correct_error`)로 앞 답을 받은 뒤
뒤 호출 때문에 앞 답이 달라졌는지는 `session.events()` 로 확인합니다(`session_revision` 이 올랐으면
미등록 단어가 새로 확정된 것입니다). 스트리밍(`session.correct_error_stream`)은 같은 정보를
`session_correction` 응답으로 보내 주고, 되돌릴 구간(`reverted`)의 교정을 취소하면 됩니다. 세션이
만료되거나 서버가 모르면 `NOT_FOUND` 오류가 나니, 세션을 다시 열고 필요한 앞부분부터 다시 보냅니다.

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
