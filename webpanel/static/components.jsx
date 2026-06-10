/* global React */
// REBOBINA — Componentes base e iconos. Exporta a window.
const { useState, useMemo, useEffect, useRef } = React;

/* ----------------------------- Iconos (stroke) ----------------------------- */
const Ico = {
  grid: "M3 3h7v7H3zM14 3h7v7h-7zM14 14h7v7h-7zM3 14h7v7H3z",
  inbox: "M3 12l3-7h12l3 7M3 12v6a1 1 0 001 1h16a1 1 0 001-1v-6M3 12h5l2 3h4l2-3h5",
  bell: "M18 8a6 6 0 00-12 0c0 7-3 9-3 9h18s-3-2-3-9M13.7 21a2 2 0 01-3.4 0",
  film: "M3 4h18v16H3zM7 4v16M17 4v16M3 9h4M3 15h4M17 9h4M17 15h4",
  users: "M16 21v-2a4 4 0 00-4-4H6a4 4 0 00-4 4v2M9 11a4 4 0 100-8 4 4 0 000 8M22 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75",
  tag: "M20.59 13.41l-7.17 7.17a2 2 0 01-2.83 0L2 12V2h10l8.59 8.59a2 2 0 010 2.82zM7 7h.01",
  history: "M3 3v5h5M3.05 13A9 9 0 106 5.3L3 8M12 7v5l4 2",
  truck: "M1 3h15v13H1zM16 8h4l3 3v5h-7M5.5 19a2.5 2.5 0 100-5 2.5 2.5 0 000 5M18.5 19a2.5 2.5 0 100-5 2.5 2.5 0 000 5",
  search: "M11 19a8 8 0 100-16 8 8 0 000 16zM21 21l-4.35-4.35",
  check: "M20 6L9 17l-5-5",
  x: "M18 6L6 18M6 6l12 12",
  alert: "M12 9v4M12 17h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z",
  box: "M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0021 16zM3.27 6.96L12 12.01l8.73-5.05M12 22.08V12",
  clock: "M12 22a10 10 0 100-20 10 10 0 000 20zM12 6v6l4 2",
  arrowDown: "M12 5v14M19 12l-7 7-7-7",
  arrowUp: "M12 19V5M5 12l7-7 7 7",
  plus: "M12 5v14M5 12h14",
  star: "M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01z",
  chat: "M21 11.5a8.38 8.38 0 01-.9 3.8 8.5 8.5 0 01-7.6 4.7 8.38 8.38 0 01-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 01-.9-3.8 8.5 8.5 0 014.7-7.6 8.38 8.38 0 013.8-.9h.5a8.48 8.48 0 018 8v.5z",
  phone: "M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07 19.5 19.5 0 01-6-6 19.79 19.79 0 01-3.07-8.67A2 2 0 014.11 2h3a2 2 0 012 1.72c.13.96.36 1.9.7 2.81a2 2 0 01-.45 2.11L8.09 9.91a16 16 0 006 6l1.27-1.27a2 2 0 012.11-.45c.9.34 1.85.57 2.81.7A2 2 0 0122 16.92z",
  cart: "M9 22a1 1 0 100-2 1 1 0 000 2zM20 22a1 1 0 100-2 1 1 0 000 2zM1 1h4l2.68 13.39a2 2 0 002 1.61h9.72a2 2 0 002-1.61L23 6H6",
  refresh: "M23 4v6h-6M1 20v-6h6M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15",
  rent: "M9 17H7A5 5 0 017 7h2M15 7h2a5 5 0 010 10h-2M8 12h8",
  dollar: "M12 1v22M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6",
  sparkle: "M12 3l1.9 5.8L20 10l-6.1 1.2L12 17l-1.9-5.8L4 10l6.1-1.2z",
  eye: "M1 12s4-7 11-7 11 7 11 7-4 7-11 7-11-7-11-7zM12 15a3 3 0 100-6 3 3 0 000 6z",
  settings: "M12 15a3 3 0 100-6 3 3 0 000 6zM19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 11-2.83 2.83l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 11-2.83-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 112.83-2.83l.06.06a1.65 1.65 0 001.82.33H9a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 112.83 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z",
  trend: "M23 6l-9.5 9.5-5-5L1 18",
  chevron: "M9 18l6-6-6-6",
};

