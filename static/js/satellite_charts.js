document.addEventListener('DOMContentLoaded', function() {
  // Chart element IDs
  const ELEMENTS = {
    observationsData: 'observations-data',
    charts: {
      brightness: 'brightness_chart',
      phaseAngle: 'phase_angle_chart',
      satElevation: 'sat_elevation_chart',
      solarElevation: 'solar_elevation_chart'
    },
    toggles: {
      binnedSatElevation: 'toggle_binned_sat_elevation',
      binnedSolarElevation: 'toggle_binned_solar_elevation',
      dataRange: 'toggle_data_range'
    },
    resetButtons: {
      brightness: 'reset_zoom_brightness',
      phaseAngle: 'reset_zoom_phase',
      satElevation: 'reset_zoom_sat_elevation',
      solarElevation: 'reset_zoom_solar_elevation'
    }
  };

  // Parse initial observation data from the page
  let observationData = [];
  const observationsDataElement = document.getElementById(ELEMENTS.observationsData);

  if (observationsDataElement) {
    try {
      observationData = JSON.parse(observationsDataElement.textContent);
    } catch (error) {
      console.error('Error parsing observations data:', error);
      observationData = [];
    }
  }

  // Consolidated configuration
  const CONFIG = {
    binSize: {
      satelliteAltitude: 1, // km
      solarElevation: 0.25  // degrees
    },
    pointSize: {
      min: 3,
      max: 15,
      densityDivisor: 10
    },
    errorBar: {
      width: 3,
      whiskerSize: 5
    },
    charts: {
      phaseAngle: { min: 0, max: 180, padding: 5 },
      solarElevation: { min: -90, max: 90, padding: 5 },
      satelliteAltitude: { min: 0, max: 1000, padding: 5 }
    },
    binning: {
      densityDivisor: 5,
      hoverRadiusMin: 5,
      hoverRadiusMax: 20
    },
    zoom: {
      dragBorderWidth: 2
    }
  };

  // Get constellation color using shared configuration
  function getConstellationColor(constellationId) {
    const theme = window.ConstellationConfig.getCurrentTheme();

    // If no constellation ID (e.g., single satellite view), use default theme colors
    if (!constellationId) {
      return theme === 'dark' ? 'rgba(255, 193, 7, 1)' : 'rgba(20, 41, 67, 1)';
    }

    return window.ConstellationConfig.getColor(constellationId, theme);
  }

  // Optimized data processing - single pass through data
  function processAllChartData(observationData) {
    const brightnessData = [];
    const phaseAngleData = [];
    const satElevationData = [];
    const solarElevationData = [];

    // Single pass through data to avoid multiple iterations
    for (const item of observationData) {
      if (item.magnitude === null || item.magnitude_uncertainty === null) continue;

      // Cache constellation color (avoid calling twice)
      const color = getConstellationColor(item.constellation);

      const baseItem = {
        y: item.magnitude,
        uncertainty: item.magnitude_uncertainty,
        date: new Date(item.date),
        backgroundColor: color,
        borderColor: color,
        constellation: item.constellation // Preserve constellation info
      };

      // Brightness data (time-based)
      brightnessData.push({
        ...baseItem,
        x: new Date(item.date)
      });

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
  let brightness_data = chartData.brightness;
  let phase_angle_data = chartData.phaseAngle;
  let sat_elevation_data = chartData.satElevation;
  let solar_elevation_data = chartData.solarElevation;

  // Chart instances
  let brightnessChartInstance;
  let phaseAngleChartInstance;
  let satElevationChartInstance;
  let solarElevationChartInstance;

  // Chart data bounds (calculated dynamically based on data)
  let phaseAngleDataMin = null;
  let phaseAngleDataMax = null;
  let satElevationDataMin = null;
  let satElevationDataMax = null;
  let solarElevationDataMin = null;
  let solarElevationDataMax = null;

  // Check for data availability
  if (sat_elevation_data.length === 0) {
    console.warn('No satellite elevation data available');
  }
  if (solar_elevation_data.length === 0) {
    console.warn('No solar elevation data available');
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
      maintainAspectRatio: false,
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
          limits: {
            x: { min: 'original', max: 'original', minRange: 0 },
            y: { min: 'original', max: 'original', minRange: 0 }
          },
          zoom: {
            wheel: { enabled: true },
            pinch: { enabled: true },
            drag: {
              enabled: true,
              modifierKey: 'meta',
              backgroundColor: colors.dragBoxBackground || 'rgba(20, 41, 67, 0.1)',
              borderColor: colors.dragBoxBorder || 'rgba(20, 41, 67, 0.8)',
              borderWidth: CONFIG.zoom.dragBorderWidth
            },
            mode: 'xy',
            scaleMode: 'xy'
          },
          pan: {
            enabled: true,
            mode: 'xy',
            scaleMode: 'xy'
          }
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
    // Extract colors from data points if available, otherwise use default colors
    const backgroundColors = data.map(row => row.backgroundColor || colors.backgroundColor);
    const borderColors = data.map(row => row.borderColor || colors.borderColor);

    // Use the same colors for error bars to match the constellation colors
    const errorBarColors = data.map(row => row.borderColor || colors.errorBarColor);

    const baseDataset = {
      data: data.map(row => ({
        x: row.x || row.date,
        y: row.y || row.magnitude,
        yMin: (row.y || row.magnitude) - row.uncertainty,
        yMax: (row.y || row.magnitude) + row.uncertainty,
        date: row.date,
        uncertainty: row.uncertainty
      })),
      backgroundColor: backgroundColors,
      borderColor: borderColors,
      errorBarColor: errorBarColors,
      errorBarWidth: CONFIG.errorBar.width,
      errorBarWhiskerColor: errorBarColors,
      errorBarWhiskerSize: CONFIG.errorBar.whiskerSize
    };

    if (chartType === 'line') {
      baseDataset.borderDash = [1, 1];
      baseDataset.pointRadius = CONFIG.pointSize.min;
      baseDataset.borderWidth = 1;
    }

    return baseDataset;
  }

  // Unified chart creation helper
  function createChart(elementId, data, config, colors, chartType = 'scatterWithErrorBars') {
    const options = createCommonChartOptions(config, colors, chartType);

    // Add time-specific config
    if (config.xAxisType === 'time') {
      options.scales.x.time = { unit: 'day' };
    }

    // Add min/max if specified
    if (config.xMin !== null) options.scales.x.min = config.xMin;
    if (config.xMax !== null) options.scales.x.max = config.xMax;

    // Handle multiple datasets (for binned elevation charts) or single dataset
    const datasets = Array.isArray(data[0]) || (data[0] && data[0].data)
      ? data
      : [createDataset(data, colors, chartType.includes('line') ? 'line' : 'scatter')];

    return new Chart(elementId, {
      type: chartType === 'elevation' ? 'scatterWithErrorBars' : chartType,
      data: { datasets },
      options
    });
  }

  /**
   * Format tooltip for binned data points
   */
  function formatBinnedTooltip(tooltipItem, xLabel) {
    const unit = xLabel.includes('degrees') ? '°' : '';
    const xValue = tooltipItem.parsed.x.toFixed(1);
    const pointCount = tooltipItem.raw.pointCount;

    return [
      `${xLabel}: ${xValue}${unit}`,
      `Bin represents ${pointCount} observations`
    ];
  }

  /**
   * Format tooltip for individual scatter points
   */
  function formatScatterTooltip(tooltipItem, xLabel, uncertainty) {
    const lines = [`Uncertainty: ${uncertainty}`];

    // Add x-axis value for non-time charts
    if (xLabel !== 'Date') {
      const xValue = tooltipItem.parsed.x.toFixed(2);
      const unit = xLabel.includes('degrees') ? '°' : '';
      lines.push(`${xLabel}: ${xValue}${unit}`);
    }

    // Add observation date
    const date = tooltipItem.raw.date ? tooltipItem.raw.date.toLocaleDateString() : 'N/A';
    lines.push(`Date: ${date}`);

    return lines;
  }

  /**
   * Create tooltip callbacks for charts
   */
  function createTooltipCallbacks(chartType, xLabel = 'Date') {
    return {
      title: function(tooltipItems) {
        const uncertainty = window.NumberFormatting.roundUncertainty(tooltipItems[0].raw.uncertainty);
        const magnitude = window.NumberFormatting.roundMagnitude(tooltipItems[0].parsed.y, uncertainty);
        return `Magnitude: ${magnitude}`;
      },
      afterTitle: function(tooltipItems) {
        const item = tooltipItems[0];
        const uncertainty = window.NumberFormatting.roundUncertainty(item.raw.uncertainty);
        const isBinned = (item.raw.pointCount || 1) > 1;

        return isBinned
          ? formatBinnedTooltip(item, xLabel)
          : formatScatterTooltip(item, xLabel, uncertainty);
      },
      label: function(context) {
        return null; // Remove individual point labels
      },
    };
  }

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
    const theme = window.ConstellationConfig.getCurrentTheme();
    const colors = getColorScheme(theme);

    destroyChart(brightnessChartInstance);

    const config = {
      title: 'Satellite Brightness Over Time',
      xLabel: 'Date',
      yLabel: 'Magnitude',
      xAxisType: 'time',
      xMin: null,
      xMax: null
    };

    brightnessChartInstance = createChart(
      document.getElementById(ELEMENTS.charts.brightness),
      brightness_data,
      config,
      colors
    );

    return brightnessChartInstance;
  }

  // Phase Angle vs Brightness chart
  function createPhaseAngleChart() {
    const theme = window.ConstellationConfig.getCurrentTheme();
    const colors = getColorScheme(theme);

    destroyChart(phaseAngleChartInstance);

    // Calculate the min and max values from the data
    phaseAngleDataMin = Math.floor(Math.min(...phase_angle_data.map(item => item.x))) - CONFIG.charts.phaseAngle.padding;
    phaseAngleDataMax = Math.floor(Math.max(...phase_angle_data.map(item => item.x))) + CONFIG.charts.phaseAngle.padding;

    // For line charts, group by constellation to get correct line colors
    const byConstellation = {};
    phase_angle_data.forEach(item => {
      const key = item.constellation || 'default';
      if (!byConstellation[key]) byConstellation[key] = [];
      byConstellation[key].push(item);
    });

    // Create dataset per constellation for proper line colors
    const datasets = Object.values(byConstellation).map(data =>
      createDataset(data, colors, 'line')
    );

    const config = {
      title: 'Satellite Brightness vs Phase Angle',
      xLabel: 'Phase Angle (degrees)',
      yLabel: 'Magnitude',
      xAxisType: 'linear',
      xMin: CONFIG.charts.phaseAngle.min,
      xMax: CONFIG.charts.phaseAngle.max
    };

    phaseAngleChartInstance = createChart(
      document.getElementById(ELEMENTS.charts.phaseAngle),
      datasets,
      config,
      colors,
      'lineWithErrorBars'
    );

    return phaseAngleChartInstance;
  }

  // Generic min/max calculation helper
  function calculateDataRange(data, defaultMin = 0, defaultMax = 100) {
    if (data.length > 0) {
      const padding = 5;
      return {
        min: Math.floor(Math.min(...data.map(item => item.x))) - padding,
        max: Math.ceil(Math.max(...data.map(item => item.x))) + padding
      };
    } else {
      return { min: defaultMin, max: defaultMax };
    }
  }

  // Generic elevation chart creator (used for both satellite and solar elevation)
  function createElevationChart(chartType) {
    const theme = window.ConstellationConfig.getCurrentTheme();
    const colors = getColorScheme(theme);

    // Map chart type to configuration
    const chartConfig = {
      satellite: {
        data: sat_elevation_data,
        instance: satElevationChartInstance,
        toggleId: ELEMENTS.toggles.binnedSatElevation,
        elementId: ELEMENTS.charts.satElevation,
        binSize: CONFIG.binSize.satelliteAltitude,
        chartRange: CONFIG.charts.satelliteAltitude,
        title: 'Satellite Brightness vs Altitude',
        titleBinned: `Satellite Brightness vs Altitude (Binned by Density, ${CONFIG.binSize.satelliteAltitude}km bins)`,
        xLabel: 'Satellite Altitude (km)',
        setDataMin: (val) => { satElevationDataMin = val; },
        setDataMax: (val) => { satElevationDataMax = val; },
        getDataMin: () => satElevationDataMin,
        getDataMax: () => satElevationDataMax
      },
      solar: {
        data: solar_elevation_data,
        instance: solarElevationChartInstance,
        toggleId: ELEMENTS.toggles.binnedSolarElevation,
        elementId: ELEMENTS.charts.solarElevation,
        binSize: CONFIG.binSize.solarElevation,
        chartRange: CONFIG.charts.solarElevation,
        title: 'Satellite Brightness vs Solar Elevation',
        titleBinned: `Satellite Brightness vs Solar Elevation (Binned by Density, ${CONFIG.binSize.solarElevation}° bins)`,
        xLabel: 'Solar Elevation (degrees)',
        setDataMin: (val) => { solarElevationDataMin = val; },
        setDataMax: (val) => { solarElevationDataMax = val; },
        getDataMin: () => solarElevationDataMin,
        getDataMax: () => solarElevationDataMax
      }
    }[chartType];

    destroyChart(chartConfig.instance);

    // Calculate min/max
    const range = calculateDataRange(chartConfig.data, chartConfig.chartRange.min, chartConfig.chartRange.max);
    chartConfig.setDataMin(range.min);
    chartConfig.setDataMax(range.max);

    if (chartConfig.data.length === 0) {
      console.warn(`No ${chartType} elevation data available for chart`);
    }

    // Check if binned data toggle is enabled
    const useBinnedData = document.getElementById(chartConfig.toggleId)?.checked || false;

    let datasets;
    if (useBinnedData && chartConfig.data.length > 0) {
      const binnedDatasets = createBinnedData(chartConfig.data, chartConfig.binSize);
      datasets = binnedDatasets.map(binData => ({
        ...binData,
        errorBarWidth: CONFIG.errorBar.width,
        errorBarWhiskerSize: CONFIG.errorBar.whiskerSize
      }));
    } else {
      datasets = [createDataset(chartConfig.data, colors, 'scatter')];
    }

    const config = {
      title: chartConfig.data.length > 0 ?
        (useBinnedData ? chartConfig.titleBinned : chartConfig.title) :
        `${chartConfig.title} (No Data Available)`,
      xLabel: chartConfig.xLabel,
      yLabel: 'Magnitude',
      xAxisType: 'linear',
      xMin: chartConfig.getDataMin(),
      xMax: chartConfig.getDataMax()
    };

    const instance = createChart(
      document.getElementById(chartConfig.elementId),
      datasets,
      config,
      colors,
      'scatterWithErrorBars'
    );

    // Update the instance variable
    if (chartType === 'satellite') {
      satElevationChartInstance = instance;
    } else {
      solarElevationChartInstance = instance;
    }

    return instance;
  }

  // Satellite Elevation chart wrapper
  function createSatElevationChart() {
    return createElevationChart('satellite');
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

      // Determine the dominant constellation color in this bin
      // Count occurrences of each color
      const colorCounts = {};
      points.forEach(p => {
        const color = p.backgroundColor || p.borderColor;
        if (color) {
          colorCounts[color] = (colorCounts[color] || 0) + 1;
        }
      });

      // Find the most common color (or use first point's color as fallback)
      const dominantColor = Object.keys(colorCounts).reduce((a, b) =>
        colorCounts[a] > colorCounts[b] ? a : b,
        points[0]?.backgroundColor || points[0]?.borderColor
      );

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
        backgroundColor: dominantColor,
        borderColor: dominantColor,
        errorBarColor: dominantColor,
        errorBarWhiskerColor: dominantColor,
        pointRadius: Math.min(Math.max(density / CONFIG.pointSize.densityDivisor, CONFIG.pointSize.min), CONFIG.pointSize.max),
        pointHoverRadius: Math.min(Math.max(density / CONFIG.binning.densityDivisor, CONFIG.binning.hoverRadiusMin), CONFIG.binning.hoverRadiusMax)
      };
    });
  }

  // Solar Elevation chart wrapper
  function createSolarElevationChart() {
    return createElevationChart('solar');
  }

  function updateCharts() {
    try {
      // Re-read observation data from the DOM element
      const observationsDataElement = document.getElementById(ELEMENTS.observationsData);
      let freshObservationData = [];

      if (observationsDataElement) {
        try {
          freshObservationData = JSON.parse(observationsDataElement.textContent);
        } catch (error) {
          console.error('Error parsing fresh observation data:', error);
        }
      }

      // Re-process the data for charts
      const freshChartData = processAllChartData(freshObservationData);

      // Update the module-level data variables
      brightness_data = freshChartData.brightness;
      phase_angle_data = freshChartData.phaseAngle;
      sat_elevation_data = freshChartData.satElevation;
      solar_elevation_data = freshChartData.solarElevation;

      // Create charts with new data (each create function handles cleanup)
      brightnessChartInstance = createBrightnessChart();
      phaseAngleChartInstance = createPhaseAngleChart();
      satElevationChartInstance = createSatElevationChart();
      solarElevationChartInstance = createSolarElevationChart();
    } catch (error) {
      console.error('Error in updateCharts():', error);
    }
  }

  // Reset button handler using event delegation
  function setupResetButtons() {
    document.addEventListener('click', (event) => {
      const { id } = event.target;

      if (id === ELEMENTS.resetButtons.brightness && brightnessChartInstance) {
        brightnessChartInstance.resetZoom();
      } else if (id === ELEMENTS.resetButtons.phaseAngle && phaseAngleChartInstance) {
        phaseAngleChartInstance.resetZoom();
      } else if (id === ELEMENTS.resetButtons.satElevation && satElevationChartInstance) {
        satElevationChartInstance.resetZoom();
      } else if (id === ELEMENTS.resetButtons.solarElevation && solarElevationChartInstance) {
        solarElevationChartInstance.resetZoom();
      }
    });
  }

  // Handle theming with debounced updates
  updateCharts();

  // Setup reset buttons once after initial chart creation
  setupResetButtons();

  // Expose updateCharts globally for external access (used by satellite_selector.js)
  window.updateCharts = updateCharts;

  document.getElementById(ELEMENTS.toggles.dataRange).addEventListener('change', function() {
    const useDataRange = this.checked;

    if (useDataRange) {
      // Set min/max to data range
      phaseAngleChartInstance.options.scales.x.min = phaseAngleDataMin;
      phaseAngleChartInstance.options.scales.x.max = phaseAngleDataMax;
    } else {
      // default
      phaseAngleChartInstance.options.scales.x.min = CONFIG.charts.phaseAngle.min;
      phaseAngleChartInstance.options.scales.x.max = CONFIG.charts.phaseAngle.max;
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

// Chart.js theme color schemes
const colorSchemes = {
  light: {
    backgroundColor: 'rgba(20, 41, 67, 1)',
    borderColor: 'rgba(20, 41, 67, 1)',
    gridColor: 'rgba(0, 0, 0, 0.1)',
    textColor: '#666',
    errorBarColor: 'rgba(20, 41, 67, .5)',
    dragBoxBackground: 'rgba(20, 41, 67, 0.1)',
    dragBoxBorder: 'rgba(20, 41, 67, 0.8)'
  },
  dark: {
    backgroundColor: 'rgba(255, 193, 7, 1)',
    borderColor: 'rgba(255, 193, 7, 1)',
    gridColor: 'rgba(255, 255, 255, 0.1)',
    textColor: '#ccc',
    errorBarColor: 'rgba(255, 193, 7, .5)',
    dragBoxBackground: 'rgba(255, 193, 7, 0.1)',
    dragBoxBorder: 'rgba(255, 193, 7, 0.8)'
  }
};

/**
 * Get color scheme for theme
 * @param {string} theme - 'light' or 'dark'
 * @returns {Object} Color scheme
 */
function getColorScheme(theme) {
  return colorSchemes[theme || window.ConstellationConfig.getCurrentTheme()];
}

// Subscribe to theme changes via centralized ThemeManager
if (window.ThemeManager) {
  ThemeManager.subscribe((theme) => {
    console.log('Updating charts for theme:', theme);
    // Call the globally exposed updateCharts function
    if (typeof window.updateCharts === 'function') {
      window.updateCharts();
    }
  });
}
