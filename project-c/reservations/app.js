const API_BASE = window.MESA_API_BASE || "/api/v1";

const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];

const api = {
  async tableTypes() {
    const r = await fetch(`${API_BASE}/tables/types/`);
    if (!r.ok) throw new Error(`table types ${r.status}`);
    return r.json();
  },
  async availability({ date, time, party, tableType }) {
    const qs = new URLSearchParams({ date, party });
    if (time) qs.set("time", time);
    if (tableType) qs.set("table_type", tableType);
    qs.set("tz", Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC");
    const r = await fetch(`${API_BASE}/reservations/availability/?${qs}`);
    if (!r.ok) throw new Error(`availability ${r.status}`);
    return r.json();
  },
  async menu(date) {
    const qs = new URLSearchParams({ date });
    const r = await fetch(`${API_BASE}/menu/?${qs}`);
    if (!r.ok) throw new Error(`menu ${r.status}`);
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

/* ---------- helpers ---------- */

function todayISO() {
  const d = new Date();
  const off = d.getTimezoneOffset();
  const local = new Date(d.getTime() - off * 60000);
  return local.toISOString().slice(0, 10);
}
function addDays(iso, n) {
  const d = new Date(iso + "T00:00:00");
  d.setDate(d.getDate() + n);
  return d.toISOString().slice(0, 10);
}
function money(n) {
  if (n == null) return "—";
  return `€${Number(n).toFixed(0)}`;
}
function escapeHTML(s = "") {
  return String(s).replace(
    /[&<>"']/g,
    (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c],
  );
}

/* ---------- table types ---------- */

async function loadTableTypes() {
  let types = [];
  try {
    types = await api.tableTypes();
  } catch (_) {
    // graceful: leave the type selector with just "Any"
    return;
  }
  const sel = $("#f-type");
  for (const t of types) {
    const o = document.createElement("option");
    o.value = t.id;
    o.textContent = `${t.name} (${t.seats} seats)`;
    sel.appendChild(o);
  }
}

/* ---------- availability ---------- */

function renderResults(slots) {
  const host = $("#results");
  host.setAttribute("aria-busy", "false");
  if (!slots.length) {
    host.innerHTML = `<p class="empty">No tables open for that combination. Try another date or party size.</p>`;
    return;
  }
  host.innerHTML = slots
    .map((s) => {
      const left = s.available_seats ?? 0;
      let cls = "";
      if (s.seats && left === 0) cls = "is-full";
      else if (s.seats && left / s.seats < 0.25) cls = "is-low";
      const disabled = left === 0;
      return `
      <article class="slot">
        <div class="slot-time">${escapeHTML(s.time)}</div>
        <div class="slot-meta">
          <p class="slot-table">${escapeHTML(s.table_type_name || "Table")}</p>
          <p class="slot-desc">${escapeHTML(s.table_type_desc || "")}</p>
        </div>
        <div class="slot-seats ${cls}">
          ${disabled ? "Booked" : `${left} of ${s.seats}`}
          <small>${disabled ? "" : "free"}</small>
        </div>
        <div class="slot-price">${money(s.price_per_seat)}<small style="display:block;font-size:11px;letter-spacing:.18em;text-transform:uppercase;color:var(--muted);font-family:var(--f-sans);font-weight:400">per seat</small></div>
        <button class="slot-book" ${disabled ? "disabled" : ""}
                data-table-type="${s.table_type}"
                data-table-type-name="${escapeHTML(s.table_type_name || "")}"
                data-time="${escapeHTML(s.time)}"
                data-price="${s.price_per_seat ?? ""}">
          ${disabled ? "Sold out" : "Book"}
        </button>
      </article>
    `;
    })
    .join("");
}

async function search(e) {
  if (e) e.preventDefault();
  const date = $("#f-date").value;
  const time = $("#f-time").value;
  const party = $("#f-party").value;
  const type = $("#f-type").value;
  if (!date) {
    $("#f-date").focus();
    return;
  }
  $("#results").setAttribute("aria-busy", "true");
  $("#results").innerHTML = `<p class="empty">Looking up tables…</p>`;

  try {
    const slots = await api.availability({ date, time, party, tableType: type });
    renderResults(slots);
  } catch (err) {
    $("#results").innerHTML =
      `<p class="empty">Couldn't reach the kitchen — ${escapeHTML(err.message)}</p>`;
  }
  // also refresh menu for the date
  loadMenu(date);
}

/* ---------- menu ---------- */

async function loadMenu(date) {
  const list = $("#menu-list");
  list.innerHTML = `<li class="empty">Loading…</li>`;
  let dishes = [];
  try {
    dishes = await api.menu(date || todayISO());
  } catch (err) {
    list.innerHTML = `<li class="empty">Menu unavailable — ${escapeHTML(err.message)}</li>`;
    return;
  }
  if (!dishes.length) {
    list.innerHTML = `<li class="empty">No menu published for that date yet.</li>`;
    return;
  }
  list.innerHTML = dishes
    .map(
      (d) => `
    <li class="dish">
      <p class="dish-course">${escapeHTML(d.course || "Course")}</p>
      <h3 class="dish-name">${escapeHTML(d.name)}</h3>
      <p class="dish-price">${money(d.price)}</p>
      ${d.description ? `<p class="dish-desc">${escapeHTML(d.description)}</p>` : ""}
      ${d.allergens?.length ? `<p class="dish-allergens">Contains: ${d.allergens.map(escapeHTML).join(", ")}</p>` : ""}
    </li>
  `,
    )
    .join("");
}

/* ---------- hero stats ---------- */

async function refreshHero() {
  try {
    const today = todayISO();
    const todaySlots = await api.availability({ date: today, party: 2 });
    const tonightFree = todaySlots.reduce((sum, s) => sum + (s.available_seats || 0), 0);
    $("#hero-tonight").textContent = tonightFree > 0 ? `${tonightFree} seats` : "fully booked";

    // sum a week
    const weeks = await Promise.all(
      [0, 1, 2, 3, 4, 5, 6].map((n) =>
        api.availability({ date: addDays(today, n), party: 2 }).catch(() => []),
      ),
    );
    const weekFree = weeks.flat().reduce((sum, s) => sum + (s.available_seats || 0), 0);
    $("#hero-week").textContent = `${weekFree} seats`;
  } catch (_) {
    $("#hero-tonight").textContent = "—";
    $("#hero-week").textContent = "—";
  }
}

/* ---------- confirm dialog ---------- */

const confirmDlg = $("#confirm");

document.addEventListener("click", (e) => {
  const btn = e.target.closest(".slot-book");
  if (btn && !btn.disabled) {
    const date = $("#f-date").value;
    const party = $("#f-party").value;
    const total = btn.dataset.price
      ? `€${(Number(btn.dataset.price) * Number(party)).toFixed(0)}`
      : "";
    $("#confirm-title").textContent = `Table for ${party}`;
    $("#confirm-sub").textContent =
      `${btn.dataset.tableTypeName} · ${date} at ${btn.dataset.time}` +
      (total ? ` · approx. ${total}` : "");
    confirmDlg.showModal();
  }
});
confirmDlg.addEventListener("click", (e) => {
  if (e.target.matches("[data-close]") || e.target === confirmDlg) confirmDlg.close();
});
$("#c-confirm").addEventListener("click", () => {
  // Read-only spec — don't actually POST. Just close with a confirmation.
  confirmDlg.close();
  alert(
    "In a real build this would POST /api/v1/reservations/. For this assignment the API is read-only.",
  );
});

/* ---------- wiring ---------- */

$("#finder").addEventListener("submit", search);
$("#f-date").valueAsDate = new Date(todayISO() + "T12:00:00");

/* ---------- health pulse ---------- */

(async function pulse() {
  const ok = await api.healthz();
  $("#health-dot").className = "dot " + (ok ? "ok" : "bad");
  $("#health-text").textContent = ok ? "open" : "closed";
  setTimeout(pulse, 15000);
})();

/* ---------- boot ---------- */

loadTableTypes();
loadMenu(todayISO());
refreshHero();
