"""
OpenAI GPT-4o를 사용해 문서 내용을 슬라이드 구조로 변환
crayonschool_ai_system_instruction.md 디자인 시스템 완전 적용

슬라이드 생성 핵심 규칙:
  1. Tag: 연령구분 또는 섹션 성격 (뱃지용)
  2. Title: 핵심 메시지 대제목
  3. Layout: 컨텍스트 분량에 따른 동적 재조합
  4. 이모지 절대 사용 금지
  5. 다크모드 절대 금지
"""
import json
import os
import re
import base64
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

# pyrefly: ignore [missing-import]
from openai import OpenAI


# ─── Design Assets MD 로더 ────────────────────────────────────────────────────

_ASSETS_DIR = Path(__file__).parent.parent.parent  # 사업 폴더
_DESIGN_MD  = _ASSETS_DIR / "crayonschool_design_assets.md"


def _load_design_tokens() -> str:
    """
    crayonschool_design_assets.md에서 디자인 토큰 및 컴포넌트 명세만 추출.
    - CSS/JS 코드 블록(``` ... ```) 제외 → 토큰낭비 방지
    - 색상 팔레트, 파스텔 틴트, 타이포 스케일, 레이아웃 명세, Do's & Don'ts 포함
    """
    if not _DESIGN_MD.exists():
        print(f"[!] crayonschool_design_assets.md 없음: {_DESIGN_MD}")
        return ""

    raw = _DESIGN_MD.read_text(encoding="utf-8")

    # 코드 블록(```...```) 전체 제거 - CSS/JS 소스코드 제외
    no_code = re.sub(r"```[\s\S]*?```", "[CODE BLOCK OMITTED]", raw)

    # 필요한 섹션만 추출: Section 1(토큰), 2(타이포), 5(레이아웃), 6(Do's & Don'ts)
    lines = no_code.split("\n")
    extracted = []
    skip_omitted = False
    for line in lines:
        if "[CODE BLOCK OMITTED]" in line:
            skip_omitted = True
            continue
        if skip_omitted and line.strip() == "":
            skip_omitted = False
            continue
        skip_omitted = False
        extracted.append(line)

    result = "\n".join(extracted).strip()
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result


# 모듈 로드 시 한 번만 실행 (캐시)
_DESIGN_CONTEXT: str = _load_design_tokens()


