const monthPicker = document.getElementById('monthPicker');
const tableBody = document.querySelector('#analyticsTable tbody');
const monthSalesText = document.getElementById('monthSalesText');
const exportPdfBtn = document.getElementById('analyticsExportPdf');
const exportExcelBtn = document.getElementById('analyticsExportExcel');

function formatSom(value) {
  return `${Number(value || 0).toLocaleString('en-US')} so'm`;
}

let barChart;
let pieChart;
let lineChart;

function buildCharts(data) {
  const barCtx = document.getElementById('barChart');
  const pieCtx = document.getElementById('pieChart');
  const lineCtx = document.getElementById('lineChart');

  if (barChart) barChart.destroy();
  if (pieChart) pieChart.destroy();
  if (lineChart) lineChart.destroy();

  barChart = new Chart(barCtx, {
    type: 'bar',
    data: {
      labels: data.productLabels,
      datasets: [{ label: 'Sotilgan dona', data: data.productQuantities, backgroundColor: '#2487ea' }]
    }
  });

  pieChart = new Chart(pieCtx, {
    type: 'pie',
    data: {
      labels: data.productLabels,
      datasets: [{ data: data.productRevenues, backgroundColor: ['#2487ea', '#3fa5ff', '#73c0f8', '#90cdf4', '#bfdbfe', '#dbeafe'] }]
    }
  });

  lineChart = new Chart(lineCtx, {
    type: 'line',
    data: {
      labels: data.lineLabels,
      datasets: [{
        label: 'Kunlik savdo',
        data: data.lineValues,
        borderColor: '#16a34a',
        backgroundColor: 'rgba(22, 163, 74, 0.14)',
        fill: true,
        tension: 0.3
      }]
    }
  });
}

function fillTable(rows) {
  if (!tableBody) return;

  if (!rows.length) {
    tableBody.innerHTML = '<tr><td colspan="3">Bu oy ma\'lumot yo\'q.</td></tr>';
    return;
  }

  tableBody.innerHTML = rows.map((row) => `
    <tr>
      <td>${row.name}</td>
      <td>${Number(row.quantity).toLocaleString('en-US')}</td>
      <td>${formatSom(row.revenue)}</td>
    </tr>
  `).join('');
}

function updateExportLinks(month) {
  if (exportPdfBtn) exportPdfBtn.href = `${window.analyticsExportPdfBase}?month=${month}`;
  if (exportExcelBtn) exportExcelBtn.href = `${window.analyticsExportExcelBase}?month=${month}`;
}

async function loadAnalytics(month) {
  const url = `${window.analyticsDataUrl}?month=${month}`;
  const response = await fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
  if (!response.ok) return;

  const data = await response.json();
  monthSalesText.textContent = formatSom(data.month_sales);

  buildCharts({
    productLabels: data.product_labels,
    productQuantities: data.product_quantities,
    productRevenues: data.product_revenues,
    lineLabels: data.line_labels,
    lineValues: data.line_values
  });

  fillTable(data.product_rows);
  updateExportLinks(month);
}

if (typeof Chart !== 'undefined' && window.analyticsInitial) {
  buildCharts(window.analyticsInitial);
}

if (monthPicker) {
  updateExportLinks(monthPicker.value);
  monthPicker.addEventListener('change', (e) => {
    loadAnalytics(e.target.value);
  });
}
