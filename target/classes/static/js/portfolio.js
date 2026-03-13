/**
 * 포트폴리오 페이지 필터 기능 (portfolio.php)
 */

document.addEventListener('DOMContentLoaded', function() {
    const filterButtons = document.querySelectorAll('.filter-btn');
    const portfolioItems = document.querySelectorAll('.portfolio-item');

    /**
     * 필터 버튼 클릭 이벤트
     */
    filterButtons.forEach(button => {
        button.addEventListener('click', function() {
            // 모든 버튼에서 active 클래스 제거
            filterButtons.forEach(btn => btn.classList.remove('active'));
            
            // 클릭한 버튼에 active 클래스 추가
            this.classList.add('active');
            
            const category = this.getAttribute('data-category');
            
            // 포트폴리오 아이템 필터링
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
});
