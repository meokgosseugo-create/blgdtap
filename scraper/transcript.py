#!/usr/bin/env python3
"""유튜브 / 인스타그램 영상 대본 추출기.

사용법:
    python transcript.py <URL> [<URL> ...]
    python transcript.py -f urls.txt
    python transcript.py <인스타 URL> --cookies-from-browser chrome

동작 순서:
    1. 유튜브면 업로드된 자막(수동 → 자동 생성)을 먼저 가져온다.
    2. 자막이 없거나 인스타그램이면 yt-dlp로 오디오를 받아 Whisper로 받아쓴다.
    3. output/ 폴더에 <플랫폼>_<영상ID>.txt 와 .json 으로 저장한다.
"""

import argparse
import json
import re
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import yt_dlp
from youtube_transcript_api import CouldNotRetrieveTranscript, YouTubeTranscriptApi

YOUTUBE_ID_RE = re.compile(
    r"(?:youtube\.com/(?:watch\?(?:.*&)?v=|shorts/|embed/|live/)|youtu\.be/)([A-Za-z0-9_-]{11})"
)
INSTAGRAM_RE = re.compile(r"instagram\.com/(?:[^/]+/)?(?:p|reel|reels|tv)/([A-Za-z0-9_-]+)")


def detect_platform(url):
    """URL을 보고 (플랫폼, 영상ID)를 돌려준다."""
    if m := YOUTUBE_ID_RE.search(url):
        return "youtube", m.group(1)
    if m := INSTAGRAM_RE.search(url):
        return "instagram", m.group(1)
    raise ValueError(f"유튜브/인스타그램 URL이 아닙니다: {url}")


class _QuietLogger:
    """yt-dlp 에러는 예외로 받아 직접 출력하므로 중복 출력을 막는다."""

    def debug(self, msg):
        pass

    warning = error = debug


def ydl_options(args, **extra):
    opts = {"quiet": True, "no_warnings": True, "noprogress": True, "logger": _QuietLogger()}
    if args.cookies_from_browser:
        opts["cookiesfrombrowser"] = (args.cookies_from_browser,)
    if args.cookies:
        opts["cookiefile"] = args.cookies
    opts.update(extra)
    return opts


def fetch_metadata(url, args):
    """제목, 채널, 게시글 설명 등을 가져온다. 실패해도 대본 추출은 계속한다."""
    try:
        with yt_dlp.YoutubeDL(ydl_options(args)) as ydl:
            info = ydl.extract_info(url, download=False)
    except yt_dlp.utils.DownloadError as e:
        print(f"  ! 메타데이터를 가져오지 못했습니다: {e}", file=sys.stderr)
        return {}
    return {
        "title": info.get("title"),
        "uploader": info.get("uploader") or info.get("channel"),
        "upload_date": info.get("upload_date"),
        "duration": info.get("duration"),
        "description": info.get("description"),
    }


def youtube_captions(video_id, languages):
    """유튜브에 올라와 있는 자막을 가져온다. 없으면 None."""
    api = YouTubeTranscriptApi()
    try:
        transcript = api.fetch(video_id, languages=languages)
    except CouldNotRetrieveTranscript:
        # 원하는 언어가 없으면 아무 언어 자막이라도 가져온다.
        try:
            transcript = next(iter(api.list(video_id))).fetch()
        except (CouldNotRetrieveTranscript, StopIteration):
            return None
    segments = [
        {"start": round(s.start, 2), "end": round(s.start + s.duration, 2), "text": s.text.strip()}
        for s in transcript
        if s.text.strip()
    ]
    return {"source": f"captions ({transcript.language_code})", "segments": segments}


def download_audio(url, workdir, args):
    """오디오만 내려받고 파일 경로를 돌려준다."""
    opts = ydl_options(args, format="bestaudio/best", outtmpl=str(Path(workdir) / "%(id)s.%(ext)s"))
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
    return info["requested_downloads"][0]["filepath"]


_whisper_model = None


