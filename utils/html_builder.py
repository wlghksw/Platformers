"""
CrayonSchool HTML Slide Builder
JSON 슬라이드 구조 → crayonschool_design_assets.md 디자인 시스템 적용 완전 독립형 HTML 변환

출력: presentation_crayon.css + charts_crayon.js 인라인 포함 단일 HTML 파일
"""
import os
import re
from pathlib import Path


# ─── CSS / JS 자산 로드 경로 ──────────────────────────────────────────────────
_REPO_DIR = Path(__file__).parent.parent  # PPT_maker 폴더 (깃 저장소 루트)
_PARENT_DIR = Path(__file__).parent.parent.parent  # 사업 폴더 (로컬 상위 폴더)

# Railway 배포 환경(깃 루트 내부)과 로컬 개발 환경(상위 폴더) 모두 작동할 수 있도록 Fallback 설계
if (_REPO_DIR / "css" / "presentation_crayon.css").exists():
    _CSS_PATH = _REPO_DIR / "css" / "presentation_crayon.css"
else:
    _CSS_PATH = _PARENT_DIR / "css" / "presentation_crayon.css"

if (_REPO_DIR / "js" / "charts_crayon.js").exists():
    _JS_PATH = _REPO_DIR / "js" / "charts_crayon.js"
else:
    _JS_PATH = _PARENT_DIR / "js" / "charts_crayon.js"

# 구글 폰트 임베드
_GOOGLE_FONTS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&family=Outfit:wght@400;700&display=swap" rel="stylesheet">'
)

# 연령 그룹별 카드 색상 매핑
_AGE_CARD_COLORS = {
    "preschool":   ["card-feature-rose",   "card-feature-yellow"],
    "lower_elem":  ["card-feature-teal",   "card-feature-mint"],
    "upper_elem":  ["card-feature-coral",  "card-feature-teal"],
    "all":         ["card-feature-teal",   "card-feature-yellow", "card-feature-coral"],
    None:          ["card-feature-teal",   "card-feature-yellow", "card-feature-coral"],
}

# card-feature-mint 는 CSS에 없을 수 있으므로 인라인 스타일로 보완
_CARD_INLINE_STYLES = {
    "card-feature-mint": "background-color:#EAF7F0;",
    "card-feature-sky":  "background-color:#EBF5FA;",
}


def _load_asset(path: Path) -> str:
    """파일 읽기. 없으면 빈 문자열 반환"""
    if path.exists():
        return path.read_text(encoding="utf-8")
    print(f"[!] 자산 파일을 찾을 수 없습니다: {path}")
    return ""


def _badge_class(tag: str) -> str:
    """태그 텍스트에 따라 적절한 뱃지 클래스 결정"""
    tag_lower = tag.lower()
    if any(k in tag_lower for k in ("유치", "preschool", "pre")):
        return "badge-tag-yellow"
    if any(k in tag_lower for k in ("초등", "elem", "low", "high")):
        return "badge-tag-blue"
    if any(k in tag_lower for k in ("cover", "표지", "closing", "cta", "join")):
        return "badge-tag-blue"
    return "badge-tag-yellow"


def _escape(text: str) -> str:
    """HTML 특수문자 이스케이프"""
    if not text:
        return ""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


# ─── Slide Layout Renderers ───────────────────────────────────────────────────

# ─── Accent & Escape Helper Functions ─────────────────────────────────────────

def _escape(text: str) -> str:
    """HTML 특수문자 이스케이프"""
    if not text:
        return ""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def _apply_accent(text: str) -> str:
    """텍스트에서 따옴표, 백틱, 대괄호 등으로 묶인 부분을 <span class='accent'>...</span>로 변환"""
    if not text:
        return ""
    # 1. HTML 특수문자 안전 이스케이프
    escaped = _escape(text)
    # 2. 강조 구문 자동 정규식 감지하여 그라디언트 Accent 스팬으로 치환
    escaped = re.sub(r'&quot;([^&]+?)&quot;', r'<span class="accent">\1</span>', escaped)
    escaped = re.sub(r'&#39;([^&#]+?)&#39;', r'<span class="accent">\1</span>', escaped)
    escaped = re.sub(r'\[([^\]]+?)\]', r'<span class="accent">\1</span>', escaped)
    escaped = re.sub(r'\*\*([^*]+?)\*\*', r'<span class="accent">\1</span>', escaped)
    return escaped


