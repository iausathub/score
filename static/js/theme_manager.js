/**
 * Theme Manager - Centralized theme detection and change notifications
 */

window.ThemeManager = (() => {
    const subscribers = [];
    let currentTheme = document.documentElement.getAttribute('data-bs-theme') || 'light';

    // Watch for theme changes on the html element
    const observer = new MutationObserver(() => {
        const newTheme = document.documentElement.getAttribute('data-bs-theme') || 'light';
        if (newTheme !== currentTheme) {
            currentTheme = newTheme;
            subscribers.forEach(callback => callback(newTheme));
        }
    });

    observer.observe(document.documentElement, {
        attributes: true,
        attributeFilter: ['data-bs-theme']
    });

    return {
        subscribe: (callback) => subscribers.push(callback),
        getCurrentTheme: () => document.documentElement.getAttribute('data-bs-theme') || 'light'
    };
})();
