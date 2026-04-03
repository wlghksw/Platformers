import os
import shutil
import glob
import json
import time
import re
import base64
import markdown
from datetime import datetime
from typing import List
from io import BytesIO
from PIL import Image
from mimetypes import guess_type
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import anthropic

# Document parsing libraries
from pptx import Presentation
from docx import Document
import pdfplumber  # Replaced fitz due to DLL issues
from fpdf import FPDF

app = FastAPI()

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Base directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_DIR = os.path.join(BASE_DIR, "data", "input")
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "output")

# Ensure directories exist
os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

HISTORY_FILE = os.path.join(BASE_DIR, "data", "history.json")
if not os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump([], f)

class ProcessRequest(BaseModel):
    project_name: str
    analysis_link: str = ""
    core_material: str = ""
    expected_effect: str = ""
    reference_links: str = ""
    extra_hashtags: str = ""
    api_key: str

class RenderRequest(BaseModel):
    json_data: dict
    used_images: list
    layout_images: dict  # mapping: paragraph index -> image filename (e.g. {"1": "abc.png"})
    base_filename: str
    start_time: float

def encode_image(image_path):
    max_size = 3 * 1024 * 1024  # 최대 3MB 수준으로 압축 (Claude 제한 5MB 대비 안전치)
    with Image.open(image_path) as img:
        # P나 RGBA 모드일 경우 JPEG 저장을 위해 RGB로 변환
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        
        # 해상도가 너무 클 경우 2000px로 리사이징
        max_dim = 2000
        if img.width > max_dim or img.height > max_dim:
            img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
        
        quality = 85
        buffer = BytesIO()
        while True:
            buffer.seek(0)
            buffer.truncate()
            # JPEG로 퀄리티를 조절하여 저장 시도
            img.save(buffer, format="JPEG", quality=quality)
            
            # 크기가 3MB 이하이거나, 더 이상 압축하기 어려울 경우 탈출
            if buffer.tell() <= max_size or quality <= 20:
                break
            quality -= 15
            
        buffer.seek(0)
        return base64.b64encode(buffer.read()).decode('utf-8'), "image/jpeg"

def extract_text_from_pptx(filepath):
    prs = Presentation(filepath)
    text_runs = []
    for slide in prs.slides:
        for shape in slide.shapes:
            if hasattr(shape, "text"):
                text_runs.append(shape.text)
    return "\n".join(text_runs)

def extract_text_from_docx(filepath):
    doc = Document(filepath)
    return "\n".join([para.text for para in doc.paragraphs])

def extract_text_from_pdf(filepath):
    text = ""
    try:
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
    except Exception as e:
        print(f"pdfplumber error: {e}")
    return text

@app.post("/clear_input")
async def clear_input():
    for f in glob.glob(os.path.join(INPUT_DIR, "*")):
        try:
            if os.path.isfile(f):
                os.unlink(f)
        except Exception as e:
            print(f"Delete error: {e}")
    return {"status": "success"}

