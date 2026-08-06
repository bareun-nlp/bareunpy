# -*- coding: utf-8 -*-
import json
import warnings
from sys import stdout
from typing import IO, List, NamedTuple, Optional, Union

from google.protobuf.json_format import MessageToDict
from bareunpy._custom_dict import CustomDict
from bareunpy._lang_service_client import BareunLanguageServiceClient
from bareunpy.bareun.language_service_pb2 import AnalyzeSyntaxResponse, AnalyzeSyntaxListResponse, Morpheme, Sentence, Token


class SenseInfo(NamedTuple):
    """동형이의어 의미 구분(WSD, 베타) 결과 한 건.

    ``Tagged.senses()`` / ``Tagger.senses()`` 가 돌려주는 항목이다. 형태소 하나에 대해
    "표기·품사는 같은데 뜻이 다른 단어들" 중 어떤 뜻으로 판정됐는지를 담는다.

    Attributes:
        content (str): 형태소의 표층형(예: ``다리``).
        tag (str): 품사 태그 이름(예: ``NNG``).
        sense_no (int): 어깨번호. 우리말샘 기준 의미 번호(예: 5). 사전 표기로 되돌리려면
            3자리 0채움(``005``)으로 만든다.
        meaning (str): 한국어 뜻풀이. **빈 문자열일 수 있다** — 우리말샘에 표제어가 없는
            경우가 1% 미만 존재한다.
        urimal_target_id (int): 우리말샘 표제어 고유 번호. 0 이면 미부여.
            ``https://opendict.korean.go.kr/dictionary/view?sense_no=<값>`` 으로 열 수 있다.
        probability (float): 그 의미를 고른 확률 [0,1]. **후보 의미 집합 안에서** 정규화한
            값이라 후보를 모두 더하면 1 이다. 후보가 하나뿐인 단어는 항상 1.0 이므로
            "확신"이 아니라 "고를 것이 하나뿐"이라는 뜻이다. 형태소의 ``probability``
            (품사 점수)와는 척도가 달라 같은 임계값으로 비교하면 안 된다.
    """

    content: str
    tag: str
    sense_no: int
    meaning: str
    urimal_target_id: int
    probability: float

    @property
    def urimal_url(self) -> str:
        """우리말샘 표제어 화면 주소. ``urimal_target_id`` 가 0이면 빈 문자열."""
        if not self.urimal_target_id:
            return ""
        return f"https://opendict.korean.go.kr/dictionary/view?sense_no={self.urimal_target_id}"

def _resolve_port(host: str, port: Optional[int]) -> int:
    """
    Resolve port number based on host.
    :param host: Host name
    :param port: Port number
    :return: Resolved port number
    """
    if port is not None:
        return port
    else:
        if host.lower().startswith('api.bareun.ai'):
            return 443
        else:
            return 5656