# 공통 브랜드 마크 템플릿
_BRAND_MARK = """
<div class="brand-mark">
  <div class="brand-mark-dot">C</div>
  <div class="brand-mark-text">CrayonSchool</div>
</div>
"""


# ─── Slide Layout Renderers ───────────────────────────────────────────────────

def _render_title(slide: dict) -> str:
    """표지 슬라이드 (이미지 매칭 시 분할 레이아웃 자동 적용)"""
    title   = _apply_accent(slide.get("title", ""))
    subtitle = _escape(slide.get("subtitle", ""))
    tag     = _escape(slide.get("tag", "INTRO"))
    img_url  = slide.get("matched_image_url", "")

    if img_url:
        return f"""
<div class="slide" style="background:linear-gradient(160deg, #FFFFFF 0%, #FAF8ED 60%, #FFFBE8 100%);">
  <div class="grid-deco"></div>
  <div style="position:absolute;top:0;left:0;width:8px;height:100%;background:var(--primary);border-radius:0;z-index:1;"></div>
  <div class="slide-content-flex" style="height:100%; align-items:center; padding-left:32px; width:100%; z-index:1;">
    <div style="flex:1.2; max-width:680px; padding-right:24px;">
      <span class="badge badge-tag-yellow" style="margin-bottom:24px;display:inline-block;font-size:14px;">{tag}</span>
      <div class="hero-display" style="margin-bottom:20px;line-height:1.2; font-size:48px;">{title}</div>
      <div class="body-md" style="color:var(--text-secondary);">{subtitle}</div>
    </div>
    <div class="slide-image-wrapper" style="flex:0.8; display:flex; align-items:center; justify-content:center;">
      <img src="{img_url}" alt="hero image" style="max-width:100%; max-height:480px; object-fit:contain; border-radius:var(--radius-xl); box-shadow:0 16px 40px rgba(33,94,128,0.12); border:1px solid rgba(33,94,128,0.08);" />
    </div>
  </div>
</div>
"""
    else:
        return f"""
<div class="slide" style="justify-content:center; align-items:flex-start; background:linear-gradient(160deg, #FFFFFF 0%, #FAF8ED 60%, #FFFBE8 100%);">
  <div class="grid-deco"></div>
  <div style="position:absolute;top:0;left:0;width:8px;height:100%;background:var(--primary);border-radius:0;z-index:1;"></div>
  <div style="padding-left:32px;max-width:800px;z-index:1;">
    <span class="badge badge-tag-yellow" style="margin-bottom:32px;display:inline-block;font-size:14px;">{tag}</span>
    <div class="hero-display" style="margin-bottom:24px;line-height:1.15;font-size:52px;">{title}</div>
    <div class="body-md" style="color:var(--text-secondary);max-width:640px;font-size:20px;">{subtitle}</div>
  </div>
  <div style="position:absolute;bottom:40px;right:60px;display:flex;align-items:center;gap:8px;z-index:1;">
    <div style="width:32px;height:4px;background:var(--primary);border-radius:2px;"></div>
    <div style="width:16px;height:4px;background:var(--accent);border-radius:2px;opacity:0.5;"></div>
  </div>
</div>
"""


