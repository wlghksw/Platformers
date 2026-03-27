import { useState } from "react";

const MENU = [
  { id: "dashboard", icon: "⊞", label: "대시보드" },
  { id: "documents", icon: "📄", label: "문서 자동생성" },
  { id: "data", icon: "📊", label: "데이터 분석" },
  { id: "schedule", icon: "📅", label: "일정·알림" },
  { id: "automate", icon: "⚡", label: "자동화 흐름" },
  { id: "settings", icon: "⚙", label: "설정" },
];

const STATUS_CARDS = [
  { label: "오늘 자동 생성된 문서", value: "3건", color: "#0078D4", bg: "#EFF6FF" },
  { label: "진행 중인 자동화 흐름", value: "5개", color: "#107C10", bg: "#F0FFF0" },
  { label: "이번 주 알림 발송", value: "12건", color: "#8764B8", bg: "#F5F0FF" },
  { label: "미완료 승인 요청", value: "2건", color: "#D83B01", bg: "#FFF4F0" },
];

const DOC_TEMPLATES = [
  { name: "주간 업무 보고서", desc: "팀 주간 업무 내용을 자동으로 정리합니다", tag: "보고서" },
  { name: "회의록 자동 작성", desc: "안건을 입력하면 회의록 양식으로 변환합니다", tag: "회의" },
  { name: "이메일 초안 생성", desc: "요청 내용을 바탕으로 이메일을 작성합니다", tag: "커뮤니케이션" },
  { name: "프로젝트 현황 리포트", desc: "프로젝트 진행 상황을 정리한 문서를 생성합니다", tag: "프로젝트" },
];

const DATA_TASKS = [
  { name: "월별 매출 데이터 분석", status: "완료", time: "오늘 09:15" },
  { name: "설문 응답 수집 및 집계", status: "진행 중", time: "오늘 11:30" },
  { name: "부서별 KPI 자동 리포트", status: "예약됨", time: "오늘 18:00" },
];

const SCHEDULES = [
  { title: "전사 주간 회의", time: "14:00", type: "회의", color: "#0078D4" },
  { title: "프로젝트 마감 알림 발송", time: "16:00", type: "알림", color: "#107C10" },
  { title: "월간 보고서 자동 생성", time: "18:00", type: "자동화", color: "#8764B8" },
];

const FLOWS = [
  { name: "결재 요청 → Teams 알림 → 이메일", active: true, runs: "127회 실행" },
  { name: "데이터 수집 → 자동 분석 → 리포트 저장", active: true, runs: "54회 실행" },
  { name: "일정 등록 → 참석자 알림 발송", active: false, runs: "비활성" },
  { name: "신규 직원 온보딩 문서 자동 발송", active: true, runs: "8회 실행" },
];

function Badge({ text, color }) {
  return (
    <span style={{
      background: color + "22", color, fontSize: 11, padding: "2px 8px",
      borderRadius: 20, fontWeight: 600, border: `1px solid ${color}44`
    }}>{text}</span>
  );
}

