/**
 * Data Visualization Landing Page
 * Creates the constellation observation charts: stacked magnitude histogram,
 * all-sky plot, observed brightness vs orbital altitude, and brightness
 * standardized to 1000 km.
 */

let magnitudeChart = null;
let constellationMagnitudeChart = null;
let standardizedMagnitudeChart = null;
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

// ============================================================================
// CONSTELLATION MAGNITUDE CHART
// ============================================================================

function initializeConstellationMagnitude() {
    const canvasElement = document.getElementById('constellation_magnitude');
    const constellationDataElement = document.getElementById('constellation-data');

    if (!constellationDataElement) {
        console.error('Constellation magnitude data element not found');
        return;
    }

    if (!canvasElement) {
        console.error('Constellation magnitude canvas element not found');
        return;
    }

    try {
        const theme = window.ConstellationConfig?.getCurrentTheme() || 'light';
        const isDark = theme === 'dark';
        const constellationData = lastConstellationData
            || JSON.parse(constellationDataElement.textContent.trim());

        // Plot each constellation at its median orbital altitude (x) and mean
        // apparent magnitude (y), with whiskers at ±1 standard deviation.
        // Needs both a mean magnitude and a median altitude to place a point;
        // bubble size conveys sample size.
        const chartData = constellationData.filter(c =>
            c.avg_magnitude != null
            && c.median_altitude_km != null
        );

        if (constellationMagnitudeChart) {
            constellationMagnitudeChart.destroy();
        }

        if (chartData.length === 0) {
            return;
        }

        const pointColors = chartData.map(c =>
            window.ConstellationConfig?.getColor(c.id, theme) || c.color
        );

        // Encode observation count as point area (radius ∝ sqrt(count)).
        const minRadius = 6;
        const maxRadius = 16;
        const counts = chartData.map(c => c.observation_count || 0);
        const maxCount = Math.max(...counts, 1);
        const pointRadii = counts.map(count => {
            const scaled = Math.sqrt(count / maxCount);
            return minRadius + scaled * (maxRadius - minRadius);
        });

        // x-axis range from the altitudes, padded so the largest bubbles are
        // not clipped, then rounded out to multiples of the 200 km tick step so
        // the axis labels land on clean values.
        const altitudes = chartData.map(c => c.median_altitude_km);
        const xTickStep = 200;
        const xMin = Math.floor((Math.min(...altitudes) - 60) / xTickStep) * xTickStep;
        const xMax = Math.ceil((Math.max(...altitudes) + 90) / xTickStep) * xTickStep;

        // Reference thresholds. Fainter = larger magnitude, so y is reversed.
        //  - Aesthetic reference (mag 6): flat naked-eye visibility line.
        //  - Research limit: IAU CPS recommendation, altitude-dependent —
        //    V > 7 up to 550 km, then V > 7 + 2.5*log10(A/550). Drawn as a
        //    continuous curve across the altitude axis. Ref: Boley, Green,
        //    Rawls & Eggl (2025), RNAAS 9, 60 (DOI 10.3847/2515-5172/adc12f).
        const researchLimit = (altitude) =>
            altitude <= 550 ? 7 : 7 + 2.5 * Math.log10(altitude / 550);

        const aestheticStyle = {
            label: 'Aesthetic reference (mag 6)',
            color: isDark ? '#4ade80' : '#16a34a',
            dash: [6, 4]
        };
        const researchCurveStyle = {
            label: 'Research limit (V>7, altitude-adjusted)',
            color: isDark ? '#fb923c' : '#ea580c',
            dash: []
        };

        // Sample the research curve across the x-range (with the 550 km kink).
        const curveAltitudes = [];
        for (let a = Math.floor(xMin); a <= xMax; a += 5) {
            curveAltitudes.push(a);
        }
        if (xMin < 550 && xMax > 550) {
            curveAltitudes.push(550);
            curveAltitudes.sort((p, q) => p - q);
        }
        const researchCurve = curveAltitudes.map(a => ({ x: a, y: researchLimit(a) }));

        // y-range: include whisker extremes (mean ± 1 SD) and both thresholds so
        // nothing clips.
        const yPad = 0.5;
        const whiskerLows = chartData.map(c =>
            c.mag_std != null ? c.avg_magnitude - c.mag_std : c.avg_magnitude
        );
        const whiskerHighs = chartData.map(c =>
            c.mag_std != null ? c.avg_magnitude + c.mag_std : c.avg_magnitude
        );
        const researchAtEdges = altitudes.map(researchLimit);
        const ySuggestedMin =
            Math.min(...whiskerLows, 6, ...researchAtEdges) - yPad;
        const ySuggestedMax =
            Math.max(...whiskerHighs, 6, ...researchAtEdges) + yPad;

        const textColor = isDark ? 'rgba(255, 255, 255, 0.85)' : '#555';
        const gridColor = isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.08)';

        // Whiskers (mean ± 1 SD) drawn ON TOP of the bubbles so they stay
        // visible even when a large-sample bubble (e.g. Starlink) is wider than
        // a tight spread. A contrasting halo (chart background color) keeps the
        // colored whisker legible against a same-colored bubble. Constellations
        // are identified by the color-coded legend, not on-chart labels.
        const haloColor = isDark ? '#212529' : '#fff';
        const whiskerPlugin = {
            id: 'constellationWhiskers',
            afterDatasetsDraw(chart) {
                const { ctx, scales: { x, y } } = chart;
                const cap = 5;
                ctx.save();
                ctx.lineCap = 'round';
                chartData.forEach((constellation, i) => {
                    if (constellation.mag_std == null) {
                        return;
                    }
                    const px = x.getPixelForValue(constellation.median_altitude_km);
                    const yLow = y.getPixelForValue(
                        constellation.avg_magnitude - constellation.mag_std
                    );
                    const yHigh = y.getPixelForValue(
                        constellation.avg_magnitude + constellation.mag_std
                    );
                    ctx.beginPath();
                    ctx.moveTo(px, yLow);
                    ctx.lineTo(px, yHigh);
                    ctx.moveTo(px - cap, yLow);
                    ctx.lineTo(px + cap, yLow);
                    ctx.moveTo(px - cap, yHigh);
                    ctx.lineTo(px + cap, yHigh);
                    // Contrast halo first, then the colored whisker on top.
                    ctx.strokeStyle = haloColor;
                    ctx.lineWidth = 3.5;
                    ctx.stroke();
                    ctx.strokeStyle = pointColors[i];
                    ctx.lineWidth = 1.5;
                    ctx.stroke();
                });
                ctx.restore();
            }
        };

        constellationMagnitudeChart = new Chart(canvasElement.getContext('2d'), {
            type: 'scatter',
            plugins: [whiskerPlugin],
            data: {
                datasets: [
                    {
                        label: aestheticStyle.label,
                        type: 'line',
                        data: [{ x: xMin, y: 6 }, { x: xMax, y: 6 }],
                        borderColor: aestheticStyle.color,
                        borderWidth: 2,
                        borderDash: aestheticStyle.dash,
                        pointRadius: 0,
                        fill: false
                    },
                    {
                        label: researchCurveStyle.label,
                        type: 'line',
                        data: researchCurve,
                        borderColor: researchCurveStyle.color,
                        borderWidth: 2,
                        pointRadius: 0,
                        fill: false,
                        tension: 0
                    },
                    {
                        label: 'Constellation mean',
                        data: chartData.map(c => ({
                            x: c.median_altitude_km,
                            y: c.avg_magnitude
                        })),
                        pointRadius: pointRadii,
                        pointHoverRadius: pointRadii.map(r => r + 2),
                        pointBackgroundColor: pointColors,
                        pointBorderColor: isDark ? '#212529' : '#fff',
                        pointBorderWidth: 1.5
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'bottom',
                        // Legend entries map to no toggleable dataset index.
                        onClick: () => {},
                        labels: {
                            usePointStyle: true,
                            boxHeight: 7,
                            // color-coded constellation swatches followed by the
                            // two reference lines. Constellation text uses a
                            // theme-readable color (the swatch carries the hue);
                            // reference-line text matches its line color. Per-item
                            // fontColor is required — labels.color is ignored when
                            // generateLabels is supplied.
                            generateLabels: () => [
                                ...chartData.map((c, i) => ({
                                    text: c.name,
                                    pointStyle: 'circle',
                                    fillStyle: pointColors[i],
                                    strokeStyle: pointColors[i],
                                    fontColor: textColor,
                                    lineWidth: 0
                                })),
                                ...[aestheticStyle, researchCurveStyle].map((ref) => ({
                                    text: ref.label,
                                    pointStyle: 'line',
                                    strokeStyle: ref.color,
                                    fillStyle: ref.color,
                                    fontColor: ref.color,
                                    lineWidth: 2,
                                    lineDash: ref.dash
                                }))
                            ]
                        }
                    },
                    tooltip: {
                        // Only the bubble dataset (index 2) drives tooltips; the
                        // reference line/curve points must not be picked, or a
                        // bubble near a line would be titled by the wrong index.
                        mode: 'point',
                        intersect: true,
                        filter: (item) => item.datasetIndex === 2,
                        callbacks: {
                            title: (items) => {
                                const c = chartData[items[0].dataIndex];
                                return c ? c.name : '';
                            },
                            label: (context) => {
                                const c = chartData[context.dataIndex];
                                const obs = (c.observation_count || 0).toLocaleString();
                                return `Mean ${c.avg_magnitude.toFixed(2)} mag `
                                    + `@ ${c.median_altitude_km} km • ${obs} obs`;
                            },
                            afterLabel: (context) => {
                                const c = chartData[context.dataIndex];
                                if (c.mag_std == null) {
                                    return undefined;
                                }
                                return `±1 SD: ${c.mag_std.toFixed(2)} mag`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        type: 'linear',
                        min: xMin,
                        max: xMax,
                        title: {
                            display: true,
                            text: 'Orbital altitude (km)',
                            color: textColor
                        },
                        ticks: { color: textColor, stepSize: xTickStep },
                        grid: { color: gridColor }
                    },
                    y: {
                        reverse: true,
                        suggestedMin: ySuggestedMin,
                        suggestedMax: ySuggestedMax,
                        title: {
                            display: true,
                            text: 'Apparent Magnitude',
                            color: textColor
                        },
                        ticks: { color: textColor },
                        grid: { color: gridColor }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error creating constellation magnitude chart:', error);
    }
}

// ============================================================================
// STANDARDIZED (1000 km) MAGNITUDE CHART
// ============================================================================

/**
 * Companion to the altitude chart: each constellation's brightness standardized
 * to a common 1000 km distance (removing the distance effect), ranked brightest
 * to faintest on a categorical x-axis. No visibility-limit lines — those apply
 * to apparent magnitude and live on the altitude chart. The standardized values
 * are computed in the backend (see distance_corrected_mag in general_utils).
 */
function initializeStandardizedMagnitude() {
    const canvasElement = document.getElementById('standardized_magnitude');
    const constellationDataElement = document.getElementById('constellation-data');

    if (!constellationDataElement) {
        console.error('Standardized magnitude data element not found');
        return;
    }

    if (!canvasElement) {
        console.error('Standardized magnitude canvas element not found');
        return;
    }

    try {
        const theme = window.ConstellationConfig?.getCurrentTheme() || 'light';
        const isDark = theme === 'dark';
        const constellationData = lastConstellationData
            || JSON.parse(constellationDataElement.textContent.trim());

        // Distance-corrected (1000 km) magnitudes computed in the backend
        // (see distance_corrected_mag): mean with ±1 SD whiskers, ranked
        // brightest -> faintest.
        const chartData = constellationData
            .filter(c => c.abs_mean_magnitude != null)
            .map(c => ({
                id: c.id,
                name: c.name,
                observation_count: c.observation_count,
                sMean: c.abs_mean_magnitude,
                sStd: c.abs_std_magnitude,
                sLow: c.abs_std_magnitude != null
                    ? c.abs_mean_magnitude - c.abs_std_magnitude : null,
                sHigh: c.abs_std_magnitude != null
                    ? c.abs_mean_magnitude + c.abs_std_magnitude : null
            }))
            .sort((a, b) => a.sMean - b.sMean);

        if (standardizedMagnitudeChart) {
            standardizedMagnitudeChart.destroy();
        }

        if (chartData.length === 0) {
            return;
        }

        const pointColors = chartData.map(c =>
            window.ConstellationConfig?.getColor(c.id, theme) || c.color
        );

        // Bubble radius ∝ sqrt(observation count), matching the altitude chart.
        const minRadius = 6;
        const maxRadius = 16;
        const counts = chartData.map(c => c.observation_count || 0);
        const maxCount = Math.max(...counts, 1);
        const pointRadii = counts.map(count =>
            minRadius + Math.sqrt(count / maxCount) * (maxRadius - minRadius)
        );

        const yPad = 0.5;
        const yLows = chartData.map(c => c.sLow != null ? c.sLow : c.sMean);
        const yHighs = chartData.map(c => c.sHigh != null ? c.sHigh : c.sMean);
        const ySuggestedMin = Math.min(...yLows) - yPad;
        const ySuggestedMax = Math.max(...yHighs) + yPad;

        const textColor = isDark ? 'rgba(255, 255, 255, 0.85)' : '#555';
        const gridColor = isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.08)';
        const haloColor = isDark ? '#212529' : '#fff';

        // Whiskers on top so they stay visible against large bubbles.
        const whiskerPlugin = {
            id: 'standardizedWhiskers',
            afterDatasetsDraw(chart) {
                const { ctx, scales: { y } } = chart;
                const meta = chart.getDatasetMeta(0);
                ctx.save();
                ctx.lineCap = 'round';
                chartData.forEach((c, i) => {
                    if (c.sLow == null || c.sHigh == null) {
                        return;
                    }
                    const element = meta.data[i];
                    if (!element) {
                        return;
                    }
                    const px = element.x;
                    const yLow = y.getPixelForValue(c.sLow);
                    const yHigh = y.getPixelForValue(c.sHigh);
                    ctx.beginPath();
                    ctx.moveTo(px, yLow);
                    ctx.lineTo(px, yHigh);
                    ctx.moveTo(px - 5, yLow);
                    ctx.lineTo(px + 5, yLow);
                    ctx.moveTo(px - 5, yHigh);
                    ctx.lineTo(px + 5, yHigh);
                    ctx.strokeStyle = haloColor;
                    ctx.lineWidth = 3.5;
                    ctx.stroke();
                    ctx.strokeStyle = pointColors[i];
                    ctx.lineWidth = 1.5;
                    ctx.stroke();
                });
                ctx.restore();
            }
        };

        standardizedMagnitudeChart = new Chart(canvasElement.getContext('2d'), {
            type: 'line',
            plugins: [whiskerPlugin],
            data: {
                labels: chartData.map(c => c.name),
                datasets: [{
                    data: chartData.map(c => c.sMean),
                    showLine: false,
                    pointStyle: 'circle',
                    pointRadius: pointRadii,
                    pointHoverRadius: pointRadii.map(r => r + 2),
                    pointBackgroundColor: pointColors,
                    pointBorderColor: isDark ? '#212529' : '#fff',
                    pointBorderWidth: 1.5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    // Constellations are named on the x-axis; no legend needed.
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            title: (items) => {
                                const c = chartData[items[0].dataIndex];
                                return c ? c.name : '';
                            },
                            label: (context) => {
                                const c = chartData[context.dataIndex];
                                const obs = (c.observation_count || 0).toLocaleString();
                                const sd = c.sStd != null
                                    ? ` ± ${c.sStd.toFixed(2)}` : '';
                                return `Standardized ${c.sMean.toFixed(2)}${sd} mag `
                                    + `@ 1000 km • ${obs} obs`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Constellation (brightest → faintest)',
                            color: textColor
                        },
                        ticks: { color: textColor },
                        grid: { color: gridColor }
                    },
                    y: {
                        reverse: true,
                        suggestedMin: ySuggestedMin,
                        suggestedMax: ySuggestedMax,
                        title: {
                            display: true,
                            text: 'Standardized Magnitude (@ 1000 km)',
                            color: textColor
                        },
                        ticks: { color: textColor },
                        grid: { color: gridColor }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error creating standardized magnitude chart:', error);
    }
}

/**
 * Initialize all charts on the data visualization page
 */
function initializeDataVisualization() {
    initializeMagnitudeHistogram();
    initializeAllSkyPlot();
    initializeConstellationMagnitude();
    initializeStandardizedMagnitude();
    updateStatBoxColors();
}

document.addEventListener('DOMContentLoaded', initializeDataVisualization);

// Subscribe to theme changes to update all charts and stat box colors
if (window.ThemeManager) {
    ThemeManager.subscribe((theme) => {
        console.log('Theme changed to:', theme);
        updateMagnitudeHistogramForTheme();
        initializeConstellationMagnitude();
        initializeStandardizedMagnitude();
        updateStatBoxColors();
    });
}

// Cleanup on page unload to prevent memory leaks
window.addEventListener('beforeunload', function() {
    if (magnitudeChart) {
        magnitudeChart.destroy();
        magnitudeChart = null;
    }
    if (constellationMagnitudeChart) {
        constellationMagnitudeChart.destroy();
        constellationMagnitudeChart = null;
    }
    if (standardizedMagnitudeChart) {
        standardizedMagnitudeChart.destroy();
        standardizedMagnitudeChart = null;
    }
});
