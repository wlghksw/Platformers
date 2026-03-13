<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>포트폴리오</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <?php include 'config.php'; ?>
    
    <!-- Header with Category Filters -->
    <header class="header">
        <div class="container">
            <div class="portfolio-header-top">
                <a href="index.php" class="portfolio-logo">
                    <span class="logo-text">Platformers</span>
                </a>
            </div>
            <nav class="category-nav">
                <div class="filter-buttons">
                    <?php foreach ($categories as $category): ?>
                        <button class="filter-btn <?php echo $category === '전체' ? 'active' : ''; ?>" 
                                data-category="<?php echo $category === '전체' ? 'all' : strtolower($category); ?>">
                            <?php echo $category; ?>
                        </button>
                    <?php endforeach; ?>
                </div>
            </nav>
        </div>
    </header>

    <!-- Main Content -->
    <main class="main">
        <div class="container">
            <!-- Portfolio Section -->
            <section class="portfolio-section" id="portfolio">
                <!-- Portfolio Grid -->
                <div class="portfolio-grid" id="portfolioGrid">
                    <?php foreach ($projects as $project): ?>
                        <div class="portfolio-item" data-category="<?php echo strtolower($project['category']); ?>">
                            <a href="<?php echo $project['url']; ?>" target="_blank" class="portfolio-link">
                                <div class="portfolio-thumbnail">
                                    <img src="<?php echo $project['thumbnail']; ?>" 
                                         alt="<?php echo $project['title']; ?>"
                                         onerror="this.src='https://via.placeholder.com/400x300/E0E0E0/666666?text=<?php echo urlencode($project['title']); ?>'">
                                    <div class="portfolio-overlay">
                                        <span class="overlay-text"><?php echo $project['title']; ?></span>
                                    </div>
                                </div>
                                <h3 class="portfolio-title"><?php echo $project['title']; ?></h3>
                            </a>
                        </div>
                    <?php endforeach; ?>
                </div>
            </section>
        </div>
    </main>


    <script src="script.js"></script>
</body>
</html>
