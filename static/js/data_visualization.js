/**
 * Data Visualization Landing Page
 * Creates stacked magnitude histogram and all-sky plot for constellation observation data
 */

let magnitudeChart = null;
let lastConstellationData = null;
let lastMagnitudeBins = null;

// ============================================================================
// HISTOGRAM FUNCTIONS
// ============================================================================

/**
 * Create magnitude distribution histogram using Chart.js
 * @param {HTMLElement} canvasElement - Canvas element for the chart
 * @param {Array<Object>} constellationData - Constellation metadata
 * @param {Object} magnitudeBins - Binned magnitude data
 * @returns {Chart|null} Chart instance or null on error
 */
function createMagnitudeHistogram(canvasElement, constellationData, magnitudeBins) {
    try {
        // Extract bin labels (magnitude values)
        const binLabels = Object.keys(magnitudeBins).sort((a, b) => Number(b) - Number(a));

        // Get current theme for color selection
        const theme = window.ConstellationConfig?.getCurrentTheme() || 'light';

        // Create datasets for each constellation
        const datasets = constellationData.map(constellation => {
            const data = binLabels.map(bin => magnitudeBins[bin][constellation.id] || 0);
            const color = window.ConstellationConfig?.getColor(constellation.id, theme) || constellation.color;
            return {
                label: constellation.name,
                data: data,
                backgroundColor: color,
                borderColor: color,
                borderWidth: 1
            };
        });

        // Create stacked histogram
        const ctx = canvasElement.getContext('2d');
        return new Chart(ctx, {
            type: 'bar',
            data: {
                labels: binLabels,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            boxWidth: 12,
                            padding: 10,
                            font: { size: 11 }
                        }
                    },
                    tooltip: {
                        mode: 'index',
                        callbacks: {
                            footer: function(tooltipItems) {
                                const sum = tooltipItems.reduce((acc, item) => acc + item.parsed.y, 0);
                                return 'Total: ' + sum.toLocaleString();
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        stacked: true,
                        title: {
                            display: true,
                            text: 'Apparent Magnitude Bins'
                        }
                    },
                    y: {
                        stacked: true,
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Count'
                        },
                        ticks: {
                            callback: function(value) {
                                return value.toLocaleString();
                            }
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error creating magnitude histogram:', error);
        return null;
    }
}

/**
 * Initialize magnitude histogram from DOM data elements
 */
function initializeMagnitudeHistogram() {
    const constellationDataElement = document.getElementById('constellation-data');
    const magnitudeBinsElement = document.getElementById('magnitude-bins-data');
    const canvasElement = document.getElementById('magnitude_distribution');

    if (!constellationDataElement || !magnitudeBinsElement) {
        console.error('Magnitude histogram data elements not found');
        return;
    }

    if (!canvasElement) {
        console.error('Magnitude histogram canvas element not found');
        return;
    }

    try {
        lastConstellationData = JSON.parse(constellationDataElement.textContent.trim());
        lastMagnitudeBins = JSON.parse(magnitudeBinsElement.textContent.trim());

        magnitudeChart = createMagnitudeHistogram(canvasElement, lastConstellationData, lastMagnitudeBins);

        if (magnitudeChart) {
            console.log('Magnitude histogram created successfully');
        }
    } catch (error) {
        console.error('Error parsing magnitude histogram data:', error);
    }
}

/**
 * Update magnitude histogram when theme changes
 */
function updateMagnitudeHistogramForTheme() {
    const canvasElement = document.getElementById('magnitude_distribution');

    if (!canvasElement || !lastConstellationData || !lastMagnitudeBins) {
        return;
    }

    if (magnitudeChart) {
        magnitudeChart.destroy();
    }

    magnitudeChart = createMagnitudeHistogram(canvasElement, lastConstellationData, lastMagnitudeBins);
    console.log('Magnitude histogram updated for theme change');
}

/**
 * Update constellation stat box borders when theme changes
 */
function updateStatBoxColors() {
    const statBoxes = document.querySelectorAll('.constellation-stat-box');
    const theme = window.ConstellationConfig?.getCurrentTheme() || 'light';

    statBoxes.forEach(box => {
        const constellationId = box.getAttribute('data-constellation-id');
        if (constellationId) {
            const color = window.ConstellationConfig?.getColor(constellationId, theme);
            if (color) {
                box.style.borderLeftColor = color;
            }
        }
    });
}

// ============================================================================
// ALL-SKY PLOT FUNCTIONS
// ============================================================================

/**
 * Initialize all-sky plot from DOM data element
 * Uses Plotly via satellite_plots.js
 */
function initializeAllSkyPlot() {
    const allObservationsElement = document.getElementById('observations-data');

    if (!allObservationsElement) {
        console.warn('All-sky plot data element not found (optional)');
        return;
    }

    try {
        const allObservations = JSON.parse(allObservationsElement.textContent.trim());

        if (!allObservations || allObservations.length === 0) {
            console.warn('No observation data available for all-sky plot');
            return;
        }

        // Create plot using satellite_plots.js function
        createAllSkyPlot(allObservations, {
            enableTooltip: false,
            enableZoom: false,
            groupByConstellation: false,
            plotElementId: 'allsky-plot',
            title: '',
            markerSize: 3,
            margin: { l: 20, r: 20, t: 20, b: 20 }
        });

        console.log('All-sky plot created successfully');
    } catch (error) {
        console.error('Error creating all-sky plot:', error);
    }
}

/**
 * Initialize all charts on the data visualization page
 */
function initializeDataVisualization() {
    initializeMagnitudeHistogram();
    initializeAllSkyPlot();
    updateStatBoxColors();
}

document.addEventListener('DOMContentLoaded', initializeDataVisualization);

// Subscribe to theme changes to update histogram and stat box colors
if (window.ThemeManager) {
    ThemeManager.subscribe((theme) => {
        console.log('Theme changed to:', theme);
        updateMagnitudeHistogramForTheme();
        updateStatBoxColors();
    });
}

// Cleanup on page unload to prevent memory leaks
window.addEventListener('beforeunload', function() {
    if (magnitudeChart) {
        magnitudeChart.destroy();
        magnitudeChart = null;
    }
});
