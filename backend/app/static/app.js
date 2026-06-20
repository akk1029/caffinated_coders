'use strict';

const API = '/api';
const TOKEN_KEY = 'pp_token';

const PET_STAGES = [
  { name: 'Egg',      emoji: '🥚' },
  { name: 'Hatchling',emoji: '🐣' },
  { name: 'Chick',    emoji: '🐥' },
  { name: 'Fledgling',emoji: '🐦' },
  { name: 'Parrot',   emoji: '🦜' },
  { name: 'Hawk',     emoji: '🦅' },
  { name: 'Lion',     emoji: '🦁' },
  { name: 'Dragon',   emoji: '🐉' },
  { name: 'Phoenix',  emoji: '🦄' },
  { name: 'Legend',   emoji: '⭐' },
];

// ─── Auth ────────────────────────────────────────────────────────────────────
const getToken = () => localStorage.getItem(TOKEN_KEY);
const saveToken = t => localStorage.setItem(TOKEN_KEY, t);
const clearToken = () => localStorage.removeItem(TOKEN_KEY);

function requireAuth() {
  if (!getToken()) { window.location.href = '/login'; return false; }
  return true;
}

// ─── HTTP ────────────────────────────────────────────────────────────────────
async function apiFetch(path, opts = {}) {
  const headers = { ...opts.headers };
  const t = getToken();
  if (t) headers['Authorization'] = `Bearer ${t}`;
  if (opts.body && !(opts.body instanceof FormData)) headers['Content-Type'] = 'application/json';

  const res = await fetch(API + path, { ...opts, headers });
  if (res.status === 401) { clearToken(); window.location.href = '/login'; return; }

  let data;
  try { data = await res.json(); } catch { data = null; }
  if (!res.ok) throw new Error(data?.detail || `Error ${res.status}`);
  return data;
}

// ─── Toast ───────────────────────────────────────────────────────────────────
function toast(msg, type = 'info') {
  const el = document.createElement('div');
  el.className = `toast toast-${type}`;
  el.textContent = msg;
  document.getElementById('toast-container').appendChild(el);
  setTimeout(() => el.remove(), 3200);
}

// ─── Helpers ─────────────────────────────────────────────────────────────────
function setErr(id, msg) { const e = document.getElementById(id); if (e) { e.textContent = msg; e.classList.remove('hidden'); } }
function clearErr(id)    { const e = document.getElementById(id); if (e) { e.textContent = ''; e.classList.add('hidden'); } }

function setBtn(id, busy, label) {
  const b = document.getElementById(id);
  if (!b) return;
  b.disabled = busy;
  if (label) b.textContent = busy ? 'Loading…' : label;
}

function hpColor(hp) { return hp >= 70 ? '#4caf50' : hp >= 40 ? '#ff9800' : '#f44336'; }
function expiryColor(days) { return (days <= 3) ? '#f44336' : (days <= 7) ? '#ff9800' : '#4caf50'; }
function daysLeft(expiry) { return Math.ceil((new Date(expiry) - Date.now()) / 86400000); }
function addDays(d, n) { const r = new Date(d); r.setDate(r.getDate() + n); return r; }
function isoDate(d) { return d.toISOString().split('T')[0]; }
function petEmoji(level) { return (PET_STAGES[Math.min(level - 1, PET_STAGES.length - 1)] || PET_STAGES[0]).emoji; }

function setNav() {
  const page = window.location.pathname.replace('/', '') || 'dashboard';
  document.querySelectorAll('.nav-item').forEach(a => a.classList.toggle('active', a.dataset.page === page));
}

async function setupHeader() {
  document.getElementById('logout-btn')?.addEventListener('click', () => { clearToken(); window.location.href = '/login'; });
  try {
    const u = await apiFetch('/auth/me');
    const badge = document.getElementById('tier-badge');
    if (badge) { badge.textContent = u.subscription_tier; badge.className = `badge badge-${u.subscription_tier.toLowerCase()}`; }
  } catch {}
}

