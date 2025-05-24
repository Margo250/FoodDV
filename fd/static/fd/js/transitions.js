// Плавный переход при клике на ссылки
document.addEventListener('DOMContentLoaded', () => {
    const links = document.querySelectorAll('a[href^="/"], a[href^="#"]');
    
    links.forEach(link => {
        link.addEventListener('click', (e) => {
            // Исключаем ссылки с особыми классами/атрибутами
            if (link.classList.contains('no-transition') || 
                link.getAttribute('target') === '_blank') return;
                
            e.preventDefault();
            const href = link.getAttribute('href');
            
            // Анимация исчезновения
            document.body.style.opacity = '0';
            document.body.style.transition = 'opacity 0.3s ease';
            
            setTimeout(() => {
                window.location.href = href;
            }, 300);
        });
    });
});

// Плавный переход для конкретной ссылки
document.querySelectorAll('.transition-link').forEach(link => {
    link.addEventListener('click', function(e) {
        e.preventDefault();
        const href = this.getAttribute('href');
        
        // Анимация исчезновения
        document.querySelector('main').style.opacity = '0';
        document.querySelector('main').style.transition = 'opacity 0.3s ease';
        
        setTimeout(() => {
            window.location.href = href;
        }, 300);
    });
});
