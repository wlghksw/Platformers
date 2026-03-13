// Filter functionality
document.addEventListener('DOMContentLoaded', function() {
    const filterButtons = document.querySelectorAll('.filter-btn');
    const portfolioItems = document.querySelectorAll('.portfolio-item');

    filterButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Remove active class from all buttons
            filterButtons.forEach(btn => btn.classList.remove('active'));
            
            // Add active class to clicked button
            this.classList.add('active');
            
            const category = this.getAttribute('data-category');
            
            // Filter portfolio items
            portfolioItems.forEach(item => {
                if (category === 'all') {
                    item.classList.remove('hidden');
                } else {
                    const itemCategory = item.getAttribute('data-category');
                    if (itemCategory === category) {
                        item.classList.remove('hidden');
                    } else {
                        item.classList.add('hidden');
                    }
                }
            });
        });
    });

    // Mobile menu toggle
    const menuToggle = document.getElementById('menuToggle');
    const nav = document.querySelector('.nav');
    
    if (menuToggle) {
        menuToggle.addEventListener('click', function() {
            nav.classList.toggle('mobile-open');
            this.classList.toggle('active');
        });
    }

    // Inquiry button handlers
    const inquiryButtons = document.querySelectorAll('.btn-primary, .widget-inquiry');
    inquiryButtons.forEach(button => {
        button.addEventListener('click', function() {
            // 여기에 문의 폼 모달이나 연락처 정보를 표시하는 로직을 추가할 수 있습니다
            alert('프로젝트 문의: 연락처 정보를 확인해주세요.');
        });
    });
});
