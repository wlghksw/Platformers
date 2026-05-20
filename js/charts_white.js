/* ============================================
   PLATFORMERS 사업소개서 — Charts (Chart.js) - White Theme
   ============================================ */

document.addEventListener('DOMContentLoaded', () => {
  const PRIMARY = '#0088CC';
  const PRIMARY_DARK = '#006699';
  const ACCENT = '#0055EE';
  const BG_CARD = '#F8FAFC';
  const TEXT_SEC = '#475569';
  const TEXT_MUTED = '#94A3B8';
  const SUCCESS = '#059669';
  const WARNING = '#D97706';

  /* ── P15: 게이지 차트 ── */
  const gaugeCtx = document.getElementById('gaugeChart');
  if (gaugeCtx) {
    new Chart(gaugeCtx, {
      type: 'doughnut',
      data: {
        datasets: [{
          data: [80, 20],
          backgroundColor: [PRIMARY, 'rgba(0,0,0,0.05)'],
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

  /* ── P16: 막대 그래프 ── */
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
            backgroundColor: 'rgba(0,136,204,0.6)',
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
            grid: { color: 'rgba(0,0,0,0.05)' },
            border: { display: false },
            max: 110
          }
        }
      }
    });
  }

  /* ── P6: 레이더 차트 ── */
  const radarCtx = document.getElementById('radarChart');
  if (radarCtx) {
    new Chart(radarCtx, {
      type: 'radar',
      data: {
        labels: ['컨텍스트 이해', '보안·거버넌스', '실행 정확성', '확장성', '관측성'],
        datasets: [{
          label: 'Platformers',
          data: [92, 88, 95, 85, 90],
          backgroundColor: 'rgba(0,136,204,0.1)',
          borderColor: PRIMARY,
          borderWidth: 2,
          pointBackgroundColor: PRIMARY,
          pointBorderColor: '#FFFFFF',
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
            angleLines: { color: 'rgba(0,0,0,0.05)' },
            grid: { color: 'rgba(0,0,0,0.05)' },
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

  /* ── P06: AI 역설 (재검증 비율) 차트 ── */
  const verCtx = document.getElementById('verificationChart');
  if (verCtx) {
    new Chart(verCtx, {
      type: 'doughnut',
      data: {
        datasets: [{
          data: [97.5, 2.5],
          backgroundColor: ['#DC2626', 'rgba(0,0,0,0.05)'],
          borderWidth: 0,
          cutout: '80%'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
          legend: { display: false },
          tooltip: { enabled: false }
        },
        animation: { animateScale: true, animateRotate: true }
      }
    });
  }
});
