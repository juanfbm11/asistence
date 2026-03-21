document.addEventListener('DOMContentLoaded', () => {
    const path = window.location.pathname;
    document.querySelectorAll('.nav-tab').forEach(tab => {
        const href = tab.getAttribute('href');
        if (href && href !== '/' && path.includes(href.replace(/\//g, ''))) {
            tab.classList.add('active');
        }
    });
});