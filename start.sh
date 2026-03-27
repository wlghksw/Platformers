#!/bin/bash
# WorkPortal 원클릭 실행 스크립트
# macOS: 이 파일을 더블클릭하거나 터미널에서 bash start.sh 실행

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT=8787
URL="http://localhost:$PORT"

echo ""
echo "╔══════════════════════════════════════╗"
echo "║       WorkPortal 시작 중...          ║"
echo "╚══════════════════════════════════════╝"
echo ""

# 포트 충돌 확인 후 기존 프로세스 종료
if lsof -ti tcp:$PORT &>/dev/null; then
  echo "⚠️  포트 $PORT 이미 사용 중 → 기존 프로세스 종료..."
  kill "$(lsof -ti tcp:$PORT)" 2>/dev/null || true
  sleep 1
fi

# Python3 확인
if ! command -v python3 &>/dev/null; then
  echo "❌ Python3가 설치되지 않았습니다 (macOS에 기본 설치되어 있습니다)"
  exit 1
fi

echo "🚀 서버 시작 → $URL"
echo "   종료하려면 이 창을 닫거나 Ctrl+C"
echo ""

# 브라우저 자동 오픈 (1초 후)
(sleep 1 && open "$URL") &

# 서버 실행 (server.py 없어도 내장 서버 사용)
cd "$DIR"
if [ -f "server.py" ]; then
  python3 server.py --no-browser
else
  python3 -m http.server $PORT
fi
