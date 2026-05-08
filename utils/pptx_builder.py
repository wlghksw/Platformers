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
        bg = RGBColor(0xFF, 0xFF, 0xFF)
        body_text = RGBColor(0x33, 0x33, 0x33)

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
def build_presentation(
    slides_data: dict,
    template_path: str = None,
    output_path: str = None,
    images: list = None,           # extract_images_from_pdf 결과
    template_info: dict = None,    # get_template_info 결과
) -> str:
    palette = build_palette(template_info)
    prs = Presentation()
    prs.slide_width = Inches(13.33)   # 16:9
    prs.slide_height = Inches(7.5)

    W = prs.slide_width
    H = prs.slide_height
    blank = prs.slide_layouts[6]  # Blank

    slide_list = slides_data.get("slides", [])
    total = len(slide_list)

    # 슬라이드당 사용할 이미지 풀 (대표 이미지 우선)
    img_pool = list(images) if images else []
    img_idx = 0  # 순환 인덱스

    for slide_info in slide_list:
        slide = prs.slides.add_slide(blank)
        layout = slide_info.get("layout", "content")

        # 배경
        _set_bg(slide, palette["bg"])

        # 레이아웃별 렌더
        use_image = layout in ("content", "two_column", "data") and img_pool
        current_img = None
        if use_image:
            current_img = img_pool[img_idx % len(img_pool)]
            img_idx += 1

        if layout == "title":
            _render_title(slide, slide_info, W, H, palette)
        elif layout == "two_column":
            _render_two_column(slide, slide_info, W, H, palette, current_img)
        elif layout == "data":
            _render_data(slide, slide_info, W, H, palette, current_img)
        elif layout == "closing":
            _render_closing(slide, slide_info, W, H, palette)
        else:
            _render_content(slide, slide_info, W, H, palette, current_img)

        # Tag + Page number (모든 슬라이드)
        _add_tag(slide, remove_emoji(slide_info.get("tag", "")), W, H, palette)
        _add_page_number(slide, slide_info.get("page", 1), total, W, H, palette)

        # 발표자 노트
        notes = slide_info.get("speaker_notes", "")
        if notes:
            slide.notes_slide.notes_text_frame.text = remove_emoji(notes)

    if not output_path:
        output_path = "/tmp/output_presentation.pptx"
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
    run.font.name = "Arial"
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
    run.font.name = "Arial"


def _add_title_block(slide, title: str, subtitle: str, W, palette: dict):
    """Title(y=0.65in) + Subtitle(y=1.35in) + 구분선 — 공통"""
    # 제목
    tx = slide.shapes.add_textbox(Inches(0.4), Inches(0.62), W - Inches(0.8), Inches(0.85))
    tf = tx.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = remove_emoji(title)
    run = p.runs[0]
    run.font.size = Pt(26)
    run.font.bold = True
    run.font.color.rgb = palette["title_text"]
    run.font.name = "Arial"

    # 부제목 y=1.35in
    if subtitle:
        tx2 = slide.shapes.add_textbox(Inches(0.4), Inches(1.32), W - Inches(0.8), Inches(0.35))
        tf2 = tx2.text_frame
        p2 = tf2.paragraphs[0]
        p2.text = remove_emoji(subtitle)
        run2 = p2.runs[0]
        run2.font.size = Pt(12)
        run2.font.color.rgb = palette["sub_title"]
        run2.font.name = "Arial"

    # 구분선 y≈1.55in
    line = slide.shapes.add_shape(1, Inches(0.4), Inches(1.55), W - Inches(0.8), Emu(28000))
    line.fill.solid()
    line.fill.fore_color.rgb = palette["divider"]
    line.line.fill.background()


# ─── 이미지 삽입 헬퍼 ───────────────────────
def _insert_image(slide, img_info: dict, left, top, width, height):
    """이미지를 지정 영역에 비율 유지하며 삽입"""
    try:
        pic = slide.shapes.add_picture(
            img_info["path"], left, top, width, height
        )
        # 비율 보정
        iw, ih = img_info["width"], img_info["height"]
        scale = min(width / iw, height / ih)
        new_w = int(iw * scale)
        new_h = int(ih * scale)
        pic.width = new_w
        pic.height = new_h
        # 중앙 정렬
        pic.left = left + (width - new_w) // 2
        pic.top = top + (height - new_h) // 2
        return True
    except Exception:
        return False


