# -*- coding: utf-8 -*-
"""긴 문서를 여러 번에 나눠 교정할 때 쓰는 교정 세션.

세션을 열면 서버가 같은 문서임을 알고 동작합니다. 앞 호출에서 두 번 이상 나온 미등록 단어는
알려진 말로 확정해 뒤 호출에서 고치지 않습니다. 사용자 사전과 교정 설정은 세션을 열 때 한 번
정하고 닫을 때까지 바뀌지 않습니다. 세션은 서버에 영구 저장되지 않고, 마지막 호출 뒤 10분이
지나거나 열린 지 1시간이 지나면 서버가 닫습니다.
"""

from typing import Iterator, List, Optional

import bareunpy.bareun.revision_service_pb2 as pb
import bareunpy.bareun.lang_common_pb2 as lpb
from ._revision_service_client import BareunRevisionServiceClient


class RevisionSession:
    """열려 있는 교정 세션 하나.

    :meth:`Corrector.open_session` 으로 만듭니다. ``with`` 문으로 쓰면 블록이 끝날 때 닫습니다.

    .. code-block:: python
        >>> with corrector.open_session() as session:
        ...     first = session.correct_error(part1)
        ...     second = session.correct_error(part2)

    Attributes:
        session_id (str): 서버가 정한 세션 ID(UUID).
        session_revision (int): 세션을 열 때의 개정 번호(처음은 0). 최신 값은 :meth:`events` 로 본다.
        idle_timeout_seconds (int): 마지막 호출 뒤 이 시간이 지나면 닫힌다.
        max_lifetime_seconds (int): 열린 지 이 시간이 지나면 호출 중이어도 닫힌다.
    """

    def __init__(self, client: BareunRevisionServiceClient, opened: pb.OpenSessionResponse):
        self._client = client
        self.session_id = opened.session_id
        self.session_revision = opened.session_revision
        self.idle_timeout_seconds = opened.idle_timeout_seconds
        self.max_lifetime_seconds = opened.max_lifetime_seconds

    def correct_error(self, content: str) -> pb.CorrectErrorResponse:
        """세션 안에서 맞춤법을 교정합니다(단발 호출).

        사용자 사전과 설정은 세션을 열 때 정한 값을 씁니다. 글이 서버 기준보다 길면 앞부분만
        교정되니, 응답의 :meth:`Corrector.truncation` 으로 확인하고 ``dropped_text`` 로 이어 보냅니다.

        Args:
            content (str): 교정을 요청할 글

        Returns:
            pb.CorrectErrorResponse: 교정 결과
        """
        request = pb.CorrectErrorRequest(
            document=lpb.Document(content=content, language="ko_KR"),
            encoding_type=lpb.EncodingType.UTF32,
            session_id=self.session_id,
        )
        return self._client.correct_error(request)

    def correct_error_stream(self, content: str, req_id: int = 0) -> Iterator[pb.StreamCorrectErrorResponse]:
        """세션 안에서 맞춤법을 실시간(server-streaming)으로 교정합니다.

        같은 호출 안에서 먼저 나온 미등록 단어는 아직 몰랐을 때의 규칙이 이미 고쳤을 수 있어,
        서버가 첫 응답 뒤에 ``session_correction`` 응답으로 되돌릴 구간을 알려 줍니다.

        Args:
            content (str): 교정을 요청할 글
            req_id (int): 요청 식별자. 0(기본값)이면 서버가 생성합니다.

        Yields:
            pb.StreamCorrectErrorResponse: first / progress / post / cancelled / session_correction 중 하나
        """
        request = pb.StreamCorrectErrorRequest(
            document=lpb.Document(content=content, language="ko_KR"),
            encoding_type=lpb.EncodingType.UTF32,
            session_id=self.session_id,
        )
        if req_id:
            request.req_id = req_id
        return self._client.stream_correct_error(request)

    def events(self, since_revision: int = 0) -> pb.GetSessionEventsResponse:
        """세션의 변경 사건을 가져옵니다.

        단발 호출로 앞 응답을 받은 뒤, 뒤 호출 때문에 세션이 바뀌었는지(미등록 단어가 확정됐는지)
        알아볼 때 씁니다. ``session_revision`` 이 응답의 값보다 올랐으면 앞 호출의 답이 달라졌을 수 있습니다.

        Args:
            since_revision (int): 이 번호보다 큰 개정의 사건만 받는다. 0 이면 처음부터.

        Returns:
            pb.GetSessionEventsResponse: 지금의 세션 개정 번호와 사건 목록(개정 번호 순)
        """
        return self._client.get_session_events(
            pb.GetSessionEventsRequest(session_id=self.session_id, since_revision=since_revision))

    def close(self) -> pb.CloseSessionResponse:
        """세션을 닫고 서버가 쥔 상태를 정리합니다. 닫으면 동시 세션 수 상한을 바로 돌려받습니다.

        호출하지 않아도 서버가 알아서 닫습니다. 이미 닫혔거나 만료된 세션이면 서버 오류가 납니다.
        """
        return self._client.close_session(pb.CloseSessionRequest(session_id=self.session_id))

    def __enter__(self) -> "RevisionSession":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
