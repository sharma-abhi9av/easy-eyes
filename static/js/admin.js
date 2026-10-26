// static/js/admin.js — Protected Admin Dashboard (Product CRUD & Order Management)
let adminProductsCache = [];

async function initAdminDashboard() {
  const user = await EasyEyes.requireLogin({ admin: true });
  if (!user) return;
  await Promise.all([loadAdminProducts(), loadAdminOrders()]);
}

async function loadAdminProducts() {
  const tbody = document.getElementById("admin-products-tbody");
  if (!tbody) return;

  adminProductsCache = await EasyEyes.request("/api/products");
  document.getElementById("stat-total-products").textContent = adminProductsCache.length;

  tbody.innerHTML = adminProductsCache
    .map(
      (p) => `
    <tr>
      <td><img src="${EasyEyes.esc(p.image_url)}" alt="${EasyEyes.esc(p.name)}" width="48" height="48" style="border: 1px solid #E5E2DC; object-fit: cover;" /></td>
      <td class="font-mono" style="font-size: 0.78rem;">${EasyEyes.esc(p.sku)}</td>
      <td><strong>${EasyEyes.esc(p.name)}</strong><br/><span style="font-size: 0.75rem; color: #57534E;">${EasyEyes.esc(p.category)} · ${EasyEyes.label(p.frame_shape)} · ${EasyEyes.esc(p.frame_material)}</span></td>
      <td class="font-mono">${EasyEyes.formatINR(p.price)}</td>
      <td class="font-mono">${p.stock}</td>
      <td>
        <div style="display: flex; gap: 0.5rem;">
          <button type="button" class="btn-outline btn-sm" onclick="openEditProductModal(${p.id})">Edit</button>
          <button type="button" class="btn-danger" onclick="deleteProduct(${p.id})">Delete</button>
        </div>
      </td>
    </tr>`
    )
    .join("");
}

async function loadAdminOrders() {
  const tbody = document.getElementById("admin-orders-tbody");
  if (!tbody) return;

  const orders = await EasyEyes.request("/api/admin/orders");
  document.getElementById("stat-total-orders").textContent = orders.length;
  const revenue = orders
    .filter((o) => o.payment_status === "PAID")
    .reduce((acc, o) => acc + o.total_amount, 0);
  document.getElementById("stat-total-revenue").textContent = EasyEyes.formatINR(revenue);

  if (orders.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: #57534E;">No customer orders recorded yet.</td></tr>`;
    return;
  }

  tbody.innerHTML = orders
    .map(
      (o) => `
    <tr>
      <td class="font-mono">#${o.id}</td>
      <td><strong>${EasyEyes.esc(o.customer_name || "Customer")}</strong><br/><span style="font-size: 0.75rem; color: #57534E;">${EasyEyes.esc(o.shipping_address)}</span></td>
      <td style="font-size: 0.8rem;">${o.items.map((i) => `${EasyEyes.esc(i.product_name_snapshot)} (×${i.quantity})`).join("<br/>")}</td>
      <td class="font-mono">${EasyEyes.formatINR(o.total_amount)}</td>
      <td><span class="font-mono" style="font-size: 0.75rem;">${EasyEyes.esc(o.payment_status)}</span></td>
      <td>
        <select aria-label="Order Status for Order ${o.id}" class="select-field" style="padding: 0.4rem; font-size: 0.78rem;" onchange="updateOrderStatus(${o.id}, this.value)">
          ${["PROCESSING", "SHIPPED", "DELIVERED", "CANCELLED"]
            .map((st) => `<option value="${st}" ${o.order_status === st ? "selected" : ""}>${st}</option>`)
            .join("")}
        </select>
      </td>
    </tr>`
    )
    .join("");
}

function openCreateProductModal() {
  document.getElementById("modal-title").textContent = "Add New Luxury Frame";
  document.getElementById("prod-id").value = "";
  document.getElementById("product-form").reset();
  document.getElementById("prod-image").value = "/static/images/frames/frame-1.webp";
  document.getElementById("product-modal").classList.add("open");
}

function openEditProductModal(productId) {
  const p = adminProductsCache.find((item) => item.id === productId);
  if (!p) return;
  document.getElementById("modal-title").textContent = `Edit Frame — ${p.sku}`;
  document.getElementById("prod-id").value = p.id;
  document.getElementById("prod-name").value = p.name;
  document.getElementById("prod-sku").value = p.sku;
  document.getElementById("prod-price").value = p.price;
  document.getElementById("prod-stock").value = p.stock;
  document.getElementById("prod-image").value = p.image_url;
  document.getElementById("prod-category").value = p.category;
  document.getElementById("prod-shape").value = p.frame_shape;
  document.getElementById("prod-material").value = p.frame_material;
  document.getElementById("prod-lens").value = p.lens_type;
  document.getElementById("prod-desc").value = p.description;
  document.getElementById("product-modal").classList.add("open");
}

async function deleteProduct(productId) {
  if (!confirm("Remove this frame from the catalogue?")) return;
  try {
    await EasyEyes.request(`/api/admin/products/${productId}`, { method: "DELETE" });
    EasyEyes.toast("Frame removed from catalogue.");
    await loadAdminProducts();
  } catch (err) {
    EasyEyes.toast(err.message, true);
  }
}

async function updateOrderStatus(orderId, newStatus) {
  try {
    await EasyEyes.request(`/api/admin/orders/${orderId}/status`, {
      method: "PATCH",
      body: JSON.stringify({ order_status: newStatus }),
    });
    EasyEyes.toast(`Order #${orderId} marked as ${newStatus}.`);
  } catch (err) {
    EasyEyes.toast(err.message, true);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  initAdminDashboard();

  document.getElementById("open-add-product-btn")?.addEventListener("click", openCreateProductModal);
  document.getElementById("close-product-modal-btn")?.addEventListener("click", () => {
    document.getElementById("product-modal").classList.remove("open");
  });

  document.getElementById("product-form")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const id = document.getElementById("prod-id").value;
    const payload = {
      name: document.getElementById("prod-name").value.trim(),
      sku: document.getElementById("prod-sku").value.trim().toUpperCase(),
      price: Number(document.getElementById("prod-price").value),
      stock: Number(document.getElementById("prod-stock").value),
      image_url: document.getElementById("prod-image").value.trim(),
      category: document.getElementById("prod-category").value,
      frame_shape: document.getElementById("prod-shape").value,
      frame_material: document.getElementById("prod-material").value,
      lens_type: document.getElementById("prod-lens").value,
      description: document.getElementById("prod-desc").value.trim(),
    };

    try {
      if (id) {
        await EasyEyes.request(`/api/admin/products/${id}`, {
          method: "PUT",
          body: JSON.stringify(payload),
        });
        EasyEyes.toast("Frame updated successfully.");
      } else {
        await EasyEyes.request("/api/admin/products", {
          method: "POST",
          body: JSON.stringify(payload),
        });
        EasyEyes.toast("New frame added to catalog.");
      }
      document.getElementById("product-modal").classList.remove("open");
      await loadAdminProducts();
    } catch (err) {
      EasyEyes.toast(err.message, true);
    }
  });
});
