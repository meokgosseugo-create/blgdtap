#!/bin/bash
# 더블클릭하면 브라우저에 대본 추출기 화면이 열린다.
# 처음 실행할 때 uv(파이썬 실행 도구)를 설치하고, 필요한 파이썬과 패키지는 uv가 알아서 받는다.

cd "$(dirname "$0")" || exit 1
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"

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

if ! command -v ffmpeg >/dev/null 2>&1; then
    echo
    echo "참고: ffmpeg가 없어서 인스타 릴스 등 '음성인식'이 필요한 영상은 실패할 수 있어요."
    echo "      (유튜브 자막이 있는 영상은 괜찮습니다) 필요하면 터미널에 'brew install ffmpeg' 입력."
fi

uv run app.py
echo
read -r -p "종료되었습니다. 엔터를 누르면 창이 닫힙니다."