@app.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    # 이전 세션 파일 모두 지우기 (한 번에 분석할 파일만 남김)
    for f in glob.glob(os.path.join(INPUT_DIR, "*")):
        try:
            os.remove(f)
        except Exception:
            pass

    saved_files = []
    for file in files:
        file_path = os.path.join(INPUT_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        saved_files.append(file.filename)
    return {"status": "success", "files": saved_files}

@app.post("/generate")
async def generate_blog(request: ProcessRequest):
    start_time = time.time()
    file_count = len(glob.glob(os.path.join(OUTPUT_DIR, "blog_*.html"))) + 1
    base_filename = f"blog_{file_count}"

    import requests
    from bs4 import BeautifulSoup
    
    all_text = f"프로젝트/강좌명: {request.project_name}\n\n"
    
    if request.analysis_link and request.analysis_link.strip().startswith('http'):
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            res = requests.get(request.analysis_link.strip(), headers=headers, timeout=10)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, 'html.parser')
                # 네이버 블로그 스마트에디터 iframe 대응
                if 'blog.naver.com' in request.analysis_link and 'PostView' not in request.analysis_link:
                    iframe = soup.find('iframe', id='mainFrame')
                    if iframe and iframe.get('src'):
                        real_url = "https://blog.naver.com" + iframe['src']
                        res = requests.get(real_url, headers=headers, timeout=10)
                        soup = BeautifulSoup(res.text, 'html.parser')
                
                # 불필요한 스크립트/스타일 제거
                for script in soup(["script", "style", "nav", "footer", "iframe"]):
                    script.extract()
                extracted_text = soup.get_text(separator=' ', strip=True)
                all_text += f"\n\n[웹사이트 크롤링 원문 텍스트 ({request.analysis_link})]\n{extracted_text[:4000]}\n\n"
            else:
                all_text += f"\n\n(웹사이트 크롤링 실패 - 상태코드: {res.status_code})\n\n"
        except Exception as e:
            all_text += f"\n\n(웹사이트 크롤링 오류: {str(e)})\n\n"
    image_contents = []
    used_images = []
    
    files = glob.glob(os.path.join(INPUT_DIR, "*"))
    
    if not files:
        all_text += "(참고 파일 없음)\n"
    
    for f in files:
        ext = os.path.splitext(f)[1].lower()
        try:
            if ext == ".pptx":
                all_text += f"\n--- PPT 내용 ({os.path.basename(f)}) ---\n"
                all_text += extract_text_from_pptx(f)
            elif ext == ".docx":
                all_text += f"\n--- Word 내용 ({os.path.basename(f)}) ---\n"
                all_text += extract_text_from_docx(f)
            elif ext == ".pdf":
                all_text += f"\n--- PDF 내용 ({os.path.basename(f)}) ---\n"
                all_text += extract_text_from_pdf(f)
            elif ext in [".png", ".jpg", ".jpeg"]:
                base64_image, mime_type = encode_image(f)
                image_contents.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": mime_type,
                        "data": base64_image,
                    },
                })
                # 이미지를 출력 폴더로 복사하고 프롬프트용 목록에 추가
                orig_name = os.path.basename(f)
                new_image_name = f"{base_filename}_{orig_name}"
                dest_path = os.path.join(OUTPUT_DIR, new_image_name)
                shutil.copy(f, dest_path)
                used_images.append(new_image_name)

        except Exception as e:
            print(f"Error parsing {f}: {e}")

    client = anthropic.Anthropic(api_key=request.api_key)
    
    image_instruction = ""
    if used_images:
        image_instruction = "\n### 업로드된 이미지 활용\n다음 이미지(사진) 파일들이 정보로 제공되었습니다: " + ", ".join(used_images) + "\n이 이미지들을 글의 흐름에 맞추어 본문 중간 적절한 위치에 마크다운 문법으로 넣어주세요. (예: `![이미지 설명](./" + used_images[0] + ")` 형식으로 이미지별로 최소 1장 이상)\n"

    text_prompt = f"""
# 지시어: 아래 정보를 바탕으로 네이버 블로그 스마트에디터 완벽 복제용 JSON 데이터를 생성해줘.

**[매우 중요한 기본 규칙 - 이모지 절대 금지]**
- 절대로 어떠한 형태의 이모지나 이모티콘(🔥, 😊, 🚀, 👍 등)도 사용하지 마세요.

## [입력 데이터]
- 제목 키워드: {request.project_name}
- 핵심 소재: {request.core_material}
- 기대 효과: {request.expected_effect}
- 참고 링크: {request.reference_links}
- 분석할 원본 링크: {request.analysis_link}
- 필수 해시태그: #에듀올랩 #크레용스쿨 #홈스쿨 #이러닝강좌 {request.extra_hashtags}

## [강력 지시사항: 스크래핑된 외부 문서 적극 분석]
하단 **[참고할 첨부파일 기반 추출 내용]** 섹션에 사용자가 제공한 **[웹사이트 크롤링 원문 텍스트]**가 포함되어 있다면, **반드시 그 내용을 1순위로 정독하고 요약**하여 해당 글의 방대한 지식, 특징, 상품 설명 등을 바탕으로 본문(`body_paragraphs`)과 인사이트(`quote_hook`)를 풍부하고 섬세하게 작성하세요. 
내용이 충분히 길고 유익하다면, 사용자가 수동으로 입력한 빈약한 핵심 소재 항목들을 대체하여 스크래핑된 지식 내용만으로 고품질 블로그 글을 쓰셔도 무방합니다.

## [출력 형식 (오직 JSON 데이터만 출력할 것)]
반드시 아래 JSON 포맷에 맞추어 코드 블록(```json) 안에 응답하세요. 다른 설명은 일절 생략하세요.

```json
{{
  "category": "사회/경제, 전문강좌 (혹은 성격에 맞는 분야)",
  "main_title": "{request.project_name} - [강좌성격] | [후킹]! 등 제목 형태",
  "info_left_1": "초등학생(예상 타겟)",
  "info_right_1": "사회/경제",
  "info_left_2": "1강의 50분/20차시 (임의 분량)",
  "info_right_2": "전문강좌",
  "quote_hook": "부모님의 시선을 끄는 캐치프레이즈 인용구를 작성하세요.\\n마치 세계의 이야기와 랜드마크를 재미있게~ 처럼 작성합니다.",
  "body_paragraphs": [
    "'{request.project_name}' 는 초등학생을 위한 강좌입니다. (도입 첫 문장 등 자연스러운 시작)",
    "학생들은 자연스럽게 문화, 역사를 학습 가능합니다.",
    "[IMAGE_2]",
    "본문은 1~2문장 단위로 짤막하게 나뉘어서 배열에 요소로 들어가게 됩니다."
  ],
  "highlight_keywords": [
    "문화, 역사", "소근육 발달", "이해도가 더 높아집니다", "공간 지각 능력과 창의력"
  ],
  "youtube_link_title": "유튜브에서 즐기기",
  "youtube_link": "입력받은 참고링크 중 유튜브 형태의 링크 (없으면 빈칸)",
  "homepage_link_title": "만들면서 배우는 홈페이지 - 크레용스쿨",
  "homepage_link": "입력받은 참고링크 중 홈페이지 링크 (없으면 빈칸)",
  "outro_text": "소개 드리는 강좌들은\\n엄마도 손쉽게 교육할 수 있도록\\n제작한 홈스쿨 이러닝 강좌들입니다!\\n\\n크레용스쿨에서 제작/활용하게 될\\n교육 영상 콘텐츠를 기대해 주세요.\\n\\n앞으로 좋은 콘텐츠 제작에 앞장설\\n에듀올랩에\\n많은 기대와 관심 부탁드려요.",
  "hashtags": "해시태그 모음들"
}}
```
- body_paragraphs 내부에서 시선을 끌만한(주황색/볼드 적용 유도할) 핵심 문구나 단어를 뽑아서 highlight_keywords 배열에 넣어주세요.
- quote_hook, outro_text 내에서 줄바꿈이 필요하다면 반드시 \\n 으로 처리해 주세요.

{image_instruction}

[참고할 첨부파일 기반 추출 내용]
{all_text}
"""

    messages_content = []
    if image_contents:
        messages_content.extend(image_contents)
    messages_content.append({"type": "text", "text": text_prompt})

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4000,
            messages=[{"role": "user", "content": messages_content}]
        )
        blog_content = response.content[0].text
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Parse JSON
    import re
    import json
    
    json_data = {}
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', blog_content, re.DOTALL)
    if json_match:
        try:
            json_data = json.loads(json_match.group(1))
        except Exception as e:
            print("JSON parsing error:", e)
    else:
        print("Regex failed to find JSON format.")
        
    return {"status": "success", "json_data": json_data, "used_images": used_images, "base_filename": base_filename, "start_time": start_time}

