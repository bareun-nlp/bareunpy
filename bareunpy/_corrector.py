import grpc
import json
from sys import stdout
from typing import IO, List, Union
from google.protobuf.json_format import MessageToDict

import bareun.revision_service_pb2 as pb
import bareun.lang_common_pb2 as lpb
from ._revision_service_client import BareunRevisionServiceClient

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


    :param apikey: str. Bareun API 키
    :param host: str. gRPC 서버 호스트, 로컬에 바른 서버 설치시 'localhost' 입력 (기본값: nlp.bareun.ai)
    :param port: int. gRPC 서버 포트 (기본값: 5656)
    """

    def __init__(self, apikey: str, host: str = "", port: int = 5656):
        """
        Corrector 초기화

        Args:
            apikey (str): API 키
            host (str): gRPC 서버 호스트
            port (int): gRPC 서버 포트
        """
        if host:
            host = host.strip()
        if apikey:
            apikey = apikey.strip()
        if host == "" or host is None:
            self.host = 'nlp.bareun.ai'
        else:
            self.host = host 
        
        if port is not None:
            self.port = port
        else:
            self.port = 5656

        self.client = BareunRevisionServiceClient(apikey, self.host, self.port)

    def correct_error(self, content: str,
                      custom_dicts: List[str] = [],
                      config: Union[pb.RevisionConfig, None] = None) -> pb.CorrectErrorResponse:
        """
        맞춤법 교정 요청

        Args:
            content (str): 교정을 요청할 문장
            custom_dicts (List[str]): 커스텀 도메인 정보
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
        if config != None:
            request.config.CopyFrom(config)

        return self.client.correct_error(request)

    def print_results(self, res: pb.CorrectErrorResponse, out: IO = stdout) -> None:
        """
        교정 결과를 출력

        Args:
            response pb.CorrectErrorResponse: 교정 결과 또는 교정 결과의 리스트
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
                print(f' 교정: {rev.revised}, 카테고리:{rev.category}, 도움말 {res.helps[rev.help_id].comment}')
                
        for cleanup in res.whitespace_cleanup_ranges:
            print(f'공백제거: offset:{cleanup.offset} length:{cleanup.length} position: {cleanup.position}')
        

    def as_json(self, response: pb.CorrectErrorResponse) -> dict:
        """
        교정 결과를 JSON 형식으로 변환

        Args:
            response (Union[pb.CorrectErrorResponse, List[pb.CorrectErrorResponse]]): 교정 결과 또는 교정 결과의 리스트

        Returns:
            Union[dict, List[dict]]: JSON 형식으로 변환된 결과
        """
        return MessageToDict(response, True)

    def as_json_str(self, response: pb.CorrectErrorResponse) -> str:
        """
        교정 결과를 JSON 문자열로 변환

        Args:
            response (Union[pb.CorrectErrorResponse, List[pb.CorrectErrorResponse]]): 교정 결과 또는 교정 결과의 리스트

        Returns:
            str: JSON 문자열로 변환된 결과
        """
        json_data = self.as_json(response)
        return json.dumps(json_data, ensure_ascii=False, indent=2)

    def print_as_json(self, response: pb.CorrectErrorResponse, out: IO = stdout) -> None:
        """
        교정 결과를 JSON 형식으로 출력

        Args:
            response (Union[pb.CorrectErrorResponse, List[pb.CorrectErrorResponse]]): 교정 결과 또는 교정 결과의 리스트
            out (IO): 출력 대상 (기본값: stdout)
        """
        json_data = self.as_json(response)
        json.dump(json_data, out, ensure_ascii=False, indent=2)
