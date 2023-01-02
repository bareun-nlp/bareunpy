# -*- coding: utf-8 -*-
import json
from sys import stdout
from typing import IO, List, Any

from google.protobuf.json_format import MessageToDict
import grpc
from bareunpy._lang_service_client import BareunLanguageServiceClient, MAX_MESSAGE_LENGTH
from bareun.language_service_pb2 import TokenizeResponse, Segment, SegmentSentence, SegmentToken


class Tokenized:
    """
    Tokenized result.
    It has various output manipulations.
    """

    def __init__(self, phrase: str, res: TokenizeResponse):
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
            self.r = TokenizeResponse()
            self.phrase = ''

    def msg(self) -> TokenizeResponse:
        """
        Protobuf message object containing all of NLP engine.
        """
        return self.r

    def sentences(self) -> List[SegmentSentence]:
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
        return MessageToDict(self.r, 
            including_default_value_fields=True,
            use_integers_for_enums=False)

    def as_json_str(self) -> str:
        """
        a json string representing analyzed sentences.
        :return: json string
        """
        d = MessageToDict(self.r,
            including_default_value_fields=True,
            use_integers_for_enums=False)
        return json.dumps(d, ensure_ascii=False, indent=2)

    def print_as_json(self, out: IO = stdout):
        """
        print the analysis result
        :param out: File, if nothing provided, sys.stdout is used.
        :return: None
        """
        d = MessageToDict(self.r,
            including_default_value_fields=True,
            use_integers_for_enums=False)
        json.dump(d, out, ensure_ascii=False, indent=2)

    @staticmethod
    def _segment(m: Segment, join: bool, detail: bool):
        if join:
            if detail:
                return f'{m.text.content}/{m.hint}'
            else:
                return f'{m.text.content}'
        else:
            if detail:
                return m.text.content, m.hint
            else:
                return m.text.content

    def seg(self, flatten: bool = True, join: bool = False, detail: bool = False) -> List:
        """
        분절의 결과를 튜플 형태로 반환한다.
        :param flatten : If False, returns original morphs.
        :param join    : If True, returns joined sets of morph and tag.
        :param detail  : if True, returns everything of morph result
        """
        if flatten:
            return [Tokenized._segment(m, join, detail) for s in self.r.sentences
                    for token in s.tokens
                    for m in token.segments]
        else:
            return [[Tokenized._segment(m, join, detail) for m in token.segments]
                    for s in self.r.sentences
                    for token in s.tokens]

    def segments(self) -> List:
        """문장의 모든 segment들을 반환한다. """
        return [m.text.content for s in self.r.sentences
                for token in s.tokens
                for m in token.segments]

    def nouns(self) -> List:
        """체언을 추출한다."""
        return [m.text.content for s in self.r.sentences
                for token in s.tokens
                for m in token.segments
                if m.hint == 'N']

    def verbs(self) -> List:
        """동사 또는 형용사, 즉, 용언을 추출한다."""
        return [m.text.content for s in self.r.sentences
                for token in s.tokens
                for m in token.segments
                if m.hint == 'V']

    def predicates(self) -> List:
        """용언을 추출한다."""
        return [m.text.content for s in self.r.sentences
                for token in s.tokens
                for m in token.segments
                if m.hint == 'V']

    def substantives(self) -> List:
        """체언을 추출한다."""
        return [m.text.content for s in self.r.sentences
                for token in s.tokens
                for m in token.segments
                if m.hint == 'N']

    def symbols(self) -> List:
        """기호를 추출한다."""
        return [m.text.content for s in self.r.sentences
                for token in s.tokens
                for m in token.segments
                if m.hint == 'S']

    def adverbs(self) -> List:
        """부사를 추출한다.."""
        return [m.text.content for s in self.r.sentences
                for token in s.tokens
                for m in token.segments
                if m.hint == 'A']

    def prenouns(self) -> List:
        """관형사를 추출한다."""
        return [m.text.content for s in self.r.sentences
                for token in s.tokens
                for m in token.segments
                if m.hint == 'M']

    def postpositions(self) -> List:
        """감탄사를 추출한다."""
        return [m.text.content for s in self.r.sentences
                for token in s.tokens
                for m in token.segments
                if m.hint == 'J']

    def interjections(self) -> List:
        """감탄사를 추출한다."""
        return [m.text.content for s in self.r.sentences
                for token in s.tokens
                for m in token.segments
                if m.hint == 'I']

    def endings(self) -> List:
        """어미를 반환한다."""
        return [m.text.content for s in self.r.sentences
                for token in s.tokens
                for m in token.segments
                if m.hint == 'E']

