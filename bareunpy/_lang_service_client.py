import grpc
import ssl
import logging
from typing import List

import bareunpy
import bareun.language_service_pb2 as pb
import bareun.language_service_pb2_grpc as ls
import bareun.lang_common_pb2 as lpb

MAX_MESSAGE_LENGTH = 100 * 1024 * 1024

_logger = logging.getLogger(__name__)

# 서버가 intermediate 인증서를 체인에 포함하지 않는 경우를 대비하여
# api.bareun.ai의 intermediate CA를 런타임에 가져와 캐싱합니다.
_cached_root_certs = None


def _fetch_intermediate_certs(host: str, port: int = 443) -> bytes:
    """서버의 leaf 인증서에서 AIA 확장을 읽어 intermediate CA를 자동으로 가져옵니다.

    서버가 full chain을 보내지 않는 경우, leaf cert의 Authority Information Access(AIA)
    확장에 있는 CA Issuers URL을 따라가서 intermediate 인증서를 다운로드합니다.
    """
    try:
        from cryptography import x509
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives.serialization import Encoding
        from cryptography.x509.oid import AuthorityInformationAccessOID
        import urllib.request

        # 검증 없이 서버의 leaf cert를 가져옴
        pem = ssl.get_server_certificate((host, port))
        cert = x509.load_pem_x509_certificate(pem.encode(), default_backend())

        intermediates = b""
        seen = set()
        current_cert = cert

        # AIA 체인을 따라가며 intermediate 인증서들을 수집 (최대 5단계)
        for _ in range(5):
            try:
                aia = current_cert.extensions.get_extension_for_class(
                    x509.AuthorityInformationAccess
                )
            except x509.ExtensionNotFound:
                break

            ca_url = None
            for desc in aia.value:
                if desc.access_method == AuthorityInformationAccessOID.CA_ISSUERS:
                    ca_url = desc.access_location.value
                    break
            if not ca_url or ca_url in seen:
                break
            seen.add(ca_url)

            try:
                resp = urllib.request.urlopen(ca_url, timeout=10)
                der_data = resp.read()
            except Exception:
                break

            # DER → PEM 변환
            try:
                # DER 형식인지 확인
                intermediate_cert = x509.load_der_x509_certificate(der_data, default_backend())
            except Exception:
                try:
                    intermediate_cert = x509.load_pem_x509_certificate(der_data, default_backend())
                except Exception:
                    break

            pem_bytes = intermediate_cert.public_bytes(encoding=Encoding.PEM)
            intermediates += pem_bytes

            # self-signed이면 루트 도달, 중지
            if intermediate_cert.issuer == intermediate_cert.subject:
                break
            current_cert = intermediate_cert

        return intermediates
    except Exception as e:
        _logger.debug("intermediate 인증서 자동 다운로드 실패: %s", e)
        return b""


def _get_root_certificates(host: str = "api.bareun.ai", port: int = 443) -> bytes:
    """런타임에 최신 CA 인증서를 로드합니다.

    1. certifi 패키지가 있으면 Mozilla CA 번들을 로드합니다.
       없으면 gRPC 내장 루트 인증서를 사용합니다.
    2. 서버가 intermediate 인증서를 체인에 포함하지 않는 경우를 대비하여
       AIA 확장을 통해 intermediate CA를 자동으로 가져와 번들에 추가합니다.
    결과는 모듈 수준에서 캐싱됩니다.
    """
    global _cached_root_certs
    if _cached_root_certs is not None:
        return _cached_root_certs

    # 1) certifi 또는 gRPC 기본 CA 번들
    root_certs = None
    try:
        import certifi
        with open(certifi.where(), 'rb') as f:
            root_certs = f.read()
    except (ImportError, IOError):
        pass

    # 2) intermediate 인증서 자동 보충
    intermediates = _fetch_intermediate_certs(host, port)
    if intermediates:
        if root_certs:
            root_certs = root_certs + b"\n" + intermediates
        else:
            root_certs = intermediates

    _cached_root_certs = root_certs
    return _cached_root_certs

