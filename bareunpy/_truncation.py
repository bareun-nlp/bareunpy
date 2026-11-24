# -*- coding: utf-8 -*-
"""긴 요청이 잘렸을 때(truncation)의 응답 정보를 읽는 도구.

서버는 요청 글이 기준(운영 서버는 9,000자)을 넘으면 거절하지 않고 앞부분(기본 5,000자 안팎)만
처리한 뒤, 응답의 ``truncation`` 필드로 버린 부분을 알립니다. 잘리지 않은 응답에는 이 필드가
없고, 이 정보를 모르는 옛 버전의 클라이언트도 그대로 동작합니다.

이 모듈은 그 필드를 :class:`TruncationInfo` 로 바꿔 줍니다. ``Tagged``·``Tokenized`` 와
``Corrector`` 가 같은 도구를 씁니다.
"""

from typing import Any, List, NamedTuple, Optional, Union


class TruncationInfo(NamedTuple):
    """긴 요청이 앞부분만 처리됐을 때의 정보.

    글자 수는 유니코드 코드 포인트(한글 한 글자, 영문 한 자, 공백, 줄바꿈이 각각 한 글자)로 셉니다.
    bareunpy 는 요청을 항상 UTF32 로 보내므로 ``dropped_begin_offset`` 도 파이썬 문자열의 글자
    위치와 같습니다(``content[dropped_begin_offset:]`` 가 버린 부분).

    Attributes:
        original_chars (int): 요청 글 전체의 글자 수.
        processed_chars (int): 처리한 글자 수(앞부분).
        dropped_chars (int): 처리하지 않고 버린 글자 수.
        dropped_begin_offset (int): 버린 구간이 시작하는 글자 위치. 문장 목록(``taglist``)
            요청이면 ``dropped_begin_sentence_index`` 번째 문장 안의 위치다.
        message (str): 서버가 준 안내 문구(한국어, 괄호 안에 영어).
        cut_mid_word (bool): 문장 끝이나 공백을 찾지 못해 글자 중간에서 잘랐으면 True.
            마지막 어절의 분석·교정은 믿기 어렵다.
        dropped_begin_sentence_index (Optional[int]): 문장 목록 요청(``taglist``)에서만 값이
            있다. 처리하지 않은 부분이 시작하는 문장의 번호(0부터). 그 뒤 문장은 모두 처리되지
            않았다. 다른 요청은 None.
    """

    original_chars: int
    processed_chars: int
    dropped_chars: int
    dropped_begin_offset: int
    message: str
    cut_mid_word: bool
    dropped_begin_sentence_index: Optional[int] = None

    def dropped_text(self, content: Union[str, List[str]]) -> str:
        """요청에 쓴 원문에서 처리되지 않은 부분을 돌려줍니다.

        긴 글을 나눠 다시 요청할 때 이어서 보낼 나머지입니다.

        Args:
            content: 요청에 쓴 원문. 문장 목록(``taglist``)이면 그 목록 그대로.

        Returns:
            처리되지 않은 뒷부분. 문장 목록이면 문장 사이를 줄바꿈으로 이어 붙인다.
        """
        if isinstance(content, str):
            return content[self.dropped_begin_offset:]
        index = self.dropped_begin_sentence_index or 0
        if index >= len(content):
            return ""
        head = content[index][self.dropped_begin_offset:]
        return "\n".join([head] + list(content[index + 1:]))


def truncation_of(msg: Any) -> Optional[TruncationInfo]:
    """응답 메시지에서 잘림 정보를 꺼냅니다. 잘리지 않았으면 None.

    ``truncation`` 은 proto3 ``optional`` 메시지 필드라, 잘리지 않은 응답에는 필드 자체가
    없습니다. 그래서 값 비교가 아니라 ``HasField`` 로 존재를 확인합니다.

    Args:
        msg: ``truncation`` 필드를 가진 응답(분석·토크나이즈·교정·스트림 첫 응답).
            필드가 없는 메시지(스트림의 진행·확정 응답 등)면 None.
    """
    descriptor = getattr(msg, "DESCRIPTOR", None)
    if descriptor is None or "truncation" not in descriptor.fields_by_name:
        return None
    if not msg.HasField("truncation"):
        return None
    t = msg.truncation
    index = None
    if "dropped_begin_sentence_index" in descriptor.fields_by_name \
            and msg.HasField("dropped_begin_sentence_index"):
        index = msg.dropped_begin_sentence_index
    return TruncationInfo(
        original_chars=t.original_chars,
        processed_chars=t.processed_chars,
        dropped_chars=t.dropped_chars,
        dropped_begin_offset=t.dropped_begin_offset,
        message=t.message,
        cut_mid_word=t.cut_mid_word,
        dropped_begin_sentence_index=index,
    )


class TruncationMixin:
    """응답 래퍼(``Tagged``·``Tokenized``)에 잘림 정보 조회를 더합니다.

    쓰는 쪽은 응답 메시지를 ``self.r``, 요청 원문을 ``self.phrase`` 로 가져야 한다.
    """

    r: Any
    phrase: Union[str, List[str]]

    def is_truncated(self) -> bool:
        """요청 글이 길어 앞부분만 처리됐으면 True."""
        return truncation_of(self.r) is not None

    def truncation(self) -> Optional[TruncationInfo]:
        """잘림 정보. 잘리지 않았으면 None.

        .. code-block:: python
            >>> tagged = tagger.tag(very_long_text)
            >>> t = tagged.truncation()
            >>> if t:
            ...     print(t.processed_chars, t.dropped_chars, t.message)
        """
        return truncation_of(self.r)

    def dropped_text(self) -> str:
        """처리되지 않은 뒷부분의 원문. 잘리지 않았으면 빈 문자열."""
        t = truncation_of(self.r)
        return "" if t is None else t.dropped_text(self.phrase)
