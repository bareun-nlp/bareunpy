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
        
        # 단일 문장 교정
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

        # 여러 문장 교정
        >>> responses = corrector.correct_error_list([
        ...     "어머니께서 만들어주신김치찌게가너무맵다며동생이울어버렸다.",
        ...     "영수 도 줄기가 얇어서 시들을 것 같은 꽃에물을 주었더니 고은 꽃이 피었다."
        ... ])
        >>> for res in responses:
        ...     print(res.revised)

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

        self.channel = grpc.insecure_channel(
            f"{self.host}:{self.port}",
            options=[
                ('grpc.max_send_message_length', MAX_MESSAGE_LENGTH),
                ('grpc.max_receive_message_length', MAX_MESSAGE_LENGTH),
            ]
        )
        self.client = BareunRevisionServiceClient(self.channel, apikey, self.host, self.port)

    def correct_error(self, content: str, auto_split: bool = True, custom_domain: str = "") -> pb.CorrectErrorResponse:
        """
        맞춤법 교정 요청

        Args:
            content (str): 교정을 요청할 문장
            auto_split (bool): 문장 자동 분리 여부
            custom_domain (str): 커스텀 도메인 정보

        Returns:
            pb.CorrectErrorResponse: 교정 결과
        """
        request = pb.CorrectErrorRequest(
            document=lpb.Document(content=content, language="ko_KR"),
            encoding_type=lpb.EncodingType.UTF32,
            auto_split_sentence=auto_split
        )
        if custom_domain:
            request.custom_domain = custom_domain

        return self.client.correct_error(request)

    def correct_error_list(self, contents: List[str], auto_split: bool = False, custom_domain: str = "") -> List[pb.CorrectErrorResponse]:
        """
        여러 문장에 대한 맞춤법 교정 요청

        Args:
            contents (List[str]): 교정을 요청할 문장 리스트
            auto_split (bool): 문장 자동 분리 여부
            custom_domain (str): 커스텀 도메인 정보

        Returns:
            List[pb.CorrectErrorResponse]: 각 문장에 대한 pb.CorrectErrorResponse 객체의 리스트
        """
        results = []
        for content in contents:
            request = pb.CorrectErrorRequest(
                document=lpb.Document(content=content, language="ko_KR"),
                encoding_type=lpb.EncodingType.UTF32,
                auto_split_sentence=auto_split
            )
            if custom_domain:
                request.custom_domain = custom_domain
            
            response = self.client.correct_error(request)
            results.append(response)
        return results

    def print_results(self, response: Union[pb.CorrectErrorResponse, List[pb.CorrectErrorResponse]], out: IO = stdout) -> None:
        """
        교정 결과를 출력

        Args:
            response (Union[pb.CorrectErrorResponse, List[pb.CorrectErrorResponse]]): 교정 결과 또는 교정 결과의 리스트
            out (IO): 출력 대상 (기본값: stdout)
        """
        # 단일 객체를 리스트로 변환하여 처리
        if not isinstance(response, list):
            response = [response]

        for result_index, single_response in enumerate(response, start=1):
            print(f"=== 맞춤법 검사 결과 {result_index}===", file=out)
            print(f"원문: {single_response.origin}", file=out)
            print(f"교정문: {single_response.revised}", file=out)

            if single_response.revised_sentences:
                print("\n=== 교정된 문장들 ===", file=out)
                for sentence in single_response.revised_sentences:
                    print(f"[{result_index}] 원문: {sentence.origin}", file=out)
                    print(f"    교정문: {sentence.revised}", file=out)
                    if sentence.revised_blocks:
                        print("    === 수정 블록 ===", file=out)
                        for block_index, block in enumerate(sentence.revised_blocks, start=1):
                            print(f"    {result_index}-{block_index} 원문: {block.origin.content}", file=out)
                            print(f"        교정문: {block.revised}", file=out)
                            if block.revisions:
                                print("        수정 세부사항:", file=out)
                                for rev in block.revisions:
                                    print(f"          - {rev.comment} ({rev.category})", file=out)

    def as_json(self, response: Union[pb.CorrectErrorResponse, List[pb.CorrectErrorResponse]]) -> Union[dict, List[dict]]:
        """
        교정 결과를 JSON 형식으로 변환

        Args:
            response (Union[pb.CorrectErrorResponse, List[pb.CorrectErrorResponse]]): 교정 결과 또는 교정 결과의 리스트

        Returns:
            Union[dict, List[dict]]: JSON 형식으로 변환된 결과
        """
        if isinstance(response, list):
            return [MessageToDict(resp, including_default_value_fields=True, use_integers_for_enums=False) for resp in response]
        else:
            return MessageToDict(response, including_default_value_fields=True, use_integers_for_enums=False)

    def as_json_str(self, response: Union[pb.CorrectErrorResponse, List[pb.CorrectErrorResponse]]) -> str:
        """
        교정 결과를 JSON 문자열로 변환

        Args:
            response (Union[pb.CorrectErrorResponse, List[pb.CorrectErrorResponse]]): 교정 결과 또는 교정 결과의 리스트

        Returns:
            str: JSON 문자열로 변환된 결과
        """
        json_data = self.as_json(response)
        return json.dumps(json_data, ensure_ascii=False, indent=2)

    def print_as_json(self, response: Union[pb.CorrectErrorResponse, List[pb.CorrectErrorResponse]], out: IO = stdout) -> None:
        """
        교정 결과를 JSON 형식으로 출력

        Args:
            response (Union[pb.CorrectErrorResponse, List[pb.CorrectErrorResponse]]): 교정 결과 또는 교정 결과의 리스트
            out (IO): 출력 대상 (기본값: stdout)
        """
        json_data = self.as_json(response)
        json.dump(json_data, out, ensure_ascii=False, indent=2)