class BareunLanguageServiceClient:
    """
    형태소 분석을 처리하는 클라이언트
    """

    def __init__(self, apikey:str, host:str, port:int):
        """
        클라이언트 생성자

        Args:
            apikey (str): Bareun API 키
            host (str): Bareun 서버 호스트 주소
            port (int): Bareun 서버 포트 번호
        """
        self.apikey = apikey
        self.metadata=(
                ('api-key', self.apikey),
                ('user-agent', f'bareunpy/{bareunpy.version}')
                )
        self.host = host
        self.port = port
        self.channel = self._create_secure_channel(host, port)
        self.stub = ls.LanguageServiceStub(self.channel)
    
    def _create_secure_channel(self,
        host: str,
        port: int,
    ) -> grpc.Channel:
        """
        gRPC 보안 채널을 생성합니다.
        """
        opts=[
            ('grpc.max_send_message_length', MAX_MESSAGE_LENGTH),
            ('grpc.max_receive_message_length', MAX_MESSAGE_LENGTH),
        ]
        if host.lower().startswith("api.bareun.ai"):
            root_certs = _get_root_certificates(host, port)
            creds = grpc.ssl_channel_credentials(root_certificates=root_certs)
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
            message = f'\n서버에 연결할 수 없습니다. 입력한 서버주소 [{self.host}:{self.port}]가 정확한지 확인해 주세요.\n서버 메시지: {server_message}'
        elif code == grpc.StatusCode.INVALID_ARGUMENT:
            message = f'\n잘못된 요청이 서버로 전송되었습니다. 입력 데이터를 확인하세요.\n서버 메시지: {server_message}'
        else:
            message = f'알 수 없는 오류가 발생했습니다.\n서버 메시지: {server_message}'
            raise e
        raise Exception(message) from e
    
    def analyze_syntax(self, content: str,
        custom_dicts: List[str] = [],
        auto_split=False,
        auto_spacing=True,
        auto_jointing=True) -> pb.AnalyzeSyntaxResponse:
        """
        형태소 분석을 수행합니다.

        Args:
            content (str): 형태소 분석할 원문, 여러 문장일 경우에 개행문자로 줄바꿈을 하면 됩니다.
            custom_dicts (list, optional): 사용자 사전의 이름. 기본값은 [].
            auto_split (bool, optional): 문장 자동 분리 여부, 기본값은 사용하지 않음.
            auto_spacing (bool, optional): 띄어쓰기 보정 기능, 기본값은 사용하도록 함.
            auto_jointing (bool, optional): 붙여쓰기 보정 기능, 기본값은 사용하도록 함.

        Raises:
            e: grpc.Error, 원격 호출시 예외가 발생할 수 있습니다.

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
            res, c = self.stub.AnalyzeSyntax.with_call(
                request=req, metadata=self.metadata)
            return res
        except grpc.RpcError as e:
            self._handle_grpc_error(e)
        except Exception as e2:
            import traceback
            traceback.print_exc()
            raise e2
        
    def analyze_syntax_list(self, content: List[str],
        custom_dicts: List[str] = [],
        auto_spacing=True,
        auto_jointing=True) -> pb.AnalyzeSyntaxListResponse:
        """
        형태소 분석을 수행하되, 입력된 문장 단위가 일치하도록 반환됩니다.
        문장 분할 기능을 사용하지 않습니다.

        Args:
            content (List[str]): 형태소 분석할 원문의 리스트
            custom_dicts (list, optional): 사용자 사전의 이름. 기본값은 [].
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
        req.encoding_type = lpb.EncodingType.UTF32
        req.auto_spacing = auto_spacing
        req.auto_jointing = auto_jointing
        req.custom_dict_names.extend(custom_dicts)

        try:
            res, c = self.stub.AnalyzeSyntaxList.with_call(
                request=req, metadata=self.metadata)
            return res
        except grpc.RpcError as e:
            self._handle_grpc_error(e)
        except Exception as e2:
            import traceback
            traceback.print_exc()
            raise e2


    def tokenize(self, content: str, auto_split=False) -> pb.TokenizeResponse:
        """
        형태소 분석을 수행합니다.

        Args:
            content (str): 형태소 분석할 원문, 여러 문장일 경우에 개행문자로 줄바꿈을 하면 됩니다.
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
        req.encoding_type = lpb.EncodingType.UTF32
        req.auto_split_sentence = auto_split
        try:
            res, c = self.stub.Tokenize.with_call(
                request=req, metadata=self.metadata)
            return res
        except grpc.RpcError as e:
            self._handle_grpc_error(e)
        except Exception as e2:
            import traceback
            traceback.print_exc()
            raise e2
