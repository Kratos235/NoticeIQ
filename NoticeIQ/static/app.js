// NoticeIQ – lightweight vanilla JS (no dependencies)

// ---- Sidebar toggle (mobile) ----
function toggleSidebar() {
  document.querySelector('.sidebar')?.classList.toggle('open');
  document.querySelector('.overlay')?.classList.toggle('show');
}
document.addEventListener('click', function (e) {
  if (e.target.closest('#hamburger')) toggleSidebar();
  if (e.target.closest('#overlay')) toggleSidebar();
});

// ---- "Why this matters" toggle on notice cards ----
document.addEventListener('click', function (e) {
  const btn = e.target.closest('[data-why-toggle]');
  if (btn) {
    const card = btn.closest('.notice-card');
    const box = card?.querySelector('.nc-why');
    if (box) box.classList.toggle('open');
  }
});

// ---- Toasts ----
function showToast(msg, type = 'success') {
  let wrap = document.querySelector('.toast-wrap');
  if (!wrap) {
    wrap = document.createElement('div');
    wrap.className = 'toast-wrap';
    document.body.appendChild(wrap);
  }
  const ok = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M20 6L9 17l-5-5"/></svg>';
  const err = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><circle cx="12" cy="12" r="9"/><path d="M12 8v5M12 16h.01"/></svg>';
  const t = document.createElement('div');
  t.className = 'toast ' + type;
  t.innerHTML = (type === 'error' ? err : ok) +
    '<span class="tmsg">' + msg + '</span>' +
    '<button class="tclose" aria-label="close">&times;</button>';
  wrap.appendChild(t);
  t.querySelector('.tclose').onclick = () => t.remove();
  setTimeout(() => t.remove(), 4200);
}

// Flash messages injected by the server -> toasts
window.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('[data-flash]').forEach(function (el) {
    showToast(el.dataset.flashMsg, el.dataset.flash);
    el.remove();
  });
});

// ---- Save / bookmark ----
async function toggleSave(noticeId, btn) {
  try {
    const r = await fetch('/notice/' + noticeId + '/save', { method: 'POST' });
    const data = await r.json();
    if (data.ok) {
      btn.classList.toggle('chip-teal', data.is_saved);
      btn.textContent = data.is_saved ? '★ Saved' : '☆ Save';
      showToast(data.is_saved ? 'Notice saved to your bookmarks.' : 'Removed from saved.');
    }
  } catch (e) { showToast('Could not update. Try again.', 'error'); }
}

// ---- Delete confirmation ----
function confirmDelete(form, title) {
  if (confirm('Delete "' + title + '"?\nThis action cannot be undone.')) {
    form.submit();
  }
  return false;
}

// ---- Client-side filter + search + sort for notice lists ----
function applyNoticeFilters() {
  const grid = document.getElementById('notice-collection');
  if (!grid) return;
  const q = (document.getElementById('f-search')?.value || '').toLowerCase();
  const cat = document.getElementById('f-category')?.value || 'all';
  const pri = document.getElementById('f-priority')?.value || 'all';
  const extra = document.getElementById('f-extra')?.value || 'all';
  const sort = document.getElementById('f-sort')?.value || 'priority';

  let cards = Array.from(grid.querySelectorAll('.notice-card'));
  let visible = 0;
  cards.forEach(function (c) {
    const text = (c.dataset.title + ' ' + c.dataset.body).toLowerCase();
    let ok = true;
    if (q && !text.includes(q)) ok = false;
    if (cat !== 'all' && c.dataset.category !== cat) ok = false;
    if (pri !== 'all' && c.dataset.priority !== pri) ok = false;
    if (extra === 'due' && c.dataset.due !== '1') ok = false;
    if (extra === 'unread' && c.dataset.read === '1') ok = false;
    if (extra === 'saved' && c.dataset.saved !== '1') ok = false;
    c.style.display = ok ? '' : 'none';
    if (ok) visible++;
  });

  // sort visible
  const rank = { HIGH: 3, MEDIUM: 2, LOW: 1 };
  cards.sort(function (a, b) {
    if (sort === 'priority') return b.dataset.pscore - a.dataset.pscore;
    if (sort === 'relevance') return b.dataset.relevance - a.dataset.relevance;
    if (sort === 'deadline') return (a.dataset.days || 1e9) - (b.dataset.days || 1e9);
    if (sort === 'newest') return b.dataset.id - a.dataset.id;
    return 0;
  });
  cards.forEach(c => grid.appendChild(c));

  const note = document.getElementById('count-note');
  if (note) note.textContent = visible + ' notice' + (visible === 1 ? '' : 's') + ' shown';
  const empty = document.getElementById('empty-filtered');
  if (empty) empty.style.display = visible === 0 ? '' : 'none';
}

window.addEventListener('DOMContentLoaded', function () {
  ['f-search', 'f-category', 'f-priority', 'f-extra', 'f-sort'].forEach(function (id) {
    const el = document.getElementById(id);
    if (el) el.addEventListener(el.tagName === 'INPUT' ? 'input' : 'change', applyNoticeFilters);
  });
  applyNoticeFilters();
});

// copy demo cred to login field
function useCred(email, pw) {
  const e = document.getElementById('email'), p = document.getElementById('password');
  if (e && p) { e.value = email; p.value = pw; showToast('Demo credentials filled in.'); }
}
