"""
Market Intelligence Daily Briefing - Main Orchestrator
Claude Code가 이 파일을 진입점으로 실행합니다.
실행: python main.py              # 전체 파이프라인
      python main.py --dry-run   # 업로드 없이 미리보기
      python main.py --skip-shortform  # 숏폼 생성 건너뜀
"""

import asyncio
import argparse
import logging
import sys
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

# Windows 터미널 한글/이모지 출력 문제 해결
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

from dotenv import load_dotenv
load_dotenv()

from news_collector import NewsCollector
from llm_analyzer import LLMAnalyzer
from shortform_generator import ShortformGenerator
from notion_uploader import NotionUploader
from notion_shortform_uploader import NotionShortformUploader
from pdf_generator import PDFGenerator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("orchestrator")

KST = ZoneInfo("Asia/Seoul")


async def run_pipeline(dry_run: bool = False, skip_shortform: bool = False):
    now = datetime.now(KST)
    log.info(f"=== 데일리 브리핑 파이프라인 시작: {now.strftime('%Y-%m-%d %H:%M KST')} ===")

    # 1. 데이터 수집
    log.info("STEP 1 — 뉴스 데이터 수집 중...")
    collector = NewsCollector()
    raw_articles = await collector.fetch_all()
    log.info(f"  수집 완료: {len(raw_articles)}건")

    # 2. LLM 분석 (Claude API)
    log.info("STEP 2 — Claude로 분석 중...")
    analyzer = LLMAnalyzer()
    report = await analyzer.generate_briefing(raw_articles, date=now)
    log.info(f"  분석 완료: {report['title']}")

    if dry_run:
        log.info("[DRY RUN] 실제 업로드 없이 종료합니다.")
        print("\n--- REPORT PREVIEW ---")
        try:
            print(report["markdown"])
        except UnicodeEncodeError:
            print(report["markdown"].encode('utf-8', errors='replace').decode('utf-8'))
        
        if not skip_shortform:
            log.info("[DRY RUN] 숏폼 스크립트 생성 시뮬레이션...")
            sf_gen = ShortformGenerator()
            shortform_result = await sf_gen.generate(report)
            print("\n--- SHORTFORM SCRIPT PREVIEW (15s) ---")
            v15 = shortform_result["scripts"]["versions"].get("15s", {})
            for scene in v15.get("scenes", []):
                print(f"[{scene.get('time', '')}] {scene.get('script', '')}")
        return

    # 3. Notion 업로드
    log.info("STEP 3 — Notion에 업로드 중...")
    uploader = NotionUploader()
    notion_url = await uploader.create_page(report)
    log.info(f"  Notion 업로드 완료: {notion_url}")

    # 4. PDF 생성 (Node.js Puppeteer 호출)
    log.info("STEP 4 — PDF 생성 중...")
    pdf_gen = PDFGenerator()
    pdf_path = await pdf_gen.generate(report, notion_url)
    log.info(f"  PDF 저장: {pdf_path}")

    # 5. 숏폼 스크립트 생성
    shortform_result = None
    if not skip_shortform:
        log.info("STEP 5 — 숏폼 스크립트 생성 중...")
        sf_gen = ShortformGenerator()
        shortform_result = await sf_gen.generate(report)
        log.info(f"  스크립트 파일 저장: {list(shortform_result['files'].values())}")

        log.info("STEP 5b — 숏폼 스크립트 Notion 업로드 중...")
        sf_uploader = NotionShortformUploader()
        sf_notion_url = await sf_uploader.create_script_page(
            shortform_result, report["date"]
        )
        log.info(f"  숏폼 Notion 업로드 완료: {sf_notion_url}")
    else:
        log.info("STEP 5 — 숏폼 생성 건너뜀 (--skip-shortform)")

    log.info("=== 파이프라인 완료 ===")
    return {
        "notion_url": notion_url,
        "pdf_path": pdf_path,
        "shortform_files": shortform_result["files"] if shortform_result else {},
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Market Briefing Pipeline")
    parser.add_argument("--dry-run", action="store_true", help="업로드 없이 미리보기만 출력")
    parser.add_argument("--skip-shortform", action="store_true", help="숏폼 스크립트 생성 건너뜀")
    args = parser.parse_args()
    asyncio.run(run_pipeline(dry_run=args.dry_run, skip_shortform=args.skip_shortform))
