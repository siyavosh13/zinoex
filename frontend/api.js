// api.js - ZinoEx Frontend API Helper

window.API_BASE = window.location.origin + "/api";

// Token Management
function getToken() {
  return localStorage.getItem("access_token");
}

function setToken(token) {
  localStorage.setItem("access_token", token);
}

function removeToken() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("user");
}

// API Request Helper
async function apiRequest(endpoint, options = {}) {
  const token = getToken();

  const defaultHeaders = {
    "Content-Type": "application/json",
  };

  if (token) {
    defaultHeaders["Authorization"] = `Bearer ${token}`;
  }

  const headers =
    options.body instanceof FormData
      ? token
        ? { Authorization: `Bearer ${token}` }
        : {}
      : defaultHeaders;

  const config = {
    ...options,
    headers: {
      ...headers,
      ...options.headers,
    },
  };

  try {
    const response = await fetch(`${API_BASE}${endpoint}`, config);

    let data = {};
    try {
      data = await response.json();
    } catch (e) {}

    if (!response.ok) {
      if (response.status === 401) {
        throw new Error("Unauthorized");
      }

      const message =
        data.detail ||
        data.message ||
        data.error ||
        JSON.stringify(data) ||
        `API Error: ${response.status}`;

      throw new Error(message);
    }

    return data;
  } catch (error) {
    console.error("API Error:", error);
    throw error;
  }
}

