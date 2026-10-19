"use strict";
const COLOURS = { murray: "var(--murray)", rich: "var(--rich)" };
const NS = "http://www.w3.org/2000/svg";
const D = { adj: null, plan: null, commentary: {}, meta: {}, acts: {} };
let tab = "overview";

const $ = (s, r = document) => r.querySelector(s);
function h(tag, attrs = {}, ...kids) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") e.className = v; else if (k === "html") e.innerHTML = v; else e.setAttribute(k, v);
  }
  for (const k of kids.flat()) if (k != null) e.append(k.nodeType ? k : document.createTextNode(k));
  return e;
}
function s(tag, attrs = {}, ...kids) {
  const e = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
  for (const k of kids.flat()) if (k != null) e.append(k.nodeType ? k : document.createTextNode(k));
  return e;
}
const km = n => (n == null ? "–" : (Math.round(n * 10) / 10) + " km");
const fmtDate = iso => iso ? new Date(iso + "T12:00:00").toLocaleDateString("en-GB", { weekday: "short", day: "numeric", month: "short" }) : "–";
const paceStr = p => { const m = Math.floor(p), sec = Math.round((p - m) * 60); return `${m}:${String(sec).padStart(2, "0")}`; };
const keys = () => (tab === "overview" ? Object.keys(D.adj.athletes) : [tab]);

async function load() {
  const get = async u => { try { const r = await fetch(u, { cache: "no-store" }); return r.ok ? r.json() : null; } catch { return null; } };
  const [adj, plan, com, meta, m, r] = await Promise.all(["data/adjusted.json", "data/plan.json", "data/commentary.json",
    "data/meta.json", "data/activities_murray.json", "data/activities_rich.json"].map(get));
  D.adj = adj; D.plan = plan; D.commentary = (com && com.notes) || {}; D.meta = meta || {};
  D.acts = { murray: m || [], rich: r || [] };
  await loadLog(get);
}

/* ---------- charts ---------- */
function frame(W, H, m) {
  const svg = s("svg", { viewBox: `0 0 ${W} ${H}`, class: "chart", role: "img" });
  return { svg, iw: W - m.l - m.r, ih: H - m.t - m.b, m };
}
function niceMax(v) { const p = Math.pow(10, Math.floor(Math.log10(v || 1))); for (const k of [1, 2, 2.5, 5, 10]) if (v <= k * p) return k * p; return v; }
function axes(f, ymax, ticks, label, fmt = v => v) {
  const { svg, iw, ih, m } = f;
  for (let i = 0; i <= ticks; i++) {
    const v = (ymax / ticks) * i, y = m.t + ih - (v / ymax) * ih;
    svg.append(s("line", { x1: m.l, x2: m.l + iw, y1: y, y2: y, stroke: "var(--grid)" }));
    svg.append(s("text", { x: m.l - 6, y: y + 4, "text-anchor": "end" }, fmt(v)));
  }
  svg.append(s("text", { x: 2, y: 10 }, label));
}
function xLabels(f, n) {
  const { svg, iw, ih, m } = f, band = iw / n;
  for (let i = 0; i < n; i++) if ((i + 1) % 2 === 1 || n < 14) {
    svg.append(s("text", { x: m.l + (i + .5) * band, y: m.t + ih + 16, "text-anchor": "middle" }, String(i + 1)));
  }
  svg.append(s("text", { x: m.l + iw, y: m.t + ih + 28, "text-anchor": "end" }, "week"));
}
function nowMarker(f, n) {
  const w = D.adj.athletes[Object.keys(D.adj.athletes)[0]].summary.current_week;
  if (!w) return;
  const x = f.m.l + ((w - .5) / n) * f.iw;
  f.svg.append(s("line", { x1: x, x2: x, y1: f.m.t, y2: f.m.t + f.ih, stroke: "var(--ink-3)", "stroke-dasharray": "2 3" }));
  f.svg.append(s("text", { x, y: f.m.t + 9, "text-anchor": "middle" }, "now"));
}
function hits(f, n, html) {
  const band = f.iw / n;
  for (let i = 0; i < n; i++) {
    const r = s("rect", { x: f.m.l + i * band, y: f.m.t, width: band, height: f.ih, fill: "transparent" });
    r.addEventListener("pointermove", e => tip(e, html(i)));
    r.addEventListener("pointerleave", () => tip(null));
    f.svg.append(r);
  }
}
function tip(e, html) {
  const t = $("#tip");
  if (!e) { t.hidden = true; return; }
  t.innerHTML = html; t.hidden = false;
  const x = Math.min(e.clientX + 12, innerWidth - t.offsetWidth - 8);
  t.style.left = x + "px"; t.style.top = Math.max(8, e.clientY - t.offsetHeight - 10) + "px";
}
function legend(items) {
  return h("div", { class: "legend" }, items.map(([cls, colour, text]) =>
    h("span", {}, h("i", { class: "sw " + cls, style: `background:${colour}` }), text)));
}
function tableView(head, rows) {
  return h("details", { class: "table-view" }, h("summary", {}, "Table view"),
    h("table", {}, h("thead", {}, h("tr", {}, head.map(x => h("th", {}, x)))),
      h("tbody", {}, rows.map(r => h("tr", {}, r.map(c => h("td", {}, String(c))))))));
}

