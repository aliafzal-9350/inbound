const getBaseUrl = () => {
  const envUrl = import.meta.env.VITE_API_URL;
  if (envUrl !== undefined && envUrl !== null && envUrl.trim() !== "" && !envUrl.includes("localhost")) {
    return envUrl.trim().replace(/\/$/, "");
  }
  if (typeof window !== "undefined" && window.location.hostname !== "localhost" && window.location.hostname !== "127.0.0.1") {
    if (window.location.port === "5173") {
      return `${window.location.protocol}//${window.location.hostname}:8000`;
    }
    return "/api";
  }
  if (import.meta.env.PROD) {
    return "/api";
  }
  return "http://localhost:8000";
};

const API_URL = getBaseUrl();
const TOKEN_KEY = "ravisn_token";

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

async function request(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  let res;
  try {
    res = await fetch(`${API_URL}${path}`, { ...options, headers });
  } catch (err) {
    throw new Error(`Unable to connect to backend server at ${API_URL}. Please ensure your backend server is running.`);
  }

  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    let msg = "Request failed";
    if (typeof data.detail === "string") {
      msg = data.detail;
    } else if (Array.isArray(data.detail) && data.detail[0]?.msg) {
      msg = data.detail[0].msg;
    }
    throw new Error(msg);
  }
  return data;
}

export const api = {
  signup: (payload) => request("/auth/signup", { method: "POST", body: JSON.stringify(payload) }),
  login: (payload) => request("/auth/login", { method: "POST", body: JSON.stringify(payload) }),
  resetPassword: (email, new_password) =>
    request("/auth/reset-password", { method: "POST", body: JSON.stringify({ email, new_password }) }),
  me: () => request("/auth/me"),
  listKnowledge: () => request("/knowledge"),
  addKnowledge: (payload) => request("/knowledge", { method: "POST", body: JSON.stringify(payload) }),
  uploadKnowledgeFile: async (formData) => {
    const token = getToken();
    const headers = {};
    if (token) headers["Authorization"] = `Bearer ${token}`;
    const res = await fetch(`${API_URL}/knowledge/upload`, {
      method: "POST",
      headers,
      body: formData,
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      let msg = data.detail || "Failed to upload document";
      if (Array.isArray(data.detail) && data.detail[0]?.msg) msg = data.detail[0].msg;
      throw new Error(msg);
    }
    return data;
  },
  deleteKnowledge: (id) => request(`/knowledge/${id}`, { method: "DELETE" }),
  updateKnowledge: (id, payload) => request(`/knowledge/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
  deleteAllKnowledge: () => request("/knowledge/all", { method: "DELETE" }),
  connectWhatsAppOfficial: (payload) =>
    request("/whatsapp/official/connect", { method: "POST", body: JSON.stringify(payload) }),
  startWhatsAppQr: () => request("/whatsapp/qr/start", { method: "POST" }),
  getWhatsAppQrStatus: () => request("/whatsapp/qr/status"),
  disconnectWhatsAppQr: () => request("/whatsapp/qr/disconnect", { method: "POST" }),
  connectFacebook: (payload) => request("/facebook/connect", { method: "POST", body: JSON.stringify(payload) }),
  connectInstagram: (payload) => request("/instagram/connect", { method: "POST", body: JSON.stringify(payload) }),
  listConversations: (channel) => request(`/conversations?channel=${channel}`),
  listMessages: (conversationId) => request(`/conversations/${conversationId}/messages`),
  listBookings: (channel) => request(`/bookings?channel=${channel}`),
  getApiKey: () => request("/settings/api-key"),
  saveApiKey: (openai_api_key) =>
    request("/settings/api-key", { method: "POST", body: JSON.stringify({ openai_api_key }) }),
  getAllApiKeys: () => request("/settings/api-keys"),
  saveProviderKey: (provider, api_key) =>
    request(`/settings/api-keys/${provider}`, { method: "POST", body: JSON.stringify({ api_key }) }),
  deleteProviderKey: (provider) =>
    request(`/settings/api-keys/${provider}`, { method: "DELETE" }),
  listChannels: () => request("/channels"),
  disconnectChannel: (connectionId) =>
    request(`/channels/${connectionId}/disconnect`, { method: "POST" }),
  getSystemPrompt: () => request("/settings/system-prompt"),
  saveSystemPrompt: (system_prompt) =>
    request("/settings/system-prompt", { method: "POST", body: JSON.stringify({ system_prompt }) }),
  testSystemPrompt: (system_prompt, message) =>
    request("/settings/system-prompt/test", { method: "POST", body: JSON.stringify({ system_prompt, message }) }),
};