def _render_full_text(slide: dict) -> str:
    """텍스트 전용 슬라이드 (이미지 매칭 시 분할 레이아웃 자동 적용)"""
    tag     = _escape(slide.get("tag", ""))
    title   = _apply_accent(slide.get("title", ""))
    subtitle = _escape(slide.get("subtitle", ""))
    content = slide.get("content", {})
    points  = content.get("main_points", [])
    sub_text = _escape(content.get("sub_text", ""))
    page    = slide.get("page", "")
    badge_cls = _badge_class(slide.get("tag", ""))
    img_url  = slide.get("matched_image_url", "")

    points_html = ""
    for pt in points:
        points_html += f"""
<div style="display:flex;align-items:flex-start;gap:12px;margin-bottom:16px;">
  <div style="width:6px;height:6px;border-radius:50%;background:var(--primary);margin-top:9px;flex-shrink:0;"></div>
  <div class="body-md">{_escape(str(pt))}</div>
</div>"""

    body_html = f"""
    <div style="display:flex;flex-direction:column;gap:4px;">
      {points_html}
    </div>
    {"<div class='body-sm' style='margin-top:24px;padding-top:16px;border-top:1px dashed rgba(0,0,0,0.06);color:var(--text-muted);font-style:italic;'>" + sub_text + "</div>" if sub_text else ""}
    """

    if img_url:
        return f"""
<div class="slide">
  {_BRAND_MARK}
  <div style="margin-bottom:8px;margin-top:12px;">
    <span class="badge {badge_cls}">{tag}</span>
  </div>
  <div class="heading-1" style="margin-bottom:12px;">{title}</div>
  <div class="body-sm" style="color:var(--text-secondary);margin-bottom:20px;">{subtitle}</div>
  <div class="slide-content-flex" style="flex:1; align-items:stretch;">
    <div class="content-body" style="flex:1.2; padding-right:16px;">
      {body_html}
    </div>
    <div class="slide-image-wrapper" style="flex:0.8; display:flex; align-items:center; justify-content:center;">
      <img src="{img_url}" alt="slide image" style="max-width:100%; max-height:380px; object-fit:contain; border-radius:var(--radius-lg); box-shadow:0 12px 32px rgba(33,94,128,0.08); border:1px solid rgba(33,94,128,0.08);" onerror="this.parentElement.style.display='none'; this.closest('.slide-content-flex').querySelector('.content-body').style.flex='1';" />
    </div>
  </div>
  <div class="page-number">{page}</div>
</div>
"""
    else:
        return f"""
<div class="slide">
  {_BRAND_MARK}
  <div style="margin-bottom:8px;margin-top:12px;">
    <span class="badge {badge_cls}">{tag}</span>
  </div>
  <div class="heading-1" style="margin-bottom:12px;">{title}</div>
  <div class="body-sm" style="color:var(--text-secondary);margin-bottom:28px;">{subtitle}</div>
  <div style="flex:1;">
    {body_html}
  </div>
  <div class="page-number">{page}</div>
</div>
"""


