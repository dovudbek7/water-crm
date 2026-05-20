const orderModal = document.getElementById('orderModal');
const closeBackdrop = document.getElementById('orderModalCloseBackdrop');
const closeBtn = document.getElementById('orderModalClose');
const viewButtons = document.querySelectorAll('.view-order-btn');

const modalShopName = document.getElementById('modalShopName');
const modalOrderDate = document.getElementById('modalOrderDate');
const modalItemsBody = document.querySelector('#modalItemsTable tbody');
const modalTotalAmount = document.getElementById('modalTotalAmount');
const modalPaidAmount = document.getElementById('modalPaidAmount');
const modalRemainAmount = document.getElementById('modalRemainAmount');
const modalExportPdf = document.getElementById('modalExportPdf');
const modalExportExcel = document.getElementById('modalExportExcel');

function formatSom(value) {
  return `${Number(value || 0).toLocaleString('en-US')} so'm`;
}

function orderBalanceLabel(value) {
  const amount = Number(value || 0);
  if (amount > 0) {
    return `↓ -${formatSom(Math.abs(amount))}`;
  }
  if (amount < 0) {
    return `↑ +${formatSom(Math.abs(amount))}`;
  }
  return `• ${formatSom(0)}`;
}

function orderBalanceClass(value) {
  const amount = Number(value || 0);
  if (amount > 0) return 'balance-down';
  if (amount < 0) return 'balance-up';
  return 'balance-neutral';
}

function openModal() {
  if (orderModal) orderModal.classList.add('show');
}

function closeModal() {
  if (orderModal) orderModal.classList.remove('show');
}

async function loadOrder(url) {
  const response = await fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
  if (!response.ok) return;
  const data = await response.json();

  modalShopName.value = data.shop_name;
  modalOrderDate.value = data.order_date;
  modalTotalAmount.textContent = formatSom(data.total_amount);
  modalPaidAmount.textContent = formatSom(data.paid_amount);
  modalRemainAmount.textContent = orderBalanceLabel(data.remaining_balance);
  modalRemainAmount.classList.remove('balance-down', 'balance-up', 'balance-neutral');
  modalRemainAmount.classList.add(orderBalanceClass(data.remaining_balance));

  modalExportPdf.href = data.export_pdf_url;
  modalExportExcel.href = data.export_excel_url;

  if (!data.items.length) {
    modalItemsBody.innerHTML = '<tr><td colspan="4">Mahsulotlar topilmadi.</td></tr>';
  } else {
    modalItemsBody.innerHTML = data.items
      .map((item) => `
        <tr>
          <td>${item.product}</td>
          <td>${Number(item.quantity).toLocaleString('en-US')}</td>
          <td>${formatSom(item.price)}</td>
          <td>${formatSom(item.subtotal)}</td>
        </tr>
      `)
      .join('');
  }

  openModal();
}

viewButtons.forEach((btn) => {
  btn.addEventListener('click', () => {
    const detailUrl = btn.dataset.detailUrl;
    if (detailUrl) loadOrder(detailUrl);
  });
});

closeBtn?.addEventListener('click', closeModal);
closeBackdrop?.addEventListener('click', closeModal);
