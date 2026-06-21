# -*- coding: utf-8 -*-
"""맞춤법 교정(RevisionService) Connect RPC 클라이언트.

``CorrectError``(단발 교정)와 ``StreamCorrectError``(server-streaming 실시간 교정)를
공식 Connect RPC 라이브러리(`connectrpc`)로 호출한다.
"""

from typing import Iterator

from connectrpc.errors import ConnectError

import bareunpy.bareun.revision_service_pb2 as pb
from bareunpy.bareun.revision_service_connect import RevisionServiceClientSync
from bareunpy._lang_service_client import (
    MAX_MESSAGE_LENGTH,
    build_base_address,
    build_metadata,
    BareunLanguageServiceClient,
)


class BareunRevisionServiceClient:
    """맞춤법 교정을 처리하는 클라이언트.

    api-key 는 매 호출마다 ``api-key`` 요청 헤더로 전달한다. 에러 변환 로직은
    :class:`BareunLanguageServiceClient` 와 동일하므로 그 메서드를 재사용한다.
    """

    def __init__(self, apikey: str, host: str, port: int):
        """RevisionServiceClient 초기화.

        Args:
            apikey (str): API 키
            host (str): bareun 서버 주소
            port (int): bareun 서버 포트
        """
        self.apikey = apikey
        self.host = host
        self.port = port
        self.metadata = build_metadata(apikey)
        self.stub = RevisionServiceClientSync(
            build_base_address(host, port),
            read_max_bytes=MAX_MESSAGE_LENGTH,
        )

    def close(self) -> None:
        """내부 HTTP 클라이언트를 닫습니다(선택). 닫은 뒤에는 호출할 수 없습니다."""
        self.stub.close()

    # 에러 변환 규칙은 LanguageService 와 완전히 동일하므로 중복 구현하지 않고 재사용한다.
    _handle_connect_error = BareunLanguageServiceClient._handle_connect_error

    def correct_error(self, request: pb.CorrectErrorRequest) -> pb.CorrectErrorResponse:
        """맞춤법 교정을 위한 단발(unary) Connect 호출.

        Args:
            request (pb.CorrectErrorRequest): 교정 요청 메시지

        Raises:
            Exception: 원격 호출시 예외가 발생할 수 있습니다.

        Returns:
            pb.CorrectErrorResponse: 교정 응답 메시지
        """
        try:
            return self.stub.correct_error(request, headers=self.metadata)
        except ConnectError as e:
            self._handle_connect_error(e)

    def stream_correct_error(
        self, request: pb.StreamCorrectErrorRequest
    ) -> Iterator[pb.StreamCorrectErrorResponse]:
        """맞춤법 교정을 server-streaming 방식으로 호출합니다.

        하나의 요청을 보내고, 서버가 교정 결과를 여러 개의 응답으로 나눠 보냅니다.
        반환된 이터레이터를 소비할 때 실제 네트워크 스트림이 진행되며, 스트림 도중
        발생한 오류는 사용자 친화적인 메시지로 변환되어 전파됩니다.

        Args:
            request (pb.StreamCorrectErrorRequest): 스트리밍 교정 요청 메시지

        Yields:
            pb.StreamCorrectErrorResponse: 스트리밍 교정 응답(oneof: first/cancelled/post/progress)

        Raises:
            Exception: 원격 호출시 예외가 발생할 수 있습니다.
        """
        try:
            for resp in self.stub.stream_correct_error(request, headers=self.metadata):
                yield resp
        except ConnectError as e:
            self._handle_connect_error(e)
