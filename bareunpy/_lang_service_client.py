# -*- coding: utf-8 -*-
"""형태소 분석(LanguageService) Connect RPC 클라이언트.

이 모듈은 bareun 서버의 ``LanguageService`` 를 **공식 Connect RPC 라이브러리**
(`connectrpc`, github.com/connectrpc/connect-python)로 호출한다. 과거 버전은 ``grpcio``
채널을 직접 사용했으나, 서버가 connect-go 로 전환되어 gRPC/Connect/gRPC-Web 를 한 포트에서
제공하므로 클라이언트도 HTTP 기반 Connect 로 통신한다.

또한 이 모듈은 다른 서비스 클라이언트(revision, custom_dict)가 공통으로 쓰는
주소 생성 헬퍼를 함께 제공한다. HTTP 전송/TLS 는 connectrpc 기본(pyqwest)에 맡긴다.
"""

import logging

from bareunpy._version import version
from connectrpc.code import Code
from connectrpc.errors import ConnectError

import bareun.language_service_pb2 as pb
import bareun.lang_common_pb2 as lpb
from bareun.language_service_connect import LanguageServiceClientSync

# Connect/HTTP 응답 본문 크기 제한. grpc 시절 100MB 제한과 동일한 의미로 둔다.
# connectrpc 의 read_max_bytes 에 그대로 전달한다.
MAX_MESSAGE_LENGTH = 100 * 1024 * 1024

_logger = logging.getLogger(__name__)


def is_secure_host(host: str) -> bool:
    """해당 호스트에 TLS(HTTPS)로 접속해야 하는지 판단합니다.

    공개 서비스(api.bareun.ai)는 TLS 로 제공되고, 로컬/사내에 직접 설치한 서버는
    평문(HTTP)으로 접속하는 기존 동작을 그대로 유지합니다.

    Args:
        host (str): 서버 호스트

    Returns:
        bool: api.bareun.ai 계열이면 True(=HTTPS), 그 외에는 False(=HTTP)
    """
    return host.lower().startswith("api.bareun.ai")


def build_base_address(host: str, port: int) -> str:
    """connectrpc 클라이언트에 넘길 베이스 주소(scheme 포함)를 만듭니다.

    connectrpc 클라이언트는 ``https://host:port`` 처럼 scheme 이 포함된 주소를 요구한다.

    Args:
        host (str): 서버 호스트
        port (int): 서버 포트

    Returns:
        str: ``https://...`` 또는 ``http://...`` 형식의 베이스 주소
    """
    scheme = "https" if is_secure_host(host) else "http"
    return f"{scheme}://{host}:{port}"


def build_metadata(apikey: str) -> dict:
    """모든 요청에 공통으로 붙일 헤더(메타데이터)를 만듭니다.

    - ``api-key`` : 인증 키
    - ``user-agent`` : 서버측 사용량 식별용(grpc 시절과 동일하게 ``bareunpy/<version>``)

    connectrpc 의 각 메서드는 호출마다 ``headers`` 로 Mapping 을 받는다(grpc metadata 대체).

    Args:
        apikey (str): Bareun API 키

    Returns:
        dict: 요청 헤더 매핑
    """
    return {"api-key": apikey, "user-agent": f"bareunpy/{version}"}


