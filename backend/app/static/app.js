'use strict';

const API = '/api';
const TOKEN_KEY = 'pp_token';

// Stage 1–4 mapped from HP. Index 0 = stage 1.
const STAGE_NAMES = ['Forgotten', 'Struggling', 'Happy', 'Thriving'];

const PET_QUIPS = {
  fox:    ['yip yip!', 'heehee!', 'sniff sniff~', '*wags tail*', 'ooh shiny!', 'feed me?', 'boop!'],
  wolf:   ['AWOOOO!', 'grrrr~', '*howls at moon*', 'protect the pack!', 'rawr!', 'aroooo~'],
  tiger:  ['ROAR!', 'meow?', 'nom nom nom', '*pounces*', 'I am speed', 'grrrr!', 'pat me!'],
  dragon: ['RAWRR!', '*breathes fire*', 'ancient power!', 'gimme food', 'I burn things~', 'brooooo'],
  bat:    ['eeek!', '*hangs upside down*', 'squeeeeak!', 'night mode on', 'boo!', 'i see u~'],
};

const PET_TYPES = {
  fox:    { name: 'Forest Fox',   desc: 'A clever fox attuned to nature. Quick, curious, and full of heart.', emoji: '🦊' },
  wolf:   { name: 'Nature Wolf',  desc: 'A wild wolf with a leaf crown. Fierce protector of the forest.',    emoji: '🐺' },
  tiger:  { name: 'Royal Tiger',  desc: 'A legendary tiger with ancient power. Born to lead.',               emoji: '🐯' },
  dragon: { name: 'Earth Dragon', desc: 'An ancient dragon of the deep woods. Rare and powerful.',           emoji: '🐉' },
  bat:    { name: 'Shadow Bat',   desc: 'A mystic bat of the night forest. Silent and swift.',               emoji: '🦇' },
};

function petStage(hp) {
  if (hp >= 75) return 4;
  if (hp >= 50) return 3;
  if (hp >= 25) return 2;
  return 1;
}

function petImage(type, hp, champion = false) {
  const stage = champion ? 5 : petStage(hp ?? 100);
  return `/static/pets/${type || 'fox'}-${stage}.png`;
}

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

function hpColor(hp) { return hp >= 75 ? '#5DC98A' : hp >= 50 ? '#8AC95D' : hp >= 25 ? '#E8845A' : '#E05C5C'; }
function expiryColor(days) { return (days <= 3) ? '#E05C5C' : (days <= 7) ? '#E8845A' : '#5DC98A'; }
function daysLeft(expiry) { return Math.ceil((new Date(expiry) - Date.now()) / 86400000); }
function addDays(d, n) { const r = new Date(d); r.setDate(r.getDate() + n); return r; }
function isoDate(d) { return d.toISOString().split('T')[0]; }
function petEmoji(type) { return (PET_TYPES[type] || PET_TYPES.fox).emoji; }
function petStageName(hp) { return STAGE_NAMES[petStage(hp) - 1]; }

const FLOAT_EMOJIS   = ['❤️','✨','⭐','💫','🌟','💕','🎉','💖','🔥','🌈'];
const PARTICLE_COLORS = ['#ff6b6b','#ffd93d','#6bcb77','#4d96ff','#ff9ff3','#c77dff','#ff9f43'];

let _comboCount = 0;
let _comboTimer = null;

function _petWrap(el) { return el.closest('.pet-bubble-wrap') || el.parentElement; }

function showPetBubble(anchorEl, petType) {
  const quips = PET_QUIPS[petType] || PET_QUIPS.fox;
  const wrap = _petWrap(anchorEl);
  const old = wrap.querySelector('.pet-bubble');
  if (old) { old.remove(); }
  const bubble = document.createElement('div');
  bubble.className = 'pet-bubble';
  bubble.textContent = quips[Math.floor(Math.random() * quips.length)];
  wrap.appendChild(bubble);
  setTimeout(() => bubble.remove(), 1800);
}

function _spawnParticles(wrap) {
  const n = 12;
  for (let i = 0; i < n; i++) {
    const p = document.createElement('div');
    p.className = 'pet-particle';
    const angle = (i / n) * Math.PI * 2 + Math.random() * 0.4;
    const dist  = 45 + Math.random() * 45;
    p.style.setProperty('--px', `${Math.cos(angle) * dist}px`);
    p.style.setProperty('--py', `${Math.sin(angle) * dist}px`);
    p.style.background = PARTICLE_COLORS[Math.floor(Math.random() * PARTICLE_COLORS.length)];
    p.style.animationDelay = `${Math.random() * 80}ms`;
    wrap.appendChild(p);
    setTimeout(() => p.remove(), 750);
  }
}

