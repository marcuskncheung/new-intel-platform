/* Dark Mode Theme JavaScript */
class ThemeManager {
    constructor() {
        this.init();
    }

    init() {
        // Get saved theme or default to light
        const savedTheme = localStorage.getItem('intelligence-theme') || 'light';
        this.setTheme(savedTheme);
        
        // Add theme toggle button event
        document.addEventListener('DOMContentLoaded', () => {
            this.createThemeToggle();
        });
    }

    setTheme(theme) {
        if (theme === 'dark') {
            document.documentElement.setAttribute('data-bs-theme', 'dark');
        } else {
            document.documentElement.removeAttribute('data-bs-theme');
        }
        localStorage.setItem('intelligence-theme', theme);
        this.updateToggleIcon(theme);
    }

    toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-bs-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        this.setTheme(newTheme);
    }

    updateToggleIcon(theme) {
        const toggleBtn = document.getElementById('theme-toggle');
        if (toggleBtn) {
            const icon = toggleBtn.querySelector('i');
            if (theme === 'dark') {
                icon.className = 'bi bi-sun-fill';
                toggleBtn.setAttribute('title', 'Switch to Light Mode');
            } else {
                icon.className = 'bi bi-moon-fill';
                toggleBtn.setAttribute('title', 'Switch to Dark Mode');
            }
        }
    }

    createThemeToggle() {
        // Find navbar to add toggle button
        const navbar = document.querySelector('.navbar .container');
        if (!navbar) return;

        // Check if toggle already exists
        if (document.getElementById('theme-toggle')) return;

        // Create theme toggle button
        const themeToggle = document.createElement('button');
        themeToggle.id = 'theme-toggle';
        themeToggle.className = 'theme-toggle btn btn-outline-secondary ms-2';
        themeToggle.innerHTML = '<i class="bi bi-moon-fill"></i>';
        themeToggle.setAttribute('title', 'Switch to Dark Mode');
        themeToggle.setAttribute('aria-label', 'Toggle dark mode');
        
        themeToggle.addEventListener('click', (e) => {
            e.preventDefault();
            this.toggleTheme();
        });

        // Add to navbar - try multiple locations
        const navbarCollapse = navbar.querySelector('.navbar-collapse');
        if (navbarCollapse) {
            // Look for existing navbar-nav elements
            const rightNavbar = navbarCollapse.querySelector('.ms-auto') || 
                              navbarCollapse.querySelector('.navbar-nav:last-child');
            
            if (rightNavbar) {
                // Create nav item wrapper
                const li = document.createElement('li');
                li.className = 'nav-item';
                li.appendChild(themeToggle);
                rightNavbar.appendChild(li);
            } else {
                // Create new navbar-nav for the toggle
                const navDiv = document.createElement('div');
                navDiv.className = 'navbar-nav ms-auto';
                const li = document.createElement('li');
                li.className = 'nav-item';
                li.appendChild(themeToggle);
                navDiv.appendChild(li);
                navbarCollapse.appendChild(navDiv);
            }
        } else {
            // Fallback: add directly to navbar container
            const toggleWrapper = document.createElement('div');
            toggleWrapper.className = 'ms-auto';
            toggleWrapper.appendChild(themeToggle);
            navbar.appendChild(toggleWrapper);
        }

        // Update icon based on current theme
        const currentTheme = document.documentElement.getAttribute('data-bs-theme') || 'light';
        this.updateToggleIcon(currentTheme);
    }
}

// Initialize theme manager
const themeManager = new ThemeManager();
