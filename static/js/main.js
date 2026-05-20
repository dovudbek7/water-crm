const sidebar = document.getElementById('sidebar');
const overlay = document.getElementById('sidebarOverlay');
const menuBtn = document.getElementById('menuBtn');

if (menuBtn && sidebar && overlay) {
  menuBtn.addEventListener('click', () => {
    sidebar.classList.toggle('open');
    overlay.classList.toggle('show');
  });

  overlay.addEventListener('click', () => {
    sidebar.classList.remove('open');
    overlay.classList.remove('show');
  });
}

document.querySelectorAll('form[enctype="multipart/form-data"]').forEach((form) => {
  const fileInputs = Array.from(form.querySelectorAll('input[type="file"]'));
  if (!fileInputs.length) {
    return;
  }

  form.addEventListener('submit', () => {
    if (form.dataset.uploading === 'true') {
      return;
    }

    form.dataset.uploading = 'true';

    const submitButton = form.querySelector('button[type="submit"], input[type="submit"]');
    if (submitButton) {
      submitButton.disabled = true;
      submitButton.classList.add('btn-loading');
      submitButton.innerHTML = '<span class="button-spinner" aria-hidden="true"></span><span>Юкланмоқда...</span>';
    }
  });
});