// ─── Login ───────────────────────────────────────────────────────────────────
function initLogin() {
  if (getToken()) { window.location.href = '/dashboard'; return; }
  if (new URLSearchParams(location.search).get('registered')) {
    document.getElementById('success-msg')?.classList.remove('hidden');
  }
  document.getElementById('login-form').addEventListener('submit', async e => {
    e.preventDefault(); clearErr('err');
    setBtn('submit-btn', true, 'Sign In');
    try {
      const d = await apiFetch('/auth/login', { method: 'POST', body: JSON.stringify({ email: document.getElementById('email').value, password: document.getElementById('password').value }) });
      saveToken(d.access_token);
      window.location.href = '/dashboard';
    } catch (ex) { setErr('err', ex.message); }
    finally { setBtn('submit-btn', false, 'Sign In'); }
  });
}

// ─── Register ────────────────────────────────────────────────────────────────
function initRegister() {
  if (getToken()) { window.location.href = '/dashboard'; return; }
  document.getElementById('register-form').addEventListener('submit', async e => {
    e.preventDefault(); clearErr('err');
    setBtn('submit-btn', true, 'Create Account');
    try {
      await apiFetch('/auth/register', { method: 'POST', body: JSON.stringify({ username: document.getElementById('username').value, email: document.getElementById('email').value, password: document.getElementById('password').value }) });
      window.location.href = '/login?registered=1';
    } catch (ex) { setErr('err', ex.message); }
    finally { setBtn('submit-btn', false, 'Create Account'); }
  });
}

// ─── Dashboard ───────────────────────────────────────────────────────────────
async function initDashboard() {
  if (!requireAuth()) return;
  setNav(); setupHeader();
  try {
    const [user, stats, pet] = await Promise.all([apiFetch('/auth/me'), apiFetch('/dashboard/stats'), apiFetch('/pet/')]);
    document.getElementById('greeting').textContent = `Hello, ${user.username}!`;
    document.getElementById('pantry-count').textContent = stats.pantry_count;
    document.getElementById('expiring-count').textContent = stats.expiring_soon_count;
    document.getElementById('co2-val').textContent = parseFloat(user.total_co2_saved || 0).toFixed(1);
    document.getElementById('money-val').textContent = parseFloat(user.total_money_saved || 0).toFixed(2);
    document.getElementById('recipes-today').textContent = `${user.recipes_generated_today}/3`;
    if (stats.expiring_soon_count > 0) {
      document.getElementById('expiry-alert').classList.remove('hidden');
      document.getElementById('expiring-list').textContent = stats.expiring_items.join(', ');
    }
    if (pet) {
      document.getElementById('dash-pet-emoji').textContent = petEmoji(pet.appearance_level);
      document.getElementById('dash-pet-mood').textContent = `${pet.mood_status} · Lv.${pet.appearance_level}`;
      const fill = document.getElementById('dash-hp-fill');
      fill.style.width = `${pet.health_points}%`;
      fill.style.background = hpColor(pet.health_points);
    }
    if (user.subscription_tier !== 'Premium') {
      document.getElementById('premium-banner').classList.remove('hidden');
    }
  } catch (ex) { toast(ex.message, 'error'); }
}

// ─── Inventory ───────────────────────────────────────────────────────────────
let pending = [];
const UNITS = ['pieces','kg','g','liters','ml','cups','tbsp','tsp'];

