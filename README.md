# 📈 Market Intelligence Daily Briefing

매일 KST 08:00에 자동으로 주식 브리핑을 생성하고 Notion에 업로드하는 파이프라인입니다.

## 아키텍처

```
GitHub Actions (cron) 또는 Claude Code
       ↓
main.py  ← 오케스트레이터
  ├── NewsCollector    (Google News RSS + Naver API)
  ├── LLMAnalyzer      (Claude Sonnet → 브리핑 생성)
  ├── NotionUploader   (Notion API → 페이지 생성)
  └── PDFGenerator     (Node.js Puppeteer → PDF)
```

## 빠른 시작

### 1. 의존성 설치

```bash
# Python
pip install -r requirements.txt

# Node.js (PDF 생성용)
npm install
```

### 2. 환경 변수 설정

```bash
cp .env.example .env
# .env 파일을 열어 API 키 입력
```

필요한 키:
| 변수 | 필수 | 설명 |
|------|------|------|
| `ANTHROPIC_API_KEY` | ✅ | [Anthropic Console](https://console.anthropic.com) |
| `NOTION_API_TOKEN` | ✅ | [Notion Integrations](https://notion.so/my-integrations) |
| `NOTION_DATABASE_ID` | ✅ | Notion DB URL에서 추출 |
| `NAVER_CLIENT_ID` | 선택 | Naver 뉴스 API |
| `NAVER_CLIENT_SECRET` | 선택 | Naver 뉴스 API |

### 3. Notion 데이터베이스 준비

Notion에서 새 데이터베이스를 만들고 아래 속성을 추가하세요:

| 속성 이름 | 타입 |
|---------|------|
| Name | 제목 (기본값) |
| Date | 날짜 |
| Keywords | 다중 선택 |
| Articles | 숫자 |

그 다음 Integration을 데이터베이스에 연결 (공유 → 연결 추가).

### 4. 로컬 테스트

```bash
# 미리보기 (API 호출 없음)
python main.py --dry-run

# 실제 실행
python main.py
```

## GitHub Actions 자동화

1. 이 저장소를 GitHub에 push
2. Settings → Secrets → 환경 변수 4개 등록
3. Actions 탭에서 워크플로우 활성화

매일 KST 08:00에 자동 실행됩니다. 수동 실행은 Actions → `Daily Market Briefing` → `Run workflow`.

## 다음 단계 (Phase 2)

- [ ] X (Twitter) API 연동 추가
- [ ] Bull/Bear 히스토리 차트 Notion 페이지에 삽입
- [ ] SEO 블로그 자동 초안 생성 모듈
- [ ] TikTok/Shorts 스크립트 생성 모듈
