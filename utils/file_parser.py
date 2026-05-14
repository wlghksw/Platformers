"""
파일에서 텍스트와 이미지를 추출하는 유틸리티
지원 형식: PDF, DOCX, PPTX, TXT
"""
import os
import io
from pathlib import Path


def extract_text(filepath: str) -> str:
    """파일 형식에 따라 텍스트 추출"""
    ext = Path(filepath).suffix.lower()

    if ext == ".pdf":
        return _extract_pdf(filepath)
    elif ext == ".docx":
        return _extract_docx(filepath)
    elif ext in (".pptx", ".ppt"):
        return _extract_pptx(filepath)
    elif ext == ".txt":
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    elif ext in (".xlsx", ".xls"):
        return _extract_excel(filepath)
    else:
        raise ValueError(f"지원하지 않는 파일 형식: {ext}")


def extract_images_from_pdf(filepath: str, output_dir: str, min_width: int = 200, min_height: int = 150) -> list:
    """
    PDF에서 유효한 이미지를 추출하여 파일로 저장
    Returns: [{"path": str, "page": int, "width": int, "height": int}]
    """
    # pyrefly: ignore [missing-import]
    import fitz  # PyMuPDF

    os.makedirs(output_dir, exist_ok=True)
    results = []
    seen_xrefs = set()

    doc = fitz.open(filepath)
    for page_num in range(len(doc)):
        page = doc[page_num]
        for img in page.get_images(full=True):
            xref = img[0]
            if xref in seen_xrefs:
                continue
            seen_xrefs.add(xref)

            try:
                base = doc.extract_image(xref)
                w, h = base["width"], base["height"]
                if w < min_width or h < min_height:
                    continue

                ext = base["ext"]
                img_path = os.path.join(output_dir, f"img_p{page_num+1}_{xref}.{ext}")
                with open(img_path, "wb") as f:
                    f.write(base["image"])

                results.append({
                    "path": img_path,
                    "page": page_num + 1,
                    "width": w,
                    "height": h,
                    "ext": ext,
                })
            except Exception:
                continue

    # 크기 큰 순으로 정렬 (대표 이미지 우선)
    results.sort(key=lambda x: x["width"] * x["height"], reverse=True)
    return results


def _extract_pdf(filepath: str) -> str:
    # pyrefly: ignore [missing-import]
    import fitz

    doc = fitz.open(filepath)
    texts = []
    for page_num, page in enumerate(doc, 1):
        text = page.get_text()
        if text.strip():
            texts.append(f"[페이지 {page_num}]\n{text.strip()}")
    return "\n\n".join(texts)


def _extract_docx(filepath: str) -> str:
    from docx import Document

    doc = Document(filepath)
    paragraphs = []
    for para in doc.paragraphs:
        if para.text.strip():
            if para.style.name.startswith("Heading"):
                paragraphs.append(f"\n## {para.text.strip()}")
            else:
                paragraphs.append(para.text.strip())

    for table in doc.tables:
        for row in table.rows:
            row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
            if row_text:
                paragraphs.append(row_text)

    return "\n".join(paragraphs)


def _extract_pptx(filepath: str) -> str:
    from pptx import Presentation

    prs = Presentation(filepath)
    slides_text = []
    for slide_num, slide in enumerate(prs.slides, 1):
        texts = []
        for shape in slide.shapes:
            if hasattr(shape, "text") and shape.text.strip():
                texts.append(shape.text.strip())
        if texts:
            slides_text.append(f"[슬라이드 {slide_num}]\n" + "\n".join(texts))

    return "\n\n".join(slides_text)


def _extract_excel(filepath: str) -> str:
    """
    엑셀 파일에서 텍스트 추출
    모든 시트의 데이터를 행 기반 텍스트로 변환
    """
    import pandas as pd

    result_parts = []
    try:
        # .xls는 xlrd 엔진, .xlsx는 openpyxl 엔진 자동 선택
        ext = Path(filepath).suffix.lower()
        engine = "xlrd" if ext == ".xls" else "openpyxl"
        xl = pd.ExcelFile(filepath, engine=engine)
    except Exception as e:
        raise ValueError(f"엑셀 파일을 열 수 없습니다: {e}")

    for sheet_name in xl.sheet_names:
        try:
            df = xl.parse(sheet_name, header=None, dtype=str)
            # 완전히 빈 행 제거
            df.dropna(how="all", inplace=True)
            if df.empty:
                continue

            sheet_lines = [f"[시트: {sheet_name}]"]
            for _, row in df.iterrows():
                # 셀을 '|'로 구분하고 빈 값 제외
                cells = [str(c).strip() for c in row if str(c).strip() not in ("", "nan", "None")]
                if cells:
                    sheet_lines.append(" | ".join(cells))

            if len(sheet_lines) > 1:  # 헤더 외 데이터가 있을 때만 추가
                result_parts.append("\n".join(sheet_lines))
        except Exception:
            continue

    if not result_parts:
        raise ValueError("엑셀 파일에서 텍스트를 추출할 수 없습니다. 시트에 데이터가 있는지 확인해주세요.")

    return "\n\n".join(result_parts)


