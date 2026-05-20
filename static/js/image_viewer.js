const viewerModal = document.getElementById('imageViewerModal');
const viewerImg = document.getElementById('imageViewerImage');
const viewerClose = document.getElementById('imageViewerClose');

function openViewer(src) {
  if (!viewerModal || !viewerImg || !src) return;
  viewerImg.src = src;
  viewerModal.classList.add('show');
}

function closeViewer() {
  if (!viewerModal || !viewerImg) return;
  viewerModal.classList.remove('show');
  viewerImg.src = '';
}

document.querySelectorAll('[data-fullscreen-image]').forEach((el) => {
  el.addEventListener('click', () => {
    openViewer(el.getAttribute('data-fullscreen-image') || el.getAttribute('src'));
  });
});

viewerClose?.addEventListener('click', closeViewer);
viewerModal?.addEventListener('click', (e) => {
  if (e.target === viewerModal) closeViewer();
});
