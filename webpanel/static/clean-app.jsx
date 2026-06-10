/* global React, ReactDOM, useTweaks, TweaksPanel, TweakSection, TweakRadio, TweakColor,
   Icon, WaIcon, fmtMoney, fmtDate, timeAgo, Channel, posterColor,
   CleanCatalogo, CleanClientes, CleanDescuentos, CleanHistorial, CleanRestock, CleanBar, CleanPf */
const { useState: useC, useEffect: useCE, useMemo: useCM } = React;

const CLEAN_DEFAULTS = /*EDITMODE-BEGIN*/{
  "theme": "lobby",
  "accent": "#b9802b",
  "dash": "prioridad"
}/*EDITMODE-END*/;

/* alertas (versión limpia, sin depender de v1) */
function cleanAlerts() {
  const D = window.STORE_DATA; const out = [];
  D.derived.outOfStock.forEach((m) => out.push({ id: "out-" + m.id, sev: "red", icon: "box", cat: "Agotado", title: `${m.title} agotado`, meta: `${m.format} · ${m.genre}`, data: m }));
  D.derived.overdue.forEach((r) => out.push({ id: "due-" + r.id, sev: "red", icon: "clock", cat: "Renta vencida", title: `${r.title} sin devolver`, meta: `${r.customer_name} · venció ${fmtDate(r.due_date)}`, data: r }));
  D.derived.lowStock.forEach((m) => out.push({ id: "low-" + m.id, sev: "amber", icon: "alert", cat: "Stock bajo", title: `${m.title}`, meta: `quedan ${m.stock} · demanda ${m.demand}`, data: m }));
  D.restock.filter((r) => r.type === "titulo_nuevo" && r.status === "pendiente").forEach((r) => out.push({ id: "new-" + r.id, sev: "blue", icon: "sparkle", cat: "Solicitado", title: `${r.title}`, meta: `${r.requests} solicitudes · no está en catálogo`, data: r }));
  const o = { red: 0, amber: 1, blue: 2 }; return out.sort((a, b) => o[a.sev] - o[b.sev]);
}

const PAGES = {
  resumen: ["Resumen", "Lo esencial de hoy"],
  validar: ["Por validar", "Pedidos que esperan tu confirmación"],
  alertas: ["Alertas", "Lo que necesita atención"],
  catalogo: ["Catálogo", "Existencias y precios"],
  clientes: ["Clientes", "Registrados y frecuentes"],
  descuentos: ["Descuentos", "Reglas automáticas"],
  historial: ["Historial", "Compras y rentas"],
  restock: ["Reabastecimiento", "Qué volver a pedir"],
};

/* ============================ SIDEBAR ============================ */
function CleanSide({ view, go }) {
  const D = window.STORE_DATA.derived;
  const groups = [
    ["Operación", [["resumen", "grid", null], ["validar", "inbox", D.pendingCount], ["alertas", "bell", cleanAlerts().length]]],
    ["Tienda", [["catalogo", "film", null], ["clientes", "users", null], ["descuentos", "tag", null]]],
    ["Registros", [["historial", "history", null], ["restock", "truck", D.restockPending]]],
  ];
  return (
    <aside className="side">
      <div className="side-brand">
        <div className="side-mark"><Icon name="refresh" /></div>
        <div><div className="side-name">REBOBINA</div><div className="side-sub">Renta & Venta</div></div>
      </div>
      <nav className="side-nav scroll">
        {groups.map(([label, items]) => (
          <div key={label}>
            <div className="side-sec">{label}</div>
            {items.map(([id, icon, n]) => (
              <button key={id} className={"side-item" + (view === id ? " on" : "")} onClick={() => go(id)}>
                <Icon name={icon} /><span>{PAGES[id][0]}</span>
                {n > 0 && <span className={"n" + (id === "alertas" ? " alert" : "")}>{n}</span>}
              </button>
            ))}
          </div>
        ))}
      </nav>
      <div className="side-foot"><div className="av">A</div><div><div className="who">Alan D.</div><div className="role">Dueño · Mostrador</div></div></div>
    </aside>
  );
}

