// statics/js/main.js
import { getChatId } from './api.js';
import { refs, state, tg } from './state.js';
import { ensureGrid } from './numbers.js';
import { loadCfg, applyCfgToUI, collectCfgFromUI, cfgChanged, saveSettings, setTheme, getTheme } from './settings.js';
import { loadStats, doSend, doRollback, doReset } from './actions.js';

state.chatId = getChatId();
setTheme(getTheme()); // oscuro por defecto

// ---- FULLSCREEN helpers ----
function updateFullscreenLabel() {
  // Algunas builds exponen booleano 'isFullscreen'; otras emiten payload en evento
  const on = !!(tg && (tg.isFullscreen === true));
  if (refs.btnFullscreen) {
    refs.btnFullscreen.textContent = on ? '🗗 Salir de pantalla completa' : '⛶ Pantalla completa';
  }
}
async function toggleFullscreen() {
  if (!tg) return;
  try {
    if (tg.isFullscreen) {
      await tg.exitFullscreen?.();
    } else {
      // Importante: normalmente requiere gesto del usuario (click)
      await tg.requestFullscreen?.();
    }
  } catch (e) {
    console.warn('fullscreen toggle failed', e);
  } finally {
    updateFullscreenLabel();
  }
}

// Algunos clientes disparan eventos
try {
  tg?.onEvent?.('fullscreenChanged', (e) => {
    // e?.is_fullscreen puede venir en algunos SDKs; en webview móvil tg.isFullscreen se actualiza
    updateFullscreenLabel();
  });
  tg?.onEvent?.('fullscreenFailed', (e) => {
    console.warn('fullscreenFailed', e);
  });
} catch {}

// ---- Navegación de vistas ----
function setActiveView(name){
  state.view = name;
  // secciones
  refs.viewStats.classList.toggle('active', name === 'stats');
  refs.viewNumbers.classList.toggle('active', name === 'numbers');
  refs.viewSettings.classList.toggle('active', name === 'settings');
  // toolbar principal: solo visible en estadísticas
  if (refs.toolbar) refs.toolbar.style.display = (name === 'stats') ? 'flex' : 'none';
}

function showStatsView(){
  setActiveView('stats');
  state.selected = null;
  if (refs.grid) [...refs.grid.children].forEach(c => c.classList.remove('selected'));
}
function showNumbersView(){
  setActiveView('numbers');
  state.selected = null;
  if (refs.grid) [...refs.grid.children].forEach(c => c.classList.remove('selected'));
  refs.btnSaveNumber.disabled = true;
}
function showSettingsView(){
  setActiveView('settings');
  applyCfgToUI();
  refs.btnSaveSettings.disabled = true;
}

// ----- helpers de confirmación -----
function disarmReset(){
  state.resetArmed = false;
  if (state.resetTm) { clearTimeout(state.resetTm); state.resetTm = null; }
  if (refs.btnReset?.dataset?.label) { refs.btnReset.textContent = refs.btnReset.dataset.label; delete refs.btnReset.dataset.label; }
  refs.btnReset?.classList?.remove('danger'); refs.btnReset?.removeAttribute?.('data-armed');
}
function disarmRollback(){
  state.rollbackArmed = false;
  if (state.rollbackTm) { clearTimeout(state.rollbackTm); state.rollbackTm = null; }
  if (refs.btnRollback?.dataset?.label) { refs.btnRollback.textContent = refs.btnRollback.dataset.label; delete refs.btnRollback.dataset.label; }
  refs.btnRollback?.classList?.remove('danger'); refs.btnRollback?.removeAttribute?.('data-armed');
}

// ----- Toolbar principal -----
refs.btnAdd.onclick = showNumbersView;
refs.btnFullscreen.onclick = toggleFullscreen;   // 👈 nuevo

// ➜ Confirmación para “Eliminar último”
refs.btnRollback.onclick = async ()=>{
  if (!state.rollbackArmed) {
    state.rollbackArmed = true;
    refs.btnRollback.dataset.armed = "1";
    refs.btnRollback.dataset.label = refs.btnRollback.textContent;
    refs.btnRollback.textContent = "⚠ Confirmar eliminar";
    refs.btnRollback.classList.add('danger');
    state.rollbackTm = setTimeout(disarmRollback, state.ARM_SECS * 1000);
    return;
  }
  refs.btnRollback.disabled = true;
  try {
    await doRollback();
  } finally {
    refs.btnRollback.disabled = false;
    disarmRollback();
  }
};

refs.btnRefresh.onclick = async ()=>{
  try{
    refs.btnRefresh.disabled = true;
    const t = refs.btnRefresh.textContent;
    refs.btnRefresh.textContent = 'Refrescando…';
    await loadStats(true);
    tg?.HapticFeedback?.impactOccurred?.('light');
    refs.btnRefresh.textContent = t;
  } finally { refs.btnRefresh.disabled = false; }
};

// reset con confirmación (ya existente)
refs.btnReset.onclick = async ()=>{
  if (!state.resetArmed) {
    state.resetArmed = true;
    refs.btnReset.dataset.armed = "1";
    refs.btnReset.dataset.label = refs.btnReset.textContent;
    refs.btnReset.textContent = "⚠ Confirmar reset";
    refs.btnReset.classList.add('danger');
    state.resetTm = setTimeout(disarmReset, state.ARM_SECS * 1000);
    return;
  }
  refs.btnReset.disabled = true;
  try { await doReset(); } finally { refs.btnReset.disabled = false; disarmReset(); }
};

refs.btnSettings.onclick = showSettingsView;

// ----- Números -----
refs.btnSaveNumber.onclick = async ()=>{ await doSend(); showStatsView(); };
refs.btnCancelNumber.onclick = showStatsView;

// ----- Ajustes -----
import { refs as _r } from './state.js';
import { cfgChanged as _cc } from './settings.js';

if (refs.pills) {
  refs.pills.addEventListener('click', (e)=>{
    const btn = e.target.closest('[data-size]'); if (!btn) return;
    const v = parseInt(btn.dataset.size || '0', 10);
    if (Number.isFinite(v) && v > 0) { refs.inpWinCustom.value = v; const tmp = collectCfgFromUI(); refs.btnSaveSettings.disabled = !cfgChanged(tmp, state.originalCfg); }
  });
}
[refs.inpWinCustom, refs.inpCap, refs.inpHistTail].forEach(el=>{
  if (!el) return; const ev = (el.type === 'checkbox') ? 'change' : 'input';
  el.addEventListener(ev, ()=>{ const tmp = collectCfgFromUI(); refs.btnSaveSettings.disabled = !cfgChanged(tmp, state.originalCfg); });
});
[refs.radioSrcWindow, refs.radioSrcHistory].forEach(r=>{
  if (!r) return;
  r.addEventListener('change', ()=>{
    refs.inpHistTail.disabled = !refs.radioSrcHistory.checked;
    const tmp = collectCfgFromUI();
    refs.btnSaveSettings.disabled = !cfgChanged(tmp, state.originalCfg);
  });
});

// ----- Arranque -----
(async ()=>{
  // Ajusta el webview a altura completa del cliente Telegram
  try { tg?.ready?.(); tg?.expand?.(); } catch {}

  updateFullscreenLabel();

  ensureGrid(refs.grid, (n)=>{ state.selected = n; refs.btnSaveNumber.disabled = (state.selected === null); });
  await loadCfg();
  applyCfgToUI();
  showStatsView();
  await loadStats();
  setInterval(async ()=>{ if (state.fetching || document.hidden) return; state.fetching = true; try { await loadStats(); } finally { state.fetching = false; } }, state.POLL_MS);
})();

