#!/bin/bash
# 더블클릭으로 실행하는 맥용 대본 추출기.
# 처음 실행할 때 uv(파이썬 실행 도구)를 설치하고, 필요한 파이썬과 패키지는 uv가 알아서 받는다.

cd "$(dirname "$0")" || exit 1
export PATH="$HOME/.local/bin:$PATH"

echo "=============================="
echo "  유튜브 / 인스타 대본 추출기"
echo "=============================="

if ! command -v uv >/dev/null 2>&1; then
    echo
    echo "처음 실행이라 준비 중입니다 (1~2분)..."
    if ! curl -LsSf https://astral.sh/uv/install.sh | sh; then
        echo "설치에 실패했습니다. 인터넷 연결을 확인하고 다시 실행해 주세요."
        read -r -p "엔터를 누르면 창이 닫힙니다."
        exit 1
    fi
fi

# 인스타는 로그인이 필요해서 크롬에 로그인된 정보를 쓴다.
COOKIE_ARGS=()
if [ -d "/Applications/Google Chrome.app" ]; then
    COOKIE_ARGS=(--cookies-from-browser chrome)
fi

while true; do
    echo
    echo "영상 주소(URL)를 붙여넣고 엔터 (여러 개는 띄어쓰기로 구분, 끝내려면 그냥 엔터)"
    read -r -p "> " -a URLS
    [ ${#URLS[@]} -eq 0 ] && break

    ARGS=()
    for u in "${URLS[@]}"; do
        if [[ "$u" == *instagram.com* ]]; then
            ARGS=("${COOKIE_ARGS[@]}")
            break
        fi
    done

    uv run transcript.py "${URLS[@]}" "${ARGS[@]}"
    [ -d output ] && open output
done

echo "종료합니다."
