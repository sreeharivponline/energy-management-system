document.addEventListener('DOMContentLoaded', function () {
    const canvas = document.getElementById('forecastChart');
    const labels = JSON.parse(canvas.dataset.dates);
    const values = JSON.parse(canvas.dataset.values);
    const upper = JSON.parse(canvas.dataset.upper);
    const lower = JSON.parse(canvas.dataset.lower);

    new Chart(canvas, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Predicted Usage (kWh)',
                    data: values,
                    borderColor: 'rgba(75, 192, 192, 1)',
                    backgroundColor: 'rgba(75, 192, 192, 0.1)',
                    tension: 0.3,
                },
                {
                    label: 'Upper Bound',
                    data: upper,
                    borderColor: 'rgba(255, 99, 132, 0.5)',
                    borderDash: [5, 5],
                    fill: false,
                },
                {
                    label: 'Lower Bound',
                    data: lower,
                    borderColor: 'rgba(54, 162, 235, 0.5)',
                    borderDash: [5, 5],
                    fill: false,
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: true }
            },
            scales: {
                x: {
                    title: { display: true, text: 'Date' }
                },
                y: {
                    title: { display: true, text: 'kWh' }
                }
            }
        }
    });

    // Raw Data Toggle
    const toggleBtn = document.getElementById('toggleDataBtn');
    const rawData = document.getElementById('rawData');
    toggleBtn.addEventListener('click', () => {
        rawData.style.display = rawData.style.display === 'none' ? 'block' : 'none';
        toggleBtn.textContent = rawData.style.display === 'none' ? 'Show Raw Data' : 'Hide Raw Data';
    });
});