function weeklyChart(key) {
  const a = D.adj.athletes[key], n = a.weeks.length;
  const f = frame(720, 240, { l: 38, r: 8, t: 14, b: 32 });
  const ymax = niceMax(Math.max(...a.weeks.map(w => Math.max(w.planned_km, w.actual_km))));
  axes(f, ymax, 4, "km per week");
  const band = f.iw / n, bw = band * .72, Y = v => f.m.t + f.ih - (v / ymax) * f.ih;
  a.weeks.forEach((w, i) => {
    const x = f.m.l + i * band + (band - bw) / 2;
    f.svg.append(s("rect", { x, y: Y(w.planned_km), width: bw, height: f.m.t + f.ih - Y(w.planned_km), fill: "var(--plan)", opacity: .45, rx: 2 }));
    if (w.actual_km > 0) f.svg.append(s("rect", { x: x + bw * .18, y: Y(w.actual_km), width: bw * .64, height: f.m.t + f.ih - Y(w.actual_km), fill: COLOURS[key], rx: 2 }));
  });
  xLabels(f, n); nowMarker(f, n);
  hits(f, n, i => { const w = a.weeks[i]; return `<b>Week ${w.week}</b><br>Planned ${km(w.planned_km)}<br>Actual ${km(w.actual_km)} (${w.runs} runs)`; });
  return h("div", { class: "card" }, h("h3", {}, h("i", { class: "dot", style: `background:${COLOURS[key]}` }), `${a.name}: weekly distance`), f.svg,
    legend([["", "var(--plan)", "Planned"], ["", COLOURS[key], "Actual"]]),
    tableView(["Week", "Planned km", "Actual km", "Runs"], a.weeks.map(w => [w.week, w.planned_km, w.actual_km, w.runs])));
}

