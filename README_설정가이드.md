# WorkPortal 설정 가이드

> 처음 한 번만 설정하면 이후는 `bash start.sh` 한 번으로 실행됩니다.

---

## 1단계 — Google Cloud 프로젝트 생성 및 OAuth 설정

### 1-1. Google Cloud Console 접속
1. [https://console.cloud.google.com](https://console.cloud.google.com) 접속
2. 상단 프로젝트 선택 → **새 프로젝트** 클릭
3. 프로젝트 이름: `WorkPortal` (자유롭게 지정 가능) → **만들기**

### 1-2. API 활성화
1. 왼쪽 메뉴 → **API 및 서비스** → **라이브러리**
2. 아래 두 API를 검색해서 각각 **사용 설정**:
   - `Gmail API`
   - `Google Calendar API`

### 1-3. OAuth 동의 화면 설정
1. 왼쪽 메뉴 → **API 및 서비스** → **OAuth 동의 화면**
2. **외부** 선택 → **만들기**
3. 앱 이름: `WorkPortal`, 사용자 지원 이메일: 본인 이메일 입력
4. **저장 후 계속** (나머지 단계는 기본값 유지)
5. **테스트 사용자** 탭 → **+ 사용자 추가** → 본인 Gmail 계정 추가

### 1-4. OAuth 클라이언트 ID 생성
1. 왼쪽 메뉴 → **API 및 서비스** → **사용자 인증 정보**
2. **+ 사용자 인증 정보 만들기** → **OAuth 클라이언트 ID**
3. 애플리케이션 유형: **웹 애플리케이션**
4. 이름: `WorkPortal`
5. **승인된 리디렉션 URI** → **+ URI 추가**:
   ```
   http://localhost:8787/oauth/callback
   ```
6. **만들기** 클릭

### 1-5. credentials.json 다운로드
1. 생성된 클라이언트 ID 오른쪽 **다운로드(⬇)** 버튼 클릭
2. 다운로드된 파일을 **이 폴더(WorkPortal 폴더)에 복사**
3. 파일 이름을 정확히 `credentials.json` 으로 변경

---

## 2단계 — Notion 연동

### 2-1. Notion Integration 생성
1. [https://www.notion.so/my-integrations](https://www.notion.so/my-integrations) 접속
2. **+ New integration** 클릭
3. 이름: `WorkPortal`
4. 타입: **Internal**
5. **Save** → 생성된 **Internal Integration Token** 복사 (ntn_... 또는 secret_... 로 시작)

### 2-2. Notion 페이지 연동 허용
1. Notion에서 연동하려는 페이지/데이터베이스 열기
2. 우측 상단 **···** → **Connect to** → **WorkPortal** 선택

---

## 3단계 — WorkPortal 실행

### 방법 A. 터미널 실행 (권장)
```bash
# WorkPortal 폴더에서
bash start.sh
```

### 방법 B. Python 직접 실행
```bash
python3 server.py
```

### 방법 C. 더블클릭 (macOS)
- `start.sh` 파일 우클릭 → **터미널에서 열기**

---

## 4단계 — 최초 인증

1. 브라우저에서 `http://localhost:8787` 자동으로 열림
2. 상단 **⚙️ 설정** 탭 클릭
3. **Google 연동** 버튼 클릭 → Google 로그인 화면에서 본인 계정 선택
4. "앱이 확인되지 않음" 경고가 뜨면 → **고급** → **WorkPortal(으)로 이동** 클릭
5. Gmail/Calendar 권한 허용 → "✅ Google 인증 완료!" 메시지 확인
6. Notion Integration Token을 **Notion 토큰** 입력란에 붙여넣기 → 저장

---

## 파일 구조

```
Claude-Cowork/
├── start.sh              ← 실행 스크립트 (여기서 시작)
├── server.py             ← 백엔드 서버 (Python 표준 라이브러리만 사용)
├── index.html            ← 웹 포털 UI (메인)
├── credentials.json      ← Google OAuth 키 (직접 생성 필요)
├── .tokens.json          ← 인증 토큰 자동 저장 (자동 생성)
└── README_설정가이드.md   ← 이 파일
```

---

## 문제 해결

| 증상 | 해결 방법 |
|------|-----------|
| "credentials.json 없음" 오류 | 1단계 다시 확인, 파일명 정확히 `credentials.json`인지 확인 |
| 포트 8787 이미 사용 중 | `start.sh` 가 자동 처리, 또는 터미널에서 `kill $(lsof -ti tcp:8787)` |
| Google 인증 후에도 연동 안 됨 | 설정 탭에서 **상태 새로고침** 클릭 |
| Notion 검색이 안 됨 | 2-2단계에서 해당 페이지에 Integration 연결했는지 확인 |
| "앱이 확인되지 않음" 경고 | 정상 — **고급 → 계속** 클릭하면 됩니다 (개인 사용 앱이므로 검증 불필요) |

---

*이 포털은 Google Gmail, Google Calendar, Notion을 연동하여 업무 자동화를 돕습니다.*
*Cowork의 예약 작업(스케줄)과 함께 사용하면 자동화 효과가 극대화됩니다.*
