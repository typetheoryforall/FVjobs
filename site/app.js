// Client-side filtering. The page is fully rendered without this script; it
// only adds the proof-stack chips and hides rows that do not match.
(function () {
  const jobs = [...document.querySelectorAll("#jobs .job")];
  const q = document.getElementById("q");
  const shown = document.getElementById("shown");
  const empty = document.getElementById("empty");
  const stackBox = document.getElementById("stacks");

  // Offer every tool that appears in at least two postings, most common first.
  const counts = new Map();
  for (const j of jobs) for (const s of j.dataset.stack.split("|")) counts.set(s, (counts.get(s) || 0) + 1);
  const common = [...counts].filter(([, n]) => n > 1).sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
  for (const [name, n] of common) {
    const label = document.createElement("label");
    label.innerHTML = `<input type="checkbox" value=""><span></span>`;
    label.querySelector("input").value = name;
    label.querySelector("span").textContent = name;
    label.querySelector("span").insertAdjacentHTML("beforeend", `<small>${n}</small>`);
    stackBox.append(label);
  }
  if (common.length) stackBox.parentElement.hidden = false;

  function apply() {
    const text = q.value.trim().toLowerCase();
    const remote = document.querySelector('input[name="remote"]:checked').value;
    const stacks = [...stackBox.querySelectorAll("input:checked")].map((i) => i.value);
    let n = 0;
    for (const j of jobs) {
      const has = j.dataset.stack.split("|");
      const ok =
        (!text || j.dataset.text.includes(text)) &&
        (!remote || j.dataset.remote === remote) &&
        stacks.every((s) => has.includes(s));
      j.hidden = !ok;
      if (ok) n++;
    }
    shown.textContent = n === jobs.length ? `Showing all ${n} roles` : `Showing ${n} of ${jobs.length} roles`;
    empty.hidden = n > 0;
  }

  document.querySelector(".filters").addEventListener("input", apply);
  apply();
})();