// API Object
const API = {
  // ==================== AUTH ====================

  signup: (data) =>
    apiRequest("/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  login: (data) =>
    apiRequest("/auth/login", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  getMe: () => apiRequest("/auth/me"),

  verifyEmail: (data) =>
    apiRequest("/auth/verify-email", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  resendCode: (data) =>
    apiRequest("/auth/resend-code", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  // ==================== PROFILE ====================

  updateProfile: (data) =>
    apiRequest("/profile/", {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  changePassword: (data) =>
    apiRequest("/profile/password", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  getActivity: (type = "all", skip = 0, limit = 20) =>
    apiRequest(
      `/profile/activity?activity_type=${type}&skip=${skip}&limit=${limit}`,
    ),

  deleteActivity: (id) =>
    apiRequest(`/profile/activity/${id}`, {
      method: "DELETE",
    }),

  getSessions: () => apiRequest("/profile/sessions"),

  revokeSession: (id) =>
    apiRequest(`/profile/sessions/${id}`, {
      method: "DELETE",
    }),

  getStats: () => apiRequest("/profile/stats"),

  // ==================== CONTRACTS ====================

  generateContract: (data) =>
    apiRequest("/contracts/generate", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  // ==================== CONTRACT CHAT ====================
  // Added for AI contract chat page integration.
  // These endpoints use the existing apiRequest helper, token handling,
  // and API_BASE structure without changing other parts of the app.

  chatMessage: (payload) =>
    apiRequest("/contracts/chat/message", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  getChatSession: (sessionId) =>
    apiRequest(`/contracts/chat/session/${encodeURIComponent(sessionId)}`),

  getMyChatSessions: () => apiRequest("/contracts/chat/sessions/me"),

  // ==================== CUSTOM CONTRACTS ====================

  generateCustomQuestions: (data) =>
    apiRequest("/contracts/custom/questions", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  generateCustomFinal: (data) =>
    apiRequest("/contracts/custom/generate", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  createContract: (data) =>
    apiRequest("/contracts/", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  getContracts: (skip = 0, limit = 20) =>
    apiRequest(`/contracts/?skip=${skip}&limit=${limit}`),

  getContract: (id) => apiRequest(`/contracts/${id}`),

  reviewContract: (id) =>
    apiRequest(`/contracts/${id}/review`, {
      method: "POST",
    }),

  uploadContract: async (file, title = "Uploaded Contract") => {
    const formData = new FormData();

    formData.append("file", file);
    formData.append("title", title);

    return apiRequest("/contracts/upload", {
      method: "POST",
      body: formData,
    });
  },

  deleteContract: (id) =>
    apiRequest(`/contracts/${id}`, {
      method: "DELETE",
    }),

  reviewText: (contractText, language = "English") =>
    fetch(`${API_BASE}/contracts/review`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ contract_text: contractText, language }),
    }).then(async (res) => {
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(
          `Server error: ${res.status} - ${err.detail || "Unknown error"}`,
        );
      }
      return res.json();
    }),

  reviewFile: (file, language = "English") => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("language", language);

    return apiRequest("/contracts/review-file", {
      method: "POST",
      body: formData,
    });
  },

  // ==================== BLOCKCHAIN ====================

  embedContract: (contractId, signers) =>
    apiRequest("/blockchain/embed", {
      method: "POST",
      body: JSON.stringify({
        contract_id: contractId,
        signers: signers,
      }),
    }),

  verifyContractByFile: async (file) => {
    const formData = new FormData();
    formData.append("file", file);

    return apiRequest("/blockchain/verify/file", {
      method: "POST",
      body: formData,
    });
  },

  verifyContractByHash: (hash) =>
    apiRequest("/blockchain/verify/hash", {
      method: "POST",
      body: JSON.stringify({ contract_hash: hash }),
    }),

  getBlockchainHistory: (skip = 0, limit = 20) =>
    apiRequest(`/blockchain/history?skip=${skip}&limit=${limit}`),

  getBlockchainStats: () => apiRequest("/blockchain/stats"),

  // ==================== SUBSCRIPTION ====================

  getSubscription: () => apiRequest("/subscription/"),

  upgradeSubscription: (plan) =>
    apiRequest("/subscription/upgrade", {
      method: "POST",
      body: JSON.stringify({ plan: plan }),
    }),

  cancelSubscription: () =>
    apiRequest("/subscription/cancel", {
      method: "POST",
    }),

  getBillingHistory: () => apiRequest("/subscription/billing"),

  // ==================== DASHBOARD ====================

  getDashboardStats: () => apiRequest("/dashboard/stats"),

  // =====================================================
  // ADMIN API (FIXED TO MATCH BACKEND ROUTES)
  // =====================================================

  adminGetUsers: (skip = 0, limit = 50) =>
    apiRequest(`/admin/admin/users?skip=${skip}&limit=${limit}`),

  adminGetUser: (id) => apiRequest(`/admin/admin/users/${id}`),

  adminDeleteUser: (id) =>
    apiRequest(`/admin/admin/users/${id}`, {
      method: "DELETE",
    }),

  adminMakeUserAdmin: (id) =>
    apiRequest(`/admin/admin/users/${id}/make-admin`, {
      method: "POST",
    }),

  adminActivateSubscription: (data) =>
    apiRequest(`/admin/admin/subscriptions/activate`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  adminGetAllSubscriptions: (skip = 0, limit = 50) =>
    apiRequest(`/admin/admin/subscriptions?skip=${skip}&limit=${limit}`),

  adminCancelSubscription: (id) =>
    apiRequest(`/admin/admin/subscriptions/${id}`, {
      method: "DELETE",
    }),

  adminGetPlans: () => apiRequest("/admin/admin/plans"),

  adminGetPlan: (id) => apiRequest(`/admin/admin/plans/${id}`),

  adminCreatePlan: (data) =>
    apiRequest("/admin/admin/plans", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  adminUpdatePlan: (id, data) =>
    apiRequest(`/admin/admin/plans/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  adminDeletePlan: (id) =>
    apiRequest(`/admin/admin/plans/${id}`, {
      method: "DELETE",
    }),

  adminGetModules: () => apiRequest("/admin/admin/modules"),

  adminCreateModule: (data) =>
    apiRequest("/admin/admin/modules", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  adminUpdateModule: (id, data) =>
    apiRequest(`/admin/admin/modules/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  adminDeleteModule: (id) =>
    apiRequest(`/admin/admin/modules/${id}`, {
      method: "DELETE",
    }),

  adminGetFiles: () => apiRequest("/admin/admin/files"),

  adminDeleteFile: (id) =>
    apiRequest(`/admin/admin/files/${id}`, {
      method: "DELETE",
    }),

  adminGetActivity: (skip = 0, limit = 50) =>
    apiRequest(`/admin/admin/activity?skip=${skip}&limit=${limit}`),

  adminGetIndex: () => apiRequest("/admin/admin/index"),

  adminUpdateIndex: (data) =>
    apiRequest("/admin/admin/index", {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  adminDeleteIndex: (key) =>
    apiRequest(`/admin/admin/index/${encodeURIComponent(key)}`, {
      method: "DELETE",
    }),
};

// Helper Functions
function isLoggedIn() {
  return getToken() !== null;
}

function requireAuth() {
  if (!isLoggedIn()) {
    window.location.href = "/login.html";
    return false;
  }
  return true;
}

function logout() {
  removeToken();
  window.location.href = "/login.html";
}

// =====================================================
// ADMIN PANEL COMPATIBILITY WRAPPER
// =====================================================

window.AdminAPI = {
  getStats: () => API.getDashboardStats(),

  listUsers: (skip = 0, limit = 50) => API.adminGetUsers(skip, limit),

  getUser: (id) => API.adminGetUser(id),

  deleteUser: (id) => API.adminDeleteUser(id),

  makeAdmin: (id) => API.adminMakeUserAdmin(id),

  listSubscriptions: (skip = 0, limit = 50) =>
    API.adminGetAllSubscriptions(skip, limit),

  activateSubscription: (data) => API.adminActivateSubscription(data),

  cancelSubscription: (id) => API.adminCancelSubscription(id),

  listPlans: () => API.adminGetPlans(),

  createPlan: (data) => API.adminCreatePlan(data),

  updatePlan: (id, data) => API.adminUpdatePlan(id, data),

  deletePlan: (id) => API.adminDeletePlan(id),

  listModules: () => API.adminGetModules(),

  createModule: (data) => API.adminCreateModule(data),

  updateModule: (id, data) => API.adminUpdateModule(id, data),

  deleteModule: (id) => API.adminDeleteModule(id),

  listFiles: () => API.adminGetFiles(),

  deleteFile: (id) => API.adminDeleteFile(id),

  listActivity: (skip = 0, limit = 50) => API.adminGetActivity(skip, limit),

  getIndexContent: () => API.adminGetIndex(),

  updateIndexContent: (data) => API.adminUpdateIndex(data),

  deleteIndexContent: (key) => API.adminDeleteIndex(key),
};

// =====================================================
// GLOBAL API EXPORT
// =====================================================
// This makes the API object available as window.API.
// The contract chat HTML checks window.API.chatMessage before using it.

window.API = API;