function Icon({ name, className, style }) {
  const d = Ico[name] || Ico.grid;
  return (
    React.createElement("svg", { className, style, viewBox: "0 0 24 24", fill: "none",
      stroke: "currentColor", strokeWidth: 2, strokeLinecap: "round", strokeLinejoin: "round" },
      d.split("M").filter(Boolean).map((seg, i) =>
        React.createElement("path", { key: i, d: "M" + seg })))
  );
}

/* WhatsApp glyph (filled) */
function WaIcon({ className }) {
  return React.createElement("svg", { className, viewBox: "0 0 24 24", fill: "currentColor" },
    React.createElement("path", { d: "M12.04 2C6.58 2 2.13 6.45 2.13 11.91c0 1.75.46 3.46 1.32 4.96L2 22l5.25-1.38a9.9 9.9 0 004.79 1.22h.01c5.46 0 9.91-4.45 9.91-9.91 0-2.65-1.03-5.14-2.9-7.01A9.82 9.82 0 0012.04 2zm5.8 14.13c-.25.69-1.45 1.32-2 1.4-.51.08-1.16.11-1.87-.12-.43-.14-.98-.32-1.69-.62-2.97-1.28-4.91-4.27-5.06-4.47-.15-.2-1.21-1.61-1.21-3.07 0-1.46.77-2.18 1.04-2.48.27-.3.59-.37.79-.37.2 0 .39 0 .56.01.18.01.42-.07.66.5.25.59.84 2.04.91 2.19.07.15.12.32.02.52-.1.2-.15.32-.3.5-.15.17-.31.39-.45.52-.15.15-.3.31-.13.6.17.3.76 1.25 1.63 2.02 1.12 1 2.07 1.31 2.36 1.46.3.15.47.12.64-.07.17-.2.74-.86.94-1.16.2-.3.39-.25.66-.15.27.1 1.71.81 2 .96.3.15.49.22.56.35.07.12.07.72-.18 1.41z" }));
}

/* ----------------------------- Sidebar ----------------------------- */
function Sidebar({ active, onNav, badges }) {
  const D = window.STORE_DATA.derived;
  const groups = [
    { label: "Operación", items: [
      { id: "resumen", icon: "grid", label: "Resumen" },
      { id: "validar", icon: "inbox", label: "Por validar", badge: { n: D.pendingCount, kind: "amber" } },
      { id: "alertas", icon: "bell", label: "Alertas", badge: { n: badges.alertas, kind: "red" } },
    ]},
    { label: "Tienda", items: [
      { id: "catalogo", icon: "film", label: "Catálogo" },
      { id: "clientes", icon: "users", label: "Clientes" },
      { id: "descuentos", icon: "tag", label: "Descuentos" },
    ]},
    { label: "Registros", items: [
      { id: "historial", icon: "history", label: "Historial" },
      { id: "restock", icon: "truck", label: "Reabastecimiento", badge: { n: D.restockPending, kind: "dim" } },
    ]},
  ];
  return (
    React.createElement("aside", { className: "sidebar" },
      React.createElement("div", { className: "brand" },
        React.createElement("div", { className: "brand-mark" },
          React.createElement(Icon, { name: "refresh" })),
        React.createElement("div", null,
          React.createElement("div", { className: "brand-name" }, "REBOBINA"),
          React.createElement("div", { className: "brand-sub" }, "Renta & Venta"))),
      React.createElement("nav", { className: "nav scroll" },
        groups.map((g) =>
          React.createElement("div", { key: g.label },
            React.createElement("div", { className: "nav-label" }, g.label),
            g.items.map((it) =>
              React.createElement("button", {
                key: it.id, className: "nav-item" + (active === it.id ? " active" : ""),
                onClick: () => onNav(it.id) },
                React.createElement(Icon, { name: it.icon }),
                React.createElement("span", { className: "lbl" }, it.label),
                it.badge && it.badge.n > 0 &&
                  React.createElement("span", { className: "nav-badge " + it.badge.kind }, it.badge.n)))))),
      React.createElement("div", { className: "sidebar-foot" },
        React.createElement("div", { className: "avatar" }, "A"),
        React.createElement("div", null,
          React.createElement("div", { className: "who" }, "Alan D."),
          React.createElement("div", { className: "role" }, "Dueño · Mostrador"))))
  );
}

