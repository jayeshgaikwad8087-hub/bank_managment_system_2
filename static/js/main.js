// ---------- Theme toggle (persists per-tab, no reliance on server) ----------
(function () {
  const root = document.documentElement;
  const saved = localStorage.getItem("dsg-theme");
  if (saved) root.setAttribute("data-theme", saved);

  window.toggleTheme = function () {
    const current = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
    root.setAttribute("data-theme", current);
    try { localStorage.setItem("dsg-theme", current); } catch (e) {}
    const btn = document.getElementById("themeToggleBtn");
    if (btn) btn.textContent = current === "dark" ? "☀️" : "🌙";
  };

  document.addEventListener("DOMContentLoaded", () => {
    const btn = document.getElementById("themeToggleBtn");
    if (btn) btn.textContent = root.getAttribute("data-theme") === "dark" ? "☀️" : "🌙";
  });
})();

// ---------- Sidebar toggle for mobile ----------
function toggleSidebar() {
  const sidebar = document.querySelector(".sidebar");
  if (sidebar) sidebar.classList.toggle("open");
}

// ---------- Toast notifications ----------
function showToast(message, type = "info") {
  let container = document.getElementById("toast-container");
  if (!container) {
    container = document.createElement("div");
    container.id = "toast-container";
    document.body.appendChild(container);
  }
  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 4700);
}

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".flash-message").forEach((el) => {
    showToast(el.dataset.message, el.dataset.category || "info");
  });
});

// ---------- Password strength meter ----------
function checkPasswordStrength(inputEl, barEl, labelEl) {
  const value = inputEl.value;
  let score = 0;
  if (value.length >= 8) score++;
  if (/[A-Z]/.test(value)) score++;
  if (/[a-z]/.test(value)) score++;
  if (/\d/.test(value)) score++;
  if (/[!@#$%^&*()_+\-=]/.test(value)) score++;

  const percent = (score / 5) * 100;
  const colors = ["#ff4d5e", "#ff4d5e", "#ffb020", "#ffb020", "#00d0a4", "#00a884"];
  const labels = ["Very weak", "Weak", "Fair", "Good", "Strong", "Very strong"];

  barEl.style.width = percent + "%";
  barEl.style.background = colors[score];
  if (labelEl) labelEl.textContent = labels[score];
}

// ---------- Simple modal helper ----------
function openModal(id) {
  const el = document.getElementById(id);
  if (el) el.classList.add("active");
}
function closeModal(id) {
  const el = document.getElementById(id);
  if (el) el.classList.remove("active");
}

// ---------- Confirm dialogs for destructive actions ----------
document.addEventListener("submit", (e) => {
  const form = e.target;
  if (form.dataset.confirm) {
    if (!window.confirm(form.dataset.confirm)) {
      e.preventDefault();
    }
  }
});

// ---------- Skeleton loading simulation on slow pages ----------
window.addEventListener("load", () => {
  document.querySelectorAll(".skeleton-wrap").forEach((el) => el.classList.add("loaded"));
});