def _render_card_grid(slide: dict) -> str:
    """파스텔 카드 그리드 슬라이드 (이미지 매칭 시 분할 레이아웃 자동 적용)"""
    tag      = _escape(slide.get("tag", ""))
    title    = _apply_accent(slide.get("title", ""))
    subtitle = _escape(slide.get("subtitle", ""))
    age_grp  = slide.get("age_group")
    content  = slide.get("content", {})
    cards    = content.get("cards", [])
    page     = slide.get("page", "")
    badge_cls = _badge_class(slide.get("tag", ""))
    img_url  = slide.get("matched_image_url", "")

    # 카드 색상 팔레트 선택
    palette = _AGE_CARD_COLORS.get(age_grp, _AGE_CARD_COLORS[None])

    # cards가 없으면 main_points를 카드로 변환
    if not cards:
        cards = [{"title": str(pt), "body": ""} for pt in content.get("main_points", [])]

    cards_html = ""
    for idx, card in enumerate(cards[:3]):  # 최대 3열
        color_cls = card.get("color_class") or palette[idx % len(palette)]
        inline    = _CARD_INLINE_STYLES.get(color_cls, "")
        c_title   = _escape(str(card.get("title", "")))
        c_body    = _escape(str(card.get("body", card.get("description", ""))))
        c_badge   = _escape(str(card.get("badge", card.get("tag", ""))))
        c_meta    = _escape(str(card.get("meta", "")))

        cards_html += f"""
<div class="card-feature {color_cls}" style="flex:1;min-width:0;display:flex;flex-direction:column;justify-content:space-between;{inline}">
  <div>
    {"<span class='badge badge-tag-blue' style='margin-bottom:12px;display:inline-block;font-size:11px;'>" + c_badge + "</span>" if c_badge else ""}
    <div class="heading-2" style="margin-bottom:12px;font-size:20px;font-weight:700;">{c_title}</div>
    <div class="body-sm" style="font-size:14px;line-height:1.55;color:var(--text-secondary);">{c_body}</div>
  </div>
  {"<div style='margin-top:16px;font-size:13px;color:var(--secondary);font-weight:700;border-top:1px dashed rgba(33,94,128,0.1);padding-top:8px;'>" + c_meta + "</div>" if c_meta else ""}
</div>"""

    if img_url:
        return f"""
<div class="slide">
  {_BRAND_MARK}
  <div style="margin-bottom:8px;margin-top:12px;">
    <span class="badge {badge_cls}">{tag}</span>
  </div>
  <div class="heading-1" style="margin-bottom:8px;">{title}</div>
  <div class="body-sm" style="color:var(--text-secondary);margin-bottom:20px;">{subtitle}</div>
  <div class="slide-content-flex" style="flex:1; align-items:stretch;">
    <div style="flex:1.2; display:flex; gap:16px; align-items:stretch;">
      {cards_html}
    </div>
    <div class="slide-image-wrapper" style="flex:0.8; display:flex; align-items:center; justify-content:center;">
      <img src="{img_url}" alt="slide image" style="max-width:100%; max-height:380px; object-fit:contain; border-radius:var(--radius-lg); box-shadow:0 12px 32px rgba(33,94,128,0.08); border:1px solid rgba(33,94,128,0.08);" onerror="this.parentElement.style.display='none'; this.closest('.slide-content-flex').querySelector('.content-body').style.flex='1';" />
    </div>
  </div>
  <div class="page-number">{page}</div>
</div>
"""
    else:
        return f"""
<div class="slide">
  {_BRAND_MARK}
  <div style="margin-bottom:8px;margin-top:12px;">
    <span class="badge {badge_cls}">{tag}</span>
  </div>
  <div class="heading-1" style="margin-bottom:8px;">{title}</div>
  <div class="body-sm" style="color:var(--text-secondary);margin-bottom:28px;">{subtitle}</div>
  <div style="display:flex;gap:20px;flex:1;align-items:stretch;">
    {cards_html}
  </div>
  <div class="page-number">{page}</div>
</div>
"""


def _render_split_v(slide: dict, image_list: list = None) -> str:
    """좌텍스트 + 우이미지 분할 슬라이드"""
    tag      = _escape(slide.get("tag", ""))
    title    = _apply_accent(slide.get("title", ""))
    subtitle = _escape(slide.get("subtitle", ""))
    content  = slide.get("content", {})
    points   = content.get("main_points", [])
    page     = slide.get("page", "")
    badge_cls = _badge_class(slide.get("tag", ""))
    img_url  = slide.get("matched_image_url", "")

    points_html = ""
    for pt in points:
        points_html += f"""
<div style="display:flex;gap:12px;margin-bottom:14px;align-items:flex-start;">
  <div style="width:6px;height:6px;border-radius:50%;background:var(--primary);margin-top:9px;flex-shrink:0;"></div>
  <div class="body-md">{_escape(str(pt))}</div>
</div>"""

    img_block = ""
    if img_url:
        img_block = f'<img src="{img_url}" alt="slide image" onerror="this.parentElement.style.display=\'none\'; this.closest(\'.slide-content-flex\').querySelector(\'.content-body\').style.flex=\'1\';" />'
    else:
        highlight = _escape(str(content.get("highlight_data", "")))
        img_block = f"""
<div style="width:100%;height:100%;background:linear-gradient(135deg,#FFFBE8,#E8F6F8);
  border-radius:var(--radius-lg);display:flex;align-items:center;justify-content:center;
  flex-direction:column;gap:16px;border:1px solid rgba(33,94,128,0.06);box-shadow:0 8px 24px rgba(0,0,0,0.01);">
  <div style="font-size:52px;font-weight:800;color:var(--secondary);">{highlight}</div>
</div>"""

    return f"""
<div class="slide">
  {_BRAND_MARK}
  <div style="margin-bottom:8px;margin-top:12px;">
    <span class="badge {badge_cls}">{tag}</span>
  </div>
  <div class="heading-1" style="margin-bottom:8px;">{title}</div>
  <div class="slide-content-flex" style="margin-top:8px;">
    <div class="content-body" style="flex:1.2; padding-right:16px;">
      <div class="body-sm" style="color:var(--text-secondary);margin-bottom:20px;font-size:16px;">{subtitle}</div>
      {points_html}
    </div>
    <div class="slide-image-wrapper" style="flex:0.8;">
      {img_block}
    </div>
  </div>
  <div class="page-number">{page}</div>
</div>
"""


