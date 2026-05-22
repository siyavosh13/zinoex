document.addEventListener("DOMContentLoaded", () => {
  const token = localStorage.getItem("access_token");

  if (!token) {
    window.location.href = "login.html";
    return;
  }

  const headers = {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
  };

  const setValue = (id, value) => {
    const el = document.getElementById(id);
    if (el) el.value = value ?? "";
  };

  const setText = (id, value) => {
    const el = document.getElementById(id);
    if (el) el.innerText = value ?? "";
  };

  // ===============================
  // LOAD PROFILE DATA
  // ===============================
  fetch("/api/profile/profile/me", { headers })
    .then((res) => {
      if (res.status === 401) {
        window.location.href = "login.html";
        return;
      }
      return res.json();
    })
    .then((data) => {
      console.log("Profile loaded:", data);

      // Header Section
      setText("profile_name", data.full_name || data.username);
      setText("email_display", data.email);
      setText("profile_plan", data.plan);

      // Form Fields
      setValue("first_name", data.first_name);
      setValue("last_name", data.last_name);
      setValue("username", data.username);
      setValue("email", data.email);
      setValue("phone", data.phone_number);
      setValue("company", data.company_name);
    })
    .catch((err) => console.error("Load profile error:", err));

  // ===============================
  // UPDATE PROFILE
  // ===============================
  const profileForm = document.getElementById("profile_form");

  if (profileForm) {
    profileForm.addEventListener("submit", (e) => {
      e.preventDefault();

      const body = {
        first_name: document.getElementById("first_name").value,
        last_name: document.getElementById("last_name").value,
        username: document.getElementById("username").value,
        phone_number: document.getElementById("phone").value,
        company_name: document.getElementById("company").value,
      };

      fetch("/api/profile/profile/update", {
        method: "PUT",
        headers,
        body: JSON.stringify(body),
      })
        .then((res) => res.json())
        .then((data) => {
          console.log("Profile updated:", data);
          alert("اطلاعات با موفقیت بروزرسانی شد ✅");
        })
        .catch((err) => console.error("Update error:", err));
    });
  }

  // ===============================
  // CHANGE PASSWORD
  // ===============================
  const passwordForm = document.getElementById("password_form");

  if (passwordForm) {
    passwordForm.addEventListener("submit", (e) => {
      e.preventDefault();

      const newPass = document.getElementById("new_password").value;
      const confirmPass = e.target.querySelectorAll("input[type=password]")[2]
        .value;

      if (newPass !== confirmPass) {
        alert("رمز جدید و تایید آن یکسان نیست ❌");
        return;
      }

      const body = {
        old_password: document.getElementById("current_password").value,
        new_password: newPass,
      };

      fetch("/api/profile/profile/change-password", {
        method: "PUT",
        headers,
        body: JSON.stringify(body),
      })
        .then((res) => res.json())
        .then((data) => {
          if (data.detail) {
            alert("Error: " + data.detail);
            return;
          }

          alert("رمز عبور با موفقیت تغییر کرد ✅");
          passwordForm.reset();
        })
        .catch((err) => console.error("Password change error:", err));
    });
  }
});
