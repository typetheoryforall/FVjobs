"""The analytics page: how the board, and the market it samples, have grown.

scripts/site.py calls render(). The graphs are inline SVG built here, so the
page works without JavaScript; site/analytics.js only adds hover tooltips.

Two sources feed it:

- data/history.csv (written by scripts/stats.py): the board as it stood on
  each day the data changed;
- the `posted` dates in data/jobs.yml and data/archive.yml: how many of the
  roles the board has tracked were posted by their employer in each week.
"""
import csv
import datetime as dt
import html
import math
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
HISTORY = ROOT / "data" / "history.csv"

# Bottom to top in the stacked bars. The order keeps hues that are hard to tell
# apart with colour-vision deficiency out of adjacent segments (checked with the
# dataviz palette validator in both colour schemes).
STACK = ("hardware", "ai-for-proof", "academic", "software", "cryptocurrency")
WEEKS = 26

W, H = 720, 300
PAD = {"l": 44, "r": 92, "t": 16, "b": 34}


def esc(text):
    return html.escape(str(text), quote=True)


def monday(day):
    return day - dt.timedelta(days=day.weekday())


def short(day):
    return f"{day:%b} {day.day}"


def nice_max(value):
    """A round axis maximum at or above value, with a tick step to match."""
    if value <= 0:
        return 10, 2
    exp = 10 ** max(math.floor(math.log10(value)) - 1, 0)
    for m in (1, 2, 5, 10, 20, 25, 50, 100):
        step = m * exp
        if math.ceil(value / step) <= 6:
            return math.ceil(value / step) * step, step
    return value, value


def read_history():
    if not HISTORY.exists():
        return []
    with HISTORY.open(encoding="utf-8") as f:
        return [{k: (v if k == "date" else int(v)) for k, v in row.items()} for row in csv.DictReader(f)]


def y_axis(top, step, plot_h, x0, x1, y0):
    out = []
    for v in range(0, top + 1, step):
        y = y0 - v / top * plot_h
        out.append(f'<line class="grid" x1="{x0}" x2="{x1}" y1="{y:.1f}" y2="{y:.1f}"/>')
        out.append(f'<text class="tick" x="{x0 - 8}" y="{y + 4:.1f}" text-anchor="end">{v}</text>')
    return "".join(out)


def growth_chart(history):
    """Open roles on each recorded day, on a true time axis."""
    if not history:
        return "<p>No history recorded yet.</p>"
    days = [dt.date.fromisoformat(r["date"]) for r in history]
    first, last = days[0], days[-1]
    span = max((last - first).days, 1)
    x0, x1 = PAD["l"], W - PAD["r"]
    y0, plot_h = H - PAD["b"], H - PAD["t"] - PAD["b"]
    top, step = nice_max(max(r["open"] for r in history))
    X = lambda d: x0 + (d - first).days / span * (x1 - x0)
    Y = lambda v: y0 - v / top * plot_h

    parts = [y_axis(top, step, plot_h, x0, x1, y0),
             f'<line class="axis" x1="{x0}" x2="{x1}" y1="{y0}" y2="{y0}"/>']
    tick = monday(first) + dt.timedelta(days=7) if first.weekday() else first
    while tick <= last:
        x = X(tick)
        parts.append(f'<line class="axis" x1="{x:.1f}" x2="{x:.1f}" y1="{y0}" y2="{y0 + 5}"/>'
                     f'<text class="tick" x="{x:.1f}" y="{y0 + 20}" text-anchor="middle">{short(tick)}</text>')
        tick += dt.timedelta(days=7)

    pts = [(X(d), Y(r["open"])) for d, r in zip(days, history)]
    path = " ".join(f"{'M' if i == 0 else 'L'}{x:.1f},{y:.1f}" for i, (x, y) in enumerate(pts))
    parts.append(f'<path class="trend s-open" d="{path}"/>')
    for x, y in pts:
        parts.append(f'<circle class="dot s-open" cx="{x:.1f}" cy="{y:.1f}" r="4"/>')
    lx, ly = pts[-1]
    parts.append(f'<text class="direct" x="{lx + 10:.1f}" y="{ly + 4:.1f}">{history[-1]["open"]} open</text>')
    # One hover target per recorded day, wider than the marks.
    for i, (d, r) in enumerate(zip(days, history)):
        x = X(d)
        tip = f"{short(d)}, {d.year}|Open: {r['open']}|Added: {r['added']}|Closed: {r['closed']}"
        parts.append(f'<rect class="hit" x="{x - 9:.1f}" y="{PAD["t"]}" width="18" height="{plot_h}"'
                     f' tabindex="0" data-tip="{esc(tip)}" aria-label="{esc(tip.replace("|", ", "))}"/>')
    return (f'<svg class="chart" viewBox="0 0 {W} {H}" role="img" aria-labelledby="growth-title">'
            f'{"".join(parts)}</svg>')


def weekly_counts(entries, until):
    """Tracked roles per employer posting week, for the WEEKS weeks ending with until's week."""
    end = monday(until)
    start = end - dt.timedelta(weeks=WEEKS - 1)
    weeks = [start + dt.timedelta(weeks=i) for i in range(WEEKS)]
    counts = {w: {c: 0 for c in STACK} for w in weeks}
    earlier = undated = 0
    for e in entries:
        if not e.get("posted"):
            undated += 1
            continue
        w = monday(dt.date.fromisoformat(e["posted"]))
        if w < start:
            earlier += 1
        elif w in counts and e.get("category") in counts[w]:
            counts[w][e["category"]] += 1
    return weeks, counts, earlier, undated


