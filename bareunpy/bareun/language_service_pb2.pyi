from bareun import lang_common_pb2 as _lang_common_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Sentence(_message.Message):
    __slots__ = ("text", "tokens", "refined")
    TEXT_FIELD_NUMBER: _ClassVar[int]
    TOKENS_FIELD_NUMBER: _ClassVar[int]
    REFINED_FIELD_NUMBER: _ClassVar[int]
    text: _lang_common_pb2.TextSpan
    tokens: _containers.RepeatedCompositeFieldContainer[Token]
    refined: str
    def __init__(self, text: _Optional[_Union[_lang_common_pb2.TextSpan, _Mapping]] = ..., tokens: _Optional[_Iterable[_Union[Token, _Mapping]]] = ..., refined: _Optional[str] = ...) -> None: ...

class Morpheme(_message.Message):
    __slots__ = ("text", "tag", "probability", "out_of_vocab", "custom_dict_name")
    class OutOfVocab(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        IN_WORD_EMBEDDING: _ClassVar[Morpheme.OutOfVocab]
        OUT_OF_VOCAB: _ClassVar[Morpheme.OutOfVocab]
        IN_CUSTOM_DICT: _ClassVar[Morpheme.OutOfVocab]
        IN_BUILTIN_DICT: _ClassVar[Morpheme.OutOfVocab]
        IN_URIMALSAEM: _ClassVar[Morpheme.OutOfVocab]
        IN_WIKI_DICT: _ClassVar[Morpheme.OutOfVocab]
        IN_ON_DICT: _ClassVar[Morpheme.OutOfVocab]
    IN_WORD_EMBEDDING: Morpheme.OutOfVocab
    OUT_OF_VOCAB: Morpheme.OutOfVocab
    IN_CUSTOM_DICT: Morpheme.OutOfVocab
    IN_BUILTIN_DICT: Morpheme.OutOfVocab
    IN_URIMALSAEM: Morpheme.OutOfVocab
    IN_WIKI_DICT: Morpheme.OutOfVocab
    IN_ON_DICT: Morpheme.OutOfVocab
    class Tag(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        UNK: _ClassVar[Morpheme.Tag]
        NNG: _ClassVar[Morpheme.Tag]
        NNP: _ClassVar[Morpheme.Tag]
        NNB: _ClassVar[Morpheme.Tag]
        NP: _ClassVar[Morpheme.Tag]
        NR: _ClassVar[Morpheme.Tag]
        NF: _ClassVar[Morpheme.Tag]
        NA: _ClassVar[Morpheme.Tag]
        NV: _ClassVar[Morpheme.Tag]
        VV: _ClassVar[Morpheme.Tag]
        VA: _ClassVar[Morpheme.Tag]
        VX: _ClassVar[Morpheme.Tag]
        VCP: _ClassVar[Morpheme.Tag]
        VCN: _ClassVar[Morpheme.Tag]
        MMA: _ClassVar[Morpheme.Tag]
        MMD: _ClassVar[Morpheme.Tag]
        MMN: _ClassVar[Morpheme.Tag]
        MAG: _ClassVar[Morpheme.Tag]
        MAJ: _ClassVar[Morpheme.Tag]
        IC: _ClassVar[Morpheme.Tag]
        JKS: _ClassVar[Morpheme.Tag]
        JKC: _ClassVar[Morpheme.Tag]
        JKG: _ClassVar[Morpheme.Tag]
        JKO: _ClassVar[Morpheme.Tag]
        JKB: _ClassVar[Morpheme.Tag]
        JKV: _ClassVar[Morpheme.Tag]
        JKQ: _ClassVar[Morpheme.Tag]
        JX: _ClassVar[Morpheme.Tag]
        JC: _ClassVar[Morpheme.Tag]
        EP: _ClassVar[Morpheme.Tag]
        EF: _ClassVar[Morpheme.Tag]
        EC: _ClassVar[Morpheme.Tag]
        ETN: _ClassVar[Morpheme.Tag]
        ETM: _ClassVar[Morpheme.Tag]
        XPN: _ClassVar[Morpheme.Tag]
        XSN: _ClassVar[Morpheme.Tag]
        XSV: _ClassVar[Morpheme.Tag]
        XSA: _ClassVar[Morpheme.Tag]
        XR: _ClassVar[Morpheme.Tag]
        SF: _ClassVar[Morpheme.Tag]
        SP: _ClassVar[Morpheme.Tag]
        SS: _ClassVar[Morpheme.Tag]
        SE: _ClassVar[Morpheme.Tag]
        SO: _ClassVar[Morpheme.Tag]
        SW: _ClassVar[Morpheme.Tag]
        SL: _ClassVar[Morpheme.Tag]
        SH: _ClassVar[Morpheme.Tag]
        SN: _ClassVar[Morpheme.Tag]
    UNK: Morpheme.Tag
    NNG: Morpheme.Tag
    NNP: Morpheme.Tag
    NNB: Morpheme.Tag
    NP: Morpheme.Tag
    NR: Morpheme.Tag
    NF: Morpheme.Tag
    NA: Morpheme.Tag
    NV: Morpheme.Tag
    VV: Morpheme.Tag
    VA: Morpheme.Tag
    VX: Morpheme.Tag
    VCP: Morpheme.Tag
    VCN: Morpheme.Tag
    MMA: Morpheme.Tag
    MMD: Morpheme.Tag
    MMN: Morpheme.Tag
    MAG: Morpheme.Tag
    MAJ: Morpheme.Tag
    IC: Morpheme.Tag
    JKS: Morpheme.Tag
    JKC: Morpheme.Tag
    JKG: Morpheme.Tag
    JKO: Morpheme.Tag
    JKB: Morpheme.Tag
    JKV: Morpheme.Tag
    JKQ: Morpheme.Tag
    JX: Morpheme.Tag
    JC: Morpheme.Tag
    EP: Morpheme.Tag
    EF: Morpheme.Tag
    EC: Morpheme.Tag
    ETN: Morpheme.Tag
    ETM: Morpheme.Tag
    XPN: Morpheme.Tag
    XSN: Morpheme.Tag
    XSV: Morpheme.Tag
    XSA: Morpheme.Tag
    XR: Morpheme.Tag
    SF: Morpheme.Tag
    SP: Morpheme.Tag
    SS: Morpheme.Tag
    SE: Morpheme.Tag
    SO: Morpheme.Tag
    SW: Morpheme.Tag
    SL: Morpheme.Tag
    SH: Morpheme.Tag
    SN: Morpheme.Tag
    TEXT_FIELD_NUMBER: _ClassVar[int]
    TAG_FIELD_NUMBER: _ClassVar[int]
    PROBABILITY_FIELD_NUMBER: _ClassVar[int]
    OUT_OF_VOCAB_FIELD_NUMBER: _ClassVar[int]
    CUSTOM_DICT_NAME_FIELD_NUMBER: _ClassVar[int]
    text: _lang_common_pb2.TextSpan
    tag: Morpheme.Tag
    probability: float
    out_of_vocab: Morpheme.OutOfVocab
    custom_dict_name: str
    def __init__(self, text: _Optional[_Union[_lang_common_pb2.TextSpan, _Mapping]] = ..., tag: _Optional[_Union[Morpheme.Tag, str]] = ..., probability: _Optional[float] = ..., out_of_vocab: _Optional[_Union[Morpheme.OutOfVocab, str]] = ..., custom_dict_name: _Optional[str] = ...) -> None: ...

class Token(_message.Message):
    __slots__ = ("text", "morphemes", "lemma", "tagged", "modified")
    TEXT_FIELD_NUMBER: _ClassVar[int]
    MORPHEMES_FIELD_NUMBER: _ClassVar[int]
    LEMMA_FIELD_NUMBER: _ClassVar[int]
    TAGGED_FIELD_NUMBER: _ClassVar[int]
    MODIFIED_FIELD_NUMBER: _ClassVar[int]
    text: _lang_common_pb2.TextSpan
    morphemes: _containers.RepeatedCompositeFieldContainer[Morpheme]
    lemma: str
    tagged: str
    modified: str
    def __init__(self, text: _Optional[_Union[_lang_common_pb2.TextSpan, _Mapping]] = ..., morphemes: _Optional[_Iterable[_Union[Morpheme, _Mapping]]] = ..., lemma: _Optional[str] = ..., tagged: _Optional[str] = ..., modified: _Optional[str] = ...) -> None: ...

class AnalyzeSyntaxRequest(_message.Message):
    __slots__ = ("document", "encoding_type", "auto_split_sentence", "custom_domain", "auto_spacing", "auto_jointing", "custom_dict_names")
    DOCUMENT_FIELD_NUMBER: _ClassVar[int]
    ENCODING_TYPE_FIELD_NUMBER: _ClassVar[int]
    AUTO_SPLIT_SENTENCE_FIELD_NUMBER: _ClassVar[int]
    CUSTOM_DOMAIN_FIELD_NUMBER: _ClassVar[int]
    AUTO_SPACING_FIELD_NUMBER: _ClassVar[int]
    AUTO_JOINTING_FIELD_NUMBER: _ClassVar[int]
    CUSTOM_DICT_NAMES_FIELD_NUMBER: _ClassVar[int]
    document: _lang_common_pb2.Document
    encoding_type: _lang_common_pb2.EncodingType
    auto_split_sentence: bool
    custom_domain: str
    auto_spacing: bool
    auto_jointing: bool
    custom_dict_names: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, document: _Optional[_Union[_lang_common_pb2.Document, _Mapping]] = ..., encoding_type: _Optional[_Union[_lang_common_pb2.EncodingType, str]] = ..., auto_split_sentence: _Optional[bool] = ..., custom_domain: _Optional[str] = ..., auto_spacing: _Optional[bool] = ..., auto_jointing: _Optional[bool] = ..., custom_dict_names: _Optional[_Iterable[str]] = ...) -> None: ...

class AnalyzeSyntaxResponse(_message.Message):
    __slots__ = ("sentences", "language", "tokens_count")
    SENTENCES_FIELD_NUMBER: _ClassVar[int]
    LANGUAGE_FIELD_NUMBER: _ClassVar[int]
    TOKENS_COUNT_FIELD_NUMBER: _ClassVar[int]
    sentences: _containers.RepeatedCompositeFieldContainer[Sentence]
    language: str
    tokens_count: int
    def __init__(self, sentences: _Optional[_Iterable[_Union[Sentence, _Mapping]]] = ..., language: _Optional[str] = ..., tokens_count: _Optional[int] = ...) -> None: ...

class AnalyzeSyntaxListRequest(_message.Message):
    __slots__ = ("sentences", "language", "encoding_type", "custom_domain", "auto_spacing", "auto_jointing", "custom_dict_names")
    SENTENCES_FIELD_NUMBER: _ClassVar[int]
    LANGUAGE_FIELD_NUMBER: _ClassVar[int]
    ENCODING_TYPE_FIELD_NUMBER: _ClassVar[int]
    CUSTOM_DOMAIN_FIELD_NUMBER: _ClassVar[int]
    AUTO_SPACING_FIELD_NUMBER: _ClassVar[int]
    AUTO_JOINTING_FIELD_NUMBER: _ClassVar[int]
    CUSTOM_DICT_NAMES_FIELD_NUMBER: _ClassVar[int]
    sentences: _containers.RepeatedScalarFieldContainer[str]
    language: str
    encoding_type: _lang_common_pb2.EncodingType
    custom_domain: str
    auto_spacing: bool
    auto_jointing: bool
    custom_dict_names: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, sentences: _Optional[_Iterable[str]] = ..., language: _Optional[str] = ..., encoding_type: _Optional[_Union[_lang_common_pb2.EncodingType, str]] = ..., custom_domain: _Optional[str] = ..., auto_spacing: _Optional[bool] = ..., auto_jointing: _Optional[bool] = ..., custom_dict_names: _Optional[_Iterable[str]] = ...) -> None: ...

