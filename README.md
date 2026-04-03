# 🤖 AI Naver Blog Automatic Generator (Platformers)

이 프로젝트는 **Claude 3.5 Sonnet API**와 연동하여, 사용자가 입력한 기획안(단어/문장), 업로드한 참고 문서(PDF, PPT, Word 등), 그리고 원본 웹사이트(링크 스크래핑) 등을 종합적으로 분석하여 **네이버 블로그 스마트에디터 양식에 100% 최적화된 블로그 HTML 코드를 원클릭으로 자동 생성**해 주는 파이프라인입니다.

---

## ✨ 주요 기능 (Key Features)

1. **다중 컨텍스트 입력 지원**
   - **웹 스크래핑**: URL 링크 하나만 입력하면 백엔드에서 원본 기사나 홈페이지를 자동으로 읽어와 핵심 문구를 추출합니다. (`BeautifulSoup` 기반 크롤링)
   - **문서 및 이미지 업로드**: PPTX, DOCX, PDF, JPG/PNG 형식의 기획안 파일을 던져 넣으면 서버에서 텍스트와 비전을 파싱해 AI에게 전달합니다. 

2. **완벽한 네이버 블로그 템플릿 호환**
   - 밋밋한 텍스트가 아닌, 가독성이 극대화된 [이러닝 교안강의] 스타일의 블로그 코드를 렌더링합니다.
   - 키워드 주황색(#ff8c00) 오토 하이라이팅, 가운데 정렬, 인용구(Quote) 디자인, 핵심 정보 요약 테이블이 알아서 적용됩니다.

3. **2-Step 찰떡 이미지 에디터 (수동 배치 파이프라인)**
   - AI가 글만 우선 생성하고 나면 프론트엔드 하단에 **[수동 이미지 배치 에디터]**가 열립니다.
   - 내가 원하는 타이밍의 문단 바로 아래에 업로드했던 사진들을 골라서 자유자재로 끼워 넣고, 최종적으로 완벽한 HTML 파일을 구워낼 수 있습니다.

---

## 🛠️ 기술 스택 (Tech Stack)

### Frontend
- **Framework**: Next.js (React)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Features**: 파일 Drag & Drop 업로드, 비동기 상태 관리, 동적 문단 별 이미지 배치 에디터

### Backend
- **Framework**: FastAPI (Python 3)
- **AI Integration**: Anthropic Claude API (`claude-3-5-sonnet-20241022`)
- **Web Scraping**: `requests`, `beautifulsoup4`
- **Document Parsing**: `python-pptx`, `python-docx`, `pdfplumber`

---

## 🚀 설치 및 로컬 실행 방법 (Getting Started)

이 프로젝트는 Frontend와 Backend 서버를 동시에 띄워야 정상 작동합니다.

### 1단계: 저장소 클론 및 환경 준비
```bash
git clone https://github.com/wlghksw/Platformers.git
cd Platformers
git checkout feature/Automatic-blog
```

### 2단계: Backend (Python) 구동
```bash
cd backend

# (권장) 가상환경 생성 및 활성화
python -m venv venv
source venv/Scripts/activate # Windows 환경

# 백엔드 필수 패키지 설치
pip install fastapi uvicorn anthropic python-multipart pillow python-pptx python-docx pdfplumber requests beautifulsoup4

# FastAPI 서버 실행 (http://localhost:8000)
python main.py
```
> 서버가 실행되면 `data/input`, `data/output` 등의 필수 폴더가 자동으로 생성됩니다.

### 3단계: Frontend (Next.js) 구동
새 터미널을 열고 다음 명령어를 실행합니다.
```bash
cd frontend

# 노드 패키지 설치
npm install

# 프론트엔드 개발 서버 실행 (http://localhost:3000)
npm run dev
```

---

## 💻 사용 가이드 (How to Use)

1. 브라우저에서 `http://localhost:3000` 로 접속합니다.
2. 우측 설정 패널에 **Claude API Key**를 입력합니다.
3. 분석할 원본 링크(웹사이트 주소)를 넣거나, 제목 키워드 / 필수 해시태그 등을 작성합니다.
4. 참고할 만한 이미지나 기획안 문서(최대 3개)를 드래그 앤 드롭으로 업로드합니다.
5. **[블로그 생성하기]**를 클릭합니다!
6. 잠시 후 초안 문단들이 쪼개져서 화면 하단 에디터 창에 나타납니다.
7. 글의 흐름을 보며 **넣고 싶은 위치에 업로드했던 이미지를 매핑**합니다.
8. **[완벽하게 최종 렌더링하기]**를 눌러 작업을 마무리합니다.
9. 백엔드의 `data/output` 폴더에 생성된 `~.html` 결과물을 열어 그대로 복사한 뒤, 네이버 블로그 스마트에디터에 붙여넣기 하면 끝입니다!

---

## ⚠️ 유의 사항
- Claude의 API 호출 시 Vision 용량 한계로 각 이미지는 3MB 이하로 자동 리사이징(압축)되어 전송됩니다.
- 본 프로젝트에 업로드된 이전 세션의 캐시 파일들(`data/input/*`)은 파일을 전송하지 않고 생성 버튼을 눌러도 새로고침 시 자동 청소(`/clear_input`)되도록 보완되어 관리됩니다.