def get_template_info(filepath: str) -> dict:
    """
    템플릿 PDF에서 색상 팔레트, 폰트, 레이아웃 구조를 상세 추출
    """
    # pyrefly: ignore [missing-import]
    import fitz

    info = {
        "colors": [],           # 주요 색상 hex list
        "bg_color": "#FFFFFF",  # 배경색
        "accent_color": None,   # 강조색
        "fonts": [],            # 폰트 목록
        "has_dark_bg": False,
        "layout_hints": "",
        "page_count": 0,
        "has_header_bar": False,    # 상단 컬러 바 여부
        "has_sidebar": False,       # 사이드바 여부
        "image_layout": "right",    # 이미지 배치 패턴
    }

    try:
        doc = fitz.open(filepath)
        info["page_count"] = len(doc)

        color_counter = {}
        font_set = set()

        for page_num in range(min(5, len(doc))):
            page = doc[page_num]
            pw, ph = page.rect.width, page.rect.height

            # 텍스트/폰트 추출
            for block in page.get_text("dict").get("blocks", []):
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        font = span.get("font", "")
                        if font:
                            base = font.split("-")[0].split(",")[0].strip()
                            if base and "+" not in base:
                                font_set.add(base)

                        color_int = span.get("color", 0)
                        if color_int:
                            hex_c = f"#{color_int:06X}"
                            color_counter[hex_c] = color_counter.get(hex_c, 0) + 1

            # 도형에서 색상 + 레이아웃 패턴 파악
            drawings = page.get_drawings()
            for d in drawings:
                rect = d.get("rect")
                fill = d.get("fill")
                if not (fill and rect):
                    continue

                r, g, b = fill[:3]
                hex_c = f"#{int(r*255):02X}{int(g*255):02X}{int(b*255):02X}"
                color_counter[hex_c] = color_counter.get(hex_c, 0) + 1

                # 배경색 감지 (전체 페이지 크기 도형)
                if rect.width >= pw * 0.9 and rect.height >= ph * 0.9:
                    info["bg_color"] = hex_c
                    if (r + g + b) / 3 < 0.35:
                        info["has_dark_bg"] = True

                # 상단 헤더 바 감지
                if rect.y0 < ph * 0.15 and rect.width >= pw * 0.5 and rect.height < ph * 0.2:
                    info["has_header_bar"] = True

                # 사이드바 감지
                if rect.x0 < pw * 0.1 and rect.height >= ph * 0.5:
                    info["has_sidebar"] = True

            # 이미지 배치 패턴
            img_infos = page.get_image_info()
            right_count = sum(1 for i in img_infos if i["bbox"][0] > pw * 0.4)
            left_count = sum(1 for i in img_infos if i["bbox"][2] < pw * 0.6)
            if right_count > left_count:
                info["image_layout"] = "right"
            elif left_count > right_count:
                info["image_layout"] = "left"
            else:
                info["image_layout"] = "center"

        # 흰/검 제외한 주요 색상 추출
        excluded = {"#FFFFFF", "#000000", "#FFFFFE", "#010101", "#FEFEFE"}
        sorted_colors = sorted(color_counter.items(), key=lambda x: x[1], reverse=True)
        main_colors = [c for c, _ in sorted_colors if c.upper() not in excluded]

        info["colors"] = main_colors[:6]
        if main_colors:
            info["accent_color"] = main_colors[0]
        info["fonts"] = list(font_set)[:4]

        # 레이아웃 힌트
        hints = []
        if info["has_header_bar"]:
            hints.append("colored header bar at top")
        if info["has_sidebar"]:
            hints.append("left sidebar accent")
        hints.append(f"images placed on {info['image_layout']} side")
        info["layout_hints"] = ", ".join(hints)

    except Exception as e:
        info["error"] = str(e)

    return info

