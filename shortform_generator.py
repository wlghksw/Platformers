"""
숏폼 스크립트 생성기
분석된 브리핑 리포트를 바탕으로 TikTok/YouTube Shorts용
영상 스크립트와 스토리보드를 자동 생성합니다.

생성 포맷:
  - 15초 훅 버전 (트렌드 키워드 강조)
  - 30초 핵심 브리핑 버전
  - 60초 풀 스토리 버전
"""

import json
import logging
import os
from datetime import datetime
import pathlib
import anthropic

log = logging.getLogger("shortform")

# ── 시스템 프롬프트 ──────────────────────────────────────────────
SYSTEM_PROMPT = """당신은 MZ세대를 타겟으로 하는 금융/주식 콘텐츠 크리에이터입니다.
주식 브리핑 데이터를 받아 TikTok과 YouTube Shorts에 최적화된 숏폼 영상 스크립트를 생성합니다.

핵심 원칙:
- 첫 3초 안에 시청자를 잡는 강력한 훅(Hook) 사용
- 전문 용어 최소화, 일상 언어로 쉽게 설명
- 긴장감·궁금증 유발 → 정보 전달 → 행동 유도(CTA) 구조
- 각 장면(Scene)은 최대 2~3문장, 화면 전환 포함
- 자막, 효과음, 배경음악 제안 포함

반드시 아래 JSON 형식으로만 응답하세요. 다른 텍스트 없이 JSON만 출력하세요:

{
  "date": "날짜",
  "topic": "오늘의 핵심 주제 (10자 이내)",
  "hook_keyword": "영상 전체를 관통하는 키워드 1개",
  "versions": {
    "15s": {
      "title": "제목 (25자 이내, 해시태그 없이)",
      "duration": 15,
      "target": "타겟 시청자",
      "scenes": [
        {
          "time": "0-3s",
          "type": "hook",
          "script": "나레이션 텍스트",
          "visual": "화면 연출 설명",
          "caption": "자막 텍스트",
          "sfx": "효과음/음악 제안"
        }
      ],
      "hashtags": ["해시태그1", "해시태그2"],
      "cta": "마지막 행동 유도 문구"
    },
    "30s": { "title": "", "duration": 30, "target": "", "scenes": [], "hashtags": [], "cta": "" },
    "60s": { "title": "", "duration": 60, "target": "", "scenes": [], "hashtags": [], "cta": "" }
  },
  "platform_tips": {
    "tiktok": "TikTok 업로드 시 팁",
    "youtube_shorts": "YouTube Shorts 업로드 시 팁"
  }
}"""

USER_TEMPLATE = """오늘({date}) 주식 브리핑 요약:

핵심 주제: {topic}
급상승 키워드: {keywords}
시장 분위기: {sentiment}

브리핑 내용:
{briefing_summary}

위 내용을 바탕으로 3가지 길이(15초/30초/60초)의 숏폼 영상 스크립트를 JSON으로 생성해주세요."""


