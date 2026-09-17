/**
 * Shared constellation configuration
 */
window.ConstellationConfig = {
    // Paul Tol "bright" qualitative palette (colorblind-safe; his recommended
    // default), mapped to each constellation's brand hue — every constellation
    // gets its natural color. Grey is Tol's designated "other" slot. The dark
    // column uses lightened steps of the same hues for contrast on the dark
    // surface, keeping blue deeper than cyan so Starlink and SpaceMobile stay apart.
    colors: {
        light: { starlink: '#4477AA', amazonleo: '#CCBB44', qianfan: '#AA3377', spacemobile: '#66CCEE', oneweb: '#EE6677', planetlabs: '#228833', other: '#BBBBBB' },
        dark: { starlink: '#3f80d6', amazonleo: '#d8c85a', qianfan: '#d264a0', spacemobile: '#7dd6f2', oneweb: '#f07a88', planetlabs: '#4caf5f', other: '#b0b0b0' }
    },

    names: { starlink: 'Starlink', amazonleo: 'Amazon LEO', qianfan: 'Qianfan', spacemobile: 'SpaceMobile', oneweb: 'OneWeb', planetlabs: 'Planet Labs', other: 'Other' },

    getCurrentTheme: () => document.documentElement.getAttribute('data-bs-theme') || 'light',

    getColors: (theme) => window.ConstellationConfig.colors[theme || window.ConstellationConfig.getCurrentTheme()],

    getColor: (id, theme) => {
        const colors = window.ConstellationConfig.getColors(theme);
        return colors[id] || colors.other;
    },

    getName: (id) => window.ConstellationConfig.names[id] || window.ConstellationConfig.names.other,

};
