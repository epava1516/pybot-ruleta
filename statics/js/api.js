export function getChatId() {
  // 1) Jinja (solo si vienes con ?chat_id= en modo antiguo)
  const fromJinja = (window.__CHAT_ID__ || "").trim();
  if (fromJinja) return fromJinja;

  // 2) Querystring (compat backward)
  const qs = new URLSearchParams(location.search);
  const fromQs = qs.get('chat_id');
  if (fromQs) return fromQs;

  // 3) Contexto Telegram Mini App (RECOMENDADO)
  const tg = window.Telegram?.WebApp;
  const init = tg?.initDataUnsafe || {};
  // En grupos/canales suele venir chat.id (negativo). En privado, user.id.
  if (init.chat?.id) return String(init.chat.id);
  if (init.user?.id) return String(init.user.id);

  // 4) Fallback dev (solo para entorno local navegador)
  return 'dev';
}

export const API = {
  stats:   (chatId, etag) =>
    fetch(`/api/stats?chat_id=${encodeURIComponent(chatId)}`, {
      headers: etag ? { 'If-None-Match': etag } : undefined,
    }),
  roll:    (chatId, n)    => fetch('/api/roll',     { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ chat_id: chatId, n }) }),
  rollback:(chatId)       => fetch('/api/rollback', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ chat_id: chatId }) }),
  reset:   (chatId)       => fetch('/api/reset',    { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ chat_id: chatId }) }),
  getCfg:  (chatId)       => fetch(`/api/config?chat_id=${encodeURIComponent(chatId)}`),
  setCfg:  (chatId, cfg)  => fetch('/api/config',   { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ chat_id: chatId, ...cfg }) }),
};

