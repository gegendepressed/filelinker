document.addEventListener('DOMContentLoaded', function () {
    const toggleButton = document.getElementById('toggleMode');
    const body = document.body;
    const navbar = document.getElementById('navbar');
    const sunIcon = document.getElementById('sunIcon');
    const moonIcon = document.getElementById('moonIcon');
    const brandLogo = document.getElementById('brandLogo');

    // Function to apply the saved theme
    function applyTheme(theme) {
        const isDarkMode = theme === 'dark';

        // Apply the theme classes
        body.classList.toggle('dark-mode', isDarkMode);
        navbar.classList.toggle('dark-mode', isDarkMode);
        toggleButton.classList.toggle('dark-mode', isDarkMode);

        // Update icons and logo
        sunIcon.style.display = isDarkMode ? 'block' : 'none';
        moonIcon.style.display = isDarkMode ? 'none' : 'block';
        brandLogo.src = isDarkMode
            ? "/static/images/brand-dark.svg"
            : "/static/images/brand-light.svg";
    }

    // Retrieve and apply the saved theme
    const savedTheme = localStorage.getItem('theme') || 'light';
    applyTheme(savedTheme);

    // Handle theme toggle
    toggleButton.addEventListener('click', function () {
        const isDarkMode = body.classList.toggle('dark-mode');
        navbar.classList.toggle('dark-mode');
        toggleButton.classList.toggle('dark-mode');

        // Update icons and logo
        sunIcon.style.display = isDarkMode ? 'block' : 'none';
        moonIcon.style.display = isDarkMode ? 'none' : 'block';
        brandLogo.src = isDarkMode
            ? "/static/images/brand-dark.svg"
            : "/static/images/brand-light.svg";

        // Save theme preference
        localStorage.setItem('theme', isDarkMode ? 'dark' : 'light');
    });
});
