#!/bin/bash
# 저장소 루트에서 실행 — WorkPortal은 02_projects/workportal 에 있습니다.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "$ROOT/02_projects/workportal/start.sh"
