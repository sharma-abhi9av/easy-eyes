// static/js/api.js — Shared Fetch Wrapper, XSS Escaping, Session State & UI Helpers
const EasyEyes = {
  currentUser: null,
  ready: null,

  // Escape untrusted user strings before inserting into innerHTML (Prevents Stored XSS)
  esc(value) {
    return String(value ?? "").replace(/[&<>"']/g, (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
    );
  },

  label(value) {
    return String(value ?? "").replace(/_/g, " ");
  },

  errorMessage(data, status) {
    if (data && typeof data.detail === "string") return data.detail;
    if (data && Array.isArray(data.detail)) {
      return data.detail.map((d) => String(d.msg).replace(/^Value error, /, "")).join(". ");
    }
    return `Request failed (${status})`;
  },

  async request(path, options = {}) {
    const { headers, ...rest } = options;
    const response = await fetch(path, {
      credentials: "same-origin",
      ...rest,
      headers: {
        ...(rest.body ? { "Content-Type": "application/json" } : {}),
        ...(headers || {}),
      },
    });

    let data = null;
    try {
      data = await response.json();
    } catch (_e) {
      data = null;
    }

    if (!response.ok) {
      const err = new Error(EasyEyes.errorMessage(data, response.status));
      err.status = response.status;
      throw err;
    }
    return data;
  },

  formatINR(amount) {
    return "₹" + Number(amount || 0).toLocaleString("en-IN");
  },

  toast(message, isError = false) {
    let el = document.getElementById("global-toast");
    if (!el) {
      el = document.createElement("div");
      el.id = "global-toast";
      el.className = "toast-banner";
      el.setAttribute("role", "status");
      el.setAttribute("aria-live", "polite");
      document.body.appendChild(el);
    }
    el.style.borderLeftColor = isError ? "#DC2626" : "#C5A059";
    el.textContent = message;
    el.classList.add("show");
    clearTimeout(el._timer);
    el._timer = setTimeout(() => el.classList.remove("show"), 3200);
  },

  async requireLogin({ admin = false } = {}) {
    const user = await EasyEyes.ready;
    if (!user || (admin && user.role !== "ADMIN")) {
      window.location.href = user ? "/index.html" : "/login.html";
      return null;
    }
    return user;
  },

  async initNavbar() {
    const authLink = document.getElementById("nav-auth-link");
    const adminLink = document.getElementById("nav-admin-link");
    const logoutBtn = document.getElementById("nav-logout-btn");
    const cartBadge = document.getElementById("nav-cart-count");

    let user = null;
    try {
      const sessionData = await EasyEyes.request("/api/auth/session");
      user = sessionData.user;
    } catch (_e) {
      user = null;
    }
    EasyEyes.currentUser = user;

    if (!user) {
      if (authLink) {
        authLink.textContent = "Sign In";
        authLink.href = "/login.html";
      }
      if (adminLink) adminLink.style.display = "none";
      if (logoutBtn) logoutBtn.style.display = "none";
      if (cartBadge) cartBadge.textContent = "0";
      return null;
    }

    if (authLink) {
      authLink.textContent = user.name.split(" ")[0];
      authLink.href = "/cart.html";
    }
    if (adminLink) {
      adminLink.style.display = user.role === "ADMIN" ? "inline-block" : "none";
    }
    if (logoutBtn) {
      logoutBtn.style.display = "inline-block";
      logoutBtn.onclick = async () => {
        await EasyEyes.request("/api/auth/logout", { method: "POST" });
        window.location.href = "/login.html";
      };
    }
    if (cartBadge) {
      try {
        const cart = await EasyEyes.request("/api/cart");
        cartBadge.textContent = cart.total_items;
      } catch (_e) {
        cartBadge.textContent = "0";
      }
    }
    return user;
  },
};

EasyEyes.ready = EasyEyes.initNavbar();