class BareunLanguageServiceClient:
    """형태소 분석을 처리하는 클라이언트.

    bareun ``LanguageService`` 의 ``AnalyzeSyntax``/``AnalyzeSyntaxList``/``Tokenize`` 를
    Connect RPC 로 호출한다. API 키는 매 호출마다 ``api-key`` 요청 헤더로 전달한다.
    """

    def __init__(self, apikey: str, host: str, port: int):
        """클라이언트 생성자.

        Args:
            apikey (str): Bareun API 키
            host (str): Bareun 서버 호스트 주소
            port (int): Bareun 서버 포트 번호
        """
        self.apikey = apikey
        self.host = host
        self.port = port
        self.metadata = build_metadata(apikey)
        # TLS/HTTP 전송은 connectrpc 기본(pyqwest)에 맡긴다. api.bareun.ai 는 표준 TLS 로 동작하므로
        # 별도 http_client 가 필요 없다(로컬 서버는 http:// 주소로 평문 통신).
        self.stub = LanguageServiceClientSync(
            build_base_address(host, port),
            read_max_bytes=MAX_MESSAGE_LENGTH,
        )

    def close(self) -> None:
        """내부 HTTP 클라이언트를 닫습니다(선택). 닫은 뒤에는 호출할 수 없습니다."""
        self.stub.close()

    def _handle_connect_error(self, e: ConnectError):
        """Connect 에러를 사용자 친화적인 메시지로 변환합니다.

        인증/연결/입력오류는 한국어 안내 메시지로 바꿔 ``Exception`` 으로 다시 던지고,
        그 외 코드는 원본 ``ConnectError`` 를 그대로 전파한다.

        Args:
            e (ConnectError): connectrpc 가 던진 예외

        Raises:
            Exception: 안내 메시지를 담은 예외(인증/연결/입력오류)
            ConnectError: 그 외의 코드는 원본을 그대로 전파
        """
        code = e.code
        server_message = e.message if e.message else "서버에서 추가 메시지를 제공하지 않았습니다."
        if code in (Code.PERMISSION_DENIED, Code.UNAUTHENTICATED):
            message = f'\n입력한 API KEY가 정확한지 확인해 주세요.\n > APIKEY: {self.apikey}\n서버 메시지: {server_message}'
        elif code == Code.UNAVAILABLE:
            message = f'\n서버에 연결할 수 없습니다. 입력한 서버주소 [{self.host}:{self.port}]가 정확한지 확인해 주세요.\n서버 메시지: {server_message}'
        elif code == Code.INVALID_ARGUMENT:
            message = f'\n잘못된 요청이 서버로 전송되었습니다. 입력 데이터를 확인하세요.\n서버 메시지: {server_message}'
        else:
            raise e
        raise Exception(message) from e

    def analyze_syntax(self, content: str,
        custom_dicts=[],
        auto_split=False,
        auto_spacing=True,
        auto_jointing=True) -> pb.AnalyzeSyntaxResponse:
        """형태소 분석을 수행합니다.

        Args:
            content (str): 형태소 분석할 원문, 여러 문장일 경우에 개행문자로 줄바꿈을 하면 됩니다.
            custom_dicts (list, optional): 사용자 사전의 이름. 기본값은 [].
            auto_split (bool, optional): 문장 자동 분리 여부, 기본값은 사용하지 않음.
            auto_spacing (bool, optional): 띄어쓰기 보정 기능, 기본값은 사용하도록 함.
            auto_jointing (bool, optional): 붙여쓰기 보정 기능, 기본값은 사용하도록 함.

        Raises:
            Exception: 원격 호출시 예외가 발생할 수 있습니다.

        Returns:
            pb.AnalyzeSyntaxResponse: 형태소 분석 결과
        """
        req = pb.AnalyzeSyntaxRequest()
        req.document.content = content
        req.document.language = "ko_KR"
        req.encoding_type = lpb.EncodingType.UTF32
        req.auto_split_sentence = auto_split
        req.auto_spacing = auto_spacing
        req.auto_jointing = auto_jointing
        req.custom_dict_names.extend(custom_dicts)

        try:
            return self.stub.analyze_syntax(req, headers=self.metadata)
        except ConnectError as e:
            self._handle_connect_error(e)

    def analyze_syntax_list(self, content,
        custom_dicts=[],
        auto_spacing=True,
        auto_jointing=True) -> pb.AnalyzeSyntaxListResponse:
        """형태소 분석을 수행하되, 입력된 문장 단위가 일치하도록 반환됩니다.

        문장 분할 기능을 사용하지 않습니다.

        Args:
            content (List[str]): 형태소 분석할 원문의 리스트
            custom_dicts (list, optional): 사용자 사전의 이름. 기본값은 [].
            auto_spacing (bool, optional): 띄어쓰기 보정 기능, 기본값은 사용하도록 함.
            auto_jointing (bool, optional): 붙여쓰기 보정 기능, 기본값은 사용하지 않음.

        Raises:
            Exception: 원격 호출시 예외가 발생할 수 있습니다.

        Returns:
            pb.AnalyzeSyntaxListResponse: 형태소 분석 결과
        """
        req = pb.AnalyzeSyntaxListRequest()
        req.sentences.extend(content)
        req.language = "ko_KR"
        req.encoding_type = lpb.EncodingType.UTF32
        req.auto_spacing = auto_spacing
        req.auto_jointing = auto_jointing
        req.custom_dict_names.extend(custom_dicts)

        try:
            return self.stub.analyze_syntax_list(req, headers=self.metadata)
        except ConnectError as e:
            self._handle_connect_error(e)

    def tokenize(self, content: str, auto_split=False, auto_spacing=True) -> pb.TokenizeResponse:
        """문장을 토크나이즈(분절)합니다.

        Args:
            content (str): 분절할 원문, 여러 문장일 경우에 개행문자로 줄바꿈을 하면 됩니다.
            auto_split (bool, optional): 문장 자동 분리 여부, 기본값은 사용하지 않음.
                현재 protos 에서 ``TokenizeRequest.auto_split_sentence`` 는 deprecated 이며,
                서버는 기본적으로 개행('\\n')을 기준으로 문장을 자릅니다. 하위호환을 위해 인자는 유지합니다.
            auto_spacing (bool, optional): 띄어쓰기 보정 기능, 기본값은 사용하도록 함.
                (현재 protos 의 ``TokenizeRequest.auto_spacing`` 반영)

        Raises:
            Exception: 원격 호출시 예외가 발생할 수 있습니다.

        Returns:
            pb.TokenizeResponse: 토크나이즈 결과
        """
        req = pb.TokenizeRequest()
        req.document.content = content
        req.document.language = "ko_KR"
        req.encoding_type = lpb.EncodingType.UTF32
        # auto_split_sentence 는 deprecated 이지만 proto 에 필드가 남아 있어 하위호환으로 그대로 전달한다.
        req.auto_split_sentence = auto_split
        req.auto_spacing = auto_spacing
        try:
            return self.stub.tokenize(req, headers=self.metadata)
        except ConnectError as e:
            self._handle_connect_error(e)
