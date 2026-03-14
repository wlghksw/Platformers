# Platformers - Spring Boot Portfolio Website

Spring Boot 기반 포트폴리오 웹사이트입니다.

## 프로젝트 구조

```
Platformer/
├── pom.xml                          # Maven 설정 파일
├── src/
│   ├── main/
│   │   ├── java/
│   │   │   └── com/platformers/
│   │   │       ├── PlatformersApplication.java    # 메인 애플리케이션
│   │   │       ├── controller/
│   │   │       │   └── MainController.java        # 컨트롤러
│   │   │       ├── model/
│   │   │       │   └── Project.java               # 프로젝트 모델
│   │   │       └── service/
│   │   │           └── ProjectService.java        # 프로젝트 서비스
│   │   └── resources/
│   │       ├── application.properties              # 설정 파일
│   │       ├── templates/                          # Thymeleaf 템플릿
│   │       │   ├── index.html                      # 메인 페이지
│   │       │   └── portfolio.html                  # 포트폴리오 페이지
│   │       └── static/                             # 정적 리소스
│   │           ├── css/
│   │           ├── js/
│   │           └── assets/
└── README.md
```

## 실행 방법

### 1. Maven 설치 확인
```bash
mvn --version
```

### 2. 프로젝트 빌드
```bash
mvn clean install
```

### 3. 애플리케이션 실행
```bash
mvn spring-boot:run
```

또는

```bash
java -jar target/platformers-1.0.0.jar
```

### 4. 접속
브라우저에서 `http://localhost:8080` 접속

## 기술 스택

- Java 17
- Spring Boot 3.2.0
- Thymeleaf
- Maven

## 주요 기능

- 메인 페이지 슬라이더
- 포트폴리오 그리드 레이아웃
- 카테고리 필터링
- 반응형 디자인