async function initInventory() {
  if (!requireAuth()) return;
  setNav(); setupHeader();
  await loadInventory();

  document.getElementById('camera-input').addEventListener('change', async e => {
    const file = e.target.files[0]; if (!file) return;
    setBtn('camera-btn', true, '🥕 Scan Ingredients');
    try {
      const fd = new FormData(); fd.append('file', file);
      const d = await apiFetch('/inventory/upload/', { method: 'POST', body: fd });
      const now = new Date();
      pending = [...pending, ...d.detected_ingredients.map(x => ({ item_name: x.item_name, quantity: 1, unit: 'pieces', expiry_date: isoDate(addDays(now, x.suggested_shelf_days)), estimated_cost: 2.00 }))];
      renderPending();
    } catch (ex) { toast(ex.message, 'error'); }
    finally { setBtn('camera-btn', false, '🥕 Scan Ingredients'); e.target.value = ''; }
  });

  document.getElementById('receipt-input').addEventListener('change', async e => {
    const file = e.target.files[0]; if (!file) return;
    setBtn('receipt-btn', true, '🧾 Scan Receipt');
    try {
      const fd = new FormData(); fd.append('file', file);
      const d = await apiFetch('/receipts/scan/', { method: 'POST', body: fd });
      const now = new Date();
      pending = [...pending, ...d.items.map(x => ({ item_name: x.item_name, quantity: x.quantity || 1, unit: x.unit || 'pieces', expiry_date: isoDate(addDays(now, x.suggested_shelf_days)), estimated_cost: x.estimated_cost || 2.00 }))];
      renderPending();
    } catch (ex) { toast(ex.message, 'error'); }
    finally { setBtn('receipt-btn', false, '🧾 Scan Receipt'); e.target.value = ''; }
  });

  document.getElementById('confirm-btn').addEventListener('click', async () => {
    if (!pending.length) return;
    setBtn('confirm-btn', true, `Add ${pending.length} items`);
    try {
      await apiFetch('/inventory/confirm/', { method: 'POST', body: JSON.stringify({ batches: pending.map(p => ({ ...p, expiry_date: new Date(p.expiry_date).toISOString() })) }) });
      pending = []; renderPending();
      toast('Added to pantry!', 'success');
      await loadInventory();
    } catch (ex) { toast(ex.message, 'error'); }
    finally { setBtn('confirm-btn', false, `Add items`); }
  });

  // Manual add
  const unitSel = document.getElementById('manual-unit');
  if (unitSel) unitSel.innerHTML = UNITS.map(u => `<option>${u}</option>`).join('');
  document.getElementById('manual-add-btn')?.addEventListener('click', async () => {
    const nameEl = document.getElementById('manual-name');
    const name = nameEl.value.trim();
    if (!name) { toast('Enter an item name', 'error'); return; }
    const quantity = parseFloat(document.getElementById('manual-qty').value) || 1;
    const unit = document.getElementById('manual-unit').value;
    setBtn('manual-add-btn', true, 'Add');
    try {
      const b = await apiFetch('/inventory/add/', { method: 'POST',
        body: JSON.stringify({ item_name: name, quantity, unit }) });
      toast(`Added ${b.item_name} — ${daysLeft(b.expiry_date)}d shelf life · ~RM ${parseFloat(b.estimated_cost).toFixed(2)}`, 'success');
      nameEl.value = '';
      await loadInventory();
    } catch (ex) { toast(ex.message, 'error'); }
    finally { setBtn('manual-add-btn', false, 'Add'); }
  });
}

async function loadInventory() {
  const list = document.getElementById('inv-list');
  list.innerHTML = '<div class="loading">Loading…</div>';
  try {
    const items = await apiFetch('/inventory/');
    const count = document.getElementById('inv-count');
    if (count) count.textContent = items.length;
    if (!items.length) { list.innerHTML = '<div class="empty-state">Your pantry is empty.<br>Scan ingredients or a receipt to get started!</div>'; return; }
    list.innerHTML = items.map(it => {
      const days = daysLeft(it.expiry_date);
      const col = expiryColor(days);
      const label = days <= 0 ? 'Expired' : `${days}d left`;
      return `<div class="item-row" style="border-left-color:${col}">
        <span class="item-name">${it.item_name}</span>
        <span class="item-qty">${parseFloat(it.quantity)} ${it.unit}</span>
        <span class="item-days" style="color:${col}">${label}</span>
        <div class="item-actions">
          <button class="btn btn-primary btn-sm" onclick="consumeItem('${it.batch_id}',this)" title="Mark as used">✓</button>
          <button class="btn btn-outline btn-sm" onclick="discardItem('${it.batch_id}',this)" title="Discard">✕</button>
        </div>
      </div>`;
    }).join('');
  } catch (ex) { list.innerHTML = `<p class="text-muted">${ex.message}</p>`; }
}

function renderPending() {
  const panel = document.getElementById('confirm-panel');
  const container = document.getElementById('pending-list');
  if (!pending.length) { panel.classList.add('hidden'); return; }
  panel.classList.remove('hidden');
  const confirmBtn = document.getElementById('confirm-btn');
  if (confirmBtn) confirmBtn.textContent = `Add ${pending.length} item${pending.length > 1 ? 's' : ''} to Pantry`;

  container.innerHTML = pending.map((it, i) => `
    <div class="confirm-row">
      <input style="flex:2;min-width:0" class="form-input" value="${it.item_name}" onchange="pending[${i}].item_name=this.value">
      <input style="width:62px" class="form-input" type="number" value="${it.quantity}" min="0.1" step="0.1" onchange="pending[${i}].quantity=parseFloat(this.value)||1">
      <select style="width:80px" class="form-input" onchange="pending[${i}].unit=this.value">
        ${UNITS.map(u=>`<option${u===it.unit?' selected':''}>${u}</option>`).join('')}
      </select>
      <input style="width:120px" class="form-input" type="date" value="${it.expiry_date}" onchange="pending[${i}].expiry_date=this.value">
      <input style="width:68px" class="form-input" type="number" placeholder="RM" value="${it.estimated_cost}" step="0.01" onchange="pending[${i}].estimated_cost=parseFloat(this.value)||0">
      <button class="btn btn-outline btn-sm" onclick="pending.splice(${i},1);renderPending()">✕</button>
    </div>`).join('');
}

