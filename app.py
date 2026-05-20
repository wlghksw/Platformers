"""
CrayonSchool HTML 교육 제안서 자동 생성기 - Flask 웹 서버
Railway 배포용 | GPT-4o + CrayonSchool Design System
"""
import os
import uuid
import json
import traceback
from pathlib import Path
from datetime import datetime

from flask import Flask, request, jsonify, send_file, render_template, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# 파일 크기 제한 (200MB - 멀티 파일 환경 대응)
app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024

UPLOAD_DIR = Path("/tmp/uploads")
OUTPUT_DIR = Path("/tmp/outputs")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_CONTENT_EXTENSIONS = {".pdf", ".docx", ".pptx", ".txt", ".xlsx", ".xls", ".md", ".jpg", ".jpeg", ".png"}
ALLOWED_TEMPLATE_EXTENSIONS = {".pdf"}


def allowed_content(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_CONTENT_EXTENSIONS


def allowed_template(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_TEMPLATE_EXTENSIONS



@app.route("/")
def index():
    return render_template("index.html")


@app.route("/health")
def health():
    return jsonify({"status": "ok", "timestamp": datetime.utcnow().isoformat()})


@app.route("/api/generate", methods=["POST"])
def generate():
    """HTML 교육 제안서 생성 엔드포인트 (멀티 파일 및 지식 베이스 지원)"""
    from utils.file_parser import extract_text
    from utils.openai_api import generate_slides
    
    # ── 1. 파일 및 데이터 수신 ──
    content_files = request.files.getlist("content_file")
    instructions = request.form.get("instructions", "").strip()
    category = request.form.get("category", "proposal")
    use_defaults = request.form.get("use_defaults", "false").lower() == "true"

    if not content_files or not content_files[0].filename:
        return jsonify({"error": "콘텐츠 파일을 업로드해주세요."}), 400

    # 허용되지 않는 파일 형식 검사
    for cf in content_files:
        if not allowed_content(cf.filename):
            return jsonify({"error": f"지원하지 않는 파일 형식입니다: {cf.filename}"}), 400

    session_id = str(uuid.uuid4())[:8]
    all_document_texts = []
    has_image_pdf = False
    
    # ── 2. 모든 파일 순회하며 텍스트 및 이미지 추출 ──
    from utils.file_parser import extract_images_from_pdf, extract_images_from_pptx
    from utils.openai_api import analyze_images_with_vision as tag_images_with_vision

    all_extracted_images = []
    
    for content_file in content_files:
        content_ext = Path(content_file.filename).suffix.lower()
        content_path = UPLOAD_DIR / f"{session_id}_{content_file.filename}"
        content_file.save(str(content_path))
        
        print(f"[*] Processing: {content_file.filename} ({content_ext})")
        
        # 텍스트 추출
        try:
            document_text = extract_text(str(content_path))
            if document_text and document_text.strip():
                all_document_texts.append(f"### [FILE: {content_file.filename}]\n{document_text}")
            elif content_ext == ".pdf":
                has_image_pdf = True
        except Exception as e:
            print(f"[!] Text extraction failed for {content_file.filename}: {e}")

        # 이미지 추출 (Phase 2 핵심)
        try:
            img_dir = UPLOAD_DIR / f"{session_id}_imgs"
            if content_ext == ".pdf":
                imgs = extract_images_from_pdf(str(content_path), str(img_dir))
                all_extracted_images.extend(imgs)
            elif content_ext == ".pptx":
                imgs = extract_images_from_pptx(str(content_path), str(img_dir))
                all_extracted_images.extend(imgs)
        except Exception as e:
            print(f"[!] Image extraction failed for {content_file.filename}: {e}")

    # 이미지 비전 태깅 (Phase 2 핵심: 15개까지만 정밀 분석)
    image_library = []
    if all_extracted_images:
        print(f"[*] Analyzing {len(all_extracted_images)} images with Vision AI...")
        image_library = tag_images_with_vision(all_extracted_images)
        print(f"[*] Vision tagging complete. {len(image_library)} useful images identified.")

    # 모든 텍스트 병합
    combined_text = "\n\n".join(all_document_texts)
    
    # 만약 텍스트가 하나도 없고 이미지 PDF가 있다면 Vision 모드로 전환
    use_vision = False
    if not combined_text.strip() and has_image_pdf:
        use_vision = True
    elif not combined_text.strip():
        return jsonify({"error": "업로드한 파일들에서 텍스트를 추출할 수 없습니다. 내용이 비어있거나 지원하지 않는 형식인지 확인해주세요."}), 400

    # ── 3-b. Vision 폴백: PDF가 이미지로만 구성된 경우 ──
    if use_vision:
        try:
            from utils.file_parser import extract_pdf_as_images
            from utils.openai_api import generate_slides_from_images
            
            target_pdf = None
            for f in content_files:
                if f.filename.lower().endswith(".pdf"):
                    target_pdf = UPLOAD_DIR / f"{session_id}_{f.filename}"
                    break
            
            if not target_pdf:
                return jsonify({"error": "분석할 PDF를 찾을 수 없습니다."}), 400

            print(f"[*] Vision AI mode for scanned PDF: {target_pdf.name}")
            pages = extract_pdf_as_images(str(target_pdf), max_pages=15)
            
            # Vision 모드에서는 추출된 페이지 자체가 이미지 라이브러리가 됨
            image_library = pages

            slides_data = generate_slides_from_images(
                pages, 
                custom_instructions=instructions, 
                category=category
            )
            # PPTX 빌드 추가
            from utils.pptx_builder import build_presentation
            pptx_path = OUTPUT_DIR / f"{session_id}.pptx"
            build_presentation(
                slides_data=slides_data,
                output_path=str(pptx_path),
                images=image_library,
                template_info=None,
                category=category
            )

            data_path = OUTPUT_DIR / f"{session_id}_data.json"
            with open(data_path, "w", encoding="utf-8") as f:
                json.dump({
                    "slides_data": slides_data, 
                    "images": image_library, 
                    "category": category,
                    "pptx_file": f"{session_id}.pptx"
                }, f, ensure_ascii=False)
            return jsonify({"redirect": f"/viewer/{session_id}"})
        except Exception as e:
            traceback.print_exc()
            return jsonify({"error": f"Vision 분석 실패: {str(e)}"}), 500

    # ── 5. GPT-4o API로 슬라이드 구조 생성 ──
    try:
        slides_data = generate_slides(
            document_text=combined_text,
            template_info=None,
            custom_instructions=instructions,
            category=category,
            image_library=image_library
        )
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"슬라이드 생성 실패: {str(e)}"}), 500

    # ── 6. HTML 파일 생성 및 데이터 저장 ──
    from utils.html_builder import build_html, save_html

    # 이미지 URL 매핑 (viewer와 동일한 로직)
    image_list = []
    for img in image_library:
        if isinstance(img, dict) and "path" in img:
            filename = Path(img["path"]).name
            url = f"/api/images/{session_id}/{filename}"
            image_list.append({**img, "url": url, "path": url})

    # 슬라이드에 매칭 이미지 URL 할당
    for i, slide in enumerate(slides_data.get("slides", [])):
        img_tag = slide.get("image_tag", "")
        layout  = slide.get("layout_type", "full_text")
        matched = None
        if img_tag:
            for img in image_list:
                if img.get("tag", "").lower() == img_tag.lower():
                    matched = img["url"]
                    break
            if not matched:
                for img in image_list:
                    if img_tag.lower() in img.get("tag", "").lower():
                        matched = img["url"]
                        break
        if not matched and layout in ("split_v", "split_h"):
            slide["layout_type"] = "full_text"
        slide["matched_image_url"] = matched

    html_content = build_html(
        slides_data=slides_data,
        images=image_list,
        category=category
    )

    html_path = OUTPUT_DIR / f"{session_id}.html"
    save_html(html_content, str(html_path))
    print(f"[*] HTML built successfully: {html_path}")

    # 세션 데이터 저장
    data_path = OUTPUT_DIR / f"{session_id}_data.json"
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump({
            "slides_data": slides_data,
            "images": image_list,
            "category": category,
            "html_file": f"{session_id}.html"
        }, f, ensure_ascii=False)

    return jsonify({"redirect": f"/viewer/{session_id}"})

