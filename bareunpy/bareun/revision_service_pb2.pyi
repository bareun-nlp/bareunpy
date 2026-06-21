from bareun import lang_common_pb2 as _lang_common_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class RevisionCategory(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    UNKNOWN: _ClassVar[RevisionCategory]
    GRAMMER: _ClassVar[RevisionCategory]
    WORD: _ClassVar[RevisionCategory]
    SPACING: _ClassVar[RevisionCategory]
    STANDARD: _ClassVar[RevisionCategory]
    TYPO: _ClassVar[RevisionCategory]
    FOREIGN_WORD: _ClassVar[RevisionCategory]
    CONFUSABLE_WORDS: _ClassVar[RevisionCategory]
    SENTENCE: _ClassVar[RevisionCategory]
    CONFIRM: _ClassVar[RevisionCategory]
    THINKING: _ClassVar[RevisionCategory]

class CustomDictPos(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    POS_UNK: _ClassVar[CustomDictPos]
    POS_NNG: _ClassVar[CustomDictPos]
    POS_NNP: _ClassVar[CustomDictPos]
    POS_NNG_CARET: _ClassVar[CustomDictPos]
    POS_VV: _ClassVar[CustomDictPos]
    POS_VA: _ClassVar[CustomDictPos]
    POS_MM: _ClassVar[CustomDictPos]
    POS_MAG: _ClassVar[CustomDictPos]
    POS_IC: _ClassVar[CustomDictPos]
UNKNOWN: RevisionCategory
GRAMMER: RevisionCategory
WORD: RevisionCategory
SPACING: RevisionCategory
STANDARD: RevisionCategory
TYPO: RevisionCategory
FOREIGN_WORD: RevisionCategory
CONFUSABLE_WORDS: RevisionCategory
SENTENCE: RevisionCategory
CONFIRM: RevisionCategory
THINKING: RevisionCategory
POS_UNK: CustomDictPos
POS_NNG: CustomDictPos
POS_NNP: CustomDictPos
POS_NNG_CARET: CustomDictPos
POS_VV: CustomDictPos
POS_VA: CustomDictPos
POS_MM: CustomDictPos
POS_MAG: CustomDictPos
POS_IC: CustomDictPos

class RevisionConfig(_message.Message):
    __slots__ = ("disable_split_sentence", "disable_caret_spacing", "disable_vx_spacing", "treat_as_title", "enable_limited_punctuation", "disable_confusion", "enable_cleanup_whitespace", "disable_typo_correction", "enable_sentence_check")
    DISABLE_SPLIT_SENTENCE_FIELD_NUMBER: _ClassVar[int]
    DISABLE_CARET_SPACING_FIELD_NUMBER: _ClassVar[int]
    DISABLE_VX_SPACING_FIELD_NUMBER: _ClassVar[int]
    TREAT_AS_TITLE_FIELD_NUMBER: _ClassVar[int]
    ENABLE_LIMITED_PUNCTUATION_FIELD_NUMBER: _ClassVar[int]
    DISABLE_CONFUSION_FIELD_NUMBER: _ClassVar[int]
    ENABLE_CLEANUP_WHITESPACE_FIELD_NUMBER: _ClassVar[int]
    DISABLE_TYPO_CORRECTION_FIELD_NUMBER: _ClassVar[int]
    ENABLE_SENTENCE_CHECK_FIELD_NUMBER: _ClassVar[int]
    disable_split_sentence: bool
    disable_caret_spacing: bool
    disable_vx_spacing: bool
    treat_as_title: bool
    enable_limited_punctuation: bool
    disable_confusion: bool
    enable_cleanup_whitespace: bool
    disable_typo_correction: bool
    enable_sentence_check: bool
    def __init__(self, disable_split_sentence: _Optional[bool] = ..., disable_caret_spacing: _Optional[bool] = ..., disable_vx_spacing: _Optional[bool] = ..., treat_as_title: _Optional[bool] = ..., enable_limited_punctuation: _Optional[bool] = ..., disable_confusion: _Optional[bool] = ..., enable_cleanup_whitespace: _Optional[bool] = ..., disable_typo_correction: _Optional[bool] = ..., enable_sentence_check: _Optional[bool] = ...) -> None: ...

class CorrectErrorRequest(_message.Message):
    __slots__ = ("document", "encoding_type", "custom_domain", "custom_dict_names", "config")
    DOCUMENT_FIELD_NUMBER: _ClassVar[int]
    ENCODING_TYPE_FIELD_NUMBER: _ClassVar[int]
    CUSTOM_DOMAIN_FIELD_NUMBER: _ClassVar[int]
    CUSTOM_DICT_NAMES_FIELD_NUMBER: _ClassVar[int]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    document: _lang_common_pb2.Document
    encoding_type: _lang_common_pb2.EncodingType
    custom_domain: str
    custom_dict_names: _containers.RepeatedScalarFieldContainer[str]
    config: RevisionConfig
    def __init__(self, document: _Optional[_Union[_lang_common_pb2.Document, _Mapping]] = ..., encoding_type: _Optional[_Union[_lang_common_pb2.EncodingType, str]] = ..., custom_domain: _Optional[str] = ..., custom_dict_names: _Optional[_Iterable[str]] = ..., config: _Optional[_Union[RevisionConfig, _Mapping]] = ...) -> None: ...

class ReviseHelp(_message.Message):
    __slots__ = ("id", "category", "comment", "examples", "rule_article")
    ID_FIELD_NUMBER: _ClassVar[int]
    CATEGORY_FIELD_NUMBER: _ClassVar[int]
    COMMENT_FIELD_NUMBER: _ClassVar[int]
    EXAMPLES_FIELD_NUMBER: _ClassVar[int]
    RULE_ARTICLE_FIELD_NUMBER: _ClassVar[int]
    id: str
    category: RevisionCategory
    comment: str
    examples: _containers.RepeatedScalarFieldContainer[str]
    rule_article: str
    def __init__(self, id: _Optional[str] = ..., category: _Optional[_Union[RevisionCategory, str]] = ..., comment: _Optional[str] = ..., examples: _Optional[_Iterable[str]] = ..., rule_article: _Optional[str] = ...) -> None: ...

class Revision(_message.Message):
    __slots__ = ("revised", "score", "category", "help_id", "thinking_id")
    REVISED_FIELD_NUMBER: _ClassVar[int]
    SCORE_FIELD_NUMBER: _ClassVar[int]
    CATEGORY_FIELD_NUMBER: _ClassVar[int]
    HELP_ID_FIELD_NUMBER: _ClassVar[int]
    THINKING_ID_FIELD_NUMBER: _ClassVar[int]
    revised: str
    score: float
    category: RevisionCategory
    help_id: str
    thinking_id: int
    def __init__(self, revised: _Optional[str] = ..., score: _Optional[float] = ..., category: _Optional[_Union[RevisionCategory, str]] = ..., help_id: _Optional[str] = ..., thinking_id: _Optional[int] = ...) -> None: ...

class RevisedBlock(_message.Message):
    __slots__ = ("origin", "revised", "revisions", "nested", "lemma", "pos", "thinking_count")
    ORIGIN_FIELD_NUMBER: _ClassVar[int]
    REVISED_FIELD_NUMBER: _ClassVar[int]
    REVISIONS_FIELD_NUMBER: _ClassVar[int]
    NESTED_FIELD_NUMBER: _ClassVar[int]
    LEMMA_FIELD_NUMBER: _ClassVar[int]
    POS_FIELD_NUMBER: _ClassVar[int]
    THINKING_COUNT_FIELD_NUMBER: _ClassVar[int]
    origin: _lang_common_pb2.TextSpan
    revised: str
    revisions: _containers.RepeatedCompositeFieldContainer[Revision]
    nested: _containers.RepeatedCompositeFieldContainer[RevisedBlock]
    lemma: str
    pos: CustomDictPos
    thinking_count: int
    def __init__(self, origin: _Optional[_Union[_lang_common_pb2.TextSpan, _Mapping]] = ..., revised: _Optional[str] = ..., revisions: _Optional[_Iterable[_Union[Revision, _Mapping]]] = ..., nested: _Optional[_Iterable[_Union[RevisedBlock, _Mapping]]] = ..., lemma: _Optional[str] = ..., pos: _Optional[_Union[CustomDictPos, str]] = ..., thinking_count: _Optional[int] = ...) -> None: ...

class RevisedSentence(_message.Message):
    __slots__ = ("origin", "revised")
    ORIGIN_FIELD_NUMBER: _ClassVar[int]
    REVISED_FIELD_NUMBER: _ClassVar[int]
    origin: str
    revised: str
    def __init__(self, origin: _Optional[str] = ..., revised: _Optional[str] = ...) -> None: ...

class CleanUpRange(_message.Message):
    __slots__ = ("offset", "length", "position")
    class CleanUpPosition(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        START: _ClassVar[CleanUpRange.CleanUpPosition]
        END: _ClassVar[CleanUpRange.CleanUpPosition]
        MIDDLE: _ClassVar[CleanUpRange.CleanUpPosition]
    START: CleanUpRange.CleanUpPosition
    END: CleanUpRange.CleanUpPosition
    MIDDLE: CleanUpRange.CleanUpPosition
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    LENGTH_FIELD_NUMBER: _ClassVar[int]
    POSITION_FIELD_NUMBER: _ClassVar[int]
    offset: int
    length: int
    position: CleanUpRange.CleanUpPosition
    def __init__(self, offset: _Optional[int] = ..., length: _Optional[int] = ..., position: _Optional[_Union[CleanUpRange.CleanUpPosition, str]] = ...) -> None: ...

class CorrectErrorResponse(_message.Message):
    __slots__ = ("origin", "revised", "revised_blocks", "whitespace_cleanup_ranges", "revised_sentences", "helps", "language", "tokens_count")
    class HelpsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: ReviseHelp
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[ReviseHelp, _Mapping]] = ...) -> None: ...
    ORIGIN_FIELD_NUMBER: _ClassVar[int]
    REVISED_FIELD_NUMBER: _ClassVar[int]
    REVISED_BLOCKS_FIELD_NUMBER: _ClassVar[int]
    WHITESPACE_CLEANUP_RANGES_FIELD_NUMBER: _ClassVar[int]
    REVISED_SENTENCES_FIELD_NUMBER: _ClassVar[int]
    HELPS_FIELD_NUMBER: _ClassVar[int]
    LANGUAGE_FIELD_NUMBER: _ClassVar[int]
    TOKENS_COUNT_FIELD_NUMBER: _ClassVar[int]
    origin: str
    revised: str
    revised_blocks: _containers.RepeatedCompositeFieldContainer[RevisedBlock]
    whitespace_cleanup_ranges: _containers.RepeatedCompositeFieldContainer[CleanUpRange]
    revised_sentences: _containers.RepeatedCompositeFieldContainer[RevisedSentence]
    helps: _containers.MessageMap[str, ReviseHelp]
    language: str
    tokens_count: int
    def __init__(self, origin: _Optional[str] = ..., revised: _Optional[str] = ..., revised_blocks: _Optional[_Iterable[_Union[RevisedBlock, _Mapping]]] = ..., whitespace_cleanup_ranges: _Optional[_Iterable[_Union[CleanUpRange, _Mapping]]] = ..., revised_sentences: _Optional[_Iterable[_Union[RevisedSentence, _Mapping]]] = ..., helps: _Optional[_Mapping[str, ReviseHelp]] = ..., language: _Optional[str] = ..., tokens_count: _Optional[int] = ...) -> None: ...

class StreamCorrectErrorRequest(_message.Message):
    __slots__ = ("document", "encoding_type", "custom_domain", "custom_dict_names", "config", "req_id")
    DOCUMENT_FIELD_NUMBER: _ClassVar[int]
    ENCODING_TYPE_FIELD_NUMBER: _ClassVar[int]
    CUSTOM_DOMAIN_FIELD_NUMBER: _ClassVar[int]
    CUSTOM_DICT_NAMES_FIELD_NUMBER: _ClassVar[int]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    REQ_ID_FIELD_NUMBER: _ClassVar[int]
    document: _lang_common_pb2.Document
    encoding_type: _lang_common_pb2.EncodingType
    custom_domain: str
    custom_dict_names: _containers.RepeatedScalarFieldContainer[str]
    config: RevisionConfig
    req_id: int
    def __init__(self, document: _Optional[_Union[_lang_common_pb2.Document, _Mapping]] = ..., encoding_type: _Optional[_Union[_lang_common_pb2.EncodingType, str]] = ..., custom_domain: _Optional[str] = ..., custom_dict_names: _Optional[_Iterable[str]] = ..., config: _Optional[_Union[RevisionConfig, _Mapping]] = ..., req_id: _Optional[int] = ...) -> None: ...

class StreamFirstCorrectError(_message.Message):
    __slots__ = ("origin", "revised", "revised_blocks", "whitespace_cleanup_ranges", "revised_sentences", "helps", "language", "tokens_count", "req_id", "thinking_ids")
    class HelpsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: ReviseHelp
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[ReviseHelp, _Mapping]] = ...) -> None: ...
    ORIGIN_FIELD_NUMBER: _ClassVar[int]
    REVISED_FIELD_NUMBER: _ClassVar[int]
    REVISED_BLOCKS_FIELD_NUMBER: _ClassVar[int]
    WHITESPACE_CLEANUP_RANGES_FIELD_NUMBER: _ClassVar[int]
    REVISED_SENTENCES_FIELD_NUMBER: _ClassVar[int]
    HELPS_FIELD_NUMBER: _ClassVar[int]
    LANGUAGE_FIELD_NUMBER: _ClassVar[int]
    TOKENS_COUNT_FIELD_NUMBER: _ClassVar[int]
    REQ_ID_FIELD_NUMBER: _ClassVar[int]
    THINKING_IDS_FIELD_NUMBER: _ClassVar[int]
    origin: str
    revised: str
    revised_blocks: _containers.RepeatedCompositeFieldContainer[RevisedBlock]
    whitespace_cleanup_ranges: _containers.RepeatedCompositeFieldContainer[CleanUpRange]
    revised_sentences: _containers.RepeatedCompositeFieldContainer[RevisedSentence]
    helps: _containers.MessageMap[str, ReviseHelp]
    language: str
    tokens_count: int
    req_id: int
    thinking_ids: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, origin: _Optional[str] = ..., revised: _Optional[str] = ..., revised_blocks: _Optional[_Iterable[_Union[RevisedBlock, _Mapping]]] = ..., whitespace_cleanup_ranges: _Optional[_Iterable[_Union[CleanUpRange, _Mapping]]] = ..., revised_sentences: _Optional[_Iterable[_Union[RevisedSentence, _Mapping]]] = ..., helps: _Optional[_Mapping[str, ReviseHelp]] = ..., language: _Optional[str] = ..., tokens_count: _Optional[int] = ..., req_id: _Optional[int] = ..., thinking_ids: _Optional[_Iterable[int]] = ...) -> None: ...

