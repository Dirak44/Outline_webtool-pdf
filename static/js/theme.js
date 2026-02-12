/* Theme Toggle - Dark/Light Mode
   Automatisch via System-Einstellung (prefers-color-scheme),
   manuell umschaltbar mit localStorage Persistenz */

(function() {
    var THEME_KEY = 'outline-pdf-theme';

    function getSystemTheme() {
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }

    function getPreferredTheme() {
        var stored = localStorage.getItem(THEME_KEY);
        if (stored) return stored;
        return getSystemTheme();
    }

    function applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        // Icon aktualisieren (falls vorhanden)
        var icon = document.getElementById('themeIcon');
        if (icon) {
            icon.className = theme === 'dark' ? 'bi bi-sun-fill' : 'bi bi-moon-fill';
        }
    }

    function toggleTheme() {
        var current = document.documentElement.getAttribute('data-theme') || 'light';
        var next = current === 'dark' ? 'light' : 'dark';
        localStorage.setItem(THEME_KEY, next);
        applyTheme(next);
    }

    // Sofort anwenden (vor DOM-Laden, verhindert Flash)
    applyTheme(getPreferredTheme());

    // System-Theme Aenderungen automatisch uebernehmen (nur wenn kein manueller Override)
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function(e) {
        if (!localStorage.getItem(THEME_KEY)) {
            applyTheme(e.matches ? 'dark' : 'light');
        }
    });

    // Global verfuegbar machen
    window.toggleTheme = toggleTheme;
})();
