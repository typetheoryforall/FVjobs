// Client-side filtering. The page is fully rendered without this script; it
// only adds the proof-stack chips, reorders rows and hides rows that do not match.
(function () {
  const list = document.getElementById("jobs");
  const jobs = [...list.querySelectorAll(".job")]; // rendered A–Z by company
  const undated = document.getElementById("undated");
  const q = document.getElementById("q");
  const shown = document.getElementById("shown");
  const empty = document.getElementById("empty");
  const stackBox = document.getElementById("stacks");
  const MAX_TOOLS = 16;
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
    let n = 0;
    for (const j of jobs) {
      const has = j.dataset.stack.split("|");
      const ok =
        (!text || j.dataset.text.includes(text)) &&
        (!category || j.dataset.category === category) &&
        (!remote || j.dataset.remote === remote) &&
        (!big || (j.dataset.big === "1") === (big === "yes")) &&
        stacks.every((s) => has.includes(s));
      j.hidden = !ok;
      if (ok) n++;
    }
    shown.textContent = n === jobs.length ? `Showing all ${n} roles` : `Showing ${n} of ${jobs.length} roles`;
    empty.hidden = n > 0;
  }

  document.querySelector(".filters").addEventListener("input", (event) => {
    if (event.target.name === "category") buildStacks();
    if (event.target.name === "order") order();
    apply();
  });
  // A link to a closed role (…/#FV-141) has to open the archive to show it.
  function reveal() {
    const card = location.hash && document.getElementById(decodeURIComponent(location.hash.slice(1)));
    if (!card) return;
    card.closest("details")?.setAttribute("open", "");
    card.scrollIntoView();
  }
  addEventListener("hashchange", reveal);

  buildStacks();
  apply();
  reveal();
})();
