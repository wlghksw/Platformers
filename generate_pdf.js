#!/usr/bin/env node
/**
 * generate_pdf.js
 * 브리핑 마크다운을 받아 스타일된 PDF로 변환합니다.
 * 사용: node generate_pdf.js --output ./output/briefing.pdf --data '{"title":"...","markdown":"..."}'
 *
 * 설치: npm install puppeteer marked
 */

const puppeteer = require("puppeteer");
const { marked } = require("marked");
const path = require("path");

// CLI 인수 파싱
const args = process.argv.slice(2);
const getArg = (flag) => {
  const i = args.indexOf(flag);
  return i !== -1 ? args[i + 1] : null;
};

const outputPath = getArg("--output") || "./output/briefing.pdf";
const rawData = getArg("--data") || "{}";
const report = JSON.parse(rawData);

const htmlTemplate = (title, date, htmlBody, notionUrl) => `
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap');
    
    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: 'Noto Sans KR', sans-serif;
      font-size: 13px;
      line-height: 1.7;
      color: #1a1a2e;
      padding: 40px 48px;
    }

    /* 헤더 배너 */
    .header {
      background: linear-gradient(135deg, #1a1a2e 0%, #16213e 60%, #0f3460 100%);
      color: white;
      padding: 28px 32px;
      border-radius: 12px;
      margin-bottom: 28px;
    }
    .header h1 { font-size: 20px; font-weight: 700; margin-bottom: 4px; }
    .header .meta { font-size: 11px; opacity: 0.7; }

    /* 섹션 */
    h2 {
      font-size: 15px;
      font-weight: 700;
      color: #0f3460;
      border-left: 4px solid #0f3460;
      padding-left: 10px;
      margin: 22px 0 10px;
    }
    h3 { font-size: 13px; font-weight: 600; margin: 14px 0 6px; }

    p { margin-bottom: 8px; color: #2d2d2d; }

    ul { padding-left: 20px; margin-bottom: 10px; }
    li { margin-bottom: 4px; color: #2d2d2d; }

    /* Bull/Bear 카드 */
    h2:has(+ ul) { margin-bottom: 6px; }
    
    /* 키워드 태그 스타일은 JS로 처리 */
    .keyword-tag {
      display: inline-block;
      background: #e8f4fd;
      color: #0f3460;
      border: 1px solid #b8d4ee;
      border-radius: 12px;
      padding: 2px 10px;
      font-size: 11px;
      font-weight: 500;
      margin: 2px;
    }

    /* Notion 링크 */
    .notion-link {
      margin-top: 28px;
      padding: 12px 16px;
      background: #f5f5f5;
      border-radius: 8px;
      font-size: 11px;
      color: #666;
    }
    .notion-link a { color: #0f3460; }

    /* 푸터 */
    .footer {
      margin-top: 32px;
      padding-top: 12px;
      border-top: 1px solid #e5e5e5;
      font-size: 10px;
      color: #aaa;
      text-align: center;
    }

    /* 페이지 나누기 방지 */
    h2, h3 { page-break-after: avoid; }
  </style>
</head>
<body>
  <div class="header">
    <h1>${title}</h1>
    <div class="meta">${date} · AI 자동 생성 브리핑</div>
  </div>

  <div class="content">
    ${htmlBody}
  </div>

  ${notionUrl ? `
  <div class="notion-link">
    📎 Notion 원본:
    <a href="${notionUrl}">${notionUrl}</a>
  </div>` : ""}

  <div class="footer">
    본 리포트는 AI가 뉴스를 수집·분석하여 자동 생성했습니다. 투자 판단의 참고 자료로만 활용하세요.
  </div>
</body>
</html>
`;

// 키워드 줄을 태그 뱃지로 변환
function postProcessHTML(html) {
  // "급상승 키워드" 다음 <p> 태그의 쉼표 구분 텍스트를 뱃지로 변환
  return html.replace(
    /(<h2>[^<]*급상승[^<]*<\/h2>\s*<p>)([^<]+)(<\/p>)/,
    (_, open, keywords, close) => {
      const tags = keywords
        .split(",")
        .map((k) => `<span class="keyword-tag">${k.trim()}</span>`)
        .join(" ");
      return `${open}${tags}${close}`;
    }
  );
}

(async () => {
  const browser = await puppeteer.launch({
    args: ["--no-sandbox", "--disable-setuid-sandbox"],
  });
  const page = await browser.newPage();

  const rawHtml = marked.parse(report.markdown || "");
  const processedHtml = postProcessHTML(rawHtml);
  const fullHtml = htmlTemplate(
    report.title || "주식 브리핑",
    report.date || "",
    processedHtml,
    report.notion_url || ""
  );

  await page.setContent(fullHtml, { waitUntil: "networkidle0" });

  await page.pdf({
    path: outputPath,
    format: "A4",
    margin: { top: "12mm", bottom: "12mm", left: "10mm", right: "10mm" },
    printBackground: true,
  });

  await browser.close();
  console.log(`PDF 생성 완료: ${path.resolve(outputPath)}`);
})();