function DashboardView() {
  return (
    <div>
      <h2 style={{ margin: "0 0 6px", fontSize: 22, color: "#201F1E" }}>대시보드</h2>
      <p style={{ margin: "0 0 24px", color: "#605E5C", fontSize: 14 }}>
        오늘도 업무 자동화로 시간을 절약하세요 👋
      </p>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 14, marginBottom: 28 }}>
        {STATUS_CARDS.map((c) => (
          <div key={c.label} style={{
            background: c.bg, border: `1.5px solid ${c.color}33`,
            borderRadius: 10, padding: "18px 20px"
          }}>
            <div style={{ fontSize: 28, fontWeight: 700, color: c.color }}>{c.value}</div>
            <div style={{ fontSize: 13, color: "#605E5C", marginTop: 4 }}>{c.label}</div>
          </div>
        ))}
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 18 }}>
        <div style={{ background: "#fff", border: "1.5px solid #EDEBE9", borderRadius: 10, padding: 20 }}>
          <div style={{ fontWeight: 700, marginBottom: 14, color: "#201F1E" }}>오늘의 자동화 일정</div>
          {SCHEDULES.map((s) => (
            <div key={s.title} style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 10 }}>
              <div style={{
                width: 8, height: 8, borderRadius: "50%", background: s.color, flexShrink: 0
              }} />
              <div style={{ flex: 1, fontSize: 14, color: "#201F1E" }}>{s.title}</div>
              <div style={{ fontSize: 13, color: "#605E5C" }}>{s.time}</div>
              <Badge text={s.type} color={s.color} />
            </div>
          ))}
        </div>
        <div style={{ background: "#fff", border: "1.5px solid #EDEBE9", borderRadius: 10, padding: 20 }}>
          <div style={{ fontWeight: 700, marginBottom: 14, color: "#201F1E" }}>최근 데이터 작업</div>
          {DATA_TASKS.map((t) => (
            <div key={t.name} style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 10 }}>
              <div style={{ flex: 1, fontSize: 14, color: "#201F1E" }}>{t.name}</div>
              <Badge
                text={t.status}
                color={t.status === "완료" ? "#107C10" : t.status === "진행 중" ? "#0078D4" : "#8764B8"}
              />
              <div style={{ fontSize: 12, color: "#A19F9D", whiteSpace: "nowrap" }}>{t.time}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function DocumentsView() {
  const [selected, setSelected] = useState(null);
  const [input, setInput] = useState("");
  const [generated, setGenerated] = useState("");
  const [loading, setLoading] = useState(false);

  const generate = () => {
    if (!selected || !input.trim()) return;
    setLoading(true);
    setTimeout(() => {
      setGenerated(
        `[${selected.name}]\n\n작성일: ${new Date().toLocaleDateString("ko-KR")}\n\n입력 내용: ${input}\n\n---\n자동 생성된 문서 내용이 여기에 표시됩니다.\n\n• AI가 입력하신 내용을 분석하여 전문 양식으로 변환했습니다.\n• 필요 시 내용을 직접 수정하거나 다운로드할 수 있습니다.\n• MS Teams Copilot 연동 후에는 더욱 풍부한 내용을 생성합니다.`
      );
      setLoading(false);
    }, 1200);
  };

  return (
    <div>
      <h2 style={{ margin: "0 0 6px", fontSize: 22, color: "#201F1E" }}>문서 자동생성</h2>
      <p style={{ margin: "0 0 20px", color: "#605E5C", fontSize: 14 }}>
        템플릿을 선택하고 내용을 입력하면 AI가 문서를 자동으로 작성합니다
      </p>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(2,1fr)", gap: 12, marginBottom: 24 }}>
        {DOC_TEMPLATES.map((t) => (
          <div
            key={t.name}
            onClick={() => { setSelected(t); setGenerated(""); }}
            style={{
              border: selected?.name === t.name ? "2px solid #0078D4" : "1.5px solid #EDEBE9",
              borderRadius: 10, padding: 16, cursor: "pointer", background: selected?.name === t.name ? "#EFF6FF" : "#fff",
              transition: "all 0.15s"
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 6 }}>
              <div style={{ fontWeight: 600, fontSize: 14, color: "#201F1E" }}>{t.name}</div>
              <Badge text={t.tag} color="#0078D4" />
            </div>
            <div style={{ fontSize: 13, color: "#605E5C" }}>{t.desc}</div>
          </div>
        ))}
      </div>
      {selected && (
        <div style={{ background: "#fff", border: "1.5px solid #EDEBE9", borderRadius: 10, padding: 20 }}>
          <div style={{ fontWeight: 600, marginBottom: 10, color: "#201F1E" }}>
            📝 {selected.name} 작성하기
          </div>
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="작성할 내용의 핵심 키워드나 요점을 입력하세요..."
            style={{
              width: "100%", minHeight: 80, padding: 12, border: "1.5px solid #EDEBE9",
              borderRadius: 8, fontSize: 14, resize: "vertical", outline: "none",
              fontFamily: "inherit", boxSizing: "border-box", color: "#201F1E"
            }}
          />
          <button
            onClick={generate}
            disabled={!input.trim() || loading}
            style={{
              marginTop: 10, background: loading ? "#A19F9D" : "#0078D4", color: "#fff",
              border: "none", borderRadius: 8, padding: "10px 24px",
              fontSize: 14, fontWeight: 600, cursor: loading ? "not-allowed" : "pointer"
            }}
          >
            {loading ? "생성 중..." : "AI로 문서 생성"}
          </button>
          {generated && (
            <pre style={{
              marginTop: 16, background: "#F3F2F1", borderRadius: 8, padding: 16,
              fontSize: 13, color: "#201F1E", whiteSpace: "pre-wrap", lineHeight: 1.7
            }}>
              {generated}
            </pre>
          )}
        </div>
      )}
    </div>
  );
}

function DataView() {
  return (
    <div>
      <h2 style={{ margin: "0 0 6px", fontSize: 22, color: "#201F1E" }}>데이터 수집·분석</h2>
      <p style={{ margin: "0 0 20px", color: "#605E5C", fontSize: 14 }}>
        데이터를 업로드하거나 자동 수집을 설정하고 AI 분석 리포트를 받으세요
      </p>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 18 }}>
        <div style={{ background: "#fff", border: "1.5px solid #EDEBE9", borderRadius: 10, padding: 20 }}>
          <div style={{ fontWeight: 700, marginBottom: 14, color: "#201F1E" }}>데이터 업로드</div>
          <div style={{
            border: "2px dashed #C7E0F4", borderRadius: 10, padding: 32,
            textAlign: "center", color: "#605E5C", cursor: "pointer", background: "#F8FCFF"
          }}>
            <div style={{ fontSize: 32, marginBottom: 8 }}>📂</div>
            <div style={{ fontSize: 14, marginBottom: 4, fontWeight: 600 }}>파일을 여기에 드래그하거나</div>
            <div style={{ fontSize: 13, color: "#A19F9D" }}>Excel, CSV, JSON 파일 지원</div>
            <button style={{
              marginTop: 12, background: "#0078D4", color: "#fff", border: "none",
              borderRadius: 6, padding: "8px 18px", fontSize: 13, cursor: "pointer"
            }}>파일 선택</button>
          </div>
        </div>
        <div style={{ background: "#fff", border: "1.5px solid #EDEBE9", borderRadius: 10, padding: 20 }}>
          <div style={{ fontWeight: 700, marginBottom: 14, color: "#201F1E" }}>진행 중인 작업</div>
          {DATA_TASKS.map((t) => (
            <div key={t.name} style={{
              border: "1px solid #EDEBE9", borderRadius: 8, padding: 12, marginBottom: 10
            }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div style={{ fontSize: 14, fontWeight: 600, color: "#201F1E" }}>{t.name}</div>
                <Badge
                  text={t.status}
                  color={t.status === "완료" ? "#107C10" : t.status === "진행 중" ? "#0078D4" : "#8764B8"}
                />
              </div>
              <div style={{ fontSize: 12, color: "#A19F9D", marginTop: 4 }}>{t.time}</div>
            </div>
          ))}
        </div>
      </div>
      <div style={{
        marginTop: 18, background: "#FFF9F0", border: "1.5px solid #F7D6A0",
        borderRadius: 10, padding: 16, display: "flex", alignItems: "center", gap: 12
      }}>
        <div style={{ fontSize: 20 }}>⚡</div>
        <div>
          <div style={{ fontWeight: 600, fontSize: 14, color: "#8A4500" }}>Power Automate 연동 예정</div>
          <div style={{ fontSize: 13, color: "#A05000", marginTop: 2 }}>
            MS365 도입 후 SharePoint, Teams, Outlook과 자동으로 데이터를 연동할 수 있습니다
          </div>
        </div>
      </div>
    </div>
  );
}

