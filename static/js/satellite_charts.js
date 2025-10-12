document.addEventListener('DOMContentLoaded', function() {
  // Cache DOM elements for performance
  const DOM_CACHE = {
    observationsData: document.getElementById('observations-data'),
    brightnessChart: document.getElementById('brightness_chart'),
    phaseAngleChart: document.getElementById('phase_angle_chart'),
    satElevationChart: document.getElementById('sat_elevation_chart'),
    solarElevationChart: document.getElementById('solar_elevation_chart'),
    toggleBinnedSatElevation: document.getElementById('toggle_binned_sat_elevation'),
    toggleBinnedSolarElevation: document.getElementById('toggle_binned_solar_elevation'),
    toggleDataRange: document.getElementById('toggle_data_range'),
    resetZoomBrightness: document.getElementById('reset_zoom_brightness'),
    resetZoomPhase: document.getElementById('reset_zoom_phase'),
    resetZoomSatElevation: document.getElementById('reset_zoom_sat_elevation'),
    resetZoomSolarElevation: document.getElementById('reset_zoom_solar_elevation')
  };

  if (!DOM_CACHE.observationsData) {
    return;
  }

  // parse data from the page/context
  let observationData;
  try {
    observationData = JSON.parse(DOM_CACHE.observationsData.textContent);
  } catch (error) {
    console.error('Error parsing observations data:', error);
    return;
  }

  // Performance constants
  const PERFORMANCE_CONFIG = {
    BIN_SIZE: {
      SATELLITE_ALTITUDE: 1, // km
      SOLAR_ELEVATION: 0.25  // degrees
    },
    POINT_SIZE: {
      MIN: 3,
      MAX: 15,
      DENSITY_DIVISOR: 10
    }
  };

  // Chart configuration constants
  const CHART_CONFIG = {
    DEBOUNCE_DELAY: 150, // milliseconds
  };

  // Error bar configuration constants
  const ERROR_BAR_CONFIG = {
    WIDTH: 3,
    WHISKER_SIZE: 5
  };

  // Phase angle chart constants
  const PHASE_ANGLE_CONFIG = {
    MIN_DEGREES: 0,
    MAX_DEGREES: 180,
    PADDING: 5
  };

  // Solar elevation chart constants
  const SOLAR_ELEVATION_CONFIG = {
    MIN_DEGREES: -90,
    MAX_DEGREES: 90,
    PADDING: 5
  };

  // Satellite altitude chart constants
  const SATELLITE_ALTITUDE_CONFIG = {
    MIN_KM: 0,
    MAX_KM: 1000,
    PADDING: 5
  };

  // Binning calculation constants
  const BINNING_CONFIG = {
    DENSITY_DIVISOR: 5,
    HOVER_RADIUS_MIN: 5,
    HOVER_RADIUS_MAX: 20
  };

  // Zoom and interaction constants
  const ZOOM_CONFIG = {
    DRAG_BORDER_WIDTH: 2,
    TOOLTIP_PRECISION: {
      SINGLE_DECIMAL: 1,
      DOUBLE_DECIMAL: 2
    }
  };

  // Optimized data processing - single pass through data
  function processAllChartData(observationData) {
    const brightnessData = [];
    const phaseAngleData = [];
    const satElevationData = [];
    const solarElevationData = [];

    // Single pass through data to avoid multiple iterations
    for (const item of observationData) {
      if (item.magnitude === null || item.magnitude_uncertainty === null) continue;

      const baseItem = {
        y: item.magnitude,
        uncertainty: item.magnitude_uncertainty,
        date: new Date(item.date)
      };

      // Brightness data (time-based)
      if (item.magnitude !== null && item.magnitude_uncertainty !== null) {
        brightnessData.push({
          ...baseItem,
          x: new Date(item.date)
        });
      }

      // Phase angle data
      if (item.phase_angle !== null) {
        phaseAngleData.push({
          ...baseItem,
          x: item.phase_angle
        });
      }

      // Satellite elevation data
      if (item.sat_altitude_km_satchecker !== null) {
        satElevationData.push({
          ...baseItem,
          x: item.sat_altitude_km_satchecker
        });
      }

      // Solar elevation data
      if (item.solar_elevation_deg_satchecker !== null) {
        solarElevationData.push({
          ...baseItem,
          x: item.solar_elevation_deg_satchecker
        });
      }
    }

    // Sort data once
    brightnessData.sort((a, b) => a.x - b.x);
    phaseAngleData.sort((a, b) => a.x - b.x);
    satElevationData.sort((a, b) => a.x - b.x);
    solarElevationData.sort((a, b) => a.x - b.x);

    return {
      brightness: brightnessData,
      phaseAngle: phaseAngleData,
      satElevation: satElevationData,
      solarElevation: solarElevationData
    };
  }

  // Set up data for all charts using optimized single-pass processing
  const chartData = processAllChartData(observationData);
  const brightness_data = chartData.brightness;
  const phase_angle_data = chartData.phaseAngle;
  const sat_elevation_data = chartData.satElevation;
  const solar_elevation_data = chartData.solarElevation;

  // Check for data availability
  if (sat_elevation_data.length === 0) {
    console.warn('No satellite elevation data available');
  }
  if (solar_elevation_data.length === 0) {
    console.warn('No solar elevation data available');
  }

  /**
   * Creates a chart configuration object
   * @param {string} title - Chart title
   * @param {string} xLabel - X-axis label
   * @param {string} yLabel - Y-axis label
   * @param {string} xAxisType - X-axis type ('linear' or 'time')
   * @param {number|null} xMin - Minimum X value
   * @param {number|null} xMax - Maximum X value
   * @returns {Object} Chart configuration object
   */
  function createChartConfig(title, xLabel, yLabel, xAxisType = 'linear', xMin = null, xMax = null) {
    return {
      title,
      xLabel,
      yLabel,
      xAxisType,
      xMin,
      xMax
    };
  }

  /**
   * Creates common chart options with consistent styling
   * @param {Object} config - Chart configuration object
   * @param {Object} colors - Color scheme object
   * @param {string} chartType - Type of chart for specific options
   * @returns {Object} Chart.js options object
   */
  function createCommonChartOptions(config, colors, chartType = 'default') {
    return {
      responsive: true,
      scales: {
        x: {
          type: config.xAxisType,
          title: {
            display: true,
            text: config.xLabel,
            color: colors.textColor
          },
          grid: { color: colors.gridColor },
          ticks: { color: colors.textColor }
        },
        y: {
          reverse: true,
          title: {
            display: true,
            text: config.yLabel,
            color: colors.textColor
          },
          grid: { color: colors.gridColor },
          ticks: { color: colors.textColor }
        }
      },
      plugins: {
        legend: { display: false },
        title: {
          display: true,
          text: config.title,
          color: colors.textColor
        },
        tooltip: {
          callbacks: createTooltipCallbacks(chartType, config.xLabel),
          displayColors: false,
          titleFont: { weight: "normal" }
        },
        zoom: {
          zoom: {
            wheel: { enabled: true },
            pinch: { enabled: true },
            drag: {
              enabled: true,
              modifierKey: 'meta',
              backgroundColor: colors.dragBoxBackground || 'rgba(20, 41, 67, 0.1)',
              borderColor: colors.dragBoxBorder || 'rgba(20, 41, 67, 0.8)',
              borderWidth: ZOOM_CONFIG.DRAG_BORDER_WIDTH
            },
            mode: 'xy'
          },
          pan: { enabled: true, mode: 'xy' }
        }
      }
    };
  }

  /**
   * Creates a dataset for Chart.js with error bars
   * @param {Array} data - Array of data points
   * @param {Object} colors - Color scheme object
   * @param {string} chartType - Type of chart ('scatter' or 'line')
   * @returns {Object} Chart.js dataset object
   */
  function createDataset(data, colors, chartType = 'scatter') {
    const baseDataset = {
      data: data.map(row => ({
        x: row.x || row.date,
        y: row.y || row.magnitude,
        yMin: (row.y || row.magnitude) - row.uncertainty,
        yMax: (row.y || row.magnitude) + row.uncertainty,
        date: row.date,
        uncertainty: row.uncertainty
      })),
      backgroundColor: colors.backgroundColor,
      borderColor: colors.borderColor,
      errorBarColor: colors.errorBarColor,
      errorBarWidth: ERROR_BAR_CONFIG.WIDTH,
      errorBarWhiskerColor: colors.errorBarColor,
      errorBarWhiskerSize: ERROR_BAR_CONFIG.WHISKER_SIZE
    };

    if (chartType === 'line') {
      baseDataset.borderDash = [1, 1];
      baseDataset.pointRadius = PERFORMANCE_CONFIG.POINT_SIZE.MIN;
      baseDataset.borderWidth = 1;
    }

    return baseDataset;
  }

  // Elevation chart creation helper (for satellite/solar elevation charts)
  function createElevationChart(elementId, datasets, config, colors, chartType) {
    const options = createCommonChartOptions(config, colors, chartType);

    // Add min/max for elevation charts
    options.scales.x.min = config.xMin;
    options.scales.x.max = config.xMax;

    return new Chart(elementId, {
      type: 'scatterWithErrorBars',
      data: { datasets },
      options
    });
  }

  // Complete chart creation helper
  function createChart(elementId, data, config, colors, chartType = 'scatterWithErrorBars') {
    const options = createCommonChartOptions(config, colors, 'default');

    // Add time-specific config
    if (config.xAxisType === 'time') {
      options.scales.x.time = { unit: 'day' };
    }

    // Add min/max if specified
    if (config.xMin !== null) options.scales.x.min = config.xMin;
    if (config.xMax !== null) options.scales.x.max = config.xMax;

    return new Chart(elementId, {
      type: chartType,
      data: { datasets: [createDataset(data, colors, chartType.includes('line') ? 'line' : 'scatter')] },
      options
    });
  }

  // Common tooltip helper
  function createTooltipCallbacks(chartType, xLabel = 'Date') {
    return {
      title: function(tooltipItems) {
        const uncertainty = window.NumberFormatting.roundUncertainty(tooltipItems[0].raw.uncertainty);
        return `Magnitude: ${window.NumberFormatting.roundMagnitude(tooltipItems[0].parsed.y, uncertainty)}`;
      },
      afterTitle: function(tooltipItems) {
        const uncertainty = window.NumberFormatting.roundUncertainty(tooltipItems[0].raw.uncertainty);
        const pointCount = tooltipItems[0].raw.pointCount || 1;
        const isBinned = pointCount > 1;

        if (isBinned) {
          return [
            `${xLabel}: ${tooltipItems[0].parsed.x.toFixed(ZOOM_CONFIG.TOOLTIP_PRECISION.SINGLE_DECIMAL)}${xLabel.includes('degrees') ? '°' : ''}`,
            `Bin represents ${pointCount} observations`
          ];
        } else {
          // Build tooltip lines
          const tooltipLines = [`Uncertainty: ${uncertainty}`];

          // Add x-axis value for non-time charts
          if (xLabel !== 'Date') {
            const xValue = tooltipItems[0].parsed.x.toFixed(ZOOM_CONFIG.TOOLTIP_PRECISION.DOUBLE_DECIMAL);
            const unit = xLabel.includes('degrees') ? '°' : '';
            tooltipLines.push(`${xLabel}: ${xValue}${unit}`);
          }

          // Add observation date for all charts
          const date = tooltipItems[0].raw.date ? tooltipItems[0].raw.date.toLocaleDateString() : 'N/A';
          tooltipLines.push(`Date: ${date}`);

          tooltipLines.push(`Number of points: ${tooltipItems.length}`);
          return tooltipLines;
        }
      },
      label: function(context) {
        return null; // This removes individual point labels
      },
    };
  }

  // Chart instances with proper cleanup
  let brightnessChartInstance;
  let phaseAngleChartInstance;
  let satElevationChartInstance;
  let solarElevationChartInstance;

  // Chart cleanup utility
  function destroyChart(chart) {
    if (chart && typeof chart.destroy === 'function') {
      chart.destroy();
    }
  }

  // Cleanup all charts
  function cleanupAllCharts() {
    destroyChart(brightnessChartInstance);
    destroyChart(phaseAngleChartInstance);
    destroyChart(satElevationChartInstance);
    destroyChart(solarElevationChartInstance);
  }

  function createBrightnessChart() {
    const theme = getCurrentTheme();
    const colors = colorSchemes[theme];

    destroyChart(brightnessChartInstance);

    const config = createChartConfig(
      'Satellite Brightness Over Time',
      'Date',
      'Magnitude',
      'time'
    );

    brightnessChartInstance = createChart(
      document.getElementById('brightness_chart'),
      brightness_data,
      config,
      colors
    );

    return brightnessChartInstance;
  }

  // Phase Angle vs Brightness chart
  let phaseAngleDataMin = null; // To store the minimum value of phase angle data
  let phaseAngleDataMax = null; // To store the maximum value of phase angle data

  function createPhaseAngleChart() {
    const theme = getCurrentTheme();
    const colors = colorSchemes[theme];

    destroyChart(phaseAngleChartInstance);

    // Calculate the min and max values from the data
    phaseAngleDataMin = Math.floor(Math.min(...phase_angle_data.map(item => item.x))) - PHASE_ANGLE_CONFIG.PADDING;
    phaseAngleDataMax = Math.floor(Math.max(...phase_angle_data.map(item => item.x))) + PHASE_ANGLE_CONFIG.PADDING;

    const config = createChartConfig(
      'Satellite Brightness vs Phase Angle',
      'Phase Angle (degrees)',
      'Magnitude',
      'linear',
      PHASE_ANGLE_CONFIG.MIN_DEGREES,
      PHASE_ANGLE_CONFIG.MAX_DEGREES
    );

    phaseAngleChartInstance = createChart(
      document.getElementById('phase_angle_chart'),
      phase_angle_data,
      config,
      colors,
      'lineWithErrorBars'
    );


    return phaseAngleChartInstance;
  }

  // Satellite Elevation chart
  let satElevationDataMin = null;
  let satElevationDataMax = null;

  function createSatElevationChart() {
    const theme = getCurrentTheme();
    const colors = colorSchemes[theme];

    destroyChart(satElevationChartInstance);

    // Calculate min/max for satellite altitude
    const satRange = calculateDataRange(sat_elevation_data, SATELLITE_ALTITUDE_CONFIG.MIN_KM, SATELLITE_ALTITUDE_CONFIG.MAX_KM);
    satElevationDataMin = satRange.min;
    satElevationDataMax = satRange.max;

    if (sat_elevation_data.length === 0) {
      console.warn('No satellite elevation data available for chart');
    }

    // Check if binned data toggle is enabled
    const useBinnedData = document.getElementById('toggle_binned_sat_elevation')?.checked || false;

    let datasets;
    if (useBinnedData && sat_elevation_data.length > 0) {
      // Create binned data for better visualization of dense clusters
      const binnedDatasets = createBinnedData(sat_elevation_data, PERFORMANCE_CONFIG.BIN_SIZE.SATELLITE_ALTITUDE);
      datasets = binnedDatasets.map(binData => ({
        ...binData,
        backgroundColor: colors.backgroundColor,
        borderColor: colors.borderColor,
        errorBarColor: colors.errorBarColor,
        errorBarWidth: ERROR_BAR_CONFIG.WIDTH,
        errorBarWhiskerColor: colors.errorBarColor,
        errorBarWhiskerSize: ERROR_BAR_CONFIG.WHISKER_SIZE
      }));
    } else {
      // Use raw data
      datasets = [createDataset(sat_elevation_data, colors, 'scatter')];
    }

    const config = createChartConfig(
      sat_elevation_data.length > 0 ?
        (useBinnedData ? `Satellite Brightness vs Altitude (Binned by Density, ${PERFORMANCE_CONFIG.BIN_SIZE.SATELLITE_ALTITUDE}km bins)` : 'Satellite Brightness vs Altitude') :
        'Satellite Brightness vs Altitude (No Data Available)',
      'Satellite Altitude (km)',
      'Magnitude',
      'linear',
      satElevationDataMin,
      satElevationDataMax
    );

    // Create chart with custom datasets using the existing helper
    satElevationChartInstance = createElevationChart(
      document.getElementById('sat_elevation_chart'),
      datasets,
      config,
      colors,
      'satElevation'
    );

    return satElevationChartInstance;
  }

  // Solar Elevation chart
  let solarElevationDataMin = null;
  let solarElevationDataMax = null;

  // Generic min/max calculation helper
  function calculateDataRange(data, defaultMin = 0, defaultMax = 100) {
    if (data.length > 0) {
      return {
        min: Math.floor(Math.min(...data.map(item => item.x))) - PHASE_ANGLE_CONFIG.PADDING,
        max: Math.ceil(Math.max(...data.map(item => item.x))) + PHASE_ANGLE_CONFIG.PADDING
      };
    } else {
      return { min: defaultMin, max: defaultMax };
    }
  }

  // Binning functionality for dense data visualization
  function createBinnedData(data, binSize = 0.25) {
    const bins = {};

    data.forEach(point => {
      const binKey = Math.floor(point.x / binSize) * binSize;
      if (!bins[binKey]) {
        bins[binKey] = [];
      }
      bins[binKey].push(point);
    });

    // Create binned datasets with different point sizes based on density
    return Object.entries(bins).map(([binCenter, points]) => {
      const density = points.length;
      const avgMagnitude = points.reduce((sum, p) => sum + p.y, 0) / points.length;
      const avgUncertainty = points.reduce((sum, p) => sum + p.uncertainty, 0) / points.length;

      return {
        data: [{
          x: parseFloat(binCenter),
          y: avgMagnitude,
          yMin: avgMagnitude - avgUncertainty,
          yMax: avgMagnitude + avgUncertainty,
          density: density,
          pointCount: density,
          dates: points.map(p => p.date),
          uncertainties: points.map(p => p.uncertainty)
        }],
        pointRadius: Math.min(Math.max(density / PERFORMANCE_CONFIG.POINT_SIZE.DENSITY_DIVISOR, PERFORMANCE_CONFIG.POINT_SIZE.MIN), PERFORMANCE_CONFIG.POINT_SIZE.MAX),
        pointHoverRadius: Math.min(Math.max(density / BINNING_CONFIG.DENSITY_DIVISOR, BINNING_CONFIG.HOVER_RADIUS_MIN), BINNING_CONFIG.HOVER_RADIUS_MAX)
      };
    });
  }

  function createSolarElevationChart() {
    const theme = getCurrentTheme();
    const colors = colorSchemes[theme];

    destroyChart(solarElevationChartInstance);

    // Calculate min/max for solar elevation
    const solarRange = calculateDataRange(solar_elevation_data, SOLAR_ELEVATION_CONFIG.MIN_DEGREES, SOLAR_ELEVATION_CONFIG.MAX_DEGREES);
    solarElevationDataMin = solarRange.min;
    solarElevationDataMax = solarRange.max;

    if (solar_elevation_data.length === 0) {
      console.warn('No solar elevation data available for chart');
    }

    // Check if binned data toggle is enabled
    const useBinnedData = document.getElementById('toggle_binned_solar_elevation')?.checked || false;

    let datasets;
    if (useBinnedData && solar_elevation_data.length > 0) {
      // Create binned data for better visualization of dense clusters
      const binnedDatasets = createBinnedData(solar_elevation_data, PERFORMANCE_CONFIG.BIN_SIZE.SOLAR_ELEVATION);
      datasets = binnedDatasets.map(binData => ({
        ...binData,
        backgroundColor: colors.backgroundColor,
        borderColor: colors.borderColor,
        errorBarColor: colors.errorBarColor,
        errorBarWidth: ERROR_BAR_CONFIG.WIDTH,
        errorBarWhiskerColor: colors.errorBarColor,
        errorBarWhiskerSize: ERROR_BAR_CONFIG.WHISKER_SIZE
      }));
    } else {
      // Use raw data
      datasets = [createDataset(solar_elevation_data, colors, 'scatter')];
    }

    const config = createChartConfig(
      solar_elevation_data.length > 0 ?
        (useBinnedData ? `Satellite Brightness vs Solar Elevation (Binned by Density, ${PERFORMANCE_CONFIG.BIN_SIZE.SOLAR_ELEVATION}° bins)` : 'Satellite Brightness vs Solar Elevation') :
        'Satellite Brightness vs Solar Elevation (No Data Available)',
      'Solar Elevation (degrees)',
      'Magnitude',
      'linear',
      solarElevationDataMin,
      solarElevationDataMax
    );

    // Create chart with custom datasets using the existing helper
    solarElevationChartInstance = createElevationChart(
      document.getElementById('solar_elevation_chart'),
      datasets,
      config,
      colors,
      'solarElevation'
    );

    return solarElevationChartInstance;
  }

  // Debouncing utility for performance
  function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }

  // Chart update with debouncing and requestAnimationFrame for smooth updates
  const debouncedUpdateCharts = debounce(() => {
    requestAnimationFrame(() => {
      brightnessChartInstance = createBrightnessChart();
      phaseAngleChartInstance = createPhaseAngleChart();
      satElevationChartInstance = createSatElevationChart();
      solarElevationChartInstance = createSolarElevationChart();
    });
  }, CHART_CONFIG.DEBOUNCE_DELAY); // debounce delay

  function updateCharts() {
    // Create charts immediately on first call
    brightnessChartInstance = createBrightnessChart();
    phaseAngleChartInstance = createPhaseAngleChart();
    satElevationChartInstance = createSatElevationChart();
    solarElevationChartInstance = createSolarElevationChart();
  }

  // Chart registry for reset button management
  const chartRegistry = {
    brightness: () => brightnessChartInstance,
    phaseAngle: () => phaseAngleChartInstance,
    satElevation: () => satElevationChartInstance,
    solarElevation: () => solarElevationChartInstance
  };

  // Generic reset button setup using event delegation
  function setupResetButtons() {
    // Use event delegation for better performance and automatic cleanup
    document.addEventListener('click', (event) => {
      const target = event.target;

      // Handle brightness chart reset
      if (target.id === 'reset_zoom_brightness' && chartRegistry.brightness()) {
        chartRegistry.brightness().resetZoom();
        return;
      }

      // Handle phase angle chart reset
      if (target.id === 'reset_zoom_phase' && chartRegistry.phaseAngle()) {
        chartRegistry.phaseAngle().resetZoom();
        return;
      }

      // Handle satellite elevation chart reset
      if (target.id === 'reset_zoom_sat_elevation' && chartRegistry.satElevation()) {
        chartRegistry.satElevation().resetZoom();
        return;
      }

      // Handle solar elevation chart reset
      if (target.id === 'reset_zoom_solar_elevation' && chartRegistry.solarElevation()) {
        chartRegistry.solarElevation().resetZoom();
        return;
      }
    });
  }

  // Handle theming with debounced updates
  updateCharts();

  // Setup reset buttons once after initial chart creation
  setupResetButtons();

  // Optimized theme change handling
  document.querySelectorAll('[data-bs-theme-value]').forEach(toggle => {
    toggle.addEventListener('click', () => {
      // Use debounced updates for theme changes
      debouncedUpdateCharts();
    });
  });

  document.getElementById('toggle_data_range').addEventListener('change', function() {
    const useDataRange = this.checked;

    if (useDataRange) {
      // Set min/max to data range
      phaseAngleChartInstance.options.scales.x.min = phaseAngleDataMin;
      phaseAngleChartInstance.options.scales.x.max = phaseAngleDataMax;
    } else {
      // default
      phaseAngleChartInstance.options.scales.x.min = PHASE_ANGLE_CONFIG.MIN_DEGREES;
      phaseAngleChartInstance.options.scales.x.max = PHASE_ANGLE_CONFIG.MAX_DEGREES;
    }

    phaseAngleChartInstance.update();
  });

  // Toggle handling helper
  function setupToggleHandler(toggleId, chartFunction) {
    document.getElementById(toggleId).addEventListener('change', function() {
      chartFunction();
    });
  }

  // Setup all toggle handlers
  setupToggleHandler('toggle_binned_solar_elevation', createSolarElevationChart);
  setupToggleHandler('toggle_binned_sat_elevation', createSatElevationChart);

  // Cleanup on page unload to prevent memory leaks
  window.addEventListener('beforeunload', cleanupAllCharts);
});