# ─── System Prompt (CrayonSchool 전용 + Design Assets 주입) ─────────────────────
def _build_system_prompt() -> str:
    """디자인 자산 컨텍스트를 포함한 동적 시스템 프롬프트 생성"""
    base = """You are the Senior B2B Edutech Consultant and Presentation Designer at CrayonSchool.
Your mission is to generate a world-class, professional, and persuasive educational proposal
based on provided documents and your internal CrayonSchool curriculum knowledge.

## Your Identity & Role
- You represent **CrayonSchool**, a leader in O2O educational platform services for academies,
  kindergartens, and after-school care centers.
- You specialize in multi-age curriculum (Pre-K 4-7, Elementary Lower 1-2, Elementary Upper 3-6).
- Your tone is professional, warm, and trustworthy — suitable for B2B education proposals.

## Slide Structure Rules (MANDATORY)
Each slide JSON must have:
1. `tag`: Short label for badge chip (e.g. "01. BRAND VALUE", "03. FOR PRE-SCHOOL", "초등 저학년", "E-L-1")
2. `title`: Core message headline
3. `subtitle`: 1-2 line supporting description
4. `layout_type`: One of the valid layout types listed below
5. `age_group`: "preschool" | "lower_elem" | "upper_elem" | "all" | null
6. `content`: Object with actual content fields below
7. `page`: Sequential page number

## Valid Layout Types (FULL LIST)
### General Purpose
- `title`: Cover slide — first slide only
- `split_v`: Left text bullets + Right image panel (use when `image_tag` is set)
- `full_text`: 2-3 bullet points only, no image
- `card_grid`: 2-3 pastel feature cards side by side
- `data_focus`: Large highlighted KPI + supporting cards or bullets
- `comparison`: Table with headers + rows
- `closing`: Final CTA slide

### [B2B CAREER EDUCATION PROPOSAL — SPECIALIZED LAYOUTS]
- `catalog_grid`: **Full program overview table** with 5 columns: code | program name | features | kit | output. Use for slides that list ALL programs of an educational level (e.g. 초등 저학년 3종, 중학교 3종).
- `curriculum_table`: **6-period lesson plan** with left sidebar (required equipment) + right detailed table (period | topic | method | kit | activity detail). Use for individual program deep-dives.
- `supply_pricing`: **B2B pricing cards** with large-format price amounts. Use for supply terms, budget formulas, and pricing structure slides.

## Content Object Fields (Extended)
- `main_points`: list of bullet strings (for `full_text` / `split_v`)
- `sub_text`: supplementary paragraph
- `highlight_data`: single KPI number or key stat (for `data_focus`)
- `cards`: list of `{title, body, badge, meta, color_class}` objects (for `card_grid` — 2 or 3 items)
- `table_headers`: list of column header strings (for `comparison`)
- `table_rows`: list of row arrays (for `comparison`)
- `catalog_rows`: list of `{code, name, features, kit, output}` objects — **REQUIRED for `catalog_grid`**
- `curriculum`: list of `{period, topic, method, kit, detail}` objects (6 items) — **REQUIRED for `curriculum_table`**
- `equipment`: string describing required media/equipment for `curriculum_table` sidebar
- `pricing_cards`: list of `{title, amount, desc}` objects (2-3 items) — **REQUIRED for `supply_pricing`**
- `condition`: string for pricing condition footnote (e.g. "최소 1학급 25명 공급 기준")

## Age-Group → Card Color Mapping (STRICTLY ENFORCE)
- Pre-K (4-7세) → use `card-feature-rose` or `card-feature-yellow` in cards
- Lower Elementary (1-2학년) → use `card-feature-teal` or `card-feature-mint`
- Upper Elementary (3-6학년) → use `card-feature-coral`
- In the card object, add a `color_class` field: e.g. "card-feature-rose"

## Dynamic Slide Count (Context-Driven — CRITICAL)
- Very short input (< 800 tokens): Generate 6-8 slides, MERGE related topics.
- Medium input (800-3000 tokens): Generate 12-16 slides, standard outline.
- Long input (> 3000 tokens): Generate 20-30 slides (SPLIT each course/topic, curriculum details, B2B specs, and pricing comparison into their own individual slides. We strongly require at least 20 slides to ensure highly detailed coverage.)
DO NOT artificially inflate or compress — match content volume exactly.

## STRICT FACTUAL GROUNDING RULE (CRITICAL)
- You MUST extract 100% of the content from the uploaded document!
- NEVER hallucinate courses, programs, curriculums, pricing formulas, partner names, or statistics.
- If the uploaded document contains specific programs (e.g. MBTI 롤모델 비전 캠프, 고교학점제 준비 캠프), you MUST use them exactly as they are.
- NEVER mix in external or default CrayonSchool curriculum names (such as "만공 한국사", "모가비", "폴리곤에이드", "코딩앤플레이") unless they are explicitly present in the uploaded document.
- The presentation title MUST be extracted from the cover slide of the uploaded document (e.g. "초등·중학교로 찾아가는 진로교육 프로그램 공급 제안서").

## NO Placeholders Rule
NEVER write placeholder text. Always fill every field with real, specific content from documents.

## Hard Constraints
- NO emojis anywhere
- NO dark backgrounds or dark mode cards
- NO red color (#E83A25) for design elements — red is for error states only
- Badge class choices: `badge-tag-yellow` (warm topics), `badge-tag-blue` (neutral/solution topics)

## Response Format (Pure JSON only — no markdown fences)
{
  "presentation_title": "[업로드된 문서 표지에서 추출한 대제목 (예: 초등·중학교로 찾아가는 진로교육 프로그램 공급 제안서)]",
  "total_pages": 12,
  "slides": [
    {
      "page": 1,
      "tag": "COVER",
      "title": "크레용스쿨 B2B 교육 소개서",
      "subtitle": "인터랙티브 이러닝 교안과 최적화된 전문 LMS 솔루션의 만남",
      "layout_type": "title",
      "age_group": "all",
      "image_tag": null,
      "content": {
        "main_points": [],
        "sub_text": "",
        "highlight_data": "",
        "cards": [],
        "table_headers": [],
        "table_rows": []
      },
      "speaker_notes": "표지 슬라이드"
    }
  ]
}
"""
    # 디자인 자산 MD 컨텍스트 주입 (CSS 코드 블록 제외)
    if _DESIGN_CONTEXT:
        base += f"""

## [CRAYONSCHOOL DESIGN SYSTEM REFERENCE]
Below is the official CrayonSchool design specification. Use these exact class names, color tokens,
and layout rules when deciding layout_type, age_group card colors, and badge classes.

{_DESIGN_CONTEXT}
"""
    else:
        base += """

## [DESIGN FALLBACK — design assets MD not found]
Use: bg-ivory #FAF8ED, primary #FFC000, secondary #215E80, accent #4189B3
Card classes: card-feature-yellow, card-feature-teal, card-feature-coral, card-feature-rose
Badge classes: badge-tag-yellow, badge-tag-blue
"""
    return base