function ScheduleView() {
  const [newTitle, setNewTitle] = useState("");
  const [newTime, setNewTime] = useState("");
  const [items, setItems] = useState(SCHEDULES);

  const add = () => {
    if (!newTitle.trim() || !newTime) return;
    setItems([...items, { title: newTitle, time: newTime, type: "알림", color: "#107C10" }]);
    setNewTitle(""); setNewTime("");
  };

  return (
    <div>
      <h2 style={{ margin: "0 0 6px", fontSize: 22, color: "#201F1E" }}>일정·알림 관리</h2>
      <p style={{ margin: "0 0 20px", color: "#605E5C", fontSize: 14 }}>
        일정을 등록하면 자동으로 팀원들에게 알림이 발송됩니다
      </p>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 18 }}>
        <div style={{ background: "#fff", border: "1.5px solid #EDEBE9", borderRadius: 10, padding: 20 }}>
          <div style={{ fontWeight: 700, marginBottom: 14, color: "#201F1E" }}>오늘 일정</div>
          {items.map((s, i) => (
            <div key={i} style={{
              display: "flex", alignItems: "center", gap: 12,
              padding: "10px 0", borderBottom: i < items.length - 1 ? "1px solid #F3F2F1" : "none"
            }}>
              <div style={{
                width: 40, height: 40, borderRadius: 8, background: s.color + "22",
                display: "flex", alignItems: "center", justifyContent: "center",
                fontSize: 18, flexShrink: 0
              }}>
                {s.type === "회의" ? "🤝" : s.type === "알림" ? "🔔" : "⚡"}
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 14, fontWeight: 600, color: "#201F1E" }}>{s.title}</div>
                <div style={{ fontSize: 12, color: "#A19F9D" }}>{s.time}</div>
              </div>
              <Badge text={s.type} color={s.color} />
            </div>
          ))}
        </div>
        <div style={{ background: "#fff", border: "1.5px solid #EDEBE9", borderRadius: 10, padding: 20 }}>
          <div style={{ fontWeight: 700, marginBottom: 14, color: "#201F1E" }}>새 일정 등록</div>
          <input
            value={newTitle}
            onChange={(e) => setNewTitle(e.target.value)}
            placeholder="일정 제목"
            style={{
              width: "100%", padding: "10px 12px", border: "1.5px solid #EDEBE9",
              borderRadius: 8, fontSize: 14, marginBottom: 10, outline: "none",
              fontFamily: "inherit", boxSizing: "border-box", color: "#201F1E"
            }}
          />
          <input
            type="time"
            value={newTime}
            onChange={(e) => setNewTime(e.target.value)}
            style={{
              width: "100%", padding: "10px 12px", border: "1.5px solid #EDEBE9",
              borderRadius: 8, fontSize: 14, marginBottom: 10, outline: "none",
              fontFamily: "inherit", boxSizing: "border-box", color: "#201F1E"
            }}
          />
          <button
            onClick={add}
            style={{
              width: "100%", background: "#0078D4", color: "#fff", border: "none",
              borderRadius: 8, padding: "10px 0", fontSize: 14, fontWeight: 600, cursor: "pointer"
            }}
          >
            일정 등록 및 알림 설정
          </button>
          <div style={{
            marginTop: 14, background: "#F0FFF0", border: "1px solid #C6E8C6",
            borderRadius: 8, padding: 12, fontSize: 13, color: "#107C10"
          }}>
            ✅ Teams 연동 시 등록과 동시에 채널 알림이 자동 발송됩니다
          </div>
        </div>
      </div>
    </div>
  );
}