class AnalyzeSyntaxListResponse(_message.Message):
    __slots__ = ("sentences", "language", "tokens_count")
    SENTENCES_FIELD_NUMBER: _ClassVar[int]
    LANGUAGE_FIELD_NUMBER: _ClassVar[int]
    TOKENS_COUNT_FIELD_NUMBER: _ClassVar[int]
    sentences: _containers.RepeatedCompositeFieldContainer[Sentence]
    language: str
    tokens_count: int
    def __init__(self, sentences: _Optional[_Iterable[_Union[Sentence, _Mapping]]] = ..., language: _Optional[str] = ..., tokens_count: _Optional[int] = ...) -> None: ...

class TokenizeRequest(_message.Message):
    __slots__ = ("document", "encoding_type", "auto_split_sentence", "auto_spacing")
    DOCUMENT_FIELD_NUMBER: _ClassVar[int]
    ENCODING_TYPE_FIELD_NUMBER: _ClassVar[int]
    AUTO_SPLIT_SENTENCE_FIELD_NUMBER: _ClassVar[int]
    AUTO_SPACING_FIELD_NUMBER: _ClassVar[int]
    document: _lang_common_pb2.Document
    encoding_type: _lang_common_pb2.EncodingType
    auto_split_sentence: bool
    auto_spacing: bool
    def __init__(self, document: _Optional[_Union[_lang_common_pb2.Document, _Mapping]] = ..., encoding_type: _Optional[_Union[_lang_common_pb2.EncodingType, str]] = ..., auto_split_sentence: _Optional[bool] = ..., auto_spacing: _Optional[bool] = ...) -> None: ...