function longChart(list) {
  const n = 26, f = frame(720, 260, { l: 38, r: 8, t: 14, b: 32 });
  const all = list.flatMap(k => D.adj.athletes[k].weeks.filter(w => w.week < 26).flatMap(w => [w.planned_long, w.adjusted_long, w.actual_long]));
  const ymax = niceMax(Math.max(...all, 10));
  axes(f, ymax, 4, "long run, km");
  const band = f.iw / n, X = i => f.m.l + (i + .5) * band, Y = v => f.m.t + f.ih - (v / ymax) * f.ih;
  const base = D.adj.athletes[list[list.length - 1]].weeks;
  f.svg.append(s("polyline", { points: base.map((w, i) => ({ w, i })).filter(o => o.w.week < 26 && o.w.planned_long > 0).map(o => `${X(o.i)},${Y(o.w.planned_long)}`).join(" "), fill: "none", stroke: "var(--plan)", "stroke-width": 2 }));
  f.svg.append(s("text", { x: X(25), y: f.m.t + 9, "text-anchor": "end" }, "Race: 50 km"));
  list.forEach(k => {
    const ws = D.adj.athletes[k].weeks;
    const up = ws.map((w, i) => ({ w, i })).filter(o => (o.w.status === "Upcoming" || o.w.status === "This week") && o.w.week < 26 && o.w.adjusted_long > 0);
    if (up.length) f.svg.append(s("polyline", { points: up.map(o => `${X(o.i)},${Y(o.w.adjusted_long)}`).join(" "), fill: "none", stroke: COLOURS[k], "stroke-width": 2, "stroke-dasharray": "5 4" }));
    ws.forEach((w, i) => { if (w.actual_long > 0) f.svg.append(s("circle", { cx: X(i), cy: Y(w.actual_long), r: 4.5, fill: COLOURS[k], stroke: "var(--surface)", "stroke-width": 2 })); });
  });
  xLabels(f, n); nowMarker(f, n);
  hits(f, n, i => `<b>Week ${i + 1}</b>` + list.map(k => { const w = D.adj.athletes[k].weeks[i];
    return `<br>${D.adj.athletes[k].name}: plan ${km(w.planned_long)}` + (w.adjusted_long !== w.planned_long ? `, adjusted ${km(w.adjusted_long)}` : "") + (w.actual_long ? `, actual ${km(w.actual_long)}` : ""); }).join(""));
  const lg = [["line", "var(--plan)", "Plan"]];
  list.forEach(k => lg.push(["line", COLOURS[k], `${D.adj.athletes[k].name} (dots actual, dashed adjusted)`]));
  const rows = base.map((w, i) => [w.week, w.planned_long, ...list.flatMap(k => { const x = D.adj.athletes[k].weeks[i]; return [x.adjusted_long, x.actual_long]; })]);
  const head = ["Week", "Planned", ...list.flatMap(k => [`${D.adj.athletes[k].name} adjusted`, `${D.adj.athletes[k].name} actual`])];
  return h("div", { class: "card" }, h("h3", {}, "Saturday long run"), f.svg, legend(lg), tableView(head, rows));
}

function trendChart(list) {
  const n = 26, f = frame(720, 220, { l: 38, r: 8, t: 14, b: 32 });
  const pts = list.flatMap(k => D.adj.athletes[k].metrics.map(m => m.easy_pace));
  if (!pts.length) return h("div", { class: "card" }, h("h3", {}, "Easy-run pace"), h("p", { class: "muted" }, "Appears once easy runs with heart-rate data are recorded."));
  const lo = Math.floor(Math.min(...pts) * 2) / 2 - .5, hi = Math.ceil(Math.max(...pts) * 2) / 2 + .5;
  const band = f.iw / n, X = i => f.m.l + (i + .5) * band, Y = v => f.m.t + ((v - lo) / (hi - lo)) * f.ih;
  for (let v = lo; v <= hi + 1e-9; v += .5) {
    f.svg.append(s("line", { x1: f.m.l, x2: f.m.l + f.iw, y1: Y(v), y2: Y(v), stroke: "var(--grid)" }));
    f.svg.append(s("text", { x: f.m.l - 6, y: Y(v) + 4, "text-anchor": "end" }, paceStr(v)));
  }
  f.svg.append(s("text", { x: 2, y: 10 }, "min/km (faster is higher)"));
  list.forEach(k => {
    const m = D.adj.athletes[k].metrics;
    f.svg.append(s("polyline", { points: m.map(o => `${X(o.week - 1)},${Y(o.easy_pace)}`).join(" "), fill: "none", stroke: COLOURS[k], "stroke-width": 2 }));
    m.forEach(o => f.svg.append(s("circle", { cx: X(o.week - 1), cy: Y(o.easy_pace), r: 3.5, fill: COLOURS[k], stroke: "var(--surface)", "stroke-width": 2 })));
  });
  xLabels(f, n); nowMarker(f, n);
  hits(f, n, i => `<b>Week ${i + 1}</b>` + list.map(k => { const o = D.adj.athletes[k].metrics.find(m => m.week === i + 1);
    return o ? `<br>${D.adj.athletes[k].name}: ${paceStr(o.easy_pace)} /km at HR ${o.easy_hr}` : ""; }).join(""));
  const rows = list.flatMap(k => D.adj.athletes[k].metrics.map(o => [D.adj.athletes[k].name, o.week, paceStr(o.easy_pace), o.easy_hr]));
  return h("div", { class: "card" }, h("h3", {}, "Easy-run pace (runs at or below the easy HR ceiling)"), f.svg,
    legend(list.map(k => ["line", COLOURS[k], D.adj.athletes[k].name])), tableView(["Athlete", "Week", "Pace /km", "Avg HR"], rows));
}