/* ----------------------------- TopBar ----------------------------- */
function TopBar({ title, sub, query, setQuery, onBell, alertCount }) {
  return (
    React.createElement("div", { className: "topbar" },
      React.createElement("div", null,
        React.createElement("div", { className: "page-title" }, title),
        sub && React.createElement("div", { className: "page-sub" }, sub)),
      React.createElement("label", { className: "search" },
        React.createElement(Icon, { name: "search" }),
        React.createElement("input", { value: query, placeholder: "Buscar películas, clientes, pedidos…",
          onChange: (e) => setQuery(e.target.value) })),
      React.createElement("button", { className: "icon-btn", onClick: onBell, title: "Alertas" },
        React.createElement(Icon, { name: "bell" }),
        alertCount > 0 && React.createElement("span", { className: "dot" })))
  );
}

/* ----------------------------- Primitives ----------------------------- */
function Stat({ label, value, unit, foot, icon, tone, danger, accent }) {
  const toneBg = { red: "var(--red-soft)", green: "var(--green-soft)", amber: "var(--amber-soft)", blue: "var(--blue-soft)" };
  const toneFg = { red: "var(--red)", green: "var(--green)", amber: "var(--accent-deep)", blue: "var(--blue)" };
  return (
    React.createElement("div", { className: "stat" + (danger ? " danger" : "") + (accent ? " accent" : "") },
      React.createElement("div", { className: "label" }, label),
      React.createElement("div", { className: "value" }, value,
        unit && React.createElement("span", { className: "unit" }, " " + unit)),
      foot && React.createElement("div", { className: "foot" }, foot),
      icon && !accent && React.createElement("div", { className: "ico", style: { background: toneBg[tone] || "var(--surface-3)", color: toneFg[tone] || "var(--ink-2)" } },
        React.createElement(Icon, { name: icon })))
  );
}

function Chip({ kind, children, dot, icon }) {
  return React.createElement("span", { className: "chip " + (kind || "dim") + (dot ? " dot" : "") },
    icon && React.createElement(Icon, { name: icon }), children);
}

function Fmt({ format }) {
  const cls = format === "4K" ? "f4k" : format === "Blu-ray" ? "fblu" : "";
  return React.createElement("span", { className: "fmt " + cls }, format);
}

// Color de "póster" derivado del título
function posterColor(title) {
  let h = 0;
  for (let i = 0; i < title.length; i++) h = (h * 31 + title.charCodeAt(i)) % 360;
  return `linear-gradient(155deg, hsl(${h} 42% 32%), hsl(${(h + 40) % 360} 48% 22%))`;
}
function Poster({ title }) {
  return React.createElement("div", { className: "poster", style: { background: posterColor(title) } },
    title.replace(/^(El|La|Los|Las)\s/i, "").charAt(0));
}

function Channel({ channel }) {
  if (channel === "whatsapp")
    return React.createElement("span", { className: "wa" }, React.createElement(WaIcon, {}), "WhatsApp");
  return React.createElement("span", { className: "ch-mostrador" }, React.createElement(Icon, { name: "settings" }), "Mostrador");
}

function Meter({ value, max }) {
  const pct = Math.min(100, (value / max) * 100);
  const cls = value === 0 ? "crit" : value <= 2 ? "crit" : value <= 4 ? "low" : "";
  return React.createElement("div", { className: "meter " + cls },
    React.createElement("i", { style: { width: Math.max(6, pct) + "%" } }));
}

function Empty({ icon, text }) {
  return React.createElement("div", { className: "empty" },
    React.createElement(Icon, { name: icon || "check" }),
    React.createElement("div", null, text));
}

/* tiempo relativo */
function timeAgo(isoStr) {
  const now = new Date(window.STORE_DATA.TODAY).getTime();
  const diff = (now - new Date(isoStr).getTime()) / 60000;
  if (diff < 1) return "ahora";
  if (diff < 60) return `hace ${Math.round(diff)} min`;
  if (diff < 1440) return `hace ${Math.round(diff / 60)} h`;
  return `hace ${Math.round(diff / 1440)} d`;
}
function fmtMoney(n) { return "$" + Number(n).toLocaleString("es-MX"); }
function fmtDate(isoStr) {
  return new Date(isoStr).toLocaleDateString("es-MX", { day: "2-digit", month: "short" });
}

Object.assign(window, {
  Icon, WaIcon, Sidebar, TopBar, Stat, Chip, Fmt, Poster, Channel, Meter, Empty,
  posterColor, timeAgo, fmtMoney, fmtDate,
});
