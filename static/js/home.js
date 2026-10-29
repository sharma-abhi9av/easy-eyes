// Homepage motion and collection navigation. Product data stays in catalog.js.
document.addEventListener("DOMContentLoaded", () => {
  const grid = document.getElementById("product-grid");
  const reduceMotion = matchMedia("(prefers-reduced-motion: reduce)");

  EasyEyes.ready.then((user) => {
    if (!user) document.getElementById("nav-auth-link").textContent = "Log In";
  });

  for (const [id, direction] of [["products-prev", -1], ["products-next", 1]]) {
    document.getElementById(id)?.addEventListener("click", () => {
      if (!grid) return;
      grid.scrollBy({
        left: direction * Math.min(grid.clientWidth * 0.8, 700),
        behavior: reduceMotion.matches ? "auto" : "smooth",
      });
    });
  }

  if (!document.documentElement.classList.contains("motion-ready")) return;

  const observer = new IntersectionObserver((entries) => {
    for (const entry of entries) {
      if (!entry.isIntersecting) continue;
      entry.target.classList.add("is-visible");
      observer.unobserve(entry.target);
    }
  }, { threshold: 0.16 });

  document.querySelectorAll("[data-reveal]").forEach((element) => observer.observe(element));

  const left = document.querySelector(".hero-photo-left");
  const center = document.querySelector(".hero-photo-center");
  const right = document.querySelector(".hero-photo-right");
  const title = document.querySelector(".hero-stage h1");
  let framePending = false;

  const updateParallax = () => {
    framePending = false;
    const distance = Math.min(window.scrollY, 700);
    if (left) left.style.translate = `0 ${-distance * 0.13}px`;
    if (center) center.style.translate = `0 ${distance * 0.09}px`;
    if (right) right.style.translate = `0 ${-distance * 0.2}px`;
    if (title) title.style.translate = `0 ${distance * 0.07}px`;
  };

  window.addEventListener("scroll", () => {
    if (framePending) return;
    framePending = true;
    requestAnimationFrame(updateParallax);
  }, { passive: true });
  updateParallax();
});
