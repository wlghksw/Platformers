# CrayonSchool AI HTML 제안서 자동 생성기

GPT-4o를 사용해 다양한 문서(PDF, DOCX, PPTX, TXT, XLSX, MD)를 CrayonSchool 브랜드 디자인의 독립형 HTML 슬라이드로 변환합니다.

## 필수 생성 규칙 (항상 적용)
- **Tag**: 슬라이드 성격 표시 (유치, 초등, SOLUTION, BRAND 등 뱃지용)
- **Title**: 핵심 메시지를 담은 대제목
- **이모지 절대 사용 금지**
- **다크모드 절대 금지 (밝은 아이보리 테마 고정)**

---

## 프로젝트 구조
```
PPT_maker/
├── app.py                  # Flask 메인 서버
├── utils/
│   ├── file_parser.py      # PDF/DOCX/PPTX 텍스트 및 이미지 추출
│   ├── openai_api.py       # GPT-4o API 슬라이드 구조 생성 (Design 주입)
│   └── html_builder.py     # CrayonSchool HTML 빌더
├── templates/
│   └── index.html          # 웹 UI
├── requirements.txt
├── railway.toml            # Railway 배포 설정
└── .env.example
```

---

## 로컬 개발 환경 설정

```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. 환경 변수 설정
cp .env.example .env
# .env 파일에서 ANTHROPIC_API_KEY 설정

# 3. 서버 실행
python app.py
# → http://localhost:5000
```

---

## Railway 배포

### 방법 1: GitHub 연동 (권장)
1. GitHub에 이 프로젝트 push
2. [Railway](https://railway.app) → New Project → Deploy from GitHub
3. 환경 변수 설정:
   - `ANTHROPIC_API_KEY` = `sk-ant-...`
4. 자동 배포 완료

### 방법 2: Railway CLI
```bash
npm install -g @railway/cli
railway login
railway init
railway up

# 환경 변수 설정
railway variables set ANTHROPIC_API_KEY=sk-ant-xxxxx
```

---

## API 엔드포인트

### `POST /api/generate`
PPT 파일 생성 및 다운로드

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `content_file` | File | ✅ | 콘텐츠 문서 (PDF/DOCX/PPTX/TXT) |
| `template_file` | File | ❌ | PPT 양식 템플릿 (.pptx) |
| `instructions` | String | ❌ | 추가 생성 지시사항 |

**응답**: PPTX 파일 (Content-Disposition: attachment)

### `POST /api/preview`
슬라이드 구조만 JSON으로 미리보기 (PPTX 생성 없음)

### `GET /health`
헬스체크

---

## 슬라이드 레이아웃 타입

| 타입 | 용도 |
|------|------|
| `title` | 표지 슬라이드 |
| `content` | 일반 내용 (불릿 포인트) |
| `two_column` | 비교/좌우 대비 |
| `data` | 숫자/통계 강조 |
| `closing` | 마지막 슬라이드 |

---

## 지원 파일 형식

| 용도 | 형식 |
|------|------|
| 콘텐츠 문서 | `.pdf`, `.docx`, `.pptx`, `.txt` |
| 양식 템플릿 | `.pptx` |
