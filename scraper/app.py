#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "youtube-transcript-api>=1.2",
#     "yt-dlp>=2026.8.19",
#     "faster-whisper>=1.1",
# ]
# ///
"""대본 추출기 웹 화면. 내 컴퓨터(127.0.0.1)에서만 열리며 외부에 공개되지 않는다.

    uv run app.py      → 브라우저가 자동으로 열린다
"""

import json
import sys
import threading
import uuid
import webbrowser
from argparse import Namespace
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import transcript as T

HOST, PORT = "127.0.0.1", 8765
PAGE = (Path(__file__).parent / "index.html").read_text(encoding="utf-8")

jobs = {}  # job_id -> {"status": "running"|"done"|"error", "log": str, "result": dict, "error": str}
whisper_lock = threading.Lock()  # 음성인식은 한 번에 하나씩만


def make_args(browser):
    return Namespace(
        cookies_from_browser=browser or None,
        cookies=None,
        lang=["ko", "en"],
        whisper_lang="ko",
        model="small",
        force_whisper=False,
    )


def run_job(job_id, url, browser):
    job = jobs[job_id]

    def log(msg):
        job["log"] = msg.strip(" ·")

    try:
        with whisper_lock:
            record = T.extract(url, make_args(browser), log)
        record["text"] = T.format_text(record)
        record["text_timestamps"] = T.format_text(record, timestamps=True)
        record["script_timestamps"] = "\n".join(f"[{T.fmt_time(x['start'])}] {x['text']}" for x in record["segments"])
        job["result"] = record
        job["status"] = "done"
    except Exception as e:
        job["error"] = friendly_error(url, e)
        job["status"] = "error"


def friendly_error(url, e):
    msg = str(e)
    if isinstance(e, ValueError):
        return msg
    if "instagram" in url and ("login" in msg.lower() or "cookies" in msg.lower() or "rate" in msg.lower()):
        return "인스타 로그인 정보를 읽지 못했어요. 선택한 브라우저에 인스타그램이 로그인되어 있는지 확인해 주세요.\n\n" + msg
    if "ffmpeg" in msg.lower():
        return "ffmpeg가 필요합니다. 터미널에서 `brew install ffmpeg` 후 다시 시도해 주세요.\n\n" + msg
    return msg


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):  # 터미널 로그 조용히
        pass

    def send_json(self, data, code=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/":
            body = PAGE.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path.startswith("/api/status/"):
            job = jobs.get(self.path.rsplit("/", 1)[-1])
            self.send_json(job or {"status": "error", "error": "작업을 찾을 수 없어요"}, 200 if job else 404)
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path != "/api/extract":
            return self.send_error(404)
        # 다른 웹사이트가 내 컴퓨터의 이 주소로 요청을 보내는 것을 막는다.
        if self.headers.get("Host", "").split(":")[0] not in ("127.0.0.1", "localhost"):
            return self.send_error(403)
        try:
            payload = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
            url = payload["url"].strip()
            T.detect_platform(url)
        except (ValueError, KeyError) as e:
            return self.send_json({"error": str(e) if isinstance(e, ValueError) and "URL" in str(e) else "주소를 확인해 주세요"}, 400)
        job_id = uuid.uuid4().hex
        jobs[job_id] = {"status": "running", "log": "시작하는 중..."}
        threading.Thread(target=run_job, args=(job_id, url, payload.get("browser")), daemon=True).start()
        self.send_json({"job_id": job_id})


def main():
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    url = f"http://{HOST}:{PORT}"
    print(f"대본 추출기가 열렸습니다: {url}")
    print("이 창을 닫으면 프로그램이 종료됩니다.")
    threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    sys.exit(main())
