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
  new Chart(
    document.getElementById('brightness_chart'),
    {
      type: 'scatter',
      data: {
        datasets: [{
          data: brightness_data.map(row => ({
            x: row.date,
            y: row.magnitude
          })),
          backgroundColor: 'rgba(20, 41, 67, 1)',
          borderColor: 'rgba(20, 41, 67, 1)',
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
              text: 'Date'
            }
          },
          y: {
            reverse: true, // Reverse y-axis (lower magnitude = brighter)
            title: {
              display: true,
              text: 'Magnitude'
            }
          }
        },
        plugins: {
          legend: {
            display: false
          },
          title: {
            display: true,
            text: 'Satellite Brightness Over Time'
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

  // Phase Angle vs Brightness chart
  new Chart(
    document.getElementById('phase_angle_chart'),
    {
      type: 'line',
      data: {
        datasets: [{
          label: 'Satellite Brightness vs Phase Angle',
          data: phase_angle_data,
          backgroundColor: 'rgba(20, 41, 67, 1)',
          borderColor: 'rgba(20, 41, 67, 1)',
          pointRadius: 3,  // Adjust point size as needed
        }]
      },
      options: {
        responsive: true,
        scales: {
          x: {
            type: 'linear',
            title: {
              display: true,
              text: 'Phase Angle'
            }
          },
          y: {
            reverse: true,
            title: {
              display: true,
              text: 'Magnitude'
            }
          }
        },
        plugins: {
          legend: {
            display: false
          },
          title: {
            display: true,
            text: 'Satellite Brightness vs Phase Angle'
          },
          tooltip: {
            callbacks: {
              title: function(tooltipItems) {
                return `Magnitude: ${tooltipItems[0].parsed.y.toFixed(2)}`;
              },
              afterTitle: function(tooltipItems) {
                const date = tooltipItems[0].raw.date.toLocaleDateString();
                return [
                  `Phase Angle: ${tooltipItems[0].parsed.x.toFixed(2)}`,
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
});
