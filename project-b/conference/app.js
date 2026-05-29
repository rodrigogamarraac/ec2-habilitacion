const API_BASE = window.SYMPOSIUM_API_BASE || "/api/v1";

const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];

const state = {
  q: "",
  track: "",
  day: "",
  tz: Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC",
  page: 1,
  pageSize: 12,
  tracks: [],
  sessionsCount: 0,
};

/* ---------- API ---------- */

const api = {
  async tracks() {
    const r = await fetch(`${API_BASE}/tracks/`);
    if (!r.ok) throw new Error(`tracks ${r.status}`);
    return r.json();
  },
  async sessions(params) {
    const qs = new URLSearchParams();
    if (params.q) qs.set("q", params.q);
    if (params.track) qs.set("track", params.track);
    if (params.day) qs.set("day", params.day);
    if (params.tz) qs.set("tz", params.tz);
    qs.set("page", params.page);
    qs.set("page_size", params.pageSize);
    const r = await fetch(`${API_BASE}/sessions/?${qs}`);
    if (!r.ok) throw new Error(`sessions ${r.status}`);
    return r.json();
  },
  async session(id) {
    const r = await fetch(`${API_BASE}/sessions/${id}`);
    if (r.status === 404) return null;
    if (!r.ok) throw new Error(`session ${r.status}`);
    return r.json();
  },
  async healthz() {
    try {
      const r = await fetch(`${API_BASE}/healthz`, { cache: "no-store" });
      return r.ok;
    } catch (_) {
      return false;
    }
  },
};

/* ---------- formatting (timezone-aware) ---------- */