@app.route("/download/<session_id>")
def download_html(session_id):
    html_filename = f"{session_id}.html"
    return send_from_directory(
        OUTPUT_DIR, html_filename,
        as_attachment=True,
        download_name=f"CrayonSchool_Proposal_{session_id}.html"
    )

@app.route("/viewer/<session_id>")
def viewer(session_id):
    """생성된 HTML 파일을 직접 서빙"""
    html_path = OUTPUT_DIR / f"{session_id}.html"
    if html_path.exists():
        return send_file(str(html_path), mimetype="text/html")

    # HTML 파일이 없으면 data.json으로 재생성 시도
    data_path = OUTPUT_DIR / f"{session_id}_data.json"
    if not data_path.exists():
        return "Session not found", 404

    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    from utils.html_builder import build_html, save_html
    html_content = build_html(
        slides_data=data.get("slides_data", {}),
        images=data.get("images", []),
        category=data.get("category", "proposal")
    )
    save_html(html_content, str(html_path))
    return send_file(str(html_path), mimetype="text/html")

@app.route("/api/images/<session_id>/<filename>")
def serve_image(session_id, filename):
    img_dir = UPLOAD_DIR / f"{session_id}_imgs"
    return send_from_directory(img_dir, filename)


@app.route("/api/preview", methods=["POST"])
def preview():
    """
    슬라이드 구조 미리보기 JSON 반환 (HTML 생성 없이)
    """
    from utils.file_parser import extract_text
    from utils.openai_api import generate_slides

    if "content_file" not in request.files:
        return jsonify({"error": "content_file이 필요합니다."}), 400

    content_file = request.files["content_file"]
    instructions = request.form.get("instructions", "").strip()

    if not content_file.filename or not allowed_content(content_file.filename):
        return jsonify({"error": "지원하지 않는 파일 형식입니다."}), 400

    session_id = str(uuid.uuid4())[:8]
    content_ext = Path(content_file.filename).suffix.lower()
    content_path = UPLOAD_DIR / f"{session_id}_preview{content_ext}"
    content_file.save(str(content_path))

    try:
        document_text = extract_text(str(content_path))
        slides_data = generate_slides(
            document_text=document_text,
            template_info=None,
            custom_instructions=instructions,
            category="proposal"
        )
        return jsonify(slides_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # Railway 등 환경에서 PORT 환경변수를 우선 사용
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
