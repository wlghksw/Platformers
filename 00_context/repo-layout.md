# 저장소 폴더 역할 (00~04)

Cowork에 넘길 자료·프로젝트·산출·스킬을 구분하기 위한 구조입니다.

| 폴더 | 역할 |
|------|------|
| `00_context/` | 개인 프로필, 작업 규칙, 문체·스타일, 이 저장소 안내 |
| `01_inbox/` | 가공 전 입력물 (메모, 붙여넣기, 요청 초안 등) |
| `02_projects/` | 진행 중 코드·앱 (예: `workportal/`) |
| `03_output/` | 완성 산출물 (`YYYY-MM-DD_주제_v1` 규칙 권장) |
| `04_skills/` | 반복 작업용 스킬 정의 (`SKILL.md` 등) |

## WorkPortal 실행

저장소 루트에서 `bash start.sh` → `02_projects/workportal`의 서버가 올라갑니다.  
Google OAuth 파일 `credentials.json`은 `02_projects/workportal/` 에 두면 됩니다.
