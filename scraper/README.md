# 영상 대본 추출기 (유튜브 / 인스타그램)

URL을 넣으면 영상 대본을 `.txt`와 `.json`으로 저장합니다.

- **유튜브**: 올라와 있는 자막을 바로 가져옵니다 (빠름). 자막이 없으면 음성인식.
- **인스타 릴스**: 오디오를 받아서 음성인식(Whisper)으로 받아씁니다.

> 내 컴퓨터(맥)에서 실행하세요. 클라우드 서버는 유튜브/인스타가 차단하는 경우가 많습니다.

## 맥에서 쉽게 쓰기 (터미널 몰라도 됨)

1. **다운로드:** 아래 링크를 누르면 ZIP 파일이 받아집니다.
   https://github.com/meokgosseugo-create/blgdtap/archive/refs/heads/claude/youtube-instagram-script-scraper-4myj0a.zip
2. 다운로드 폴더에서 ZIP을 더블클릭해 압축을 풀고, 안의 `scraper` 폴더를 원하는 곳(예: 바탕화면)에 둡니다.
3. `scraper` 폴더 안의 **`대본추출.command`** 를 더블클릭합니다.
   - "확인되지 않은 개발자" 경고가 뜨면: **시스템 설정 → 개인정보 보호 및 보안** 맨 아래의 **"그래도 열기"** 를 누른 뒤 다시 더블클릭하세요. (처음 한 번만)
4. 처음 실행할 때는 필요한 프로그램을 자동으로 설치합니다 (몇 분 걸림). 그다음부터는 바로 시작합니다.
5. 영상 주소를 붙여넣고 엔터 → 끝나면 결과 폴더(`output`)가 자동으로 열립니다.
   - 여러 개는 띄어쓰기로 구분해서 한 번에 붙여넣으면 됩니다.
   - 끝내려면 아무것도 입력하지 않고 엔터.

인스타 릴스는 **크롬에 인스타그램이 로그인되어 있어야** 합니다. 처음에 "키체인 접근 허용" 창이 뜨면 "허용"을 누르세요.

## 터미널로 직접 쓰기 (고급)

```bash
cd scraper
uv run transcript.py "https://www.youtube.com/watch?v=영상ID"
uv run transcript.py -f urls.txt                         # 파일에 URL 한 줄씩
uv run transcript.py "인스타 URL" --cookies-from-browser chrome
```

uv 대신 일반 파이썬(3.10 이상)을 쓰려면 `pip install -r requirements.txt` 후 `python transcript.py ...`.

## 옵션

| 옵션 | 설명 |
|---|---|
| `--timestamps` | txt에 `[01:23]` 같은 시간 표시 포함 |
| `--model small` | Whisper 모델 크기. `tiny` < `base` < `small`(기본) < `medium` < `large-v3` — 클수록 정확하지만 느림 |
| `--whisper-lang auto` | 음성인식 언어 자동감지 (기본은 한국어 `ko`) |
| `--lang ko en` | 유튜브 자막 우선 언어 |
| `--force-whisper` | 유튜브 자막이 있어도 음성인식 사용 (자동자막 품질이 나쁠 때) |
| `--cookies-from-browser chrome` | 브라우저 로그인 정보 사용 (`chrome`, `safari`, `firefox` 등) |
| `-o 폴더` | 저장 폴더 변경 |

## 참고

- 음성인식을 처음 쓸 때 Whisper 모델을 내려받느라 1~2분 걸립니다 (`small` 약 500MB). 그 뒤로는 바로 시작합니다.
- `--cookies-from-browser`를 처음 쓰면 맥이 키체인 접근 허용을 물어볼 수 있습니다 → "허용".
- 오류가 나면 최신 버전으로 받으면 해결되는 경우가 많습니다 (유튜브/인스타가 자주 바뀜).
- 대본은 참고·분석용으로 쓰고, 남의 대본을 그대로 게시하지 마세요 (저작권).