class Segment(_message.Message):
    __slots__ = ("text", "hint")
    TEXT_FIELD_NUMBER: _ClassVar[int]
    HINT_FIELD_NUMBER: _ClassVar[int]
    text: _lang_common_pb2.TextSpan
    hint: str
    def __init__(self, text: _Optional[_Union[_lang_common_pb2.TextSpan, _Mapping]] = ..., hint: _Optional[str] = ...) -> None: ...

class SegmentToken(_message.Message):
    __slots__ = ("text", "segments", "tagged")
    TEXT_FIELD_NUMBER: _ClassVar[int]
    SEGMENTS_FIELD_NUMBER: _ClassVar[int]
    TAGGED_FIELD_NUMBER: _ClassVar[int]
    text: _lang_common_pb2.TextSpan
    segments: _containers.RepeatedCompositeFieldContainer[Segment]
    tagged: str
    def __init__(self, text: _Optional[_Union[_lang_common_pb2.TextSpan, _Mapping]] = ..., segments: _Optional[_Iterable[_Union[Segment, _Mapping]]] = ..., tagged: _Optional[str] = ...) -> None: ...

class SegmentSentence(_message.Message):
    __slots__ = ("text", "tokens")
    TEXT_FIELD_NUMBER: _ClassVar[int]
    TOKENS_FIELD_NUMBER: _ClassVar[int]
    text: _lang_common_pb2.TextSpan
    tokens: _containers.RepeatedCompositeFieldContainer[SegmentToken]
    def __init__(self, text: _Optional[_Union[_lang_common_pb2.TextSpan, _Mapping]] = ..., tokens: _Optional[_Iterable[_Union[SegmentToken, _Mapping]]] = ...) -> None: ...

class TokenizeResponse(_message.Message):
    __slots__ = ("sentences", "language", "tokens_count")
    SENTENCES_FIELD_NUMBER: _ClassVar[int]
    LANGUAGE_FIELD_NUMBER: _ClassVar[int]
    TOKENS_COUNT_FIELD_NUMBER: _ClassVar[int]
    sentences: _containers.RepeatedCompositeFieldContainer[SegmentSentence]
    language: str
    tokens_count: int
    def __init__(self, sentences: _Optional[_Iterable[_Union[SegmentSentence, _Mapping]]] = ..., language: _Optional[str] = ..., tokens_count: _Optional[int] = ...) -> None: ...
