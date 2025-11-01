import { API } from './api.js';
import { tg, refs, state } from './state.js';
import { renderStats, tagOf } from './render.js';

export async function loadStats(force = false){
  const r = await API.stats(state.chatId, state.lastEtag);

  // 304 → nada que hacer
  if (r.status === 304) return;

  // cachea ETag si llega
  const et = r.headers.get('ETag');
  if (et) state.lastEtag = et;

  const j = await r.json();
  const tag = tagOf(j);

  if (force || tag !== state.lastTag) {
    renderStats(refs.statsBox, j);
    state.lastTag = tag;
  }
}

export async function doSend(){
  if (state.selected === null) { alert('Selecciona un número primero'); return; }
  try {
    const r = await API.roll(state.chatId, state.selected);
    const j = await r.json();
    renderStats(refs.statsBox, j);
    state.lastTag = tagOf(j);
    state.lastEtag = null; // invalida ETag para próxima lectura
    tg?.HapticFeedback?.impactOccurred?.('light');
  } catch { alert('Error enviando número'); }
}

export async function doRollback(){
  try {
    const r = await API.rollback(state.chatId);
    const j = await r.json();
    renderStats(refs.statsBox, j);
    state.lastTag = tagOf(j);
    state.lastEtag = null;
  } catch { alert('Error al eliminar'); }
}

export async function doReset(){
  try {
    const r = await API.reset(state.chatId);
    if (!r.ok) throw new Error(await r.text());
    const j = await r.json();
    state.selected = null;
    if (refs.grid) [...refs.grid.children].forEach(c => c.classList.remove('selected'));
    renderStats(refs.statsBox, j);
    state.lastTag = tagOf(j);
    state.lastEtag = null;
    tg?.HapticFeedback?.impactOccurred?.('light');
  } catch (e) {
    console.error('reset error', e);
    alert('Error al resetear');
  }
}
