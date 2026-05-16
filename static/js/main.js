// ── Sidebar Drawer ────────────────────────────────────────────────────────
function openSidebar() {
  document.getElementById('sidebarDrawer')?.classList.add('open');
  document.getElementById('sidebarOverlay')?.classList.add('open');
  document.body.style.overflow = 'hidden';
}
function closeSidebar() {
  document.getElementById('sidebarDrawer')?.classList.remove('open');
  document.getElementById('sidebarOverlay')?.classList.remove('open');
  document.body.style.overflow = '';
}

document.getElementById('hamburger')?.addEventListener('click', openSidebar);
document.getElementById('sidebarClose')?.addEventListener('click', closeSidebar);
document.getElementById('sidebarOverlay')?.addEventListener('click', closeSidebar);
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeSidebar(); });

// Close search dropdown on outside click
document.addEventListener('click', e => {
  if (!e.target.closest('.search-wrap')) {
    document.getElementById('searchDropdown')?.classList.remove('open');
  }
});

// Global search
let searchTimer = null;
const gSearch = document.getElementById('globalSearch');
const gDrop   = document.getElementById('searchDropdown');

gSearch?.addEventListener('input', () => {
  clearTimeout(searchTimer);
  const q = gSearch.value.trim();
  if (q.length < 2) { gDrop.classList.remove('open'); gDrop.innerHTML=''; return; }
  searchTimer = setTimeout(() => liveSearch(q), 420);
});
gSearch?.addEventListener('keydown', e => {
  if (e.key === 'Enter') {
    const q = gSearch.value.trim();
    if (q) location.href = `/search?q=${encodeURIComponent(q)}`;
  }
  if (e.key === 'Escape') gDrop.classList.remove('open');
});

async function liveSearch(q) {
  gDrop.innerHTML = `<div class="search-empty"><i class="fa fa-spinner fa-spin"></i> Mencari...</div>`;
  gDrop.classList.add('open');
  try {
    const j = await (await fetch(`/api/search/${encodeURIComponent(q)}`)).json();
    const list = j?.data?.animeList || [];
    if (!list.length) { gDrop.innerHTML = `<div class="search-empty">Tidak ditemukan.</div>`; return; }
    gDrop.innerHTML = list.slice(0,7).map(a => `
      <div class="search-item" onclick="location.href='/anime/${a.animeId}'">
        <img src="${a.poster}" onerror="this.src='/static/img/no-img.svg'"/>
        <div>
          <div class="search-item-title">${a.title}</div>
          <div class="search-item-meta">${a.status||''} ${a.score?'⭐'+a.score:''}</div>
        </div>
      </div>`).join('');
  } catch { gDrop.innerHTML = `<div class="search-empty">Gagal mencari.</div>`; }
}

// ── Helpers ──────────────────────────────────────────────────────────────

/** Render poster cards into a container el */
function renderCards(list, el) {
  if (!list?.length) { el.innerHTML = `<div class="loading">Tidak ada data.</div>`; return; }
  el.innerHTML = list.map(a => `
    <div class="a-card" onclick="location.href='/anime/${a.animeId}'">
      <div class="a-card-poster">
        <img src="${a.poster}" loading="lazy" onerror="this.src='/static/img/no-img.svg'" alt="${a.title}"/>
        ${a.episodes ? `<div class="a-card-ep">Ep ${a.episodes}</div>` : ''}
      </div>
      <div class="a-card-info">
        <div class="a-card-title">${a.title}</div>
        <div class="a-card-meta">
          ${a.score ? `<span class="a-card-score">⭐${a.score}</span>` : ''}
          ${a.releaseDay||''}
        </div>
      </div>
    </div>`).join('');
}

function renderSkels(el, n=12) {
  el.innerHTML = Array(n).fill(`
    <div>
      <div class="skeleton skel-poster"></div>
      <div class="skeleton skel-line" style="width:85%"></div>
      <div class="skeleton skel-line w50"></div>
    </div>`).join('');
}

/** synopsis: obj with {paragraphs:[...]} OR plain string */
function parseSynopsis(synopsis) {
  if (!synopsis) return 'Tidak ada sinopsis.';
  if (typeof synopsis === 'string') return `<p>${synopsis}</p>`;
  if (Array.isArray(synopsis)) return synopsis.filter(Boolean).map(p=>`<p>${p}</p>`).join('');
  if (synopsis.paragraphs) return (synopsis.paragraphs||[]).filter(Boolean).map(p=>`<p>${p}</p>`).join('') || 'Tidak ada sinopsis.';
  return 'Tidak ada sinopsis.';
}

