document.addEventListener('DOMContentLoaded', function() {
  const observationData = JSON.parse(document.getElementById('observations-data').textContent);

  // Set up data for the brightness chart
  const brightness_data = observationData
    .filter(item => item.magnitude !== null)
    .map(item => ({
      date: new Date(item.date),
      magnitude: item.magnitude
    }))
    .sort((a, b) => a.date - b.date);

  // Set up data for the phase angle chart
  const phase_angle_data = observationData
    .filter(item => item.magnitude !== null && item.phase_angle !== null)
    .map(item => ({
      x: item.phase_angle,
      y: item.magnitude,
      date: new Date(item.date)  // Store the date for tooltip
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

    brightnessChart = new Chart(
      document.getElementById('brightness_chart'),
      {
        type: 'scatter',
        data: {
          datasets: [{
            data: brightness_data.map(row => ({
              x: row.date,
              y: row.magnitude
            })),
            backgroundColor: colors.backgroundColor,
            borderColor: colors.borderColor,
            tension: 0.1
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
                  const date = new Date(tooltipItems[0].parsed.x).toLocaleDateString();
                  return [`Date: ${date}`, `Number of points: ${tooltipItems.length}`];
                },
                label: function(context) {
                  return null; // This removes individual point labels
                },
              },
              displayColors: false, // This removes the color boxes for individual points
              titleFont: {
                  weight: "normal"
              }
            }
          }
        }
      }
    );
    return brightnessChart;
  }

  // Phase Angle vs Brightness chart
  let phaseAngleChart;

  function createPhaseAngleChart() {
    const theme = getCurrentTheme();
    const colors = colorSchemes[theme];

    if (phaseAngleChart) {
      phaseAngleChart.destroy();
    }

    phaseAngleChart = new Chart(
      document.getElementById('phase_angle_chart'),
      {
        type: 'line',
        data: {
          datasets: [{
            label: 'Satellite Brightness vs Phase Angle',
            data: phase_angle_data,
            backgroundColor: colors.backgroundColor,
            borderColor: colors.borderColor,
            pointRadius: 3,  // Adjust point size as needed
          }]
        },
        options: {
          responsive: true,
          scales: {
            x: {
              type: 'linear',
              min: 0,  // Set minimum value to 0
              max: 180,  // Set maximum value to 180
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
                stepSize: 30  // This will create ticks at 0, 30, 60, 90, 120, 150, 180
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
                    `Phase Angle: ${tooltipItems[0].parsed.x.toFixed(2)}°`,
                    `Date: ${date}`,
                    `Number of points: ${tooltipItems.length}`
                  ];
                },
                label: function(context) {
                  return null;  // This removes individual point labels
                },
              },
              displayColors: false,
              titleFont: {
                  weight: "normal"
              }
            }
          }
        }
      }
    );
    return phaseAngleChart;
  }

  function updateCharts() {
    console.log('Updating charts. Current theme:', getCurrentTheme());
    brightnessChart = createBrightnessChart();
    phaseAngleChart = createPhaseAngleChart();
  }

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
});

function getCurrentTheme() {
  return document.documentElement.getAttribute('data-bs-theme') || 'light';
}

const colorSchemes = {
  light: {
    backgroundColor: 'rgba(20, 41, 67, 1)',
    borderColor: 'rgba(20, 41, 67, 1)',
    gridColor: 'rgba(0, 0, 0, 0.1)',
    textColor: '#666'
  },
  dark: {
    backgroundColor: 'rgba(255, 193, 7, 1)',
    borderColor: 'rgba(255, 193, 7, 1)',
    gridColor: 'rgba(255, 255, 255, 0.1)',
    textColor: '#ccc'
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
