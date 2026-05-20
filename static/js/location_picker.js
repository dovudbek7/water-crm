const locationSheet = document.getElementById('locationSheet');
const locationSheetBackdrop = document.getElementById('locationSheetBackdrop');
const locationSheetClose = document.getElementById('locationSheetClose');
const locationSheetGoogle = document.getElementById('locationSheetGoogle');
const locationSheetYandex = document.getElementById('locationSheetYandex');

function closeLocationSheet() {
  locationSheet?.classList.remove('show');
}

function openLocationSheet(googleUrl, yandexUrl) {
  if (!locationSheet || !locationSheetGoogle || !locationSheetYandex) return;
  locationSheetGoogle.style.display = googleUrl ? 'inline-flex' : 'none';
  locationSheetYandex.style.display = yandexUrl ? 'inline-flex' : 'none';
  locationSheetGoogle.href = googleUrl || '#';
  locationSheetYandex.href = yandexUrl || '#';
  locationSheet.classList.add('show');
}

window.openLocationSheet = openLocationSheet;

document.querySelectorAll('.js-location-picker').forEach((button) => {
  button.addEventListener('click', () => {
    openLocationSheet(button.dataset.googleUrl || '', button.dataset.yandexUrl || '');
  });
});

locationSheetBackdrop?.addEventListener('click', closeLocationSheet);
locationSheetClose?.addEventListener('click', closeLocationSheet);
