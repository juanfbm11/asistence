document.addEventListener('DOMContentLoaded', () => {
    const path = window.location.pathname;

    document.querySelectorAll('.nav-tab').forEach(tab => {
        const href = tab.getAttribute('href');
        if (href && href !== '/' && path.includes(href.replace(/\//g, ''))) {
            tab.classList.add('active');
        }
    });

    const settingsMenu = document.querySelector('.settings-menu');
    const settingsToggle = document.querySelector('.settings-toggle');

    if (settingsMenu && settingsToggle) {
        const settingsDropdown = settingsMenu.querySelector('.settings-dropdown');

        settingsToggle.addEventListener('click', event => {
            event.stopPropagation();
            const isOpen = settingsMenu.classList.toggle('open');
            settingsToggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
            if (settingsDropdown) {
                settingsDropdown.hidden = !isOpen;
            }
        });

        document.addEventListener('click', event => {
            if (!settingsMenu.contains(event.target)) {
                settingsMenu.classList.remove('open');
                settingsToggle.setAttribute('aria-expanded', 'false');
                if (settingsDropdown) {
                    settingsDropdown.hidden = true;
                }
            }
        });
    }
});
