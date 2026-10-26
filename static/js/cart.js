// static/js/cart.js — Cart Management, On-Demand Razorpay Loader & Order History
let pendingCheckoutData = null;

function loadRazorpay() {
  if (window.Razorpay) return Promise.resolve();
  return new Promise((resolve, reject) => {
    const s = document.createElement("script");
    s.src = "https://checkout.razorpay.com/v1/checkout.js";
    s.onload = resolve;
    s.onerror = () => reject(new Error("Could not reach the payment gateway. Please try again."));
    document.head.appendChild(s);
  });
}

async function loadCartAndOrders() {
  const user = await EasyEyes.requireLogin();
  if (!user) return;

  const itemsBox = document.getElementById("cart-items-container");
  const subtotalEl = document.getElementById("cart-subtotal");
  const totalEl = document.getElementById("cart-total");
  const badge = document.getElementById("nav-cart-count");
  const checkoutBtn = document.getElementById("checkout-submit-btn");

  try {
    const cart = await EasyEyes.request("/api/cart");
    if (badge) badge.textContent = cart.total_items;
    if (subtotalEl) subtotalEl.textContent = EasyEyes.formatINR(cart.subtotal);
    if (totalEl) totalEl.textContent = EasyEyes.formatINR(cart.subtotal);

    if (cart.items.length === 0) {
      if (checkoutBtn) checkoutBtn.disabled = true;
      itemsBox.innerHTML = `
        <div style="background: #fff; border: 1px solid #E5E2DC; padding: 2.5rem; text-align: center;">
          <p class="font-serif" style="font-size: 1.5rem; margin-bottom: 0.75rem;">Your shopping bag is currently empty.</p>
          <a href="/index.html#catalog" class="btn-outline btn-sm">Explore Eyewear Collection</a>
        </div>`;
    } else {
      if (checkoutBtn) checkoutBtn.disabled = false;
      itemsBox.innerHTML = cart.items
        .map(
          (item) => `
        <div style="display: flex; gap: 1.25rem; align-items: center; background: #fff; border: 1px solid #E5E2DC; padding: 1rem; margin-bottom: 1rem;">
          <img src="${EasyEyes.esc(item.product.image_url)}" alt="${EasyEyes.esc(item.product.name)}" width="90" height="90" style="border: 1px solid #E5E2DC; object-fit: cover;" />
          <div style="flex: 1;">
            <a href="/product.html?id=${item.product_id}" class="font-serif" style="font-size: 1.2rem; font-weight: 600; color: #121212; text-decoration: none;">
              ${EasyEyes.esc(item.product.name)}
            </a>
            <p class="font-mono" style="font-size: 0.85rem; color: #57534E; margin-top: 0.2rem;">
              ${EasyEyes.formatINR(item.product.price)} each · Stock: ${item.product.stock}
            </p>
            <div style="display: flex; align-items: center; gap: 0.6rem; margin-top: 0.65rem;">
              <button type="button" class="btn-outline btn-sm" aria-label="Decrease quantity" onclick="changeQty(${item.id}, ${item.quantity - 1})">−</button>
              <span class="font-mono" style="font-size: 0.9rem; min-width: 1.5rem; text-align: center;">${item.quantity}</span>
              <button type="button" class="btn-outline btn-sm" aria-label="Increase quantity" onclick="changeQty(${item.id}, ${item.quantity + 1})">+</button>
              <button type="button" class="nav-link" style="color: #991B1B; margin-left: 0.75rem; font-size: 0.72rem;" onclick="removeItem(${item.id})">Remove</button>
            </div>
          </div>
          <div class="font-mono" style="font-weight: 600; font-size: 1rem;">
            ${EasyEyes.formatINR(item.line_total)}
          </div>
        </div>`
        )
        .join("");
    }

    await loadMyOrders();
  } catch (err) {
    EasyEyes.toast(err.message, true);
  }
}

async function changeQty(itemId, newQty) {
  if (newQty < 1) {
    return removeItem(itemId);
  }
  try {
    await EasyEyes.request(`/api/cart/${itemId}`, {
      method: "PATCH",
      body: JSON.stringify({ quantity: newQty }),
    });
    await loadCartAndOrders();
  } catch (err) {
    EasyEyes.toast(err.message, true);
  }
}

async function removeItem(itemId) {
  try {
    await EasyEyes.request(`/api/cart/${itemId}`, { method: "DELETE" });
    EasyEyes.toast("Item removed from bag.");
    await loadCartAndOrders();
  } catch (err) {
    EasyEyes.toast(err.message, true);
  }
}

