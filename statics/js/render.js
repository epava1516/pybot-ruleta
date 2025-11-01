import { twoCol, tripletRow, filasStack, LABELS, fmtPct } from './ui.js';

export function renderStats(statsBox, payload){
  const s = payload && payload.stats;
  if (!s){
    statsBox.innerHTML = `<div class="muted">No hay datos aún.</div>`;
    return;
  }

  const meta = (s && s._meta) || {};
  const source = meta.source || 'window';
  const histTail = Number(meta.hist_tail || 0);
  const cap = meta.window_capacity ?? (payload && payload.window);

  const arr = Array.isArray(s.numbers) ? s.numbers : [];
  const len = arr.length;
  const rollsHtml = arr.length
    ? arr.map(([n,c])=>`<span class="pill">${n}${c?` ${c}`:''}</span>`).join('')
    : '<span class="muted">—</span>';

  const p = s.percents || {};
  const docVals = (p.docenas && Array.isArray(p.docenas)) ? p.docenas : [0,0,0];
  const rowVals = (p.filas   && Array.isArray(p.filas))   ? p.filas   : [0,0,0];

  const colores = twoCol('🎨 Colores', [
    ['<span class="dot red"></span> Rojo',    fmtPct(p.rojo)],
    ['<span class="dot black"></span> Negro', fmtPct(p.negro)],
  ]);
  const paridad = twoCol('🔢 Paridad', [['Par', fmtPct(p.par)], ['Impar', fmtPct(p.impar)]]);
  const rangos  = twoCol('📏 Rangos',  [['⬇ 1–18', fmtPct(p.bajos)], ['⬆ 19–36', fmtPct(p.altos)]]);
  const cero    = twoCol('🟢 Cero',    [['0', fmtPct(p.cero)]], { highlight:false });

  const docenas = tripletRow('📦 Docenas', LABELS.docenas, docVals);
  const filas   = filasStack(rowVals);

  const headInfo = (source === 'history')
    ? `<div><strong>Fuente:</strong> Historial (K=${histTail}) — ${len} tiradas</div>`
    : `<div><strong>Fuente:</strong> Ventana (${len} / ${cap ?? '-'})</div>`;

  statsBox.innerHTML = `
    <div class="line muted" style="margin-bottom:6px;">
      ${headInfo}
      <div class="grow"></div>
      <div><strong>Desde último 0:</strong> ${s.since_last_0 ?? 0}</div>
    </div>

    <div class="section">
      <div class="section-title">🎰 Tiradas (${source === 'history' ? 'historial' : 'ventana'} completa)</div>
      <div class="lastrolls">${rollsHtml}</div>
    </div>

    ${colores}
    ${paridad}
    ${rangos}
    ${cero}
    ${docenas}
    ${filas}
  `;
}

export function tagOf(payload){
  const s = payload && payload.stats;
  if (!s) return 'empty';
  const len = (s.numbers || []).length;
  const since = s.since_last_0 ?? 0;
  return `${len}|${since}`;
}