/** Render pagination */
function renderPagination(el, current, total, onPage) {
  if (total <= 1) { el.innerHTML=''; return; }
  let h = `<button class="page-btn" onclick="(${onPage})(${current-1})" ${current===1?'disabled':''}><i class="fa fa-chevron-left"></i></button>`;
  for (let i=1;i<=total;i++) {
    if (i===1||i===total||(i>=current-2&&i<=current+2))
      h += `<button class="page-btn ${i===current?'active':''}" onclick="(${onPage})(${i})">${i}</button>`;
    else if (i===current-3||i===current+3)
      h += `<span class="page-btn" style="pointer-events:none">…</span>`;
  }
  h += `<button class="page-btn" onclick="(${onPage})(${current+1})" ${current===total?'disabled':''}><i class="fa fa-chevron-right"></i></button>`;
  el.innerHTML = h;
}

window.renderCards = renderCards;
window.renderSkels = renderSkels;
window.parseSynopsis = parseSynopsis;
window.renderPagination = renderPagination;

/* ── Info Popups ────────────────────────────────────────────── */
(function() {
  const overlay = document.getElementById('popupOverlay');
  if (!overlay) return;

  function openPopup(id) {
    const modal = document.getElementById('popup-' + id);
    if (!modal) return;
    overlay.classList.add('open');
    modal.classList.add('open');
    document.body.style.overflow = 'hidden';
  }

  function closeAll() {
    overlay.classList.remove('open');
    document.querySelectorAll('.popup-modal.open').forEach(m => m.classList.remove('open'));
    document.body.style.overflow = '';
  }

  // open on trigger click
  document.querySelectorAll('.popup-trigger').forEach(function(el) {
    el.addEventListener('click', function(e) {
      e.preventDefault();
      openPopup(this.dataset.popup);
    });
  });

  // close on X button
  document.querySelectorAll('.popup-close').forEach(function(btn) {
    btn.addEventListener('click', closeAll);
  });

  // close on overlay click
  overlay.addEventListener('click', closeAll);

  // close on ESC
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') closeAll();
  });
})();

// ── Dark / Light Mode ─────────────────────────────────────────────────────
(function() {
  var root = document.getElementById('htmlRoot');
  var btn  = document.getElementById('themeToggle');
  var icon = document.getElementById('themeIcon');
  if (!root || !btn) return;

  function applyTheme(dark) {
    if (dark) {
      root.classList.add('dark');
      icon.className = 'fas fa-sun';
    } else {
      root.classList.remove('dark');
      icon.className = 'fas fa-moon';
    }
  }

  // init from localStorage
  var saved = localStorage.getItem('aniryuTheme');
  applyTheme(saved === 'dark');

  btn.addEventListener('click', function() {
    var isDark = root.classList.contains('dark');
    localStorage.setItem('aniryuTheme', isDark ? 'light' : 'dark');
    applyTheme(!isDark);
  });
})();

// ── Bookmark Helpers (localStorage) ──────────────────────────────────────
var BKEY = 'aniryuBookmarks';

function bmGet() {
  try { return JSON.parse(localStorage.getItem(BKEY) || '[]'); } catch(e) { return []; }
}
function bmSave(arr) {
  localStorage.setItem(BKEY, JSON.stringify(arr));
}
function bmHas(id) {
  return bmGet().some(function(a){ return a.animeId === id; });
}
function bmToggle(anime) {
  var arr = bmGet();
  var idx = arr.findIndex(function(a){ return a.animeId === anime.animeId; });
  if (idx >= 0) { arr.splice(idx, 1); } else { arr.unshift(anime); }
  bmSave(arr);
  return idx < 0; // true = added
}

window.bmGet    = bmGet;
window.bmHas    = bmHas;
window.bmToggle = bmToggle;

/** Build bookmark button HTML */
function bmBtnHtml(anime) {
  var has = bmHas(anime.animeId);
  return '<button class="bm-btn ' + (has ? 'active' : '') + '" id="bmBtn" title="' + (has ? 'Hapus Bookmark' : 'Tambah Bookmark') + '">'
       + '<i class="' + (has ? 'fas' : 'far') + ' fa-bookmark"></i>'
       + (has ? ' Tersimpan' : ' Bookmark')
       + '</button>';
}
window.bmBtnHtml = bmBtnHtml;

/** Attach bookmark button click after it's in DOM */
function bmBindBtn(anime) {
  var btn = document.getElementById('bmBtn');
  if (!btn) return;
  btn.addEventListener('click', function() {
    var added = bmToggle(anime);
    btn.classList.toggle('active', added);
    btn.innerHTML = '<i class="' + (added ? 'fas' : 'far') + ' fa-bookmark"></i> ' + (added ? 'Tersimpan' : 'Bookmark');
    btn.title = added ? 'Hapus Bookmark' : 'Tambah Bookmark';
  });
}
window.bmBindBtn = bmBindBtn;
