/**
 * Satellite All-Sky Plots using Plotly.js
 * Creates all-sky plots showing satellite observations as viewed from ground
 */

// ============================================================================
// CONSTANTS
// ============================================================================

const CONSTELLATION_SYMBOLS = {
    'starlink': 'circle',
    'kuiper': 'square',
    'qianfan': 'diamond',
    'spacemobile': 'triangle-up',
    'oneweb': 'star',
    'planetlabs': 'diamond-tall',
    'other': 'cross',
    'all': 'circle'
};

const PLOT_CONFIG = {
    colorscales: {
        dark: 'Viridis',
        light: 'YlOrRd'
    },
    defaultMarkerSize: 6,
    compassTicks: {
        values: [0, 15, 30, 45, 60, 75, 90, 105, 120, 135, 150, 165, 180, 195, 210, 225, 240, 255, 270, 285, 300, 315, 330, 345],
        labels: ['N', '', '', 'NE', '', '', 'E', '', '', 'SE', '', '', 'S', '', '', 'SW', '', '', 'W', '', '', 'NW', '', '']
    }
};

/**
 * Store last plot data and options for theme change updates.
 * When theme changes, the plot is recreated with these stored values.
 */
let lastPlotData = null;
let lastPlotOptions = null;


// Subscribe to theme changes via centralized ThemeManager
if (window.ThemeManager) {
    ThemeManager.subscribe((theme) => {
        if (lastPlotData && lastPlotOptions) {
            console.log('Updating all-sky plot for theme:', theme);
            createAllSkyPlot(lastPlotData, lastPlotOptions);
        }
    });
}


/**
 * Update charts - called by satellite_selector.js
 * Reads data from observations-data element and creates/updates the plot
 * @global
 */
window.updateCharts = function() {
    const el = document.getElementById('observations-data');
    if (!el) {
        console.error('observations-data element not found');
        return;
    }

    try {
        const data = JSON.parse(el.textContent);
        if (data && data.length > 0) {
            // Show the plots container
            const container = document.getElementById('plots-container');
            if (container) {
                container.classList.remove('d-none');
            }

            // Create the all-sky plot with default settings
            createAllSkyPlot(data, {
                enableTooltip: true,
                enableZoom: true,
                groupByConstellation: true,
                plotElementId: 'allsky-plot',
                title: 'All-Sky Plot: Selected Observations'
            });
        }
    } catch (e) {
        console.error('Error parsing observation data:', e);
    }
};

/**
 * Create an all-sky polar plot showing satellite observations
 * @param {Array<Object>} observationData - Array of observation objects
 * @param {Object} options - Plot configuration options
 * @param {boolean} [options.enableTooltip=true] - Show tooltips on hover
 * @param {boolean} [options.enableZoom=true] - Enable zoom/pan interactions
 * @param {boolean} [options.groupByConstellation=true] - Group traces by constellation
 * @param {string} [options.plotElementId='allsky-plot'] - DOM element ID for plot
 * @param {string} [options.title='All-Sky Plot: Satellite Observations'] - Plot title
 * @param {number} [options.markerSize=6] - Marker size in pixels
 * @param {Object} [options.margin] - Custom plot margins {l, r, t, b}
 */
