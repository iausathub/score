document.addEventListener('DOMContentLoaded', function() {
  const observationsDataElement = document.getElementById('observations-data');

  if (!observationsDataElement) {
    console.log('Observations data element not found. Charts will not be rendered.');
    return;
  }

  // parse data from the page/context
  let observationData;
  try {
    observationData = JSON.parse(observationsDataElement.textContent);
  } catch (error) {
    console.error('Error parsing observations data:', error);
    return;
  }

  // Set up data for the brightness chart
  const brightness_data = observationData
    .filter(item => item.magnitude !== null && item.magnitude_uncertainty !== null)
    .map(item => ({
      date: new Date(item.date),
      magnitude: item.magnitude,
      uncertainty: item.magnitude_uncertainty
    }))
    .sort((a, b) => a.date - b.date);

  // Set up data for the phase angle chart
  const phase_angle_data = observationData
    .filter(item => item.magnitude !== null && item.phase_angle !== null && item.magnitude_uncertainty !== null)
    .map(item => ({
      x: item.phase_angle,
      y: item.magnitude,
      uncertainty: item.magnitude_uncertainty,
      date: new Date(item.date)
    }))
    .sort((a, b) => a.x - b.x); // Sort by phase angle smallest to largest

  // Brightness chart
  let brightnessChart;

  function createBrightnessChart() {
    const theme = getCurrentTheme();
    const colors = colorSchemes[theme];

    if (brightnessChart) {
      brightnessChart.destroy();
    }

    console.log('Creating brightness chart with data:', brightness_data);

    brightnessChart = new Chart(
      document.getElementById('brightness_chart'),
      {
        type: 'scatterWithErrorBars',
        data: {
          datasets: [{
            data: brightness_data.map(row => ({
              x: row.date,
              y: row.magnitude,
              yMin: row.magnitude - row.uncertainty,
              yMax: row.magnitude + row.uncertainty,
              date: row.date,
              uncertainty: row.uncertainty
            })),
            backgroundColor: colors.backgroundColor,
            borderColor: colors.borderColor,
            errorBarColor: colors.errorBarColor,
            errorBarWidth: 3,
            errorBarWhiskerColor: colors.errorBarColor,
            errorBarWhiskerSize: 5
          }]
        },
        options: {
          responsive: true,
          scales: {
            x: {
              type: 'time',
              time: {
                unit: 'day'
              },
              title: {
                display: true,
                text: 'Date',
                color: colors.textColor
              },
              grid: {
                color: colors.gridColor
              },
              ticks: {
                color: colors.textColor
              }
            },
            y: {
              reverse: true, // Reverse y-axis (lower magnitude = brighter)
              title: {
                display: true,
                text: 'Magnitude',
                color: colors.textColor
              },
              grid: {
                color: colors.gridColor
              },
              ticks: {
                color: colors.textColor
              }
            }
          },
          plugins: {
            legend: {
              display: false
            },
            title: {
              display: true,
              text: 'Satellite Brightness Over Time',
              color: colors.textColor
            },
            tooltip: {
              callbacks: {
                title: function(tooltipItems) {
                  return `Magnitude: ${tooltipItems[0].parsed.y.toFixed(2)}`;
                },
                afterTitle: function(tooltipItems) {
                  const uncertainty = tooltipItems[0].raw.uncertainty;
                  const date = new Date(tooltipItems[0].parsed.x).toLocaleDateString();
                  return [`Uncertainty: ${uncertainty}`, `Date: ${date}`, `Number of points: ${tooltipItems.length}`];
                },
                label: function(context) {
                  return null; // This removes individual point labels
                },
              },
              displayColors: false, // This removes the color boxes for individual points
              titleFont: {
                  weight: "normal"
              }
            },
            zoom: {
              zoom: {
                wheel: {
                  enabled: true,
                },
                pinch: {
                  enabled: true
                },
                mode: 'xy',
              },
              pan: {
                enabled: true,
                mode: 'xy',
              }
            }
          },
        }
      }
    );

    console.log('Brightness chart created:', brightnessChart);
    return brightnessChart;
  }

  // Phase Angle vs Brightness chart
  let phaseAngleChart;
  let phaseAngleDataMin = null; // To store the minimum value of phase angle data
  let phaseAngleDataMax = null; // To store the maximum value of phase angle data

  function createPhaseAngleChart() {
    const theme = getCurrentTheme();
    const colors = colorSchemes[theme];

    if (phaseAngleChart) {
      phaseAngleChart.destroy();
    }

    console.log('Creating phase angle chart with data:', phase_angle_data);

    // Calculate the min and max values from the data
    phaseAngleDataMin = Math.floor(Math.min(...phase_angle_data.map(item => item.x))) - 5;
    phaseAngleDataMax = Math.floor(Math.max(...phase_angle_data.map(item => item.x))) + 5;

    phaseAngleChart = new Chart(
      document.getElementById('phase_angle_chart'),
      {
        type: 'lineWithErrorBars',
        data: {
          datasets: [{
            label: 'Satellite Brightness vs Phase Angle',
            data: phase_angle_data.map(item => ({
              x: item.x,
              y: item.y,
              yMin: item.y - item.uncertainty,
              yMax: item.y + item.uncertainty,
              date: item.date,
              uncertainty: item.uncertainty
            })),
            backgroundColor: colors.backgroundColor,
            borderColor: colors.borderColor,
            borderDash: [1, 1],
            pointRadius: 3,
            borderWidth: 1,
            errorBarColor: colors.errorBarColor,
            errorBarWidth: 3,
            errorBarWhiskerColor: colors.errorBarColor,
            errorBarWhiskerSize: 5
          }]
        },
        options: {
          responsive: true,
          scales: {
            x: {
              type: 'linear',
              min: 0,
              max: 180,
              title: {
                display: true,
                text: 'Phase Angle (degrees)',
                color: colors.textColor
              },
              grid: {
                color: colors.gridColor
              },
              ticks: {
                color: colors.textColor,
                stepSize: 15
              }
            },
            y: {
              reverse: true,
              title: {
                display: true,
                text: 'Magnitude',
                color: colors.textColor
              },
              grid: {
                color: colors.gridColor
              },
              ticks: {
                color: colors.textColor
              }
            }
          },
          plugins: {
            legend: {
              display: false
            },
            title: {
              display: true,
              text: 'Satellite Brightness vs Phase Angle',
              color: colors.textColor
            },
            tooltip: {
              callbacks: {
                title: function(tooltipItems) {
                  return `Magnitude: ${tooltipItems[0].parsed.y.toFixed(2)}`;
                },
                afterTitle: function(tooltipItems) {
                  const date = tooltipItems[0].raw.date.toLocaleDateString();
                  return [
                    `Uncertainty: ${tooltipItems[0].raw.uncertainty}`,
                    `Phase Angle: ${tooltipItems[0].parsed.x.toFixed(2)}°`,
                    `Date: ${date}`,
                    `Number of points: ${tooltipItems.length}`,
                  ];
                },
                label: function(context) {
                  return null;
                },
              },
              displayColors: false,
              titleFont: {
                  weight: "normal"
              }
            },
            zoom: {
              zoom: {
                wheel: {
                  enabled: true,
                },
                pinch: {
                  enabled: true
                },
                mode: 'xy',
              },
              pan: {
                enabled: true,
                mode: 'xy',

              },
            }
          },

        }
      }
    );

    console.log('Phase angle chart created:', phaseAngleChart);
    return phaseAngleChart;
  }

  function updateCharts() {
    console.log('Updating charts. Current theme:', getCurrentTheme());
    brightnessChart = createBrightnessChart();
    phaseAngleChart = createPhaseAngleChart();
  }

  // Reset handling
  document.getElementById('reset_zoom_brightness').addEventListener('click', () => {
    brightnessChart.resetZoom();
  });

  document.getElementById('reset_zoom_phase').addEventListener('click', () => {
    phaseAngleChart.resetZoom();
  });

  // Handle theming
  console.log('DOM content loaded. Initial theme:', getCurrentTheme());
  updateCharts();

  document.querySelectorAll('[data-bs-theme-value]').forEach(toggle => {
    toggle.addEventListener('click', () => {
      console.log('Theme toggle clicked');
      setTimeout(() => {
        console.log('Delayed update. Current theme:', getCurrentTheme());
        updateCharts();
      }, 100);
    });
  });

  document.getElementById('toggle_data_range').addEventListener('change', function() {
    const useDataRange = this.checked;

    if (useDataRange) {
      // Set min/max to data range
      phaseAngleChart.options.scales.x.min = phaseAngleDataMin;
      phaseAngleChart.options.scales.x.max = phaseAngleDataMax;
    } else {
      // default
      phaseAngleChart.options.scales.x.min = 0;
      phaseAngleChart.options.scales.x.max = 180;
    }

    phaseAngleChart.update();
  });
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
    errorBarColor: 'rgba(20, 41, 67, .5)'  // primary color with 50% opacity
  },
  dark: {
    backgroundColor: 'rgba(255, 193, 7, 1)',
    borderColor: 'rgba(255, 193, 7, 1)',
    gridColor: 'rgba(255, 255, 255, 0.1)',
    textColor: '#ccc',
    errorBarColor: 'rgba(255, 193, 7, .5)'  // primary color with 50% opacity
  }
};

// Listen for theme changes
const observer = new MutationObserver((mutations) => {
  mutations.forEach((mutation) => {
    if (mutation.type === 'attributes' && mutation.attributeName === 'data-bs-theme') {
      updateCharts();
    }
  });
});

observer.observe(document.documentElement, {
  attributes: true,
  attributeFilter: ['data-bs-theme']
});