async function consumeItem(id, btn) {
  btn.disabled = true;
  try {
    const r = await apiFetch(`/inventory/${id}/consume`, { method: 'POST' });
    btn.closest('.item-row').remove();
    toast(`Saved ${r.co2_saved} kg CO₂ · RM ${r.money_saved}`, 'success');
  } catch (ex) { toast(ex.message, 'error'); btn.disabled = false; }
}

async function discardItem(id, btn) {
  btn.disabled = true;
  try {
    await apiFetch(`/inventory/${id}`, { method: 'DELETE' });
    btn.closest('.item-row').remove();
    toast('Discarded', 'info');
  } catch (ex) { toast(ex.message, 'error'); btn.disabled = false; }
}

// ─── Recipes ─────────────────────────────────────────────────────────────────
async function initRecipes() {
  if (!requireAuth()) return;
  setNav(); setupHeader();
  const user = await apiFetch('/auth/me');
  const atLimit = user.subscription_tier === 'Free' && user.recipes_generated_today >= 3;
  const usageEl = document.getElementById('usage-text');
  if (usageEl) usageEl.textContent = `${user.recipes_generated_today}/3 free today`;
  if (atLimit) {
    document.getElementById('limit-alert')?.classList.remove('hidden');
    document.getElementById('gen-btn').disabled = true;
  }
  document.getElementById('gen-btn')?.addEventListener('click', async () => {
    clearErr('recipe-err');
    setBtn('gen-btn', true, 'Generate Recipes');
    try {
      const d = await apiFetch('/recipes/generate/', { method: 'POST' });
      renderRecipes(d.recipes);
      document.getElementById('recipe-empty')?.classList.add('hidden');
    } catch (ex) { setErr('recipe-err', ex.message); }
    finally { setBtn('gen-btn', false, 'Generate Recipes'); }
  });

  loadSaved();
}

let _recipes = [];   // generated recipes
let _saved = [];     // saved recipes

function recipeCardHTML(r, i, ctx) {
  const tags = [r.category, r.area].filter(Boolean).join(' · ');
  const meta = ctx === 'gen'
    ? `Uses ${r.usedIngredientCount} of your ingredients${r.missedIngredientCount>0?` · Missing ${r.missedIngredientCount}`:''}${r.expiringUsedCount>0?` · <span class="recipe-exp">⏳ ${r.expiringUsedCount} expiring</span>`:''}`
    : (tags || 'Saved recipe');
  const usedRow = (r.usedIngredients && r.usedIngredients.length)
    ? `<p class="rd-row"><strong>Your ingredients:</strong> ${r.usedIngredients.join(', ')}</p>` : '';
  const instrRow = r.instructions
    ? `<p class="rd-row rd-instructions">${r.instructions}</p>`
    : `<p class="rd-row text-muted">No instructions provided by source.</p>`;
  const actions = ctx === 'gen'
    ? `<button class="btn btn-sm btn-outline" data-act="save">💾 Save</button>
       <button class="btn btn-sm btn-primary" data-act="cooked">🍳 Cooked</button>`
    : `<button class="btn btn-sm btn-danger" data-act="remove">🗑 Remove</button>`;
  const video = r.youtube
    ? `<a class="btn btn-sm btn-danger" href="${r.youtube}" target="_blank" rel="noopener">▶ Video</a>` : '';
  return `
    <div class="recipe-card" data-ctx="${ctx}" data-idx="${i}">
      ${r.image ? `<img class="recipe-img" src="${r.image}" alt="${r.title}" onerror="this.style.display='none'">` : ''}
      <div class="recipe-body">
        <p class="recipe-title">${r.title} <span class="rd-caret">▾</span></p>
        <p class="recipe-meta">${meta}</p>
        <div class="recipe-details hidden">
          ${ctx === 'gen' && tags ? `<p class="rd-row rd-tags">${tags}</p>` : ''}
          ${usedRow}
          ${instrRow}
        </div>
        <div class="recipe-actions">
          ${actions}
          ${video}
        </div>
      </div>
    </div>`;
}

