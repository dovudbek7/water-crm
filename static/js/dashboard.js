if (typeof Chart !== 'undefined') {
  const monthlyCtx = document.getElementById('monthlySalesChart');
  const topCtx = document.getElementById('topProductsChart');

  if (monthlyCtx) {
    new Chart(monthlyCtx, {
      type: 'line',
      data: {
        labels: monthlyLabels,
        datasets: [{
          label: 'Savdo',
          data: monthlyValues,
          borderColor: '#2487ea',
          backgroundColor: 'rgba(36, 135, 234, 0.18)',
          fill: true,
          tension: 0.35
        }]
      }
    });
  }

  if (topCtx) {
    new Chart(topCtx, {
      type: 'bar',
      data: {
        labels: topLabels,
        datasets: [{
          label: 'Sotilgan dona',
          data: topValues,
          backgroundColor: ['#2487ea', '#4ca2f6', '#73b9fb', '#9ed0ff', '#c2e4ff', '#d7edff']
        }]
      },
      options: {
        plugins: {
          legend: { display: false }
        }
      }
    });
  }
}
