// theme-toggle.js

document.addEventListener('DOMContentLoaded', () => {
    // Function to apply the theme based on the current mode
    function applyTheme(theme) {
        const body = document.body;
        if (theme === 'dark') {
            body.classList.add('dark-theme');
            document.getElementById('theme-toggle').checked = true;
        } else {
            body.classList.remove('dark-theme');
            document.getElementById('theme-toggle').checked = false;
        }
    }

    // Function to toggle the theme and save preference
    function toggleTheme() {
        const body = document.body;
        if (body.classList.contains('dark-theme')) {
            body.classList.remove('dark-theme');
            localStorage.setItem('theme', 'light');
        } else {
            body.classList.add('dark-theme');
            localStorage.setItem('theme', 'dark');
        }
    }

    // Event listener for the theme toggle switch
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('change', toggleTheme);
    }

    // Apply the saved theme on page load
    const savedTheme = localStorage.getItem('theme') || 'light';
    applyTheme(savedTheme);
});