/* ---------- cards, table, runs ---------- */
function summaryCard(key) {
  const a = D.adj.athletes[key], sm = a.summary, nl = sm.next_long;
  const cur = a.weeks.find(w => w.week === sm.current_week);
  const plan = D.plan.weeks.find(w => w.week === (nl && nl.week));
  const date = plan && plan.athletes[key].long_date;
  const changed = nl && nl.adjusted_long !== nl.planned_long;
  const card = h("div", { class: "card" },
    h("h3", {}, h("i", { class: "dot", style: `background:${COLOURS[key]}` }), a.name),
    nl ? h("div", {}, h("div", { class: "big" }, km(nl.adjusted_long)),
      h("div", { class: "muted" }, `Next long run, week ${nl.week}, ${fmtDate(date)}`,
        changed ? h("span", { class: "adj" }, ` (plan was ${km(nl.planned_long)})`) : null)) : h("div", { class: "muted" }, "No long run left."),
    h("div", { class: "kv" },
      cur ? h("span", {}, "This week ", h("b", {}, `${km(cur.actual_km)} of ${km(cur.planned_km)}`)) : null,
      h("span", {}, "Total ", h("b", {}, km(sm.total_km_since_start))),
      sm.last_run ? h("span", {}, "Last run ", h("b", {}, `${km(sm.last_run.distance_km)}`), ` on ${fmtDate(sm.last_run.date)}`) : null));
  if (nl && nl.reasons.length) card.append(h("ul", { class: "notes" }, [...new Set(nl.reasons)].map(r => h("li", {}, r))));
  if (sm.notes.length) card.append(h("ul", { class: "notes" }, sm.notes.map(r => h("li", {}, r))));
  if (D.commentary[key]) card.append(h("div", { class: "note-claude" }, h("b", {}, "Weekly note: "), D.commentary[key]));
  return card;
}

function planTable(key) {
  const a = D.adj.athletes[key], pw = D.plan.weeks;
  const chip = st => h("span", { class: "chip " + ({ Done: "good", Partial: "warn", Missed: "bad" }[st] || "") },
    ({ Done: "✓ ", Partial: "◐ ", Missed: "✕ " }[st] || "") + st);
  const rows = a.weeks.map(w => {
    const p = pw[w.week - 1], at = p.athletes[key];
    const adjusted = w.status === "Upcoming" || w.status === "This week";
    return h("tr", { class: (w.status === "This week" ? "now " : "") + (p.cutback ? "cut" : "") },
      h("td", {}, w.week), h("td", {}, fmtDate(at.long_date || p.saturday), h("small", {}, p.phase + (p.cutback ? ", cutback" : ""))),
      h("td", {}, adjusted && w.adjusted_long !== w.planned_long
        ? h("span", {}, h("span", { class: "adj" }, km(w.adjusted_long)), h("small", {}, "plan " + km(w.planned_long)))
        : km(w.planned_long)),
      h("td", {}, w.actual_long ? km(w.actual_long) : "–"),
      h("td", {}, km(w.actual_km), h("small", {}, "plan " + km(w.planned_km))),
      h("td", {}, chip(w.status)),
      h("td", {}, checkinCell(key, w, at)),
      h("td", {}, at.runs.map(r => h("small", {}, `${r.label}: ${r.desc} (${km(r.km)})`)), p.note ? h("small", {}, p.note) : null));
  });
  return h("div", {}, h("h2", {}, `${a.name}: week by week`), h("div", { class: "table-wrap" },
    h("table", {}, h("thead", {}, h("tr", {}, ["Wk", "Long run", "Long (target)", "Long (actual)", "Distance", "Status", "Check-in", "Sessions and notes"].map(x => h("th", {}, x)))), h("tbody", {}, rows))));
}

