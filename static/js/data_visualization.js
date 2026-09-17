/**
 * Data Visualization Landing Page
 * Creates the constellation observation charts: stacked magnitude histogram,
 * all-sky plot, observed brightness vs orbital altitude, and brightness
 * standardized to 1000 km.
 */

let magnitudeChart = null;
let constellationMagnitudeUniformChart = null;
let constellationMagnitudeScaledChart = null;
let standardizedMagnitudeChart = null;
let lastConstellationData = null;
let lastAltitudeData = null;
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
// OBSERVED BRIGHTNESS VS ORBITAL ALTITUDE CHART(S)
// ============================================================================

// Starlink generations share the Starlink color; every other row uses its own.
function constellationColor(id, theme) {
    const key = id.startsWith('starlink') ? 'starlink' : id;
    return window.ConstellationConfig?.getColor(key, theme) || '#888888';
}

// Theme-aware colors/labels for the two reference lines.
function altitudeReferenceStyles(isDark) {
    return {
        aesthetic: {
            label: 'Visual eye limit (mag 6)',
            color: isDark ? '#4ade80' : '#16a34a',
            dash: [6, 4]
        },
        research: {
            label: 'IAU maximum brightness recommendation',
            color: isDark ? '#fb923c' : '#ea580c',
            dash: []
        }
    };
}

// IAU CPS recommendation: V > 7 up to 550 km, then V > 7 + 2.5*log10(A/550).
// Ref: Boley, Green, Rawls & Eggl (2025), RNAAS 9, 60 (DOI 10.3847/2515-5172/adc12f).
function altitudeResearchLimit(altitude) {
    return altitude <= 550 ? 7 : 7 + 2.5 * Math.log10(altitude / 550);
}

/**
 * Build one brightness-vs-altitude scatter for the given canvas.
 * @param {string} canvasId - target canvas element id
 * @param {Array<Object>} chartData - altitude rows (Starlink split by generation)
 * @param {string} theme - 'light' | 'dark'
 * @param {boolean} uniform - true: fixed marker size; false: size proportional to sqrt(obs)
 * @returns {Chart|null}
 */