class Tokenizer:
    """Wrapper for `bareun v1.7.x <https://github.com/bareun-nlp>`_.
    'bareun' is a morphological analyzer developed by Baikal AI, Inc. and Korea Press Foundation.

    .. code-block:: python
        :emphasize-lines: 1
        >>> import bareunpy as brn
        >>> tokenizer = brn.Tokenizer()
        >>> print(tokenizer.segments('안녕하세요, 반가워요.'))
        ['안녕', '하', '시', '어요', ',', '반갑', '어요', '.']
        >>> print(tokenizer.nouns('나비 허리에 새파란 초생달이 시리다.'))
        ['나비', '허리', '초생달']
        >>> print(tokenizer.seg('햇빛이 선명하게 나뭇잎을 핥고 있었다.'))
        [('햇빛', 'NNG'), ('이', 'JKS'), ('선명', 'NNG'), ('하', 'XSA'), ('게', 'EC'), ('나뭇잎', 'NNG'),
         ('을', 'JKO'), ('핥', 'VV'), ('고', 'EC'), ('있', 'VX'), ('었', 'EP'), ('다', 'EF'), ('.', 'SF')]
    :param host         : str. host name for bareun server
    :param port         : int. port  for bareun server
    """

    def __init__(self, host: str = "", port: int = 5656):

        if host:
            host = host.strip()
        if host == "" or host is None:
            self.host = 'nlp.bareun.ai'
        else:
            self.host = host

        if port is not None:
            self.port = port
        else:
            self.port = 5656

        self.channel = grpc.insecure_channel(
            f"{self.host}:{self.port}",
            options=[
                ('grpc.max_send_message_length', MAX_MESSAGE_LENGTH),
                ('grpc.max_receive_message_length', MAX_MESSAGE_LENGTH),
            ])
        self.client = BareunLanguageServiceClient(self.channel)

    def tokenize(self, phrase: str, auto_split: bool = False) -> Tokenized:
        if len(phrase) == 0:
            print("OOPS, no sentences.")
            return Tokenized('', TokenizeResponse())
        return Tokenized(phrase,
                      self.client.tokenize(phrase, auto_split))

    def tokenize_list(self, phrase: List[str]) -> Tokenized:
        """
        tag string array.
        :param phrase: array of string
        :return: Tagged result instance
        """
        if len(phrase) == 0:
            print("OOPS, no sentences.")
            return Tokenized('', TokenizeResponse())
        p = '\n'.join(phrase)
        return Tokenized(p,
                      self.client.tokenize(p, auto_split=False))

    def seg(self, phrase: str, flatten: bool = True, join: bool = False, detail: bool = False) -> List:
        """
        분절 하기,
        :param phrase  : string to analyse
        :param flatten : If False, returns original morphs.
        :param join    : If True, returns joined sets of morph and tag.
        :param detail  : if True, returns every things of morph result
        """
        return self.tokenize(phrase).seg(flatten, join, detail)

    def segments(self, phrase: str) -> List:
        """문장을 분절하여 어절 내부의 기본 단위로 만들어 낸다."""
        return self.tokenize(phrase).segments()

    def nouns(self, phrase: str) -> List:
        """문장을 분절하여 어절 내부의 기본 단위로 만들어 내고 체언을 뽑아낸다."""
        return self.tokenize(phrase).nouns()

    def verbs(self, phrase: str) -> List:
        """문장을 분절하여 어절 내부의 기본 단위로 만들어 내고 용언을 뽑아낸다."""
        return self.tokenize(phrase).verbs()
