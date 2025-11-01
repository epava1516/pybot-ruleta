const ROJO = new Set([1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36]);


export function ensureGrid(gridEl, onSelect){
  if (!gridEl || gridEl.childElementCount) return;

  function cell(n) {
    const div = document.createElement('div');
    div.className = 'btn-num ' + (n === 0 ? 'zero' : (ROJO.has(n) ? 'red' : 'black'));
    div.textContent = n;
    div.onclick = () => {
      [...gridEl.children].forEach(c => c.classList.remove('selected'));
      div.classList.add('selected');
      onSelect(n);
    };
    return div;
  }

  gridEl.appendChild(cell(0));
  for (let n = 1; n <= 36; n++) gridEl.appendChild(cell(n));
}
