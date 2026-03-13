// Hero Slider Functionality
document.addEventListener('DOMContentLoaded', function() {
    const slides = document.querySelectorAll('.slide');
    const tabs = document.querySelectorAll('.project-tab');
    
    let currentSlide = 0;
    const totalSlides = slides.length;
    let autoSlideInterval;
    let isUserInteracting = false;

    // Update slide display
    function updateSlide() {
        // Remove active class from all slides and tabs
        slides.forEach(slide => slide.classList.remove('active'));
        tabs.forEach(tab => tab.classList.remove('active'));
        
        // Add active class to current slide and tab
        slides[currentSlide].classList.add('active');
        tabs[currentSlide].classList.add('active');
    }

    // Go to specific slide
    function goToSlide(index) {
        currentSlide = index;
        updateSlide();
        resetAutoSlide();
        isUserInteracting = true;
        setTimeout(() => { isUserInteracting = false; }, 3000);
    }

    // Next slide
    function nextSlide() {
        if (!isUserInteracting) {
            currentSlide = (currentSlide + 1) % totalSlides;
            updateSlide();
        }
    }

    // Auto slide
    function startAutoSlide() {
        autoSlideInterval = setInterval(nextSlide, 6000); // Change slide every 6 seconds
    }

    function resetAutoSlide() {
        clearInterval(autoSlideInterval);
        startAutoSlide();
    }

    // Tab click event listeners
    tabs.forEach((tab, index) => {
        tab.addEventListener('click', () => goToSlide(index));
    });

    // Keyboard navigation
    document.addEventListener('keydown', function(e) {
        if (e.key === 'ArrowLeft') {
            currentSlide = (currentSlide - 1 + totalSlides) % totalSlides;
            updateSlide();
            resetAutoSlide();
            isUserInteracting = true;
            setTimeout(() => { isUserInteracting = false; }, 3000);
        }
        if (e.key === 'ArrowRight') {
            currentSlide = (currentSlide + 1) % totalSlides;
            updateSlide();
            resetAutoSlide();
            isUserInteracting = true;
            setTimeout(() => { isUserInteracting = false; }, 3000);
        }
    });

    // Preload all slide backgrounds
    const slideBackgrounds = document.querySelectorAll('.slide-background');
    slideBackgrounds.forEach((bg, index) => {
        const bgUrl = bg.getAttribute('data-bg');
        
        if (bgUrl && bgUrl.trim() !== '') {
            const img = new Image();
            img.onload = function() {
                // Image loaded successfully
                bg.style.backgroundImage = `url('${bgUrl}')`;
            };
            img.onerror = function() {
                // If image fails to load, ensure gradient is visible
                if (!bg.classList.contains('gradient-bg-1') && !bg.classList.contains('gradient-bg-2')) {
                    bg.style.backgroundImage = 'none';
                    bg.style.backgroundColor = index === 0 ? '#2a4a6b' : '#4a2a6b';
                }
            };
            img.src = bgUrl;
        } else {
            // No image URL, gradient will be used
            bg.style.backgroundImage = 'none';
        }
    });

    // Initialize
    updateSlide();
    startAutoSlide();


    // Mobile menu toggle
    const menuToggle = document.getElementById('menuToggle');
    const nav = document.querySelector('.main-nav');
    
    if (menuToggle) {
        menuToggle.addEventListener('click', function() {
            nav.classList.toggle('mobile-open');
            this.classList.toggle('active');
        });
    }
});
