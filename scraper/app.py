"""대본 추출기 — 링크를 붙여넣으면 영상 대본을 보여주는 데스크톱 앱."""

import subprocess
import sys
import threading
from pathlib import Path

import core

BASE = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))


class Api:
    """화면(index.html)에서 호출하는 기능들."""

    def __init__(self):
        self.window = None
        self._job = {"state": "idle"}
        self._lock = threading.Lock()

    def start(self, url, model, browser):
        with self._lock:
            if self._job["state"] == "running":
                return
            self._job = {"state": "running", "stage": "시작하는 중", "ratio": None}
        threading.Thread(target=self._run, args=(url, model, browser), daemon=True).start()

    def _progress(self, stage, ratio):
        self._job.update(stage=stage, ratio=ratio)

    def _run(self, url, model, browser):
        try:
            result = core.extract(url, model, browser, self._progress)
            self._job = {"state": "done", **result}
        except Exception as e:
            self._job = {"state": "error", "error": core.friendly_error(url, e)}

    def status(self):
        return self._job

    def copy(self, text):
        """클립보드에 복사한다. 성공하면 True."""
        if sys.platform != "darwin":
            return False
        subprocess.run(["pbcopy"], input=text.encode("utf-8"), check=True)
        return True

    def save(self, filename, text):
        """저장 위치를 물어보고 .txt로 저장한다."""
        import webview

        dialog = getattr(webview, "FileDialog", None)
        kind = dialog.SAVE if dialog else webview.SAVE_DIALOG
        path = self.window.create_file_dialog(kind, save_filename=filename)
        if not path:
            return False
        path = path if isinstance(path, str) else path[0]
        Path(path).write_text(text, encoding="utf-8")
        return True


def selftest():
    """빌드된 앱 안에서 필요한 부품이 모두 동작하는지 확인한다. (CI에서 사용)"""
    import tempfile
    import wave

    import av  # noqa: F401
    import ctranslate2  # noqa: F401
    import onnxruntime  # noqa: F401
    import webview  # noqa: F401
    import yt_dlp  # noqa: F401

    try:
        import yt_dlp_ejs  # noqa: F401
    except ImportError:
        print("! yt_dlp_ejs 없음")
        return 1
    print("imports ok")

    deno = core.deno_path()
    if not deno:
        print("! deno 없음")
        return 1
    print("deno:", subprocess.run([deno, "--version"], capture_output=True, text=True).stdout.splitlines()[0])

    assert (BASE / "index.html").is_file(), "index.html 없음"

    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / "silence.wav"
        with wave.open(str(wav), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(16000)
            w.writeframes(b"\x00\x00" * 16000 * 2)
        segments = core.transcribe(str(wav), "tiny", lambda *a: None)
    print("whisper ok:", segments)
    return 0


def main():
    if "--selftest" in sys.argv:
        sys.exit(selftest())

    import webview

    api = Api()
    html = (BASE / "index.html").read_text(encoding="utf-8")
    api.window = webview.create_window(
        "대본 추출기", html=html, js_api=api, width=820, height=760, min_size=(520, 560)
    )
    webview.start()


if __name__ == "__main__":
    main()
