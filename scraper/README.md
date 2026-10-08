# 대본 추출기

유튜브 · 인스타 릴스 링크를 붙여넣으면 영상 속 말을 Whisper로 받아써서 보여주는 맥 프로그램입니다.
복사하거나 `.txt`로 저장할 수 있어요. 모든 처리는 내 맥 안에서 이뤄집니다.

## 설치 (Apple Silicon 맥: M1 · M2 · M3 · M4)

1. 다운로드: https://github.com/meokgosseugo-create/blgdtap/releases/download/latest/ScriptGrabber-mac.zip
2. ZIP을 더블클릭해 풀면 **대본 추출기** 앱이 나옵니다. **응용 프로그램** 폴더로 옮기세요.
3. 더블클릭하면 "열 수 없음" 경고가 뜹니다. (애플 인증을 받지 않은 앱이라 처음 한 번만 뜹니다)
   **완료** → **시스템 설정 → 개인정보 보호 및 보안** 맨 아래 **"그래도 열기"** → 비밀번호 입력.

## 사용법

1. 앱을 열고 영상 링크를 붙여넣은 뒤 **대본 가져오기**.
2. 끝나면 **대본 복사** 또는 **.txt로 저장**.

- **정확도**: 빠름 < 정확(기본) < 가장 정확. 높을수록 정확하지만 오래 걸립니다.
  처음 한 번 모델을 내려받아요 (빠름 0.5GB · 정확 1.5GB · 가장 정확 3GB).
- **인스타**: 선택한 브라우저(기본 크롬)에 인스타그램이 로그인되어 있어야 합니다.
  처음에 "키체인 접근" 창이 뜨면 **허용**.

## 개발자용

- `core.py` 다운로드(yt-dlp) + 음성인식(faster-whisper), `app.py` 앱 창(pywebview), `index.html` 화면.
- 맥 앱은 `.github/workflows/build-mac.yml`이 GitHub에서 자동으로 만들어 Releases(`latest`)에 올립니다.
- 직접 실행: `pip install -r requirements.txt && python app.py`