function AutomateView() {
  const [flows, setFlows] = useState(FLOWS);

  const toggle = (i) => {
    setFlows(flows.map((f, idx) => idx === i ? { ...f, active: !f.active } : f));
  };

  return (
    <div>
      <h2 style={{ margin: "0 0 6px", fontSize: 22, color: "#201F1E" }}>자동화 흐름 관리</h2>
      <p style={{ margin: "0 0 20px", color: "#605E5C", fontSize: 14 }}>
        Power Automate 흐름을 이 포털에서 직접 제어합니다
      </p>
      {flows.map((f, i) => (
        <div key={i} style={{
          background: "#fff", border: "1.5px solid #EDEBE9", borderRadius: 10,
          padding: 18, marginBottom: 12, display: "flex", alignItems: "center", gap: 14
        }}>
          <div style={{ fontSize: 24 }}>⚡</div>
          <div style={{ flex: 1 }}>
            <div style={{ fontWeight: 600, fontSize: 14, color: "#201F1E" }}>{f.name}</div>
            <div style={{ fontSize: 12, color: "#A19F9D", marginTop: 3 }}>{f.runs}</div>
          </div>
          <div
            onClick={() => toggle(i)}
            style={{
              width: 44, height: 24, borderRadius: 12, cursor: "pointer",
              background: f.active ? "#0078D4" : "#C7C6C5", position: "relative",
              transition: "background 0.2s", flexShrink: 0
            }}
          >
            <div style={{
              position: "absolute", top: 3, left: f.active ? 22 : 2,
              width: 18, height: 18, borderRadius: "50%", background: "#fff",
              transition: "left 0.2s"
            }} />
          </div>
          <div style={{ fontSize: 13, color: f.active ? "#107C10" : "#A19F9D", width: 50 }}>
            {f.active ? "활성" : "비활성"}
          </div>
        </div>
      ))}
      <div style={{
        marginTop: 8, background: "#EFF6FF", border: "1.5px solid #C7E0F4",
        borderRadius: 10, padding: 16, display: "flex", alignItems: "center", gap: 12
      }}>
        <div style={{ fontSize: 20 }}>🔗</div>
        <div>
          <div style={{ fontWeight: 600, fontSize: 14, color: "#004E8C" }}>MS365 Power Automate 연동</div>
          <div style={{ fontSize: 13, color: "#0064B1", marginTop: 2 }}>
            라이선스 도입 후 실제 흐름과 연결됩니다 · Teams, Outlook, SharePoint 지원
          </div>
        </div>
      </div>
    </div>
  );
}

