import grpc
from typing import List

import bareunpy
import bareun.language_service_pb2 as pb
import bareun.language_service_pb2_grpc as ls
import bareun.lang_common_pb2 as lpb

MAX_MESSAGE_LENGTH = 100 * 1024 * 1024
CA_BUNDLE = b"""-----BEGIN CERTIFICATE-----
MIIGEzCCA/ugAwIBAgIQfVtRJrR2uhHbdBYLvFMNpzANBgkqhkiG9w0BAQwFADCB
iDELMAkGA1UEBhMCVVMxEzARBgNVBAgTCk5ldyBKZXJzZXkxFDASBgNVBAcTC0pl
cnNleSBDaXR5MR4wHAYDVQQKExVUaGUgVVNFUlRSVVNUIE5ldHdvcmsxLjAsBgNV
BAMTJVVTRVJUcnVzdCBSU0EgQ2VydGlmaWNhdGlvbiBBdXRob3JpdHkwHhcNMTgx
MTAyMDAwMDAwWhcNMzAxMjMxMjM1OTU5WjCBjzELMAkGA1UEBhMCR0IxGzAZBgNV
BAgTEkdyZWF0ZXIgTWFuY2hlc3RlcjEQMA4GA1UEBxMHU2FsZm9yZDEYMBYGA1UE
ChMPU2VjdGlnbyBMaW1pdGVkMTcwNQYDVQQDEy5TZWN0aWdvIFJTQSBEb21haW4g
VmFsaWRhdGlvbiBTZWN1cmUgU2VydmVyIENBMIIBIjANBgkqhkiG9w0BAQEFAAOC
AQ8AMIIBCgKCAQEA1nMz1tc8INAA0hdFuNY+B6I/x0HuMjDJsGz99J/LEpgPLT+N
TQEMgg8Xf2Iu6bhIefsWg06t1zIlk7cHv7lQP6lMw0Aq6Tn/2YHKHxYyQdqAJrkj
eocgHuP/IJo8lURvh3UGkEC0MpMWCRAIIz7S3YcPb11RFGoKacVPAXJpz9OTTG0E
oKMbgn6xmrntxZ7FN3ifmgg0+1YuWMQJDgZkW7w33PGfKGioVrCSo1yfu4iYCBsk
Haswha6vsC6eep3BwEIc4gLw6uBK0u+QDrTBQBbwb4VCSmT3pDCg/r8uoydajotY
uK3DGReEY+1vVv2Dy2A0xHS+5p3b4eTlygxfFQIDAQABo4IBbjCCAWowHwYDVR0j
BBgwFoAUU3m/WqorSs9UgOHYm8Cd8rIDZsswHQYDVR0OBBYEFI2MXsRUrYrhd+mb
+ZsF4bgBjWHhMA4GA1UdDwEB/wQEAwIBhjASBgNVHRMBAf8ECDAGAQH/AgEAMB0G
A1UdJQQWMBQGCCsGAQUFBwMBBggrBgEFBQcDAjAbBgNVHSAEFDASMAYGBFUdIAAw
CAYGZ4EMAQIBMFAGA1UdHwRJMEcwRaBDoEGGP2h0dHA6Ly9jcmwudXNlcnRydXN0
LmNvbS9VU0VSVHJ1c3RSU0FDZXJ0aWZpY2F0aW9uQXV0aG9yaXR5LmNybDB2Bggr
BgEFBQcBAQRqMGgwPwYIKwYBBQUHMAKGM2h0dHA6Ly9jcnQudXNlcnRydXN0LmNv
bS9VU0VSVHJ1c3RSU0FBZGRUcnVzdENBLmNydDAlBggrBgEFBQcwAYYZaHR0cDov
L29jc3AudXNlcnRydXN0LmNvbTANBgkqhkiG9w0BAQwFAAOCAgEAMr9hvQ5Iw0/H
ukdN+Jx4GQHcEx2Ab/zDcLRSmjEzmldS+zGea6TvVKqJjUAXaPgREHzSyrHxVYbH
7rM2kYb2OVG/Rr8PoLq0935JxCo2F57kaDl6r5ROVm+yezu/Coa9zcV3HAO4OLGi
H19+24rcRki2aArPsrW04jTkZ6k4Zgle0rj8nSg6F0AnwnJOKf0hPHzPE/uWLMUx
RP0T7dWbqWlod3zu4f+k+TY4CFM5ooQ0nBnzvg6s1SQ36yOoeNDT5++SR2RiOSLv
xvcRviKFxmZEJCaOEDKNyJOuB56DPi/Z+fVGjmO+wea03KbNIaiGCpXZLoUmGv38
sbZXQm2V0TP2ORQGgkE49Y9Y3IBbpNV9lXj9p5v//cWoaasm56ekBYdbqbe4oyAL
l6lFhd2zi+WJN44pDfwGF/Y4QA5C5BIG+3vzxhFoYt/jmPQT2BVPi7Fp2RBgvGQq
6jG35LWjOhSbJuMLe/0CjraZwTiXWTb2qHSihrZe68Zk6s+go/lunrotEbaGmAhY
LcmsJWTyXnW0OMGuf1pGg+pRyrbxmRE1a6Vqe8YAsOf4vmSyrcjC8azjUeqkk+B5
yOGBQMkKW+ESPMFgKuOXwIlCypTPRpgSabuY0MLTDXJLR27lk8QyKGOHQ+SwMj4K
00u/I5sUKUErmgQfky3xxzlIPK1aEn8=
-----END CERTIFICATE-----
-----BEGIN CERTIFICATE-----
MIIFgTCCBGmgAwIBAgIQOXJEOvkit1HX02wQ3TE1lTANBgkqhkiG9w0BAQwFADB7
MQswCQYDVQQGEwJHQjEbMBkGA1UECAwSR3JlYXRlciBNYW5jaGVzdGVyMRAwDgYD
VQQHDAdTYWxmb3JkMRowGAYDVQQKDBFDb21vZG8gQ0EgTGltaXRlZDEhMB8GA1UE
AwwYQUFBIENlcnRpZmljYXRlIFNlcnZpY2VzMB4XDTE5MDMxMjAwMDAwMFoXDTI4
MTIzMTIzNTk1OVowgYgxCzAJBgNVBAYTAlVTMRMwEQYDVQQIEwpOZXcgSmVyc2V5
MRQwEgYDVQQHEwtKZXJzZXkgQ2l0eTEeMBwGA1UEChMVVGhlIFVTRVJUUlVTVCBO
ZXR3b3JrMS4wLAYDVQQDEyVVU0VSVHJ1c3QgUlNBIENlcnRpZmljYXRpb24gQXV0
aG9yaXR5MIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEAgBJlFzYOw9sI
s9CsVw127c0n00ytUINh4qogTQktZAnczomfzD2p7PbPwdzx07HWezcoEStH2jnG
vDoZtF+mvX2do2NCtnbyqTsrkfjib9DsFiCQCT7i6HTJGLSR1GJk23+jBvGIGGqQ
Ijy8/hPwhxR79uQfjtTkUcYRZ0YIUcuGFFQ/vDP+fmyc/xadGL1RjjWmp2bIcmfb
IWax1Jt4A8BQOujM8Ny8nkz+rwWWNR9XWrf/zvk9tyy29lTdyOcSOk2uTIq3XJq0
tyA9yn8iNK5+O2hmAUTnAU5GU5szYPeUvlM3kHND8zLDU+/bqv50TmnHa4xgk97E
xwzf4TKuzJM7UXiVZ4vuPVb+DNBpDxsP8yUmazNt925H+nND5X4OpWaxKXwyhGNV
icQNwZNUMBkTrNN9N6frXTpsNVzbQdcS2qlJC9/YgIoJk2KOtWbPJYjNhLixP6Q5
D9kCnusSTJV882sFqV4Wg8y4Z+LoE53MW4LTTLPtW//e5XOsIzstAL81VXQJSdhJ
WBp/kjbmUZIO8yZ9HE0XvMnsQybQv0FfQKlERPSZ51eHnlAfV1SoPv10Yy+xUGUJ
5lhCLkMaTLTwJUdZ+gQek9QmRkpQgbLevni3/GcV4clXhB4PY9bpYrrWX1Uu6lzG
KAgEJTm4Diup8kyXHAc/DVL17e8vgg8CAwEAAaOB8jCB7zAfBgNVHSMEGDAWgBSg
EQojPpbxB+zirynvgqV/0DCktDAdBgNVHQ4EFgQUU3m/WqorSs9UgOHYm8Cd8rID
ZsswDgYDVR0PAQH/BAQDAgGGMA8GA1UdEwEB/wQFMAMBAf8wEQYDVR0gBAowCDAG
BgRVHSAAMEMGA1UdHwQ8MDowOKA2oDSGMmh0dHA6Ly9jcmwuY29tb2RvY2EuY29t
L0FBQUNlcnRpZmljYXRlU2VydmljZXMuY3JsMDQGCCsGAQUFBwEBBCgwJjAkBggr
BgEFBQcwAYYYaHR0cDovL29jc3AuY29tb2RvY2EuY29tMA0GCSqGSIb3DQEBDAUA
A4IBAQAYh1HcdCE9nIrgJ7cz0C7M7PDmy14R3iJvm3WOnnL+5Nb+qh+cli3vA0p+
rvSNb3I8QzvAP+u431yqqcau8vzY7qN7Q/aGNnwU4M309z/+3ri0ivCRlv79Q2R+
/czSAaF9ffgZGclCKxO/WIu6pKJmBHaIkU4MiRTOok3JMrO66BQavHHxW/BBC5gA
CiIDEOUMsfnNkjcZ7Tvx5Dq2+UUTJnWvu6rvP3t3O9LEApE9GQDTF1w52z97GA1F
zZOFli9d31kWTz9RvdVFGD/tSo7oBmF0Ixa1DVBzJ0RHfxBdiSprhTEUxOipakyA
vGp4z7h/jnZymQyd/teRCBaho1+V
-----END CERTIFICATE-----
"""

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
        self.channel = self._create_secure_channel(host, port, ca_cert_pem=CA_BUNDLE)
        self.stub = ls.LanguageServiceStub(self.channel)
    
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
