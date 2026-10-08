# 영상 대본 추출기 (유튜브 / 인스타그램)

URL을 넣으면 영상 대본을 `.txt`와 `.json`으로 저장합니다.

- **유튜브**: 올라와 있는 자막을 바로 가져옵니다 (빠름). 자막이 없으면 음성인식.
- **인스타 릴스**: 오디오를 받아서 음성인식(Whisper)으로 받아씁니다.

> 내 컴퓨터(맥)에서 실행하세요. 클라우드 서버는 유튜브/인스타가 차단하는 경우가 많습니다.

## 맥 설치 (처음 한 번만)

터미널을 열고:

```bash
# 1) 레포 받기 (이미 받았다면 생략)
git clone https://github.com/meokgosseugo-create/blgdtap.git
cd blgdtap/scraper

# 2) 가상환경 만들고 패키지 설치
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

`python3`가 없다고 나오면 먼저 `xcode-select --install` 또는 [python.org](https://www.python.org/downloads/macos/)에서 설치하세요.

## 사용법

터미널을 새로 열 때마다 먼저:

```bash
cd blgdtap/scraper
source .venv/bin/activate
```

그다음:

```bash
# 유튜브 하나
python transcript.py "https://www.youtube.com/watch?v=영상ID"

# 여러 개 한꺼번에
python transcript.py "URL1" "URL2" "URL3"

# 파일에 URL을 한 줄씩 적어두고 한꺼번에
python transcript.py -f urls.txt

# 인스타 릴스 (크롬에 인스타 로그인 되어 있어야 함)
python transcript.py "https://www.instagram.com/reel/XXXX/" --cookies-from-browser chrome
```

결과는 `output/` 폴더에 `youtube_영상ID.txt`, `youtube_영상ID.json` 형태로 저장됩니다.
`.txt`에는 제목, 채널, 게시글 설명, 대본이 들어가고 `.json`에는 구간별 타임스탬프까지 들어갑니다.

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
- 오류가 나면 먼저 `pip install -U yt-dlp`로 업데이트해 보세요. 유튜브/인스타가 자주 바뀌어서 업데이트로 해결되는 경우가 많습니다.
- 대본은 참고·분석용으로 쓰고, 남의 대본을 그대로 게시하지 마세요 (저작권).
