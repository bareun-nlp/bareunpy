from bareun import dict_common_pb2 as _dict_common_pb2
from google.protobuf import empty_pb2 as _empty_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class CustomDictionaryMeta(_message.Message):
    __slots__ = ("domain_name", "np_set", "cp_set", "cp_caret_set", "vv_set", "va_set")
    class DictMeta(_message.Message):
        __slots__ = ("type", "name", "items_count")
        TYPE_FIELD_NUMBER: _ClassVar[int]
        NAME_FIELD_NUMBER: _ClassVar[int]
        ITEMS_COUNT_FIELD_NUMBER: _ClassVar[int]
        type: _dict_common_pb2.DictType
        name: str
        items_count: int
        def __init__(self, type: _Optional[_Union[_dict_common_pb2.DictType, str]] = ..., name: _Optional[str] = ..., items_count: _Optional[int] = ...) -> None: ...
    DOMAIN_NAME_FIELD_NUMBER: _ClassVar[int]
    NP_SET_FIELD_NUMBER: _ClassVar[int]
    CP_SET_FIELD_NUMBER: _ClassVar[int]
    CP_CARET_SET_FIELD_NUMBER: _ClassVar[int]
    VV_SET_FIELD_NUMBER: _ClassVar[int]
    VA_SET_FIELD_NUMBER: _ClassVar[int]
    domain_name: str
    np_set: CustomDictionaryMeta.DictMeta
    cp_set: CustomDictionaryMeta.DictMeta
    cp_caret_set: CustomDictionaryMeta.DictMeta
    vv_set: CustomDictionaryMeta.DictMeta
    va_set: CustomDictionaryMeta.DictMeta
    def __init__(self, domain_name: _Optional[str] = ..., np_set: _Optional[_Union[CustomDictionaryMeta.DictMeta, _Mapping]] = ..., cp_set: _Optional[_Union[CustomDictionaryMeta.DictMeta, _Mapping]] = ..., cp_caret_set: _Optional[_Union[CustomDictionaryMeta.DictMeta, _Mapping]] = ..., vv_set: _Optional[_Union[CustomDictionaryMeta.DictMeta, _Mapping]] = ..., va_set: _Optional[_Union[CustomDictionaryMeta.DictMeta, _Mapping]] = ...) -> None: ...

class CustomDictionary(_message.Message):
    __slots__ = ("domain_name", "np_set", "cp_set", "cp_caret_set", "vv_set", "va_set", "mm_set", "mag_set", "ic_set")
    DOMAIN_NAME_FIELD_NUMBER: _ClassVar[int]
    NP_SET_FIELD_NUMBER: _ClassVar[int]
    CP_SET_FIELD_NUMBER: _ClassVar[int]
    CP_CARET_SET_FIELD_NUMBER: _ClassVar[int]
    VV_SET_FIELD_NUMBER: _ClassVar[int]
    VA_SET_FIELD_NUMBER: _ClassVar[int]
    MM_SET_FIELD_NUMBER: _ClassVar[int]
    MAG_SET_FIELD_NUMBER: _ClassVar[int]
    IC_SET_FIELD_NUMBER: _ClassVar[int]
    domain_name: str
    np_set: _dict_common_pb2.DictSet
    cp_set: _dict_common_pb2.DictSet
    cp_caret_set: _dict_common_pb2.DictSet
    vv_set: _dict_common_pb2.DictSet
    va_set: _dict_common_pb2.DictSet
    mm_set: _dict_common_pb2.DictSet
    mag_set: _dict_common_pb2.DictSet
    ic_set: _dict_common_pb2.DictSet
    def __init__(self, domain_name: _Optional[str] = ..., np_set: _Optional[_Union[_dict_common_pb2.DictSet, _Mapping]] = ..., cp_set: _Optional[_Union[_dict_common_pb2.DictSet, _Mapping]] = ..., cp_caret_set: _Optional[_Union[_dict_common_pb2.DictSet, _Mapping]] = ..., vv_set: _Optional[_Union[_dict_common_pb2.DictSet, _Mapping]] = ..., va_set: _Optional[_Union[_dict_common_pb2.DictSet, _Mapping]] = ..., mm_set: _Optional[_Union[_dict_common_pb2.DictSet, _Mapping]] = ..., mag_set: _Optional[_Union[_dict_common_pb2.DictSet, _Mapping]] = ..., ic_set: _Optional[_Union[_dict_common_pb2.DictSet, _Mapping]] = ...) -> None: ...

class CustomDictionaryMap(_message.Message):
    __slots__ = ("custom_dict_map",)
    class CustomDictMapEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: CustomDictionary
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[CustomDictionary, _Mapping]] = ...) -> None: ...
    CUSTOM_DICT_MAP_FIELD_NUMBER: _ClassVar[int]
    custom_dict_map: _containers.MessageMap[str, CustomDictionary]
    def __init__(self, custom_dict_map: _Optional[_Mapping[str, CustomDictionary]] = ...) -> None: ...

