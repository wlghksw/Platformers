/* ==========================================================================
   CRAYONSCHOOL Presentation Theme Charts JS v1.0
   Chart.js integrations configured with warm primary academic brand colors.
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
  /* ── CrayonSchool Theme Color Palette ── */
  const CRAYON_PALETTE = {
    yellow: '#FFC000',
    yellowLight: '#FFFBE8',
    navy: '#215E80',
    skyBlue: '#4189B3',
    lightGray: '#EBEBEB',
    darkGray: '#555555',
    textMuted: '#999999'
  };

  /* ── 1. 교육 업무 자동화율 도넛 차트 (Doughnut Chart) ── */
  const autoCtx = document.getElementById('automationChart');
  if (autoCtx) {
    new Chart(autoCtx, {
      type: 'doughnut',
      data: {
        labels: ['자동화 완료', '대기 업무'],
        datasets: [{
          data: [82.5, 17.5],
          backgroundColor: [CRAYON_PALETTE.yellow, CRAYON_PALETTE.lightGray],
          borderWidth: 0,
          cutout: '80%'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
          legend: { display: false },
          tooltip: {
            enabled: true,
            titleFont: { family: 'Noto Sans KR', size: 12 },
            bodyFont: { family: 'Noto Sans KR', size: 12 }
          }
        },
        animation: {
          animateScale: true,
          animateRotate: true
        }
      }
    });
  }

  /* ── 2. 플랫폼 운영 기술 역량 방사형 차트 (Radar Chart) ── */
  const platformCtx = document.getElementById('platformRadarChart');
  if (platformCtx) {
    new Chart(platformCtx, {
      type: 'radar',
      data: {
        labels: ['과정 관리', '강사 매칭', '교구재 유통', '출결 시스템', '정산 자동화'],
        datasets: [{
          label: '크레용스쿨 플랫폼',
          data: [95, 92, 88, 90, 85],
          borderColor: CRAYON_PALETTE.navy,
          backgroundColor: 'rgba(33, 94, 128, 0.1)',
          borderWidth: 2,
          pointBackgroundColor: CRAYON_PALETTE.skyBlue,
          pointBorderColor: '#FFFFFF',
          pointBorderWidth: 2,
          pointRadius: 4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
          legend: { display: false },
          tooltip: {
            titleFont: { family: 'Noto Sans KR', size: 12 },
            bodyFont: { family: 'Noto Sans KR', size: 12 }
          }
        },
        scales: {
          r: {
            angleLines: { color: 'rgba(33, 94, 128, 0.08)' },
            grid: { color: 'rgba(33, 94, 128, 0.08)' },
            ticks: { display: false },
            suggestedMin: 0,
            suggestedMax: 100,
            pointLabels: {
              font: {
                family: 'Noto Sans KR',
                size: 12,
                weight: '700'
              },
              color: CRAYON_PALETTE.darkGray
            }
          }
        }
      }
    });
  }

  /* ── 3. 도입 전/후 업무 효율 향상 지표 막대 차트 (Bar Chart) ── */
  const efficiencyCtx = document.getElementById('efficiencyBarChart');
  if (efficiencyCtx) {
    new Chart(efficiencyCtx, {
      type: 'bar',
      data: {
        labels: ['정산 시간', '강의 관리 비용', '학부모 소통 지연'],
        datasets: [
          {
            label: '도입 전 (AS-IS)',
            data: [100, 100, 100],
            backgroundColor: 'rgba(153, 153, 153, 0.3)',
            borderColor: 'rgba(153, 153, 153, 0.4)',
            borderWidth: 1,
            borderRadius: 6,
            barPercentage: 0.6
          },
          {
            label: '도입 후 (TO-BE)',
            data: [15, 40, 20],
            backgroundColor: CRAYON_PALETTE.navy,
            borderColor: CRAYON_PALETTE.navy,
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
            labels: {
              color: CRAYON_PALETTE.darkGray,
              font: { size: 12, family: 'Noto Sans KR' },
              padding: 16
            }
          }
        },
        scales: {
          x: {
            ticks: { color: CRAYON_PALETTE.darkGray, font: { size: 12, family: 'Noto Sans KR' } },
            grid: { display: false },
            border: { display: false }
          },
          y: {
            ticks: {
              color: CRAYON_PALETTE.textMuted,
              font: { size: 11, family: 'Outfit' },
              callback: v => v + '%'
            },
            grid: { color: 'rgba(0, 0, 0, 0.04)' },
            border: { display: false },
            max: 110
          }
        }
      }
    });
  }
});
