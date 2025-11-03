// statics/js/api.js
export function getChatId() {
  // 1) Contexto Telegram real (Main Mini App / direct link / inline)
  const tg = window.Telegram?.WebApp;
  const chat = tg?.initDataUnsafe?.chat;
  if (chat && typeof chat.id !== 'undefined' && chat.id !== null) {
    return String(chat.id);
  }
  const user = tg?.initDataUnsafe?.user;
  if (user && typeof user.id !== 'undefined' && user.id !== null) {
    // En chats privados, el "chat" puede no venir -> usar user.id
    return String(user.id);
  }

  // 2) Inyección de servidor (cuando renderizas con Jinja)
  const fromJinja = (window.__CHAT_ID__ || "").trim();
  if (fromJinja) return fromJinja;

  // 3) Fallback por query (modo desarrollo o enlaces manuales)
  const qs = new URLSearchParams(location.search);
  const fromQuery = qs.get('chat_id');
  return fromQuery || 'dev';
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

