"""
Claude API를 사용해 문서 내용을 슬라이드 구조로 변환
슬라이드 생성 로직 필수 규칙:
  1. Tag: 슬라이드 성격 표시 (SERVICE, STRATEGY 등)
  2. Title: 핵심 메시지를 담은 대제목
  3. Page Number: 우측 하단 페이지 번호
  4. 이모지 절대 사용 금지
"""
import json
import os
import re

import anthropic


SYSTEM_PROMPT = """You are a professional presentation designer and strategist.
Analyze the given document and generate a structured PPT slide plan in JSON format.

## Slide Generation Rules (Mandatory)
1. **Tag**: Label each slide's role in UPPERCASE English (e.g. OVERVIEW, SERVICE, STRATEGY, PROBLEM, SOLUTION, DATA, TIMELINE, TEAM, CONCLUSION)
2. **Title**: A clear, impactful headline that captures the core message of the slide
3. **Page Number**: Assign sequential page numbers — rendered at the bottom-right of every slide
4. **No emojis** — never use emojis or icon-like special characters anywhere in the output

## Slide Count Guidelines (CRITICAL INSTRUCTION)
- YOU MUST GENERATE AN ABSOLUTE MINIMUM OF 15 SLIDES, regardless of how short the input document is.
- If the document is very short, break down the points into much finer detail, adding "deep dive" slides or elaboration to ensure at least 15 slides are produced.
- Determine the number of slides based on document length:
  - Short documents: 15–20 slides
  - Medium documents: 20–25 slides
  - Long documents: 25–35 slides
- Never artificially compress content — each major topic or chapter deserves its own slide.
- Cover slide (layout: title) and closing slide (layout: closing) are always included in the count.

## Design System (Strictly Enforced)
- **Aspect ratio**: 16:9 only (slide canvas = 33.87 cm x 19.05 cm)
- **Consistent element positions across all slides**:
  - Chapter tag: top-left, fixed at y = 0.25 in, x = 0.4 in
  - Slide title: top area, fixed at y = 0.65 in, x = 0.4 in
  - Subtitle / section label: directly below title, fixed at y = 1.35 in, x = 0.4 in
  - Body content: starts at y = 1.8 in, x = 0.4 in
  - Page number: bottom-right, fixed at y = 6.9 in, x = 12.1 in
- Every slide must have a tag, title, and page number — no exceptions
- Do not place any element outside the safe zone (0.4 in margin on all sides)

## Response Format (JSON only — no markdown, no extra text)
{
  "presentation_title": "Full presentation title",
  "total_pages": 25,
  "slides": [
    {
      "page": 1,
      "tag": "OVERVIEW",
      "title": "Slide headline",
      "subtitle": "Optional section label or supporting line",
      "layout": "title" | "chapter" | "content" | "two_column" | "data" | "closing",
      "content": {
        "main_points": ["Key point 1", "Key point 2"],
        "sub_text": "Supporting description (optional)",
        "highlight": "Key number or keyword to emphasize (optional)",
        "left_column": ["Left side content"],
        "right_column": ["Right side content"]
      },
      "speaker_notes": "Presenter notes"
    }
  ]
}

## Layout Selection Guide
- title: Cover slide (first slide only)
- chapter: Divider slide for a new section/chapter (contains 01, 02 prefix)
- content: General content with bullet points
- two_column: Comparisons, pros/cons, before/after
- data: Numbers, statistics, KPIs
- closing: Final slide — conclusion or call to action

## Constraints
- Each slide must be self-explanatory without context from other slides
- Keep text concise per slide — no walls of text
- Group related points logically — don't split one idea across too many slides
- Respond with pure JSON only (no markdown code fences)"""


def _estimate_slide_count(text_length: int) -> tuple[int, int]:
    """텍스트 길이로 예상 슬라이드 범위 반환 (최대 35장 캡)"""
    if text_length < 3000:
        return 15, 20
    elif text_length < 10000:
        return 20, 25
    else:
        return 25, 35


def _chunk_text(text: str, chunk_size: int = 15000) -> list[str]:
    """텍스트를 페이지 경계 기준으로 청크 분할"""
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    current = ""
    for line in text.split("\n"):
        if len(current) + len(line) > chunk_size and current:
            chunks.append(current.strip())
            current = line + "\n"
        else:
            current += line + "\n"
    if current.strip():
        chunks.append(current.strip())
    return chunks