/* ============================ RESUMEN (limpio) ============================ */
function CleanResumen({ go, onOpen, dash }) {
  const D = window.STORE_DATA; const d = D.derived;
  const alerts = cleanAlerts();
  const feed = (
    <div className="feed">
      <div className="block-h" style={{ marginBottom: 4 }}><h2 style={{ fontSize: 16 }}>Actividad del bot</h2><span className="wa more"><WaIcon /> en vivo</span></div>
      {D.activity.slice(0, 7).map((a) => {
        const col = { alerta: "var(--red)", venta: "var(--green)", pedido: "var(--accent)", cliente: "var(--blue)", consulta: "var(--ink-3)" }[a.kind] || "var(--ink-3)";
        return <div key={a.id} className="fi"><div className="fd" style={{ background: col }} /><div><div className="ft">{a.text}</div><div className="fm">hace {a.minsAgo < 60 ? a.minsAgo + " min" : Math.round(a.minsAgo / 60) + " h"}</div></div></div>;
      })}
    </div>
  );
  const priorityList = (
    <div>
      <div className="block-h" style={{ marginBottom: 4 }}><h2 style={{ fontSize: 16 }}>Pedidos por validar</h2><span className="c">{D.pendingOrders.length}</span><button className="btn sm ghost more" onClick={() => go("validar")}>Ver todos</button></div>
      <div className="list">
        {D.pendingOrders.slice(0, 4).map((p) => (
          <div key={p.id} className="li" onClick={() => onOpen("pedido", p)}>
            <span className={"li-dot " + (p.needs_attention ? "red" : "amber")} />
            <div className="li-main"><div className="li-t">{p.customer_name}</div><div className="li-s">{p.type === "renta" ? "Renta" : "Compra"} · {p.items.length} título{p.items.length > 1 ? "s" : ""}{p.needs_attention ? " · revisar stock" : p.discount_pct > 0 ? ` · −${p.discount_pct}%` : ""}</div></div>
            <div className="li-side"><div className="li-amt">{fmtMoney(p.total)}</div></div>
            <span className="li-go"><Icon name="chevron" /></span>
          </div>
        ))}
      </div>
      <div className="block-h" style={{ marginTop: 30, marginBottom: 4 }}><h2 style={{ fontSize: 16 }}>Necesita atención</h2><span className="c">{alerts.length}</span><button className="btn sm ghost more" onClick={() => go("alertas")}>Ver todas</button></div>
      <div className="list">
        {alerts.slice(0, 5).map((a) => (
          <div key={a.id} className="li" onClick={() => onOpen("alerta", a)}>
            <span className={"li-dot " + a.sev} />
            <div className="li-main"><div className="li-t">{a.title}</div><div className="li-s">{a.meta}</div></div>
            <span className={"tag " + (a.sev === "red" ? "red" : a.sev === "amber" ? "amber" : "blue")}>{a.cat}</span>
            <span className="li-go"><Icon name="chevron" /></span>
          </div>
        ))}
      </div>
    </div>
  );
  return (
    <div className="cfade maxw">
      <div className="metrics">
        <div className="metric"><div className="k">Ingresos hoy</div><div className="v">{fmtMoney(d.revenueToday)}</div><div className="d">{d.ordersToday} operaciones</div></div>
        <div className="metric"><div className="k">Por validar</div><div className="v">{d.pendingCount}</div><div className="d">{d.attentionCount} requieren atención</div></div>
        <div className="metric flag"><div className="k">Alertas</div><div className="v">{alerts.length}</div><div className="d">{d.outOfStock.length} agotados · {d.overdue.length} vencidas</div></div>
        <div className="metric"><div className="k">Frecuentes</div><div className="v">{d.frequentCount}<small> /{D.customers.length}</small></div><div className="d">clientes</div></div>
      </div>
      <div className="dash2">{dash === "actividad" ? <React.Fragment>{feed}{priorityList}</React.Fragment> : <React.Fragment>{priorityList}{feed}</React.Fragment>}</div>
    </div>
  );
}

