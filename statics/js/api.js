export function getChatId() {
  const fromJinja = (window.__CHAT_ID__ || "").trim();
  if (fromJinja) return fromJinja;
  const qs = new URLSearchParams(location.search);
  return qs.get('chat_id') || 'dev';
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
