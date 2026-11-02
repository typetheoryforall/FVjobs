// Client-side filtering. The page is fully rendered without this script; it
// only adds the proof-stack chips, reorders rows and hides rows that do not
// match or are not on the current page.
(function () {
  const list = document.getElementById("jobs");
  const jobs = [...list.querySelectorAll(".job")]; // rendered A–Z by company
  const undated = document.getElementById("undated");
  const q = document.getElementById("q");
  const shown = document.getElementById("shown");
  const empty = document.getElementById("empty");
  const pager = document.getElementById("pager");
  const per = document.getElementById("per");
  const stackBox = document.getElementById("stacks");
  const MAX_TOOLS = 16;
  const PER_KEY = "fvjobs-per-page";
  let matching = []; // rows that pass the filters, in the order shown
  let page = 1;
  const picked = (name) => document.querySelector(`input[name="${name}"]:checked`).value;

  // Offer the tools most common among roles of the chosen kind, most common
  // first, keeping any already ticked. The search box finds the rest.
  function buildStacks() {
    const category = picked("category");
    const ticked = new Set([...stackBox.querySelectorAll("input:checked")].map((i) => i.value));
    const counts = new Map();
    for (const j of jobs) {
      if (category && j.dataset.category !== category) continue;
      for (const s of j.dataset.stack.split("|")) counts.set(s, (counts.get(s) || 0) + 1);
    }
    const offer = [...counts]
      .filter(([, n]) => n > 1)
      .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
      .slice(0, MAX_TOOLS);
    for (const s of ticked) if (!offer.some(([name]) => name === s)) offer.push([s, counts.get(s) || 0]);

    stackBox.replaceChildren(
      ...offer.map(([name, n]) => {
        const label = document.createElement("label");
        label.innerHTML = `<input type="checkbox" value=""><span></span>`;
        const input = label.querySelector("input");
        input.value = name;
        input.checked = ticked.has(name);
        label.querySelector("span").textContent = name;
        label.querySelector("span").insertAdjacentHTML("beforeend", `<small>${n}</small>`);
        return label;
      })
    );
    stackBox.parentElement.hidden = offer.length === 0;
  }

  // Sort by the employer's posting date. Roles without one go last either way;
  // the sort is stable, so ties stay in company order.
  function order() {
    const how = picked("order");
    const dir = how === "newest" ? -1 : 1;
    const sorted = !how
      ? jobs
      : [...jobs].sort((a, b) => {
          const pa = a.dataset.posted, pb = b.dataset.posted;
          if (!pa || !pb) return !pa - !pb;
          return pa < pb ? -dir : pa > pb ? dir : 0;
        });
    list.append(...sorted);
    undated.hidden = !how;
  }

  function apply() {
    const text = q.value.trim().toLowerCase();
    const category = picked("category");
    const remote = picked("remote");
    const big = picked("big");
    const stacks = [...stackBox.querySelectorAll("input:checked")].map((i) => i.value);
    matching = [...list.children].filter((j) => {
      const has = j.dataset.stack.split("|");
      return (
        (!text || j.dataset.text.includes(text)) &&
        (!category || j.dataset.category === category) &&
        (!remote || j.dataset.remote === remote) &&
        (!big || (j.dataset.big === "1") === (big === "yes")) &&
        stacks.every((s) => has.includes(s))
      );
    });
    page = 1;
    paginate();
  }

  // Show one page of the matching rows, and the pager to reach the others.
  function paginate() {
    const size = Number(per.value);
    const n = matching.length;
    const pages = Math.max(1, Math.ceil(n / size));
    page = Math.min(page, pages);
    const first = (page - 1) * size;
    const onPage = new Set(matching.slice(first, first + size));
    for (const j of jobs) j.hidden = !onPage.has(j);

    const of = n === jobs.length ? `${n} roles` : `${n} matching roles (${jobs.length} in all)`;
    shown.textContent =
      pages === 1
        ? n === jobs.length ? `Showing all ${n} roles` : `Showing ${n} of ${jobs.length} roles`
        : `Showing ${first + 1}–${first + onPage.size} of ${of}`;
    empty.hidden = n > 0;

    pager.hidden = pages === 1;
    // Nothing to choose when every size fits the list on one page.
    per.parentElement.hidden = n <= Number(per.options[0].value);
    const button = (label, to, attrs = {}) => {
      const b = document.createElement("button");
      b.type = "button";
      b.innerHTML = label;
      b.dataset.page = to;
      for (const [k, v] of Object.entries(attrs)) b.setAttribute(k, v);
      return b;
    };
    const ends = (on) => (on ? {} : { disabled: "" });
    const number = (p) => button(String(p), p, { "aria-label": `Page ${p}`, ...(p === page ? { "aria-current": "page" } : {}) });
    const items = [button(`← <span class="word">Previous</span>`, page - 1, { "aria-label": "Previous page", ...ends(page > 1) })];
    let last = 0;
    for (const p of pageNumbers(pages)) {
      if (p - last === 2) items.push(number(last + 1));
      else if (p - last > 2) items.push(Object.assign(document.createElement("span"), { className: "gap", textContent: "…" }));
      items.push(number(p));
      last = p;
    }
    items.push(button(`<span class="word">Next</span> →`, page + 1, { "aria-label": "Next page", ...ends(page < pages) }));
    pager.replaceChildren(...items);
  }

  // The first and last pages and the ones next to the current page; the
  // caller fills a one-page gap and marks longer ones with an ellipsis.
  function pageNumbers(pages) {
    if (pages <= 7) return Array.from({ length: pages }, (_, i) => i + 1);
    const near = page <= 3 ? [2, 3, 4] : page >= pages - 2 ? [pages - 3, pages - 2, pages - 1] : [page - 1, page, page + 1];
    return [1, ...near, pages];
  }

  pager.addEventListener("click", (event) => {
    const b = event.target.closest("button");
    if (!b || b.disabled) return;
    page = Number(b.dataset.page);
    paginate();
    shown.focus(); // scrolls back to the top of the list and reads out the new range
  });

  // Remember the page size on this browser. Storage can be unavailable, and
  // the default of 20 is fine then.
  try {
    const saved = localStorage.getItem(PER_KEY);
    if ([...per.options].some((o) => o.value === saved)) per.value = saved;
  } catch {}

  per.addEventListener("change", () => {
    try { localStorage.setItem(PER_KEY, per.value); } catch {}
    // Stay on the page that holds the first role shown so far.
    const top = matching.findIndex((j) => !j.hidden);
    page = top < 0 ? 1 : Math.floor(top / Number(per.value)) + 1;
    paginate();
  });

  document.querySelector(".filters").addEventListener("input", (event) => {
    if (event.target.name === "category") buildStacks();
    if (event.target.name === "order") order();
    apply();
  });
  // Back to every open role. The order stays, as it hides nothing.
  function clearFilters() {
    q.value = "";
    for (const name of ["category", "remote", "big"]) {
      document.querySelector(`input[name="${name}"][value=""]`).checked = true;
    }
    for (const i of stackBox.querySelectorAll("input:checked")) i.checked = false;
    buildStacks();
    apply();
  }

  // A link to a role (…/#FV-042) has to turn to the page that holds it,
  // clearing any filter that hides it, and a link to a closed one (…/#FV-141)
  // has to open the archive.
  function reveal() {
    const card = location.hash && document.getElementById(decodeURIComponent(location.hash.slice(1)));
    if (!card) return;
    if (card.parentElement === list && !matching.includes(card)) clearFilters();
    const at = matching.indexOf(card);
    if (at >= 0) {
      page = Math.floor(at / Number(per.value)) + 1;
      paginate();
    }
    card.closest("details")?.setAttribute("open", "");
    // On a reload the browser would put back the old scroll position, which
    // pointed into whatever page was showing before.
    history.scrollRestoration = "manual";
    card.scrollIntoView();
  }
  // Pasting the link that is already in the address bar fires only popstate,
  // since the hash does not change.
  addEventListener("hashchange", reveal);
  addEventListener("popstate", reveal);

  buildStacks();
  apply();
  reveal();
})();
