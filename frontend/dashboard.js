document.addEventListener("DOMContentLoaded", async () => {
  const token = localStorage.getItem("access_token");

  if (!token) {
    window.location.href = "login.html";
    return;
  }

  const headers = {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
  };

  const safeSet = (id, value) => {
    const el = document.getElementById(id);
    if (el) el.innerText = value ?? "-";
  };

  // آدرس API های اصلاح‌شده
  const API_BASE = "/api/dashboard";

  try {
    // ---------------- USER ----------------
    const meRes = await fetch(`${API_BASE}/me`, { headers });
    if (!meRes.ok) throw new Error("User info fetch failed");
    const user = await meRes.json();

    safeSet("user-email", user.email);
    safeSet("user-plan", user.plan);

    // ---------------- STATS ----------------
    const statsRes = await fetch(`${API_BASE}/stats`, { headers });
    if (!statsRes.ok) throw new Error("Stats fetch failed");
    const stats = await statsRes.json();

    safeSet("stat-contracts", stats.contracts);
    safeSet("stat-reviews", stats.reviews);
    safeSet("stat-blockchain", stats.blockchain);

    // ---------------- ACTIVITY ----------------
    const activityRes = await fetch(`${API_BASE}/activity`, { headers });
    if (!activityRes.ok) throw new Error("Activity fetch failed");
    const activity = await activityRes.json();

    const container = document.getElementById("activity-list");
    container.innerHTML = "";

    if (Array.isArray(activity) && activity.length) {
      activity.forEach((item) => {
        const div = document.createElement("div");

        div.className = "activity-item p-3 border border-gray-200 rounded mb-2";

        div.innerHTML = `
          <div class="font-semibold text-gray-800">${item.event_type}</div>
          <div class="text-gray-600">${item.message}</div>
          <div class="text-xs text-gray-400 mt-1">
            ${new Date(item.time).toLocaleString()}
          </div>
        `;

        container.appendChild(div);
      });
    } else {
      container.innerHTML =
        '<p class="text-gray-500 text-sm">No recent activity.</p>';
    }
  } catch (err) {
    // نمایش خطا در صفحه و لاگ
    console.error("Dashboard load error:", err);
    const container = document.getElementById("activity-list");
    if (container)
      container.innerHTML =
        `<p class="text-red-500 text-sm">Dashboard error: ${err.message}</p>`;
  }
});