class GetCustomDictionaryListResponse(_message.Message):
    __slots__ = ("domain_dicts",)
    DOMAIN_DICTS_FIELD_NUMBER: _ClassVar[int]
    domain_dicts: _containers.RepeatedCompositeFieldContainer[CustomDictionaryMeta]
    def __init__(self, domain_dicts: _Optional[_Iterable[_Union[CustomDictionaryMeta, _Mapping]]] = ...) -> None: ...

class GetCustomDictionaryRequest(_message.Message):
    __slots__ = ("domain_name",)
    DOMAIN_NAME_FIELD_NUMBER: _ClassVar[int]
    domain_name: str
    def __init__(self, domain_name: _Optional[str] = ...) -> None: ...

class GetCustomDictionaryResponse(_message.Message):
    __slots__ = ("domain_name", "dict")
    DOMAIN_NAME_FIELD_NUMBER: _ClassVar[int]
    DICT_FIELD_NUMBER: _ClassVar[int]
    domain_name: str
    dict: CustomDictionary
    def __init__(self, domain_name: _Optional[str] = ..., dict: _Optional[_Union[CustomDictionary, _Mapping]] = ...) -> None: ...

class UpdateCustomDictionaryRequest(_message.Message):
    __slots__ = ("domain_name", "dict")
    DOMAIN_NAME_FIELD_NUMBER: _ClassVar[int]
    DICT_FIELD_NUMBER: _ClassVar[int]
    domain_name: str
    dict: CustomDictionary
    def __init__(self, domain_name: _Optional[str] = ..., dict: _Optional[_Union[CustomDictionary, _Mapping]] = ...) -> None: ...

class UpdateCustomDictionaryResponse(_message.Message):
    __slots__ = ("updated_domain_name",)
    UPDATED_DOMAIN_NAME_FIELD_NUMBER: _ClassVar[int]
    updated_domain_name: str
    def __init__(self, updated_domain_name: _Optional[str] = ...) -> None: ...

class RemoveCustomDictionariesRequest(_message.Message):
    __slots__ = ("domain_names", "all")
    DOMAIN_NAMES_FIELD_NUMBER: _ClassVar[int]
    ALL_FIELD_NUMBER: _ClassVar[int]
    domain_names: _containers.RepeatedScalarFieldContainer[str]
    all: bool
    def __init__(self, domain_names: _Optional[_Iterable[str]] = ..., all: _Optional[bool] = ...) -> None: ...

class RemoveCustomDictionariesResponse(_message.Message):
    __slots__ = ("deleted_domain_names",)
    class DeletedDomainNamesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: bool
        def __init__(self, key: _Optional[str] = ..., value: _Optional[bool] = ...) -> None: ...
    DELETED_DOMAIN_NAMES_FIELD_NUMBER: _ClassVar[int]
    deleted_domain_names: _containers.ScalarMap[str, bool]
    def __init__(self, deleted_domain_names: _Optional[_Mapping[str, bool]] = ...) -> None: ...

class CheckConflictRequest(_message.Message):
    __slots__ = ("domain_names",)
    DOMAIN_NAMES_FIELD_NUMBER: _ClassVar[int]
    domain_names: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, domain_names: _Optional[_Iterable[str]] = ...) -> None: ...

class CheckConflictResponse(_message.Message):
    __slots__ = ("conflicts",)
    CONFLICTS_FIELD_NUMBER: _ClassVar[int]
    conflicts: _containers.RepeatedCompositeFieldContainer[Conflict]
    def __init__(self, conflicts: _Optional[_Iterable[_Union[Conflict, _Mapping]]] = ...) -> None: ...

class DictOne(_message.Message):
    __slots__ = ("dict_name", "dict_set_name")
    DICT_NAME_FIELD_NUMBER: _ClassVar[int]
    DICT_SET_NAME_FIELD_NUMBER: _ClassVar[int]
    dict_name: str
    dict_set_name: str
    def __init__(self, dict_name: _Optional[str] = ..., dict_set_name: _Optional[str] = ...) -> None: ...

class Conflict(_message.Message):
    __slots__ = ("left", "right", "left_word", "right_word", "conflict", "duplicated", "conflict_msg")
    LEFT_FIELD_NUMBER: _ClassVar[int]
    RIGHT_FIELD_NUMBER: _ClassVar[int]
    LEFT_WORD_FIELD_NUMBER: _ClassVar[int]
    RIGHT_WORD_FIELD_NUMBER: _ClassVar[int]
    CONFLICT_FIELD_NUMBER: _ClassVar[int]
    DUPLICATED_FIELD_NUMBER: _ClassVar[int]
    CONFLICT_MSG_FIELD_NUMBER: _ClassVar[int]
    left: DictOne
    right: DictOne
    left_word: str
    right_word: str
    conflict: bool
    duplicated: bool
    conflict_msg: str
    def __init__(self, left: _Optional[_Union[DictOne, _Mapping]] = ..., right: _Optional[_Union[DictOne, _Mapping]] = ..., left_word: _Optional[str] = ..., right_word: _Optional[str] = ..., conflict: _Optional[bool] = ..., duplicated: _Optional[bool] = ..., conflict_msg: _Optional[str] = ...) -> None: ...
