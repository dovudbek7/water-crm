const rowsBody = document.getElementById('itemRows');
const addRowBtn = document.getElementById('addRowBtn');
const totalFormsInput = document.getElementById('id_form-TOTAL_FORMS');
const rowTemplate = document.getElementById('rowTemplate');
const grandTotalInput = document.getElementById('grandTotal');
const remainingTotalInput = document.getElementById('remainingTotal');
const paidAmountInput = document.getElementById('id_paid_amount');

function formatSom(value) {
  return `${Number(value || 0).toLocaleString('en-US')} so'm`;
}

function parseNumber(value) {
  if (value === null || value === undefined) return 0;
  return Number(String(value).replace(/[^\d.-]/g, '')) || 0;
}

function lineTotal(row) {
  const qtyInput = row.querySelector('input[name$="-quantity"]');
  const productSelect = row.querySelector('select[name$="-product"]');
  const priceInput = row.querySelector('.price-input');
  const lineTotalInput = row.querySelector('.line-total-input');

  const price = Number(window.productPrices?.[productSelect?.value] || 0);
  const qty = Number(qtyInput?.value || 0);
  const total = price * qty;

  if (priceInput) priceInput.value = formatSom(price);
  if (lineTotalInput) lineTotalInput.value = formatSom(total);

  return total;
}

function recalc() {
  let sum = 0;
  document.querySelectorAll('.item-row').forEach((row) => {
    const deleteInput = row.querySelector('input[type="checkbox"][name$="-DELETE"]');
    if (deleteInput && deleteInput.checked) return;
    if (row.style.display === 'none') return;
    sum += lineTotal(row);
  });

  if (grandTotalInput) grandTotalInput.value = formatSom(sum);

  const paid = parseNumber(paidAmountInput?.value || 0);
  const remaining = sum - paid;
  if (remainingTotalInput) remainingTotalInput.value = formatSom(remaining);
}

function bindRow(row) {
  const productSelect = row.querySelector('select[name$="-product"]');
  const qtyInput = row.querySelector('input[name$="-quantity"]');
  const removeBtn = row.querySelector('.remove-row');

  productSelect?.addEventListener('change', recalc);
  qtyInput?.addEventListener('input', recalc);

  if (removeBtn) {
    removeBtn.addEventListener('click', () => {
      const deleteInput = row.querySelector('input[type="checkbox"][name$="-DELETE"]');
      if (deleteInput) {
        deleteInput.checked = true;
        row.style.display = 'none';
      } else {
        row.remove();
      }
      recalc();
    });
  }
}

function addRow() {
  if (!totalFormsInput || !rowsBody || !rowTemplate) return;

  const index = Number(totalFormsInput.value);
  const firstProduct = document.getElementById('id_form-0-product');
  const firstQty = document.getElementById('id_form-0-quantity');
  const firstDelete = document.getElementById('id_form-0-DELETE');
  if (!firstProduct || !firstQty || !firstDelete) return;

  const emptyProduct = firstProduct.outerHTML
    .replaceAll('-0-', `-${index}-`)
    .replaceAll('_0_', `_${index}_`)
    .replace(' selected', '');
  const emptyQty = firstQty.outerHTML
    .replaceAll('-0-', `-${index}-`)
    .replaceAll('_0_', `_${index}_`)
    .replace(/value="[^"]*"/g, 'value="1"');
  const emptyDelete = firstDelete.outerHTML
    .replaceAll('-0-', `-${index}-`)
    .replaceAll('_0_', `_${index}_`)
    .replace('checked', '');

  const html = rowTemplate.innerHTML
    .replace('__PRODUCT__', emptyProduct)
    .replace('__QTY__', emptyQty)
    .replace('__DELETE__', emptyDelete);

  rowsBody.insertAdjacentHTML('beforeend', html);
  const newRow = rowsBody.lastElementChild;
  const newProductSelect = newRow.querySelector('select[name$="-product"]');
  if (newProductSelect) {
    newProductSelect.selectedIndex = 0;
  }
  const newQtyInput = newRow.querySelector('input[name$="-quantity"]');
  if (newQtyInput) {
    newQtyInput.value = '1';
  }
  bindRow(newRow);

  totalFormsInput.value = index + 1;
  recalc();
}

if (rowsBody) {
  rowsBody.querySelectorAll('.item-row').forEach(bindRow);
  recalc();
}

paidAmountInput?.addEventListener('input', recalc);
addRowBtn?.addEventListener('click', addRow);
