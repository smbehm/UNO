(function () {
  const overlay = document.getElementById("nav");
  const openBtn = document.querySelector(".menu-dots");
  const closeBtn = document.querySelector(".close-grid");
  if (openBtn && overlay) {
    openBtn.addEventListener("click", () => overlay.classList.add("open"));
  }
  if (closeBtn && overlay) {
    closeBtn.addEventListener("click", () => overlay.classList.remove("open"));
  }
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") overlay && overlay.classList.remove("open");
  });

  document.querySelectorAll("[data-acc]").forEach((root) => {
    root.querySelectorAll(".acc-item").forEach((item) => {
      const btn = item.querySelector(".acc-btn");
      if (!btn) return;
      btn.addEventListener("click", () => {
        const open = item.classList.contains("open");
        root.querySelectorAll(".acc-item").forEach((i) => {
          i.classList.remove("open");
          const ico = i.querySelector(".acc-ico");
          if (ico) ico.textContent = "+";
        });
        if (!open) {
          item.classList.add("open");
          const ico = item.querySelector(".acc-ico");
          if (ico) ico.textContent = "−";
        }
      });
    });
  });

  const chips = document.querySelectorAll(".chip[data-filter]");
  const cards = document.querySelectorAll("[data-tags]");
  chips.forEach((chip) => {
    chip.addEventListener("click", () => {
      chips.forEach((c) => c.classList.remove("is-on"));
      chip.classList.add("is-on");
      const f = chip.dataset.filter;
      cards.forEach((card) => {
        const show = f === "all" || (card.dataset.tags || "").includes(f);
        card.style.display = show ? "" : "none";
      });
    });
  });
})();
