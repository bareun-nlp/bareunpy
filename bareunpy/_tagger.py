# -*- coding: utf-8 -*-
import json
from sys import stdout
from typing import IO, List, Union

from google.protobuf.json_format import MessageToDict
import grpc
from bareunpy._custom_dict import CustomDict
from bareunpy._lang_service_client import BareunLanguageServiceClient
from bareun.language_service_pb2 import AnalyzeSyntaxResponse, AnalyzeSyntaxListResponse, Morpheme, Sentence, Token


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

    def __init__(self, apikey:str, host: str = "", port: int = 5656, custom_dicts: List[str] = []):

        if host:
            host = host.strip()

        if host == "" or host is None:
            self.host = 'api.bareun.ai'
        else:
            self.host = host

        if port is not None:
            self.port = port
        else:
            if self.host.lower().startswith('api.bareun.ai'):
                self.port = 443
            else:
                self.port = 5656
        self.apikey = apikey

        if apikey == None or len(apikey) == 0:
            raise ValueError("an apikey must be provided!")

        self.client = BareunLanguageServiceClient(apikey, self.host, self.port)

        self.custom_dicts = custom_dicts
        self.internal_custom_dicts = {}
    
    def _handle_grpc_error(self, e: grpc.RpcError):
        """gRPC 에러를 처리하는 메서드"""
        details = getattr(e, "details", lambda: None)()
        code = getattr(e, "code", lambda: grpc.StatusCode.OK)()

        server_message = details if details else "서버에서 추가 메시지를 제공하지 않았습니다."
        if code == grpc.StatusCode.PERMISSION_DENIED:
            message = f'\n입력한 API KEY가 정확한지 확인해 주세요.\n > APIKEY: {self.apikey}\n서버 메시지: {server_message}'
        elif code == grpc.StatusCode.UNAVAILABLE:
            message = f'\n서버에 연결할 수 없습니다. 입력한 서버주소 [{self.host}:{self.port}]가 정확한지 확인해 주세요.\n서버 메시지: {server_message}'
        else:
            raise e
        raise Exception(message) from e

    @DeprecationWarning
    def set_domain(self, domain: str):
        """
        Set domain of custom dict.
        :param domain: domain name of custom dict
        """
        if len(self.custom_dicts) == 0:
            self.custom_dicts = []
        self.custom_dicts.append(domain)

    def set_custom_dicts(self, custom_dicts: List[str]):
        """
        Set domain of custom dict.
        :param domain: domain name of custom dict
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
            self.internal_custom_dicts[name] = CustomDict(self.apikey, name,  self.channel)
            return self.internal_custom_dicts[name]

    def tag(self, phrase: str, auto_split: bool = False, auto_spacing: bool = True, auto_jointing: bool = True) -> Tagged:
        if len(phrase) == 0:
            print("OOPS, no sentences.")
            return Tagged('', AnalyzeSyntaxResponse())
        try:
            res = self.client.analyze_syntax(phrase, self.custom_dicts, auto_split=auto_split, auto_spacing=auto_spacing, auto_jointing=auto_jointing)
            return Tagged(phrase, res)
        except grpc.RpcError as e:
            self._handle_grpc_error(e)

    def tags(self, phrase: List[str], auto_split: bool = False, auto_spacing: bool = True, auto_jointing: bool = True) -> Tagged:
        """
        tag string array.
        :param phrase: array of string
        :param auto_split(bool, optional): Whether to automatically perform sentence split
        :param auto_spacing(bool, optional): Whether to automatically perform space insertion for typo correction
        :param auto_jointing(bool, optional): Whether to automatically perform word joining for typo correction
        :return: Tagged result instance
        """
        if len(phrase) == 0:
            print("OOPS, no sentences.")
            return Tagged('', AnalyzeSyntaxResponse())
        p = '\n'.join(phrase)
        try:
            res = self.client.analyze_syntax(p, self.custom_dicts, auto_split=auto_split, auto_spacing=auto_spacing, auto_jointing=auto_jointing)
            return Tagged(p, res)
        except grpc.RpcError as e:
            self._handle_grpc_error(e)

    def taglist(self, phrase: List[str], auto_spacing: bool = True, auto_jointing: bool = True) -> Tagged:
        """
        the array is not being split and the input value is being returned as-is.
        :param phrase: array of string
        :param auto_split(bool, optional): Whether to automatically perform sentence split
        :param auto_spacing(bool, optional): Whether to automatically perform space insertion for typo correction
        :param auto_jointing(bool, optional): Whether to automatically perform word joining for typo correction
        :return: Tagged result instance
        """
        if len(phrase) == 0:
            print("OOPS, no sentences.")
            return Tagged('', AnalyzeSyntaxListResponse())
        try:
            res = self.client.analyze_syntax_list(phrase, self.custom_dicts, auto_spacing=auto_spacing, auto_jointing=auto_jointing)
            return Tagged(phrase, res)
        except grpc.RpcError as e:
            self._handle_grpc_error(e)

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
