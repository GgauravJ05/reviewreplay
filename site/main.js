// ReviewReplay landing page: copy buttons, mobile menu, scroll reveals, tagline word reveal.
(() => {
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // Copy install command
  document.querySelectorAll(".copy-btn").forEach((btn) => {
    const status = btn.closest(".cta-block").querySelector(".copy-status");
    const label = btn.querySelector("span");
    btn.addEventListener("click", async () => {
      status.classList.remove("error");
      try {
        await navigator.clipboard.writeText(btn.dataset.copy);
        label.textContent = "Copied";
        status.textContent = "Install command copied. Paste it in your terminal.";
      } catch {
        status.classList.add("error");
        status.textContent = "Copy failed. Select the command and copy it manually.";
      }
      setTimeout(() => { label.textContent = "Copy install command"; }, 2000);
    });
  });

  // Mobile menu
  const toggle = document.querySelector(".menu-toggle");
  const menu = document.getElementById("mobile-menu");
  const links = [...menu.querySelectorAll("a")];
  const setOpen = (open) => {
    toggle.setAttribute("aria-expanded", String(open));
    toggle.setAttribute("aria-label", open ? "Close menu" : "Open menu");
    document.body.style.overflow = open ? "hidden" : "";
    if (open) {
      menu.hidden = false;
      const step = Math.min(60, 400 / links.length);
      links.forEach((a, i) => { a.style.transitionDelay = `${i * step}ms`; });
      requestAnimationFrame(() => requestAnimationFrame(() => menu.classList.add("open")));
    } else {
      links.forEach((a) => { a.style.transitionDelay = "0ms"; });
      menu.classList.remove("open");
      setTimeout(() => { if (!menu.classList.contains("open")) menu.hidden = true; }, 300);
    }
  };
  toggle.addEventListener("click", () => setOpen(toggle.getAttribute("aria-expanded") !== "true"));
  links.forEach((a) => a.addEventListener("click", () => setOpen(false)));
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && !menu.hidden) { setOpen(false); toggle.focus(); } });
  window.matchMedia("(min-width: 721px)").addEventListener("change", (e) => { if (e.matches) setOpen(false); });

  // Section reveals, once each
  const reveals = document.querySelectorAll(".reveal");
  if (!("IntersectionObserver" in window)) {
    reveals.forEach((el) => el.classList.add("in"));
  } else {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) { entry.target.classList.add("in"); io.unobserve(entry.target); }
      });
    }, { threshold: 0.12 });
    reveals.forEach((el) => io.observe(el));
  }

  // Tagline: words light up one at a time as they cross a trigger line
  document.querySelectorAll("[data-reveal-words]").forEach((el) => {
    if (reduced || !("IntersectionObserver" in window)) return;
    const words = el.textContent.trim().split(/\s+/);
    el.setAttribute("aria-label", el.textContent.trim());
    el.textContent = "";
    words.forEach((w, i) => {
      const span = document.createElement("span");
      span.className = "w";
      span.setAttribute("aria-hidden", "true");
      span.textContent = w;
      el.appendChild(span);
      if (i < words.length - 1) el.appendChild(document.createTextNode(" "));
    });
    const spans = [...el.querySelectorAll(".w")];
    let ticking = false;
    const update = () => {
      ticking = false;
      const trigger = window.innerHeight * 0.7;
      const rect = el.getBoundingClientRect();
      if (rect.top > window.innerHeight || rect.bottom < 0) return;
      // Progress through the block maps to how many words are lit, in reading order.
      const progress = Math.min(1, Math.max(0, (trigger - rect.top) / Math.max(1, rect.height * 0.9)));
      const lit = Math.round(progress * spans.length);
      spans.forEach((s, i) => s.classList.toggle("on", i < lit));
    };
    const onScroll = () => { if (!ticking) { ticking = true; requestAnimationFrame(update); } };
    const io = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) { window.addEventListener("scroll", onScroll, { passive: true }); update(); }
        else window.removeEventListener("scroll", onScroll);
      });
    });
    io.observe(el);
  });
})();