function createAllSkyPlot(observationData, options = {}) {
    const {
        enableTooltip = true,
        enableZoom = true,
        groupByConstellation = true,
        plotElementId = 'allsky-plot',
        title = 'All-Sky Plot: Satellite Observations',
        markerSize = PLOT_CONFIG.defaultMarkerSize,
        margin = null
    } = options;

    // Store data and options for theme change updates
    lastPlotData = observationData;
    lastPlotOptions = options;

    const validObs = observationData.filter(o =>
        o.alt_deg_satchecker != null && o.az_deg_satchecker != null && o.magnitude != null
    );
    if (!validObs.length) return;

    const theme = window.ConstellationConfig.getCurrentTheme();
    const colors = window.ConstellationConfig.getColors(theme);

    let traces;
    if (groupByConstellation) {
        // Group by constellation and create traces
        const groups = {};
        validObs.forEach(o => {
            const key = o.constellation || 'other';
            (groups[key] = groups[key] || []).push(o);
        });
        traces = Object.entries(groups).map(([c, obs], index) =>
            createTrace(obs, c, colors[c], enableTooltip, index === 0, markerSize)  // Only show colorbar for first trace
        );
    } else {
        // Create a single trace with all observations
        traces = [createTrace(validObs, 'all', colors.starlink || '#4285f4', enableTooltip, true, markerSize)];
    }

    const isDark = theme === 'dark';
    const textColor = isDark ? '#ccc' : '#666';

    // Get the container element for responsive sizing
    const container = document.getElementById(plotElementId);

    // Create custom home/reset button since polar plots don't seem to
    // have one by default.
    const homeButton = {
      name: 'home',
      title: 'Reset view',
      icon: {
          width: 512,
          height: 512,
          path: 'M256 0l-256 256h64v256h128v-128h128v128h128v-256h64z',
          transform: 'scale(1)'
      },
      click: function(gd) {
          Plotly.relayout(gd, {
              'polar.radialaxis.range': [0, 90],
              'polar.radialaxis.autorange': false,
              'polar.angularaxis.rotation': 90
          });
      }
    };

    Plotly.newPlot(plotElementId, traces, {
        title: { text: title, font: { size: 14, color: textColor } },
        polar: {
            bgcolor: isDark ? '#1a1a1a' : '#fff',
            radialaxis: {
                range: [0, 90],
                dtick: 15,
                tickfont: { size: 10, color: textColor },
                gridcolor: isDark ? 'rgba(255,255,255,0.4)' : 'rgba(0,0,0,0.3)',
                gridwidth: 1.5,
                showline: true,
                linewidth: 2,
                linecolor: isDark ? 'rgba(255,255,255,0.3)' : 'rgba(0,0,0,0.2)'
            },
            angularaxis: {
                tickvals: PLOT_CONFIG.compassTicks.values,
                ticktext: PLOT_CONFIG.compassTicks.labels,
                direction: 'clockwise',
                rotation: 90,
                gridcolor: isDark ? 'rgba(255,255,255,0.3)' : 'rgba(0,0,0,0.2)',
                gridwidth: 1,
                tickfont: { size: 12, color: textColor }
            }
        },
        paper_bgcolor: 'rgba(0,0,0,0)',
        font: { color: textColor },
        legend: {
            x: 1.05,
            y: 1,
            bgcolor: isDark ? 'rgba(240,240,240,0.95)' : 'rgba(255,255,255,0.9)',  // Light bg for both themes
            bordercolor: isDark ? '#aaa' : '#ddd',
            borderwidth: 1,
            font: { color: '#333' },  // Dark text for contrast on light bg
            // Hide legend if not grouping by constellation
            ...(groupByConstellation ? {} : { visible: false })
        },
        // Adjust margins based on whether legend is shown or custom margins provided
        margin: margin || { l: 50, r: groupByConstellation ? 180 : 50, t: title ? 100 : 50, b: 50 },
        autosize: true  // Enable responsive sizing
    }, {
        responsive: true,
        displayModeBar: true,
        modeBarButtonsToRemove: ['select2d', 'lasso2d'],
        modeBarButtonsToAdd: [homeButton],
        displaylogo: false,
        scrollZoom: enableZoom,
        doubleClick: 'reset'
    }).then(function() {
        // Adjust modebar spacing after plot is created to keep
        // buttons from getting cut off
        setTimeout(function() {
            const plotDiv = document.getElementById(plotElementId);
            const modebar = plotDiv.querySelector('.modebar');

            if (modebar) {
                const buttons = modebar.querySelectorAll('.modebar-btn');

                buttons.forEach(btn => {
                    btn.style.display = 'inline-flex';
                    btn.style.marginRight = '4px';
                    btn.style.setProperty('padding', '2px', 'important');
                });
            }
        }, 100);
    });
}

