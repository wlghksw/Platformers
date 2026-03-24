"""
PDF 생성기: Node.js Puppeteer를 subprocess로 호출하여
브리핑 리포트를 PDF로 변환합니다.
"""

import asyncio
import logging
import os
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

log = logging.getLogger("pdf")
KST = ZoneInfo("Asia/Seoul")

PUPPETEER_SCRIPT = Path(__file__).parent / "generate_pdf.js"
OUTPUT_DIR = Path("./output")


class PDFGenerator:
    def __init__(self):
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    async def generate(self, report: dict, notion_url: str = "") -> str:
        """
        Node.js Puppeteer 스크립트를 호출해 PDF 생성.
        반환: 생성된 PDF 파일 경로
        """
        date_str = datetime.now(KST).strftime("%Y%m%d")
        output_path = OUTPUT_DIR / f"briefing_{date_str}.pdf"

        # 리포트 데이터를 JSON으로 Puppeteer에 전달
        report_data = json.dumps({
            "title": report["title"],
            "date": report["date_kst"],
            "markdown": report["markdown"],
            "notion_url": notion_url,
        }, ensure_ascii=False)

        cmd = [
            "node",
            str(PUPPETEER_SCRIPT),
            "--output", str(output_path),
            "--data", report_data,
        ]

        log.info(f"Puppeteer 실행: {' '.join(cmd[:3])} ...")
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            log.error(f"Puppeteer 오류:\n{stderr.decode()}")
            raise RuntimeError(f"PDF 생성 실패 (exit {proc.returncode})")

        log.info(f"PDF 생성 완료: {output_path}")
        return str(output_path)
