// static/js/admin_dashboard.js
document.addEventListener('DOMContentLoaded', function () {
    const ctxCity = document.getElementById('cityUsageChart');
    if (ctxCity) {
        new Chart(ctxCity, {
            type: 'bar',
            data: {
                labels: JSON.parse(ctxCity.getAttribute('data-labels')),
                datasets: [{
                    label: 'Total Consumption (kWh)',
                    data: JSON.parse(ctxCity.getAttribute('data-values')),
                    backgroundColor: 'rgba(231, 76, 60, 0.5)',
                    borderColor: 'rgba(231, 76, 60, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
});