function getCurrentTheme() {
  return document.documentElement.getAttribute('data-bs-theme') || 'light';
}

const colorSchemes = {
  light: {
    backgroundColor: 'rgba(20, 41, 67, 1)',
    borderColor: 'rgba(20, 41, 67, 1)',
    gridColor: 'rgba(0, 0, 0, 0.1)',
    textColor: '#666',
    errorBarColor: 'rgba(20, 41, 67, .5)',  // primary color with 50% opacity
    dragBoxBackground: 'rgba(20, 41, 67, 0.1)',
    dragBoxBorder: 'rgba(20, 41, 67, 0.8)'
  },
  dark: {
    backgroundColor: 'rgba(255, 193, 7, 1)',
    borderColor: 'rgba(255, 193, 7, 1)',
    gridColor: 'rgba(255, 255, 255, 0.1)',
    textColor: '#ccc',
    errorBarColor: 'rgba(255, 193, 7, .5)',  // primary color with 50% opacity
    dragBoxBackground: 'rgba(255, 193, 7, 0.1)',
    dragBoxBorder: 'rgba(255, 193, 7, 0.8)'
  }
};

// Listen for theme changes
const observer = new MutationObserver((mutations) => {
  mutations.forEach((mutation) => {
    if (mutation.type === 'attributes' && mutation.attributeName === 'data-bs-theme') {
      debouncedUpdateCharts();
    }
  });
});

observer.observe(document.documentElement, {
  attributes: true,
  attributeFilter: ['data-bs-theme']
});