function routeSvg(route) {
  if (!route || route.length < 3) return null;
  const la = route.map(p => p[0]), lo = route.map(p => p[1]);
  const [a0, a1, o0, o1] = [Math.min(...la), Math.max(...la), Math.min(...lo), Math.max(...lo)];
  const k = Math.cos(((a0 + a1) / 2) * Math.PI / 180), w = (o1 - o0) * k || 1e-4, hh = (a1 - a0) || 1e-4, sc = Math.min(180 / w, 80 / hh);
  const ox = (200 - w * sc) / 2, oy = (90 - hh * sc) / 2;
  const pts = route.map(p => `${(ox + (p[1] - o0) * k * sc).toFixed(1)},${(oy + (a1 - p[0]) * sc).toFixed(1)}`).join(" ");
  return s("svg", { viewBox: "0 0 200 90", role: "img", "aria-label": "Route outline" }, s("polyline", { points: pts, fill: "none", stroke: "var(--ink-2)", "stroke-width": 2, "stroke-linejoin": "round", "stroke-linecap": "round" }));
}
function recentRuns(key) {
  const runs = (D.acts[key] || []).slice(-8).reverse();
  if (!runs.length) return h("p", { class: "muted" }, "No runs yet.");
  return h("div", {}, h("h2", {}, `${D.adj.athletes[key].name}: recent runs`), h("div", { class: "runs" }, runs.map(r =>
    h("div", { class: "run" }, routeSvg(r.route) || h("svg", { viewBox: "0 0 200 90" }), h("b", {}, r.name),
      h("span", {}, `${fmtDate(r.date)} · ${km(r.distance_km)} · ${paceStr(r.moving_s / 60 / r.distance_km)}/km` + (r.avg_hr ? ` · HR ${Math.round(r.avg_hr)}` : "") + ` · ${r.elev_m} m`)))));
}

