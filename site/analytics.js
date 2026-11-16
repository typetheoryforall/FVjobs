// Hover and focus tooltips for the analytics graphs. Each hit target carries
// its text in data-tip, lines separated by "|"; the page reads fine without it.
(function () {
  const tip = document.getElementById("tip");
  if (!tip) return;

  function show(target, x, y) {
    const [head, ...rows] = target.dataset.tip.split("|");
    tip.replaceChildren();
    const b = document.createElement("b");
    b.textContent = head;
    tip.append(b);
    for (const row of rows) {
      const line = document.createElement("div");
      line.textContent = row;
      tip.append(line);
    }
    tip.hidden = false;
    const pad = 14, w = tip.offsetWidth, h = tip.offsetHeight;
    let left = x + pad, top = y - h - pad;
    if (left + w > window.innerWidth - 8) left = x - w - pad;
    if (top < 8) top = y + pad;
    tip.style.left = `${Math.max(8, left)}px`;
    tip.style.top = `${top}px`;
    document.querySelectorAll(".hit.on").forEach((el) => el.classList.remove("on"));
    target.classList.add("on");
  }

  function hide() {
    tip.hidden = true;
    document.querySelectorAll(".hit.on").forEach((el) => el.classList.remove("on"));
  }

  document.querySelectorAll(".chart .hit").forEach((el) => {
    el.addEventListener("pointermove", (e) => show(el, e.clientX, e.clientY));
    el.addEventListener("pointerleave", hide);
    el.addEventListener("focus", () => {
      const r = el.getBoundingClientRect();
      show(el, r.left + r.width / 2, r.top + 24);
    });
    el.addEventListener("blur", hide);
  });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") hide(); });
})();
