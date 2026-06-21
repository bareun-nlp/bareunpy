#!/usr/bin/env bash
#
# gen_proto.sh — 현재 bareun protos 에서 bareunpy 의 `bareun/` 패키지를 재생성한다.
#
# bareunpy 는 메시지(*_pb2)와 공식 Connect 스텁(*_connect.py)을 패키지에 동봉한다(=vendoring).
# proto 가 바뀌면 이 스크립트로 다시 생성해 커밋한다.
#
# 사전 준비:
#   1) buf 설치 (https://buf.build)
#   2) 별도 플러그인 설치 불필요 — buf 원격 플러그인(buf.build/connectrpc/python 등)을 사용한다.
#
# 사용법:
#   BAREUN_PROTOS=/path/to/baikal-nlp/protos tools/gen_proto.sh
#   # 또는 기본값(모노레포가 ../bareun 에 있다고 가정):
#   tools/gen_proto.sh
#
set -euo pipefail

# bareunpy 저장소 루트(이 스크립트의 상위 디렉토리)
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# bareun 모노레포의 protos 디렉토리. 환경변수로 덮어쓸 수 있다.
PROTOS="${BAREUN_PROTOS:-$ROOT/../bareun/protos}"

if [ ! -d "$PROTOS/bareun" ]; then
  echo "ERROR: protos 디렉토리를 찾을 수 없습니다: $PROTOS" >&2
  echo "       BAREUN_PROTOS 환경변수로 baikal-nlp/protos 경로를 지정하세요." >&2
  exit 1
fi

# 생성 대상 proto 목록(서비스/메시지). gointernal 등 서버 내부 전용은 제외한다.
PATHS=(
  bareun/lang_common.proto
  bareun/dict_common.proto
  bareun/language_service.proto
  bareun/custom_dict.proto
  bareun/revision_service.proto
)

# buf 의 --path 는 CWD 기준으로 해석되므로 protos 디렉토리에서 실행한다.
# 커밋된 buf.gen.yaml 은 out: . (상대) 이지만, protos 디렉토리에서 실행하면 out 이 protos 를
# 가리키게 되므로, out 을 bareunpy 루트(ROOT, 절대경로)로 치환한 임시 템플릿을 만들어 사용한다.
TMP_TEMPLATE="$(mktemp -t bareunpy-buf-gen.XXXXXX.yaml)"
trap 'rm -f "$TMP_TEMPLATE"' EXIT
sed "s#^\( *out: \)\.#\1$ROOT#" "$ROOT/buf.gen.yaml" > "$TMP_TEMPLATE"

ARGS=()
for p in "${PATHS[@]}"; do
  ARGS+=(--path "$p")
done

echo "generating bareun/ stubs from: $PROTOS"
( cd "$PROTOS" && buf generate . --template "$TMP_TEMPLATE" "${ARGS[@]}" )

# 생성된 패키지가 import 가능하도록 __init__.py / py.typed 를 보장한다.
touch "$ROOT/bareun/__init__.py" "$ROOT/bareun/py.typed"

echo "done. 'bareun/' 패키지가 갱신되었습니다. git diff 로 변경을 확인하세요."
