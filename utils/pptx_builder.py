"""
슬라이드 구조 + 이미지 + 양식 색상을 반영하여 PPTX 생성

필수 규칙:
- Tag: 슬라이드 좌상단 (y=0.25in 고정)
- Title: y=0.65in 고정
- Subtitle: y=1.35in 고정
- Body: y=1.8in 고정
- Page Number: 우측 하단 (y=6.9in 고정)
- 이모지 사용 금지
- 16:9 고정
"""
import os
import re
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt, Emu


# ─── 색상 유틸 ───────────────────────────────
def hex_to_rgb(hex_str: str) -> RGBColor:
    h = hex_str.lstrip("#")
    if len(h) != 6:
        return RGBColor(0x1E, 0x27, 0x61)
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def build_palette(template_info: dict) -> dict:
    """템플릿 정보에서 색상 팔레트 구성"""
    colors = template_info.get("colors", []) if template_info else []
    dark_bg = template_info.get("has_dark_bg", False) if template_info else False

    # 크레용스쿨 양식: #215E80(진파랑), #4189B3(중간파랑), #FFD018(노랑), #585958(회색)
    if len(colors) >= 2:
        primary = hex_to_rgb(colors[0])
        accent = hex_to_rgb(colors[1]) if len(colors) > 1 else hex_to_rgb("#4A90D9")
        highlight = hex_to_rgb(colors[2]) if len(colors) > 2 else hex_to_rgb("#FFD018")
    else:
        primary = RGBColor(0x1E, 0x27, 0x61)
        accent = RGBColor(0x4A, 0x90, 0xD9)
        highlight = RGBColor(0xFF, 0xD0, 0x18)

    if dark_bg:
        bg = RGBColor(0x1A, 0x1A, 0x2E)
        body_text = RGBColor(0xEE, 0xEE, 0xEE)
    else:
        # 에듀올랩 / 크레용스쿨 고유 브랜드 아이보리 배경 및 차콜 블랙 글자 통일
        bg = RGBColor(0xFA, 0xF8, 0xED)
        body_text = RGBColor(0x11, 0x11, 0x11)

    return {
        "primary": primary,
        "accent": accent,
        "highlight": highlight,
        "bg": bg,
        "title_text": primary,
        "body_text": body_text,
        "tag_bg": primary,
        "tag_text": RGBColor(0xFF, 0xFF, 0xFF),
        "page_num": RGBColor(0x99, 0x99, 0x99),
        "sub_title": accent,
        "divider": accent,
        "card_bg": RGBColor(0xF4, 0xF7, 0xFC),
    }


# ─── 이모지 제거 ────────────────────────────
def remove_emoji(text: str) -> str:
    if not text:
        return ""
    pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF"
        "\U00002700-\U000027BF\U0001F900-\U0001F9FF"
        "\U00002600-\U000026FF"
        "]+",
        flags=re.UNICODE,
    )
    return pattern.sub("", str(text)).strip()


# ─── 메인 빌드 함수 ──────────────────────────
# ─── 레이아웃 비율 파싱 ──────────────────────
def parse_ratio(ratio_str: str) -> float:
    """ '4:6' 같은 문자열을 텍스트 영역의 비율(0.4)로 변환 """
    try:
        if not ratio_str or ":" not in ratio_str:
            return 0.55
        parts = ratio_str.split(":")
        left = float(parts[0])
        right = float(parts[1])
        return left / (left + right)
    except Exception:
        return 0.55


