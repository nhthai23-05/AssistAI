const API_BASE = "http://localhost:8000";

async function apiFetch(path, options = {}) {
  const { body, headers, ...rest } = options;
  const res = await fetch(API_BASE + path, {
    credentials: "include",
    headers: { "Content-Type": "application/json", ...(headers || {}) },
    body: body !== undefined ? JSON.stringify(body) : undefined,
    ...rest,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    let msg = `HTTP ${res.status}`;
    if (err.detail) {
      msg = Array.isArray(err.detail)
        ? err.detail.map(d => d.msg || JSON.stringify(d)).join("; ")
        : String(err.detail);
    } else if (err.message) {
      msg = err.message;
    }
    console.error(`API ${res.status}`, path, err);
    throw new Error(msg);
  }
  return res.json();
}

const API = {
  base: API_BASE,

  // Auth
  authStatus: (userId) =>
    apiFetch(`/api/auth/status?user_id=${userId}`),
  logout: (userId) =>
    apiFetch(`/api/auth/logout?user_id=${userId}`, { method: "POST" }),

  // Chat sessions
  listSessions: (userId, limit = 30) =>
    apiFetch(`/api/chat/sessions?user_id=${userId}&limit=${limit}`),
  deleteSession: (userId, sessionId) =>
    apiFetch(`/api/chat/sessions/${sessionId}?user_id=${userId}`, { method: "DELETE" }),

  // Chat messages
  sendMessage: (userId, message, sessionId = null, imageBase64 = null) =>
    apiFetch(`/api/chat/message?user_id=${userId}`, {
      method: "POST",
      body: {
        message,
        session_id: sessionId,
        ...(imageBase64 ? { image_base64: imageBase64 } : {}),
      },
    }),
  getChatHistory: (userId, sessionId, limit = 50) =>
    apiFetch(`/api/chat/history?user_id=${userId}&session_id=${sessionId}&limit=${limit}`),
  updateActionStatus: (userId, messageId, actionIdx, status) =>
    apiFetch(`/api/chat/messages/${messageId}/actions/${actionIdx}?user_id=${userId}&status=${encodeURIComponent(status)}`, { method: "PATCH" }),

  // Calendar
  getEvents: (userId, daysAhead = 30, daysBack = 0) =>
    apiFetch(`/api/calendar/events?user_id=${userId}&days_ahead=${daysAhead}&days_back=${daysBack}&max_results=200`),
  createEvent: (userId, data) =>
    apiFetch(`/api/calendar/events?user_id=${userId}`, { method: "POST", body: data }),
  updateEvent: (userId, eventId, data) =>
    apiFetch(`/api/calendar/events/${encodeURIComponent(eventId)}?user_id=${userId}`, { method: "PUT", body: data }),
  deleteEvent: (userId, eventId) =>
    apiFetch(`/api/calendar/events/${encodeURIComponent(eventId)}?user_id=${userId}`, { method: "DELETE" }),

  // Sheets
  getExpenses: (userId, limit = 100) =>
    apiFetch(`/api/sheets/expenses?user_id=${userId}&limit=${limit}`),
  getCategories: (userId) =>
    apiFetch(`/api/sheets/categories?user_id=${userId}`),
  getIncomeCategories: (userId) =>
    apiFetch(`/api/sheets/income-categories?user_id=${userId}`),
  getSummary: (userId) =>
    apiFetch(`/api/sheets/summary?user_id=${userId}`),
  addExpense: (userId, expense) =>
    apiFetch(`/api/sheets/expenses?user_id=${userId}`, { method: "POST", body: expense }),
  deleteExpense: (userId, rowNumber) =>
    apiFetch(`/api/sheets/expenses/${rowNumber}?user_id=${userId}`, { method: "DELETE" }),
  updateExpense: (userId, rowNumber, expense) =>
    apiFetch(`/api/sheets/expenses/${rowNumber}?user_id=${userId}`, { method: "PUT", body: expense }),
  updateBalance: (userId, data) =>
    apiFetch(`/api/sheets/balance?user_id=${userId}`, { method: "PUT", body: data }),
  updateBudget: (userId, data) =>
    apiFetch(`/api/sheets/budget?user_id=${userId}`, { method: "PUT", body: data }),
  addCategory: (userId, data) =>
    apiFetch(`/api/sheets/categories?user_id=${userId}`, { method: "POST", body: data }),
  deleteCategory: (userId, data) =>
    apiFetch(`/api/sheets/categories?user_id=${userId}`, { method: "DELETE", body: data }),

  // Income transactions (Giao dịch sheet, columns G:J)
  getIncomeTransactions: (userId, limit = 100) =>
    apiFetch(`/api/sheets/income-transactions?user_id=${userId}&limit=${limit}`),
  addIncome: (userId, income) =>
    apiFetch(`/api/sheets/income?user_id=${userId}`, { method: "POST", body: income }),
  updateIncome: (userId, rowNumber, income) =>
    apiFetch(`/api/sheets/income/${rowNumber}?user_id=${userId}`, { method: "PUT", body: income }),
  deleteIncome: (userId, rowNumber) =>
    apiFetch(`/api/sheets/income/${rowNumber}?user_id=${userId}`, { method: "DELETE" }),
};

export default API;
