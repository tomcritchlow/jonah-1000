const input = document.getElementById('q');
const count = document.getElementById('count');
const cells = Array.from(document.querySelectorAll('.grid a'));
let pending = null;
let loading = null;

// search-data.js defines window.SEARCH_INDEX; injected as a script tag
// (not fetch) so search also works when the site is opened from file://
function loadIndex() {
  if (window.SEARCH_INDEX) return Promise.resolve();
  if (!loading) {
    loading = new Promise((resolve, reject) => {
      const s = document.createElement('script');
      s.src = 'search-data.js';
      s.onload = resolve;
      s.onerror = reject;
      document.head.appendChild(s);
    });
  }
  return loading;
}

function apply(q) {
  q = q.trim().toLowerCase();
  if (!q) {
    cells.forEach(c => c.classList.remove('hide'));
    count.textContent = '';
    return;
  }
  const terms = q.split(/\s+/);
  let shown = 0;
  cells.forEach((c, i) => {
    const hay = window.SEARCH_INDEX[i];
    const ok = terms.every(t => hay.includes(t));
    c.classList.toggle('hide', !ok);
    if (ok) shown++;
  });
  count.textContent = shown + ' post' + (shown === 1 ? '' : 's');
}

input.addEventListener('input', () => {
  clearTimeout(pending);
  pending = setTimeout(async () => {
    await loadIndex();
    apply(input.value);
  }, 150);
});