def generate_slides(
    document_text: str,
    template_info: dict = None,
    custom_instructions: str = None,
    category: str = "proposal"
) -> dict:
    """
    Claude API로 슬라이드 구조 생성
    긴 문서는 청크별로 처리 후 병합
    """
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"), timeout=300.0)
    text_length = len(document_text)
    min_slides, max_slides = _estimate_slide_count(text_length)
    
    # 청크 크기 최적화 (20장 내외면 보통 1~2청크면 충분)
    chunks = _chunk_text(document_text, chunk_size=15000)

    # 스타일 컨텍스트 문자열 (공통)
    style_block = ""
    if template_info:
        style_lines = []
        if template_info.get("colors"):
            style_lines.append(f"- Dominant colors: {', '.join(template_info['colors'][:4])}")
        if template_info.get("fonts"):
            style_lines.append(f"- Fonts: {', '.join(template_info['fonts'][:2])}")
        if template_info.get("has_dark_bg"):
            style_lines.append("- Background: dark")
        if template_info.get("layout_hints"):
            style_lines.append(f"- Layout style: {template_info['layout_hints']}")
        if style_lines:
            style_block = "\n## Template Style\n" + "\n".join(style_lines) + "\n"

    # 다중 청크 — 청크별 생성 후 병합
    all_slides = []
    presentation_title = ""
    page_offset = 0

    for i, chunk in enumerate(chunks):
        is_first = (i == 0)
        is_last = (i == len(chunks) - 1)
        
        # 전체 20장 내외가 되도록 청크당 개수 배분
        chunk_min = max(3, min_slides // len(chunks))
        chunk_max = max(5, max_slides // len(chunks) + (2 if is_last else 0))

        try:
            result = _call_api(
                client, chunk, style_block, custom_instructions,
                chunk_min, chunk_max,
                page_offset=page_offset,
                is_continuation=(not is_first),
                is_last=is_last,
                category=category
            )
        except Exception as e:
            # 특정 청크 실패 시 건너뛰고 다음으로 진행하거나 에러 로깅
            if is_first: raise e
            continue

        if not presentation_title:
            presentation_title = result.get("presentation_title", "")

        chunk_slides = result.get("slides", [])

        # 마지막 청크가 아니면 closing 슬라이드 제거
        if not is_last:
            chunk_slides = [s for s in chunk_slides if s.get("layout") != "closing"]

        all_slides.extend(chunk_slides)
        page_offset = len(all_slides)
        
        # 전체 슬라이드가 최대 장수를 넘으면 중단
        if len(all_slides) >= max_slides:
            all_slides = all_slides[:max_slides]
            break

    # 페이지 번호 재정렬
    total = len(all_slides)
    for idx, slide in enumerate(all_slides, 1):
        slide["page"] = idx

    return {
        "presentation_title": presentation_title,
        "total_pages": total,
        "slides": all_slides,
    }


def _call_api(client, text: str, style_block: str, custom_instructions: str,
              min_slides: int, max_slides: int, page_offset: int,
              is_continuation: bool, is_last: bool = True, category: str = "proposal") -> dict:
    """단일 Claude API 호출"""

    category_note = ""
    if category == "at_curriculum":
        category_note = f"""
## [CATEGORY: AT Center Curriculum]
1. Structure:
   - Must divide the presentation into clearly numbered Chapters (01, 02, etc.).
   - EVERY Chapter MUST start with a "chapter" layout slide.
   - Example slide sequence: title -> chapter (01) -> content -> content -> chapter (02) -> content -> closing.
2. Chapter Slide Rules (CRITICAL):
   - For "chapter" layout slides, the "tag" field MUST be the zero-padded chapter number ONLY: "01", "02", "03".
   - For "chapter" layout slides, the "title" field MUST be the chapter title WITHOUT the number prefix.
   - WRONG: {{"layout": "chapter", "tag": "CHAPTER", "title": "01 농수산물유통안정법의 역사"}}
   - CORRECT: {{"layout": "chapter", "tag": "01", "title": "농수산물유통안정법의 역사"}}
3. Tone: Educational, clear, instructional, and structured for learners.
4. Content: Focus on learning objectives and step-by-step concepts.
5. Goal: Generate around {min_slides} to {max_slides} slides.
"""
    else:
        category_note = f"""
## [CATEGORY: Education Proposal]
1. Structure: Professional business proposal flow (Overview -> Problem -> Solution -> Strategy -> Conclusion).
2. Layouts: Do NOT use "chapter" layout. Stick to title, content, two_column, data, closing.
3. Tone: Persuasive, professional, corporate.
4. Goal: Generate around {min_slides} to {max_slides} slides.
"""

    continuation_note = ""
    if is_continuation:
        continuation_note = (
            f"\nNote: This is a continuation. Start page numbering from {page_offset + 1}. "
            f"Do NOT include a title slide. "
            + ("Include a closing slide." if is_last else "No closing slide.")
        )
    else:
        continuation_note = f"\nGenerate between {min_slides} and {max_slides} slides for this section."

    user_content = f"""{category_note}

Analyze this document content and generate a slide structure.
{continuation_note}
{style_block}
## Document Content
{text}
"""
    if custom_instructions:
        user_content += f"\n## Additional Instructions\n{custom_instructions}\n"

    response = client.messages.create(
        model="claude-sonnet-4-6", 
        max_tokens=8192,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}],
    )

    raw_text = response.content[0].text.strip()
    
    # JSON 추출 및 정제
    clean_text = re.sub(r"```(?:json)?\s*|\s*```", "", raw_text).strip()
    
    try:
        return json.loads(clean_text)
    except json.JSONDecodeError:
        # 사소한 문법 오류(쉼표 누락 등) 복구 시도
        try:
            # 1. 객체/배열 사이의 누락된 쉼표 복구 (예: } "key" -> }, "key")
            fixed_text = re.sub(r'}\s*"', '}, "', clean_text)
            fixed_text = re.sub(r']\s*"', '], "', fixed_text)
            return json.loads(fixed_text)
        except Exception:
            raise ValueError(f"Claude JSON 파싱 실패. 문법 오류가 있습니다.\nResponse: {raw_text[:500]}...")