function _spawnFloats(wrap, combo) {
  const count = Math.min(2 + combo, 6);
  for (let i = 0; i < count; i++) {
    const el = document.createElement('div');
    el.className = 'pet-float-emoji';
    el.textContent = FLOAT_EMOJIS[Math.floor(Math.random() * FLOAT_EMOJIS.length)];
    el.style.left   = `${15 + Math.random() * 70}%`;
    el.style.top    = `${20 + Math.random() * 40}%`;
    el.style.animationDelay = `${i * 90}ms`;
    wrap.appendChild(el);
    setTimeout(() => el.remove(), 1100 + i * 90);
  }
}

function _spawnRing(wrap) {
  const r = document.createElement('div');
  r.className = 'pet-ring';
  wrap.appendChild(r);
  setTimeout(() => r.remove(), 550);
}

function _showCombo(wrap, n) {
  const old = wrap.querySelector('.pet-combo');
  if (old) old.remove();
  if (n < 2) return;
  const el = document.createElement('div');
  el.className = 'pet-combo';
  const labels = { 2:'x2!', 3:'x3! 🔥', 4:'x4! 💥', 5:'x5! ⚡' };
  el.textContent = labels[Math.min(n, 5)] || `x${n}! 🌟`;
  if (n >= 4) el.style.color = '#ff3d00';
  if (n >= 5) el.style.fontSize = '22px';
  wrap.appendChild(el);
  setTimeout(() => el.remove(), 900);
}

function bindPetClick(imgEl, petType) {
  imgEl.style.cursor = 'pointer';
  imgEl.addEventListener('click', () => {
    const wrap = _petWrap(imgEl);

    // Combo
    _comboCount++;
    clearTimeout(_comboTimer);
    _comboTimer = setTimeout(() => { _comboCount = 0; }, 900);

    // Squish-bounce (restart each click)
    imgEl.classList.remove('pet-bounce');
    void imgEl.offsetWidth; // force reflow so animation restarts
    imgEl.classList.add('pet-bounce');
    imgEl.addEventListener('animationend', () => imgEl.classList.remove('pet-bounce'), { once: true });

    _spawnRing(wrap);
    _spawnParticles(wrap);
    _spawnFloats(wrap, _comboCount);
    _showCombo(wrap, _comboCount);
    showPetBubble(imgEl, petType);
  });
}

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
async function afterLogin() {
  try {
    const pet = await apiFetch('/pet/');
    window.location.href = pet.is_hatched ? '/dashboard' : '/hatch';
  } catch {
    window.location.href = '/dashboard';
  }
}

