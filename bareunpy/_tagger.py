# -*- coding: utf-8 -*-
import json
from sys import stdout
from typing import IO, List, Any

from google.protobuf.json_format import MessageToDict
import grpc
from bareunpy._custom_dict import CustomDict
from bareunpy._lang_service_client import BareunLanguageServiceClient, MAX_MESSAGE_LENGTH
from bareun.language_service_pb2 import AnalyzeSyntaxResponse, Morpheme, Sentence, Token


class Tagged:
    """
    Tagged result.
    It has various output manipulations.
    """

    def __init__(self, phrase: str, res: AnalyzeSyntaxResponse):
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

    def msg(self) -> AnalyzeSyntaxResponse:
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
    def _pos(m: Morpheme, join: bool, detail: bool):
        if join:
            if detail:
                p = f':{m.probability:5.3f}' if m.probability > 0 else ''
                oov = f'#{Morpheme.OutOfVocab.Name(m.out_of_vocab)}' if m.out_of_vocab != 0 else ''
                return f'{m.text.content}/{Morpheme.Tag.Name(m.tag)}{p}{oov}'
            else:
                return f'{m.text.content}/{Morpheme.Tag.Name(m.tag)}'
        else:
            if detail:
                return m.text.content,\
                       Morpheme.Tag.Name(m.tag),\
                       Morpheme.OutOfVocab.Name(m.out_of_vocab),\
                       m.probability
            else:
                return m.text.content, Morpheme.Tag.Name(m.tag)

    def pos(self, flatten: bool = True, join: bool = False, detail: bool = False) -> List:
        """
        POS tagger to tuple.
        :param flatten : If False, returns original morphs.
        :param join    : If True, returns joined sets of morph and tag.
        :param detail  : if True, returns everything of morph result
        """
        if flatten:
            return [Tagged._pos(m, join, detail) for s in self.r.sentences
                    for token in s.tokens
                    for m in token.morphemes]
        else:
            return [[Tagged._pos(m, join, detail) for m in token.morphemes]
                    for s in self.r.sentences
                    for token in s.tokens]

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
        >>> tagger = brn.Tagger(domain="custom")
        >>> print(tagger.morphs('안녕하세요, 반가워요.'))
        ['안녕', '하', '시', '어요', ',', '반갑', '어요', '.']
        >>> print(tagger.nouns('나비 허리에 새파란 초생달이 시리다.'))
        ['나비', '허리', '초생달']
        >>> print(tagger.pos('햇빛이 선명하게 나뭇잎을 핥고 있었다.'))
        [('햇빛', 'NNG'), ('이', 'JKS'), ('선명', 'NNG'), ('하', 'XSA'), ('게', 'EC'), ('나뭇잎', 'NNG'),
         ('을', 'JKO'), ('핥', 'VV'), ('고', 'EC'), ('있', 'VX'), ('었', 'EP'), ('다', 'EF'), ('.', 'SF')]
    :param host         : str. host name for bareun server
    :param port         : int. port  for bareun server
    :param domain       : custom domain name for analyzing request
    """

    def __init__(self, host: str = "", port: int = 5656, domain: str = ""):

        if host:
            host = host.strip()
        if domain:
            domain = domain.strip()

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

        self.domain = domain
        self.custom_dicts = {}

    def set_domain(self, domain: str):
        """
        Set domain of custom dict.
        :param domain: domain name of custom dict
        """
        self.domain = domain

    def custom_dict(self, domain: str) -> CustomDict:
        # self.domain = domain
        if domain == "" or domain is None:
            raise ValueError("invalid domain name for custom dict")

        if domain in self.custom_dicts:
            return self.custom_dicts[domain]
        else:
            self.custom_dicts[domain] = CustomDict(domain, self.channel)
            return self.custom_dicts[domain]

    def tag(self, phrase: str, auto_split: bool = False) -> Tagged:
        if len(phrase) == 0:
            print("OOPS, no sentences.")
            return Tagged('', AnalyzeSyntaxResponse())
        return Tagged(phrase,
                      self.client.analyze_syntax(phrase, self.domain, auto_split))

    def tags(self, phrase: List[str]) -> Tagged:
        """
        tag string array.
        :param phrase: array of string
        :return: Tagged result instance
        """
        if len(phrase) == 0:
            print("OOPS, no sentences.")
            return Tagged('', AnalyzeSyntaxResponse())
        p = '\n'.join(phrase)
        return Tagged(p,
                      self.client.analyze_syntax(p, self.domain, auto_split=False))

    def pos(self, phrase: str, flatten: bool = True, join: bool = False, detail: bool = False) -> List:
        """
        POS tagger.
        :param phrase  : string to analyse
        :param flatten : If False, returns original morphs.
        :param join    : If True, returns joined sets of morph and tag.
        :param detail  : if True, returns every things of morph result
        """
        return self.tag(phrase).pos(flatten, join, detail)

    def morphs(self, phrase: str) -> List:
        """Parse phrase to morphemes."""
        return self.tag(phrase).morphs()

    def nouns(self, phrase: str) -> List:
        """Noun extractor."""
        return self.tag(phrase).nouns()

    def verbs(self, phrase: str) -> List:
        """Verbs extractor."""
        return self.tag(phrase).verbs()
