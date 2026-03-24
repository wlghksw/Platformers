"""
노션 숏폼 업로더: 생성된 숏폼 스크립트를 노션에 업로드합니다.
"""

import logging
import os
import aiohttp
from notion_uploader import NotionUploader, NOTION_API_BASE, NOTION_VERSION

log = logging.getLogger("notion_sf")

class NotionShortformUploader(NotionUploader):
    def __init__(self):
        super().__init__()
        # 숏폼 전용 데이터베이스가 설정되어 있다면 그것을 사용하고, 없으면 기본 DB 사용
        self.database_id = os.getenv("NOTION_SHORTFORM_DATABASE_ID", self.database_id)

    async def create_script_page(self, shortform_result: dict, date_str: str) -> str:
        """숏폼 스크립트를 노션 페이지로 생성하고 URL을 반환"""
        scripts = shortform_result["scripts"]
        
        # 숏폼 스크립트를 노션 블록으로 변환
        blocks = self._build_script_blocks(scripts)
        
        payload = {
            "parent": {"database_id": self.database_id},
            "icon": {"emoji": "🎬"},
            "properties": {
                "이름": {
                    "title": [{"text": {"content": f"🎬 [숏폼 스크립트] {scripts.get('topic', '시장 브리핑')} ({date_str})"}}]
                },
                "Date": {
                    "date": {"start": date_str}
                },
                "Keywords": {
                    "multi_select": [
                        {"name": "숏폼"}, {"name": scripts.get("hook_keyword", "트렌드")}
                    ]
                }
            },
            "children": blocks,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{NOTION_API_BASE}/pages",
                headers=self.headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    log.error(f"Notion Shortform API 오류 {resp.status}: {body}")
                    return "업로드 실패"
                data = await resp.json()

        return data.get("url", "")

    def _build_script_blocks(self, scripts: dict) -> list[dict]:
        """숏폼 JSON 데이터를 노션 블록 리스트로 변환"""
        blocks = []
        
        blocks.append(self._heading(2, f"🎯 핵심 주제: {scripts.get('topic', '')}"))
        blocks.append(self._paragraph(f"훅 키워드: #{scripts.get('hook_keyword', '')}"))
        
        for version_key, version in scripts.get("versions", {}).items():
            blocks.append(self._heading(3, f"📹 {version_key} 버전: {version.get('title', '')}"))
            blocks.append(self._paragraph(f"타겟: {version.get('target', '')} | 예상 길이: {version.get('duration', '')}초"))
            
            # 장면별 상세 스크립트
            for scene in version.get("scenes", []):
                scene_text = (
                    f"[{scene.get('time', '')}] {scene.get('type', '').upper()}\n"
                    f"• 나레이션: {scene.get('script', '')}\n"
                    f"• 화면: {scene.get('visual', '')}\n"
                    f"• 자막: {scene.get('caption', '')}"
                )
                blocks.append(self._paragraph(scene_text))
            
            blocks.append(self._bullet(f"CTA: {version.get('cta', '')}"))
            blocks.append(self._bullet(f"해시태그: {' '.join(version.get('hashtags', []))}"))
            blocks.append({"type": "divider", "divider": {}, "object": "block"})

        return blocks[:100]
