import grpc
from typing import List

import bareunpy
import bareun.language_service_pb2 as pb
import bareun.language_service_pb2_grpc as ls

MAX_MESSAGE_LENGTH = 100 * 1024 * 1024


class BareunLanguageServiceClient:
    """
    형태소 분석을 처리하는 클라이언트
    """

    def __init__(self, channel:grpc.Channel, apikey:str, host:str, port:int):
        """
        클라이언트 생성자

        Args:
            channel (grpc.Channel): 원격 채널 정보
        """
        self.channel = channel
        self.apikey = apikey
        self.metadata=(
                ('api-key', self.apikey),
                ('user-agent', f'bareunpy/{bareunpy.version}')
                )
        self.host = host
        self.port = port
        self.stub = ls.LanguageServiceStub(self.channel)

    def analyze_syntax(self, content: str,
        domain: str = "",
        auto_split=False,
        auto_spacing=True,
        auto_jointing=False) -> pb.AnalyzeSyntaxResponse:
        """
        형태소 분석을 수행합니다.

        Args:
            content (str): 형태소 분석할 원문, 여러 문장일 경우에 개행문자로 줄바꿈을 하면 됩니다.
            domain (str, optional): 사용사 사전의 이름. 기본값은 "".
            auto_split (bool, optional): 문장 자동 분리 여부, 기본값은 사용하지 않음.
            auto_spacing (bool, optional): 띄어쓰기 보정 기능, 기본값은 사용하도록 함.
            auto_jointing (bool, optional): 붙여쓰기 보정 기능, 기본값은 사용하지 않음.

        Raises:
            e: grpc.Error, 원격 호출시 예외가 발생할 수 있습니다.

        Returns:
            pb.AnalyzeSyntaxResponse: 형태소 분석 결과
        """
        req = pb.AnalyzeSyntaxRequest()
        # req.document = pb.Document()
        req.document.content = content
        req.document.language = "ko_KR"
        req.encoding_type = pb.EncodingType.UTF32
        req.auto_split_sentence = auto_split
        req.auto_spacing = auto_spacing
        req.auto_jointing = auto_jointing
        if domain:
            req.custom_domain = domain
        try:
            res, c = self.stub.AnalyzeSyntax.with_call(
                request=req, metadata=self.metadata)
            return res
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.PERMISSION_DENIED:
                message = f'\n입력한 API key가 정확한지 확인해 주세요.\n > apikey: {self.apikey}'
                raise Exception(message) from e
            elif e.code() == grpc.StatusCode.UNAVAILABLE:
                message = f'\n입력한 서버 주소가 정확한지 확인해 주세요.\n > host:port = {self.host}:{self.port}'
                raise Exception(message) from e
            else:
                raise e
        except Exception as e2:
            import traceback
            traceback.print_exc()
            raise e2
        
    def analyze_syntax_list(self, content: List[str],
        domain: str = "",
        auto_spacing=True,
        auto_jointing=False) -> pb.AnalyzeSyntaxListResponse:
        """
        형태소 분석을 수행하되, 입력된 문장 단위가 일치하도록 반환됩니다.
        문장 분할 기능을 사용하지 않습니다.

        Args:
            content (List[str]): 형태소 분석할 원문의 리스트
            domain (str, optional): 사용사 사전의 이름. 기본값은 "".
            auto_spacing (bool, optional): 띄어쓰기 보정 기능, 기본값은 사용하도록 함.
            auto_jointing (bool, optional): 붙여쓰기 보정 기능, 기본값은 사용하지 않음.

        Raises:
            e: grpc.Error, 원격 호출시 예외가 발생할 수 있습니다.

        Returns:
            pb.AnalyzeSyntaxListResponse: 형태소 분석 결과
        """
        req = pb.AnalyzeSyntaxListRequest()
        req.sentences.extend(content)
        req.language = "ko_KR"
        req.encoding_type = pb.EncodingType.UTF32
        req.auto_spacing = auto_spacing
        req.auto_jointing = auto_jointing
        if domain:
            req.custom_domain = domain
        try:
            res, c = self.stub.AnalyzeSyntaxList.with_call(
                request=req, metadata=self.metadata)
            return res
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.PERMISSION_DENIED:
                message = f'\n입력한 API key가 정확한지 확인해 주세요.\n > apikey: {self.apikey}'
                raise Exception(message) from e
            elif e.code() == grpc.StatusCode.UNAVAILABLE:
                message = f'\n입력한 서버 주소가 정확한지 확인해 주세요.\n > host:port = {self.host}:{self.port}'
                raise Exception(message) from e
            else:
                raise e
        except Exception as e2:
            import traceback
            traceback.print_exc()
            raise e2


    def tokenize(self, content: str, auto_split=False) -> pb.TokenizeResponse:
        """
        형태소 분석을 수행합니다.

        Args:
            content (str): 형태소 분석할 원문, 여러 문장일 경우에 개행문자로 줄바꿈을 하면 됩니다.
            domain (str, optional): 사용사 사전의 이름. 기본값은 "".
            auto_split (bool, optional): 문장 자동 분리 여부, 기본값은 사용하지 않음.

        Raises:
            e: grpc.Error, 원격 호출시 예외가 발생할 수 있습니다.

        Returns:
            pb.AnalyzeSyntaxResponse: 형태소 분석 결과
        """
        req = pb.TokenizeRequest()
        # req.document = pb.Document()
        req.document.content = content
        req.document.language = "ko_KR"
        req.encoding_type = pb.EncodingType.UTF32
        req.auto_split_sentence = auto_split
        try:
            res, c = self.stub.Tokenize.with_call(
                request=req, metadata=self.metadata)
            return res
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.PERMISSION_DENIED:
                message = f'\n입력한 API key가 정확한지 확인해 주세요.\n > apikey: {self.apikey}'
                raise Exception(message) from e
            elif e.code() == grpc.StatusCode.UNAVAILABLE:
                message = f'\n입력한 서버 주소가 정확한지 확인해 주세요.\n > host:port = {self.host}:{self.port}'
                raise Exception(message) from e
            else:
                raise e