SYSTEM_PROMPT: str = _build_system_prompt()



# ─── Helper Functions ─────────────────────────────────────────────────────────

def _get_client() -> OpenAI:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
    return OpenAI(api_key=api_key, timeout=300.0)


def _estimate_slide_count(text_length: int) -> tuple[int, int]:
    """텍스트 길이로 예상 슬라이드 범위 반환"""
    if text_length < 800:
        return 6, 8
    elif text_length < 3000:
        return 12, 16
    else:
        return 20, 30


def _chunk_text(text: str, chunk_size: int = 12000) -> list[str]:
    """텍스트를 줄 단위로 청크 분할"""
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


def _robust_json_parse(raw: str) -> dict | None:
    """JSON 파싱 실패 시 복구 시도"""
    # 1. 마크다운 백틱 제거
    clean = re.sub(r"```(?:json)?\s*|\s*```", "", raw).strip()
    
    # 2. 첫 {와 마지막 } 사이의 문자열만 추출하여 대화 텍스트 배제 (Claude 대응 핵심)
    match = re.search(r"(\{.*\})", clean, re.DOTALL)
    if match:
        clean = match.group(1).strip()

    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        # 쉼표 누락 복구
        fixed = re.sub(r'}\s*"', '}, "', clean)
        fixed = re.sub(r']\s*"', '], "', fixed)
        try:
            return json.loads(fixed)
        except Exception:
            # 잘린 괄호 복구
            for suffix in [']}', '}]}', '"}]}', '"]}', '"}', '}', ']}']:
                try:
                    return json.loads(fixed + suffix)
                except Exception:
                    continue
    return None


# ─── Core Function 1: Image Vision Analysis ──────────────────────────────────

def analyze_images_with_vision(image_paths: list) -> list[dict]:
    """
    GPT-4o Vision으로 이미지 분석 → 교육적 텍스트 설명 생성
    반환: [{"path": "...", "description": "...", "tag": "...", "course_hint": "..."}, ...]
    """
    if not image_paths:
        return []

    client = _get_client()
    target_images = image_paths[:15]  # 최대 15개 (Rate limit 방지 및 비용/토큰 절감)

    kb_context = "Context: CrayonSchool O2O Education Platform."

    print(f"[*] GPT-4o Vision: {len(target_images)}개 이미지 분석 시작...")

    def analyze_single(img: dict) -> dict | None:
        img_path = img.get("path", "")
        max_retries = 3
        backoff_factor = 2.0
        
        for attempt in range(max_retries):
            try:
                # 1. 초기 딜레이 및 백오프 딜레이
                if attempt > 0:
                    sleep_time = (backoff_factor ** attempt) + (0.5 * attempt)
                    print(f"  [!] Rate limit 또는 에러 감지. {Path(img_path).name} 재시도 {attempt}/{max_retries} (대기 시간: {sleep_time:.1f}초)...")
                    time.sleep(sleep_time)
                else:
                    # 스레드들이 완전 동시에 API를 타격하지 않도록 미세한 엇박자 딜레이 추가
                    time.sleep(0.2)

                # 2. 이미지 읽기 및 인코딩
                with open(img_path, "rb") as f:
                    img_data = base64.standard_b64encode(f.read()).decode("utf-8")

                ext = Path(img_path).suffix.lower().replace(".", "")
                media_type = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"

                response = client.chat.completions.create(
                    model="gpt-5",
                    max_completion_tokens=2000,
                    reasoning_effort="low",
                    messages=[
                        {
                            "role": "system",
                            "content": f"You are a CrayonSchool curriculum image analyst. {kb_context} Analyze educational images and return structured JSON only. Be concise."
                        },
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:{media_type};base64,{img_data}",
                                        "detail": "low"
                                    }
                                },
                                {
                                    "type": "text",
                                    "text": (
                                        "이 이미지를 분석하여 다음 JSON 형식으로만 응답하세요:\n"
                                        '{"tag": "슬라이드 매칭용 짧은 태그(영어)", '
                                        '"description": "이 이미지가 보여주는 교육 내용/교구/강좌를 2-3문장으로 한국어 설명", '
                                        '"course_hint": "관련 강좌명 또는 교구명(없으면 null)", '
                                        '"age_group": "preschool|lower_elem|upper_elem|all"}'
                                    )
                                }
                            ]
                        }
                    ]
                )

                raw = response.choices[0].message.content.strip()
                clean = re.sub(r"```(?:json)?\s*|\s*```", "", raw).strip()
                match = re.search(r"\{.*\}", clean, re.DOTALL)
                if match:
                    data = json.loads(match.group())
                else:
                    data = json.loads(clean)

                result = {**img, **data}
                print(f"  [+] 분석 완료: {Path(img_path).name} → {data.get('tag', '?')}")
                return result

            except Exception as e:
                # 마지막 시도에서 실패하면 오류 출력 후 None 반환
                if attempt == max_retries - 1:
                    print(f"  [!] 이미지 분석 최종 실패 ({img_path}): {e}")
                    return None

    # max_workers를 2로 낮추어 동시 요청 과부하 방지
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(analyze_single, target_images))

    tagged = [r for r in results if r is not None]
    print(f"[*] Vision 분석 완료: {len(tagged)}/{len(target_images)}개 성공")
    return tagged