/* ---------- weekly check-ins (ticks and notes), stored in log/checkins.json via the GitHub API ---------- */
const REPO = "murray888/ultra-x-50k-training", LOGPATH = "log/checkins.json";
const CK = { log: {}, token: "", sel: {}, draft: {}, msg: {}, signin: false };
try { CK.token = localStorage.getItem("gh_token") || ""; } catch {}
const b64 = t => btoa(unescape(encodeURIComponent(t)));
const unb64 = t => decodeURIComponent(escape(atob(t.replace(/\s/g, ""))));
function ghHeaders(auth = true) {
  const hd = { Accept: "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28" };
  if (auth && CK.token) hd.Authorization = "Bearer " + CK.token;
  return hd;
}
async function ghGet() {
  const url = `https://api.github.com/repos/${REPO}/contents/${LOGPATH}?ref=main`;
  let r = await fetch(url, { cache: "no-store", headers: ghHeaders() });
  if (r.status === 401) r = await fetch(url, { cache: "no-store", headers: ghHeaders(false) });
  if (r.status === 404) return { log: {}, sha: null };
  if (!r.ok) throw new Error("GitHub " + r.status);
  const j = await r.json();
  return { log: JSON.parse(unb64(j.content)), sha: j.sha };
}
async function loadLog(get) {
  try { CK.log = (await ghGet()).log; }
  catch { CK.log = (await get("data/log.json")) || {}; }
}
async function saveWeek(key, week) {
  const d = CK.draft[key + "|" + week];
  for (let i = 0; i < 3; i++) {
    const { log, sha } = await ghGet();
    (log[key] = log[key] || {})[week] = { done: d.done, note: d.note, updated: new Date().toISOString() };
    const r = await fetch(`https://api.github.com/repos/${REPO}/contents/${LOGPATH}`, {
      method: "PUT", headers: ghHeaders(),
      body: JSON.stringify({ message: `Check-in: ${key} week ${week}`, content: b64(JSON.stringify(log, null, 1)), branch: "main", ...(sha ? { sha } : {}) }) });
    if (r.ok) { CK.log = log; delete CK.draft[key + "|" + week]; return; }
    if (r.status !== 409 && r.status !== 422) throw new Error(r.status === 401 || r.status === 403 || r.status === 404 ? "Token rejected (needs Contents: Read and write on this repo)" : "GitHub " + r.status);
  }
  throw new Error("Someone else saved at the same moment. Try again.");
}
function sessionsFor(key, week) {
  const p = D.plan.weeks[week - 1], at = p.athletes[key], aw = D.adj.athletes[key].weeks.find(x => x.week === week);
  const long = aw && aw.adjusted_long != null ? aw.adjusted_long : at.long_km;
  return [...at.runs.map(r => ({ id: r.label, text: `${r.label}: ${r.desc} (${km(r.km)})` })),
    { id: "Long", text: `Long run: ${km(long)}${at.long_date ? ", " + fmtDate(at.long_date) : ""}${at.optional ? " (optional)" : ""}` }];
}
function defaultWeek(key) {
  const sm = D.adj.athletes[key].summary;
  return Math.min(Math.max(sm.current_week || 1, 1), D.plan.weeks.length);
}
function checkinCard(key) {
  const a = D.adj.athletes[key], week = CK.sel[key] || (CK.sel[key] = defaultWeek(key)), dk = key + "|" + week;
  const p = D.plan.weeks[week - 1], saved = (CK.log[key] || {})[week] || { done: {}, note: "" };
  const cur = CK.draft[dk] || { done: { ...saved.done }, note: saved.note || "" };
  const can = !!CK.token, card = h("div", { class: "card checkin" });
  const go = n => { CK.sel[key] = Math.min(Math.max(week + n, 1), D.plan.weeks.length); card.replaceWith(checkinCard(key)); };
  const logged = (D.acts[key] || []).filter(r => r.date >= p.monday && r.date <= p.sunday);
  const save = h("button", { class: "primary" }, "Save");
  const msg = h("span", { class: "muted" }, CK.msg[dk] || "");
  const sync = () => { save.disabled = !can || !CK.draft[dk]; };
  const touch = () => { CK.draft[dk] = cur; CK.msg[dk] = ""; msg.textContent = ""; sync(); };
  card.append(h("h3", {}, h("i", { class: "dot", style: `background:${COLOURS[key]}` }), `${a.name}: week check-in`),
    h("div", { class: "weeknav" }, h("button", { class: "ghost", "aria-label": "Previous week" }, "‹"),
      h("b", {}, `Week ${week}`), h("span", { class: "muted" }, `${fmtDate(p.monday)} to ${fmtDate(p.sunday)}`),
      h("button", { class: "ghost", "aria-label": "Next week" }, "›")));
  const [prev, next] = card.querySelectorAll(".weeknav button");
  prev.onclick = () => go(-1); next.onclick = () => go(1);
  card.append(h("div", { class: "ticks" }, sessionsFor(key, week).map(x => {
    const cb = h("input", { type: "checkbox" }); cb.checked = !!cur.done[x.id]; cb.disabled = !can;
    cb.onchange = () => { cur.done[x.id] = cb.checked; touch(); };
    return h("label", {}, cb, " " + x.text);
  })));
  const ta = h("textarea", { rows: "2", maxlength: "280", placeholder: can ? "Short note (public): how it felt, niggles, what changed" : "Sign in to add a note" });
  ta.value = cur.note; ta.disabled = !can; ta.oninput = () => { cur.note = ta.value; touch(); };
  card.append(ta, h("div", { class: "muted small" }, logged.length ? `Health uploads this week: ${logged.length} run${logged.length > 1 ? "s" : ""}, ${km(logged.reduce((t, r) => t + r.distance_km, 0))}` : "No Health uploads for this week yet."));
  save.onclick = async () => {
    save.disabled = true; msg.textContent = "Saving…";
    try { await saveWeek(key, week); CK.msg[dk] = "Saved. The site refreshes in about a minute."; }
    catch (e) { CK.msg[dk] = "Not saved: " + e.message; }
    card.replaceWith(checkinCard(key));
  };
  sync();
  const auth = h("div", { class: "auth muted small" });
  if (can) {
    auth.append("Signed in on this device. ", h("button", { class: "link" }, "Sign out"));
    auth.querySelector("button").onclick = () => { CK.token = ""; try { localStorage.removeItem("gh_token"); } catch {} render(); };
  } else if (CK.signin) {
    const inp = h("input", { type: "password", placeholder: "GitHub token", autocomplete: "off" });
    const ok = h("button", { class: "primary" }, "Use token");
    ok.onclick = () => { CK.token = inp.value.trim(); CK.signin = false; try { localStorage.setItem("gh_token", CK.token); } catch {} render(); };
    auth.append(inp, ok);
  } else {
    const b = h("button", { class: "link" }, "Sign in to tick and add notes");
    b.onclick = () => { CK.signin = true; render(); };
    auth.append(b);
  }
  card.append(h("div", { class: "actions" }, save, msg), auth);
  return card;
}
const checkinCell = (key, w, at) => {
  const e = (CK.log[key] || {})[w.week];
  if (!e) return "–";
  const ids = [...at.runs.map(r => r.label), "Long"];
  return h("span", {}, ids.map(i => (e.done && e.done[i] ? "✓ " : "◻ ") + i).join("  "), e.note ? h("small", {}, e.note) : null);
};