class Tagged:
    """
    Tagged result.
    It has various output manipulations.
    """

    def __init__(self, phrase: Union[str, List[str]], res: Union[AnalyzeSyntaxResponse, AnalyzeSyntaxListResponse]):
        """
        constructor, which is used internally.
        :param phrase: requested sentences.
        :param res:
        """
        super().__init__()
        self.phrase = phrase
        self.r = res

        # 빈 응답이 있는 경우를 대비해서 값이 없지 않도록 처리한다.
        if self.r is None:
            self.r = AnalyzeSyntaxResponse()
            self.phrase = ''

    def msg(self) -> Union[AnalyzeSyntaxResponse, AnalyzeSyntaxListResponse]:
        """
        Protobuf message object containing all of NLP engine.
        """
        return self.r

    def sentences(self) -> List[Sentence]:
        """
        :return: get sentences from tagged results.
        """
        ret = list()
        for s in self.r.sentences:
            ret.append(s)
        return ret

    def as_json(self):
        """
        convert the message to a json object.
        :return: Json Obejct
        """
        return MessageToDict(self.r, True)

    def as_json_str(self) -> str:
        """
        a json string representing analyzed sentences.
        :return: json string
        """
        d = MessageToDict(self.r, True)
        return json.dumps(d, ensure_ascii=False, indent=2)

    def print_as_json(self, out: IO = stdout):
        """
        print the analysis result
        :param out: File, if nothing provided, sys.stdout is used.
        :return: None
        """
        d = MessageToDict(self.r, True)
        json.dump(d, out, ensure_ascii=False, indent=2)

    @staticmethod
    def _sense_no(m: Morpheme) -> int:
        """형태소에 부여된 어깨번호를 돌려줍니다(없으면 0).

        ``sense`` 는 proto3 ``optional`` 메시지 필드라, 의미가 부여되지 않은 형태소
        (조사·어미 등, 또는 ``with_sense`` 를 켜지 않은 호출 전체)에는 필드 자체가 없습니다.
        그래서 값 비교가 아니라 ``HasField`` 로 존재를 확인합니다.
        """
        return m.sense.sense_no if m.HasField("sense") else 0

    @staticmethod
    def _pos(m: Morpheme, join: bool, detail: bool, sense: bool = False):
        sense_no = Tagged._sense_no(m) if sense else 0
        if join:
            # 어깨번호가 있으면 말뭉치·문서와 같은 `표층형__NNN` 표기로 덧붙인다.
            content = f'{m.text.content}__{sense_no:03d}' if sense_no else m.text.content
            if detail:
                p = f':{m.probability:5.3f}' if m.probability > 0 else ''
                oov = f'#{Morpheme.OutOfVocab.Name(m.out_of_vocab)}' if m.out_of_vocab != 0 else ''
                return f'{content}/{Morpheme.Tag.Name(m.tag)}{p}{oov}'
            else:
                return f'{content}/{Morpheme.Tag.Name(m.tag)}'
        else:
            if detail:
                base = (m.text.content,
                        Morpheme.Tag.Name(m.tag),
                        Morpheme.OutOfVocab.Name(m.out_of_vocab),
                        m.probability)
            else:
                base = (m.text.content, Morpheme.Tag.Name(m.tag))
            # sense=True 면 튜플 끝에 어깨번호를 하나 더 붙인다(미부여는 0).
            return base + (sense_no,) if sense else base

    def pos(self, flatten: bool = True, join: bool = False, detail: bool = False,
            sense: bool = False) -> List:
        """
        POS tagger to tuple.
        :param flatten : If False, returns original morphs.
        :param join    : If True, returns joined sets of morph and tag.
        :param detail  : if True, returns everything of morph result
        :param sense   : if True, 동형이의어 어깨번호를 함께 표기합니다(WSD, 베타).
                         join=True 면 `다리__005/NNG` 형태로, join=False 면 튜플 끝에
                         어깨번호(미부여는 0)가 추가됩니다. 분석 요청 시
                         `with_sense=True` 로 호출했을 때만 값이 채워집니다.
        """
        if flatten:
            return [Tagged._pos(m, join, detail, sense) for s in self.r.sentences
                    for token in s.tokens
                    for m in token.morphemes]
        else:
            return [[Tagged._pos(m, join, detail, sense) for m in token.morphemes]
                    for s in self.r.sentences
                    for token in s.tokens]

    def senses(self, flatten: bool = True) -> List:
        """동형이의어 의미 구분(WSD, 베타) 결과만 골라서 돌려줍니다.

        의미가 **부여된 형태소만** 나옵니다. 조사·어미처럼 사전 의미 번호가 없는 형태소는
        빠지므로, 결과가 형태소 목록보다 짧은 것이 정상입니다. 분석을 ``with_sense=True``
        로 요청하지 않았다면 빈 목록입니다.

        :param flatten: True(기본)면 형태소 단위로 평탄한 목록, False 면 어절별 목록의 목록.
        :return: :class:`SenseInfo` 의 목록(또는 목록의 목록)
        """
        if flatten:
            return [Tagged._sense_info(m) for s in self.r.sentences
                    for token in s.tokens
                    for m in token.morphemes
                    if m.HasField("sense")]
        else:
            return [[Tagged._sense_info(m) for m in token.morphemes if m.HasField("sense")]
                    for s in self.r.sentences
                    for token in s.tokens]

    @staticmethod
    def _sense_info(m: Morpheme) -> SenseInfo:
        """의미가 부여된 형태소를 :class:`SenseInfo` 로 바꿉니다(호출 전 존재 확인 필요)."""
        return SenseInfo(
            content=m.text.content,
            tag=Morpheme.Tag.Name(m.tag),
            sense_no=m.sense.sense_no,
            meaning=m.sense.meaning,
            urimal_target_id=m.sense.urimal_target_id,
            probability=m.sense.probability,
        )

    def morphs(self) -> List:
        """Parse phrase to morphemes."""
        return [m.text.content for s in self.r.sentences
                for token in s.tokens
                for m in token.morphemes]

    def nouns(self) -> List:
        """Noun extractor."""
        return [m.text.content for s in self.r.sentences
                for token in s.tokens
                for m in token.morphemes
                if m.tag in {Morpheme.Tag.NNP, Morpheme.Tag.NNG, Morpheme.Tag.NP, Morpheme.Tag.NNB}]

    def verbs(self) -> List:
        """Noun extractor."""
        return [m.text.content for s in self.r.sentences
                for token in s.tokens
                for m in token.morphemes
                if m.tag in {Morpheme.Tag.VV}]