export default function EmployeePortal() {
  const [activeMenu, setActiveMenu] = useState("dashboard");

  const renderContent = () => {
    if (activeMenu === "dashboard") return <DashboardView />;
    if (activeMenu === "documents") return <DocumentsView />;
    if (activeMenu === "data") return <DataView />;
    if (activeMenu === "schedule") return <ScheduleView />;
    if (activeMenu === "automate") return <AutomateView />;
    if (activeMenu === "settings") return (
      <div>
        <h2 style={{ fontSize: 22, color: "#201F1E", margin: "0 0 12px" }}>설정</h2>
        <p style={{ color: "#605E5C", fontSize: 14 }}>MS365 연동 및 알림 설정을 여기서 관리합니다</p>
        {[
          ["Microsoft Teams", "연결 대기 중", "#A19F9D"],
          ["Power Automate", "연결 대기 중", "#A19F9D"],
          ["Microsoft Copilot", "라이선스 필요", "#D83B01"],
          ["이메일 알림", "활성", "#107C10"],
        ].map(([name, status, color]) => (
          <div key={name} style={{
            background: "#fff", border: "1.5px solid #EDEBE9", borderRadius: 10,
            padding: 16, marginBottom: 10, display: "flex", justifyContent: "space-between", alignItems: "center"
          }}>
            <div style={{ fontWeight: 600, color: "#201F1E" }}>{name}</div>
            <Badge text={status} color={color} />
          </div>
        ))}
      </div>
    );
  };

  return (
    <div style={{
      fontFamily: "'Segoe UI', 'Apple SD Gothic Neo', sans-serif",
      display: "flex", height: "100vh", background: "#FAF9F8"
    }}>
      {/* 사이드바 */}
      <div style={{
        width: 220, background: "#201F1E", display: "flex", flexDirection: "column",
        padding: "20px 0", flexShrink: 0
      }}>
        {/* 로고 */}
        <div style={{ padding: "0 20px 24px", borderBottom: "1px solid #3B3A39" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <div style={{
              width: 32, height: 32, borderRadius: 8, background: "#0078D4",
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: 16, fontWeight: 700, color: "#fff"
            }}>W</div>
            <div>
              <div style={{ color: "#fff", fontWeight: 700, fontSize: 14 }}>WorkPortal</div>
              <div style={{ color: "#A19F9D", fontSize: 11 }}>업무 자동화 허브</div>
            </div>
          </div>
        </div>
        {/* 메뉴 */}
        <div style={{ flex: 1, padding: "16px 12px" }}>
          {MENU.map((m) => (
            <div
              key={m.id}
              onClick={() => setActiveMenu(m.id)}
              style={{
                display: "flex", alignItems: "center", gap: 10, padding: "10px 12px",
                borderRadius: 8, marginBottom: 2, cursor: "pointer",
                background: activeMenu === m.id ? "#0078D4" : "transparent",
                color: activeMenu === m.id ? "#fff" : "#C7C6C5",
                transition: "all 0.15s",
                fontSize: 14
              }}
            >
              <span style={{ fontSize: 16 }}>{m.icon}</span>
              {m.label}
            </div>
          ))}
        </div>
        {/* 사용자 정보 */}
        <div style={{
          padding: "16px 20px", borderTop: "1px solid #3B3A39",
          display: "flex", alignItems: "center", gap: 10
        }}>
          <div style={{
            width: 32, height: 32, borderRadius: "50%", background: "#0078D4",
            display: "flex", alignItems: "center", justifyContent: "center",
            color: "#fff", fontSize: 14, fontWeight: 700
          }}>최</div>
          <div>
            <div style={{ color: "#fff", fontSize: 13, fontWeight: 600 }}>최지환</div>
            <div style={{ color: "#A19F9D", fontSize: 11 }}>관리자</div>
          </div>
        </div>
      </div>
      {/* 메인 컨텐츠 */}
      <div style={{ flex: 1, overflow: "auto", padding: 32 }}>
        {renderContent()}
      </div>
    </div>
  );
}
