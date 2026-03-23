<?php
require __DIR__ . '/config.php';
?>
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Platformers - Portfolio</title>
  <link rel="stylesheet" href="static/css/main.css?v=3">
</head>
<body>

<div class="grid-bg"></div>
<div class="cursor" id="cursor"></div>
<div class="cursor-ring" id="cursorRing"></div>

<!-- NAV -->
<nav>
  <a href="index.php" class="nav-logo">
    <div class="dot"></div>
    Platformers
  </a>
  <ul class="nav-links">
    <li><a href="index.php#services">Services</a></li>
    <li><a href="portfolio.php">Work</a></li>
    <li><a href="index.php#process">Process</a></li>
    <li><a href="index.php#techstack">Stack</a></li>
  </ul>
  <button class="nav-cta" onclick="window.location.href='mailto:hello@platformers.kr'">Contact Us</button>
</nav>

<main style="padding-top:120px;">
  <!-- FILTERS -->
  <section id="marquee">
    <div class="marquee-label">Filter by Category</div>
    <div class="category-nav">
      <div class="filter-buttons">
        <?php foreach ($categories as $category): ?>
          <?php
          $isAll = ($category === '전체');
          $dataCat = $isAll ? 'all' : $category;
          $btnClass = 'filter-btn' . ($isAll ? ' active' : '');
          ?>
          <button type="button"
                  class="<?php echo htmlspecialchars($btnClass); ?>"
                  data-category="<?php echo htmlspecialchars($dataCat); ?>">
            <?php echo htmlspecialchars($category); ?>
          </button>
        <?php endforeach; ?>
      </div>
    </div>
  </section>

  <!-- PORTFOLIO GRID -->
  <section id="portfolio">
    <div class="section-header reveal">
      <div>
        <div class="section-tag">Selected Work</div>
        <h2 class="section-title">All<br>Projects</h2>
      </div>
    </div>

    <div class="portfolio-grid" id="portfolioGrid">
      <?php foreach ($projects as $project): ?>
        <div class="project-card reveal portfolio-item"
             data-category="<?php echo htmlspecialchars($project['category']); ?>">
          <div class="project-visual"
               style="background-image:url(<?php echo htmlspecialchars($project['thumbnail']); ?>);background-size:cover;background-position:center;">
            <div class="project-overlay">
              <a href="<?php echo htmlspecialchars($project['url']); ?>" target="_blank" rel="noopener noreferrer" class="project-overlay-btn">View Project →</a>
            </div>
          </div>
          <div class="project-info">
            <div>
              <div class="project-category"><?php echo htmlspecialchars($project['category']); ?></div>
              <div class="project-name"><?php echo htmlspecialchars($project['title']); ?></div>
            </div>
            <a href="<?php echo htmlspecialchars($project['url']); ?>" target="_blank" rel="noopener noreferrer" class="project-arrow">↗</a>
          </div>
        </div>
      <?php endforeach; ?>
    </div>
  </section>
</main>

<!-- FOOTER -->
<footer>
  <div class="footer-logo">Platformers<span style="color:var(--accent2)">.</span></div>
  <ul class="footer-links">
    <li><a href="index.php#services">Services</a></li>
    <li><a href="portfolio.php">Work</a></li>
    <li><a href="index.php#process">Process</a></li>
    <li><a href="mailto:hello@platformers.kr">Contact</a></li>
  </ul>
  <div class="footer-copy">© 2025 Platformers. All rights reserved.</div>
</footer>

<script src="static/js/main.js"></script>
</body>
</html>