/* ============================ POR VALIDAR (limpio) ============================ */
function CleanValidar({ query, onOpen, sel, resolved, resolve }) {
  const D = window.STORE_DATA;
  const [f, setF] = useC("todos");
  let list = D.pendingOrders.filter((p) => !resolved[p.id]);
  if (f === "atencion") list = list.filter((p) => p.needs_attention);
  if (f === "limpios") list = list.filter((p) => !p.needs_attention);
  if (query) { const q = query.toLowerCase(); list = list.filter((p) => p.customer_name.toLowerCase().includes(q) || p.items.some((it) => it.title.toLowerCase().includes(q)) || String(p.id).includes(q)); }
  const nResolved = Object.keys(resolved).length;
  return (
    <div className="cfade maxw">
      <div className="block-h" style={{ marginTop: 26 }}>
        <div className="seg">{[["todos", "Todos"], ["atencion", "Requieren atención"], ["limpios", "Listos"]].map(([k, l]) => <button key={k} className={f === k ? "on" : ""} onClick={() => setF(k)}>{l}</button>)}</div>
        <span className="wa more"><WaIcon /> llegan del bot{nResolved > 0 ? ` · ${nResolved} resueltos` : ""}</span>
      </div>
      <div className="list" style={{ borderTop: "1px solid var(--line)", marginTop: 14 }}>
        {list.map((p) => (
          <div key={p.id} className={"li" + (sel === "pedido-" + p.id ? " sel" : "")} onClick={() => onOpen("pedido", p)}>
            <span className={"li-dot " + (p.needs_attention ? "red" : "amber")} />
            <div className="li-main">
              <div className="li-t">{p.customer_name} <span className="dim num" style={{ fontWeight: 400, fontSize: 12 }}>#{p.id}</span></div>
              <div className="li-s">{p.type === "renta" ? "Renta" : "Compra"} · {p.items.map((i) => i.title).join(", ")}</div>
            </div>
            {p.needs_attention && <span className="tag red"><Icon name="alert" /> stock</span>}
            {p.discount_pct > 0 && <span className="tag amber">−{p.discount_pct}%</span>}
            <div className="li-side"><div className="li-amt">{fmtMoney(p.total)}</div><div className="dim" style={{ fontSize: 11 }}>{timeAgo(p.created_at)}</div></div>
            <span className="li-go"><Icon name="chevron" /></span>
          </div>
        ))}
      </div>
      {list.length === 0 && <div className="empty"><Icon name="check" /><div>Bandeja al día.</div></div>}
    </div>
  );
}

/* ============================ ALERTAS (limpio) ============================ */
function CleanAlertas({ query, onOpen, done, setDone }) {
  const [cat, setCat] = useC("todas");
  let alerts = cleanAlerts();
  const cats = [["todas", "Todas"], ["Agotado", "Agotados"], ["Stock bajo", "Stock bajo"], ["Renta vencida", "Vencidas"], ["Solicitado", "Solicitados"]];
  if (cat !== "todas") alerts = alerts.filter((a) => a.cat === cat);
  if (query) { const q = query.toLowerCase(); alerts = alerts.filter((a) => a.title.toLowerCase().includes(q) || a.meta.toLowerCase().includes(q)); }
  const vis = alerts.filter((a) => !done[a.id]);
  const all = cleanAlerts();
  return (
    <div className="cfade maxw">
      <div className="metrics">
        <div className="metric flag"><div className="k">Urgentes</div><div className="v">{all.filter((a) => a.sev === "red").length}</div><div className="d">agotados y vencidas</div></div>
        <div className="metric"><div className="k">Por vigilar</div><div className="v">{all.filter((a) => a.sev === "amber").length}</div><div className="d">stock bajo</div></div>
        <div className="metric"><div className="k">Oportunidades</div><div className="v">{all.filter((a) => a.sev === "blue").length}</div><div className="d">títulos pedidos</div></div>
      </div>
      <div className="block">
        <div className="block-h"><div className="seg">{cats.map(([k, l]) => <button key={k} className={cat === k ? "on" : ""} onClick={() => setCat(k)}>{l}</button>)}</div><span className="c more">{vis.length} pendientes</span></div>
        <div className="list" style={{ borderTop: "1px solid var(--line)" }}>
          {vis.map((a) => (
            <div key={a.id} className="li" onClick={() => onOpen("alerta", a)}>
              <span className={"li-dot " + a.sev} />
              <div className="li-main"><div className="li-t">{a.title}</div><div className="li-s">{a.meta}</div></div>
              <span className={"tag " + (a.sev === "red" ? "red" : a.sev === "amber" ? "amber" : "blue")}>{a.cat}</span>
              <button className="btn sm ghost" title="Atender" onClick={(e) => { e.stopPropagation(); setDone((m) => ({ ...m, [a.id]: 1 })); }}><Icon name="check" /></button>
            </div>
          ))}
          {vis.length === 0 && <div className="empty"><Icon name="check" /><div>Todo bajo control.</div></div>}
        </div>
      </div>
    </div>
  );
}

