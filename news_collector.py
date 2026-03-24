"""
뉴스 수집기: Google News RSS + Naver News Search API
최근 24시간 기사를 수집합니다.
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import aiohttp
import feedparser

log = logging.getLogger("collector")
KST = ZoneInfo("Asia/Seoul")

# 수집할 Google News RSS 쿼리 목록
GOOGLE_RSS_QUERIES = [
    "미국 주식 증시",
    "연준 Fed 금리",
    "나스닥 다우 S&P",
    "한국 코스피 코스닥",
    "반도체 AI 주식",
]

GOOGLE_RSS_BASE = "https://news.google.com/rss/search?q={query}&hl=ko&gl=KR&ceid=KR:ko"


class NewsCollector:
    def __init__(self):
        self.naver_client_id = os.getenv("NAVER_CLIENT_ID", "")
        self.naver_client_secret = os.getenv("NAVER_CLIENT_SECRET", "")
        self.cutoff = datetime.now(KST) - timedelta(hours=24)

    async def fetch_all(self) -> list[dict]:
        """모든 소스에서 병렬로 수집"""
        async with aiohttp.ClientSession() as session:
            tasks = [
                self._fetch_google_news(session),
                self._fetch_naver_news(session),
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        articles = []
        for r in results:
            if isinstance(r, Exception):
                log.warning(f"수집 오류 (무시): {r}")
            else:
                articles.extend(r)

        # 중복 제거 (제목 기준)
        seen = set()
        deduped = []
        for a in articles:
            key = a["title"][:30]
            if key not in seen:
                seen.add(key)
                deduped.append(a)

        log.info(f"중복 제거 후: {len(deduped)}건 / 전체 {len(articles)}건")
        return deduped

    async def _fetch_google_news(self, session: aiohttp.ClientSession) -> list[dict]:
        articles = []
        for query in GOOGLE_RSS_QUERIES:
            url = GOOGLE_RSS_BASE.format(query=query.replace(" ", "+"))
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    text = await resp.text()
                feed = feedparser.parse(text)
                for entry in feed.entries[:5]:  # 쿼리당 최대 5건
                    articles.append({
                        "title": entry.get("title", ""),
                        "summary": entry.get("summary", ""),
                        "link": entry.get("link", ""),
                        "source": "google_news",
                        "query": query,
                        "published": entry.get("published", ""),
                    })
            except Exception as e:
                log.warning(f"Google RSS 오류 ({query}): {e}")
        return articles

    async def _fetch_naver_news(self, session: aiohttp.ClientSession) -> list[dict]:
        """Naver News Search API (클라이언트 ID/Secret 필요)"""
        if not self.naver_client_id:
            log.info("NAVER_CLIENT_ID 미설정 — Naver 뉴스 수집 건너뜀")
            return []

        queries = ["미국 주식", "코스피 코스닥", "반도체 주식", "연준 금리"]
        articles = []
        headers = {
            "X-Naver-Client-Id": self.naver_client_id,
            "X-Naver-Client-Secret": self.naver_client_secret,
        }
        for query in queries:
            url = "https://openapi.naver.com/v1/search/news.json"
            params = {"query": query, "display": 5, "sort": "date"}
            try:
                async with session.get(url, headers=headers, params=params,
                                       timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    data = await resp.json()
                for item in data.get("items", []):
                    articles.append({
                        "title": item["title"].replace("<b>", "").replace("</b>", ""),
                        "summary": item.get("description", ""),
                        "link": item.get("originallink") or item.get("link", ""),
                        "source": "naver_news",
                        "query": query,
                        "published": item.get("pubDate", ""),
                    })
            except Exception as e:
                log.warning(f"Naver API 오류 ({query}): {e}")
        return articles
