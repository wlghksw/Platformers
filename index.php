<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>포트폴리오 - 메인</title>
    <link rel="stylesheet" href="main.css">
</head>
<body>
    <?php include 'config.php'; ?>
    
    <!-- Header -->
    <header class="main-header">
        <div class="header-container">
            <div class="logo">
                <span class="logo-text">Platformers</span>
            </div>
            <nav class="main-nav">
                <a href="portfolio.php" class="nav-link">포트폴리오</a>
            </nav>
            <div class="header-actions">
                <button class="menu-toggle" id="menuToggle">
                    <span></span>
                    <span></span>
                    <span></span>
                </button>
            </div>
        </div>
    </header>

    <!-- Hero Section with Slider -->
    <main class="hero-section">
        <div class="hero-slider" id="heroSlider">
            <?php foreach ($projects as $index => $project): ?>
                <div class="slide <?php echo $index === 0 ? 'active' : ''; ?>" data-slide="<?php echo $index + 1; ?>">
                    <div class="slide-background <?php echo empty($project['thumbnail']) ? 'gradient-bg-' . ($index + 1) : ''; ?>" 
                         data-bg="<?php echo htmlspecialchars($project['thumbnail']); ?>"></div>
                    <div class="slide-overlay"></div>
                    <div class="slide-content">
                        <div class="content-left">
                            <h1 class="hero-title">지역문화플랫폼</h1>
                            <div class="title-divider"></div>
                            <div class="project-tabs">
                                <?php foreach ($projects as $idx => $proj): ?>
                                    <button class="project-tab <?php echo $idx === $index ? 'active' : ''; ?>" data-slide="<?php echo $idx; ?>">
                                        <?php echo $proj['title']; ?>
                                    </button>
                                <?php endforeach; ?>
                            </div>
                            <div class="project-info">
                                <div class="project-logo">
                                    <span class="logo-symbol"><?php echo mb_substr($project['title'], 0, 1); ?></span>
                                </div>
                                <div class="project-details">
                                    <h2 class="project-name"><?php echo $project['title']; ?></h2>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            <?php endforeach; ?>
        </div>

    </main>


    <script src="main.js"></script>
</body>
</html>
