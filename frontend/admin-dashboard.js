// ============================================
// ZinoEx Admin API Client (Final Production Version)
// ============================================

const API_BASE = "http://localhost:8000";

// --------------------------------------------
// CORE REQUEST FUNCTION
// --------------------------------------------

async function apiRequest(
  endpoint,
  method = "GET",
  data = null,
  isForm = false,
) {
  const token = localStorage.getItem("access_token");

  const headers = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (!isForm) headers["Content-Type"] = "application/json";

  const config = { method, headers };
  if (data) config.body = isForm ? data : JSON.stringify(data);

  let res;

  try {
    res = await fetch(`${API_BASE}${endpoint}`, config);
  } catch (err) {
    console.error("NETWORK ERROR →", err);
    throw new Error("Network connection failed");
  }

  if (res.status === 401) {
    localStorage.removeItem("access_token");
    alert("Your session has expired. Please log in again.");
    window.location.href = "/frontend/login.html";
    return;
  }

  if (res.status === 204) return null;

  let json;
  try {
    json = await res.json();
  } catch {
    throw new Error("Invalid JSON response from server");
  }

  if (!res.ok) {
    console.error("API ERROR →", json);
    throw new Error(json.detail || json.message || "Request failed");
  }

  return json.data !== undefined ? json.data : json;
}
// ============================================
// ADMIN API
// ============================================

const AdminAPI = {
  // -------------------------------
  // STATS
  // -------------------------------

  getStats() {
    return apiRequest("/api/admin/admin/stats");
  },

  // -------------------------------
  // USERS
  // -------------------------------

  listUsers() {
    return apiRequest("/api/admin/admin/users");
  },

  getUserUsage(userId) {
    return apiRequest(`/api/admin/admin/users/${userId}/usage`);
  },

  deleteUser(userId) {
    return apiRequest(`/api/admin/admin/users/${userId}`, "DELETE");
  },

  makeAdmin(userId) {
    return apiRequest(`/api/admin/admin/users/${userId}/make-admin`, "POST");
  },

  suspendUser(userId) {
    return apiRequest(`/api/admin/admin/users/${userId}/suspend`, "POST");
  },

  activateUser(userId) {
    return apiRequest(`/api/admin/admin/users/${userId}/activate`, "POST");
  },

  // -------------------------------
  // SUBSCRIPTIONS
  // -------------------------------

  listSubscriptions() {
    return apiRequest("/api/admin/admin/subscriptions");
  },

  activateSubscription(data) {
    return apiRequest("/api/admin/admin/subscriptions/activate", "POST", data);
  },

  cancelSubscription(id) {
    return apiRequest(`/api/admin/admin/subscriptions/${id}/cancel`, "POST");
  },

  // -------------------------------
  // PLANS
  // -------------------------------

  listPlans() {
    return apiRequest("/api/admin/admin/plans");
  },

  createPlan(data) {
    return apiRequest("/api/admin/admin/plans", "POST", data);
  },

  updatePlan(id, data) {
    return apiRequest(`/api/admin/admin/plans/${id}`, "PUT", data);
  },

  deletePlan(id) {
    return apiRequest(`/api/admin/admin/plans/${id}`, "DELETE");
  },

  enablePlan(id) {
    return apiRequest(`/api/admin/admin/plans/${id}/enable`, "POST");
  },

  disablePlan(id) {
    return apiRequest(`/api/admin/admin/plans/${id}/disable`, "POST");
  },

  // -------------------------------
  // MODULES
  // -------------------------------

  listModules() {
    return apiRequest("/api/admin/admin/modules");
  },

  createModule(data) {
    return apiRequest("/api/admin/admin/modules", "POST", data);
  },

  updateModule(id, data) {
    return apiRequest(`/api/admin/admin/modules/${id}`, "PUT", data);
  },

  deleteModule(id) {
    return apiRequest(`/api/admin/admin/modules/${id}`, "DELETE");
  },

  // -------------------------------
  // INDEX / HOMEPAGE CONTENT
  // -------------------------------

  getIndexContent() {
    return apiRequest("/api/admin/admin/index");
  },

  updateIndexContent(data) {
    return apiRequest("/api/admin/admin/index", "PUT", data);
  },

  batchUpdateContent(data) {
    return apiRequest("/api/admin/admin/content/batch", "PUT", data);
  },

  deleteIndexContent(key) {
    return apiRequest(`/api/admin/admin/index/${key}`, "DELETE");
  },

  // -------------------------------
  // FILES / MEDIA MANAGER
  // -------------------------------

  listFiles() {
    return apiRequest("/api/admin/admin/files");
  },

  uploadFile(file) {
    const fd = new FormData();
    fd.append("file", file);
    return apiRequest("/api/admin/admin/files", "POST", fd, true);
  },

  deleteFile(id) {
    return apiRequest(`/api/admin/admin/files/${id}`, "DELETE");
  },

  // -------------------------------
  // ACTIVITY LOGS
  // -------------------------------

  listActivity() {
    return apiRequest("/api/admin/admin/activity");
  },

  clearActivity() {
    return apiRequest("/api/admin/admin/activity", "DELETE");
  },
};

// --------------------------------------------
// EXPORT TO WINDOW
// --------------------------------------------

window.AdminAPI = AdminAPI;