def _render_data_focus(slide: dict) -> str:
    """KPI 수치 강조 슬라이드"""
    tag      = _escape(slide.get("tag", ""))
    title    = _apply_accent(slide.get("title", ""))
    subtitle = _escape(slide.get("subtitle", ""))
    content  = slide.get("content", {})
    points   = content.get("main_points", [])
    highlight = _escape(str(content.get("highlight_data", "")))
    page     = slide.get("page", "")
    badge_cls = _badge_class(slide.get("tag", ""))
    cards    = content.get("cards", [])

    body_html = ""
    if cards:
        card_items = ""
        for c in cards[:3]:
            num   = _escape(str(c.get("number", c.get("highlight_data", c.get("title", "")))))
            label = _escape(str(c.get("label", c.get("body", ""))))
            card_items += f"""
<div class="card-base" style="flex:1;text-align:center;padding:28px 16px;border-radius:var(--radius-md);">
  <div style="font-size:40px;font-weight:800;color:var(--secondary);margin-bottom:8px;font-family:\'Outfit\',sans-serif;">{num}</div>
  <div class="body-sm" style="font-weight:500;color:var(--text-secondary);">{label}</div>
</div>"""
        body_html = f'<div style="display:flex;gap:20px;margin-top:24px;">{card_items}</div>'
    else:
        for pt in points:
            body_html += f"""
<div style="display:flex;gap:12px;margin-bottom:14px;align-items:flex-start;">
  <div style="width:6px;height:6px;border-radius:50%;background:var(--primary);margin-top:9px;flex-shrink:0;"></div>
  <div class="body-md">{_escape(str(pt))}</div>
</div>"""

    return f"""
<div class="slide">
  {_BRAND_MARK}
  <div style="margin-bottom:8px;margin-top:12px;">
    <span class="badge {badge_cls}">{tag}</span>
  </div>
  <div class="heading-1" style="margin-bottom:8px;">{title}</div>
  <div class="slide-content-flex" style="flex:1;flex-direction:column;justify-content:center;">
    <div style="display:flex;align-items:baseline;gap:16px;margin:8px 0 16px;">
      {"<div class='kpi-mega primary'>" + highlight + "</div>" if highlight else ""}
      <div class="body-sm" style="color:var(--text-secondary);font-size:16px;font-weight:500;">{subtitle}</div>
    </div>
    <div style="flex:1;">
      {body_html}
    </div>
  </div>
  <div class="page-number">{page}</div>
</div>
"""


