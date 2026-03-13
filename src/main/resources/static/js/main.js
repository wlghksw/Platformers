// Custom cursor
const cursor = document.getElementById('cursor');
const cursorRing = document.getElementById('cursorRing');
let mouseX = 0, mouseY = 0;
let ringX = 0, ringY = 0;

document.addEventListener('mousemove', e => {
  mouseX = e.clientX;
  mouseY = e.clientY;
  if (cursor) {
    cursor.style.left = mouseX + 'px';
    cursor.style.top = mouseY + 'px';
  }
});

function animateRing() {
  ringX += (mouseX - ringX) * 0.12;
  ringY += (mouseY - ringY) * 0.12;
  if (cursorRing) {
    cursorRing.style.left = ringX + 'px';
    cursorRing.style.top = ringY + 'px';
  }
  requestAnimationFrame(animateRing);
}
animateRing();

document.querySelectorAll('a, button, .project-card, .service-card, .tech-item').forEach(el => {
  el.addEventListener('mouseenter', () => cursor && cursor.classList.add('expanded'));
  el.addEventListener('mouseleave', () => cursor && cursor.classList.remove('expanded'));
});

// Hero canvas animation
const canvas = document.getElementById('heroCanvas');
let ctx = null;
if (canvas) ctx = canvas.getContext('2d');

function resizeCanvas() {
  if (!canvas) return;
  canvas.width = canvas.offsetWidth;
  canvas.height = canvas.offsetHeight;
}
resizeCanvas();
window.addEventListener('resize', resizeCanvas);

let particles = [];
let time = 0;
let scrollProgress = 0;

class Particle {
  constructor() { this.reset(); }
  reset() {
    this.x = Math.random() * canvas.width;
    this.y = Math.random() * canvas.height;
    this.size = Math.random() * 1.5 + 0.5;
    this.speedX = (Math.random() - 0.5) * 0.4;
    this.speedY = (Math.random() - 0.5) * 0.4;
    this.opacity = Math.random() * 0.4 + 0.05;
    this.color = Math.random() > 0.7 ? '#5B4FE8' : Math.random() > 0.5 ? '#00E5FF' : '#ffffff';
    this.life = 0;
    this.maxLife = Math.random() * 200 + 100;
  }
  update() {
    this.x += this.speedX;
    this.y += this.speedY;
    this.life++;
    if (this.life > this.maxLife || this.x < 0 || this.x > canvas.width || this.y < 0 || this.y > canvas.height) {
      this.reset();
    }
  }
  draw() {
    if (!ctx) return;
    const alpha = this.life < 20 ? (this.life / 20) * this.opacity :
                  this.life > this.maxLife - 20 ? ((this.maxLife - this.life) / 20) * this.opacity :
                  this.opacity;
    ctx.beginPath();
    ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
    ctx.fillStyle = this.color;
    ctx.globalAlpha = alpha;
    ctx.fill();
    ctx.globalAlpha = 1;
  }
}

if (canvas) {
  for (let i = 0; i < 120; i++) particles.push(new Particle());
}

function drawGrid() {
  if (!ctx || !canvas) return;
  ctx.strokeStyle = 'rgba(255,255,255,0.015)';
  ctx.lineWidth = 1;
  const gridSize = 60;
  for (let x = 0; x < canvas.width; x += gridSize) {
    ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, canvas.height); ctx.stroke();
  }
  for (let y = 0; y < canvas.height; y += gridSize) {
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(canvas.width, y); ctx.stroke();
  }
}