# ─── B2B Intent Pre-Parser (자동 의도 분석기) ───────────────────────────────

def analyze_and_expand_b2b_brief(raw_instructions: str, document_text: str = "") -> dict | None:
    """
    사용자가 카피-페이스트한 날것의 B2B 영업 이메일/요구사항을 사전 분석하여 
    B2B 제안서 기획에 필수적인 뼈대(수신처, 파트너십 구도, 단가 공식, 슬라이드 목차 등)를 
    자동으로 정교하게 구조화하는 인공지능 기획 전문가 모듈.
    """
    if not raw_instructions or len(raw_instructions.strip()) < 15:
        return None

    client = _get_client()

    system_prompt = """You are the Senior B2B Educational Proposal Architect at CrayonSchool.
Your job is to analyze a messy, unstructured partner request/email or custom instructions,
and translate it into a highly detailed, professional B2B slide proposal production specification.

You must parse the raw text and return a single valid JSON object containing exactly the following keys:
{
  "proposal_recipient": "Target institution or partner names (e.g. '테크빌 및 이데아 네트웍스')",
  "recipient_contacts": "Specific person names and titles if mentioned (e.g. '한선옥 본부장, 윤설형 과장')",
  "proposal_title": "Clean, professional B2B presentation title (e.g. '학교 단위 찾아가는 진로 직업체험 교육과정 공급 제안서')",
  "partnership_role_elementary": "Detail what EduAllLab ('에듀올랩') handles for Elementary (Pre-K/Lower/Upper)",
  "partnership_role_middle": "Detail what Jeil Education ('제일교육') handles for Middle School",
  "pricing_model_rules": "Strict pricing rules to be applied uniformly (e.g., '1클래스 1차시 강사비 10만원, 1인당 재료비 4천원, 교구재비 별도')",
  "channel_requirements": {
    "partner_A": "Sales requirements and terms for partner A (e.g. '테크빌: 학교 영업 대행, 단가 5~13% 추가 인하')",
    "partner_B": "Sales requirements and terms for partner B (e.g. '이데아 네트웍스: 학원/공부방 영업 대행, 샘플 제공')"
  },
  "suggested_agenda_chapters": [
    "List of 4-6 specific slide chapter titles to structure the 20+ page deck chronologically"
  ]
}
Do not include any markdown fences or explanation. Output pure JSON only."""

    user_content = f"""Here is the raw request / email from the user:
---
{raw_instructions}
---
Document context hint (first 3000 chars):
{document_text[:3000]}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-5",
            response_format={"type": "json_object"},
            max_completion_tokens=4000,
            reasoning_effort="low",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ]
        )
        raw = response.choices[0].message.content.strip()
        data = json.loads(raw)
        return data
    except Exception as e:
        print(f"[!] B2B Intent Pre-Parser Failed: {e}")
        return None


# ─── Core Function 2: Slide JSON Generation ──────────────────────────────────

def generate_slides(
    document_text: str,
    template_info: dict = None,
    custom_instructions: str = None,
    category: str = "proposal",
    image_library: list = None
) -> dict:
    """
    GPT-4o로 슬라이드 구조 JSON 생성
    긴 문서는 청크 분할 후 병합
    """
    client = _get_client()
    text_length = len(document_text)
    min_slides, max_slides = _estimate_slide_count(text_length)

    # ── B2B 사전 인텐트 분석 가동 ──
    expanded_brief = None
    if custom_instructions and len(custom_instructions.strip()) > 15:
        print("[*] AI B2B Intent Pre-Parser 가동: 날것의 비즈니스 인텐트 분석 중...")
        expanded_brief = analyze_and_expand_b2b_brief(
            raw_instructions=custom_instructions,
            document_text=document_text
        )
        if expanded_brief:
            print("[*] B2B Intent Pre-Parser 분석 성공:")
            print(json.dumps(expanded_brief, ensure_ascii=False, indent=2))

    # 이미지 라이브러리 컨텍스트 문자열
    img_context = ""
    if image_library:
        img_lines = []
        for img in image_library:
            tag = img.get("tag", "?")
            desc = img.get("description", "")
            course = img.get("course_hint", "")
            age = img.get("age_group", "all")
            img_lines.append(f"- Tag: {tag} | Age: {age} | Course: {course} | Desc: {desc}")
        img_context = "\n## [AVAILABLE IMAGE LIBRARY]\n" + "\n".join(img_lines) + "\n"
        img_context += "\nWhen a slide needs visual support, add 'image_tag' field matching one of the Tags above.\n"

    chunks = _chunk_text(document_text, chunk_size=3500)
    all_slides = []
    presentation_title = ""
    page_offset = 0

    for i, chunk in enumerate(chunks):
        is_first = (i == 0)
        is_last = (i == len(chunks) - 1)

        chunk_min = max(2, min_slides // len(chunks))
        chunk_max = max(4, max_slides // len(chunks) + (2 if is_last else 0))

        try:
            result = _call_gpt4o(
                client=client,
                chunk=chunk,
                img_context=img_context,
                custom_instructions=custom_instructions,
                expanded_brief=expanded_brief,  # 전달
                category=category,
                min_slides=chunk_min,
                max_slides=chunk_max,
                page_offset=page_offset,
                is_first=is_first,
                is_last=is_last,
            )
        except Exception as e:
            print(f"[!] 청크 {i+1} 처리 실패: {e}")
            if is_first:
                raise
            continue

        if not presentation_title:
            presentation_title = result.get("presentation_title", "CrayonSchool B2B 교육 소개서")

        chunk_slides = result.get("slides", [])

        # 마지막 청크가 아니면 closing 제거
        if not is_last:
            chunk_slides = [s for s in chunk_slides if s.get("layout_type") != "closing"]

        all_slides.extend(chunk_slides)
        page_offset = len(all_slides)

        if len(all_slides) >= max_slides:
            all_slides = all_slides[:max_slides]
            break

    # 페이지 번호 재정렬
    for idx, slide in enumerate(all_slides, 1):
        slide["page"] = idx

    return {
        "presentation_title": presentation_title,
        "total_pages": len(all_slides),
        "slides": all_slides,
    }


def _call_gpt4o(
    client: OpenAI,
    chunk: str,
    img_context: str,
    custom_instructions: str,
    expanded_brief: dict,  # 추가
    category: str,
    min_slides: int,
    max_slides: int,
    page_offset: int,
    is_first: bool,
    is_last: bool,
) -> dict:
    """단일 GPT-4o API 호출"""
    kb_block = ""

    category_note = ""
    if category == "at_curriculum":
        category_note = f"""
