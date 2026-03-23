# Platformers — PHP 버전

Spring Boot(Thymeleaf) 사이트와 동일한 UI·데이터를 **순수 PHP**로 옮긴 복제본입니다.

## 구조

| 파일 | 설명 |
|------|------|
| `index.php` | 메인 페이지 |
| `portfolio.php` | 포트폴리오 목록 (필터 포함) |
| `config.php` | 프로젝트·카테고리 데이터 |
| `static/css/main.css` | 스타일 (Java 버전과 동일) |
| `static/js/main.js` | 스크립트 (Java 버전과 동일) |
| `static/assets/*.png` | 썸네일 이미지 |

## 실행 방법

프로젝트 폴더에서 PHP 내장 서버:

```bash
cd platformers-php
php -S localhost:8000
```

브라우저에서 **http://localhost:8000/index.php** 또는 **http://localhost:8000/** (디렉터리 인덱스가 없으면 `/index.php`).

포트폴리오: **http://localhost:8000/portfolio.php**

## 데이터 수정

`config.php`의 `$projects`, `$categories` 배열을 편집하면 됩니다.
