// static/js/catalog.js — Catalog Filtering, Search, Wishlist & Quick Add
let wishlistedIds = new Set();

async function loadWishlistSet() {
  try {
    const items = await EasyEyes.request("/api/wishlist");
    wishlistedIds = new Set(items.map((p) => p.id));
  } catch (_e) {
    wishlistedIds = new Set();
  }
}

function buildFilterQuery() {
  const params = new URLSearchParams();
  const search = document.getElementById("search-input")?.value.trim();
  const category = document.getElementById("filter-category")?.value;
  const shape = document.getElementById("filter-shape")?.value;
  const material = document.getElementById("filter-material")?.value;
  const sort = document.getElementById("sort-select")?.value;

  if (search) params.set("search", search);
  if (category) params.set("category", category);
  if (shape) params.set("frame_shape", shape);
  if (material) params.set("frame_material", material);
  if (sort) params.set("sort", sort);
  return params.toString();
}

async function fetchAndRenderCatalog() {
  const grid = document.getElementById("product-grid");
  const countEl = document.getElementById("results-count");
  if (!grid) return;

  try {
    const query = buildFilterQuery();
    const products = await EasyEyes.request(`/api/products${query ? "?" + query : ""}`);

    if (countEl) {
      countEl.textContent = `${products.length} ${products.length === 1 ? "Frame" : "Frames"} Curated`;
    }

    if (products.length === 0) {
      grid.innerHTML = `
        <div style="grid-column: 1 / -1; text-align: center; padding: 3.5rem; background: #fff; border: 1px solid #E5E2DC;">
          <p class="font-serif" style="font-size: 1.5rem; margin-bottom: 0.5rem;">No frames match your current selection.</p>
          <p style="color: #57534E; font-size: 0.9rem; margin-bottom: 1.25rem;">Try clearing one or more filters to view the full collection.</p>
          <button type="button" id="empty-reset-btn" class="btn-outline btn-sm">Reset All Filters</button>
        </div>`;
      document.getElementById("empty-reset-btn")?.addEventListener("click", resetFilters);
      return;
    }

    grid.innerHTML = products
      .map((p) => {
        const isWished = wishlistedIds.has(p.id);
        return `
        <article class="product-card">
          <div class="card-img-box">
            <button type="button"
                    class="wishlist-icon-btn ${isWished ? "active" : ""}"
                    aria-label="Toggle Wishlist for ${EasyEyes.esc(p.name)}"
                    onclick="handleWishlistToggle(${p.id}, this)">
              ${isWished ? "♥" : "♡"}
            </button>
            <a href="/product.html?id=${p.id}" aria-label="View details for ${EasyEyes.esc(p.name)}">
              <img src="${EasyEyes.esc(p.image_url)}"
                   alt="${EasyEyes.esc(p.name)} — ${EasyEyes.esc(p.frame_material)} ${EasyEyes.label(p.frame_shape)} eyewear"
                   width="400"
                   height="400"
                   loading="lazy"
                   decoding="async" />
            </a>
          </div>
          <div class="card-body">
            <div class="card-meta">
              <span>${EasyEyes.esc(p.category)} · ${EasyEyes.esc(p.frame_material)}</span>
              <span>★ ${p.rating_avg.toFixed(1)} (${p.review_count})</span>
            </div>
            <a href="/product.html?id=${p.id}" class="card-title">${EasyEyes.esc(p.name)}</a>
            <p style="font-size: 0.8rem; color: #57534E;">${EasyEyes.label(p.frame_shape)} · ${EasyEyes.label(p.lens_type)} Lens</p>
            <div class="card-price-row">
              <span class="font-mono" style="font-size: 1rem; font-weight: 600;">${EasyEyes.formatINR(p.price)}</span>
              <button type="button"
                      class="btn-primary btn-sm"
                      onclick="quickAddToCart(${p.id})"
                      ${p.stock < 1 ? "disabled" : ""}>
                ${p.stock < 1 ? "Sold Out" : "Add to Bag"}
              </button>
            </div>
          </div>
        </article>`;
      })
      .join("");
  } catch (err) {
    grid.innerHTML = `<p style="grid-column: 1 / -1; padding: 2rem; color: #991B1B;">We could not load the collection. ${EasyEyes.esc(err.message)}</p>`;
  }
}

async function quickAddToCart(productId) {
  try {
    const cart = await EasyEyes.request("/api/cart", {
      method: "POST",
      body: JSON.stringify({ product_id: productId, quantity: 1 }),
    });
    const badge = document.getElementById("nav-cart-count");
    if (badge) badge.textContent = cart.total_items;
    EasyEyes.toast("Frame added to your bag.");
  } catch (err) {
    if (err.status === 401) {
      EasyEyes.toast("Please sign in to add frames to your bag.", true);
      setTimeout(() => (window.location.href = "/login.html"), 900);
    } else {
      EasyEyes.toast(err.message, true);
    }
  }
}

async function handleWishlistToggle(productId, btnEl) {
  try {
    const res = await EasyEyes.request(`/api/wishlist/${productId}`, { method: "POST" });
    if (res.wishlisted) {
      wishlistedIds.add(productId);
      btnEl.classList.add("active");
      btnEl.textContent = "♥";
      EasyEyes.toast("Saved to your wishlist.");
    } else {
      wishlistedIds.delete(productId);
      btnEl.classList.remove("active");
      btnEl.textContent = "♡";
      EasyEyes.toast("Removed from wishlist.");
    }
  } catch (err) {
    if (err.status === 401) {
      EasyEyes.toast("Sign in to save frames to your wishlist.", true);
      setTimeout(() => (window.location.href = "/login.html"), 900);
    } else {
      EasyEyes.toast(err.message, true);
    }
  }
}

function resetFilters() {
  ["search-input", "filter-category", "filter-shape", "filter-material"].forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.value = "";
  });
  const sortEl = document.getElementById("sort-select");
  if (sortEl) sortEl.value = "featured";
  fetchAndRenderCatalog();
}

document.addEventListener("DOMContentLoaded", async () => {
  const user = await EasyEyes.ready;
  if (user) await loadWishlistSet();
  await fetchAndRenderCatalog();

  let debounceTimer;
  document.getElementById("search-input")?.addEventListener("input", () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(fetchAndRenderCatalog, 220);
  });

  ["filter-category", "filter-shape", "filter-material", "sort-select"].forEach((id) => {
    document.getElementById(id)?.addEventListener("change", fetchAndRenderCatalog);
  });

  document.getElementById("reset-filters-btn")?.addEventListener("click", resetFilters);
});