class Tagger:
    """Wrapper for `bareun v1.7.x <https://github.com/bareun-nlp>`_.
    'bareun' is a morphological analyzer developed by Baikal AI, Inc. and Korea Press Foundation.

    .. code-block:: python
        :emphasize-lines: 1
        >>> import bareunpy as brn
        >>> tagger = brn.Tagger(apikey="kpba-YOURKEY", custom_dicts=["custom", "my"])
        >>> print(tagger.morphs('안녕하세요, 반가워요.'))
        ['안녕', '하', '시', '어요', ',', '반갑', '어요', '.']
        >>> print(tagger.nouns('나비 허리에 새파란 초생달이 시리다.'))
        ['나비', '허리', '초생달']
        >>> print(tagger.pos('햇빛이 선명하게 나뭇잎을 핥고 있었다.'))
        [('햇빛', 'NNG'), ('이', 'JKS'), ('선명', 'NNG'), ('하', 'XSA'), ('게', 'EC'), ('나뭇잎', 'NNG'),
         ('을', 'JKO'), ('핥', 'VV'), ('고', 'EC'), ('있', 'VX'), ('었', 'EP'), ('다', 'EF'), ('.', 'SF')]
    :param host         : str. host name for bareun server
    :param port         : int. port  for bareun server
    :param custom_dicts : List[str]. custom dictionary names for analyzing request
    """

    def __init__(self, apikey: str, host: str = "", port: Optional[int] = None, custom_dicts: Optional[List[str]] = None):

        if host:
            host = host.strip()

        if host == "" or host is None:
            self.host = 'api.bareun.ai'
        else:
            self.host = host

        self.port = _resolve_port(self.host, port)
        self.apikey = apikey

        if apikey == None or len(apikey) == 0:
            raise ValueError("an apikey must be provided!")

        self.client = BareunLanguageServiceClient(apikey, self.host, self.port)

        self.custom_dicts = list(custom_dicts) if custom_dicts is not None else []
        self.internal_custom_dicts = {}
    
    def set_domain(self, domain: str):
        """사용자 사전 이름을 추가합니다.

        .. deprecated::
            :meth:`set_custom_dicts` 를 사용하세요.
        """
        warnings.warn(
            "set_domain() 은 deprecated 입니다. set_custom_dicts() 를 사용하세요.",
            DeprecationWarning,
            stacklevel=2,
        )
        self.custom_dicts.append(domain)

    def set_custom_dicts(self, custom_dicts: List[str]):
        """
        사용자 사전 이름 목록을 설정합니다.
        :param custom_dicts: 사용자 사전 이름 목록
        """
        if len(custom_dicts) > 0:
            self.custom_dicts = custom_dicts
        else:
            self.custom_dicts = []

    def custom_dict(self, name: str) -> CustomDict:
        # self.domain = domain
        if name == "" or name is None:
            raise ValueError("invalid name for custom dict")

        if name in self.internal_custom_dicts:
            return self.internal_custom_dicts[name]
        else:
            self.internal_custom_dicts[name] = CustomDict(self.apikey, name, self.host, self.port)
            return self.internal_custom_dicts[name]

    def tag_raw(self, phrase: str, auto_split: bool = False, with_sense: bool = False) -> Tagged:
        """모델 추론만 수행하는 원시(raw) 형태소 분석을 수행합니다.

        복합명사·동사 분해, 자동 띄어쓰기·붙여쓰기 보정, 사용자 사전을 일절 적용하지 않습니다.
        seg+tag 모델의 순수 추론 결과가 필요할 때 사용합니다.

        :param phrase: 분석할 문자열
        :param auto_split: 문장 자동 분리 여부 (기본값: False)
        :param with_sense: 동형이의어 의미 구분(WSD, 베타) 결과를 함께 받을지 여부 (기본값: False)
        :return: Tagged result instance
        """
        if len(phrase) == 0:
            print("OOPS, no sentences.")
            return Tagged('', AnalyzeSyntaxResponse())
        res = self.client.analyze_syntax_raw(phrase, auto_split=auto_split, with_sense=with_sense)
        return Tagged(phrase, res)

    def tag(self, phrase: str, auto_split: bool = False, auto_spacing: bool = True,
            auto_jointing: bool = True, with_sense: bool = False) -> Tagged:
        """형태소 분석을 수행합니다.

        :param phrase: 분석할 문자열
        :param auto_split: 문장 자동 분리 여부 (기본값: False)
        :param auto_spacing: 띄어쓰기 보정 기능 (기본값: True)
        :param auto_jointing: 붙여쓰기 보정 기능 (기본값: True)
        :param with_sense: 동형이의어 의미 구분(WSD, 베타) 결과를 함께 받을지 여부 (기본값: False).
            켜면 결과에서 :meth:`Tagged.senses` 로 어깨번호·뜻풀이를 꺼낼 수 있습니다.
        :return: Tagged result instance
        """
        if len(phrase) == 0:
            print("OOPS, no sentences.")
            return Tagged('', AnalyzeSyntaxResponse())
        # 에러 변환은 BareunLanguageServiceClient 내부에서 처리하므로 여기서 직접 호출한다.
        res = self.client.analyze_syntax(phrase, self.custom_dicts, auto_split=auto_split,
                                         auto_spacing=auto_spacing, auto_jointing=auto_jointing,
                                         with_sense=with_sense)
        return Tagged(phrase, res)

    def tags(self, phrase: List[str], auto_split: bool = False, auto_spacing: bool = True,
             auto_jointing: bool = True, with_sense: bool = False) -> Tagged:
        """
        tag string array.
        :param phrase: array of string
        :param auto_split(bool, optional): Whether to automatically perform sentence split
        :param auto_spacing(bool, optional): Whether to automatically perform space insertion for typo correction
        :param auto_jointing(bool, optional): Whether to automatically perform word joining for typo correction
        :param with_sense(bool, optional): 동형이의어 의미 구분(WSD, 베타) 결과 포함 여부
        :return: Tagged result instance
        """
        if len(phrase) == 0:
            print("OOPS, no sentences.")
            return Tagged('', AnalyzeSyntaxResponse())
        p = '\n'.join(phrase)
        res = self.client.analyze_syntax(p, self.custom_dicts, auto_split=auto_split,
                                         auto_spacing=auto_spacing, auto_jointing=auto_jointing,
                                         with_sense=with_sense)
        return Tagged(p, res)

    def taglist(self, phrase: List[str], auto_spacing: bool = True, auto_jointing: bool = True,
                with_sense: bool = False) -> Tagged:
        """
        문장 분할 없이 입력된 문장 단위 그대로 형태소 분석을 수행합니다.
        :param phrase: 분석할 문장의 리스트
        :param auto_spacing(bool, optional): 띄어쓰기 보정 기능 (기본값: True)
        :param auto_jointing(bool, optional): 붙여쓰기 보정 기능 (기본값: True)
        :param with_sense(bool, optional): 동형이의어 의미 구분(WSD, 베타) 결과 포함 여부
        :return: Tagged result instance
        """
        if len(phrase) == 0:
            print("OOPS, no sentences.")
            return Tagged('', AnalyzeSyntaxListResponse())
        res = self.client.analyze_syntax_list(phrase, self.custom_dicts, auto_spacing=auto_spacing,
                                              auto_jointing=auto_jointing, with_sense=with_sense)
        return Tagged(phrase, res)

    def pos(self, phrase: str, flatten: bool = True, join: bool = False, detail: bool = False,
            sense: bool = False) -> List:
        """
        POS tagger.
        :param phrase  : string to analyse
        :param flatten : If False, returns original morphs.
        :param join    : If True, returns joined sets of morph and tag.
        :param detail  : if True, returns every things of morph result
        :param sense   : if True, 동형이의어 어깨번호를 함께 표기합니다(WSD, 베타).
                         이 값이 True 면 분석 요청도 자동으로 `with_sense=True` 로 보냅니다.
        """
        return self.tag(phrase, with_sense=sense).pos(flatten, join, detail, sense)

    def senses(self, phrase: str, auto_split: bool = False) -> List:
        """동형이의어 의미 구분(WSD, 베타) 결과만 바로 얻습니다.

        내부적으로 ``with_sense=True`` 로 형태소 분석을 수행한 뒤, 의미가 부여된 형태소만
        :class:`SenseInfo` 목록으로 돌려줍니다.

        .. code-block:: python
            >>> import bareunpy as brn
            >>> t = brn.Tagger(apikey="koba-YOURKEY")
            >>> for s in t.senses('다리를 건넜다.'):
            ...     print(s.content, s.tag, s.sense_no, s.meaning)
            다리 NNG 5 물을 건너거나 ... 만든 시설물.
            건너 VV 1 무엇을 사이에 두고 한편에서 맞은편으로 가다.

        :param phrase: 분석할 문자열
        :param auto_split: 문장 자동 분리 여부 (기본값: False)
        :return: :class:`SenseInfo` 의 목록
        """
        return self.tag(phrase, auto_split=auto_split, with_sense=True).senses()

    def morphs(self, phrase: str) -> List:
        """Parse phrase to morphemes."""
        return self.tag(phrase).morphs()

    def nouns(self, phrase: str) -> List:
        """Noun extractor."""
        return self.tag(phrase).nouns()

    def verbs(self, phrase: str) -> List:
        """Verbs extractor."""
        return self.tag(phrase).verbs()
