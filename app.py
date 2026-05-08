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

from flask import Flask, request, jsonify, send_file, render_template
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

ALLOWED_CONTENT_EXTENSIONS = {".pdf", ".docx", ".pptx", ".txt"}
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
    """
    PPT 생성 엔드포인트

    Form data:
        content_file: 콘텐츠 문서 (PDF, DOCX, PPTX, TXT)
        template_file: 양식 파일 (PPTX, 선택)
        instructions: 추가 지시사항 (텍스트, 선택)
    """
    from utils.file_parser import extract_text, get_template_info, extract_images_from_pdf
    from utils.claude_api import generate_slides
    from utils.pptx_builder import build_presentation

    # ── 1. 파일 수신 (콘텐츠 문서만 필수로 받음) ──
    if "content_file" not in request.files:
        return jsonify({"error": "콘텐츠 파일을 업로드해주세요."}), 400

    content_file = request.files["content_file"]
    instructions = request.form.get("instructions", "").strip()

    if not content_file.filename:
        return jsonify({"error": "파일을 선택해주세요."}), 400

    if not allowed_content(content_file.filename):
        return jsonify({"error": f"지원하지 않는 파일 형식입니다. ({', '.join(ALLOWED_CONTENT_EXTENSIONS)})"}), 400

    # ── 2. 파일 저장 ──
    session_id = str(uuid.uuid4())[:8]
    content_ext = Path(content_file.filename).suffix.lower()
    content_path = UPLOAD_DIR / f"{session_id}_content{content_ext}"
    content_file.save(str(content_path))

    # ── 3. 텍스트 추출 ──
    try:
        document_text = extract_text(str(content_path))
        if not document_text.strip():
            return jsonify({"error": "문서에서 텍스트를 추출할 수 없습니다."}), 400
    except Exception as e:
        return jsonify({"error": f"파일 파싱 실패: {str(e)}"}), 500

    # ── 4. 콘텐츠 PDF 이미지 추출 (제안서 내 사진 활용) ──
    images = []
    if content_ext == ".pdf":
        try:
            img_dir = str(UPLOAD_DIR / f"{session_id}_imgs")
            images = extract_images_from_pdf(str(content_path), img_dir)
        except Exception:
            images = []

    # ── 5. Claude API로 슬라이드 구조 생성 (크레용스쿨 표준 양식 적용) ──
    try:
        # 템플릿 정보 없이 내용만으로 슬라이드 구성 요청
        slides_data = generate_slides(
            document_text=document_text,
            template_info=None,
            custom_instructions=instructions,
        )
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"슬라이드 구조 생성 실패: {str(e)}"}), 500

    # ── 6. 데이터 저장 및 뷰어로 리다이렉트 ──
    data_path = OUTPUT_DIR / f"{session_id}_data.json"
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump({
            "slides_data": slides_data,
            "images": images
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
        
    return render_template("viewer.html", slides=slides, title=title, images=image_urls)

from flask import send_from_directory
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
            custom_instructions=instructions,
        )
        return jsonify(slides_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG", "false").lower() == "true")
