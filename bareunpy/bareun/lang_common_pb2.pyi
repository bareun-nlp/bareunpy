from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class EncodingType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    NONE: _ClassVar[EncodingType]
    UTF8: _ClassVar[EncodingType]
    UTF16: _ClassVar[EncodingType]
    UTF32: _ClassVar[EncodingType]
NONE: EncodingType
UTF8: EncodingType
UTF16: EncodingType
UTF32: EncodingType

class TextSpan(_message.Message):
    __slots__ = ("content", "begin_offset", "length")
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    BEGIN_OFFSET_FIELD_NUMBER: _ClassVar[int]
    LENGTH_FIELD_NUMBER: _ClassVar[int]
    content: str
    begin_offset: int
    length: int
    def __init__(self, content: _Optional[str] = ..., begin_offset: _Optional[int] = ..., length: _Optional[int] = ...) -> None: ...

class Document(_message.Message):
    __slots__ = ("content", "language")
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    LANGUAGE_FIELD_NUMBER: _ClassVar[int]
    content: str
    language: str
    def __init__(self, content: _Optional[str] = ..., language: _Optional[str] = ...) -> None: ...