function wireCards(grid) {
  // Click a card (but not its action buttons) to expand/collapse the details.
  grid.querySelectorAll('.recipe-card').forEach(card => {
    card.addEventListener('click', e => {
      if (e.target.closest('.recipe-actions')) return;
      const details = card.querySelector('.recipe-details');
      const caret = card.querySelector('.rd-caret');
      if (!details) return;
      details.classList.toggle('hidden');
      if (caret) caret.textContent = details.classList.contains('hidden') ? '▾' : '▴';
    });
  });
  grid.querySelectorAll('button[data-act]').forEach(btn =>
    btn.addEventListener('click', e => { e.stopPropagation(); handleRecipeAction(btn); })
  );
}

function renderRecipes(recipes) {
  _recipes = recipes || [];
  const grid = document.getElementById('recipe-grid');
  grid.innerHTML = _recipes.map((r, i) => recipeCardHTML(r, i, 'gen')).join('');
  wireCards(grid);
}

function renderSaved(recipes) {
  _saved = recipes || [];
  const section = document.getElementById('saved-section');
  const grid = document.getElementById('saved-grid');
  if (!_saved.length) { section.classList.add('hidden'); grid.innerHTML = ''; return; }
  section.classList.remove('hidden');
  grid.innerHTML = _saved.map((r, i) => recipeCardHTML(r, i, 'saved')).join('');
  wireCards(grid);
}

async function loadSaved() {
  try { renderSaved((await apiFetch('/recipes/saved/')).recipes); } catch {}
}

async function handleRecipeAction(btn) {
  const card = btn.closest('.recipe-card');
  const ctx = card.dataset.ctx;
  const r = (ctx === 'saved' ? _saved : _recipes)[+card.dataset.idx];
  if (!r) return;
  const act = btn.dataset.act;

  if (act === 'save') {
    btn.disabled = true;
    try {
      await apiFetch('/recipes/save/', { method: 'POST', body: JSON.stringify({
        id: String(r.id), title: r.title, image: r.image || '', youtube: r.youtube || '',
        instructions: r.instructions || '', category: r.category || '', area: r.area || '',
      }) });
      btn.textContent = '✓ Saved';
      toast('Recipe saved', 'success');
      loadSaved();
    } catch (ex) { btn.disabled = false; toast(ex.message, 'error'); }

  } else if (act === 'cooked') {
    btn.disabled = true;
    try {
      const d = await apiFetch('/recipes/cooked/', { method: 'POST',
        body: JSON.stringify({ ingredients: r.usedIngredients || [] }) });
      btn.textContent = `✓ Cooked (${d.consumed})`;
      toast(d.consumed > 0
        ? `Pantry updated — ${d.consumed} used · ${d.co2_saved} kg CO₂ · RM ${d.money_saved} saved`
        : 'No matching pantry items to use', d.consumed > 0 ? 'success' : 'info');
    } catch (ex) { btn.disabled = false; toast(ex.message, 'error'); }

  } else if (act === 'remove') {
    btn.disabled = true;
    try {
      await apiFetch(`/recipes/saved/${encodeURIComponent(r.id)}`, { method: 'DELETE' });
      toast('Removed from saved', 'info');
      loadSaved();
    } catch (ex) { btn.disabled = false; toast(ex.message, 'error'); }
  }
}

// ─── Pet ─────────────────────────────────────────────────────────────────────
async function initPet() {
  if (!requireAuth()) return;
  setNav(); setupHeader();
  try {
    renderPet(await apiFetch('/pet/'));
    document.getElementById('feed-btn').addEventListener('click', async () => {
      setBtn('feed-btn', true, 'Feed');
      try { renderPet(await apiFetch('/pet/feed/', { method: 'POST' })); toast('+10 HP!', 'success'); }
      catch (ex) { toast(ex.message, 'error'); }
      finally { setBtn('feed-btn', false, 'Feed (+10 HP)'); }
    });
  } catch (ex) { toast(ex.message, 'error'); }
}

