// connector_details.js
// 각 커넥터 ID별 상세 연결 정보
// - howToConnect : Power Automate에서 실제 연결하는 단계
// - prerequisites : 필요한 사전 조건
// - officialDoc   : Microsoft 공식 문서 URL
// 확실히 아는 것만 채우고, 모르면 빈 배열/빈 문자열로 처리

const CONNECTOR_DETAILS = {
  // ── Microsoft 365 ──────────────────────────────────────────
  2: { // Microsoft Teams
    howToConnect: [
      "1. Power Automate → 새 흐름 만들기",
      "2. 트리거/액션 검색창에 'Teams' 입력",
      "3. Microsoft Teams 커넥터 선택",
      "4. '로그인' 클릭 → Microsoft 365 계정으로 인증",
      "5. 팀·채널을 드롭다운에서 선택 후 저장"
    ],
    prerequisites: ["Microsoft 365 계정", "Microsoft Teams 사용 중인 조직"],
    officialDoc: "https://learn.microsoft.com/en-us/connectors/teams/"
  },
  3: { // SharePoint
    howToConnect: [
      "1. Power Automate → 새 흐름 만들기",
      "2. 'SharePoint' 검색 후 커넥터 선택",
      "3. '로그인' 클릭 → Microsoft 365 계정으로 인증",
      "4. 사이트 주소(URL) 입력 또는 드롭다운 선택",
      "5. 목록/라이브러리 선택 후 저장"
    ],
    prerequisites: ["Microsoft 365 계정", "SharePoint 사이트 접근 권한"],
    officialDoc: "https://learn.microsoft.com/en-us/connectors/sharepointonline/"
  },
  4: { // OneDrive for Business
    howToConnect: [
      "1. Power Automate → 새 흐름 만들기",
      "2. 'OneDrive for Business' 검색 후 선택",
      "3. Microsoft 365 계정으로 인증",
      "4. 폴더 경로 입력 또는 선택"
    ],
    prerequisites: ["Microsoft 365 계정", "OneDrive for Business 활성화"],
    officialDoc: "https://learn.microsoft.com/en-us/connectors/onedriveforbusiness/"
  },
  5: { // Microsoft Forms
    howToConnect: [
      "1. Power Automate → 새 흐름 만들기",
      "2. 'Microsoft Forms' 검색 후 선택",
      "3. Microsoft 365 계정으로 인증",
      "4. 양식 ID 드롭다운에서 해당 양식 선택"
    ],
    prerequisites: ["Microsoft 365 계정", "Microsoft Forms에 생성된 양식"],
    officialDoc: "https://learn.microsoft.com/en-us/connectors/microsoftforms/"
  },
  6: { // Excel Online (Business)
    howToConnect: [
      "1. 'Excel Online (Business)' 검색 후 선택",
      "2. '로그인' 클릭 → 계정 인증",
      "3. 파일 위치(OneDrive/SharePoint) 선택",
      "4. 파일 내 '표(Table)' 서식이 적용된 데이터 선택"
    ],
    prerequisites: ["Excel 파일 내 데이터가 '표(Table)' 서식으로 저장되어야 함"],
    officialDoc: "https://learn.microsoft.com/en-us/connectors/excelonlinebusiness/"
  },
  19: { // OpenAI (ChatGPT)
    howToConnect: [
      "1. platform.openai.com에서 API 키 생성",
      "2. Power Automate → OpenAI 검색 후 선택",
      "3. '로그인' → 발급받은 API 키 입력하여 연결"
    ],
    prerequisites: ["OpenAI 계정 및 API Key (유료 플랜 권장)", "Premium 라이선스"],
    officialDoc: "https://learn.microsoft.com/en-us/connectors/openai/"
  },
  58: { // Gmail
    howToConnect: [
      "1. 'Gmail' 검색 후 커넥터 선택",
      "2. 'Google 계정 로그인' 클릭하여 인증",
      "3. Power Automate 액세스 허용 클릭"
    ],
    prerequisites: ["Google 계정 (Gmail 사용 설정)"],
    officialDoc: "https://learn.microsoft.com/en-us/connectors/gmail/"
  },
  59: { // Slack
    howToConnect: [
      "1. 'Slack' 검색 후 액션 선택",
      "2. Slack 워크스페이스 로그인 및 앱 추가 승인",
      "3. 채널 ID 또는 이름을 입력하여 연동"
    ],
    prerequisites: ["Slack 워크스페이스 계정 및 채널 접근 권한"],
    officialDoc: "https://learn.microsoft.com/en-us/connectors/slack/"
  },
  149: { // Salesforce
    howToConnect: [
      "1. 'Salesforce' 검색 후 선택",
      "2. Salesforce 계정으로 OAuth 로그인을 통한 인증",
      "3. 샌드박스 또는 프로덕션 환경 선택"
    ],
    prerequisites: ["Salesforce 계정 및 API 액세스 권한", "Premium 라이선스"],
    officialDoc: "https://learn.microsoft.com/en-us/connectors/salesforce/"
  },
  7: { // Microsoft Planner
    howToConnect: [
      "1. 'Planner' 검색 후 선택",
      "2. 계정 인증",
      "3. 그룹 및 플랜 이름을 드롭다운에서 선택"
    ],
    prerequisites: ["Microsoft 365 계정", "Planner 플랜 생성 권한"],
    officialDoc: "https://learn.microsoft.com/en-us/connectors/planner/"
  },
  8: { // Office 365 Users
    howToConnect: ["1. 'Office 365 Users' 검색 후 액션 추가", "2. 로그인을 통해 조직 디렉터리 접근 허용"],
    prerequisites: ["Microsoft 365 계정"],
    officialDoc: "https://learn.microsoft.com/en-us/connectors/office365users/"
  },
  9: { // Approvals
    howToConnect: ["1. 'Approvals' 검색", "2. '승인 시작 및 기다리기' 등의 액션 선택", "3. 별도 설정 없이 계정 인증으로 사용 가능"],
    prerequisites: ["Power Automate 라이선스"],
    officialDoc: "https://learn.microsoft.com/en-us/power-automate/approvals-overview"
  },
  10: { // Notifications
    howToConnect: ["1. 'Notifications' 검색", "2. 모바일 앱 알림 또는 이메일 알림 선택"],
    prerequisites: ["Power Automate 모바일 앱 설치 (푸시 알림 시)"],
    officialDoc: "https://learn.microsoft.com/en-us/connectors/flowpush/"
  },
  12: { // Azure OpenAI
    howToConnect: ["1. Azure Portal에서 OpenAI 리소스 생성", "2. API Key 및 Endpoint 확인", "3. Power Automate에서 해당 정보 입력하여 연결"],
    prerequisites: ["Azure 구독", "Azure OpenAI 서비스 승인", "Premium 라이선스"],
    officialDoc: "https://learn.microsoft.com/en-us/connectors/azureopenai/"
  },
  13: { // Notion
    howToConnect: ["1. 'Notion' 검색", "2. Notion 계정 로그인", "3. 접근 허용할 페이지 선택"],
    prerequisites: ["Notion 계정", "통합(Integration) 설정 권한"],
    officialDoc: "https://learn.microsoft.com/en-us/connectors/notion/"
  },
  14: { // Power BI
    howToConnect: ["1. 'Power BI' 검색", "2. 데이터 세트 또는 보고서 선택", "3. 필요시 서비스 주체 또는 사용자 계정 인증"],
    prerequisites: ["Power BI Pro 또는 Premium 라이선스"],
    officialDoc: "https://learn.microsoft.com/en-us/connectors/powerbi/"
  },
  27: { // HTTP
    howToConnect: ["1. 'HTTP' 검색 (기본 제공)", "2. Method, URI 입력", "3. 필요시 인증(OAuth 등) 설정"],
    prerequisites: ["Premium 라이선스"],
    officialDoc: "https://learn.microsoft.com/en-us/connectors/http/"
  },
  31: { // Recurrence
    howToConnect: ["1. 트리거에서 '되풀이(Recurrence)' 검색", "2. 간격 및 빈도 설정"],
    prerequisites: ["없음 (기본 트리거)"],
    officialDoc: "https://learn.microsoft.com/en-us/azure/connectors/connectors-native-recurrence"
  },
  65: { // SQL Server
    howToConnect: ["1. 'SQL Server' 검색", "2. 서버 이름, 데이터베이스 이름 입력", "3. 인증 방식(SQL 또는 Windows) 선택 및 정보 입력"],
    prerequisites: ["SQL Server 접근 권한", "온프레미스인 경우 데이터 게이트웨이 필요", "Premium 라이선스"],
    officialDoc: "https://learn.microsoft.com/en-us/connectors/sql/"
  },
  67: { // Google Sheets
    howToConnect: ["1. 'Google Sheets' 검색", "2. Google 계정 로그인", "3. 스프레드시트 파일 및 워크시트 선택"],
    prerequisites: ["Google 계정", "Google Drive 파일 접근 권한"],
    officialDoc: "https://learn.microsoft.com/en-us/connectors/googlesheet/"
  }
};