# ─── 레이아웃별 렌더 ────────────────────────
def _render_title(slide, slide_info: dict, W, H, palette: dict):
    """표지 슬라이드"""
    title = remove_emoji(slide_info.get("title", ""))
    sub = remove_emoji(slide_info.get("subtitle", "") or slide_info.get("content", {}).get("sub_text", ""))

    # 상단 절반 컬러 블록
    shape = slide.shapes.add_shape(1, 0, 0, W, H * 55 // 100)
    shape.fill.solid()
    shape.fill.fore_color.rgb = palette["primary"]
    shape.line.fill.background()

    # 제목 (흰색)
    tx = slide.shapes.add_textbox(Inches(0.8), Inches(1.3), W - Inches(1.6), Inches(1.8))
    tf = tx.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = title
    run = p.runs[0]
    run.font.size = Pt(38)
    run.font.bold = True
    run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    run.font.name = "Arial"

    # 강조선
    bar = slide.shapes.add_shape(1, Inches(0.8), Inches(3.2), Inches(1.5), Emu(40000))
    bar.fill.solid()
    bar.fill.fore_color.rgb = palette["highlight"]
    bar.line.fill.background()

    # 부제목 (하단)
    if sub:
        tx2 = slide.shapes.add_textbox(Inches(0.8), Inches(4.5), W - Inches(1.6), Inches(1.0))
        tf2 = tx2.text_frame
        tf2.word_wrap = True
        p2 = tf2.paragraphs[0]
        p2.text = sub
        run2 = p2.runs[0]
        run2.font.size = Pt(16)
        run2.font.color.rgb = palette["body_text"]
        run2.font.name = "Arial"


def _render_content(slide, slide_info: dict, W, H, palette: dict, img_info: dict = None):
    """일반 콘텐츠 슬라이드 — 이미지 있으면 우측 배치"""
    content = slide_info.get("content", {})
    title = slide_info.get("title", "")
    subtitle = slide_info.get("subtitle", "")
    main_points = content.get("main_points", [])
    sub_text = content.get("sub_text", "")
    highlight = str(content.get("highlight", "") or "")

    _add_title_block(slide, title, subtitle, W, palette)

    content_top = Inches(1.78)
    content_h = H - content_top - Inches(0.65)

    if img_info:
        # 텍스트 영역: 왼쪽 55%
        text_w = W * 54 // 100
        img_left = text_w + Inches(0.15)
        img_w = W - img_left - Inches(0.3)

        # 하이라이트
        body_top = content_top
        if highlight:
            tx_hi = slide.shapes.add_textbox(Inches(0.4), body_top, text_w - Inches(0.4), Inches(0.75))
            tf_hi = tx_hi.text_frame
            p_hi = tf_hi.paragraphs[0]
            p_hi.text = remove_emoji(highlight)
            r = p_hi.runs[0]
            r.font.size = Pt(36)
            r.font.bold = True
            r.font.color.rgb = palette["accent"]
            r.font.name = "Arial"
            body_top += Inches(0.85)

        # 불릿
        if main_points:
            tx_b = slide.shapes.add_textbox(Inches(0.5), body_top, text_w - Inches(0.5), H - body_top - Inches(0.7))
            tf_b = tx_b.text_frame
            tf_b.word_wrap = True
            for i, pt in enumerate(main_points):
                p = tf_b.paragraphs[0] if i == 0 else tf_b.add_paragraph()
                p.text = f"  {remove_emoji(str(pt))}"
                run = p.runs[0]
                run.font.size = Pt(15)
                run.font.color.rgb = palette["body_text"]
                run.font.name = "Arial"
                p.space_after = Pt(4)

        # 이미지 (우측)
        _insert_image(slide, img_info, img_left, content_top, img_w, content_h)

    else:
        # 이미지 없음 — 전체 너비 텍스트
        body_top = content_top
        if highlight:
            tx_hi = slide.shapes.add_textbox(Inches(0.4), body_top, Inches(4), Inches(0.75))
            tf_hi = tx_hi.text_frame
            p_hi = tf_hi.paragraphs[0]
            p_hi.text = remove_emoji(highlight)
            r = p_hi.runs[0]
            r.font.size = Pt(40)
            r.font.bold = True
            r.font.color.rgb = palette["accent"]
            r.font.name = "Arial"
            body_top += Inches(0.9)

        if main_points:
            tx_b = slide.shapes.add_textbox(Inches(0.5), body_top, W - Inches(1.0), H - body_top - Inches(0.7))
            tf_b = tx_b.text_frame
            tf_b.word_wrap = True
            for i, pt in enumerate(main_points):
                p = tf_b.paragraphs[0] if i == 0 else tf_b.add_paragraph()
                p.text = f"  {remove_emoji(str(pt))}"
                run = p.runs[0]
                run.font.size = Pt(16)
                run.font.color.rgb = palette["body_text"]
                run.font.name = "Arial"
                p.space_after = Pt(5)

        if sub_text:
            tx_sub = slide.shapes.add_textbox(Inches(0.4), H - Inches(1.3), W - Inches(0.8), Inches(0.5))
            p_sub = tx_sub.text_frame.paragraphs[0]
            p_sub.text = remove_emoji(sub_text)
            r_sub = p_sub.runs[0]
            r_sub.font.size = Pt(11)
            r_sub.font.italic = True
            r_sub.font.color.rgb = palette["page_num"]
            r_sub.font.name = "Arial"


def _render_two_column(slide, slide_info: dict, W, H, palette: dict, img_info: dict = None):
    """두 컬럼 슬라이드"""
    content = slide_info.get("content", {})
    title = slide_info.get("title", "")
    subtitle = slide_info.get("subtitle", "")
    left_col = content.get("left_column", content.get("main_points", [])[:3])
    right_col = content.get("right_column", content.get("main_points", [])[3:])

    _add_title_block(slide, title, subtitle, W, palette)

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
            run.font.name = "Arial"
            p.space_after = Pt(4)


def _render_data(slide, slide_info: dict, W, H, palette: dict, img_info: dict = None):
    """데이터/통계 슬라이드"""
    content = slide_info.get("content", {})
    title = slide_info.get("title", "")
    subtitle = slide_info.get("subtitle", "")
    main_points = content.get("main_points", [])
    highlight = remove_emoji(str(content.get("highlight", "") or ""))

    _add_title_block(slide, title, subtitle, W, palette)

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
        r.font.name = "Arial"

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
            run.font.name = "Arial"


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
    run.font.name = "Arial"

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
        run2.font.name = "Arial"
