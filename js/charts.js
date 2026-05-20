/* ============================================
   PLATFORMERS 사업소개서 — Charts (Chart.js)
   ============================================ */

document.addEventListener('DOMContentLoaded', () => {
  const PRIMARY = '#00C4E8';
  const PRIMARY_DARK = '#0099B8';
  const ACCENT = '#0066FF';
  const BG_CARD = '#111827';
  const TEXT_SEC = '#94A3B8';
  const TEXT_MUTED = '#64748B';
  const SUCCESS = '#10B981';
  const WARNING = '#F59E0B';

  /* ── P15: 게이지 차트 — 정보 확인 시간 80% 단축 ── */
  const gaugeCtx = document.getElementById('gaugeChart');
  if (gaugeCtx) {
    new Chart(gaugeCtx, {
      type: 'doughnut',
      data: {
        datasets: [{
          data: [80, 20],
          backgroundColor: [PRIMARY, 'rgba(255,255,255,0.05)'],
          borderWidth: 0,
          cutout: '78%'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
          legend: { display: false },
          tooltip: { enabled: false }
        },
        rotation: -90,
        circumference: 180
      }
    });
  }

  /* ── P16: 막대 그래프 — 응답 정확도 / 비용 절감 ── */
  const barCtx = document.getElementById('barChart');
  if (barCtx) {
    new Chart(barCtx, {
      type: 'bar',
      data: {
        labels: ['응답 정확도', '생성 비용', '작업 시간'],
        datasets: [
          {
            label: 'Before',
            data: [62, 100, 100],
            backgroundColor: 'rgba(148,163,184,0.3)',
            borderColor: 'rgba(148,163,184,0.5)',
            borderWidth: 1,
            borderRadius: 6,
            barPercentage: 0.6
          },
          {
            label: 'After (AI)',
            data: [94, 35, 25],
            backgroundColor: 'rgba(0,196,232,0.6)',
            borderColor: PRIMARY,
            borderWidth: 1,
            borderRadius: 6,
            barPercentage: 0.6
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
          legend: {
            display: true,
            position: 'bottom',
            labels: { color: TEXT_SEC, font: { size: 11, family: 'Pretendard' }, padding: 16 }
          },
          tooltip: { enabled: true }
        },
        scales: {
          x: {
            ticks: { color: TEXT_SEC, font: { size: 11, family: 'Pretendard' } },
            grid: { display: false },
            border: { display: false }
          },
          y: {
            ticks: {
              color: TEXT_MUTED,
              font: { size: 10, family: 'Pretendard' },
              callback: v => v + '%'
            },
            grid: { color: 'rgba(255,255,255,0.04)' },
            border: { display: false },
            max: 110
          }
        }
      }
    });
  }

  /* ── P17: 꺾은선 그래프 — MAU 증가 추이 ── */
  const lineCtx = document.getElementById('lineChart');
  if (lineCtx) {
    const gradient = lineCtx.getContext('2d').createLinearGradient(0, 0, 0, 200);
    gradient.addColorStop(0, 'rgba(0,196,232,0.3)');
    gradient.addColorStop(1, 'rgba(0,196,232,0)');

    new Chart(lineCtx, {
      type: 'line',
      data: {
        labels: ['1월', '2월', '3월', '4월', '5월', '6월', '7월', '8월'],
        datasets: [{
          label: 'MAU',
          data: [120, 280, 450, 820, 1350, 2100, 3200, 4800],
          borderColor: PRIMARY,
          backgroundColor: gradient,
          fill: true,
          tension: 0.4,
          pointBackgroundColor: PRIMARY,
          pointBorderColor: '#0A0E17',
          pointBorderWidth: 2,
          pointRadius: 4,
          borderWidth: 2.5
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: BG_CARD,
            titleColor: '#fff',
            bodyColor: TEXT_SEC,
            borderColor: 'rgba(0,196,232,0.2)',
            borderWidth: 1,
            cornerRadius: 8,
            padding: 10
          }
        },
        scales: {
          x: {
            ticks: { color: TEXT_SEC, font: { size: 10, family: 'Pretendard' } },
            grid: { display: false },
            border: { display: false }
          },
          y: {
            ticks: { color: TEXT_MUTED, font: { size: 10, family: 'Pretendard' } },
            grid: { color: 'rgba(255,255,255,0.04)' },
            border: { display: false }
          }
        }
      }
    });
  }

  /* ── P6: 레이더 차트 — AI 기술 역량 ── */
  const radarCtx = document.getElementById('radarChart');
  if (radarCtx) {
    new Chart(radarCtx, {
      type: 'radar',
      data: {
        labels: ['LLM 활용', '데이터 처리', '자동화 설계', '멀티 플랫폼', '보안·거버넌스', 'API 연동'],
        datasets: [{
          label: 'Platformers',
          data: [95, 88, 92, 85, 80, 90],
          backgroundColor: 'rgba(0,196,232,0.15)',
          borderColor: PRIMARY,
          borderWidth: 2,
          pointBackgroundColor: PRIMARY,
          pointBorderColor: '#0A0E17',
          pointBorderWidth: 2,
          pointRadius: 4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
          legend: { display: false }
        },
        scales: {
          r: {
            angleLines: { color: 'rgba(255,255,255,0.06)' },
            grid: { color: 'rgba(255,255,255,0.06)' },
            pointLabels: {
              color: TEXT_SEC,
              font: { size: 11, family: 'Pretendard', weight: '600' }
            },
            ticks: { display: false },
            suggestedMin: 0,
            suggestedMax: 100
          }
        }
      }
    });
  }
});
