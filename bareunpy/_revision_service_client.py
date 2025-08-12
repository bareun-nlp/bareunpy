import grpc
import bareun.revision_service_pb2 as pb
import bareun.revision_service_pb2_grpc as rs_grpc
from bareunpy._lang_service_client import CA_BUNDLE

MAX_MESSAGE_LENGTH = 100 * 1024 * 1024


class BareunRevisionServiceClient:
    """
    맞춤법 검사를 처리하는 클라이언트
    """

    def __init__(self, apikey: str, host: str, port: int):
        """
        RevisionServiceClient 초기화

        Args:
            apikey (str): API 키
            host (str): gRPC 서버 주소
            port (int): gRPC 서버 포트
        """
        self.apikey = apikey
        self.host = host
        self.port = port
        self.channel = self._create_secure_channel(host, port, ca_cert_pem=CA_BUNDLE)
        self.metadata = [
            ('api-key', self.apikey),
            ('user-agent', 'bareun-revision-client'),
        ]
        self.stub = rs_grpc.RevisionServiceStub(self.channel)

    def _create_secure_channel(self,
            host: str,
            port: int,
            *,
            ca_cert_pem: bytes = None
        ) -> grpc.Channel:
            """
            gRPC 보안 채널을 생성합니다.
            """
            opts=[
                ('grpc.max_send_message_length', MAX_MESSAGE_LENGTH),
                ('grpc.max_receive_message_length', MAX_MESSAGE_LENGTH),
            ]
            if host.lower().startswith("api.bareun.ai"):
                creds = grpc.ssl_channel_credentials(root_certificates=ca_cert_pem)
                return grpc.secure_channel(f"{host}:{port}",
                                        creds,
                                        options=opts)
            else:
                return grpc.insecure_channel(
                    f"{host}:{port}",
                    options=opts
                )

    def _handle_grpc_error(self, e: grpc.RpcError):
        """gRPC 에러를 처리하는 메서드"""
        details = getattr(e, "details", lambda: None)()
        code = getattr(e, "code", lambda: grpc.StatusCode.OK)()
        server_message = details if details else "서버에서 추가 메시지를 제공하지 않았습니다."
        if code == grpc.StatusCode.PERMISSION_DENIED:
            message = f'\n입력한 API KEY가 정확한지 확인해 주세요.\n > APIKEY: {self.apikey}\n서버 메시지: {server_message}'
        elif code == grpc.StatusCode.UNAVAILABLE:
            message = f'\n서버에 연결할 수 없습니다. 입력한 서버주소 [{self.host}:{self.port}]를 확인하세요.\n서버 메시지: {server_message}'
        elif code == grpc.StatusCode.INVALID_ARGUMENT:
            message = f'\n잘못된 요청이 서버로 전송되었습니다. 입력 데이터를 확인하세요.\n서버 메시지: {server_message}'
        else:
            message = f'알 수 없는 오류가 발생했습니다.\n서버 메시지: {server_message}'
            raise e
        raise Exception(message) from e

    def correct_error(self, request: pb.CorrectErrorRequest) -> pb.CorrectErrorResponse:
        """
        맞춤법 교정을 위한 gRPC 호출

        Args:
            request (pb.CorrectErrorRequest): gRPC 요청 메시지

        Returns:
            pb.CorrectErrorResponse: gRPC 응답 메시지
        """
        try:
            response, call = self.stub.CorrectError.with_call(
                request=request, metadata=self.metadata
            )
            return response
        except grpc.RpcError as e:
            self._handle_grpc_error(e)