class CancelledRevision(_message.Message):
    __slots__ = ("req_id", "thinking_id")
    REQ_ID_FIELD_NUMBER: _ClassVar[int]
    THINKING_ID_FIELD_NUMBER: _ClassVar[int]
    req_id: int
    thinking_id: int
    def __init__(self, req_id: _Optional[int] = ..., thinking_id: _Optional[int] = ...) -> None: ...

class PostRevision(_message.Message):
    __slots__ = ("req_id", "thinking_id", "revision", "help")
    REQ_ID_FIELD_NUMBER: _ClassVar[int]
    THINKING_ID_FIELD_NUMBER: _ClassVar[int]
    REVISION_FIELD_NUMBER: _ClassVar[int]
    HELP_FIELD_NUMBER: _ClassVar[int]
    req_id: int
    thinking_id: int
    revision: Revision
    help: ReviseHelp
    def __init__(self, req_id: _Optional[int] = ..., thinking_id: _Optional[int] = ..., revision: _Optional[_Union[Revision, _Mapping]] = ..., help: _Optional[_Union[ReviseHelp, _Mapping]] = ...) -> None: ...

class ProgressRevision(_message.Message):
    __slots__ = ("req_id", "thinking_id", "thinking_msg")
    REQ_ID_FIELD_NUMBER: _ClassVar[int]
    THINKING_ID_FIELD_NUMBER: _ClassVar[int]
    THINKING_MSG_FIELD_NUMBER: _ClassVar[int]
    req_id: int
    thinking_id: int
    thinking_msg: str
    def __init__(self, req_id: _Optional[int] = ..., thinking_id: _Optional[int] = ..., thinking_msg: _Optional[str] = ...) -> None: ...

class StreamCorrectErrorResponse(_message.Message):
    __slots__ = ("first", "cancelled", "post", "progress")
    FIRST_FIELD_NUMBER: _ClassVar[int]
    CANCELLED_FIELD_NUMBER: _ClassVar[int]
    POST_FIELD_NUMBER: _ClassVar[int]
    PROGRESS_FIELD_NUMBER: _ClassVar[int]
    first: StreamFirstCorrectError
    cancelled: CancelledRevision
    post: PostRevision
    progress: ProgressRevision
    def __init__(self, first: _Optional[_Union[StreamFirstCorrectError, _Mapping]] = ..., cancelled: _Optional[_Union[CancelledRevision, _Mapping]] = ..., post: _Optional[_Union[PostRevision, _Mapping]] = ..., progress: _Optional[_Union[ProgressRevision, _Mapping]] = ...) -> None: ...
