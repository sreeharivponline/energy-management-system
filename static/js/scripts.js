// static/js/scripts.js
document.addEventListener('DOMContentLoaded', function () {
    // Initialize charts
    const ctxConsumption = document.getElementById('consumptionChart');
    const ctxCost = document.getElementById('costChart');
    if (ctxConsumption) {
        new Chart(ctxConsumption, {
            type: 'bar',
            data: {
                labels: JSON.parse(ctxConsumption.getAttribute('data-labels')),
                datasets: [{
                    label: 'Consumption (kWh)',
                    data: JSON.parse(ctxConsumption.getAttribute('data-values')),
                    backgroundColor: 'rgba(46, 204, 113, 0.5)',
                    borderColor: 'rgba(46, 204, 113, 1)',
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
    if (ctxCost) {
        new Chart(ctxCost, {
            type: 'bar',
            data: {
                labels: JSON.parse(ctxCost.getAttribute('data-labels')),
                datasets: [{
                    label: 'Cost (₹)',
                    data: JSON.parse(ctxCost.getAttribute('data-values')),
                    backgroundColor: 'rgba(52, 152, 219, 0.5)',
                    borderColor: 'rgba(52, 152, 219, 1)',
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

    // Flash message auto-hide
    const flashMessages = document.querySelectorAll('.flash');
    flashMessages.forEach(msg => {
        setTimeout(() => msg.style.display = 'none', 5000);
    });
});