const input = document.getElementById('q');
const count = document.getElementById('count');
const grid = document.querySelector('.grid');
const cells = Array.from(grid.querySelectorAll('a'));
const viewButtons = document.querySelectorAll('.views button');
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

// keep the query in the URL so searches can be shared and survive Back;
// post pages read it back from sessionStorage for their "index" link
function remember(q) {
  const url = new URL(location.href);
  if (q.trim()) url.searchParams.set('q', q.trim());
  else url.searchParams.delete('q');
  history.replaceState(null, '', url);
  try { sessionStorage.setItem('indexSearch', url.search); } catch (e) {}
}

async function run(q) {
  await loadIndex();
  apply(q);
}

input.addEventListener('input', () => {
  clearTimeout(pending);
  pending = setTimeout(() => {
    remember(input.value);
    run(input.value);
  }, 150);
});

// start fetching the index as soon as someone reaches for the search box
input.addEventListener('focus', loadIndex, { once: true });

const initial = new URLSearchParams(location.search).get('q');
if (initial) {
  input.value = initial;
  remember(initial);
  run(initial);
} else {
  remember('');
}

function setView(view) {
  grid.classList.toggle('list', view === 'list');
  viewButtons.forEach(b => b.setAttribute('aria-pressed', String(b.dataset.view === view)));
}

viewButtons.forEach(b => b.addEventListener('click', () => {
  setView(b.dataset.view);
  try { localStorage.setItem('view', b.dataset.view); } catch (e) {}
}));

try { setView(localStorage.getItem('view') || 'grid'); } catch (e) {}