def whisper_transcribe(audio_path, args):
    global _whisper_model
    from faster_whisper import WhisperModel  # 무거우니 필요할 때만 불러온다

    if _whisper_model is None:
        print(f"  · Whisper 모델 로딩 ({args.model}) — 처음엔 다운로드로 시간이 걸립니다")
        _whisper_model = WhisperModel(args.model, device="auto", compute_type="int8")
    language = None if args.whisper_lang == "auto" else args.whisper_lang
    segments, info = _whisper_model.transcribe(audio_path, language=language, vad_filter=True)
    result = []
    for seg in segments:
        result.append({"start": round(seg.start, 2), "end": round(seg.end, 2), "text": seg.text.strip()})
        print(f"\r  · 받아쓰는 중... {seg.end:.0f}초", end="", flush=True)
    print()
    return {"source": f"whisper-{args.model} ({info.language})", "segments": result}


def process(url, args):
    platform, video_id = detect_platform(url)
    print(f"[{platform}] {url}")

    meta = fetch_metadata(url, args)

    transcript = None
    if platform == "youtube" and not args.force_whisper:
        transcript = youtube_captions(video_id, args.lang)
        if transcript is None:
            print("  · 자막이 없어 음성인식으로 진행합니다")

    if transcript is None:
        with tempfile.TemporaryDirectory() as tmp:
            print("  · 오디오 다운로드 중...")
            audio = download_audio(url, tmp, args)
            transcript = whisper_transcribe(audio, args)

    full_text = " ".join(s["text"] for s in transcript["segments"])
    record = {
        "url": url,
        "platform": platform,
        "id": video_id,
        **meta,
        "transcript_source": transcript["source"],
        "transcript": full_text,
        "segments": transcript["segments"],
        "fetched_at": datetime.now().isoformat(timespec="seconds"),
    }

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = out_dir / f"{platform}_{video_id}"
    stem.with_suffix(".json").write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")

    header = [f"제목: {meta.get('title') or '-'}", f"채널: {meta.get('uploader') or '-'}", f"URL: {url}"]
    if meta.get("description"):
        header.append(f"\n[게시글 설명]\n{meta['description']}")
    lines = [f"[{fmt_time(s['start'])}] {s['text']}" for s in transcript["segments"]] if args.timestamps else [full_text]
    stem.with_suffix(".txt").write_text("\n".join(header) + "\n\n[대본]\n" + "\n".join(lines) + "\n", encoding="utf-8")

    print(f"  ✓ 저장: {stem}.txt / .json ({transcript['source']}, {len(full_text)}자)")


def fmt_time(seconds):
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def main():
    p = argparse.ArgumentParser(description="유튜브/인스타그램 영상 대본 추출기")
    p.add_argument("urls", nargs="*", help="영상 URL (여러 개 가능)")
    p.add_argument("-f", "--file", help="URL 목록 파일 (한 줄에 하나, #은 주석)")
    p.add_argument("-o", "--output", default="output", help="저장 폴더 (기본: output)")
    p.add_argument("--lang", nargs="+", default=["ko", "en"], help="유튜브 자막 우선 언어 (기본: ko en)")
    p.add_argument("--whisper-lang", default="ko", help="음성인식 언어 (기본: ko, 자동감지: auto)")
    p.add_argument("--model", default="small", help="Whisper 모델: tiny/base/small/medium/large-v3 (기본: small)")
    p.add_argument("--force-whisper", action="store_true", help="유튜브 자막이 있어도 음성인식 사용")
    p.add_argument("--timestamps", action="store_true", help="txt에 타임스탬프 포함")
    p.add_argument("--cookies-from-browser", metavar="BROWSER", help="브라우저 로그인 쿠키 사용 (chrome, safari 등) — 인스타용")
    p.add_argument("--cookies", metavar="FILE", help="cookies.txt 파일 경로")
    args = p.parse_args()

    urls = list(args.urls)
    if args.file:
        for line in Path(args.file).read_text(encoding="utf-8").splitlines():
            if (line := line.strip()) and not line.startswith("#"):
                urls.append(line)
    if not urls:
        p.error("URL을 하나 이상 입력하세요")

    failed = []
    for url in urls:
        try:
            process(url, args)
        except Exception as e:  # 한 개가 실패해도 나머지는 계속 처리
            print(f"  ✗ 실패: {e}", file=sys.stderr)
            failed.append(url)

    print(f"\n완료: {len(urls) - len(failed)}/{len(urls)}")
    if failed:
        print("실패한 URL:\n  " + "\n  ".join(failed), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