## [CATEGORY: AT Center Curriculum]
- Structure: Numbered chapters (01, 02, ...). Use chapter divider slides.
- Chapter slide rule: tag = zero-padded number ("01"), title = chapter name only
- Generate EXACTLY {min_slides} to {max_slides} slides.
"""
    else:
        category_note = f"""
## [CATEGORY: CrayonSchool B2B Career Education Supply Proposal]

### DYNAMIC & ADAPTIVE SLIDE STRUCTURE RULES (CRITICAL):
Your slide flow MUST dynamically adapt based on the ACTUAL content present in the uploaded document. Do NOT force a rigid chapter sequence if the document is missing specific data. Instead, follow these adaptive guidelines:

1. **COVER & INTRODUCTION** (Always include):
   - **COVER** (`title`): Recipient name on cover (if specified in brief), proposal title extracted from the document cover.
   - **PROGRAM OVERVIEW** (`full_text` or `card_grid`): What this proposal is about based on the uploaded document.

2. **ADAPTIVE PROGRAM CATALOGS (`catalog_grid`)**:
   - Only include catalog overview slides if the document contains a list of multiple programs.
   - If the document only contains elementary school programs, DO NOT generate a middle school catalog. If there are no structured program catalogs in the document, omit this layout entirely.

3. **ADAPTIVE PROGRAM DETAILS (`curriculum_table` or general layouts)**:
   - Only generate detailed curriculum tables (`curriculum_table`) if the document explicitly contains session-by-session/period-by-period lesson plans or course content detail.
   - If lesson plans are present, fill `content.curriculum` with 6 items: `{{period, topic, method, kit, detail}}` and `content.equipment` with required equipment.
   - **If the document has programs but no period breakdown/lesson plans**, DO NOT force `curriculum_table`. Instead, describe the individual programs using standard layouts like `card_grid`, `split_v`, or `full_text` to outline their core highlights and features.