function initLogin() {
  if (getToken()) { afterLogin(); return; }
  if (new URLSearchParams(location.search).get('registered')) {
    document.getElementById('success-msg')?.classList.remove('hidden');
  }
  document.getElementById('login-form').addEventListener('submit', async e => {
    e.preventDefault(); clearErr('err');
    setBtn('submit-btn', true, 'Sign In');
    try {
      const d = await apiFetch('/auth/login', { method: 'POST', body: JSON.stringify({ email: document.getElementById('email').value, password: document.getElementById('password').value }) });
      saveToken(d.access_token);
      await afterLogin();
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
      const { username, email, password } = {
        username: document.getElementById('username').value,
        email:    document.getElementById('email').value,
        password: document.getElementById('password').value,
      };
      await apiFetch('/auth/register', { method: 'POST', body: JSON.stringify({ username, email, password }) });
      // Auto-login then go to hatch
      const d = await apiFetch('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) });
      saveToken(d.access_token);
      window.location.href = '/hatch';
    } catch (ex) { setErr('err', ex.message); }
    finally { setBtn('submit-btn', false, 'Create Account'); }
  });
}

// ─── Hatch ───────────────────────────────────────────────────────────────────
async function initHatch() {
  if (!requireAuth()) return;
  try {
    const pet = await apiFetch('/pet/');
    if (pet.is_hatched) { window.location.href = '/dashboard'; return; }
  } catch { window.location.href = '/dashboard'; return; }
}

let _hatchPet = null;

async function startHatch() {
  const wrap = document.getElementById('egg-wrap');
  if (wrap.classList.contains('shaking')) return;
  wrap.classList.add('shaking');

  // Fetch pet type while egg shakes
  try { _hatchPet = await apiFetch('/pet/'); } catch {}

  // Shake for 2.2s then flash
  await new Promise(r => setTimeout(r, 2200));

  const burst = document.getElementById('light-burst');
  burst.classList.add('flash');
  await new Promise(r => setTimeout(r, 350));

  // Show pet behind the flash
  revealPet(_hatchPet);
  await new Promise(r => setTimeout(r, 300));
  burst.classList.remove('flash');
}

function revealPet(pet) {
  document.getElementById('egg-section').style.display = 'none';
  document.getElementById('reveal-section').classList.add('show');

  const type = (pet && PET_TYPES[pet.pet_type]) || PET_TYPES.fox;
  const petType = (pet && pet.pet_type) || 'fox';
  const display = document.getElementById('pet-display');
  display.innerHTML = '';

  const img = document.createElement('img');
  img.className = 'hatch-pet-img';
  img.alt = type.name;
  img.onerror = () => {
    const fallback = document.createElement('div');
    fallback.className = 'hatch-pet-emoji';
    fallback.textContent = type.emoji;
    display.replaceChildren(fallback);
  };
  img.src = `/static/pets/${petType}-3.png`;
  display.appendChild(img);

  document.getElementById('pet-name').textContent = type.name;
  document.getElementById('pet-desc').textContent = type.desc;
}

async function startAdventure() {
  const btn = document.getElementById('start-btn');
  btn.disabled = true; btn.textContent = 'Loading…';
  try {
    await apiFetch('/pet/hatch/', { method: 'POST' });
  } catch {}
  window.location.href = '/dashboard';
}

// ─── Dashboard ───────────────────────────────────────────────────────────────
async function initDashboard() {
  if (!requireAuth()) return;
  setNav(); setupHeader();

  const viewBtn = document.getElementById('view-uploads-btn');
  if (viewBtn) {
    viewBtn.addEventListener('click', () => {
      const gallery = document.getElementById('uploads-gallery');
      if (gallery.classList.contains('hidden')) {
        gallery.classList.remove('hidden');
        viewBtn.textContent = '🙈 Hide My Photos';
        loadUploads();
      } else {
        gallery.classList.add('hidden');
        viewBtn.textContent = '🖼️ View My Photos';
      }
    });
  }

  try {
    const [user, stats, pet, lb] = await Promise.all([
      apiFetch('/auth/me'), apiFetch('/dashboard/stats'),
      apiFetch('/pet/'),    apiFetch('/leaderboard/'),
    ]);
    const isChampion = lb?.user_rank === 1;

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
      const dashPetEl = document.getElementById('dash-pet-emoji');
      dashPetEl.innerHTML = '';
      const dImg = document.createElement('img');
      dImg.style.cssText = 'width:250px;height:250px;object-fit:contain;filter:drop-shadow(0 6px 28px rgba(93,201,138,0.25))';
      dImg.alt = (PET_TYPES[pet.pet_type] || PET_TYPES.fox).name;
      dImg.onerror = () => {
        const fb = document.createElement('span');
        fb.textContent = petEmoji(pet.pet_type);
        fb.style.fontSize = '160px';
        dashPetEl.replaceChildren(fb);
      };
      dImg.src = petImage(pet.pet_type, pet.health_points, isChampion);
      dashPetEl.classList.add('pet-bubble-wrap');
      dashPetEl.appendChild(dImg);
      bindPetClick(dImg, pet.pet_type);

      const moodEl = document.getElementById('dash-pet-mood');
      moodEl.textContent = isChampion
        ? `👑 Champion · ${(PET_TYPES[pet.pet_type] || PET_TYPES.fox).name}`
        : `${petStageName(pet.health_points)} · ${(PET_TYPES[pet.pet_type] || PET_TYPES.fox).name}`;
      if (isChampion) moodEl.style.color = '#f59e0b';
      const fill = document.getElementById('dash-hp-fill');
      fill.style.width = `${pet.health_points}%`;
      fill.style.background = hpColor(pet.health_points);
    }
    if (user.subscription_tier !== 'Premium') {
      document.getElementById('premium-banner').classList.remove('hidden');
    }
  } catch (ex) { toast(ex.message, 'error'); }
}