# ── 메인 클래스 ──────────────────────────────────────────────────
class ShortformGenerator:
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise EnvironmentError("ANTHROPIC_API_KEY 환경 변수가 필요합니다.")
        self.client = anthropic.Anthropic(api_key=api_key)

    async def generate(self, report: dict) -> dict:
        """
        브리핑 리포트를 받아 3종 숏폼 스크립트를 생성하고 반환.
        반환 구조: { "scripts": {...}, "files": {"15s": path, "30s": path, "60s": path} }
        """
        user_msg = self._build_user_message(report)

        log.info("숏폼 스크립트 생성 중 (Claude API 호출)...")
        message = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=8000,
            system=SYSTEM_PROMPT + "\n\n중요: 불필요한 공백을 줄이고 핵심 내용 위주로 경제적인 JSON을 생성하세요.",
            messages=[{"role": "user", "content": user_msg}],
        )

        raw = message.content[0].text.strip()

        # JSON 파싱 — 더욱 견고한 추출 방식 (첫 { 부터 마지막 } 까지)
        try:
            import re
            # 첫 번째 '{'와 마지막 '}' 사이의 내용을 추출
            match = re.search(r'(\{.*\})', raw, re.DOTALL)
            if match:
                json_str = match.group(1).strip()
            else:
                json_str = raw.strip()
            
            scripts = json.loads(json_str)
        except json.JSONDecodeError as e:
            log.error(f"JSON 파싱 실패: {e}")
            # 디버깅을 위해 응답 일부 출력
            print(f"--- RAW RESPONSE (FIRST 500 CHARS) ---\n{raw[:500]}...")
            print(f"--- RAW RESPONSE (LAST 500 CHARS) ---\n{raw[-500:]}...")
            raise RuntimeError(f"Claude의 응답을 JSON으로 변환할 수 없습니다: {e}")

        # 파일로 저장

        # 파일로 저장
        files = self._save_scripts(scripts, report["date"])
        log.info(f"숏폼 스크립트 저장 완료: {list(files.values())}")

        return {"scripts": scripts, "files": files}

    # ── 내부 헬퍼 ───────────────────────────────────────────────
    def _build_user_message(self, report: dict) -> str:
        markdown = report.get("markdown", "")

        # 브리핑에서 핵심 섹션만 추출 (토큰 절약)
        summary_lines = []
        capture = False
        for line in markdown.split("\n"):
            if any(kw in line for kw in ["핵심 요약", "Bull", "Bear", "주목 포인트", "급상승"]):
                capture = True
            if capture:
                summary_lines.append(line)
            if len(summary_lines) > 20:
                break
        briefing_summary = "\n".join(summary_lines) or markdown[:600]

        keywords = ", ".join(report.get("trending_keywords", []))

        # 간단한 감성 판단
        bull_count = markdown.count("📈") + markdown.count("강세")
        bear_count = markdown.count("📉") + markdown.count("약세")
        if bull_count > bear_count:
            sentiment = "강세 (Bull) 우세"
        elif bear_count > bull_count:
            sentiment = "약세 (Bear) 우세"
        else:
            sentiment = "혼조세"

        return USER_TEMPLATE.format(
            date=report.get("date_kst", report.get("date", "")),
            topic=report.get("trending_keywords", ["주식 시장"])[0] if report.get("trending_keywords") else "주식 시장",
            keywords=keywords or "해당 없음",
            sentiment=sentiment,
            briefing_summary=briefing_summary,
        )

    def _save_scripts(self, scripts: dict, date_str: str) -> dict[str, str]:
        """각 버전을 별도 JSON 파일 + 읽기 쉬운 TXT 파일로 저장"""
        out_dir = pathlib.Path("./output/shortform") / date_str
        out_dir.mkdir(parents=True, exist_ok=True)

        files = {}
        for version_key, version_data in scripts.get("versions", {}).items():
            duration = version_data.get("duration", version_key)

            # JSON 저장
            json_path = out_dir / f"script_{duration}s.json"
            json_path.write_text(
                json.dumps(version_data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            # 읽기 쉬운 TXT 저장
            txt_path = out_dir / f"script_{duration}s.txt"
            txt_path.write_text(
                self._to_readable(version_data, scripts, date_str),
                encoding="utf-8",
            )

            files[f"{duration}s"] = str(txt_path)

        # 전체 JSON도 저장
        full_path = out_dir / "scripts_full.json"
        full_path.write_text(
            json.dumps(scripts, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        files["full"] = str(full_path)
        return files

    def _to_readable(self, version: dict, meta: dict, date_str: str) -> str:
        """JSON → 사람이 읽기 쉬운 스크립트 포맷"""
        lines = [
            f"{'='*60}",
            f"  {version.get('title', '')}",
            f"  {meta.get('date', date_str)}  |  {version.get('duration', '?')}초  |  {version.get('target', '')}",
            f"{'='*60}",
            f"훅 키워드: #{meta.get('hook_keyword', '')}",
            "",
        ]
        for scene in version.get("scenes", []):
            lines += [
                f"[{scene.get('time', '')}]  {scene.get('type', '').upper()}",
                f"  나레이션 : {scene.get('script', '')}",
                f"  화면 연출 : {scene.get('visual', '')}",
                f"  자막     : {scene.get('caption', '')}",
                f"  효과음   : {scene.get('sfx', '')}",
                "",
            ]
        hashtags = "  ".join(f"#{t}" for t in version.get("hashtags", []))
        lines += [
            f"CTA: {version.get('cta', '')}",
            f"해시태그: {hashtags}",
        ]
        return "\n".join(lines)
