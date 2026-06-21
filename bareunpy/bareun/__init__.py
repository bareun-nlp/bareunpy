# -*- coding: utf-8 -*-
"""bareun 프로토버프 생성 코드 서브패키지.

bareun 모노레포 protos/ 에서 buf generate 로 생성된 파일들을 모아 둔다.
tools/gen_proto.sh 로 재생성한다.

----

생성된 *_pb2.py / *_connect.py 파일 내부에는
  from bareun import X_pb2
  import bareun.X_pb2
형태의 크로스-임포트가 하드코딩되어 있다(buf 플러그인이 proto package 이름을
그대로 사용하기 때문). 이 패키지를 최상위 bareun 패키지 대신 bareunpy.bareun
서브패키지로 두면서, sys.modules 에 'bareun' 별칭을 등록해 크로스-임포트를
유지한다.

또한 서브모듈을 미리 로드해 bareunpy.bareun.X 와 bareun.X 가 항상 동일
모듈 객체를 가리키도록 한다(이중 로드 방지).
"""
import importlib as _importlib
import sys as _sys

# bareunpy.bareun 을 최상위 bareun 으로 등록한다.
# 이로써 생성 코드의 `from bareun import X_pb2` 가 bareunpy/bareun/ 디렉터리를
# 탐색하는 것과 같은 효과를 낸다.
_sys.modules.setdefault('bareun', _sys.modules[__name__])

# 서브모듈을 의존성 순서대로 미리 로드한다.
# bareun.X 와 bareunpy.bareun.X 가 항상 같은 객체를 가리키도록
# 양쪽 sys.modules 키에 모두 등록한다.
for _name in (
    # 의존성 없는 공통 메시지 먼저
    'lang_common_pb2',
    'dict_common_pb2',
    # 공통에 의존하는 서비스 메시지
    'language_service_pb2',
    'custom_dict_pb2',
    'revision_service_pb2',
    # Connect 스텁(각 서비스 메시지에 의존)
    'language_service_connect',
    'custom_dict_connect',
    'revision_service_connect',
):
    _mod = _importlib.import_module(f'{__name__}.{_name}')
    # bareun.X 키도 같은 객체로 등록해 이중 로드를 방지한다.
    _sys.modules[f'bareun.{_name}'] = _mod
    # 패키지 속성으로도 노출한다.
    globals()[_name] = _mod

del _importlib, _name, _mod
