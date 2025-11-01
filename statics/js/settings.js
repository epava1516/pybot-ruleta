import { API } from './api.js';
import { refs, state } from './state.js';

const THEME_KEY = 'rb_theme';
export function getTheme(){
  const t = localStorage.getItem(THEME_KEY);
  return (t === 'light' || t === 'dark') ? t : 'dark';
}
export function setTheme(t){
  const theme = (t === 'light') ? 'light' : 'dark';
  document.documentElement.dataset.theme = theme;
  localStorage.setItem(THEME_KEY, theme);
  if (refs.segTheme) {
    [...refs.segTheme.querySelectorAll('.seg-btn')].forEach(b=>{
      b.classList.toggle('active', b.dataset.theme === theme);
    });
  }
}

export function applyCfgToUI(){
  if (refs.pills) {
    [...refs.pills.querySelectorAll('[data-size]')].forEach(el=>{
      const v = parseInt(el.dataset.size || '0', 10);
      el.classList.toggle('active', v === Number(state.cfg.window));
    });
  }
  if (refs.inpWinCustom) refs.inpWinCustom.value = Number(state.cfg.window);

  const useHistory = (state.cfg.hist_tail || 0) > 0;
  if (refs.radioSrcWindow)  refs.radioSrcWindow.checked  = !useHistory;
  if (refs.radioSrcHistory) refs.radioSrcHistory.checked =  useHistory;
  if (refs.inpHistTail){
    refs.inpHistTail.value = useHistory ? Number(state.cfg.hist_tail) : '';
    refs.inpHistTail.disabled = !useHistory;
  }

  if (refs.inpCap) refs.inpCap.value = (state.cfg.history_cap ?? 20);
  setTheme(getTheme());
}

export function collectCfgFromUI(){
  const out = {...state.cfg};

  let w = Number(refs.inpWinCustom?.value ?? state.cfg.window);
  if (!Number.isFinite(w) || w <= 0) w = state.cfg.window;
  out.window = Math.max(1, Math.floor(w));

  const useHistory = !!refs.radioSrcHistory?.checked;
  if (useHistory) {
    const tail = Number(refs.inpHistTail?.value ?? 0);
    out.hist_tail = Math.max(1, Math.floor(Number.isFinite(tail) ? tail : 1));
  } else {
    out.hist_tail = 0;
  }

  const capVal = Number(refs.inpCap?.value ?? state.cfg.history_cap);
  out.history_cap = Number.isFinite(capVal) && capVal > 0 ? Math.floor(capVal) : 20;

  out._theme = getTheme();
  return out;
}

export function cfgChanged(a, b){
  return a.window !== b.window ||
         (a.history_cap ?? null) !== (b.history_cap ?? null) ||
         (a.hist_tail ?? 0) !== (b.hist_tail ?? 0);
}

export async function loadCfg(){
  try{
    const r = await API.getCfg(state.chatId);
    if (r.ok) {
      const j = await r.json();
      state.cfg = {
        window: Number.isFinite(j.window) ? j.window : state.cfg.window,
        history_cap: (j.history_cap ?? state.cfg.history_cap ?? 20),
        hist_tail: Number.isFinite(j.hist_tail) ? j.hist_tail : 0,
      };
      state.originalCfg = {...state.cfg};
    }
  }catch{}
}

export async function saveSettings(onSaved){
  const newCfg = collectCfgFromUI();
  const { _theme, ...payload } = newCfg;
  try{
    const r = await API.setCfg(state.chatId, payload);
    if (!r.ok) throw new Error(await r.text());
    state.cfg = {...payload};
    state.originalCfg = {...state.cfg};
    setTheme(_theme);
    await onSaved?.();
  }catch{
    alert('No se pudieron guardar los ajustes');
  }
}