async function loadMyOrders() {
  const box = document.getElementById("orders-history-container");
  if (!box) return;
  try {
    const orders = await EasyEyes.request("/api/orders/my");
    if (orders.length === 0) {
      box.innerHTML = `<p style="color: #57534E; font-size: 0.9rem;">You have not placed any orders yet.</p>`;
      return;
    }
    box.innerHTML = orders
      .map(
        (o) => `
      <div style="background: #fff; border: 1px solid #E5E2DC; padding: 1.25rem; margin-bottom: 1rem;">
        <div style="display: flex; justify-content: space-between; flex-wrap: wrap; gap: 0.5rem; border-bottom: 1px solid #E5E2DC; padding-bottom: 0.6rem; margin-bottom: 0.75rem;">
          <span class="font-mono" style="font-size: 0.82rem;">ORDER #${o.id} · ${EasyEyes.esc(o.razorpay_order_id || "")}</span>
          <span style="font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em;">
            Payment: ${EasyEyes.esc(o.payment_status)} | Fulfillment: ${EasyEyes.esc(o.order_status)}
          </span>
        </div>
        <div style="font-size: 0.85rem; color: #57534E; margin-bottom: 0.5rem;">
          ${o.items.map((i) => `${EasyEyes.esc(i.product_name_snapshot)} × ${i.quantity} (${EasyEyes.formatINR(i.price_snapshot)})`).join(" · ")}
        </div>
        <div style="display: flex; justify-content: space-between; font-size: 0.85rem;">
          <span>Ship to: ${EasyEyes.esc(o.shipping_address)}</span>
          <strong class="font-mono">Total: ${EasyEyes.formatINR(o.total_amount)}</strong>
        </div>
      </div>`
      )
      .join("");
  } catch (_e) {
    box.innerHTML = "";
  }
}

async function finalizePayment(orderId, rzpOrderId, rzpPaymentId, rzpSignature) {
  try {
    await EasyEyes.request("/api/orders/verify", {
      method: "POST",
      body: JSON.stringify({
        order_id: orderId,
        razorpay_order_id: rzpOrderId,
        razorpay_payment_id: rzpPaymentId,
        razorpay_signature: rzpSignature,
      }),
    });
    document.getElementById("test-payment-modal")?.classList.remove("open");
    document.getElementById("shipping-address").value = "";
    EasyEyes.toast("Order confirmed and payment verified!");
    await loadCartAndOrders();
  } catch (err) {
    EasyEyes.toast(err.message, true);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  loadCartAndOrders();

  document.getElementById("checkout-form")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const address = document.getElementById("shipping-address").value.trim();
    try {
      const initData = await EasyEyes.request("/api/orders/checkout", {
        method: "POST",
        body: JSON.stringify({ shipping_address: address }),
      });

      if (!initData.is_simulated) {
        await loadRazorpay();
        const rzp = new window.Razorpay({
          key: initData.razorpay_key_id,
          amount: initData.amount_paise,
          currency: initData.currency,
          name: "Easy Eyes Luxury Eyewear",
          description: `Order #${initData.order_id}`,
          order_id: initData.razorpay_order_id,
          prefill: { name: initData.customer_name, email: initData.customer_email },
          theme: { color: "#121212" },
          handler: async function (response) {
            await finalizePayment(
              initData.order_id,
              response.razorpay_order_id,
              response.razorpay_payment_id,
              response.razorpay_signature
            );
          },
        });
        rzp.open();
      } else {
        pendingCheckoutData = initData;
        document.getElementById("sim-order-ref").textContent = initData.razorpay_order_id;
        document.getElementById("sim-order-amount").textContent = EasyEyes.formatINR(initData.total_amount_inr);
        document.getElementById("test-payment-modal")?.classList.add("open");
      }
    } catch (err) {
      EasyEyes.toast(err.message, true);
    }
  });

  document.getElementById("confirm-sim-payment-btn")?.addEventListener("click", async () => {
    if (!pendingCheckoutData) return;
    await finalizePayment(
      pendingCheckoutData.order_id,
      pendingCheckoutData.razorpay_order_id,
      "pay_test_" + Date.now(),
      "sig_test_verified"
    );
  });

  document.getElementById("close-sim-modal-btn")?.addEventListener("click", () => {
    document.getElementById("test-payment-modal")?.classList.remove("open");
  });
});
