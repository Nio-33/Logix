/**
 * Logix Theme Manager
 * Handles theme persistence and application across all dashboard pages
 */

class ThemeManager {
    constructor() {
        this.themeKey = 'logix_theme';
        this.settingsKey = 'logix_settings';
        this.init();
    }

    /**
     * Initialize theme manager
     */
    init() {
        console.log('🎨 ThemeManager initializing...');
        // Apply saved theme immediately to prevent flash
        const savedTheme = this.applySavedTheme();
        console.log('🎨 ThemeManager initialized with theme:', savedTheme);
        
        // Listen for theme changes from other pages
        window.addEventListener('storage', (e) => {
            if (e.key === this.themeKey || e.key === this.settingsKey) {
                this.applySavedTheme();
            }
        });
        
        // Listen for system theme changes
        if (window.matchMedia) {
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
                const currentTheme = this.getCurrentTheme();
                if (currentTheme === 'System Default') {
                    this.applyTheme(currentTheme);
                }
            });
        }
    }

    /**
     * Get current theme preference
     */
    getCurrentTheme() {
        // First check settings object
        const settings = localStorage.getItem(this.settingsKey);
        if (settings) {
            try {
                const parsed = JSON.parse(settings);
                if (parsed.theme) {
                    return parsed.theme;
                }
            } catch (e) {
                console.warn('Failed to parse settings:', e);
            }
        }
        
        // Fallback to direct theme key
        return localStorage.getItem(this.themeKey) || 'Light';
    }

    /**
     * Apply theme to document
     */
    applyTheme(theme) {
        const html = document.documentElement;
        const wasDark = html.classList.contains('dark');
        
        // Remove existing theme classes
        html.classList.remove('dark');
        
        if (theme === 'Dark') {
            html.classList.add('dark');
        } else if (theme === 'Light') {
            html.classList.remove('dark');
        } else if (theme === 'System Default') {
            // Use system preference
            if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
                html.classList.add('dark');
            } else {
                html.classList.remove('dark');
            }
        }
        
        const isDark = html.classList.contains('dark');
        console.log(`🎨 Theme applied: ${theme} (${isDark ? 'dark' : 'light'})`);
        
        // Dispatch custom event for other components
        window.dispatchEvent(new CustomEvent('themeChanged', { 
            detail: { theme: theme, isDark: isDark }
        }));
    }

    /**
     * Apply saved theme from localStorage
     */
    applySavedTheme() {
        const theme = this.getCurrentTheme();
        this.applyTheme(theme);
        return theme;
    }

    /**
     * Save theme preference
     */
    saveTheme(theme) {
        // Save to settings object
        let settings = {};
        try {
            const saved = localStorage.getItem(this.settingsKey);
            if (saved) {
                settings = JSON.parse(saved);
            }
        } catch (e) {
            console.warn('Failed to parse existing settings:', e);
        }
        
        settings.theme = theme;
        localStorage.setItem(this.settingsKey, JSON.stringify(settings));
        
        // Also save direct theme key for backward compatibility
        localStorage.setItem(this.themeKey, theme);
        
        // Apply theme immediately
        this.applyTheme(theme);
    }

    /**
     * Toggle between light and dark theme
     */
    toggleTheme() {
        const currentTheme = this.getCurrentTheme();
        const newTheme = currentTheme === 'Dark' ? 'Light' : 'Dark';
        this.saveTheme(newTheme);
        return newTheme;
    }

    /**
     * Get theme toggle button HTML
     */
    getThemeToggleButton() {
        const currentTheme = this.getCurrentTheme();
        const isDark = document.documentElement.classList.contains('dark');
        
        return `
            <button 
                onclick="window.themeManager.toggleTheme()" 
                class="p-2 rounded-lg text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                title="Toggle theme"
            >
                ${isDark ? 
                    '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"></path></svg>' :
                    '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"></path></svg>'
                }
            </button>
        `;
    }
}

// Initialize theme manager when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('🎨 DOM ready, initializing ThemeManager...');
    window.themeManager = new ThemeManager();
});

// Also initialize immediately if DOM is already loaded
if (document.readyState === 'loading') {
    console.log('🎨 DOM still loading, waiting for DOMContentLoaded...');
    // DOM is still loading, wait for DOMContentLoaded
} else {
    console.log('🎨 DOM already loaded, initializing ThemeManager immediately...');
    // DOM is already loaded
    window.themeManager = new ThemeManager();
}
