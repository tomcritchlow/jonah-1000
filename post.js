// ←/→ step through posts
document.addEventListener('keydown', e => {
  if (e.altKey || e.ctrlKey || e.metaKey || e.shiftKey) return;
  if (e.target.closest('input, textarea, select, [contenteditable]')) return;
  const rel = { ArrowLeft: 'prev', ArrowRight: 'next' }[e.key];
  const link = rel && document.querySelector(`nav a[rel="${rel}"]`);
  if (link) location.href = link.href;
});

// send "index" back to the search the reader came from
try {
  const search = sessionStorage.getItem('indexSearch');
  if (search) {
    document.querySelectorAll('nav a.home').forEach(a => {
      const url = new URL(a.href);
      url.search = search;
      a.href = url;
    });
  }
} catch (e) {}