def generate_slides_from_images(
    pages: list,
    custom_instructions: str = None,
    category: str = "proposal"
) -> dict:
    """
    이미지 PDF(스캔본)를 Claude Vision API로 직접 분석해 슬라이드 생성.
    pages: extract_pdf_as_images()의 반환값
    """
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"), timeout=300.0)

    total_pages = len(pages)
    # 이미지 분석 시에는 텍스트보다 정보량이 적을 수 있으므로 슬라이드 수 조절
    min_slides = max(8, total_pages)
    max_slides = min(25, total_pages * 2)

    # 카테고리별 지시사항
    category_note = ""
    if category == "at_curriculum":
        category_note = f"""
## [CATEGORY: AT Center Curriculum]
1. Structure: Clearly numbered Chapters (01, 02, etc.).
2. Chapter Slides: Use "chapter" layout. "tag" must be "01", "02".
3. Goal: Generate around {min_slides} to {max_slides} slides.
"""
    else:
        category_note = f"""
## [CATEGORY: Education Proposal]
1. Structure: Overview -> Problem -> Solution -> Strategy -> Conclusion.
2. Goal: Generate around {min_slides} to {max_slides} slides.
"""

    content_blocks = []
    for p in pages:
        content_blocks.append({"type": "text", "text": f"[페이지 {p['page']}]"})
        content_blocks.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": p["media_type"],
                "data": p["base64"]
            }
        })

    instruction_text = f"""{category_note}
위 이미지들을 보고 핵심 내용을 추출하여 유효한 JSON 형식으로만 응답하세요.
**중요: 모든 JSON 객체와 필드 사이에 반드시 쉼표(,)를 누락하지 마세요.**
Generate between {min_slides} and {max_slides} slides.
"""
    if custom_instructions:
        instruction_text += f"\n## Additional Instructions\n{custom_instructions}\n"

    content_blocks.append({"type": "text", "text": instruction_text})

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8192,
        system=SYSTEM_PROMPT + "\nIMPORTANT: Ensure the JSON is perfectly valid and all strings/objects are closed properly.",
        messages=[{"role": "user", "content": content_blocks}],
    )

    raw_text = response.content[0].text.strip()
    clean_text = re.sub(r"```(?:json)?\s*|\s*```", "", raw_text).strip()

    try:
        # 첫 번째 시도: 일반 파싱
        result = json.loads(clean_text)
    except json.JSONDecodeError:
        # 두 번째 시도: 쉼표 복구 후 파싱
        try:
            fixed_text = re.sub(r'}\s*"', '}, "', clean_text)
            result = json.loads(fixed_text)
        except Exception:
            raise ValueError("Vision API가 생성한 JSON에 문법 오류가 있습니다. 다시 시도해 주세요.")

    slides = result.get("slides", [])
    for idx, slide in enumerate(slides, 1):
        slide["page"] = idx
    result["total_pages"] = len(slides)
    return result
