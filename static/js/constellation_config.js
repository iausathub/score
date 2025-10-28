/**
 * Shared constellation configuration
 */
window.ConstellationConfig = {
    colors: {
        light: { starlink: '#142943', kuiper: '#fbb552', qianfan: '#8e44ad', spacemobile: '#16a085', oneweb: '#c0392b', other: '#5c7da7' },
        dark: { starlink: '#4a9eff', kuiper: '#e18605', qianfan: '#9b59b6', spacemobile: '#27ae60', oneweb: '#ec7063', other: '#8ba3c4' }
    },

    names: { starlink: 'Starlink', kuiper: 'Kuiper', qianfan: 'Qianfan', spacemobile: 'SpaceMobile', oneweb: 'OneWeb', other: 'Other' },

    getCurrentTheme: () => document.documentElement.getAttribute('data-bs-theme') || 'light',

    getColors: (theme) => window.ConstellationConfig.colors[theme || window.ConstellationConfig.getCurrentTheme()],

    getColor: (id, theme) => {
        const colors = window.ConstellationConfig.getColors(theme);
        return colors[id] || colors.other;
    },

    getName: (id) => window.ConstellationConfig.names[id] || window.ConstellationConfig.names.other,

};
