from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class DictType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    TOKEN_INDEX: _ClassVar[DictType]
    WORD_LIST: _ClassVar[DictType]
    WORD_LIST_COMPOUND: _ClassVar[DictType]
TOKEN_INDEX: DictType
WORD_LIST: DictType
WORD_LIST_COMPOUND: DictType

class DictSet(_message.Message):
    __slots__ = ("items", "type", "name")
    class ItemsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: int
        def __init__(self, key: _Optional[str] = ..., value: _Optional[int] = ...) -> None: ...
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    items: _containers.ScalarMap[str, int]
    type: DictType
    name: str
    def __init__(self, items: _Optional[_Mapping[str, int]] = ..., type: _Optional[_Union[DictType, str]] = ..., name: _Optional[str] = ...) -> None: ...
