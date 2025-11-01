export const tg = window.Telegram?.WebApp;

export const refs = {
  viewStats:   document.getElementById('view-stats'),
  viewNumbers: document.getElementById('view-numbers'),
  viewSettings:document.getElementById('view-settings'),

  statsBox:    document.getElementById('stats'),
  grid:        document.getElementById('grid'),

  btnAdd:      document.getElementById('btnAdd'),
  btnRollback: document.getElementById('btnRollback'),
  btnReset:    document.getElementById('btnReset'),
  btnRefresh:  document.getElementById('btnRefresh'),
  btnSettings: document.getElementById('btnSettings'),

  btnSaveNumber:   document.getElementById('btnSaveNumber'),
  btnCancelNumber: document.getElementById('btnCancelNumber'),

  // ajustes
  pills:        document.getElementById('cfg-window-pills'),
  inpWinCustom: document.getElementById('cfg-window-custom'),
  inpCap:       document.getElementById('cfg-history-cap'),
  inpHistTail:  document.getElementById('cfg-hist-tail'),
  radioSrcWindow:  document.getElementById('cfg-source-window'),
  radioSrcHistory: document.getElementById('cfg-source-history'),
  segTheme:     document.getElementById('cfg-theme'),

  btnSaveSettings:    document.getElementById('btnSaveSettings'),
  btnDiscardSettings: document.getElementById('btnDiscardSettings'),
};

export const state = {
  view: 'stats',
  selected: null,
  lastTag: null,
  lastEtag: null,   // 👈 ETag cacheado
  fetching: false,
  chatId: null,
  cfg: { window: 15, history_cap: 20, hist_tail: 0 },
  originalCfg: {},
  resetArmed: false,
  resetTm: null,
  ARM_SECS: 4,
  POLL_MS: 1500,
};

// rojo para la cuadrícula
export const ROJO = new Set([1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36]);