function makeAltitudeChart(canvasId, chartData, theme, uniform) {
    const canvasElement = document.getElementById(canvasId);
    if (!canvasElement) {
        console.error('Altitude canvas not found:', canvasId);
        return null;
    }
    const isDark = theme === 'dark';
    const pointColors = chartData.map(c => constellationColor(c.id, theme));
    const pointFill = pointColors.map(c => c + 'B3'); // 0.7 opacity fill

    // Marker radius: uniform, or proportional to sqrt(observation count).
    let pointRadii;
    if (uniform) {
        pointRadii = chartData.map(() => 7.5);
    } else {
        const minRadius = 6;
        const maxRadius = 16;
        const counts = chartData.map(c => c.observation_count || 0);
        const maxCount = Math.max(...counts, 1);
        pointRadii = counts.map(count =>
            minRadius + Math.sqrt(count / maxCount) * (maxRadius - minRadius)
        );
    }

    const altitudes = chartData.map(c => c.median_altitude_km);
    const xTickStep = 200;
    const xMin = Math.floor((Math.min(...altitudes) - 60) / xTickStep) * xTickStep;
    const xMax = Math.ceil((Math.max(...altitudes) + 90) / xTickStep) * xTickStep;

    const ref = altitudeReferenceStyles(isDark);

    // Sample the research curve across the x-range (with the 550 km adjustment).
    const curveAltitudes = [];
    for (let a = Math.floor(xMin); a <= xMax; a += 5) {
        curveAltitudes.push(a);
    }
    if (xMin < 550 && xMax > 550) {
        curveAltitudes.push(550);
        curveAltitudes.sort((p, q) => p - q);
    }
    const researchCurve = curveAltitudes.map(a => ({ x: a, y: altitudeResearchLimit(a) }));

    // y-range: include whisker extremes (mean ± 1 SD) and both thresholds.
    const yPad = 0.5;
    const whiskerLows = chartData.map(c =>
        c.mag_std != null ? c.avg_magnitude - c.mag_std : c.avg_magnitude
    );
    const whiskerHighs = chartData.map(c =>
        c.mag_std != null ? c.avg_magnitude + c.mag_std : c.avg_magnitude
    );
    const researchAtEdges = altitudes.map(altitudeResearchLimit);
    const ySuggestedMin = Math.min(...whiskerLows, 6, ...researchAtEdges) - yPad;
    const ySuggestedMax = Math.max(...whiskerHighs, 6, ...researchAtEdges) + yPad;

    const textColor = isDark ? 'rgba(255, 255, 255, 0.85)' : '#555';
    const gridColor = isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.08)';
    const haloColor = isDark ? '#212529' : '#fff';

    // Whiskers (mean ± 1 SD) drawn BEHIND the points (beforeDatasetsDraw) so the
    // markers sit on top of their error bars. A contrast halo keeps them legible.
    const whiskerPlugin = {
        id: 'altitudeWhiskers',
        beforeDatasetsDraw(chart) {
            const { ctx, scales: { x, y } } = chart;
            const cap = 5;
            ctx.save();
            ctx.lineCap = 'round';
            chartData.forEach((c, i) => {
                if (c.mag_std == null) {
                    return;
                }
                const px = x.getPixelForValue(c.median_altitude_km);
                const yLow = y.getPixelForValue(c.avg_magnitude - c.mag_std);
                const yHigh = y.getPixelForValue(c.avg_magnitude + c.mag_std);
                ctx.beginPath();
                ctx.moveTo(px, yLow);
                ctx.lineTo(px, yHigh);
                ctx.moveTo(px - cap, yLow);
                ctx.lineTo(px + cap, yLow);
                ctx.moveTo(px - cap, yHigh);
                ctx.lineTo(px + cap, yHigh);
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

    // Starlink generation labels next to each Starlink point (they share a color).
    const genLabelPlugin = {
        id: 'altitudeGenLabels',
        afterDatasetsDraw(chart) {
            const { ctx, scales: { x, y } } = chart;
            ctx.save();
            ctx.font = 'bold 12px Arial';
            ctx.textBaseline = 'middle';
            ctx.textAlign = 'left';
            const starlinkColor = constellationColor('starlink', theme);
            chartData.forEach((c, i) => {
                if (!c.id.startsWith('starlink')) {
                    return;
                }
                const label = c.name.replace('Starlink ', '');
                const px = x.getPixelForValue(c.median_altitude_km) + pointRadii[i] + 4;
                const py = y.getPixelForValue(c.avg_magnitude);
                ctx.lineWidth = 3;
                ctx.strokeStyle = haloColor;
                ctx.strokeText(label, px, py);
                ctx.fillStyle = starlinkColor;
                ctx.fillText(label, px, py);
            });
            ctx.restore();
        }
    };

    return new Chart(canvasElement.getContext('2d'), {
        type: 'scatter',
        plugins: [whiskerPlugin, genLabelPlugin],
        data: {
            datasets: [
                {
                    label: ref.aesthetic.label,
                    type: 'line',
                    data: [{ x: xMin, y: 6 }, { x: xMax, y: 6 }],
                    borderColor: ref.aesthetic.color,
                    borderWidth: 2,
                    borderDash: ref.aesthetic.dash,
                    pointRadius: 0,
                    fill: false
                },
                {
                    label: ref.research.label,
                    type: 'line',
                    data: researchCurve,
                    borderColor: ref.research.color,
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
                    pointBackgroundColor: pointFill,
                    pointBorderColor: haloColor,
                    pointBorderWidth: 1.5
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                // Identity is shown by the shared HTML legend (#altitude-legend).
                legend: { display: false },
                tooltip: {
                    // Only the bubble dataset (index 2) drives tooltips.
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
                    title: { display: true, text: 'Orbital altitude (km)', color: textColor },
                    ticks: { color: textColor, stepSize: xTickStep },
                    grid: { color: gridColor }
                },
                y: {
                    reverse: true,
                    suggestedMin: ySuggestedMin,
                    suggestedMax: ySuggestedMax,
                    title: { display: true, text: 'Apparent Magnitude', color: textColor },
                    ticks: { color: textColor },
                    grid: { color: gridColor }
                }
            }
        }
    });
}

/**
 * Collapse altitude rows into one entry per constellation (Starlink generations
 * merged), summing satellite and observation counts. Shared by the on-screen
 * legend (which uses name/color) and the download counts panel (which also uses
 * the summed sats/obs).
 * @returns {Array<{name: string, color: string, sats: number, obs: number}>}
 */
function collapseAltitudeFamilies(chartData, theme) {
    const families = new Map();
    chartData.forEach(c => {
        const fam = c.id.startsWith('starlink') ? 'starlink' : c.id;
        if (!families.has(fam)) {
            families.set(fam, {
                name: fam === 'starlink' ? 'Starlink' : c.name,
                color: constellationColor(c.id, theme),
                sats: 0,
                obs: 0
            });
        }
        const f = families.get(fam);
        f.sats += c.satellite_count || 0;
        f.obs += c.observation_count || 0;
    });
    return [...families.values()];
}

/**
 * Shared HTML legend for the two altitude charts: constellation names (Starlink
 * generations collapsed into one entry) on one row, reference lines on their own.
 * Per-constellation satellite/observation counts are intentionally NOT shown here
 * — those appear only in the downloaded image (see compositeAndDownload).
 */
function buildAltitudeLegend(chartData, theme) {
    const el = document.getElementById('altitude-legend');
    if (!el) {
        return;
    }
    const isDark = theme === 'dark';
    const textColor = isDark ? 'rgba(255, 255, 255, 0.85)' : '#555';
    const ref = altitudeReferenceStyles(isDark);
    el.innerHTML = '';
    el.style.color = textColor;

    const families = collapseAltitudeFamilies(chartData, theme);

    const row1 = document.createElement('div');
    row1.className = 'viz-legend-row';
    families.forEach(f => {
        const item = document.createElement('span');
        item.className = 'viz-legend-item';
        item.innerHTML =
            `<span class="viz-legend-dot" style="background:${f.color}"></span>${f.name}`;
        row1.appendChild(item);
    });

    const row2 = document.createElement('div');
    row2.className = 'viz-legend-row';
    [ref.aesthetic, ref.research].forEach(r => {
        const item = document.createElement('span');
        item.className = 'viz-legend-item';
        const dash = r.dash && r.dash.length ? ' dashed' : '';
        item.innerHTML =
            `<span class="viz-legend-line${dash}" style="border-color:${r.color}"></span>${r.label}`;
        row2.appendChild(item);
    });

    el.appendChild(row1);
    el.appendChild(row2);
}

/** Read the altitude dataset, build the shared legend, and render both charts. */
function initializeAltitudeCharts() {
    const dataElement = document.getElementById('altitude-data');
    if (!dataElement) {
        console.error('Altitude data element not found');
        return;
    }
    try {
        const theme = window.ConstellationConfig?.getCurrentTheme() || 'light';
        lastAltitudeData = JSON.parse(dataElement.textContent.trim());
        const chartData = lastAltitudeData.filter(c =>
            c.avg_magnitude != null && c.median_altitude_km != null
        );

        if (constellationMagnitudeUniformChart) {
            constellationMagnitudeUniformChart.destroy();
            constellationMagnitudeUniformChart = null;
        }
        if (constellationMagnitudeScaledChart) {
            constellationMagnitudeScaledChart.destroy();
            constellationMagnitudeScaledChart = null;
        }
        if (chartData.length === 0) {
            return;
        }

        buildAltitudeLegend(chartData, theme);
        constellationMagnitudeUniformChart =
            makeAltitudeChart('constellation_magnitude_uniform', chartData, theme, true);
        constellationMagnitudeScaledChart =
            makeAltitudeChart('constellation_magnitude_scaled', chartData, theme, false);
    } catch (error) {
        console.error('Error creating altitude charts:', error);
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

// ============================================================================
// CHART DOWNLOAD (PNG/JPG with citation footer)
// ============================================================================

const CHART_CITATION_SOURCE =
    'Source: SCORE — Satellite Constellation Observation Repository, IAU CPS.';
const CHART_PLOTS_URL = 'https://score.cps.iau.org/visualization';

/** Citation line stamped into the footer of every downloaded chart image. */
function buildChartCitation() {
    const date = new Date().toISOString().slice(0, 10);
    return `${CHART_CITATION_SOURCE} Retrieved ${date}.`;
}

/** Largest font size (down to 10px) at which text fits within maxWidth. */
function fitCitationFontSize(text, maxWidth, startSize) {
    const probe = document.createElement('canvas').getContext('2d');
    let size = startSize;
    probe.font = `${size}px Arial, sans-serif`;
    while (size > 10 && probe.measureText(text).width > maxWidth) {
        size -= 1;
        probe.font = `${size}px Arial, sans-serif`;
    }
    return size;
}

/**
 * Composite a rendered chart onto a theme-matched background with a citation
 * footer, then trigger a download. Background and text follow the current theme
 * so the export matches what is on screen (and dark-mode chart text stays
 * legible instead of vanishing on a forced-white background).
 * @param {HTMLCanvasElement|HTMLImageElement} source - rendered chart
 * @param {Object} opts - { format: 'png'|'jpeg', filename }
 */
function compositeAndDownload(source, { format, filename, counts }) {
    const width = source.width;
    const height = source.height;
    if (!width || !height) {
        console.error('Chart image not ready for download:', filename);
        return;
    }

    const isDark = (window.ConstellationConfig?.getCurrentTheme() || 'light') === 'dark';
    const bgColor = isDark ? '#212529' : '#ffffff';
    const textColor = isDark ? 'rgba(255, 255, 255, 0.75)' : '#555555';
    const strongText = isDark ? 'rgba(255, 255, 255, 0.9)' : '#333333';
    const linkColor = isDark ? '#6ea8fe' : '#0d6efd';
    const separatorColor = isDark ? 'rgba(255, 255, 255, 0.15)' : '#dddddd';

    // Two-line footer: citation on the first line, link to the plots page on
    // the second. Font is sized to the wider of the two lines so both fit.
    const citation = buildChartCitation();
    const sidePad = Math.round(width * 0.02);
    const maxTextWidth = width - sidePad * 2;
    const baseSize = Math.max(12, Math.round(width * 0.016));
    const fontSize = Math.min(
        fitCitationFontSize(citation, maxTextWidth, baseSize),
        fitCitationFontSize(CHART_PLOTS_URL, maxTextWidth, baseSize)
    );
    const topPad = Math.round(fontSize * 0.8);
    const lineGap = Math.round(fontSize * 0.45);
    const footerHeight = topPad * 2 + fontSize * 2 + lineGap;

    // Optional per-constellation counts panel — download only, two columns.
    const hasCounts = Array.isArray(counts) && counts.length > 0;
    const rowHeight = Math.round(fontSize * 1.7);
    const countRows = hasCounts ? Math.ceil(counts.length / 2) : 0;
    const panelHeight = hasCounts
        ? Math.round(fontSize * 1.3) + rowHeight + countRows * rowHeight + Math.round(fontSize * 0.6)
        : 0;

    const out = document.createElement('canvas');
    out.width = width;
    out.height = height + panelHeight + footerHeight;
    const ctx = out.getContext('2d');

    ctx.fillStyle = bgColor;
    ctx.fillRect(0, 0, out.width, out.height);
    ctx.drawImage(source, 0, 0, width, height);
    ctx.textAlign = 'left';
    ctx.textBaseline = 'middle';

    if (hasCounts) {
        const colWidth = (width - 2 * sidePad) / 2;
        const dot = Math.round(fontSize * 0.75);
        let panelY = height + Math.round(fontSize * 1.3);
        ctx.font = `bold ${fontSize}px Arial, sans-serif`;
        ctx.fillStyle = strongText;
        ctx.fillText('Per-constellation totals', sidePad, panelY);
        panelY += rowHeight;
        ctx.font = `${fontSize}px Arial, sans-serif`;
        counts.forEach((c, i) => {
            const cx = sidePad + (i % 2) * colWidth;
            const cy = panelY + Math.floor(i / 2) * rowHeight;
            ctx.fillStyle = c.color;
            ctx.beginPath();
            ctx.arc(cx + dot / 2, cy, dot / 2, 0, Math.PI * 2);
            ctx.fill();
            ctx.fillStyle = strongText;
            const satLabel = `${c.sats} sat${c.sats === 1 ? '' : 's'}`;
            const obsLabel = `${(c.obs || 0).toLocaleString()} obs`;
            ctx.fillText(`${c.name} — ${satLabel} · ${obsLabel}`, cx + dot + 8, cy);
        });
    }

    const footerTop = height + panelHeight;
    ctx.strokeStyle = separatorColor;
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, footerTop + 0.5);
    ctx.lineTo(width, footerTop + 0.5);
    ctx.stroke();

    ctx.font = `${fontSize}px Arial, sans-serif`;
    ctx.fillStyle = textColor;
    ctx.fillText(citation, sidePad, footerTop + topPad + fontSize / 2);
    ctx.fillStyle = linkColor;
    ctx.fillText(
        CHART_PLOTS_URL,
        sidePad,
        footerTop + topPad + fontSize + lineGap + fontSize / 2
    );

    const isJpeg = format === 'jpeg';
    const dataUrl = out.toDataURL(
        isJpeg ? 'image/jpeg' : 'image/png', isJpeg ? 0.92 : undefined
    );

    const link = document.createElement('a');
    link.href = dataUrl;
    link.download = `${filename}.${isJpeg ? 'jpg' : 'png'}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

/** Export a Chart.js chart (its live canvas already includes plugin drawing). */
function downloadChartJs(chart, filename, format, counts) {
    if (!chart) {
        console.error('Chart not ready for download:', filename);
        return;
    }
    // Clear any active hover/tooltip so it isn't baked into the exported image.
    // Force a synchronous redraw (chart.draw) — chart.update() schedules the
    // repaint via requestAnimationFrame, so the canvas would still show the
    // tooltip when we read it immediately afterward.
    chart.setActiveElements([]);
    if (chart.tooltip) {
        chart.tooltip.setActiveElements([], { x: 0, y: 0 });
        chart.tooltip.opacity = 0;
    }
    chart.draw();
    compositeAndDownload(chart.canvas, { format, filename, counts });
}

/**
 * Per-constellation counts for the altitude-chart download panel (Starlink
 * generations collapsed). Returns null if the altitude data isn't loaded.
 */
function altitudeDownloadCounts() {
    if (!lastAltitudeData) {
        return null;
    }
    const theme = window.ConstellationConfig?.getCurrentTheme() || 'light';
    const chartData = lastAltitudeData.filter(c =>
        c.avg_magnitude != null && c.median_altitude_km != null
    );
    return collapseAltitudeFamilies(chartData, theme);
}

/**
 * Export the Plotly all-sky plot. Plotly renders to its own SVG/canvas, so ask
 * it for a PNG first, then run that image through the shared compositor to get
 * the citation footer (and the requested output format).
 */
function downloadAllSkyImage(format) {
    const plotElement = document.getElementById('allsky-plot');
    if (!plotElement || !window.Plotly) {
        console.error('All-sky plot not available for download');
        return;
    }
    const width = plotElement.offsetWidth || 700;
    const height = plotElement.offsetHeight || 350;
    window.Plotly.toImage(plotElement, { format: 'png', width, height, scale: 2 })
        .then((dataUrl) => {
            const img = new Image();
            img.onload = () => compositeAndDownload(img, {
                format, filename: 'score_all_observations'
            });
            img.onerror = () => console.error('Failed to render all-sky image for download');
            img.src = dataUrl;
        })
        .catch((error) => console.error('Error exporting all-sky plot:', error));
}

/** Route a download request (keyed by the chart's element id) to its exporter. */
function handleChartDownload(chartKey, format) {
    switch (chartKey) {
        case 'magnitude_distribution':
            downloadChartJs(magnitudeChart, 'score_magnitude_distribution', format);
            break;
        case 'constellation_magnitude_uniform':
            downloadChartJs(constellationMagnitudeUniformChart,
                'score_brightness_vs_altitude', format, altitudeDownloadCounts());
            break;
        case 'constellation_magnitude_scaled':
            downloadChartJs(constellationMagnitudeScaledChart,
                'score_brightness_vs_altitude_scaled', format, altitudeDownloadCounts());
            break;
        case 'standardized_magnitude':
            downloadChartJs(standardizedMagnitudeChart, 'score_standardized_brightness', format);
            break;
        case 'allsky-plot':
            downloadAllSkyImage(format);
            break;
        default:
            console.error('Unknown chart for download:', chartKey);
    }
}

let chartDownloadsInitialized = false;

/**
 * Wire the per-card download dropdowns. Uses one delegated listener (attached
 * once) so it keeps working after charts are destroyed/recreated on theme
 * change, and reads the live chart references at click time.
 */
function initializeChartDownloads() {
    if (chartDownloadsInitialized) {
        return;
    }
    chartDownloadsInitialized = true;
    document.addEventListener('click', (event) => {
        const trigger = event.target.closest('[data-chart-download]');
        if (!trigger) {
            return;
        }
        handleChartDownload(
            trigger.getAttribute('data-chart-download'),
            trigger.getAttribute('data-format')
        );
    });
}

/**
 * Initialize all charts on the data visualization page
 */
function initializeDataVisualization() {
    initializeMagnitudeHistogram();
    initializeAllSkyPlot();
    initializeAltitudeCharts();
    initializeStandardizedMagnitude();
    initializeChartDownloads();
    updateStatBoxColors();
}

document.addEventListener('DOMContentLoaded', initializeDataVisualization);

// Subscribe to theme changes to update all charts and stat box colors
if (window.ThemeManager) {
    ThemeManager.subscribe((theme) => {
        console.log('Theme changed to:', theme);
        updateMagnitudeHistogramForTheme();
        initializeAltitudeCharts();
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
    if (constellationMagnitudeUniformChart) {
        constellationMagnitudeUniformChart.destroy();
        constellationMagnitudeUniformChart = null;
    }
    if (constellationMagnitudeScaledChart) {
        constellationMagnitudeScaledChart.destroy();
        constellationMagnitudeScaledChart = null;
    }
    if (standardizedMagnitudeChart) {
        standardizedMagnitudeChart.destroy();
        standardizedMagnitudeChart = null;
    }
});