function drawLogoMark() {
  if (!ctx || !canvas) return;
  const cx = canvas.width * 0.72;
  const cy = canvas.height * 0.5;
  const radius = Math.min(canvas.width, canvas.height) * 0.28;
  const t = time * 0.005;
  const pulse = 1 + Math.sin(t * 2) * 0.02;
  const scrollScale = 1 - scrollProgress * 0.3;

  ctx.save();
  ctx.translate(cx, cy);
  ctx.scale(scrollScale, scrollScale);

  for (let i = 0; i < 3; i++) {
    const ringR = radius * (0.8 + i * 0.15);
    const dash = 6 - i;
    const gap = 12 + i * 8;
    ctx.beginPath();
    ctx.arc(0, 0, ringR * pulse, 0, Math.PI * 2);
    ctx.strokeStyle = `rgba(91,79,232,${0.15 - i * 0.04})`;
    ctx.lineWidth = 1;
    ctx.setLineDash([dash, gap]);
    ctx.lineDashOffset = -t * (20 + i * 10);
    ctx.stroke();
    ctx.setLineDash([]);
  }

  const sq = radius * 0.75 * pulse;
  const bLen = sq * 0.25;
  const corners = [[-sq,-sq],[sq,-sq],[sq,sq],[-sq,sq]];
  const dirs = [[1,0,0,1],[-1,0,0,1],[-1,0,0,-1],[1,0,0,-1]];
  ctx.strokeStyle = 'rgba(0,229,255,0.5)';
  ctx.lineWidth = 1.5;
  corners.forEach(([cx2, cy2], i) => {
    const [dx1, dy1, dx2, dy2] = dirs[i];
    ctx.beginPath();
    ctx.moveTo(cx2 + dx1*bLen, cy2);
    ctx.lineTo(cx2, cy2);
    ctx.lineTo(cx2, cy2 + dy2*bLen);
    ctx.stroke();
  });

  const fontS = radius * 0.55;
  ctx.font = `800 ${fontS}px 'Syne', system-ui, sans-serif`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillStyle = `rgba(255,255,255,${0.06 + scrollProgress * 0.05})`;
  ctx.fillText('P', 0, 0);

  const grad = ctx.createRadialGradient(0, 0, 0, 0, 0, radius * 0.4);
  grad.addColorStop(0, 'rgba(91,79,232,0.12)');
  grad.addColorStop(1, 'rgba(91,79,232,0)');
  ctx.beginPath();
  ctx.arc(0, 0, radius * 0.4, 0, Math.PI * 2);
  ctx.fillStyle = grad;
  ctx.fill();

  for (let i = 0; i < 5; i++) {
    const angle = t * (0.8 + i * 0.1) + (i * Math.PI * 2 / 5);
    const orbitR = radius * 0.65;
    const dx = Math.cos(angle) * orbitR;
    const dy = Math.sin(angle) * orbitR;
    ctx.beginPath();
    ctx.arc(dx, dy, 2, 0, Math.PI * 2);
    ctx.fillStyle = i % 2 === 0 ? 'rgba(0,229,255,0.7)' : 'rgba(91,79,232,0.7)';
    ctx.fill();
  }

  ctx.restore();
}

function drawScanLine() {
  if (!ctx || !canvas) return;
  const y = ((time * 0.5) % (canvas.height + 40)) - 20;
  const grad = ctx.createLinearGradient(0, y - 40, 0, y + 40);
  grad.addColorStop(0, 'rgba(0,229,255,0)');
  grad.addColorStop(0.5, 'rgba(0,229,255,0.03)');
  grad.addColorStop(1, 'rgba(0,229,255,0)');
  ctx.fillStyle = grad;
  ctx.fillRect(0, y - 40, canvas.width, 80);
}

function drawFrame() {
  if (!ctx || !canvas) return;
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  drawGrid();
  drawScanLine();
  particles.forEach(p => { p.update(); p.draw(); });
  drawLogoMark();
  time++;
  requestAnimationFrame(drawFrame);
}
if (canvas) drawFrame();

// Scroll interactions
const scrollHint = document.getElementById('scrollHint');

window.addEventListener('scroll', () => {
  const scroll = window.scrollY;
  const hero = document.getElementById('hero');
  if (hero) {
    const heroH = hero.offsetHeight;
    scrollProgress = Math.min(scroll / heroH, 1);
  }
  if (scrollHint) {
    scrollHint.style.opacity = Math.max(0, 1 - scroll / 150);
  }
});

// Scroll reveal
const revealEls = document.querySelectorAll('.reveal');
const observer = new IntersectionObserver(entries => {
  entries.forEach((entry, i) => {
    if (entry.isIntersecting) {
      setTimeout(() => entry.target.classList.add('visible'), i * 60);
      observer.unobserve(entry.target);
    }
  });
}, { threshold: 0.1 });

revealEls.forEach(el => observer.observe(el));

// Portfolio filter (portfolio 페이지에서 사용)
const filterButtons = document.querySelectorAll('.filter-btn');
const portfolioItems = document.querySelectorAll('.portfolio-item');

filterButtons.forEach(btn => {
  btn.addEventListener('click', () => {
    const cat = btn.getAttribute('data-category');
    filterButtons.forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    portfolioItems.forEach(item => {
      const itemCat = item.getAttribute('data-category');
      item.style.display = (cat === 'all' || itemCat === cat) ? '' : 'none';
    });
  });
});