def _render_comparison(slide: dict) -> str:
    """비교 테이블 슬라이드"""
    tag      = _escape(slide.get("tag", ""))
    title    = _apply_accent(slide.get("title", ""))
    subtitle = _escape(slide.get("subtitle", ""))
    content  = slide.get("content", {})
    headers  = content.get("table_headers", [])
    rows     = content.get("table_rows", [])
    page     = slide.get("page", "")
    badge_cls = _badge_class(slide.get("tag", ""))

    if not headers and not rows:
        return _render_full_text(slide)

    th_html = "".join(f"<th>{_escape(str(h))}</th>" for h in headers)
    rows_html = ""
    for row in rows:
        cells = row if isinstance(row, list) else [row]
        td_html = "".join(f"<td>{_escape(str(c))}</td>" for c in cells)
        rows_html += f"<tr>{td_html}</tr>"

    return f"""
<div class="slide">
  {_BRAND_MARK}
  <div style="margin-bottom:8px;margin-top:12px;">
    <span class="badge {badge_cls}">{tag}</span>
  </div>
  <div class="heading-1" style="margin-bottom:8px;">{title}</div>
  <div class="body-sm" style="color:var(--text-secondary);margin-bottom:20px;">{subtitle}</div>
  <div style="flex:1;overflow:hidden;margin-top:8px;">
    <table class="comparison-table">
      <thead><tr>{th_html}</tr></thead>
      <tbody>{rows_html}</tbody>
    </table>
  </div>
  <div class="page-number">{page}</div>
</div>
"""


def _render_closing(slide: dict) -> str:
    """마무리 슬라이드"""
    title   = _apply_accent(slide.get("title", "크레용스쿨과 함께하세요"))
    subtitle = _escape(slide.get("subtitle", "아이들의 창의적 성장을 돕는 가장 현명한 파트너십"))
    content = slide.get("content", {})
    sub_text = _escape(content.get("sub_text", ""))
    page    = slide.get("page", "")

    return f"""
<div class="slide" style="justify-content:center;align-items:center;text-align:center;
  background:linear-gradient(160deg, #FFFFFF 0%, #FAF8ED 60%, #FFFBE8 100%);">
  <div class="grid-deco"></div>
  <div style="position:absolute;top:0;left:0;width:100%;height:6px;background:var(--primary);z-index:1;"></div>
  <span class="badge badge-tag-blue" style="margin-bottom:24px;display:inline-block;z-index:1;font-size:13px;letter-spacing:1px;">JOIN CRAYON SCHOOL</span>
  <div class="hero-display" style="margin-bottom:16px;font-size:46px;z-index:1;">{title}</div>
  <div class="body-md" style="color:var(--text-secondary);margin-bottom:32px;max-width:640px;z-index:1;font-size:19px;">{subtitle}</div>
  {"<div class='body-sm' style='color:var(--secondary);font-weight:700;z-index:1;font-size:15px;'>" + sub_text + "</div>" if sub_text else ""}
  <div class="page-number" style="z-index:1;">{page}</div>
</div>
"""


# ─── B2B Proposal Specific Renderers ──────────────────────────────────────────

def _render_catalog_grid(slide: dict) -> str:
    """전체 프로그램 요약 표 (카탈로그 그리드)"""
    tag      = _escape(slide.get("tag", ""))
    title    = _apply_accent(slide.get("title", ""))
    subtitle = _escape(slide.get("subtitle", ""))
    content  = slide.get("content", {})
    rows     = content.get("catalog_rows", [])
    page     = slide.get("page", "")
    badge_cls = _badge_class(slide.get("tag", ""))

    rows_html = ""
    for r in rows:
        code = _escape(r.get("code", ""))
        name = _escape(r.get("name", ""))
        features = _escape(r.get("features", ""))
        kit = _escape(r.get("kit", ""))
        output = _escape(r.get("output", ""))
        rows_html += f"""
        <div style="display:contents;">
          <div class="catalog-cell" style="justify-content:center;"><span class="catalog-code">{code}</span></div>
          <div class="catalog-cell" style="font-weight:700; color:var(--secondary);">{name}</div>
          <div class="catalog-cell">{features}</div>
          <div class="catalog-cell">{kit}</div>
          <div class="catalog-cell">{output}</div>
        </div>
        """

    return f"""
<div class="slide">
  {_BRAND_MARK}
  <div style="margin-bottom:8px;margin-top:12px;">
    <span class="badge {badge_cls}">{tag}</span>
  </div>
  <div class="heading-1" style="margin-bottom:8px;">{title}</div>
  <div class="body-sm" style="color:var(--text-secondary);margin-bottom:20px;">{subtitle}</div>
  
  <div class="catalog-grid" style="flex:1; margin-top:8px;">
    <div style="display:contents;">
      <div class="catalog-header">코드</div>
      <div class="catalog-header">프로그램명 (대상)</div>
      <div class="catalog-header">교육 특징 및 내용</div>
      <div class="catalog-header">6차시 구성 교구</div>
      <div class="catalog-header">최종 결과물</div>
    </div>
    {rows_html}
  </div>
  
  <div class="page-number">{page}</div>
</div>
"""

