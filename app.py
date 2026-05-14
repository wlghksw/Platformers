"""
PPT 자동 생성기 - Flask 웹 서버
Railway 배포용
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

# 파일 크기 제한 (50MB)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024

UPLOAD_DIR = Path("/tmp/uploads")
OUTPUT_DIR = Path("/tmp/outputs")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_CONTENT_EXTENSIONS = {".pdf", ".docx", ".pptx", ".txt", ".xlsx", ".xls"}
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
    """PPT 생성 엔드포인트 (멀티 파일 지원)"""
    from utils.file_parser import extract_text
    from utils.claude_api import generate_slides
    
    # ── 1. 파일 수신 (여러 파일 가능) ──
    content_files = request.files.getlist("content_file")
    instructions = request.form.get("instructions", "").strip()
    category = request.form.get("category", "proposal")

    if not content_files or not content_files[0].filename:
        return jsonify({"error": "콘텐츠 파일을 업로드해주세요."}), 400

    # 허용되지 않는 파일 형식 검사
    for cf in content_files:
        if not allowed_content(cf.filename):
            return jsonify({"error": f"지원하지 않는 파일 형식입니다: {cf.filename}"}), 400

    session_id = str(uuid.uuid4())[:8]
    all_document_texts = []
    has_image_pdf = False
    
    # ── 2. 모든 파일 순회하며 텍스트 추출 ──
    for content_file in content_files:
        content_ext = Path(content_file.filename).suffix.lower()
        content_path = UPLOAD_DIR / f"{session_id}_{content_file.filename}"
        content_file.save(str(content_path))
        
        print(f"[*] Extracting text from: {content_file.filename} ({content_ext})")
        try:
            document_text = extract_text(str(content_path))
            if not document_text or not document_text.strip():
                if content_ext == ".pdf":
                    has_image_pdf = True
                    print(f"[*] Detected image-based PDF: {content_file.filename}")
                continue
            
            all_document_texts.append(f"### [FILE: {content_file.filename}]\n{document_text}")
        except Exception as e:
            print(f"[!] Failed to parse {content_file.filename}: {e}")

    # 모든 텍스트 병합
    combined_text = "\n\n".join(all_document_texts)
    
    # 만약 텍스트가 하나도 없고 이미지 PDF가 있다면 Vision 모드로 전환
    use_vision = False
    if not combined_text.strip() and has_image_pdf:
        use_vision = True
    elif not combined_text.strip():
        return jsonify({"error": "업로드한 파일들에서 텍스트를 추출할 수 없습니다. 내용이 비어있거나 지원하지 않는 형식인지 확인해주세요."}), 400

    # ── 3-b. Vision 폴백: PDF가 이미지로만 구성된 경우 (첫 번째 이미지 PDF 기준) ──
    if use_vision:
        try:
            from utils.file_parser import extract_pdf_as_images
            from utils.claude_api import generate_slides_from_images
            
            # 텍스트가 없는 첫 번째 PDF를 찾아 Vision 분석 진행
            target_pdf = None
            for f in content_files:
                if f.filename.lower().endswith(".pdf"):
                    target_pdf = UPLOAD_DIR / f"{session_id}_{f.filename}"
                    break
            
            if not target_pdf:
                return jsonify({"error": "이미지 기반 분석을 위한 PDF 파일을 찾을 수 없습니다."}), 400

            print(f"[*] Switching to Vision AI mode for: {target_pdf.name}")
            pages = extract_pdf_as_images(str(target_pdf), max_pages=15)
            if not pages:
                return jsonify({"error": "PDF에서 이미지를 추출할 수 없습니다."}), 400
                
            print(f"[*] Sending {len(pages)} page images to Vision AI...")
            slides_data = generate_slides_from_images(pages, custom_instructions=instructions, category=category)
            data_path = OUTPUT_DIR / f"{session_id}_data.json"
            with open(data_path, "w", encoding="utf-8") as f:
                json.dump({"slides_data": slides_data, "images": [], "category": category}, f, ensure_ascii=False)
            return jsonify({"redirect": f"/viewer/{session_id}"})
        except Exception as e:
            traceback.print_exc()
            return jsonify({"error": f"Vision AI 분석 실패: {str(e)}"}), 500

    # ── 5. Claude API로 슬라이드 구조 생성 ──
    try:
        slides_data = generate_slides(
            document_text=combined_text,
            template_info=None,
            custom_instructions=instructions,
            category=category
        )
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"슬라이드 생성 실패: {str(e)}"}), 500

    # ── 6. 데이터 저장 및 뷰어로 리다이렉트 ──
    data_path = OUTPUT_DIR / f"{session_id}_data.json"
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump({
            "slides_data": slides_data,
            "images": [], # 멀티 파일 환경에서는 이미지 추출 우선 생략
            "category": category
        }, f, ensure_ascii=False)

    return jsonify({"redirect": f"/viewer/{session_id}"})

@app.route("/viewer/<session_id>")
def viewer(session_id):
    data_path = OUTPUT_DIR / f"{session_id}_data.json"
    if not data_path.exists():
        return "Session not found", 404
        
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    slides = data.get("slides_data", {}).get("slides", [])
    title = data.get("slides_data", {}).get("presentation_title", "Presentation")
    
    image_paths = data.get("images", [])
    image_urls = [f"/api/images/{session_id}/{Path(img['path']).name}" for img in image_paths if isinstance(img, dict) and "path" in img]
    
    # 첫 번째 슬라이드를 강제로 표지(title)로 지정 (크레용스쿨 템플릿용)
    if slides and slides[0].get("layout") != "title":
        slides[0]["layout"] = "title"
        
    return render_template(
        "viewer.html",
        slides=slides,
        title=title,
        images=image_urls,
        session_id=session_id,
        category=data.get("category", "proposal")
    )

@app.route("/api/images/<session_id>/<filename>")
def serve_image(session_id, filename):
    img_dir = UPLOAD_DIR / f"{session_id}_imgs"
    return send_from_directory(img_dir, filename)


@app.route("/api/preview", methods=["POST"])
def preview():
    """
    슬라이드 구조만 미리보기 (PPTX 생성 없이)
    빠른 미리보기용
    """
    from utils.file_parser import extract_text
    from utils.claude_api import generate_slides

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