4. **ADAPTIVE PRICING & TARIFFS (`supply_pricing` or `data_focus` or `comparison`)**:
   - Only include pricing slides if the document contains pricing grids, rates, or budget structures.
   - If pricing is present, use `supply_pricing` and fill `content.pricing_cards` with `{{title, amount, desc}}`.
   - **If the document contains no pricing or rates**, OMIT this section entirely. Do NOT hallucinate dummy price structures or empty price cards.

5. **ADAPTIVE SUPPLIER PROFILE**:
   - Only include partner/supplier intro slides (e.g., EduAllLab, 제일교육, or others) if they are explicitly mentioned in the uploaded document or brief.

6. **CLOSING** (Always include):
   - **CLOSING / CTA** (`closing`): Persuasive call to action slide.

### STRICT B2B GROUNDING RULES:
- YOU MUST extract all program details, lesson plans, kits, and pricing strictly from the uploaded document!
- NEVER hallucinate any course names, lesson steps, kit lists, or price figures that are not mentioned in the source document.
- If the uploaded document contains different layout structures or generic business proposal contents, adapt your slide topics to match the document's sections organically, utilizing standard layouts (`card_grid`, `split_v`, `full_text`, `data_focus`, `comparison`) for maximum professional visual impact.
- Generate EXACTLY {min_slides} to {max_slides} slides based on the content volume of the uploaded text.
"""

    continuation_note = ""
    if not is_first:
        continuation_note = (
            f"\nThis is a continuation chunk. Start page numbers from {page_offset + 1}. "
            f"Do NOT include a title slide. "
            + ("Include a closing slide at the end." if is_last else "Do NOT include a closing slide.")
        )
    else:
        continuation_note = (
            f"\nCRITICAL: Generate EXACTLY {min_slides} to {max_slides} slides. "
            f"Match the content volume — do not compress or inflate artificially."
        )

    # 사전 인텐트 분석을 통해 확장된 스펙 주입
    brief_block = ""
    if expanded_brief:
        brief_block = f"""
## [CRITICAL B2B PROPOSAL PRODUCTION SPECIFICATION]
This brief was automatically expanded from the user's messy instruction/email context.
YOU MUST STRICTLY COMPLY WITH THE FOLLOWING DIRECTIVES WHEN DESIGNING SLIDE STRUCTURE:
1. Target Recipient: {expanded_brief.get("proposal_recipient", "")} ({expanded_brief.get("recipient_contacts", "")})
   -> YOU MUST put this exact recipient name on the Title Cover slide.