function renderPet(pet) {
  const s = PET_STAGES[Math.min(pet.appearance_level - 1, PET_STAGES.length - 1)];
  document.getElementById('pet-emoji').textContent = s.emoji;
  document.getElementById('pet-stage').textContent = `${s.name} · Level ${pet.appearance_level}`;
  document.getElementById('pet-mood').textContent = pet.mood_status;
  document.getElementById('pet-mood').style.color = hpColor(pet.health_points);
  document.getElementById('hp-text').textContent = `${pet.health_points}/100 HP`;
  const fill = document.getElementById('hp-fill');
  fill.style.width = `${pet.health_points}%`;
  fill.style.background = hpColor(pet.health_points);
}

// ─── Premium ─────────────────────────────────────────────────────────────────
async function initPremium() {
  if (!requireAuth()) return;
  setNav(); setupHeader();
  const user = await apiFetch('/auth/me');
  if (user.subscription_tier === 'Premium') {
    document.getElementById('already-premium').classList.remove('hidden');
    document.getElementById('upgrade-section').classList.add('hidden');
    document.getElementById('expiry-date').textContent = user.subscription_expiry ? new Date(user.subscription_expiry).toLocaleDateString() : 'N/A';
    return;
  }
  document.getElementById('subscribe-btn')?.addEventListener('click', async () => {
    clearErr('pay-err');
    setBtn('subscribe-btn', true, 'Activating…');
    try {
      await apiFetch('/payments/demo-subscribe/', { method: 'POST' });
      toast('Premium activated!', 'success');
      setTimeout(() => window.location.reload(), 1500);
    } catch (ex) { setErr('pay-err', ex.message); }
    finally { setBtn('subscribe-btn', false, 'Subscribe Now'); }
  });
}

// ─── Leaderboard ─────────────────────────────────────────────────────────────
function petImage(level) {
  if (level >= 8) return '/static/pets/top-leaderboard.png';
  if (level >= 5) return '/static/pets/wolf-4.png';
  return '/static/pets/fox-4.png';
}

async function initLeaderboard() {
  if (!requireAuth()) return;
  setNav(); setupHeader();
  try {
    const [data, me] = await Promise.all([apiFetch('/leaderboard/'), apiFetch('/auth/me')]);
    const MEDALS = ['🥇','🥈','🥉'];
    const top3 = data.rankings.slice(0, 3);
    const rest  = data.rankings.slice(3);

    // Podium (top 3)
    document.getElementById('lb-podium').innerHTML = top3.map((e, i) => {
      const isMe = e.user_id === me.user_id;
      const rankClass = `rank-${i + 1}`;
      return `<div class="lb-podium-card ${rankClass}${isMe ? ' me' : ''}">
        <div class="lb-podium-medal">${MEDALS[i]}</div>
        <img class="pet-img" src="${petImage(e.pet_level || 1)}" alt="pet">
        <div class="lb-podium-name">${e.username}${isMe ? ' (you)' : ''}</div>
        <div class="lb-podium-co2">${e.total_co2_saved.toFixed(1)} kg CO₂</div>
      </div>`;
    }).join('');

    // Rest of list (#4+)
    if (rest.length) {
      document.getElementById('lb-list').innerHTML =
        `<div class="lb-rest-hdr">The Rest</div>` +
        rest.map((e, i) => {
          const isMe = e.user_id === me.user_id;
          return `<div class="lb-row${isMe ? ' me' : ''}">
            <span class="lb-rank">#${i + 4}</span>
            <span class="lb-pet">${petEmoji(e.pet_level || 1)}</span>
            <span class="lb-name">${e.username}${isMe ? ' (you)' : ''}</span>
            <span class="lb-co2">${e.total_co2_saved.toFixed(1)} kg CO₂</span>
          </div>`;
        }).join('');
    }

    if (data.user_rank) document.getElementById('my-rank').textContent = `Your rank: #${data.user_rank}`;
  } catch (ex) { toast(ex.message, 'error'); }
}

// ─── Router ──────────────────────────────────────────────────────────────────
const ROUTES = {
  '/login':       initLogin,
  '/register':    initRegister,
  '/dashboard':   initDashboard,
  '/inventory':   initInventory,
  '/recipes':     initRecipes,
  '/pet':         initPet,
  '/premium':     initPremium,
  '/leaderboard': initLeaderboard,
};

document.addEventListener('DOMContentLoaded', () => {
  if ('serviceWorker' in navigator) navigator.serviceWorker.register('/static/sw.js').catch(() => {});
  const init = ROUTES[window.location.pathname];
  if (init) init();
});
