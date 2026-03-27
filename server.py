"""
WorkPortal 로컬 서버
표준 라이브러리만 사용 — pip install 불필요
실행: python3 server.py
"""
import http.server
import json
import urllib.request
import urllib.parse
import urllib.error
import ssl
import os
import threading
import webbrowser
import time
from http import HTTPStatus

# ─── 설정 ────────────────────────────────────────────────
PORT = 8787
TOKEN_FILE = os.path.join(os.path.dirname(__file__), ".tokens.json")
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), "credentials.json")

# Google OAuth2 스코프
SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar",
]

# ─── 토큰 관리 ────────────────────────────────────────────
def load_tokens():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE) as f:
            return json.load(f)
    return {}

def save_tokens(data):
    with open(TOKEN_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_credentials():
    if not os.path.exists(CREDENTIALS_FILE):
        return None
    with open(CREDENTIALS_FILE) as f:
        creds = json.load(f)
    web = creds.get("web") or creds.get("installed")
    return web

def refresh_access_token(tokens):
    creds = load_credentials()
    if not creds or "refresh_token" not in tokens:
        return None
    data = urllib.parse.urlencode({
        "client_id": creds["client_id"],
        "client_secret": creds["client_secret"],
        "refresh_token": tokens["refresh_token"],
        "grant_type": "refresh_token",
    }).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data, method="POST")
    try:
        with urllib.request.urlopen(req) as res:
            result = json.loads(res.read())
            tokens["access_token"] = result["access_token"]
            save_tokens(tokens)
            return tokens["access_token"]
    except Exception as e:
        print(f"토큰 갱신 실패: {e}")
        return None

def get_access_token():
    tokens = load_tokens()
    if not tokens.get("access_token"):
        return None
    return tokens.get("access_token")

# ─── Google API 호출 헬퍼 ─────────────────────────────────
def google_api(path, method="GET", body=None, params=None):
    token = get_access_token()
    if not token:
        return {"error": "not_authenticated"}

    url = f"https://www.googleapis.com{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, context=ctx) as res:
            return json.loads(res.read())
    except urllib.error.HTTPError as e:
        body_text = e.read().decode()
        if e.code == 401:
            # 토큰 만료 → 갱신 시도
            tokens = load_tokens()
            new_token = refresh_access_token(tokens)
            if new_token:
                return google_api(path, method, body, params)
        return {"error": f"HTTP {e.code}", "detail": body_text}
    except Exception as e:
        return {"error": str(e)}

# ─── Notion API 호출 ──────────────────────────────────────
def notion_api(path, method="GET", body=None):
    tokens = load_tokens()
    notion_token = tokens.get("notion_token")
    if not notion_token:
        return {"error": "notion_not_configured"}

    url = f"https://api.notion.com/v1{path}"
    headers = {
        "Authorization": f"Bearer {notion_token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, context=ctx) as res:
            return json.loads(res.read())
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}", "detail": e.read().decode()}
    except Exception as e:
        return {"error": str(e)}