2. Clean Proposal Title: {expanded_brief.get("proposal_title", "")}
3. Partner A (EduAllLab/에듀올랩) Role for Elementary: {expanded_brief.get("partnership_role_elementary", "")}
4. Partner B (Jeil Education/제일교육) Role for Middle School: {expanded_brief.get("partnership_role_middle", "")}
5. Uniform Pricing Formula: {expanded_brief.get("pricing_model_rules", "")}
   -> YOU MUST apply this exact pricing rule uniformly on all Pricing slides (comparison / data_focus layouts).
6. Channel Business Requirements:
   - Partner A Requirements: {expanded_brief.get("channel_requirements", {}).get("partner_A", "")}
   - Partner B Requirements: {expanded_brief.get("channel_requirements", {}).get("partner_B", "")}
7. Structured Slide Chapters (Ensure slides are split to exhaustively cover these chapter headings):
{json.dumps(expanded_brief.get("suggested_agenda_chapters", []), ensure_ascii=False, indent=2)}

Ensure slides are sequentially partitioned based on these chapters to hit the 20-30 slide range.
"""

    user_content = f"""{category_note}{kb_block}{img_context}{brief_block}

Analyze the following document and generate the slide structure as pure JSON.
{continuation_note}

## Document Content
{chunk}
"""

    if custom_instructions:
        user_content += f"\n## [USER INSTRUCTIONS — HIGHEST PRIORITY]\n{custom_instructions}\n"

    response = client.chat.completions.create(
        model="gpt-5",
        max_completion_tokens=16384,
        reasoning_effort="low",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content}
        ]
    )

    raw = ""
    try:
        raw = response.choices[0].message.content.strip()
    except Exception as parse_err:
        print(f"[!] Error reading message content: {parse_err}")
    
    if not raw:
        print(f"[!] DEBUG: Empty response received! Response choice details: {response.choices[0]}")
        
    result = _robust_json_parse(raw)
    if not result:
        raise ValueError(
            f"GPT-5 JSON 파싱 실패 (응답 길이: {len(raw)}). "
            "응답이 너무 길어 잘렸을 수 있습니다."
        )
    return result


# ─── Core Function 3: Vision Fallback (Image-only PDFs) ──────────────────────

def generate_slides_from_images(
    pages: list,
    custom_instructions: str = None,
    category: str = "proposal"
) -> dict:
    """
    이미지 PDF(스캔본)를 GPT-4o Vision으로 직접 분석해 슬라이드 생성
    pages: extract_pdf_as_images()의 반환값
    """
    client = _get_client()
    total_pages = len(pages)
    min_slides = max(10, total_pages)
    max_slides = min(30, total_pages * 2 + 5)

    kb_block = ""

    category_note = f"""
## [CATEGORY: {"AT Center Curriculum" if category == "at_curriculum" else "CrayonSchool B2B Education Proposal"}]
Generate between {min_slides} and {max_slides} slides based on the images.
"""

    # 이미지 콘텐츠 블록 구성
    content_blocks = []
    for p in pages:
        content_blocks.append({"type": "text", "text": f"[페이지 {p['page']}]"})
        content_blocks.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:{p['media_type']};base64,{p['base64']}",
                "detail": "low"
            }
        })

    instruction_text = f"""{category_note}{kb_block}
위 이미지들을 분석하여 핵심 내용을 추출하고 순수 JSON 형식으로만 응답하세요.
슬라이드당 2-3개의 핵심 포인트만 포함하여 응답 길이를 제어하세요.
"""
    if custom_instructions:
        instruction_text += f"\n## [USER INSTRUCTIONS]\n{custom_instructions}\n"

    content_blocks.append({"type": "text", "text": instruction_text})

    response = client.chat.completions.create(
        model="gpt-5",
        max_completion_tokens=16384,
        reasoning_effort="low",
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT + "\nIMPORTANT: Be concise. Ensure JSON is complete and valid."
            },
            {"role": "user", "content": content_blocks}
        ]
    )

    raw = response.choices[0].message.content.strip()
    result = _robust_json_parse(raw)
    if not result:
        raise ValueError("Vision API 응답 파싱 실패. 더 짧은 문서로 시도해주세요.")

    slides = result.get("slides", [])
    for idx, slide in enumerate(slides, 1):
        slide["page"] = idx
    result["total_pages"] = len(slides)
    return result