async function loadUploads() {
  const gallery = document.getElementById('uploads-gallery');
  gallery.innerHTML = '<p class="text-muted text-center" style="grid-column:1/-1">Loading…</p>';
  try {
    const uploads = await apiFetch('/uploads/');
    gallery.innerHTML = '';
    if (!uploads || uploads.length === 0) {
      gallery.innerHTML = '<p class="text-muted text-center" style="grid-column:1/-1">No photos uploaded yet.</p>';
      return;
    }
    uploads.forEach(u => {
      const a = document.createElement('a');
      a.href = u.url;
      a.target = '_blank';
      a.rel = 'noopener';
      a.title = u.filename;
      const img = document.createElement('img');
      img.src = u.url;
      img.alt = u.filename;
      img.loading = 'lazy';
      img.style.cssText = 'width:100%;aspect-ratio:1;object-fit:cover;border-radius:8px;border:1px solid #eee';
      a.appendChild(img);
      gallery.appendChild(a);
    });
  } catch (ex) {
    gallery.innerHTML = '';
    toast(ex.message, 'error');
  }
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
    const [pet, lb] = await Promise.all([apiFetch('/pet/'), apiFetch('/leaderboard/')]);
    const isChampion = lb?.user_rank === 1;
    renderPet(pet, isChampion);
    document.getElementById('feed-btn').addEventListener('click', async () => {
      setBtn('feed-btn', true, 'Feed');
      try { renderPet(await apiFetch('/pet/feed/', { method: 'POST' }), isChampion); toast('+10 HP!', 'success'); }
      catch (ex) { toast(ex.message, 'error'); }
      finally { setBtn('feed-btn', false, 'Feed (+10 HP)'); }
    });
    document.getElementById('poke-btn').addEventListener('click', async () => {
      setBtn('poke-btn', true, 'Demo −10 HP');
      try { renderPet(await apiFetch('/pet/poke/', { method: 'POST' }), isChampion); }
      catch (ex) { toast(ex.message, 'error'); }
      finally { setBtn('poke-btn', false, 'Demo −10 HP'); }
    });
  } catch (ex) { toast(ex.message, 'error'); }
}

function renderPet(pet, isChampion = false) {
  const type = PET_TYPES[pet.pet_type] || PET_TYPES.fox;
  const petEl = document.getElementById('pet-emoji');
  petEl.innerHTML = '';
  petEl.classList.add('pet-bubble-wrap');

  const img = document.createElement('img');
  img.style.cssText = 'width:300px;height:300px;object-fit:contain';
  img.alt = type.name;
  img.onerror = () => {
    const fb = document.createElement('span');
    fb.textContent = type.emoji;
    fb.style.fontSize = '180px';
    petEl.replaceChildren(fb);
  };
  img.src = petImage(pet.pet_type, pet.health_points, isChampion);
  if (isChampion) img.style.filter = 'drop-shadow(0 0 18px rgba(255,215,0,0.85))';
  petEl.appendChild(img);
  bindPetClick(img, pet.pet_type);

  document.getElementById('pet-stage').textContent = type.name;
  const stageNameEl = document.getElementById('pet-stage-name');
  if (isChampion) {
    stageNameEl.textContent = '👑 Champion';
    stageNameEl.style.color = '#f59e0b';
  } else {
    stageNameEl.textContent = petStageName(pet.health_points);
    stageNameEl.style.color = hpColor(pet.health_points);
  }
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
      const isFirst = i === 0;
      const normalImg = petImage(e.pet_type, e.health_points);
      const imgSrc = isFirst ? `/static/pets/${e.pet_type || 'fox'}-5.png` : normalImg;
      return `<div class="lb-podium-card rank-${i + 1}${isMe ? ' me' : ''}">
        <div class="lb-podium-medal">${MEDALS[i]}</div>
        <img class="pet-img${isFirst ? ' pet-img-champion' : ''}" src="${imgSrc}" alt="pet"
             onerror="this.onerror=null;this.src='${normalImg}'">
        ${isFirst ? `<div class="lb-champion-label">👑 Champion</div>` : ''}
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
          const type = PET_TYPES[e.pet_type] || PET_TYPES.fox;
          return `<div class="lb-row${isMe ? ' me' : ''}">
            <span class="lb-rank">#${i + 4}</span>
            <img class="lb-pet-img" src="${petImage(e.pet_type, e.health_points)}" alt="pet"
                 onerror="this.outerHTML='<span class=lb-pet>${type.emoji}</span>'">
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
  '/hatch':       initHatch,
};

document.addEventListener('DOMContentLoaded', () => {
  if ('serviceWorker' in navigator) navigator.serviceWorker.register('/static/sw.js').catch(() => {});
  const init = ROUTES[window.location.pathname];
  if (init) init();
});