def _render_curriculum_table(slide: dict) -> str:
    """6차시 커리큘럼 테이블 + 좌측 사이드바(장비) 레이아웃"""
    tag      = _escape(slide.get("tag", ""))
    title    = _apply_accent(slide.get("title", ""))
    subtitle = _escape(slide.get("subtitle", ""))
    content  = slide.get("content", {})
    equipment = _escape(content.get("equipment", "미디어 시설 및 교구재"))
    curriculum = content.get("curriculum", [])
    page     = slide.get("page", "")
    badge_cls = _badge_class(slide.get("tag", ""))

    rows_html = ""
    for idx, c in enumerate(curriculum):
        chasi = _escape(str(c.get("period", idx+1)))
        topic = _escape(c.get("topic", ""))
        method = _escape(c.get("method", "이론·실습"))
        kit = _escape(c.get("kit", ""))
        detail = _escape(c.get("detail", ""))
        
        rows_html += f"""
        <tr>
          <td>{chasi}</td>
          <td style="font-weight:700; color:var(--secondary);">{topic}</td>
          <td><span class="chip-tag" style="margin:0;">{method}</span></td>
          <td>{kit}</td>
          <td>{detail}</td>
        </tr>
        """

    return f"""
<div class="slide">
  {_BRAND_MARK}
  <div style="margin-bottom:8px;margin-top:12px;">
    <span class="badge {badge_cls}">{tag}</span>
  </div>
  <div class="heading-1" style="margin-bottom:8px;">{title}</div>
  <div class="body-sm" style="color:var(--text-secondary);margin-bottom:20px;">{subtitle}</div>
  
  <div class="slide-content-flex" style="flex:1; gap:24px; margin-top:8px;">
    <!-- Left Sidebar -->
    <div style="flex:0.28; min-width:240px; display:flex; flex-direction:column;">
      <div class="sidebar-box" style="flex:1;">
        <div class="sidebar-title">
          <div style="width:6px;height:18px;background:var(--primary);border-radius:2px;"></div>
          필요 인력 및 장비
        </div>
        <div class="body-sm" style="color:var(--text-secondary); line-height:1.65; font-size:14px;">
          {equipment}
        </div>
      </div>
    </div>
    
    <!-- Right Table -->
    <div style="flex:0.72; overflow:hidden;">
      <table class="curriculum-table">
        <thead>
          <tr>
            <th style="width:60px; text-align:center;">차시</th>
            <th style="width:22%;">주제</th>
            <th style="width:16%; text-align:center;">교육방법</th>
            <th style="width:25%;">활용교구</th>
            <th style="width:auto;">활동 내용</th>
          </tr>
        </thead>
        <tbody>
          {rows_html}
        </tbody>
      </table>
    </div>
  </div>
  
  <div class="page-number">{page}</div>
</div>
"""