def weekly_chart(weeks, counts, labels, until):
    x0, x1 = PAD["l"], W - PAD["r"]
    y0, plot_h = H - PAD["b"], H - PAD["t"] - PAD["b"]
    totals = [sum(counts[w].values()) for w in weeks]
    top, step = nice_max(max(totals, default=0))
    slot = (x1 - x0) / len(weeks)
    bar = slot * 0.72
    Y = lambda v: v / top * plot_h
    parts = [y_axis(top, step, plot_h, x0, x1, y0)]
    for i, w in enumerate(weeks):
        x = x0 + i * slot + (slot - bar) / 2
        base = y0
        stacked = [(c, counts[w][c]) for c in STACK if counts[w][c]]
        for j, (c, n) in enumerate(stacked):
            h = Y(n)
            y = base - h
            if j == len(stacked) - 1:
                # Round only the data end at the top of the stack.
                r = min(4, h, bar / 2)
                d = (f"M{x:.1f},{base:.1f}V{y + r:.1f}Q{x:.1f},{y:.1f} {x + r:.1f},{y:.1f}"
                     f"H{x + bar - r:.1f}Q{x + bar:.1f},{y:.1f} {x + bar:.1f},{y + r:.1f}V{base:.1f}Z")
                parts.append(f'<path class="seg c-{c}" d="{d}"/>')
            else:
                parts.append(f'<rect class="seg c-{c}" x="{x:.1f}" y="{y:.1f}" width="{bar:.1f}" height="{h:.1f}"/>')
            base = y
        partial = w == monday(until)
        rows = "|".join(f"{labels[c]}: {counts[w][c]}" for c in STACK if counts[w][c])
        tip = f"Week of {short(w)}, {w.year}{' (so far)' if partial else ''}|Total: {totals[i]}" + (f"|{rows}" if rows else "")
        parts.append(f'<rect class="hit" x="{x0 + i * slot:.1f}" y="{PAD["t"]}" width="{slot:.1f}" height="{plot_h}"'
                     f' tabindex="0" data-tip="{esc(tip)}" aria-label="{esc(tip.replace("|", ", "))}"/>')
        if (len(weeks) - 1 - i) % 4 == 0:
            cx = x0 + i * slot + slot / 2
            parts.append(f'<text class="tick" x="{cx:.1f}" y="{y0 + 20}" text-anchor="middle">{short(w)}</text>')
    parts.append(f'<line class="axis" x1="{x0}" x2="{x1}" y1="{y0}" y2="{y0}"/>')
    last = totals[-1]
    lx = x0 + (len(weeks) - 1) * slot + slot / 2 + bar / 2 + 6
    parts.append(f'<text class="direct" x="{lx:.1f}" y="{y0 - Y(last) + 4:.1f}">{last} so far</text>')
    return (f'<svg class="chart" viewBox="0 0 {W} {H}" role="img" aria-labelledby="weekly-title">'
            f'{"".join(parts)}</svg>')


def legend(labels):
    return "".join(f'<li><span class="swatch c-{c}"></span>{esc(labels[c])}</li>' for c in STACK)


def tiles(history, jobs, archive):
    if not history:
        return ""
    now, first = history[-1], history[0]
    week_ago = dt.date.fromisoformat(now["date"]) - dt.timedelta(days=7)
    past = [r for r in history if dt.date.fromisoformat(r["date"]) <= week_ago]
    gained = now["open"] - past[-1]["open"] if past else now["open"]
    items = [
        (now["open"], "open roles", f"{gained:+d} in the last 7 days"),
        (now["tracked"], "roles tracked", f"since {short(dt.date.fromisoformat(first['date']))}, {first['date'][:4]}"),
        (now["companies"], "employers hiring", "with at least one open role"),
        (now["archived"], "roles closed", "kept in the archive"),
    ]
    return "".join(f'<div class="tile"><p class="num">{n}</p><p class="what">{esc(w)}</p>'
                   f'<p class="sub">{esc(s)}</p></div>' for n, w, s in items)



def render(template, jobs, archive, labels, site, repo):
    history = read_history()
    entries = [*jobs, *archive]
    until = dt.date.fromisoformat(history[-1]["date"]) if history else dt.date.today()
    weeks, counts, earlier, undated = weekly_counts(entries, until)
    in_window = sum(sum(c.values()) for c in counts.values())
    return (
        template.replace("{{site}}", site)
        .replace("{{repo}}", repo)
        .replace("{{updated}}", history[-1]["date"] if history else "")
        .replace("{{tiles}}", tiles(history, jobs, archive))
        .replace("{{growth}}", growth_chart(history))
        .replace("{{weekly}}", weekly_chart(weeks, counts, labels, until))
        .replace("{{legend}}", legend(labels))
        .replace("{{weeks}}", str(WEEKS))
        .replace("{{in_window}}", str(in_window))
        .replace("{{earlier}}", str(earlier))
        .replace("{{undated}}", str(undated))
    )
