"use client";

import { useState, useEffect } from "react";

export default function Dashboard() {
  const [projectName, setProjectName] = useState("");
  const [analysisLink, setAnalysisLink] = useState("");
  const [coreMaterial, setCoreMaterial] = useState("");
  const [expectedEffect, setExpectedEffect] = useState("");
  const [referenceLinks, setReferenceLinks] = useState("");
  const [extraHashtags, setExtraHashtags] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState("");
  const [result, setResult] = useState<any>(null);
  const [stats, setStats] = useState({ todayCount: 0, avgTime: 0, totalCount: 0 });

  type GenerationState = 'idle' | 'generating' | 'draft_ready' | 'rendering' | 'done';
  const [genState, setGenState] = useState<GenerationState>('idle');
  const [draftData, setDraftData] = useState<any>(null);
  const [draftUsedImages, setDraftUsedImages] = useState<string[]>([]);
  const [draftBaseFilename, setDraftBaseFilename] = useState<string>('');
  const [draftStartTime, setDraftStartTime] = useState<number>(0);
  const [layoutImages, setLayoutImages] = useState<Record<string, string>>({});

  const fetchStats = async () => {
    try {
      const response = await fetch("http://localhost:8000/stats");
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error("Stats fetch error:", error);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  const handleUpload = async () => {
    if (!apiKey) {
      alert("Claude API Key를 입력해주세요.");
      return;
    }
    if (files.length === 0 && !projectName) {
      alert("파일 혹은 프로젝트명(제목)을 입력해주세요.");
      return;
    }

    setLoading(true);
    setStatus("파일을 서버로 업로드 중...");

    try {
      // 1. Upload files or clear previous
      if (files.length > 0) {
        const formData = new FormData();
        files.forEach((file) => formData.append("files", file));
        
        await fetch("http://localhost:8000/upload", {
          method: "POST",
          body: formData,
        });
      } else {
        await fetch("http://localhost:8000/clear_input", {
          method: "POST",
        });
      }

      setStatus("데이터 분석 및 AI 변환 중... (Claude Vision/Styling)");

      // 2. Generate
      const response = await fetch("http://localhost:8000/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          project_name: projectName,
          analysis_link: analysisLink,
          core_material: coreMaterial,
          expected_effect: expectedEffect,
          reference_links: referenceLinks,
          extra_hashtags: extraHashtags,
          api_key: apiKey
        }),
      });

      const data = await response.json();
      if (data.status === "success") {
        setDraftData(data.json_data);
        setDraftUsedImages(data.used_images);
        setDraftBaseFilename(data.base_filename);
        setDraftStartTime(data.start_time);
        setGenState('draft_ready');
        setStatus("문단 생성이 완료되었습니다. 아래에서 이미지를 배치해 주세요!");
      } else {
        setStatus("오류 발생: " + data.detail);
      }
    } catch (error) {
      console.error(error);
      setStatus("통신 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  };

  const handleRenderHtml = async () => {
    setGenState('rendering');
    setStatus("최종 렌더링 중...");
    try {
      const response = await fetch("http://localhost:8000/render_html", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          json_data: draftData,
          used_images: draftUsedImages,
          layout_images: layoutImages,
          base_filename: draftBaseFilename,
          start_time: draftStartTime
        })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "렌더링 실패");
      
      setResult(data);
      setStatus("완료! 최종 결과 파일이 data/output 폴더에 저장되었습니다.");
      setGenState('done');
      fetchStats();
    } catch (err: any) {
      alert("렌더링 실패: " + err.message);
      setGenState('draft_ready');
      setStatus("렌더링 실패");
    }
  };

  return (
    <div>
      <header className="header">
        <h1>Dashboard</h1>
        <p style={{ color: 'var(--text-muted)' }}>블로그 생성 파이프라인을 관리하세요.</p>
      </header>

      <section className="stats-grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
        <div className="stat-card">
          <span className="stat-label">오늘 생성 건수</span>
          <div className="stat-value">{stats.todayCount}</div>
        </div>
        <div className="stat-card">
          <span className="stat-label">평균 변환 시간</span>
          <div className="stat-value">{stats.avgTime}s</div>
        </div>
        <div className="stat-card">
          <span className="stat-label">전체 저장됨</span>
          <div className="stat-value">{stats.totalCount}</div>
        </div>
      </section>

      <div className="content-grid">
        <section className="upload-card">
          <h2 style={{ marginBottom: '20px' }}>새 블로그 스크립트 작성</h2>
          
          <div className="input-group">
            <label className="input-label">📝 분석할 원본 링크 (URL) <span style={{fontSize:'0.8rem', color:'#ff9900', fontWeight:'normal'}}>이 링크의 텍스트를 AI가 읽고 글을 씁니다.</span></label>
            <input type="text" className="form-input" placeholder="예: https://blog.naver.com/... (뉴스, 블로그 기사 등)" value={analysisLink} onChange={(e) => setAnalysisLink(e.target.value)} />
          </div>
          <div className="input-group">
            <label className="input-label">제목 키워드 (프로젝트명/강좌명)</label>
            <input type="text" className="form-input" placeholder="예: Home스쿨 | 세계문화 이야기" value={projectName} onChange={(e) => setProjectName(e.target.value)} />
          </div>
          <div className="input-group" style={{ opacity: analysisLink ? 0.3 : 1, transition: 'opacity 0.3s' }}>
            <label className="input-label">핵심 소재 (분석 링크가 없을 경우 수동입력용)</label>
            <textarea className="form-input" placeholder="예: 입체 퍼즐, 사회교육, 랜드마크 학습" value={coreMaterial} onChange={(e) => setCoreMaterial(e.target.value)} style={{ minHeight: '80px', resize: 'vertical' }} />
          </div>
          <div className="input-group" style={{ opacity: analysisLink ? 0.3 : 1, transition: 'opacity 0.3s' }}>
            <label className="input-label">기대 효과 (아이들이 얻는 이점)</label>
            <textarea className="form-input" placeholder="예: 소근육 발달, 공간 지각 능력, 창의력" value={expectedEffect} onChange={(e) => setExpectedEffect(e.target.value)} style={{ minHeight: '80px', resize: 'vertical' }} />
          </div>
          <div className="input-group">
            <label className="input-label">🔗 하단 첨부용 참고 링크 (홈페이지/유튜브)</label>
            <input type="text" className="form-input" placeholder="예: https://..., https://youtu.be/..." value={referenceLinks} onChange={(e) => setReferenceLinks(e.target.value)} />
          </div>
          <div className="input-group">
            <label className="input-label">필수/추가 해시태그</label>
            <input type="text" className="form-input" placeholder="기본 태그 외 추가 태그 입력 (예: #초등교육 #교구추천)" value={extraHashtags} onChange={(e) => setExtraHashtags(e.target.value)} />
          </div>

          <div className="input-group">
            <label className="input-label">참고 파일 업로드 (PPT, PDF, Word, 이미지)</label>
            <div 
              className="dropzone"
              onClick={() => document.getElementById('file-input')?.click()}
            >
              {files.length > 0 ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', alignItems: 'center', width: '100%' }}>
                  <p style={{ color: 'var(--primary-color)', fontWeight: 600, margin: '0 0 8px 0' }}>
                    ✅ {files.length}개의 파일 선택됨
                  </p>
                  <ul style={{ listStyle: 'none', padding: 0, margin: 0, width: '100%', maxWidth: '400px', textAlign: 'left' }}>
                    {files.map((file, idx) => (
                      <li key={idx} style={{ 
                        fontSize: '0.85rem', 
                        padding: '8px 12px', 
                        backgroundColor: '#f1f5f9', 
                        borderRadius: '6px',
                        marginBottom: '6px',
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px'
                      }}>
                        <span style={{ fontSize: '1.2rem' }}>
                          {file.name.toLowerCase().endsWith('.pdf') ? '📄' : 
                           file.name.toLowerCase().endsWith('.pptx') ? '📊' : 
                           file.name.toLowerCase().endsWith('.docx') ? '📝' : 
                           file.name.toLowerCase().match(/\.(jpg|jpeg|png)$/i) ? '🖼️' : '📁'}
                        </span>
                        {file.name}
                      </li>
                    ))}
                  </ul>
                  <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '8px' }}>
                    클릭하여 파일 추가 업로드 (최대 3개)
                  </p>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setFiles([]);
                    }}
                    style={{
                      marginTop: '8px',
                      padding: '4px 10px',
                      fontSize: '0.75rem',
                      backgroundColor: '#fee2e2',
                      color: '#ef4444',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      fontWeight: 600
                    }}
                  >
                    목록 초기화
                  </button>
                </div>
              ) : (
                <p style={{ color: 'var(--text-muted)' }}>
                  클릭하여 파일 업로드 (최대 3개)
                </p>
              )}
              <input 
                id="file-input" 
                type="file" 
                multiple 
                hidden 
                onChange={(e) => {
                  if (e.target.files) {
                    const selectedFiles = Array.from(e.target.files);
                    setFiles(prev => {
                      const newFiles = [...prev, ...selectedFiles];
                      if (newFiles.length > 3) {
                        alert("최대 3개의 파일까지만 업로드할 수 있습니다.");
                        return newFiles.slice(0, 3);
                      }
                      return newFiles;
                    });
                  }
                  e.target.value = '';
                }}
              />
            </div>
          </div>

          <button 
            className="btn-primary" 
            onClick={handleUpload}
            disabled={loading}
          >
            {loading ? "작업 중..." : "블로그 생성하기"}
          </button>

          {status && (
            <div style={{ marginTop: '20px', padding: '16px', backgroundColor: '#f0f9ff', borderRadius: '8px', color: '#0369a1', fontSize: '0.9rem' }}>
              ⏳ {status}
            </div>
          )}

          {genState === 'draft_ready' && (
            <div style={{ marginTop: '30px', padding: '24px', backgroundColor: '#fff', border: '2px solid #ff9900', borderRadius: '12px', boxShadow: '0 4px 12px rgba(0,0,0,0.05)' }}>
              <h2 style={{ fontSize: '1.2rem', marginBottom: '10px', color: '#ff9900', display: 'flex', alignItems: 'center', gap: '8px' }}>
                📸 이미지 배치 및 최종 수정
              </h2>
              <p style={{ fontSize: '0.9rem', color: '#666', marginBottom: '24px' }}>AI가 생성한 각 단락을 읽어보시고, 필요시 지정된 문단 바로 아래에 이미지를 꽂아넣으세요.</p>
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                {draftData?.body_paragraphs?.map((p: string, idx: number) => (
                  <div key={idx} style={{ backgroundColor: '#f8fafc', padding: '16px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                    <p style={{ color: '#334155', lineHeight: 1.6, marginBottom: '16px', fontSize: '0.95rem' }}>{p}</p>
                    <div style={{ borderTop: '1px dashed #cbd5e1', paddingTop: '16px' }}>
                      <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#475569', marginBottom: '8px' }}>
                        ➕ 이 문단 내용 아래에 이미지 추가
                      </label>
                      <select 
                        value={layoutImages[idx] || ""}
                        onChange={(e) => setLayoutImages(prev => ({...prev, [idx]: e.target.value}))}
                        style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid #cbd5e1', backgroundColor: 'white', color: '#334155', outline: 'none' }}
                      >
                        <option value="">-- 이미지를 삽입하지 않음 --</option>
                        {draftUsedImages.length > 0 && draftUsedImages.map((imgName, i) => (
                          <option key={i} value={imgName}>{imgName}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                ))}
              </div>

              <div style={{ marginTop: '30px', textAlign: 'center' }}>
                <button 
                  onClick={handleRenderHtml}
                  className="btn-primary"
                  style={{ backgroundColor: '#ff9900', padding: '14px 40px', fontSize: '1.1rem', borderRadius: '30px', boxShadow: '0 4px 10px rgba(255, 153, 0, 0.3)', border: 'none', color: 'white', fontWeight: 'bold', cursor: 'pointer' }}
                >
                  🚀 완벽하게 최종 블로그 포스팅 렌더링하기
                </button>
              </div>
            </div>
          )}
        </section>

        <section>
          <div className="stat-card" style={{ marginBottom: '24px' }}>
            <h2 style={{ fontSize: '1.1rem', marginBottom: '16px' }}>설정 (Settings)</h2>
            <div className="input-group">
              <label className="input-label">Claude API Key</label>
              <input 
                type="password" 
                className="form-input" 
                placeholder="sk-ant-..." 
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
              />
            </div>
          </div>

          {result && (
            <div className="stat-card" style={{ borderTop: '4px solid #10b981' }}>
              <h2 style={{ fontSize: '1rem', marginBottom: '12px' }}>최근 생성 결과</h2>
              <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '12px' }}>
                파일명: {result.filename}
              </p>
              <button 
                className="btn-primary" 
                style={{ backgroundColor: '#22c55e' }}
                onClick={() => alert("data/output 폴더에서 파일을 확인하세요!")}
              >
                결과 확인하기
              </button>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
