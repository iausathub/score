/**
 * Shared constellation configuration
 */
window.ConstellationConfig = {
    colors: {
        light: { starlink: '#142943', kuiper: '#fbb552', qianfan: '#8e44ad', spacemobile: '#0891b2', oneweb: '#c0392b', planetlabs: '#65a30d', other: '#5c7da7' },
        dark: { starlink: '#4a9eff', kuiper: '#e18605', qianfan: '#9b59b6', spacemobile: '#22d3ee', oneweb: '#ec7063', planetlabs: '#a3e635', other: '#8ba3c4' }
    },

    names: { starlink: 'Starlink', kuiper: 'Kuiper', qianfan: 'Qianfan', spacemobile: 'SpaceMobile', oneweb: 'OneWeb', planetlabs: 'Planet Labs', other: 'Other' },

    getCurrentTheme: () => document.documentElement.getAttribute('data-bs-theme') || 'light',

    getColors: (theme) => window.ConstellationConfig.colors[theme || window.ConstellationConfig.getCurrentTheme()],

    getColor: (id, theme) => {
        const colors = window.ConstellationConfig.getColors(theme);
        return colors[id] || colors.other;
    },

    getName: (id) => window.ConstellationConfig.names[id] || window.ConstellationConfig.names.other,

};
