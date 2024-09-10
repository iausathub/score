document.addEventListener('DOMContentLoaded', function() {
  // Parse the dates and sort the data
  const observationData = JSON.parse(document.getElementById('observations-data').textContent);
  const brightness_data = observationData
    .filter(item => item.magnitude !== null)
    .map(item => ({
      date: new Date(item.date),
      magnitude: item.magnitude
    }))
    .sort((a, b) => a.date - b.date);

  const phase_angle_data = observationData
    .filter(item => item.magnitude !== null && item.phase_angle !== null)
    .map(item => ({
      x: item.phase_angle,
      y: item.magnitude,
      label: item.date
    }))
    .sort((a, b) => a.x - b.x);

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
            text: 'Satellite Brightness Over Time'
          },
          tooltip: {
            callbacks: {
              label: function(context) {
                return [
                  `Magnitude: ${context.parsed.y.toFixed(2)}`,
                ];
              }
            }
          }
        }
      }
    }
  );

  // phase angle vs brightness
  new Chart(
    document.getElementById('phase_angle_chart'),
    {
      type: 'line',
      data: {
        datasets: [{
          label: 'Satellite Brightness vs Phase Angle',
          data: phase_angle_data,
          borderColor: 'rgba(20, 41, 67, 1)',
          backgroundColor: 'rgba(20, 41, 67, 0.1)',
          tension: 0.1
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
              label: function(context) {
                return [
                  `Magnitude: ${context.parsed.y.toFixed(2)}`,
                  `Phase Angle: ${context.parsed.x.toFixed(2)}`,
                  `Date: ${context.raw.label}`
                ];
              }
            }
          }
        }
      }
    }
  );
});