# ─── 메인 빌드 함수 ──────────────────────────
def build_presentation(
    slides_data: dict,
    template_path: str = None,
    output_path: str = None,
    images: list = None,           # 이미지 라이브러리 (태그 포함)
    template_info: dict = None,    
    category: str = "proposal"     # 추가: 크레용스쿨 또는 AT 커리큘럼 양식 분기용
) -> str:
    palette = build_palette(template_info)
    prs = Presentation()
    prs.slide_width = Inches(13.33)   # 16:9
    prs.slide_height = Inches(7.5)

    W = prs.slide_width
    H = prs.slide_height
    blank = prs.slide_layouts[6]

    slide_list = slides_data.get("slides", [])
    total = len(slide_list)

    # 이미지 매핑 고도화 (유연한 검색 지원)
    def find_best_image(tag_query):
        if not tag_query or not images: return None
        tag_query = tag_query.lower()
        # 1. 완전 일치 검색
        for img in images:
            if img["tag"].lower() == tag_query: return img
        # 2. 부분 일치 검색
        for img in images:
            if tag_query in img["tag"].lower() or img["tag"].lower() in tag_query: return img
        # 3. 설명(Description) 기반 검색
        for img in images:
            if tag_query in img.get("description", "").lower(): return img
        return None

    for i, slide_info in enumerate(slide_list):
        slide = prs.slides.add_slide(blank)
        
        l_type = slide_info.get("layout_type", slide_info.get("layout", "full_text"))
        ratio = parse_ratio(slide_info.get("layout_ratio", "1:0"))
        img_tag = slide_info.get("image_tag", "")

        # 1. 슬라이드 자체의 기본 배경색 채우기
        _set_bg(slide, palette["bg"])

        # 2. 고해상도 기초 배경 템플릿(PNG) 오버레이 주입
        _draw_slide_background(slide, W, H, l_type, category)

        # 최적의 이미지 매칭
        current_img = find_best_image(img_tag)
        
        # 만약 이미지가 필요한 레이아웃인데 못 찾았다면, 순차적으로 하나씩 할당 (이미지 실종 방지)
        if not current_img and l_type in ["split_v", "split_h", "data_focus"] and images:
            current_img = images[i % len(images)]

        # 렌더링 분기 (이미지 실종 방지 및 챕터 렌더링 추가)
        if l_type == "title":
            _render_title(slide, slide_info, W, H, palette, category=category)
        elif l_type == "chapter":
            _render_chapter(slide, slide_info, W, H, palette, category=category)
        elif l_type == "closing":
            _render_closing(slide, slide_info, W, H, palette)
        elif l_type == "split_v":
            _render_split_v(slide, slide_info, W, H, palette, current_img, ratio)
        elif l_type == "split_h":
            _render_split_h(slide, slide_info, W, H, palette, current_img, ratio)
        elif l_type == "data_focus":
            _render_data(slide, slide_info, W, H, palette, current_img)
        else:
            # full_text or default
            _render_content(slide, slide_info, W, H, palette, current_img)

        # 고정 요소 (AT 커리큘럼의 표지/챕터는 템플릿 고유 무드 유지를 위해 태그/페이지 번호 드로잉 생략)
        if category != "at_curriculum" or l_type not in ["title", "chapter"]:
            _add_tag(slide, remove_emoji(slide_info.get("tag", "")), W, H, palette)
            _add_page_number(slide, slide_info.get("page", 1), total, W, H, palette)

        notes = slide_info.get("speaker_notes", "")
        if notes:
            slide.notes_slide.notes_text_frame.text = remove_emoji(notes)

    if not output_path:
        output_path = "output_presentation.pptx"
    prs.save(output_path)
    return output_path


# ─── 배경 ───────────────────────────────────
def _set_bg(slide, color: RGBColor):
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color