def _render_supply_pricing(slide: dict) -> str:
    """B2B 공급 조건 및 견적 대형 카드 슬라이드"""
    tag      = _escape(slide.get("tag", ""))
    title    = _apply_accent(slide.get("title", ""))
    subtitle = _escape(slide.get("subtitle", ""))
    content  = slide.get("content", {})
    cards    = content.get("pricing_cards", [])
    condition = _escape(content.get("condition", "최소 1학급 25명 공급 기준"))
    page     = slide.get("page", "")
    badge_cls = _badge_class(slide.get("tag", ""))

    cards_html = ""
    for c in cards[:3]:
        c_title = _escape(c.get("title", ""))
        amount = _escape(c.get("amount", ""))
        desc = _escape(c.get("desc", ""))
        cards_html += f"""
        <div class="pricing-card">
          <div style="font-size:15px; font-weight:700; color:var(--text-secondary);">{c_title}</div>
          <div class="price-amount">{amount}</div>
          <div class="price-desc">{desc}</div>
        </div>
        """

    return f"""
<div class="slide">
  {_BRAND_MARK}
  <div style="margin-bottom:8px;margin-top:12px;">
    <span class="badge {badge_cls}">{tag}</span>
  </div>
  <div class="heading-1" style="margin-bottom:8px;">{title}</div>
  <div class="body-sm" style="color:var(--text-secondary);margin-bottom:28px;">{subtitle}</div>
  
  <div style="display:flex; gap:24px; flex:1; align-items:stretch;">
    {cards_html}
  </div>
  
  <div style="margin-top:24px; text-align:center; padding:16px; background-color:var(--primary-light); border-radius:var(--radius-full); font-weight:700; color:var(--secondary); font-size:15px; border: 1px dashed rgba(255, 192, 0, 0.4); box-shadow:0 4px 12px rgba(255, 192, 0, 0.03);">
    ■ 단가 책정 원칙: {condition}
  </div>
  
  <div class="page-number">{page}</div>
</div>
"""


# ─── Layout Dispatch ─────────────────────────────────────────────────────────

def _render_slide(slide: dict, image_list: list = None) -> str:
    """layout_type에 따라 적절한 렌더러 선택"""
    layout = slide.get("layout_type", slide.get("layout", "full_text"))

    dispatch = {
        "title":            _render_title,
        "closing":          _render_closing,
        "card_grid":        _render_card_grid,
        "data_focus":       _render_data_focus,
        "comparison":       _render_comparison,
        "split_v":          lambda s: _render_split_v(s, image_list),
        "split_h":          lambda s: _render_split_v(s, image_list),
        "full_text":        _render_full_text,
        # B2B 신규 레이아웃
        "catalog_grid":     _render_catalog_grid,
        "curriculum_table": _render_curriculum_table,
        "supply_pricing":   _render_supply_pricing,
        # 구버전 호환
        "content":          _render_full_text,
        "two_column":       _render_card_grid,
        "data":             _render_data_focus,
        "chapter":          _render_title,
    }

    renderer = dispatch.get(layout, _render_full_text)
    return renderer(slide)


# ─── Main Builder ─────────────────────────────────────────────────────────────

# 줌 컨트롤 HTML 패널 및 스크립트 자산 정의
_ZOOM_CONTROLS_ASSET = ""

def build_html(
    slides_data: dict,
    images: list = None,
    category: str = "proposal"
) -> str:
    """
    슬라이드 JSON → 완전 독립형 HTML 문자열 변환

    Args:
        slides_data: generate_slides() 반환값
        images: 이미지 라이브러리 (matched_image_url 포함)
        category: "proposal" | "at_curriculum"

    Returns:
        독립 실행 가능한 완성형 HTML 문자열
    """
    css_content = _load_asset(_CSS_PATH)
    js_content  = _load_asset(_JS_PATH)

    title = _escape(slides_data.get("presentation_title", "CrayonSchool 교육 제안서"))
    slides = slides_data.get("slides", [])

    # 첫 슬라이드 강제 표지 처리
    if slides and slides[0].get("layout_type") not in ("title",):
        slides[0]["layout_type"] = "title"

    # 슬라이드 HTML 생성
    slides_html = ""
    for slide in slides:
        slides_html += _render_slide(slide, image_list=images)

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  {_GOOGLE_FONTS}
  <style>
{css_content}

/* ── Presentation Wrapper (browser preview mode) ── */
.presentation-wrapper {{
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 32px;
  padding: 40px 20px;
  min-height: 100vh;
  background: #2b2b2b;
}}
  </style>
</head>
<body>
  <div class="presentation-wrapper">
    {slides_html}
  </div>
  
  {_ZOOM_CONTROLS_ASSET}
  
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
  <script>
{js_content}
  </script>
</body>
</html>
"""
    return html


def save_html(html_str: str, output_path: str) -> None:
    """HTML 파일 저장"""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_str)
    print(f"[*] HTML 저장 완료: {output_path}")