function fmtClock(iso, tz) {
  return new Date(iso).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
    timeZone: tz,
  });
}
function fmtDay(iso, tz) {
  return new Date(iso).toLocaleDateString(undefined, {
    weekday: "short",
    day: "2-digit",
    month: "short",
    timeZone: tz,
  });
}
function fmtDayISO(iso, tz) {
  // For comparison in the day picker
  const d = new Date(iso);
  const parts = new Intl.DateTimeFormat("en-CA", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    timeZone: tz,
  }).formatToParts(d);
  const y = parts.find((p) => p.type === "year").value;
  const m = parts.find((p) => p.type === "month").value;
  const da = parts.find((p) => p.type === "day").value;
  return `${y}-${m}-${da}`;
}
function durationMin(a, b) {
  return Math.max(0, Math.round((new Date(b) - new Date(a)) / 60000));
}
function escapeHTML(s = "") {
  return String(s).replace(
    /[&<>"']/g,
    (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c],
  );
}

/* ---------- rendering ---------- */

function renderTracksChips(tracks) {
  const host = $("#track-filter");
  // wipe everything except the "All tracks" button
  $$('#track-filter .chip:not([data-track=""])').forEach((n) => n.remove());
  for (const t of tracks) {
    const b = document.createElement("button");
    b.className = "chip";
    b.dataset.track = t.id;
    b.textContent = t.name;
    b.style.setProperty("--track-color", t.color || "");
    b.role = "tab";
    b.ariaSelected = "false";
    host.appendChild(b);
  }
  host.addEventListener(
    "click",
    (e) => {
      const btn = e.target.closest(".chip");
      if (!btn) return;
      $$("#track-filter .chip").forEach((c) => {
        c.classList.toggle("is-active", c === btn);
        c.ariaSelected = c === btn ? "true" : "false";
      });
      state.track = btn.dataset.track || "";
      state.page = 1;
      loadSessions();
    },
    { once: true },
  );
}

function renderTrackGrid(tracks) {
  $("#track-grid").innerHTML = tracks
    .map(
      (t) => `
    <article class="track-card" style="--track-color: ${t.color || "#6f1d1b"}">
      <h3 class="track-name">${escapeHTML(t.name)}</h3>
      <p class="track-count">${t.session_count ?? 0} sessions</p>
      <p class="track-desc">${escapeHTML(t.description || "")}</p>
    </article>
  `,
    )
    .join("");
  $("#stat-tracks").textContent = tracks.length;
}

function seatBucket(s) {
  if (!s.capacity) return "";
  const left = Math.max(0, s.capacity - (s.registered || 0));
  if (left === 0) return "is-full";
  if (left / s.capacity < 0.15) return "is-low";
  return "";
}

function renderSessions(items) {
  const ol = $("#session-list");
  ol.setAttribute("aria-busy", "false");
  if (!items.length) {
    ol.innerHTML = `<li class="loading">No sessions match. Try another track or topic.</li>`;
    return;
  }

  ol.innerHTML = items
    .map((s) => {
      const left = s.capacity ? Math.max(0, s.capacity - (s.registered || 0)) : null;
      const speakerLine = (s.speakers || [])
        .map(
          (sp) =>
            sp.name +
            (sp.affiliation
              ? ` <span style="color:var(--muted)">(${escapeHTML(sp.affiliation)})</span>`
              : ""),
        )
        .join(" &nbsp;·&nbsp; ");
      return `
      <li>
        <article class="session" tabindex="0" role="button"
                 data-id="${s.id}" aria-label="${escapeHTML(s.title)}, open detail"
                 style="--track-color: ${s.track?.color || "#6f1d1b"}">
          <div class="session-time">
            <span class="day">${escapeHTML(fmtDay(s.starts_at, state.tz))}</span>
            <span class="clock">${escapeHTML(fmtClock(s.starts_at, state.tz))}</span>
            <span class="dur">${durationMin(s.starts_at, s.ends_at)} min</span>
          </div>
          <div class="session-body">
            <div class="session-track">${escapeHTML(s.track?.name || "General")}</div>
            <h3 class="session-title">${escapeHTML(s.title)}</h3>
            <p class="session-people">${speakerLine || "Speakers to be announced."}</p>
          </div>
          <div class="session-seats">
            <span class="seat-num ${seatBucket(s)}">${left ?? "—"}</span>
            <div class="seat-label">${left === 0 ? "full" : "seats"}</div>
          </div>
        </article>
      </li>
    `;
    })
    .join("");
}

function renderTzOptions() {
  const sel = $("#tz");
  // A reasonable shortlist; the user can still use the OS default they were assigned.
  const zones = [
    state.tz,
    "UTC",
    "Europe/London",
    "Europe/Berlin",
    "Europe/Madrid",
    "America/New_York",
    "America/Mexico_City",
    "America/Sao_Paulo",
    "America/La_Paz",
    "America/Buenos_Aires",
    "Asia/Tokyo",
    "Asia/Singapore",
    "Australia/Sydney",
  ];
  const uniq = [...new Set(zones)];
  sel.innerHTML = uniq
    .map(
      (z) =>
        `<option value="${escapeHTML(z)}" ${z === state.tz ? "selected" : ""}>${escapeHTML(z)}</option>`,
    )
    .join("");
}

function renderDayOptionsFrom(sessions) {
  const sel = $("#day");
  const current = sel.value;
  const days = [...new Set(sessions.map((s) => fmtDayISO(s.starts_at, state.tz)))].sort();
  sel.innerHTML =
    `<option value="">All days</option>` +
    days
      .map(
        (d) => `<option value="${d}" ${d === current ? "selected" : ""}>${escapeHTML(d)}</option>`,
      )
      .join("");
}

/* ---------- modal ---------- */

const modal = $("#session-modal");

async function openSession(id) {
  modal.showModal();
  $("#modal-content").innerHTML = `<p class="loading">Loading…</p>`;
  let s;
  try {
    s = await api.session(id);
  } catch (err) {
    $("#modal-content").innerHTML = `<p>API trouble — ${escapeHTML(err.message)}</p>`;
    return;
  }
  if (!s) {
    $("#modal-content").innerHTML = `<p>Session not found.</p>`;
    return;
  }

  const speakers = (s.speakers || [])
    .map(
      (sp) => `
    <li>
      <span class="spk-i">${escapeHTML(
        (sp.name || "?")
          .split(/\s+/)
          .map((p) => p[0])
          .slice(0, 2)
          .join(""),
      )}</span>
      <span>
        <span class="spk-n">${escapeHTML(sp.name)}</span><br>
        ${sp.affiliation ? `<span class="spk-a">${escapeHTML(sp.affiliation)}</span>` : ""}
      </span>
    </li>
  `,
    )
    .join("");

  $("#modal-content").innerHTML = `
    <h2>${escapeHTML(s.title)}</h2>
    <p class="sub">
      ${escapeHTML(fmtDay(s.starts_at, state.tz))} —
      ${escapeHTML(fmtClock(s.starts_at, state.tz))}
      to ${escapeHTML(fmtClock(s.ends_at, state.tz))}
      (${escapeHTML(state.tz)}) ·
      ${escapeHTML(s.track?.name || "General")}
    </p>
    ${s.abstract ? `<p class="abstract">${escapeHTML(s.abstract)}</p>` : ""}
    <ul class="speakers">${speakers || '<li class="spk-a" style="font-style:italic">Speakers TBA.</li>'}</ul>
  `;
}

modal.addEventListener("click", (e) => {
  if (e.target.matches("[data-close]") || e.target === modal) modal.close();
});

/* ---------- loading ---------- */

async function loadTracks() {
  try {
    const tracks = await api.tracks();
    state.tracks = tracks;
    renderTracksChips(tracks);
    renderTrackGrid(tracks);
  } catch (err) {
    $("#track-grid").innerHTML =
      `<p class="loading">Tracks unavailable — ${escapeHTML(err.message)}</p>`;
  }
}

async function loadSessions() {
  $("#session-list").setAttribute("aria-busy", "true");
  try {
    const data = await api.sessions(state);
    renderSessions(data.results || []);
    state.sessionsCount = data.count || 0;
    $("#stat-sessions").textContent = state.sessionsCount;
    // approximate speakers + seats
    const allSpeakers = new Set();
    let seats = 0;
    for (const s of data.results || []) {
      (s.speakers || []).forEach((sp) => allSpeakers.add(sp.id || sp.name));
      seats += Math.max(0, (s.capacity || 0) - (s.registered || 0));
    }
    $("#stat-speakers").textContent = allSpeakers.size;
    $("#stat-seats").textContent = seats;
    renderDayOptionsFrom(data.results || []);
  } catch (err) {
    $("#session-list").innerHTML =
      `<li class="loading">Could not load sessions — ${escapeHTML(err.message)}</li>`;
  }
}

/* ---------- wiring ---------- */

document.addEventListener("click", (e) => {
  const card = e.target.closest(".session");
  if (card) openSession(card.dataset.id);
});
document.addEventListener("keydown", (e) => {
  if (!(e.target instanceof HTMLElement)) return;
  if ((e.key === "Enter" || e.key === " ") && e.target.classList.contains("session")) {
    e.preventDefault();
    openSession(e.target.dataset.id);
  }
});

$("#q").addEventListener(
  "input",
  debounce((e) => {
    state.q = e.target.value.trim();
    state.page = 1;
    loadSessions();
  }, 250),
);

$("#tz").addEventListener("change", (e) => {
  state.tz = e.target.value;
  state.page = 1;
  loadSessions();
});

$("#day").addEventListener("change", (e) => {
  state.day = e.target.value;
  state.page = 1;
  loadSessions();
});

function debounce(fn, ms) {
  let t;
  return (...a) => {
    clearTimeout(t);
    t = setTimeout(() => fn(...a), ms);
  };
}

/* ---------- health ---------- */

(async function pulse() {
  const pill = $("#health-pill");
  const ok = await api.healthz();
  pill.className = "pill " + (ok ? "ok" : "bad");
  pill.textContent = ok ? "online" : "offline";
  setTimeout(pulse, 15000);
})();

/* ---------- boot ---------- */

renderTzOptions();
loadTracks();
loadSessions();
