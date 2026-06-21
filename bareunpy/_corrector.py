# -*- coding: utf-8 -*-
import json
from sys import stdout
from typing import IO, Iterator, List, Union
from google.protobuf.json_format import MessageToDict

import bareun.revision_service_pb2 as pb
import bareun.lang_common_pb2 as lpb
from ._revision_service_client import BareunRevisionServiceClient
from bareunpy._tagger import _resolve_port

MAX_MESSAGE_LENGTH = 100 * 1024 * 1024


class Corrector:
    """
    Corrector는 맞춤법 교정 서비스를 제공하는 클래스입니다.

    .. code-block:: python
        :emphasize-lines: 1
        >>> from bareunpy import Corrector
        >>> corrector = Corrector(apikey="koba-YOURKEY")

        >>> response = corrector.correct_error("영수 도 줄기가 얇어서 시들을 것 같은 꽃에물을 주었더니 고은 꽃이 피었다.")
        >>> corrector.print_results(response)
            === 맞춤법 검사 결과 1===
            원문: 영수 도 줄기가 얇어서 시들을 것 같은 꽃에물을 주었더니 고은 꽃이 피었다.
            교정문: 영수도 줄기가 얇아서 시들 것 같은 꽃에 물을 주었더니 고운 꽃이 피었다.

            === 교정된 문장들 ===
            [1] 원문: 영수 도 줄기가 얇어서 시들을 것 같은 꽃에물을 주었더니 고은 꽃이 피었다.
                교정문: 영수도 줄기가 얇아서 시들 것 같은 꽃에 물을 주었더니 고운 꽃이 피었다.
                === 수정 블록 ===
                1-1 원문: 영수 도
                    교정문: 영수도
                    수정 세부사항:
                    - 조사는 그 앞말에 붙여 쓴다. (일반)
                1-2 ...

        >>> # 실시간(스트리밍) 교정
        >>> for res in corrector.correct_error_stream("고은 꽃이 피었다."):
        ...     # res 는 oneof(first/cancelled/post/progress) 응답
        ...     print(res.WhichOneof("res"))


    :param apikey: str. Bareun API 키
    :param host: str. 서버 호스트, 로컬에 바른 서버 설치시 'localhost' 입력 (기본값: api.bareun.ai)
    :param port: int. 서버 포트 (기본값: api.bareun.ai 는 443, 그 외는 5656)
    """

    def __init__(self, apikey: str, host: str = "", port: int = None):
        """
        Corrector 초기화

        Args:
            apikey (str): API 키
            host (str): 서버 호스트
            port (int): 서버 포트
        """
        if host:
            host = host.strip()
        if apikey:
            apikey = apikey.strip()
        if host == "" or host is None:
            self.host = 'api.bareun.ai'
        else:
            self.host = host

        self.port = _resolve_port(self.host, port)

        if apikey is None or len(apikey) == 0:
            raise ValueError("an apikey must be provided!")
        self.apikey = apikey

        self.client = BareunRevisionServiceClient(apikey, self.host, self.port)

    def correct_error(self, content: str,
                      custom_dicts: List[str] = [],
                      config: Union[pb.RevisionConfig, None] = None) -> pb.CorrectErrorResponse:
        """
        맞춤법 교정 요청 (단발 호출)

        Args:
            content (str): 교정을 요청할 문장
            custom_dicts (List[str]): 사용자 사전의 이름 목록
            config Union[pb.RevisionConfig, None] : 요청 설정

        Returns:
            pb.CorrectErrorResponse: 교정 결과
        """
        request = pb.CorrectErrorRequest(
            document=lpb.Document(content=content, language="ko_KR"),
            encoding_type=lpb.EncodingType.UTF32,
        )
        if len(custom_dicts):
            request.custom_dict_names.extend(custom_dicts)
        if config is not None:
            request.config.CopyFrom(config)

        return self.client.correct_error(request)

    def correct_error_stream(self, content: str,
                             custom_dicts: List[str] = [],
                             config: Union[pb.RevisionConfig, None] = None,
                             req_id: int = 0) -> Iterator[pb.StreamCorrectErrorResponse]:
        """
        맞춤법 교정을 실시간(server-streaming)으로 요청합니다.

        하나의 문장(문서)을 보내면, 서버가 교정 결과를 여러 응답으로 나눠 스트리밍합니다.
        반환된 이터레이터를 순회하면서 각 응답을 처리하면 됩니다. 각 응답은
        ``res`` oneof 로 다음 중 하나를 담습니다.

        - ``first``     : 첫 번째 기본 교정 결과(:class:`pb.StreamFirstCorrectError`)
        - ``progress``  : AI 가 추가로 검토 중인 항목의 진행 상태
        - ``post``      : 추가 검토가 끝나 확정된 교정 결과
        - ``cancelled`` : 이전에 제안했던 교정이 취소됨

        Args:
            content (str): 교정을 요청할 문장
            custom_dicts (List[str]): 사용자 사전의 이름 목록
            config (Union[pb.RevisionConfig, None]): 요청 설정
            req_id (int): 요청 식별자. 0(기본값)이면 서버가 생성합니다.

        Yields:
            pb.StreamCorrectErrorResponse: 스트리밍 교정 응답
        """
        request = pb.StreamCorrectErrorRequest(
            document=lpb.Document(content=content, language="ko_KR"),
            encoding_type=lpb.EncodingType.UTF32,
        )
        # req_id 가 0 이면 보내지 않아도 서버가 생성한다(proto 주석 참고).
        if req_id:
            request.req_id = req_id
        if len(custom_dicts):
            request.custom_dict_names.extend(custom_dicts)
        if config is not None:
            request.config.CopyFrom(config)

        return self.client.stream_correct_error(request)

    def close(self) -> None:
        """내부 세션을 닫습니다(선택)."""
        self.client.close()

    def print_results(self, res: pb.CorrectErrorResponse, out: IO = stdout) -> None:
        """
        교정 결과를 출력

        Args:
            res (pb.CorrectErrorResponse): 교정 결과
            out (IO): 출력 대상 (기본값: stdout)
        """
        print(f'원문: {res.origin}', file=out)
        print(f'교정: {res.revised}', file=out)

        print("\n=== 교정된 문장들 ===", file=out)

        for sent in res.revised_sentences:
            print(f" 원문: {sent.origin}", file=out)
            print(f"교정문: {sent.revised}", file=out)

        for block in res.revised_blocks:
            print(f'원문:{block.origin.content} offset:{block.origin.begin_offset}, length:{block.origin.length}', file=out)
            print(f'대표 교정: {block.revised}', file=out)
            for rev in block.revisions:
                print(f' 교정: {rev.revised}, 카테고리:{rev.category}, 도움말 {res.helps[rev.help_id].comment}', file=out)

        for cleanup in res.whitespace_cleanup_ranges:
            print(f'공백제거: offset:{cleanup.offset} length:{cleanup.length} position: {cleanup.position}', file=out)

    def as_json(self, response: pb.CorrectErrorResponse) -> dict:
        """
        교정 결과를 JSON(dict) 형식으로 변환

        Args:
            response (pb.CorrectErrorResponse): 교정 결과

        Returns:
            dict: JSON 형식으로 변환된 결과
        """
        return MessageToDict(response, True)

    def as_json_str(self, response: pb.CorrectErrorResponse) -> str:
        """
        교정 결과를 JSON 문자열로 변환

        Args:
            response (pb.CorrectErrorResponse): 교정 결과

        Returns:
            str: JSON 문자열로 변환된 결과
        """
        json_data = self.as_json(response)
        return json.dumps(json_data, ensure_ascii=False, indent=2)

    def print_as_json(self, response: pb.CorrectErrorResponse, out: IO = stdout) -> None:
        """
        교정 결과를 JSON 형식으로 출력

        Args:
            response (pb.CorrectErrorResponse): 교정 결과
            out (IO): 출력 대상 (기본값: stdout)
        """
        json_data = self.as_json(response)
        json.dump(json_data, out, ensure_ascii=False, indent=2)