# ─── API 라우터 ───────────────────────────────────────────
def handle_api(path, method, body, query):
    # 인증 상태 확인
    if path == "/api/status":
        tokens = load_tokens()
        creds = load_credentials()
        ntn = tokens.get("notion_token", "")
        return {
            "google": bool(tokens.get("access_token")),
            "notion": bool(ntn),
            "credentials": bool(creds),
            "notion_masked": ntn[:10] if ntn else None,
        }

    # 로그아웃 (토큰 삭제)
    if path == "/api/logout" and method == "POST":
        tokens = load_tokens()
        tokens.pop("access_token", None)
        tokens.pop("refresh_token", None)
        save_tokens(tokens)
        return {"ok": True}

    # Notion 토큰 저장
    if path == "/api/notion/token" and method == "POST":
        token = body.get("token", "").strip()
        tokens = load_tokens()
        tokens["notion_token"] = token
        save_tokens(tokens)
        return {"ok": True}

    # ── Gmail ──────────────────────────────────────────────
    if path == "/api/gmail/messages":
        q = query.get("q", ["is:unread newer_than:3d -category:promotions"])[0]
        return google_api("/gmail/v1/users/me/messages",
                          params={"q": q, "maxResults": 10})

    if path == "/api/gmail/message" and method == "GET":
        msg_id = query.get("id", [""])[0]
        return google_api(f"/gmail/v1/users/me/messages/{msg_id}",
                          params={"format": "metadata"})

    if path == "/api/gmail/drafts" and method == "GET":
        return google_api("/gmail/v1/users/me/drafts", params={"maxResults": 5})

    if path == "/api/gmail/draft" and method == "GET":
        draft_id = query.get("id", [""])[0]
        return google_api(f"/gmail/v1/users/me/drafts/{draft_id}")

    if path == "/api/gmail/profile" and method == "GET":
        return google_api("/gmail/v1/users/me/profile")

    if path == "/api/gmail/draft" and method == "POST":
        to = body.get("to", "")
        subject = body.get("subject", "")
        content = body.get("body", "")
        raw = _build_email(to, subject, content)
        return google_api("/gmail/v1/users/me/drafts", method="POST",
                          body={"message": {"raw": raw}})

    # ── Calendar ───────────────────────────────────────────
    if path == "/api/calendar/events" and method == "GET":
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat()
        end = query.get("timeMax", [None])[0]
        params = {"timeMin": now, "maxResults": 10,
                  "singleEvents": "true", "orderBy": "startTime"}
        if end:
            params["timeMax"] = end
        return google_api("/calendar/v3/calendars/primary/events", params=params)

    if path == "/api/calendar/event" and method == "POST":
        event = {
            "summary": body.get("title", ""),
            "description": body.get("description", ""),
            "start": {"dateTime": body.get("start"), "timeZone": "Asia/Seoul"},
            "end":   {"dateTime": body.get("end"),   "timeZone": "Asia/Seoul"},
            "reminders": {"useDefault": False,
                          "overrides": [{"method": "popup", "minutes": 30}]},
        }
        return google_api("/calendar/v3/calendars/primary/events",
                          method="POST", body=event)

    # ── Notion ─────────────────────────────────────────────
    if path == "/api/notion/search" and method == "GET":
        q = query.get("q", [""])[0]
        return notion_api("/search", method="POST", body={"query": q, "page_size": 5})

    if path == "/api/notion/page" and method == "POST":
        return notion_api("/pages", method="POST", body=body)

    # ── 문서 생성 (AI 없이 템플릿 기반) ──────────────────────
    if path == "/api/docs/generate" and method == "POST":
        template = body.get("template", "")
        content = body.get("content", "")
        from datetime import date
        today = date.today().strftime("%Y년 %m월 %d일")
        result = _generate_doc(template, content, today)
        return {"result": result}

    return {"error": "not_found"}

def _build_email(to, subject, body_text):
    import base64
    msg = f"From: me\r\nTo: {to}\r\nSubject: {subject}\r\nContent-Type: text/plain; charset=utf-8\r\n\r\n{body_text}"
    return base64.urlsafe_b64encode(msg.encode("utf-8")).decode("utf-8")

def _generate_doc(template, content, today):
    templates = {
        "주간 업무 보고서": f"""[주간 업무 보고서]
작성일: {today}  |  작성자: 최지환

■ 이번 주 완료 업무
{content}

■ 다음 주 계획
• 이번 주 연속 업무 진행
• 주요 이슈 후속 조치

■ 특이사항
• 없음""",
        "회의록": f"""[회의록]
일시: {today}  |  작성자: 최지환

■ 안건
{content}

■ 논의 내용
• 안건별 의견 공유 및 협의

■ 결정 사항
• (작성 필요)

■ 다음 액션
• 담당자 / 기한: 1주일 이내""",
        "이메일 초안": f"""안녕하세요,

아래 내용으로 연락드립니다.

{content}

확인 후 회신 부탁드립니다.
감사합니다.

최지환 드림""",
        "프로젝트 리포트": f"""[프로젝트 현황 리포트]
작성일: {today}  |  작성자: 최지환

■ 프로젝트 개요
{content}

■ 현재 진행 상황
• 진행 중 항목 정리 필요

■ 이슈 및 리스크
• 없음

■ 다음 마일스톤
• (작성 필요)"""
    }
    return templates.get(template, f"[{template}]\n{today}\n\n{content}")


# ─── HTTP 요청 핸들러 ─────────────────────────────────────
PORTAL_HTML = os.path.join(os.path.dirname(__file__), "index.html")

class WorkPortalHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # 로그 최소화

    def do_OPTIONS(self):
        self._cors()
        self.send_response(HTTPStatus.NO_CONTENT)
        self.end_headers()

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self._cors()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length:
            return json.loads(self.rfile.read(length))
        return {}

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # OAuth 시작 (포털 버튼에서 호출)
        if path == "/oauth/start":
            creds = load_credentials()
            if not creds:
                self._json({"error": "credentials.json 파일이 없습니다. README_설정가이드.md 참고"}, 400)
                return
            params = urllib.parse.urlencode({
                "client_id": creds["client_id"],
                "redirect_uri": f"http://localhost:{PORT}/oauth/callback",
                "response_type": "code",
                "scope": " ".join(SCOPES),
                "access_type": "offline",
                "prompt": "consent",
            })
            auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{params}"
            self._json({"auth_url": auth_url})
            return

        # OAuth 콜백
        if path == "/oauth/callback":
            self._handle_oauth_callback(query)
            return

        # API
        if path.startswith("/api/"):
            result = handle_api(path, "GET", {}, query)
            self._json(result)
            return

        # 포털 HTML 서빙
        if path in ("/", "/index.html"):
            path = PORTAL_HTML
        else:
            path = os.path.join(os.path.dirname(__file__), path.lstrip("/"))

        if os.path.isfile(path):
            with open(path, "rb") as f:
                content = f.read()
            self.send_response(200)
            ct = "text/html" if path.endswith(".html") else "text/plain"
            self.send_header("Content-Type", ct)
            self.end_headers()
            self.wfile.write(content)
        else:
            self._json({"error": "not found"}, 404)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        body = self._read_body()
        if path.startswith("/api/"):
            result = handle_api(path, "POST", body, {})
            self._json(result)
        else:
            self._json({"error": "not found"}, 404)

    def _handle_oauth_callback(self, query):
        code = query.get("code", [None])[0]
        if not code:
            self._send_html("<h2>인증 실패</h2>")
            return

        creds = load_credentials()
        if not creds:
            self._send_html("<h2>credentials.json 없음</h2>")
            return

        # 코드 → 토큰 교환
        data = urllib.parse.urlencode({
            "code": code,
            "client_id": creds["client_id"],
            "client_secret": creds["client_secret"],
            "redirect_uri": f"http://localhost:{PORT}/oauth/callback",
            "grant_type": "authorization_code",
        }).encode()

        ctx = ssl.create_default_context()
        req = urllib.request.Request(
            "https://oauth2.googleapis.com/token", data=data, method="POST")
        try:
            with urllib.request.urlopen(req, context=ctx) as res:
                tokens = json.loads(res.read())
                save_tokens(tokens)
                # 포털로 리디렉트 (성공 신호 포함)
                self.send_response(302)
                self._cors()
                self.send_header("Location", f"http://localhost:{PORT}/?google=ok")
                self.end_headers()
        except Exception as e:
            self._send_html(f"<h2>오류: {e}</h2>")

    def _send_html(self, html):
        body = html.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)


# ─── OAuth 시작 ───────────────────────────────────────────
def start_oauth():
    creds = load_credentials()
    if not creds:
        print("❌ credentials.json 파일이 없습니다. README를 참고해 설정해 주세요.")
        return
    params = urllib.parse.urlencode({
        "client_id": creds["client_id"],
        "redirect_uri": f"http://localhost:{PORT}/oauth/callback",
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent",
    })
    url = f"https://accounts.google.com/o/oauth2/v2/auth?{params}"
    print(f"🌐 브라우저에서 Google 로그인 창이 열립니다...")
    webbrowser.open(url)


# ─── 서버 시작 ────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    print("=" * 50)
    print("  WorkPortal 서버")
    print(f"  http://localhost:{PORT}")
    print("=" * 50)

    tokens = load_tokens()
    creds = load_credentials()

    if not creds:
        print("\n⚠️  Google 연동 설정이 필요합니다.")
        print("  → README_설정가이드.md 를 먼저 읽어주세요.\n")
    elif not tokens.get("access_token"):
        print("\n🔑 Google 인증이 필요합니다. 브라우저 창이 열립니다...")
        # 서버가 먼저 시작된 뒤 OAuth 실행
        threading.Timer(1.5, start_oauth).start()
    else:
        print("\n✅ Google 연동 완료")

    notion_token = tokens.get("notion_token")
    if notion_token:
        print("✅ Notion 연동 완료")
    else:
        print("⚠️  Notion: 설정 페이지에서 토큰을 입력해주세요")

    print(f"\n🚀 서버 시작 → http://localhost:{PORT} 열기\n")

    # 서버 시작 + 브라우저 자동 열기
    if "--no-browser" not in sys.argv:
        threading.Timer(1.0, lambda: webbrowser.open(f"http://localhost:{PORT}")).start()

    with http.server.ThreadingHTTPServer(("", PORT), WorkPortalHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n서버 종료")
