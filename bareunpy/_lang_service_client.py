import grpc

import bareun.language_service_pb2 as pb
import bareun.language_service_pb2_grpc as ls

MAX_MESSAGE_LENGTH = 100 * 1024 * 1024


class BareunLanguageServiceClient:
    """
    형태소 분석을 처리하는 클라이언트
    """

    def __init__(self, remote: str):
        """
        클라이언트 생성자

        Args:
            remote (str): 원격 주소, IP주소:포트 또는 호스트이름:포트 형식으로 사용합니다.
        """
        channel = grpc.insecure_channel(
            remote,
            options=[
                ('grpc.max_send_message_length', MAX_MESSAGE_LENGTH),
                ('grpc.max_receive_message_length', MAX_MESSAGE_LENGTH),
            ])

        self.stub = ls.LanguageServiceStub(channel)

    def analyze_syntax(self, content: str, domain: str = "", auto_split=False) -> pb.AnalyzeSyntaxResponse:
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
        req = pb.AnalyzeSyntaxRequest()
        # req.document = pb.Document()
        req.document.content = content
        req.document.language = "ko_KR"
        req.encoding_type = pb.EncodingType.UTF32
        req.auto_split_sentence = auto_split
        if domain:
            req.custom_domain = domain
        try:
            res = self.stub.AnalyzeSyntax(req)
            return res
        except grpc.RpcError as e:
            raise e

