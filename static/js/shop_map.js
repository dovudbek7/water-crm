const mapEl = document.getElementById('mapPicker');
const latInput = document.getElementById('id_latitude');
const lngInput = document.getElementById('id_longitude');
const currentBtn = document.getElementById('mapCurrentLocation');
const locationText = document.getElementById('mapLocationText');

if (mapEl && latInput && lngInput && typeof L !== 'undefined') {
  const fallbackLat = 41.311081;
  const fallbackLng = 69.240562;
  const startLat = Number.parseFloat(latInput.value || fallbackLat);
  const startLng = Number.parseFloat(lngInput.value || fallbackLng);

  const map = L.map(mapEl).setView([startLat, startLng], 13);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors',
  }).addTo(map);

  let marker = L.marker([startLat, startLng]).addTo(map);

  function setPoint(lat, lng) {
    marker.setLatLng([lat, lng]);
    latInput.value = lat.toFixed(6);
    lngInput.value = lng.toFixed(6);
    if (locationText) {
      locationText.textContent = `Tanlangan nuqta: ${lat.toFixed(6)}, ${lng.toFixed(6)}`;
    }
  }

  setPoint(startLat, startLng);

  map.on('click', (e) => {
    setPoint(e.latlng.lat, e.latlng.lng);
  });

  currentBtn?.addEventListener('click', () => {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition((position) => {
      const lat = position.coords.latitude;
      const lng = position.coords.longitude;
      map.setView([lat, lng], 16);
      setPoint(lat, lng);
    });
  });
}