/* ---------- page ---------- */
function render() {
  const L = keys(), main = $("#main");
  main.replaceChildren(
    h("section", { class: "grid" }, L.map(summaryCard)),
    h("section", { class: "grid" }, L.map(checkinCard)),
    h("section", {}, longChart(L)),
    h("section", { class: "grid" }, L.map(weeklyChart)),
    h("section", {}, trendChart(L)),
    ...L.map(k => h("section", {}, planTable(k))),
    ...L.map(k => h("section", {}, recentRuns(k))));
  document.querySelectorAll(".tab").forEach(t => t.setAttribute("aria-selected", String(t.dataset.tab === tab)));
}
function init() {
  const tabs = $("#tabs");
  [["overview", "Both"], ...Object.entries(D.adj.athletes).map(([k, a]) => [k, a.name])].forEach(([k, label]) => {
    const b = h("button", { class: "tab", role: "tab", "data-tab": k }, k === "overview" ? null : h("i", { class: "dot", style: `background:${COLOURS[k]}` }), label);
    b.addEventListener("click", () => { tab = k; render(); }); tabs.append(b);
  });
  const sm = D.adj.athletes[Object.keys(D.adj.athletes)[0]].summary;
  $("#countdown").replaceChildren(h("b", {}, `${sm.days_to_race} days`), `to ${fmtDate(D.adj.race.date)} · ${D.adj.race.start} start`);
  $("#sub").textContent = "Updated " + new Date(D.adj.generated).toLocaleString("en-GB", { dateStyle: "medium", timeStyle: "short" }) + " · plan as of " + fmtDate(D.adj.today);
  if (D.meta.demo) { const b = $("#banner"); b.hidden = false; b.textContent = "Demo data: these runs are invented to show how the site works. Real Apple Health runs replace them after the first upload."; }
  render();
}
$("#theme").addEventListener("click", () => {
  const r = document.documentElement, dark = getComputedStyle(r).colorScheme === "dark";
  r.setAttribute("data-theme", dark ? "light" : "dark");
  try { localStorage.setItem("theme", dark ? "light" : "dark"); } catch {}
});
try { const t = localStorage.getItem("theme"); if (t) document.documentElement.setAttribute("data-theme", t); } catch {}
load().then(() => { if (!D.adj || !D.plan) { $("#main").textContent = "No data yet. Run the workflow once to generate it."; return; } init(); });