/* ============================ DRAWER (detalle) ============================ */
function Drawer({ detail, onClose, resolve, setDone, resolved }) {
  const open = !!detail;
  return (
    <React.Fragment>
      <div className={"scrim" + (open ? " open" : "")} onClick={onClose} />
      <div className={"drawer" + (open ? " open" : "")}>
        <button className="drawer-close" onClick={onClose}><Icon name="x" /></button>
        {detail && <DrawerContent detail={detail} onClose={onClose} resolve={resolve} setDone={setDone} resolved={resolved} />}
      </div>
    </React.Fragment>
  );
}

function DrawerContent({ detail, onClose, resolve, setDone, resolved }) {
  const D = window.STORE_DATA;
  const { type, data } = detail;

  if (type === "pedido") {
    const p = data; const isDone = resolved[p.id];
    return (
      <React.Fragment>
        <div className="drawer-h">
          <div className="wa" style={{ marginBottom: 8 }}><WaIcon /> {p.channel === "whatsapp" ? "WhatsApp" : "Mostrador"} · #{p.id}</div>
          <div className="h1" style={{ fontSize: 26 }}>{p.customer_name}</div>
          <div className="muted" style={{ fontSize: 13, marginTop: 6 }}>{p.type === "renta" ? "Renta" : "Compra"} · {p.phone} · {timeAgo(p.created_at)}</div>
        </div>
        <div className="drawer-body scroll">
          <div className="section-label">Líneas del pedido</div>
          {p.items.map((it, i) => (
            <div key={i} className="dline">
              <CleanPf title={it.title} />
              <div style={{ flex: 1 }}><div style={{ fontWeight: 600 }}>{it.title} <span className="tag line">{it.format}</span></div><div className="dim" style={{ fontSize: 12 }}>{it.quantity} × {fmtMoney(it.unit_price)} · {it.action}</div></div>
              {it.available ? <span className="tag green"><Icon name="check" /> {it.stock} stock</span> : <span className="tag red"><Icon name="alert" /> sin stock</span>}
            </div>
          ))}
          {p.reasoning.length > 0 && <React.Fragment>
            <div className="section-label">Razonamiento del sistema</div>
            <div className="reasonbox">
              {p.reasoning.map((r, i) => <div key={i} className="rr"><span className="rt">{r.rule}{r.delta ? ` +${r.delta}%` : ""}</span><span>{r.text}</span></div>)}
            </div>
          </React.Fragment>}
          <div className="section-label">Totales</div>
          <div className="kv"><span className="k">Subtotal</span><span className="v num">{fmtMoney(p.subtotal)}</span></div>
          {p.discount_pct > 0 && <div className="kv"><span className="k">Descuento ({p.discount_pct}%)</span><span className="v num" style={{ color: "var(--accent)" }}>−{fmtMoney(p.discount_amount)}</span></div>}
          <div className="kv" style={{ borderBottom: 0 }}><span className="k" style={{ fontWeight: 600, color: "var(--ink)" }}>Total</span><span className="v num" style={{ fontSize: 20, fontFamily: "var(--font-display)" }}>{fmtMoney(p.total)}</span></div>
        </div>
        {!isDone ? (
          <div className="drawer-foot">
            <button className="btn pri" style={{ flex: 1 }} onClick={() => { resolve(p.id, "aprobado"); onClose(); }}><Icon name="check" /> Validar y registrar</button>
            <button className="btn" onClick={() => { resolve(p.id, "rechazado"); onClose(); }}><Icon name="x" /> Rechazar</button>
          </div>
        ) : <div className="drawer-foot"><span className={"tag " + (resolved[p.id] === "aprobado" ? "green" : "red")} style={{ padding: "8px 12px" }}>{resolved[p.id] === "aprobado" ? "Validado" : "Rechazado"}</span></div>}
      </React.Fragment>
    );
  }

  if (type === "pelicula") {
    const m = data;
    const ordersOf = D.orders.filter((o) => o.items.some((it) => it.title === m.title)).length;
    return (
      <React.Fragment>
        <div className="drawer-h" style={{ display: "flex", gap: 16, alignItems: "center" }}>
          <div className="pf" style={{ width: 60, height: 84, fontSize: 26, background: posterColor(m.title) }}>{m.title.replace(/^(El|La|Los|Las)\s/i, "").charAt(0)}</div>
          <div><div className="h1" style={{ fontSize: 24 }}>{m.title}</div><div className="muted" style={{ fontSize: 13, marginTop: 6 }}>{m.genre} · {m.year} · {m.format}</div></div>
        </div>
        <div className="drawer-body scroll">
          <div className="section-label">Inventario</div>
          <div className="dline" style={{ paddingTop: 0 }}><div style={{ flex: 1 }}><CleanBar value={m.stock} max={10} /></div><span className="num" style={{ fontWeight: 600, color: m.stock === 0 ? "var(--red)" : "var(--ink)" }}>{m.stock} en stock</span></div>
          <div className="kv"><span className="k">Precio de venta</span><span className="v num">{fmtMoney(m.price_buy)}</span></div>
          <div className="kv"><span className="k">Precio de renta</span><span className="v num">{fmtMoney(m.price_rent)}</span></div>
          <div className="kv"><span className="k">Calificación</span><span className="v num" style={{ color: "var(--accent)" }}>★ {m.rating.toFixed(1)}</span></div>
          <div className="kv"><span className="k">Demanda</span><span className="v" style={{ textTransform: "capitalize" }}>{m.demand}</span></div>
          <div className="kv"><span className="k">Operaciones registradas</span><span className="v num">{ordersOf}</span></div>
          {m.stock === 0 && <div className="reasonbox" style={{ marginTop: 18, borderColor: "var(--red)", background: "var(--red-soft)" }}><div className="rr" style={{ color: "var(--red)" }}><Icon name="alert" style={{ width: 15, height: 15 }} /> Título agotado — sin existencias para renta ni venta.</div></div>}
        </div>
        <div className="drawer-foot"><button className="btn pri" style={{ flex: 1 }}><Icon name="truck" /> Sugerir reabastecimiento</button></div>
      </React.Fragment>
    );
  }

  if (type === "cliente") {
    const c = data;
    const his = D.orders.filter((o) => o.customer_id === c.id);
    return (
      <React.Fragment>
        <div className="drawer-h" style={{ display: "flex", gap: 14, alignItems: "center" }}>
          <div className={"av-sm" + (c.is_frequent ? " hot" : "")} style={{ width: 52, height: 52, fontSize: 20 }}>{c.name.charAt(0)}</div>
          <div><div className="h1" style={{ fontSize: 24 }}>{c.name}</div><div className="wa" style={{ marginTop: 6 }}><WaIcon /> {c.phone}</div></div>
        </div>
        <div className="drawer-body scroll">
          <div className="section-label">Perfil</div>
          <div className="kv"><span className="k">Estatus</span><span className="v">{c.is_frequent ? "Frecuente (−10%)" : "Regular"}</span></div>
          <div className="kv"><span className="k">Rentas acumuladas</span><span className="v num">{c.rentals_count}</span></div>
          <div className="kv"><span className="k">Gasto histórico</span><span className="v num">{fmtMoney(c.total_spend)}</span></div>
          <div className="kv"><span className="k">Cliente desde</span><span className="v num">{fmtDate(c.created_at)}</span></div>
          <div className="section-label">Operaciones recientes</div>
          {his.length === 0 ? <div className="dim" style={{ fontSize: 13 }}>Sin operaciones registradas.</div> :
            his.slice(0, 6).map((o) => <div key={o.id} className="dline"><span className={"li-dot " + (o.type === "renta" ? "blue" : "amber")} /><div style={{ flex: 1 }}><div style={{ fontWeight: 600, fontSize: 13.5 }}>#{o.id} · {o.type === "renta" ? "Renta" : "Compra"}</div><div className="dim" style={{ fontSize: 12 }}>{o.items.map((i) => i.title).join(", ")}</div></div><span className="num" style={{ fontWeight: 600 }}>{fmtMoney(o.total)}</span></div>)}
        </div>
      </React.Fragment>
    );
  }

  if (type === "operacion") {
    const o = data;
    return (
      <React.Fragment>
        <div className="drawer-h">
          <div className="muted num" style={{ fontSize: 12, marginBottom: 6 }}>OPERACIÓN #{o.id}</div>
          <div className="h1" style={{ fontSize: 24 }}>{o.customer_name}</div>
          <div className="muted" style={{ fontSize: 13, marginTop: 6, display: "flex", gap: 8, alignItems: "center" }}><span className={"tag " + (o.type === "renta" ? "blue" : "amber")}>{o.type === "renta" ? "Renta" : "Compra"}</span><Channel channel={o.channel} /> · {timeAgo(o.created_at)}</div>
        </div>
        <div className="drawer-body scroll">
          <div className="section-label">Títulos</div>
          {o.items.map((it, i) => <div key={i} className="dline"><CleanPf title={it.title} /><div style={{ flex: 1 }}><div style={{ fontWeight: 600 }}>{it.title}</div><div className="dim" style={{ fontSize: 12 }}>{it.quantity} × {fmtMoney(it.unit_price)}</div></div><span className="num" style={{ fontWeight: 600 }}>{fmtMoney(it.line_total)}</span></div>)}
          <div className="section-label">Totales</div>
          <div className="kv"><span className="k">Subtotal</span><span className="v num">{fmtMoney(o.subtotal)}</span></div>
          {o.discount_pct > 0 && <div className="kv"><span className="k">Descuento ({o.discount_pct}%)</span><span className="v num" style={{ color: "var(--accent)" }}>−{fmtMoney(o.discount_amount)}</span></div>}
          <div className="kv" style={{ borderBottom: 0 }}><span className="k" style={{ fontWeight: 600, color: "var(--ink)" }}>Total</span><span className="v num" style={{ fontSize: 20, fontFamily: "var(--font-display)" }}>{fmtMoney(o.total)}</span></div>
        </div>
      </React.Fragment>
    );
  }

  if (type === "restock") {
    const r = data; const isDone = (window.__restockDone && window.__restockDone[r.id]) || r.status === "atendida";
    return (
      <React.Fragment>
        <div className="drawer-h" style={{ display: "flex", gap: 14, alignItems: "center" }}>
          <CleanPf title={r.title} />
          <div><div className="h1" style={{ fontSize: 22 }}>{r.title}</div><div className="muted" style={{ fontSize: 13, marginTop: 6 }}>{r.movie_id ? `En catálogo · ${r.format}` : `Título nuevo · ${r.genre || "—"}`}</div></div>
        </div>
        <div className="drawer-body scroll">
          <div className="kv"><span className="k">Motivo</span><span className="v">{r.type === "agotado" ? "Agotado" : r.type === "stock_bajo" ? "Stock bajo" : "Pedido por clientes"}</span></div>
          <div className="kv"><span className="k">Solicitudes</span><span className="v num">{r.requests}</span></div>
          <div className="kv"><span className="k">Cantidad sugerida</span><span className="v num">+{r.suggested_qty}</span></div>
          <div className="kv"><span className="k">Detectado</span><span className="v num">{timeAgo(r.created_at)}</span></div>
          <div className="reasonbox" style={{ marginTop: 18 }}><div className="rr"><Icon name="sparkle" style={{ width: 14, height: 14, color: "var(--accent)" }} /><span>{r.movie_id ? "El sistema detectó este faltante durante pedidos por WhatsApp y sugiere reponerlo." : "Varios clientes han pedido este título; aún no forma parte del catálogo."}</span></div></div>
        </div>
        <div className="drawer-foot">{isDone ? <span className="tag green" style={{ padding: "8px 12px" }}><Icon name="check" /> Pedido hecho</span> : <button className="btn pri" style={{ flex: 1 }} onClick={() => { setDone((m) => ({ ...m, [r.id]: 1 })); onClose(); }}><Icon name="check" /> Marcar como pedido</button>}</div>
      </React.Fragment>
    );
  }

  if (type === "alerta") {
    const a = data;
    return (
      <React.Fragment>
        <div className="drawer-h"><span className={"tag " + (a.sev === "red" ? "red" : a.sev === "amber" ? "amber" : "blue")} style={{ marginBottom: 10 }}>{a.cat}</span><div className="h1" style={{ fontSize: 23 }}>{a.title}</div><div className="muted" style={{ fontSize: 13, marginTop: 6 }}>{a.meta}</div></div>
        <div className="drawer-body scroll"><div className="reasonbox"><div className="rr"><Icon name={a.icon} style={{ width: 15, height: 15, color: a.sev === "red" ? "var(--red)" : "var(--accent)" }} /><span>{a.cat === "Agotado" ? "Reponer cuanto antes para no perder ventas ni rentas." : a.cat === "Renta vencida" ? "Contactar al cliente para gestionar la devolución." : a.cat === "Stock bajo" ? "Quedan pocas copias; evalúa reabastecer según la demanda." : "Considera traer este título: varios clientes lo han pedido."}</span></div></div></div>
        <div className="drawer-foot"><button className="btn pri" style={{ flex: 1 }} onClick={() => { setDone((m) => ({ ...m, [a.id]: 1 })); onClose(); }}><Icon name="check" /> Marcar atendida</button></div>
      </React.Fragment>
    );
  }
  return null;
}

/* ============================ APP ============================ */
function CleanRoot() {
  const [t, setTweak] = useTweaks(CLEAN_DEFAULTS);
  const [view, setView] = useC("resumen");
  const [query, setQuery] = useC("");
  const [detail, setDetail] = useC(null);
  const [resolved, setResolved] = useC({});
  const [restockDone, setRestockDone] = useC({});
  const [alertDone, setAlertDone] = useC({});

  useCE(() => { window.__restockDone = restockDone; }, [restockDone]);
  useCE(() => {
    const el = document.documentElement;
    el.setAttribute("data-theme", t.theme);
    el.style.setProperty("--accent", t.accent);
  }, [t.theme, t.accent]);
  useCE(() => { setQuery(""); setDetail(null); }, [view]);
  useCE(() => {
    const onKey = (e) => { if (e.key === "Escape") setDetail(null); };
    window.addEventListener("keydown", onKey); return () => window.removeEventListener("keydown", onKey);
  }, []);

  const onOpen = (type, data) => setDetail({ type, data });
  const resolve = (id, s) => {
    setResolved((m) => ({ ...m, [id]: s }));
    // Persiste la decisión en la base de datos real (validar/rechazar el pedido).
    fetch("/panel/api/validate", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ order_id: id, action: s }),
    }).catch(() => {});
  };
  const sel = detail ? detail.type + "-" + (detail.data.id) : null;
  const [title, sub] = PAGES[view];

  function body() {
    switch (view) {
      case "resumen": return <CleanResumen go={setView} onOpen={onOpen} dash={t.dash === "actividad" ? "actividad" : "prioridad"} />;
      case "validar": return <CleanValidar query={query} onOpen={onOpen} sel={sel} resolved={resolved} resolve={resolve} />;
      case "alertas": return <CleanAlertas query={query} onOpen={onOpen} done={alertDone} setDone={setAlertDone} />;
      case "catalogo": return <CleanCatalogo query={query} onOpen={onOpen} sel={sel} />;
      case "clientes": return <CleanClientes query={query} onOpen={onOpen} sel={sel} />;
      case "descuentos": return <CleanDescuentos />;
      case "historial": return <CleanHistorial query={query} onOpen={onOpen} sel={sel} />;
      case "restock": return <CleanRestock query={query} onOpen={onOpen} sel={sel} done={restockDone} setDone={setRestockDone} />;
      default: return null;
    }
  }

  return (
    <div className="app">
      <CleanSide view={view} go={setView} />
      <div className="main">
        <div className="top">
          <div className="h1">{title}</div>
          <div className="h1-sub">{sub}</div>
          <label className="search"><Icon name="search" /><input value={query} placeholder="Buscar…" onChange={(e) => setQuery(e.target.value)} /></label>
        </div>
        <div className="wrap scroll" key={view}>{body()}</div>
      </div>
      <Drawer detail={detail} onClose={() => setDetail(null)} resolve={resolve} setDone={detail && detail.type === "alerta" ? setAlertDone : setRestockDone} resolved={resolved} />

      <TweaksPanel title="Tweaks">
        <TweakSection label="Tema" />
        <TweakRadio label="Ambiente" value={t.theme} options={[{ value: "lobby", label: "Claro" }, { value: "sala", label: "Oscuro" }]} onChange={(v) => setTweak("theme", v)} />
        <TweakColor label="Acento" value={t.accent} options={["#b9802b", "#c0392b", "#34648f", "#2c8559"]} onChange={(v) => setTweak("accent", v)} />
        <TweakSection label="Resumen" />
        <TweakRadio label="Orden" value={t.dash} options={[{ value: "prioridad", label: "Pendientes" }, { value: "actividad", label: "Actividad" }]} onChange={(v) => setTweak("dash", v)} />
      </TweaksPanel>
    </div>
  );
}

const __rootEl = document.getElementById("root");
if (__rootEl && !window.__PRINT_MODE) ReactDOM.createRoot(__rootEl).render(<CleanRoot />);
Object.assign(window, { CleanResumen, CleanValidar, CleanAlertas, cleanAlerts, CLEAN_PAGES: PAGES });
