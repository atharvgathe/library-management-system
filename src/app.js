const $ = id => document.getElementById(id);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let books = [];

function toast(text, ok = true) {
  const t = document.createElement('div');
  t.className = 'toast ' + (ok ? 'ok' : 'err'); t.textContent = text;
  $('toasts').append(t); setTimeout(() => t.remove(), 3000);
}
async function api(url, method = 'GET', data) {
  try {
    const r = await fetch(url, { method, headers: {'Content-Type': 'application/json'}, body: data ? JSON.stringify(data) : undefined });
    const j = await r.json();
    if (!r.ok) { toast(j.error || 'Something went wrong', false); return null; }
    return j;
  } catch { toast('Cannot reach the server', false); return null; }
}

function renderBooks() {
  const f = $('filter').value;
  const list = books.filter(b => f === 'all' || (f === 'in') === !!b.available);
  $('books').innerHTML = list.map(b => `<tr>
    <td><b>${esc(b.title)}</b></td><td>${esc(b.author)}</td><td>${esc(b.isbn)}</td><td><span class="cat">${esc(b.category)}</span></td>
    <td><span class="tag ${b.available ? 'in' : 'out'}">${b.available ? 'Available' : 'Issued to ' + esc(b.issued_to)}</span></td>
    <td class="act">${b.available ? `<button class="ok-b" data-a="issue" data-id="${b.id}">Issue</button>` : `<button class="blue-b" data-a="ret" data-id="${b.id}">Return</button>`}
    <button class="bad-b" data-a="del" data-id="${b.id}">Delete</button></td></tr>`).join('');
  $('empty').hidden = list.length > 0;
}
async function loadBooks() {
  const res = await api('/api/books?q=' + encodeURIComponent($('search').value));
  if (res) { books = res; renderBooks(); }
  const all = await api('/api/books');
  if (all) {
    const a = all.filter(b => b.available).length;
    $('sTotal').textContent = all.length; $('sAvail').textContent = a; $('sIssued').textContent = all.length - a;
    $('cats').innerHTML = [...new Set(all.map(b => b.category))].map(c => `<option value="${esc(c)}">`).join('');
  }
}
async function loadMembers() {
  const ms = await api('/api/members'); if (!ms) return;
  $('sMem').textContent = ms.length;
  $('memberSel').innerHTML = '<option value="">Member to issue to…</option>' + ms.map(m => `<option value="${m.id}">${esc(m.name)}</option>`).join('');
  $('members').innerHTML = ms.map(m => `<tr><td>${esc(m.name)}</td><td>${esc(m.email)}</td></tr>`).join('') || '<tr><td colspan="2" class="empty">No members yet.</td></tr>';
}
async function loadHistory() {
  const h = await api('/api/issues'); if (!h) return;
  $('hist').innerHTML = h.map(i => `<tr><td>${esc(i.title)}</td><td>${esc(i.name)}</td><td>${i.issue_date}</td><td>${i.return_date ? i.return_date : '<span class="tag out">Not returned</span>'}</td></tr>`).join('') || '<tr><td colspan="4" class="empty">No history yet.</td></tr>';
}
const refresh = () => { loadBooks(); loadHistory(); };

$('books').addEventListener('click', async e => {
  const b = e.target.closest('button'); if (!b) return;
  const id = b.dataset.id;
  if (b.dataset.a === 'issue') {
    const m = $('memberSel').value; if (!m) return toast('Select a member first', false);
    if (await api(`/api/books/${id}/issue`, 'POST', { member_id: +m })) { toast('Book issued'); refresh(); }
  } else if (b.dataset.a === 'ret') {
    if (await api(`/api/books/${id}/return`, 'POST')) { toast('Book returned'); refresh(); }
  } else if (b.dataset.a === 'del' && confirm('Delete this book?')) {
    if (await api('/api/books/' + id, 'DELETE')) { toast('Book deleted'); refresh(); }
  }
});
$('bookForm').addEventListener('submit', async e => {
  e.preventDefault();
  if (await api('/api/books', 'POST', { title: $('title').value, author: $('author').value, isbn: $('isbn').value, category: $('category').value })) {
    toast('Book added'); e.target.reset(); refresh();
  }
});
$('memForm').addEventListener('submit', async e => {
  e.preventDefault();
  if (await api('/api/members', 'POST', { name: $('mname').value, email: $('memail').value })) { toast('Member added'); e.target.reset(); loadMembers(); }
});
document.querySelectorAll('.tab').forEach(t => t.onclick = () => {
  document.querySelectorAll('.tab').forEach(x => x.classList.toggle('on', x === t));
  document.querySelectorAll('.pane').forEach(p => p.hidden = p.id !== 'tab-' + t.dataset.tab);
  if (t.dataset.tab === 'history') loadHistory();
});
let timer; $('search').oninput = () => { clearTimeout(timer); timer = setTimeout(loadBooks, 200); };
$('filter').onchange = renderBooks;
loadMembers(); refresh();