/**
 * Create a Plotly trace for a constellation
 * @param {Array<Object>} obs - Observation data for this constellation
 * @param {string} constellation - Constellation ID (starlink, kuiper, etc.)
 * @param {string} color - Base color for this constellation
 * @param {boolean} [enableTooltip=true] - Show tooltip on hover
 * @param {boolean} [showColorbar=true] - Show magnitude colorbar
 * @param {number} [markerSize=6] - Marker size in pixels
 * @returns {Object} Plotly trace object
 */
function createTrace(obs, constellation, color, enableTooltip = true, showColorbar = true, markerSize = PLOT_CONFIG.defaultMarkerSize) {
    const C = window.ConstellationConfig;
    const theme = C.getCurrentTheme();
    const isDark = theme === 'dark';
    const textColor = isDark ? '#ccc' : '#666';

    // Calculate magnitude range
    const magnitudes = obs.map(o => o.magnitude);
    const minMag = Math.min(...magnitudes);
    const maxMag = Math.max(...magnitudes);
    const range = maxMag - minMag;

    // Mimic Plotly's automatic tick selection using "nice" intervals
    // This is needed to get the magnitude to show the brighter
    // objects at the top of the colorbar
    const niceIntervals = [0.1, 0.2, 0.25, 0.5, 1, 2, 2.5, 5, 10];
    const targetTicks = 6;
    const roughInterval = range / targetTicks;

    // Find the closest "nice" interval
    let tickInterval = niceIntervals[0];
    for (const interval of niceIntervals) {
        if (interval >= roughInterval) {
            tickInterval = interval;
            break;
        }
        tickInterval = interval;
    }

    // Generate tick values
    const tickVals = [];
    const start = Math.ceil(minMag / tickInterval) * tickInterval;
    for (let tick = start; tick <= maxMag; tick += tickInterval) {
        tickVals.push(Math.round(tick / tickInterval) * tickInterval);
    }

    const trace = {
        type: 'scatterpolar',
        r: obs.map(o => 90 - o.alt_deg_satchecker),
        theta: obs.map(o => o.az_deg_satchecker),
        mode: 'markers',
        name: constellation === 'all' ? 'All Observations' : C.getName(constellation),
        legendgroup: constellation,
        marker: {
            size: markerSize,
            symbol: CONSTELLATION_SYMBOLS[constellation] || 'circle',
            color: obs.map(o => -o.magnitude),  // Negate for reversed colorbar positioning
            colorscale: PLOT_CONFIG.colorscales[theme],
            reversescale: !isDark, // reverse for better visibility in dark mode
            showscale: showColorbar,
            colorbar: {
                title: 'Magnitude',
                titleside: 'right',
                len: 0.6,
                thickness: 15,
                tickfont: { color: textColor, size: 10 },
                titlefont: { color: textColor, size: 11 },
                x: 1.02,
                y: 0.25,
                tickmode: 'array',
                tickvals: tickVals.map(v => -v),  // Negate for positioning
                ticktext: tickVals.map(v => v.toFixed(tickInterval < 1 ? 1 : 0))  // Format based on interval
            },
            opacity: 0.85,
        }
    };

    if (enableTooltip) {
        trace.text = obs.map(o =>
            `<b>${o.satellite || 'Unknown'}</b><br>` +
            `Magnitude: ${o.magnitude?.toFixed(2)} ± ${o.magnitude_uncertainty?.toFixed(2)}<br>` +
            `Altitude: ${o.alt_deg_satchecker?.toFixed(1)}°<br>` +
            `Azimuth: ${o.az_deg_satchecker?.toFixed(1)}°<br>` +
            `Date: ${new Date(o.date).toLocaleString()}`
        );
        trace.hovertemplate = '%{text}<extra></extra>';
    } else {
        trace.hoverinfo = 'none';
    }

    return trace;
}
