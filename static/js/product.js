// static/js/product.js — Product Detail Page, Specs & Customer Reviews
const urlParams = new URLSearchParams(window.location.search);
const currentProductId = Number(urlParams.get("id"));

async function loadProductDetail() {
  const container = document.getElementById("product-detail-container");
  const reviewsList = document.getElementById("reviews-list");
  if (!container) return;

  if (!currentProductId) {
    container.innerHTML = `<p style="color: #991B1B;">Eyewear frame not found.</p>`;
    return;
  }

  try {
    const p = await EasyEyes.request(`/api/products/${currentProductId}`);
    document.title = `${p.name} — Easy Eyes Luxury Eyewear`;

    container.innerHTML = `
      <div class="card-img-box" style="border: 1px solid #E5E2DC;">
        <img src="${EasyEyes.esc(p.image_url)}"
             alt="${EasyEyes.esc(p.name)}"
             width="600"
             height="600"
             fetchpriority="high" />
      </div>
      <div>
        <span class="hero-eyebrow">${EasyEyes.esc(p.category)} · SKU: <span class="font-mono">${EasyEyes.esc(p.sku)}</span></span>
        <h1 class="font-serif" style="font-size: 2.5rem; font-weight: 600; line-height: 1.15; margin-bottom: 0.75rem;">
          ${EasyEyes.esc(p.name)}
        </h1>
        <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1.25rem;">
          <span class="font-mono" style="font-size: 1.5rem; font-weight: 600;">${EasyEyes.formatINR(p.price)}</span>
          <span style="font-size: 0.85rem; color: #57534E;">★ ${p.rating_avg.toFixed(1)} (${p.review_count} reviews)</span>
        </div>
        <p style="color: #57534E; line-height: 1.75; margin-bottom: 1.5rem;">${EasyEyes.esc(p.description)}</p>

        <div class="spec-grid">
          <div class="spec-item"><span>Frame Architecture</span><strong>${EasyEyes.label(p.frame_shape)}</strong></div>
          <div class="spec-item"><span>Material Composition</span><strong>${EasyEyes.esc(p.frame_material)}</strong></div>
          <div class="spec-item"><span>Optical Lens Profile</span><strong>${EasyEyes.label(p.lens_type)}</strong></div>
          <div class="spec-item"><span>Atelier Availability</span><strong>${p.stock > 0 ? p.stock + " Units In Stock" : "Out of Stock"}</strong></div>
        </div>

        <div style="display: flex; gap: 1rem; flex-wrap: wrap; margin-top: 1.75rem;">
          <button type="button" id="pdp-add-btn" class="btn-primary" style="flex: 1;" ${p.stock < 1 ? "disabled" : ""}>
            ${p.stock < 1 ? "Currently Sold Out" : "Add Frame to Bag"}
          </button>
          <button type="button" id="pdp-wish-btn" class="btn-outline" aria-label="Save to Wishlist">
            ♥ Save to Wishlist
          </button>
        </div>
      </div>
    `;

    document.getElementById("pdp-add-btn")?.addEventListener("click", async () => {
      try {
        const cart = await EasyEyes.request("/api/cart", {
          method: "POST",
          body: JSON.stringify({ product_id: p.id, quantity: 1 }),
        });
        const badge = document.getElementById("nav-cart-count");
        if (badge) badge.textContent = cart.total_items;
        EasyEyes.toast("Added to your bag.");
      } catch (err) {
        if (err.status === 401) {
          EasyEyes.toast("Please sign in to add items to your bag.", true);
          setTimeout(() => (window.location.href = "/login.html"), 900);
        } else {
          EasyEyes.toast(err.message, true);
        }
      }
    });

    document.getElementById("pdp-wish-btn")?.addEventListener("click", async () => {
      try {
        const res = await EasyEyes.request(`/api/wishlist/${p.id}`, { method: "POST" });
        EasyEyes.toast(res.wishlisted ? "Saved to your wishlist." : "Removed from wishlist.");
      } catch (err) {
        if (err.status === 401) {
          EasyEyes.toast("Please sign in to use Wishlist.", true);
          setTimeout(() => (window.location.href = "/login.html"), 900);
        } else {
          EasyEyes.toast(err.message, true);
        }
      }
    });

    if (reviewsList) {
      if (!p.reviews || p.reviews.length === 0) {
        reviewsList.innerHTML = `<p style="color: #57534E;">No client reviews yet. Be the first to review this frame.</p>`;
      } else {
        reviewsList.innerHTML = p.reviews
          .map(
            (r) => `
          <div style="background: #fff; border: 1px solid #E5E2DC; padding: 1.25rem; margin-bottom: 1rem;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.4rem;">
              <strong>${EasyEyes.esc(r.user_name)}</strong>
              <span style="color: #8A6A2F;">${"★".repeat(r.rating)}${"☆".repeat(5 - r.rating)}</span>
            </div>
            <p style="color: #57534E; font-size: 0.9rem;">${EasyEyes.esc(r.comment)}</p>
          </div>`
          )
          .join("");
      }
    }
  } catch (err) {
    container.innerHTML = `<p style="color: #991B1B;">${EasyEyes.esc(err.message)}</p>`;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  loadProductDetail();

  const reviewForm = document.getElementById("review-form");
  reviewForm?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const rating = Number(document.getElementById("review-rating").value);
    const comment = document.getElementById("review-comment").value.trim();

    try {
      await EasyEyes.request(`/api/products/${currentProductId}/reviews`, {
        method: "POST",
        body: JSON.stringify({ rating, comment }),
      });
      document.getElementById("review-comment").value = "";
      EasyEyes.toast("Review published. Thank you!");
      await loadProductDetail();
    } catch (err) {
      if (err.status === 401) {
        EasyEyes.toast("Please sign in to post a review.", true);
        setTimeout(() => (window.location.href = "/login.html"), 900);
      } else {
        EasyEyes.toast(err.message, true);
      }
    }
  });
});
