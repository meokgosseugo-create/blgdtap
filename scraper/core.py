"""영상 링크 → 오디오 → Whisper → 대본 텍스트 (유튜브, 인스타그램 릴스 등)."""

import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

import yt_dlp

MODELS = {"small": "빠름", "medium": "정확", "large-v3": "가장 정확"}
DEFAULT_MODEL = "small"

if sys.platform == "darwin":
    DATA_DIR = Path.home() / "Library" / "Application Support" / "ScriptGrabber"
else:
    DATA_DIR = Path.home() / ".local" / "share" / "ScriptGrabber"
MODEL_DIR = DATA_DIR / "models"

_whisper_models = {}


def check_url(url):
    if not re.match(r"https?://\S+$", url):
        raise ValueError("영상 링크(https://...)를 붙여넣어 주세요.")


def deno_path():
    """유튜브 다운로드에 필요한 JS 실행기(deno). 앱에 포함된 것을 우선 쓴다."""
    bundled = Path(getattr(sys, "_MEIPASS", "")) / "deno"
    if bundled.is_file():
        return str(bundled)
    return shutil.which("deno")


def ydl_options(url, browser, **extra):
    opts = {"quiet": True, "no_warnings": True, "noprogress": True, "logger": _Silent()}
    if deno := deno_path():
        opts["js_runtimes"] = {"deno": {"path": deno}}
    if "instagram.com" in url and browser:
        opts["cookiesfrombrowser"] = (browser,)
    opts.update(extra)
    return opts


class _Silent:
    def debug(self, msg):
        pass

    warning = error = debug


def download_audio(url, workdir, browser, progress):
    """오디오만 내려받는다. (title, uploader, 파일경로)를 돌려준다."""

    def hook(d):
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            if total:
                progress("오디오 내려받는 중", d["downloaded_bytes"] / total)

    opts = ydl_options(
        url,
        browser,
        format="bestaudio/best",
        outtmpl=str(Path(workdir) / "%(id)s.%(ext)s"),
        progress_hooks=[hook],
    )
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
    return info.get("title"), info.get("uploader") or info.get("channel"), info["requested_downloads"][0]["filepath"]


def get_whisper(name, progress):
    if name not in _whisper_models:
        from faster_whisper import WhisperModel  # 무거우니 필요할 때만 불러온다

        progress("음성인식 모델 준비 중 (처음 한 번만 오래 걸려요)", None)
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        _whisper_models[name] = WhisperModel(
            name, device="cpu", compute_type="int8", cpu_threads=os.cpu_count() or 4, download_root=str(MODEL_DIR)
        )
    return _whisper_models[name]


def transcribe(audio_path, model_name, progress):
    model = get_whisper(model_name, progress)
    segments, info = model.transcribe(
        audio_path, vad_filter=True, condition_on_previous_text=False
    )
    texts = []
    for seg in segments:
        if seg.text.strip():
            texts.append(seg.text.strip())
        if info.duration:
            progress("받아쓰는 중", min(seg.end / info.duration, 1.0))
    return texts


def format_text(segments):
    """문장이 끝나는 곳(. ? !)에서 줄을 바꿔 읽기 좋게 만든다."""
    lines, line = [], []
    for text in segments:
        line.append(text)
        if re.search(r"[.?!。]['\"”’)]*$", text):
            lines.append(" ".join(line))
            line = []
    if line:
        lines.append(" ".join(line))
    return "\n".join(lines)


def extract(url, model_name=DEFAULT_MODEL, browser=None, progress=lambda stage, ratio: None):
    """링크 하나에서 대본을 뽑는다. {'title', 'uploader', 'text'}를 돌려준다."""
    url = url.strip()
    check_url(url)
    progress("영상 확인 중", None)
    with tempfile.TemporaryDirectory() as tmp:
        title, uploader, audio = download_audio(url, tmp, browser, progress)
        segments = transcribe(audio, model_name, progress)
    if not segments:
        raise RuntimeError("영상에서 말소리를 찾지 못했어요. (음악만 있거나 소리가 없는 영상일 수 있어요)")
    return {"title": title, "uploader": uploader, "text": format_text(segments)}


def friendly_error(url, e):
    """에러 메시지를 사람이 이해할 수 있게 바꾼다."""
    msg = str(e)
    low = msg.lower()
    if isinstance(e, (ValueError, RuntimeError)):
        return msg
    if "instagram" in url and any(k in low for k in ("login", "cookie", "keychain", "rate-limit", "restricted")):
        return "인스타 로그인 정보를 읽지 못했어요. 선택한 브라우저에 인스타그램이 로그인되어 있는지 확인하고, 키체인 접근 창이 뜨면 '허용'을 눌러 주세요.\n\n" + msg
    if "sign in to confirm" in low or "not a bot" in low:
        return "유튜브가 요청을 막았어요. 잠시 뒤에 다시 시도해 주세요.\n\n" + msg
    if "private" in low or "unavailable" in low:
        return "비공개이거나 볼 수 없는 영상이에요.\n\n" + msg
    if "urlopen" in low or "connection" in low or "resolve" in low or "timed out" in low:
        return "인터넷 연결을 확인해 주세요.\n\n" + msg
    return msg