@app.post("/render_html")
async def render_html(request: RenderRequest):
    import json
    json_data = request.json_data
    used_images = request.used_images
    layout_images = request.layout_images
    base_filename = request.base_filename
    start_time = request.start_time

    html_path = os.path.join(OUTPUT_DIR, f"{base_filename}.html")
    txt_path = os.path.join(OUTPUT_DIR, f"{base_filename}.txt")
    
    # Render Body Paragraphs with Highlights and User-placed Layout Images
    highlighted_paragraphs = []
    keywords = json_data.get('highlight_keywords', [])
    body_html_parts = []
    
    for idx, p_text in enumerate(json_data.get('body_paragraphs', [])):
        p = p_text
        for kw in keywords:
            if kw and kw in p:
                p = p.replace(kw, f'<span style="color:#ff8c00; font-weight:bold;">{kw}</span>')
        
        # Add paragraph HTML
        body_html_parts.append(f"<div style='text-align: center; color: #555; line-height: 1.8; font-size: 16px; font-weight: 500; font-family: \"Malgun Gothic\", sans-serif; margin-bottom: 25px;'>{p}</div>")
        
        # Check if user placed an image right after this paragraph (idx)
        str_idx = str(idx)
        if str_idx in layout_images and layout_images[str_idx]:
            img_name = layout_images[str_idx]
            body_html_parts.append(f"<div style='text-align: center; margin: 35px 0;'><img src='./{img_name}' style='max-width: 100%; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.05);'/></div>")
    
    body_html = "\n".join(body_html_parts)

    quote_hook = json_data.get('quote_hook', '').replace('\\n', '<br>').replace('\n', '<br>')
    outro_text = json_data.get('outro_text', '').replace('\\n', '<br>').replace('\n', '<br>').replace('에듀올랩', '<span style="color: #ff9900; font-size: 24px; font-weight: bold; font-style: italic;">에듀올랩</span>')
    
    # Generate Link Cards
    link_cards_html = ""
    if json_data.get('homepage_link'):
        link_cards_html += f'''
        <div style="border: 1px solid #e5e5e5; border-radius: 8px; padding: 20px; text-align: left; margin: 20px auto; max-width: 600px;">
            <a href="{json_data.get('homepage_link')}" style="text-decoration: none; color: #333; display: block;">
                <div style="font-weight: bold; margin-bottom: 8px;">{json_data.get('homepage_link_title', '링크 바로가기')}</div>
                <div style="font-size: 13px; color: #00c73c;">{json_data.get('homepage_link')}</div>
            </a>
        </div>
        '''
    if json_data.get('youtube_link'):
        link_cards_html += f'''
        <div style="font-weight: bold; margin: 40px 0 10px 0; color:#333;">{json_data.get('youtube_link_title', '유튜브에서 즐기기')}</div>
        <div style="border: 1px solid #e5e5e5; border-radius: 8px; padding: 20px; text-align: left; margin: 0 auto; max-width: 600px;">
            <a href="{json_data.get('youtube_link')}" style="text-decoration: none; color: #333; display: block;">
                <div style="font-weight: bold; margin-bottom: 8px;">유튜브 영상 보기</div>
                <div style="font-size: 13px; color: #00c73c;">youtube.com</div>
            </a>
        </div>
        '''

    # Assemble Full Naver Clone HTML Envelope
    html_template = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head><meta charset="UTF-8"><title>블로그 결과 - {base_filename}</title></head>
    <body style="margin: 0; padding: 0; background-color: #f9f9f9;">
    <div style="background-color: white; font-family: 'Apple SD Gothic Neo', 'Malgun Gothic', 'Dotum', sans-serif; max-width: 800px; margin: 40px auto; padding: 60px 40px; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
        
        <!-- header area -->
        <div style="text-align: center; margin-bottom: 40px;">
            <span style="color: #ff9900; font-weight: bold; font-size: 16px;">{json_data.get('category', '')}</span>
            <h1 style="font-size: 32px; font-weight: bold; margin: 20px 0; color: #222; word-break: keep-all; line-height: 1.4;">{json_data.get('main_title', '')}</h1>
            <div style="margin: 40px auto 30px auto; border-top: 1px solid #777; width: 60%; position: relative;">
                <div style="position: absolute; top: -7px; left: 50%; width: 12px; height: 12px; background: white; border: 1px solid #555; transform: translateX(-50%) rotate(45deg);"></div>
            </div>
        </div>
        
        <!-- first image (if explicitly chosen, else default to first uploaded) -->
        <div style="text-align: center; margin-bottom: 30px;">
            {'<img src="./' + used_images[0] + '" style="max-width: 100%; border-radius: 12px;"/>' if used_images else '<div style="padding:40px; background:#eee; border-radius:12px; color:#999;">[IMAGE_1]</div>'}
        </div>
        
        <!-- info tags -->
        <div style="margin-bottom: 60px; max-width: 600px; margin-left: auto; margin-right: auto;">
            <span style="display: inline-block; background-color: #ffb800; color: white; padding: 8px 18px; border-radius: 20px; font-weight: bold; font-size: 15px;">이러닝 교안강의</span>
            <h2 style="font-size: 22px; margin: 20px 0; color:#333;">{json_data.get('main_title', '')}</h2>
            
            <table style="width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 16px; color: #666;">
                <tr>
                    <td style="padding: 12px 0; border-bottom: 1px solid #f0f0f0;">{json_data.get('info_left_1', '')}</td>
                    <td style="padding: 12px 0; border-bottom: 1px solid #f0f0f0; text-align: right;"><span style="background-color: #ffe8b3; padding: 5px 14px; border-radius: 12px; color: #333; font-weight: 500;">{json_data.get('info_right_1', '')}</span></td>
                </tr>
                <tr>
                    <td style="padding: 12px 0; border-bottom: 1px solid #f0f0f0;">{json_data.get('info_left_2', '')}</td>
                    <td style="padding: 12px 0; border-bottom: 1px solid #f0f0f0; text-align: right;"><span style="background-color: #e2e2e2; padding: 5px 14px; border-radius: 12px; color: #333; font-weight: 500;">{json_data.get('info_right_2', '')}</span></td>
                </tr>
            </table>
        </div>

        <!-- quote hook -->
        <div style="text-align: center; margin: 70px 0;">
            <span style="font-size: 50px; color: #ccc; font-family: serif; display: block; height: 30px; line-height: 30px;">“</span>
            <p style="color: #ff9900; font-size: 20px; font-weight: bold; font-style: italic; line-height: 1.8; margin: 30px 0;">
                {quote_hook}
            </p>
            <span style="font-size: 50px; color: #ccc; font-family: serif; display: block; height: 30px; line-height: 30px;">”</span>
        </div>

        <!-- main body -->
        <div style="margin-bottom: 80px;">
            {body_html}
        </div>
        
        <!-- Links -->
        <div style="margin: 60px 0; text-align: center;">
            <div style="width: 1px; height: 40px; background-color: #aaa; margin: 0 auto 30px auto;"></div>
            {link_cards_html}
        </div>

        <!-- Outro -->
        <div style="text-align: center; font-size: 17px; color: #555; font-weight:500; line-height: 1.9; margin-top: 80px;">
            {outro_text}
            <br><br>
            <span style="color: #888; font-size: 15px;">{json_data.get('hashtags', '')}</span>
        </div>
        
    </div>
    </body>
    </html>
    """
    
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_template)

    # Clean TXT Dump (Just in Case)
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(json_data, ensure_ascii=False, indent=2))

    # Record history
    duration = time.time() - start_time
    try:
        with open(HISTORY_FILE, "r+", encoding="utf-8") as f:
            history = json.load(f)
            history.append({
                "date": datetime.now().strftime("%Y-%m-%d"),
                "duration": duration
            })
            f.seek(0)
            json.dump(history, f, indent=2)
    except Exception as e:
        print(f"History record error: {e}")

    return {"status": "success", "filename": f"{base_filename}.html"}

@app.get("/stats")
async def get_stats():
    total_files = len(glob.glob(os.path.join(OUTPUT_DIR, "blog_*.html")))
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    today_count = 0
    total_duration = 0
    history_count = 0
    
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            history = json.load(f)
            history_count = len(history)
            for item in history:
                if item.get("date") == today_str:
                    today_count += 1
                total_duration += item.get("duration", 0)
    except:
        pass
    
    avg_time = round(total_duration / history_count, 1) if history_count > 0 else 0
    
    return {
        "todayCount": today_count,
        "avgTime": avg_time,
        "totalCount": total_files
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
