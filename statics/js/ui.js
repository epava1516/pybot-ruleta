export function fmtPct(x){ return (typeof x === 'number') ? `${x.toFixed(1)}%` : '-'; }
export function pill(n, c){ return `<span class="pill">${n}${c?` ${c}`:''}</span>`; }

export function indicesTernario(values = []) {
  const v = values.map(x => Number.isFinite(x) ? x : 0);
  if (v.length !== 3) return [];
  if (v[0] === v[1] && v[1] === v[2]) return []; // todos iguales -> no resaltar
  const max = Math.max(...v);
  const idxMax = v.map((x,i)=> x === max ? i : -1).filter(i=> i >= 0);
  if (idxMax.length === 1) {
    const imax = idxMax[0];
    if (max === 100) return [imax];
    const others = v.map((x,i)=>({x,i})).filter(o => o.i !== imax);
    if (others[0].x === others[1].x) return [imax];
    const second = (others[0].x > others[1].x) ? others[0].i : others[1].i;
    return [imax, second];
  }
  return idxMax.slice(0, 2);
}

export function twoCol(title, items, opts = { highlight: true }) {
  const parsed = items.map(([lab, val]) => {
    const num = parseFloat(String(val).replace(",", "."));
    return { lab, val, num: Number.isFinite(num) ? num : 0 };
  });
  const nums = parsed.map(p => p.num);
  const maxVal = Math.max(...nums);
  const enableHighlight = opts.highlight && maxVal > 0;

  return `
    <div class="section">
      <div class="section-title">${title}</div>
      <div class="two-col">
        ${parsed.map(({ lab, val, num }) => {
          const isHot = enableHighlight && num === maxVal;
          return `
            <div class="metric-card ${isHot ? "hot" : ""}">
              <div class="metric-label ${isHot ? "bold" : ""}">${lab}</div>
              <div class="metric-value ${isHot ? "bold" : ""}">${val}</div>
            </div>
          `;
        }).join("")}
      </div>
    </div>
  `;
}

export const LABELS = { docenas: ["1–12", "13–24", "25–36"], filas: ["Superior", "Central", "Inferior"] };

export function tripletRow(title, labels, values){
  const v = Array.isArray(values) ? values : [0,0,0];
  const top = new Set(indicesTernario(v));
  return `
    <div class="section">
      <div class="section-title">${title}</div>
      <div class="triplet-row">
        ${labels.map((lab,i)=>`
          <div class="triplet-card ${top.has(i)?'hit':''}">
            <div class="lbl">${lab}</div>
            <div class="val">${fmtPct(v[i])}${top.has(i)?'':''}</div>
          </div>
        `).join('')}
      </div>
    </div>
  `;
}

export function filasStack(values){
  const v = Array.isArray(values) ? values : [0,0,0];
  const top = new Set(indicesTernario(v));
  return `
    <div class="section">
      <div class="section-title">🏛 Filas</div>
      <div class="stack">
        ${LABELS.filas.map((lab,i)=>`
          <div class="kv ${top.has(i)?'hit':''}">
            <div class="kv-label">${lab}</div>
            <div class="kv-bar"><div class="kv-fill" style="width:${Math.max(0, Math.min(100, v[i]||0))}%"></div></div>
            <div class="kv-val">${fmtPct(v[i])}${top.has(i)?'':''}</div>
          </div>
        `).join('')}
      </div>
    </div>
  `;
}
