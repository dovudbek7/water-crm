const mapEl = document.getElementById('mapPicker');
const latInput = document.getElementById('id_latitude');
const lngInput = document.getElementById('id_longitude');
const linkInput = document.getElementById('id_map_link');
const modeInputs = document.querySelectorAll('input[name="location_mode"]');
const mapPanel = document.getElementById('mapPanel');
const linkPanel = document.getElementById('linkPanel');
const currentBtn = document.getElementById('mapCurrentLocation');
const fullscreenBtn = document.getElementById('mapFullscreen');
const closeBtn = document.getElementById('mapClose');
const mapShell = document.getElementById('mapShell');

if (mapEl && typeof L !== 'undefined') {
  const initLat = parseFloat(latInput?.value || 41.2995);
  const initLng = parseFloat(lngInput?.value || 69.2401);

  const map = L.map(mapEl).setView([initLat, initLng], 12);
  const googleLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors',
  });
  const yandexLayer = L.tileLayer('https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors',
  });
  yandexLayer.addTo(map);

  let marker = L.marker([initLat, initLng]).addTo(map);

  map.on('click', (e) => {
    const { lat, lng } = e.latlng;
    marker.setLatLng([lat, lng]);
    if (latInput) latInput.value = lat.toFixed(6);
    if (lngInput) lngInput.value = lng.toFixed(6);
    if (closeBtn) closeBtn.style.display = 'inline-flex';
  });

  function setMode(mode) {
    document.querySelectorAll('.map-mode-card').forEach((card) => {
      card.classList.toggle('active', card.dataset.mode === mode);
    });

    if (mode === 'link') {
      linkPanel?.classList.remove('hidden');
      mapPanel?.classList.add('hidden');
      return;
    }

    linkPanel?.classList.add('hidden');
    mapPanel?.classList.remove('hidden');

    if (mode === 'google') {
      if (map.hasLayer(yandexLayer)) map.removeLayer(yandexLayer);
      if (!map.hasLayer(googleLayer)) googleLayer.addTo(map);
    } else {
      if (map.hasLayer(googleLayer)) map.removeLayer(googleLayer);
      if (!map.hasLayer(yandexLayer)) yandexLayer.addTo(map);
    }
    map.invalidateSize();
  }

  modeInputs.forEach((radio) => {
    radio.addEventListener('change', () => setMode(radio.value));
  });
  setMode(document.querySelector('input[name="location_mode"]:checked')?.value || 'yandex');

  currentBtn?.addEventListener('click', () => {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition((pos) => {
      const { latitude, longitude } = pos.coords;
      map.setView([latitude, longitude], 15);
      marker.setLatLng([latitude, longitude]);
      if (latInput) latInput.value = latitude.toFixed(6);
      if (lngInput) lngInput.value = longitude.toFixed(6);
      if (closeBtn) closeBtn.style.display = 'inline-flex';
    });
  });

  fullscreenBtn?.addEventListener('click', () => {
    mapShell?.classList.toggle('fullscreen');
    setTimeout(() => map.invalidateSize(), 220);
  });

  closeBtn?.addEventListener('click', () => {
    mapPanel?.classList.add('hidden');
  });

  if (linkInput && linkInput.value && !latInput?.value && !lngInput?.value) {
    const linkRadio = document.querySelector('input[name="location_mode"][value="link"]');
    if (linkRadio) {
      linkRadio.checked = true;
      setMode('link');
    }
  }
}