# ─── 고정 요소 ──────────────────────────────
def _add_tag(slide, tag: str, W, H, palette: dict):
    """Tag — 좌상단 y=0.25in 고정"""
    if not tag:
        return
    left, top = Inches(0.4), Inches(0.2)
    width, height = Inches(2.0), Inches(0.32)

    shape = slide.shapes.add_shape(1, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = palette["tag_bg"]
    shape.line.fill.background()

    tf = shape.text_frame
    tf.word_wrap = False
    p = tf.paragraphs[0]
    p.text = tag
    p.alignment = PP_ALIGN.CENTER
    run = p.runs[0]
    run.font.size = Pt(9)
    run.font.bold = True
    run.font.color.rgb = palette["tag_text"]
    run.font.name = "Malgun Gothic"
    # 수직 중앙 정렬
    from pptx.oxml.ns import qn
    from lxml import etree
    txBody = tf._txBody
    bodyPr = txBody.find(qn("a:bodyPr"))
    if bodyPr is not None:
        bodyPr.set("anchor", "ctr")


def _add_page_number(slide, page_num: int, total: int, W, H, palette: dict):
    """Page number — 우측 하단 y=6.9in 고정"""
    width, height = Inches(1.4), Inches(0.3)
    left = W - width - Inches(0.25)
    top = H - height - Inches(0.18)

    tx = slide.shapes.add_textbox(left, top, width, height)
    tf = tx.text_frame
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.RIGHT
    run = p.add_run()
    run.text = f"{page_num}  /  {total}"
    run.font.size = Pt(10)
    run.font.color.rgb = palette["page_num"]
    run.font.name = "Malgun Gothic"


# ─── 텍스트 오버플로우 방지 (Auto-Shrink) ─────────
def _add_text_with_autoshrink(shape, text: str, font_size: int, palette: dict, is_bullet: bool = False):
    """텍스트가 박스를 넘지 않도록 폰트 크기 자동 조절"""
    tf = shape.text_frame
    tf.word_wrap = True
    
    # 초기 설정
    p = tf.paragraphs[0]
    p.text = remove_emoji(text)
    p.font.size = Pt(font_size)
    p.font.color.rgb = palette["body_text"]
    p.font.name = "Malgun Gothic"
    
    if is_bullet:
        p.level = 0
        
    char_count = len(text)
    if char_count > 200:
        p.font.size = Pt(font_size * 0.8)
    elif char_count > 400:
        p.font.size = Pt(font_size * 0.6)


def _add_title_block(slide, title: str, subtitle: str, W, palette: dict, page_idx: int = None):
    """Title(y=0.65in) + Subtitle(y=1.35in) + 구분선 — 공통 (HTML 웹뷰어 디자인 싱크 적용)"""
    if page_idx is not None:
        # 1. 대형 페이지 번호 (left = 0.4", top = 0.42", width = 1.0", height = 1.0")
        tx_num = slide.shapes.add_textbox(Inches(0.4), Inches(0.42), Inches(1.0), Inches(1.0))
        tf_num = tx_num.text_frame
        tf_num.word_wrap = False
        p_num = tf_num.paragraphs[0]
        p_num.text = str(page_idx)
        p_num.font.size = Pt(56)  # HTML과 동일하게 압도적인 대형 크기로 렌더링
        p_num.font.bold = True
        p_num.font.color.rgb = RGBColor(0x11, 0x11, 0x11)
        p_num.font.name = "Malgun Gothic"

        # 2. 타이틀 시작 위치를 오른쪽으로 시프트 적용
        left_offset = Inches(1.4)
    else:
        left_offset = Inches(0.4)

    # 제목
    tx = slide.shapes.add_textbox(left_offset, Inches(0.62), W - left_offset - Inches(0.4), Inches(0.85))
    tf = tx.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = remove_emoji(title)
    run = p.runs[0]
    run.font.size = Pt(26)
    run.font.bold = True
    run.font.color.rgb = palette["title_text"]
    run.font.name = "Malgun Gothic"

    # 부제목 y=1.35in
    if subtitle:
        tx2 = slide.shapes.add_textbox(left_offset, Inches(1.32), W - left_offset - Inches(0.4), Inches(0.35))
        tf2 = tx2.text_frame
        p2 = tf2.paragraphs[0]
        p2.text = remove_emoji(subtitle)
        run2 = p2.runs[0]
        run2.font.size = Pt(12)
        run2.font.color.rgb = palette["sub_title"]
        run2.font.name = "Malgun Gothic"

    # 구분선 y≈1.55in
    line = slide.shapes.add_shape(1, left_offset, Inches(1.55), W - left_offset - Inches(0.4), Emu(28000))
    line.fill.solid()
    line.fill.fore_color.rgb = palette["divider"]
    line.line.fill.background()


# ─── 이미지 삽입 헬퍼 ───────────────────────
def _insert_image(slide, img_info: dict, left, top, width, height):
    """이미지를 지정 영역에 비율 유지하며 삽입 (단위 보정 완료)"""
    try:
        # 모든 단위를 강제로 정수(int)로 변환하여 python-pptx float 오류 원천 차단
        left = int(left)
        top = int(top)
        width = int(width)
        height = int(height)
        
        # python-pptx는 path만 주면 원본 크기로 삽입함
        pic = slide.shapes.add_picture(img_info["path"], left, top)
        
        # 원본 비율 계산
        orig_w, orig_h = pic.width, pic.height
        scale = min(width / orig_w, height / orig_h)
        
        new_w = int(orig_w * scale)
        new_h = int(orig_h * scale)
        
        pic.width = new_w
        pic.height = new_h
        
        # 영역 내 중앙 정렬
        pic.left = int(left + (width - new_w) // 2)
        pic.top = int(top + (height - new_h) // 2)
        return True
    except Exception as e:
        print(f"[!] Image insertion error: {e}")
        return False


# ─── 레이아웃별 렌더 ────────────────────────
def _draw_slide_background(slide, W, H, l_type, category):
    """카테고리와 슬라이드 타입에 맞게 고화질 기초 배경 템플릿(PNG) 주입"""
    try:
        # static/img 경로
        img_dir = Path(__file__).resolve().parent.parent / "static" / "img"
        bg_path = None
        
        if category == "at_curriculum":
            if l_type == "title":
                bg_path = img_dir / "at_cover.png"
            elif l_type == "chapter":
                bg_path = img_dir / "at_chapter.png"
            elif l_type != "closing":
                bg_path = img_dir / "at_content_bg.png"
        else: # proposal (크레용스쿨 / 에듀올랩 기본 테마)
            if l_type == "title":
                bg_path = img_dir / "cover.png"
                if not bg_path.exists():
                    bg_path = None
            elif l_type not in ["closing", "chapter"]:
                bg_path = img_dir / "header_bg.png"
                if not bg_path.exists():
                    bg_path = None

        if bg_path and bg_path.exists():
            # python-pptx는 추가 순서대로 레이어가 쌓이므로 최하단 배경이 됨
            if bg_path.name == "header_bg.png":
                # 상단 배너이므로 높이를 Inches(1.5) 정도로 슬라이드 상단에 딱 맞춤
                slide.shapes.add_picture(str(bg_path), 0, 0, width=W, height=Inches(1.5))
            else:
                # 전체 슬라이드를 꽉 채우는 풀블리드 배경
                slide.shapes.add_picture(str(bg_path), 0, 0, width=W, height=H)
            return True
    except Exception as e:
        print(f"[!] Background template insert failed: {e}")
    return False


def _render_chapter(slide, slide_info: dict, W, H, palette: dict, category: str = "proposal"):
    """챕터 분할 슬라이드 (AT Center 전용)"""
    tag = remove_emoji(slide_info.get("tag", "01"))
    title = remove_emoji(slide_info.get("title", ""))

    # 1. 챕터 배경 이미지 주입
    _draw_slide_background(slide, W, H, "chapter", category)

    # 2. 챕터 번호 (블루, 대형)
    tx_num = slide.shapes.add_textbox(Inches(1.2), Inches(2.2), Inches(5), Inches(1.2))
    tf_num = tx_num.text_frame
    p_num = tf_num.paragraphs[0]
    p_num.text = tag
    p_num.font.size = Pt(72)
    p_num.font.bold = True
    p_num.font.color.rgb = RGBColor(0x25, 0x50, 0xE8) # AT Blue
    p_num.font.name = "Malgun Gothic"

    # 3. 챕터 제목 (블랙, 대형)
    tx_title = slide.shapes.add_textbox(Inches(1.2), Inches(3.6), W - Inches(2.4), Inches(1.5))
    tf_title = tx_title.text_frame
    tf_title.word_wrap = True
    p_title = tf_title.paragraphs[0]
    p_title.text = title
    p_title.font.size = Pt(36)
    p_title.font.bold = True
    p_title.font.color.rgb = RGBColor(0x11, 0x11, 0x11)
    p_title.font.name = "Malgun Gothic"


# ─── 레이아웃별 렌더 ────────────────────────
def _render_title(slide, slide_info: dict, W, H, palette: dict, category: str = "proposal"):
    """표지 슬라이드 - 크레용스쿨 또는 AT 센터 테마"""
    title = remove_emoji(slide_info.get("title", ""))
    sub = remove_emoji(slide_info.get("subtitle", "") or slide_info.get("content", {}).get("sub_text", ""))

    # 1. 기초 양식 이미지 배경 주입
    bg_inserted = _draw_slide_background(slide, W, H, "title", category)

    if category == "at_curriculum":
        # AT 커리큘럼 전용 표지 텍스트 배치 (좌측 정렬, 블루 컬러)
        tx = slide.shapes.add_textbox(Inches(0.8), Inches(2.8), Inches(7.5), Inches(2.2))
        tf = tx.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title
        p.alignment = PP_ALIGN.LEFT
        run = p.runs[0]
        run.font.size = Pt(40)
        run.font.bold = True
        run.font.color.rgb = RGBColor(0x25, 0x50, 0xE8) # AT Blue
        run.font.name = "Malgun Gothic"
    else:
        # 크레용스쿨 / 에듀올랩 기본 표지 텍스트 배치
        footer_h = Inches(0.8)
        if not bg_inserted:
            # cover.png가 없을 때만 단색 배경 + 푸터 바 드로잉
            _set_bg(slide, RGBColor(0xFA, 0xF8, 0xED))
            bar = slide.shapes.add_shape(1, 0, H - footer_h, W, footer_h)
            bar.fill.solid()
            bar.fill.fore_color.rgb = palette["highlight"]
            bar.line.fill.background()

            tx_logo = slide.shapes.add_textbox(Inches(0.8), Inches(0.8), Inches(4), Inches(0.5))
            tf_logo = tx_logo.text_frame
            p_logo = tf_logo.paragraphs[0]
            p_logo.text = "EDUALL LAB"
            p_logo.font.size = Pt(24)
            p_logo.font.bold = True
            p_logo.font.color.rgb = RGBColor(0xE8, 0x3A, 0x25)

            tx_f = slide.shapes.add_textbox(Inches(0.8), H - footer_h, W - Inches(1.6), footer_h)
            tf_f = tx_f.text_frame
            p_f = tf_f.paragraphs[0]
            p_f.text = "© ㈜에듀올랩 | 크레용스쿨 전문 운영 파트너십"
            p_f.alignment = PP_ALIGN.LEFT
            p_f.font.size = Pt(12)
            p_f.font.color.rgb = RGBColor(0x33, 0x33, 0x33)
            tx_f.text_frame.margin_top = Inches(0.25)

        # 제목 및 부제목 (배경 이미지가 깔려있든 단색이든 동일 레이아웃)
        tx = slide.shapes.add_textbox(Inches(1.0), H // 2 - Inches(1.5), W - Inches(2.0), Inches(2.0))
        tf = tx.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title
        p.alignment = PP_ALIGN.CENTER
        run = p.runs[0]
        run.font.size = Pt(44)
        run.font.bold = True
        run.font.color.rgb = RGBColor(0x11, 0x11, 0x11)
        run.font.name = "Malgun Gothic"

        if sub:
            tx2 = slide.shapes.add_textbox(Inches(1.0), H // 2 + Inches(0.8), W - Inches(2.0), Inches(0.8))
            tf2 = tx2.text_frame
            tf2.word_wrap = True
            p2 = tf2.paragraphs[0]
            p2.text = sub
            p2.alignment = PP_ALIGN.CENTER
            run2 = p2.runs[0]
            run2.font.size = Pt(18)
            run2.font.color.rgb = RGBColor(0x55, 0x55, 0x55)
            run2.font.name = "Malgun Gothic"



def _render_content(slide, slide_info: dict, W, H, palette: dict, img_info: dict = None):
    """기본 콘텐츠 슬라이드 - 이미지 유무에 따라 자동 레이아웃"""
    if img_info:
        # 이미지가 있으면 split_v (좌우) 기본 적용 (중복 타이틀 블록 방지를 위해 바로 위임)
        _render_split_v(slide, slide_info, W, H, palette, img_info, ratio=0.5)
        return

    content = slide_info.get("content", {})
    page_idx = slide_info.get("page", 1)
    _add_title_block(slide, slide_info.get("title", ""), slide_info.get("subtitle", ""), W, palette, page_idx=page_idx)

    content_top = Inches(1.8)
    content_h = H - content_top - Inches(0.8)
    
    # 텍스트만 전체 너비
    tx = slide.shapes.add_textbox(Inches(0.6), content_top, W - Inches(1.2), content_h)
    tf = tx.text_frame
    tf.word_wrap = True
    
    # 폰트 크기 자동 계산 (불렛 개수에 따라)
    main_points = content.get("main_points", [])
    num_pts = len(main_points)
    base_size = 20 if num_pts <= 4 else (16 if num_pts <= 7 else 12)

    for i, pt in enumerate(main_points):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = f"• {remove_emoji(str(pt))}"
        p.font.size = Pt(base_size)
        p.font.color.rgb = palette["body_text"]
        p.space_after = Pt(8)

    if content.get("sub_text"):
        p = tf.add_paragraph()
        p.text = f"\n{remove_emoji(content['sub_text'])}"
        p.font.size = Pt(12)
        p.font.italic = True
        p.font.color.rgb = palette["page_num"]


def _render_split_v(slide, slide_info: dict, W, H, palette: dict, img_info: dict, ratio: float):
    """좌우 수직 분할 레이아웃 (ratio: 텍스트 너비 비율)"""
    content = slide_info.get("content", {})
    page_idx = slide_info.get("page", 1)
    _add_title_block(slide, slide_info.get("title", ""), slide_info.get("subtitle", ""), W, palette, page_idx=page_idx)

    margin = Inches(0.5)
    content_top = Inches(1.8)
    total_w = W - (margin * 2)
    content_h = H - content_top - Inches(0.8)

    text_w = total_w * ratio
    img_w = total_w - text_w - Inches(0.3)
    img_left = margin + text_w + Inches(0.3)

    # 텍스트 영역 (왼쪽)
    tx = slide.shapes.add_textbox(margin, content_top, text_w, content_h)
    tf = tx.text_frame
    tf.word_wrap = True
    
    # 폰트 크기 자동 계산
    main_points = content.get("main_points", [])
    num_pts = len(main_points)
    base_size = 18 if num_pts <= 4 else (14 if num_pts <= 7 else 11)

    for i, pt in enumerate(main_points):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = f"• {remove_emoji(str(pt))}"
        p.font.size = Pt(base_size)
        p.space_after = Pt(6)

    # 이미지 영역 (오른쪽)
    if img_info:
        _insert_image(slide, img_info, img_left, content_top, img_w, content_h)


def _render_split_h(slide, slide_info: dict, W, H, palette: dict, img_info: dict, ratio: float):
    """상하 수평 분할 레이아웃 (ratio: 텍스트 높이 비율)"""
    content = slide_info.get("content", {})
    page_idx = slide_info.get("page", 1)
    _add_title_block(slide, slide_info.get("title", ""), slide_info.get("subtitle", ""), W, palette, page_idx=page_idx)

    margin = Inches(0.5)
    content_top = Inches(1.8)
    total_h = H - content_top - Inches(0.8)
    
    text_h = total_h * ratio
    img_h = total_h - text_h - Inches(0.2)
    img_top = content_top + text_h + Inches(0.2)

    # 텍스트 영역 (상단)
    tx = slide.shapes.add_textbox(margin, content_top, W - (margin * 2), text_h)
    tf = tx.text_frame
    tf.word_wrap = True
    
    # 폰트 크기 자동 계산
    main_points = content.get("main_points", [])
    num_pts = len(main_points)
    base_size = 18 if num_pts <= 4 else (14 if num_pts <= 7 else 11)

    for i, pt in enumerate(main_points):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = f"• {remove_emoji(str(pt))}"
        p.font.size = Pt(base_size)
        p.space_after = Pt(4)

    # 이미지 영역 (하단)
    if img_info:
        _insert_image(slide, img_info, margin, img_top, W - (margin * 2), img_h)


def _render_two_column(slide, slide_info: dict, W, H, palette: dict, img_info: dict = None):
    """두 컬럼 슬라이드"""
    content = slide_info.get("content", {})
    title = slide_info.get("title", "")
    subtitle = slide_info.get("subtitle", "")
    left_col = content.get("left_column", content.get("main_points", [])[:3])
    right_col = content.get("right_column", content.get("main_points", [])[3:])

    page_idx = slide_info.get("page", 1)
    _add_title_block(slide, title, subtitle, W, palette, page_idx=page_idx)

    col_top = Inches(1.78)
    col_h = H - col_top - Inches(0.65)
    col_w = (W - Inches(1.2)) / 2

    for col_idx, (col_data, col_left) in enumerate([
        (left_col, Inches(0.4)),
        (right_col, Inches(0.4) + col_w + Inches(0.4)),
    ]):
        # 컬럼 배경 카드
        bg_color = palette["card_bg"] if col_idx == 0 else RGBColor(0xEA, 0xF3, 0xFF)
        bg = slide.shapes.add_shape(1, col_left, col_top, col_w, col_h)
        bg.fill.solid()
        bg.fill.fore_color.rgb = bg_color
        bg.line.color.rgb = palette["accent"]
        bg.line.width = Pt(0.5)

        # 컬럼 상단 색상 바
        bar = slide.shapes.add_shape(1, col_left, col_top, col_w, Inches(0.08))
        bar.fill.solid()
        bar.fill.fore_color.rgb = palette["primary"] if col_idx == 0 else palette["accent"]
        bar.line.fill.background()

        # 이미지 (왼쪽 컬럼에만, 있을 때)
        if col_idx == 0 and img_info:
            _insert_image(slide, img_info,
                          col_left + Inches(0.1), col_top + Inches(0.15),
                          col_w - Inches(0.2), Inches(1.8))
            text_top = col_top + Inches(2.0)
        else:
            text_top = col_top + Inches(0.2)

        # 텍스트
        tx = slide.shapes.add_textbox(
            col_left + Inches(0.18), text_top,
            col_w - Inches(0.36), col_h - (text_top - col_top) - Inches(0.2)
        )
        tf = tx.text_frame
        tf.word_wrap = True
        for i, item in enumerate(col_data):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.text = remove_emoji(str(item))
            run = p.runs[0]
            run.font.size = Pt(14)
            run.font.color.rgb = palette["body_text"]
            run.font.name = "Malgun Gothic"
            p.space_after = Pt(4)


def _render_data(slide, slide_info: dict, W, H, palette: dict, img_info: dict = None):
    """데이터/통계 슬라이드"""
    content = slide_info.get("content", {})
    title = slide_info.get("title", "")
    subtitle = slide_info.get("subtitle", "")
    main_points = content.get("main_points", [])
    highlight = remove_emoji(str(content.get("highlight", "") or ""))

    page_idx = slide_info.get("page", 1)
    _add_title_block(slide, title, subtitle, W, palette, page_idx=page_idx)

    # 큰 숫자 강조 (중앙)
    if highlight:
        tx_hi = slide.shapes.add_textbox(Inches(0.4), Inches(1.85), W * 45 // 100, Inches(1.2))
        tf_hi = tx_hi.text_frame
        p_hi = tf_hi.paragraphs[0]
        p_hi.text = highlight
        r = p_hi.runs[0]
        r.font.size = Pt(64)
        r.font.bold = True
        r.font.color.rgb = palette["accent"]
        r.font.name = "Malgun Gothic"

    # 이미지 (우측 상단)
    if img_info:
        img_left = W * 52 // 100
        _insert_image(slide, img_info, img_left, Inches(1.78), W - img_left - Inches(0.3), Inches(2.8))

    # 카드 그리드
    card_count = min(len(main_points), 4)
    if card_count > 0:
        card_top = Inches(3.3) if highlight else Inches(1.9)
        card_w = (W - Inches(0.8)) / card_count - Inches(0.1)
        card_h = H - card_top - Inches(0.7)

        for i, pt in enumerate(main_points[:card_count]):
            cl = Inches(0.4) + i * (card_w + Inches(0.1))
            card = slide.shapes.add_shape(1, cl, card_top, card_w, card_h)
            card.fill.solid()
            card.fill.fore_color.rgb = palette["card_bg"]
            card.line.color.rgb = palette["accent"]
            card.line.width = Pt(0.5)

            tx = slide.shapes.add_textbox(
                cl + Inches(0.12), card_top + Inches(0.15),
                card_w - Inches(0.24), card_h - Inches(0.3)
            )
            tf = tx.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.text = remove_emoji(str(pt))
            p.alignment = PP_ALIGN.CENTER
            run = p.runs[0]
            run.font.size = Pt(13)
            run.font.color.rgb = palette["body_text"]
            run.font.name = "Malgun Gothic"


def _render_closing(slide, slide_info: dict, W, H, palette: dict):
    """클로징 슬라이드"""
    _set_bg(slide, palette["primary"])

    title = remove_emoji(slide_info.get("title", ""))
    sub = remove_emoji(slide_info.get("subtitle", "") or slide_info.get("content", {}).get("sub_text", ""))

    # 강조선
    bar = slide.shapes.add_shape(1, Inches(2.5), Inches(2.8), Inches(2.0), Emu(50000))
    bar.fill.solid()
    bar.fill.fore_color.rgb = palette["highlight"]
    bar.line.fill.background()

    tx = slide.shapes.add_textbox(Inches(1.0), Inches(2.2), W - Inches(2.0), Inches(1.6))
    tf = tx.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = title
    p.alignment = PP_ALIGN.CENTER
    run = p.runs[0]
    run.font.size = Pt(38)
    run.font.bold = True
    run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    run.font.name = "Malgun Gothic"

    if sub:
        tx2 = slide.shapes.add_textbox(Inches(1.0), Inches(4.0), W - Inches(2.0), Inches(0.8))
        tf2 = tx2.text_frame
        tf2.word_wrap = True
        p2 = tf2.paragraphs[0]
        p2.text = sub
        p2.alignment = PP_ALIGN.CENTER
        run2 = p2.runs[0]
        run2.font.size = Pt(17)
        run2.font.color.rgb = RGBColor(0xCA, 0xDC, 0xFC)
        run2.font.name = "Malgun Gothic"
