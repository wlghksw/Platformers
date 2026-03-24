"""
LLM 분석기: Claude API를 사용해 수집된 뉴스를 분석하고
주식 브리핑 리포트를 생성합니다.
"""

import logging
import os
from datetime import datetime
from zoneinfo import ZoneInfo

import anthropic

log = logging.getLogger("analyzer")
KST = ZoneInfo("Asia/Seoul")

SYSTEM_PROMPT = """당신은 전문 주식 시장 애널리스트입니다.
제공된 뉴스 기사들을 분석하여 투자자를 위한 간결하고 실용적인 일일 브리핑을 작성합니다.

응답은 반드시 아래 마크다운 형식을 정확히 따르세요:

## 📊 오늘의 핵심 요약
(2~3문장으로 전체 시장 분위기 요약)

## 🇺🇸 미국 증시 동향
(전날 미국 증시 주요 이슈, 섹터별 흐름)

## 🇰🇷 국내 증시 포인트
(코스피/코스닥 관련 주요 이슈)

## 🔥 급상승 키워드 Top 5
(쉼표로 구분된 키워드 5개)

## 📈 강세 (Bull) 시그널
- (bullet point 2~4개)

## 📉 약세 (Bear) 시그널
- (bullet point 2~4개)

## 💡 오늘의 주목 포인트
(투자자가 오늘 특히 주목해야 할 1~2가지)

응답에 위 형식 외의 추가 텍스트를 포함하지 마세요."""

USER_TEMPLATE = """다음은 오늘({date}) 수집된 주요 뉴스 기사입니다.
총 {count}건의 기사를 분석하여 일일 주식 브리핑을 작성해주세요.

---
{articles_text}
---"""


class LLMAnalyzer:
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise EnvironmentError("ANTHROPIC_API_KEY 환경 변수가 설정되지 않았습니다.")
        self.client = anthropic.Anthropic(api_key=api_key)

    async def generate_briefing(self, articles: list[dict], date: datetime) -> dict:
        """뉴스 기사 리스트를 받아 구조화된 브리핑 리포트를 반환"""
        articles_text = self._format_articles(articles)
        date_str = date.strftime("%Y년 %m월 %d일 (%a)")

        user_msg = USER_TEMPLATE.format(
            date=date_str,
            count=len(articles),
            articles_text=articles_text,
        )

        log.info(f"Claude API 호출 중... ({len(articles)}건 기사)")
        message = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_msg}],
        )

        markdown_content = message.content[0].text
        title = f"📈 주식 브리핑 — {date.strftime('%Y.%m.%d')}"

        # 급상승 키워드 파싱
        trending_keywords = self._extract_keywords(markdown_content)

        return {
            "title": title,
            "date": date.strftime("%Y-%m-%d"),
            "date_kst": date_str,
            "markdown": markdown_content,
            "trending_keywords": trending_keywords,
            "article_count": len(articles),
            "model": "claude-sonnet-4-6",
        }

    def _format_articles(self, articles: list[dict]) -> str:
        """기사 리스트를 LLM에 넘길 텍스트로 포맷"""
        lines = []
        for i, a in enumerate(articles[:40], 1):  # 최대 40건 (토큰 절약)
            lines.append(f"[{i}] [{a['source']}] {a['title']}")
            if a.get("summary"):
                # 요약 앞 100자만 사용
                lines.append(f"    {a['summary'][:100]}")
        return "\n".join(lines)

    def _extract_keywords(self, markdown: str) -> list[str]:
        """마크다운에서 급상승 키워드 섹션 파싱"""
        try:
            for line in markdown.split("\n"):
                if "급상승 키워드" in line and "Top 5" in line:
                    # 다음 줄이 키워드
                    continue
                if line.strip() and not line.startswith("#") and "," in line:
                    return [k.strip() for k in line.split(",")[:5]]
        except Exception:
            pass
        return []
