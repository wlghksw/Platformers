"""
Notion 업로더: 생성된 브리핑 리포트를 Notion 데이터베이스에
새 페이지로 자동 업로드합니다.

Notion API 공식 문서: https://developers.notion.com/
"""

import logging
import os
import re

import aiohttp

log = logging.getLogger("notion")

NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


class NotionUploader:
    def __init__(self):
        self.token = os.getenv("NOTION_API_TOKEN")
        self.database_id = os.getenv("NOTION_DATABASE_ID")
        if not self.token or not self.database_id:
            raise EnvironmentError(
                "NOTION_API_TOKEN 또는 NOTION_DATABASE_ID 환경 변수가 없습니다.\n"
                "Notion Integration 설정 방법: https://www.notion.so/my-integrations"
            )
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Notion-Version": NOTION_VERSION,
        }

    async def create_page(self, report: dict) -> str:
        """브리핑 리포트를 Notion 페이지로 생성하고 URL을 반환"""
        payload = self._build_payload(report)

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{NOTION_API_BASE}/pages",
                headers=self.headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    raise RuntimeError(f"Notion API 오류 {resp.status}: {body}")
                data = await resp.json()

        page_url = data.get("url", "")
        page_id = data.get("id", "")
        log.info(f"Notion 페이지 생성: {page_id}")
        return page_url

    def _build_payload(self, report: dict) -> dict:
        """Notion API 페이지 생성 페이로드 구성"""
        blocks = self._markdown_to_blocks(report["markdown"])

        return {
            "parent": {"database_id": self.database_id},
            "icon": {"emoji": "📈"},
            "properties": {
                # 데이터베이스에 아래 필드들이 있어야 합니다
                "이름": {
                    "title": [{"text": {"content": report["title"]}}]
                },
                "Date": {
                    "date": {"start": report["date"]}
                },
                "Keywords": {
                    "multi_select": [
                        {"name": kw} for kw in report.get("trending_keywords", [])
                    ]
                },
                "Articles": {
                    "number": report.get("article_count", 0)
                },
            },
            "children": blocks,
        }

    def _markdown_to_blocks(self, markdown: str) -> list[dict]:
        """마크다운 텍스트를 Notion 블록 리스트로 변환"""
        blocks = []
        lines = markdown.strip().split("\n")

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            if stripped.startswith("## "):
                # H2 heading
                text = stripped[3:]
                blocks.append(self._heading(2, text))

            elif stripped.startswith("### "):
                text = stripped[4:]
                blocks.append(self._heading(3, text))

            elif stripped.startswith("- "):
                # Bullet
                text = stripped[2:]
                blocks.append(self._bullet(text))

            elif re.match(r"^\d+\.", stripped):
                # Numbered list
                text = re.sub(r"^\d+\.\s*", "", stripped)
                blocks.append(self._numbered(text))

            else:
                # Paragraph
                blocks.append(self._paragraph(stripped))

        return blocks[:100]  # Notion API 한 번에 최대 100 블록

    def _rich_text(self, text: str) -> list[dict]:
        return [{"type": "text", "text": {"content": text[:2000]}}]

    def _heading(self, level: int, text: str) -> dict:
        key = f"heading_{level}"
        return {key: {"rich_text": self._rich_text(text)}, "type": key, "object": "block"}

    def _paragraph(self, text: str) -> dict:
        return {"type": "paragraph", "object": "block",
                "paragraph": {"rich_text": self._rich_text(text)}}

    def _bullet(self, text: str) -> dict:
        return {"type": "bulleted_list_item", "object": "block",
                "bulleted_list_item": {"rich_text": self._rich_text(text)}}

    def _numbered(self, text: str) -> dict:
        return {"type": "numbered_list_item", "object": "block",
                "numbered_list_item": {"rich_text": self._rich_text(text)}}
