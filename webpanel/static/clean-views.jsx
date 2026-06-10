/* global React, Icon, fmtMoney, fmtDate, timeAgo, Channel, WaIcon, posterColor */
// REBOBINA Limpio — Vistas de lista (maestro). El detalle vive en el Drawer.
const { useState: useS } = React;

function Bar({ value, max }) {
  const pct = Math.min(100, (value / max) * 100);
  const cls = value === 0 || value <= 2 ? "crit" : value <= 4 ? "low" : "";
  return <div className={"bar " + cls}><i style={{ width: Math.max(5, pct) + "%" }} /></div>;
}
function Pf({ title }) {
  return <div className="pf" style={{ background: posterColor(title) }}>{title.replace(/^(El|La|Los|Las)\s/i, "").charAt(0)}</div>;
}

/* ----------------------------- CATÁLOGO ----------------------------- */
function CleanCatalogo({ query, onOpen, sel }) {
  const D = window.STORE_DATA;
  const [f, setF] = useS("todos");
  let list = D.movies.slice().sort((a, b) => a.title.localeCompare(b.title));
  if (f === "agotado") list = list.filter((m) => m.stock === 0);
  if (f === "bajo") list = list.filter((m) => m.stock > 0 && m.stock <= 2);
  if (f === "ok") list = list.filter((m) => m.stock > 2);
  if (query) { const q = query.toLowerCase(); list = list.filter((m) => m.title.toLowerCase().includes(q) || m.genre.toLowerCase().includes(q)); }
  return (
    <div className="cfade maxw">
      <div className="metrics">
        <div className="metric"><div className="k">Títulos</div><div className="v">{D.movies.length}</div><div className="d">{D.derived.totalStock} discos</div></div>
        <div className="metric flag"><div className="k">Agotados</div><div className="v">{D.derived.outOfStock.length}</div><div className="d">sin existencias</div></div>
        <div className="metric"><div className="k">Stock bajo</div><div className="v">{D.derived.lowStock.length}</div><div className="d">2 o menos</div></div>
        <div className="metric"><div className="k">Valor inventario</div><div className="v">{fmtMoney(D.derived.catalogValue)}</div><div className="d">a precio de venta</div></div>
      </div>
      <div className="block">
        <div className="block-h">
          <h2>Catálogo</h2><span className="c">{list.length}</span>
          <div className="seg block-h-seg more">
            {[["todos", "Todo"], ["ok", "Disponible"], ["bajo", "Bajo"], ["agotado", "Agotado"]].map(([k, l]) =>
              <button key={k} className={f === k ? "on" : ""} onClick={() => setF(k)}>{l}</button>)}
          </div>
        </div>
        <table className="tbl">
          <thead><tr><th>Película</th><th>Género</th><th>Formato</th><th className="c">★</th><th className="r">Venta</th><th className="r">Renta</th><th style={{ width: 130 }}>Stock</th></tr></thead>
          <tbody>
            {list.map((m) => (
              <tr key={m.id} className={sel === "pelicula-" + m.id ? "sel" : ""} onClick={() => onOpen("pelicula", m)}>
                <td><div style={{ display: "flex", alignItems: "center", gap: 11 }}><Pf title={m.title} /><div><div style={{ fontWeight: 600 }}>{m.title}</div><div className="dim" style={{ fontSize: 12 }}>{m.year}</div></div></div></td>
                <td className="muted">{m.genre}</td>
                <td><span className="tag line">{m.format}</span></td>
                <td className="c num" style={{ color: "var(--accent)" }}>{m.rating.toFixed(1)}</td>
                <td className="r num" style={{ fontWeight: 600 }}>{fmtMoney(m.price_buy)}</td>
                <td className="r num muted">{fmtMoney(m.price_rent)}</td>
                <td><div style={{ display: "flex", alignItems: "center", gap: 9 }}><div style={{ flex: 1 }}><Bar value={m.stock} max={10} /></div><span className="num" style={{ width: 18, textAlign: "right", color: m.stock === 0 ? "var(--red)" : m.stock <= 2 ? "var(--accent)" : "var(--ink)", fontWeight: 600 }}>{m.stock}</span></div></td>
              </tr>
            ))}
          </tbody>
        </table>
        {list.length === 0 && <div className="empty"><Icon name="search" /><div>Sin resultados.</div></div>}
      </div>
    </div>
  );
}

/* ----------------------------- CLIENTES ----------------------------- */
function CleanClientes({ query, onOpen, sel }) {
  const D = window.STORE_DATA;
  const [tab, setTab] = useS("todos");
  let list = D.customers.slice().sort((a, b) => b.total_spend - a.total_spend);
  if (tab === "frecuentes") list = list.filter((c) => c.is_frequent);
  if (query) { const q = query.toLowerCase(); list = list.filter((c) => c.name.toLowerCase().includes(q) || c.phone.includes(q)); }
  return (
    <div className="cfade maxw">
      <div className="metrics">
        <div className="metric"><div className="k">Registrados</div><div className="v">{D.customers.length}</div></div>
        <div className="metric"><div className="k">Frecuentes</div><div className="v">{D.derived.frequentCount}</div><div className="d">−10% automático</div></div>
        <div className="metric"><div className="k">Rentas acumuladas</div><div className="v">{D.customers.reduce((s, c) => s + c.rentals_count, 0)}</div></div>
      </div>
      <div className="block">
        <div className="block-h"><h2>Clientes</h2><span className="c">{list.length}</span>
          <div className="seg more">{[["todos", "Todos"], ["frecuentes", "Frecuentes"]].map(([k, l]) => <button key={k} className={tab === k ? "on" : ""} onClick={() => setTab(k)}>{l}</button>)}</div>
        </div>
        <div className="list" style={{ borderTop: "1px solid var(--line)" }}>
          {list.map((c) => (
            <div key={c.id} className={"li" + (sel === "cliente-" + c.id ? " sel" : "")} onClick={() => onOpen("cliente", c)}>
              <div className={"av-sm" + (c.is_frequent ? " hot" : "")}>{c.name.charAt(0)}</div>
              <div className="li-main">
                <div className="li-t">{c.name}{c.is_frequent && <span className="tag amber"><Icon name="star" /> Frecuente</span>}</div>
                <div className="li-s">{c.phone} · {c.rentals_count} rentas</div>
              </div>
              <div className="li-side"><div className="li-amt">{fmtMoney(c.total_spend)}</div><div className="dim" style={{ fontSize: 11 }}>histórico</div></div>
              <span className="li-go"><Icon name="chevron" /></span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ----------------------------- DESCUENTOS ----------------------------- */
function CleanDescuentos() {
  const D = window.STORE_DATA;
  return (
    <div className="cfade maxw" style={{ maxWidth: 760 }}>
      <div className="block" style={{ marginTop: 26 }}>
        <div className="dline" style={{ borderBottom: "1px solid var(--line)", paddingBottom: 18 }}>
          <div style={{ flex: 1 }}>
            <div style={{ fontFamily: "var(--font-display)", fontSize: 19, fontWeight: 500 }}>Política comercial automática</div>
            <div className="muted" style={{ fontSize: 13.5, marginTop: 3 }}>El sistema aplica estas reglas al armar cada pedido. Acumulables, con tope del 25%.</div>
          </div>
          <div style={{ textAlign: "center" }}><div style={{ fontFamily: "var(--font-display)", fontSize: 30, fontWeight: 500, color: "var(--accent)", lineHeight: 1 }}>25%</div><div className="dim" style={{ fontSize: 10, letterSpacing: ".1em", textTransform: "uppercase" }}>tope</div></div>
        </div>
        <div className="list" style={{ border: 0 }}>
          {D.discountRules.map((r) => (
            <div key={r.id} className="dline">
              <div style={{ width: 56, textAlign: "left" }}>{r.pct > 0 ? <span style={{ fontFamily: "var(--font-display)", fontSize: 22, fontWeight: 500, color: "var(--accent)" }}>+{r.pct}%</span> : <span className="tag blue">aviso</span>}</div>
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 600, fontSize: 14.5 }}>{r.name}</div>
                <div className="muted" style={{ fontSize: 12.5, marginTop: 2 }}>{r.criteria} <span className="dim">· {r.applies}</span></div>
              </div>
              <code className="num dim" style={{ fontSize: 11.5 }}>{r.cond}</code>
            </div>
          ))}
        </div>
        <div className="reasonbox" style={{ marginTop: 22 }}>
          <div className="muted" style={{ fontSize: 13.5, lineHeight: 1.7 }}>
            <b style={{ color: "var(--ink)" }}>Ejemplo.</b> Cliente frecuente compra 5 títulos por $637:
            <span className="tag amber" style={{ margin: "0 4px" }}>frecuente +10%</span>
            <span className="tag amber" style={{ margin: "0 4px" }}>volumen +8%</span>
            <span className="tag amber" style={{ margin: "0 4px" }}>monto +10%</span>
            = 28% → tope <b style={{ color: "var(--accent)" }}>25%</b> → total <b className="num" style={{ color: "var(--ink)" }}>$478</b>.
          </div>
        </div>
      </div>
    </div>
  );
}

/* ----------------------------- HISTORIAL ----------------------------- */
function CleanHistorial({ query, onOpen, sel }) {
  const D = window.STORE_DATA;
  const [type, setType] = useS("todos");
  let list = D.orders.slice();
  if (type !== "todos") list = list.filter((o) => o.type === type);
  if (query) { const q = query.toLowerCase(); list = list.filter((o) => o.customer_name.toLowerCase().includes(q) || String(o.id).includes(q) || o.items.some((it) => it.title.toLowerCase().includes(q))); }
  return (
    <div className="cfade maxw">
      <div className="metrics">
        <div className="metric"><div className="k">Operaciones</div><div className="v">{D.orders.length}</div></div>
        <div className="metric"><div className="k">Rentas</div><div className="v">{D.orders.filter((o) => o.type === "renta").length}</div></div>
        <div className="metric"><div className="k">Compras</div><div className="v">{D.orders.filter((o) => o.type === "compra").length}</div></div>
        <div className="metric"><div className="k">Facturado</div><div className="v">{fmtMoney(D.orders.reduce((s, o) => s + o.total, 0))}</div></div>
      </div>
      <div className="block">
        <div className="block-h"><h2>Historial</h2><span className="c">{list.length}</span>
          <div className="seg more">{[["todos", "Todas"], ["renta", "Rentas"], ["compra", "Compras"]].map(([k, l]) => <button key={k} className={type === k ? "on" : ""} onClick={() => setType(k)}>{l}</button>)}</div>
        </div>
        <table className="tbl">
          <thead><tr><th>Pedido</th><th>Cliente</th><th>Tipo</th><th>Canal</th><th className="r">Total</th><th className="r">Cuándo</th></tr></thead>
          <tbody>
            {list.map((o) => (
              <tr key={o.id} className={sel === "operacion-" + o.id ? "sel" : ""} onClick={() => onOpen("operacion", o)}>
                <td className="num" style={{ fontWeight: 600 }}>#{o.id}</td>
                <td>{o.customer_name}</td>
                <td><span className={"tag " + (o.type === "renta" ? "blue" : "amber")}>{o.type === "renta" ? "Renta" : "Compra"}</span></td>
                <td>{o.channel === "whatsapp" ? <span className="wa"><WaIcon /> WhatsApp</span> : <span className="dim" style={{ fontSize: 12 }}>Mostrador</span>}</td>
                <td className="r num" style={{ fontWeight: 600 }}>{fmtMoney(o.total)}</td>
                <td className="r num dim">{timeAgo(o.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* ----------------------------- REABASTECIMIENTO ----------------------------- */
function CleanRestock({ query, onOpen, sel, done, setDone }) {
  const D = window.STORE_DATA;
  const [tab, setTab] = useS("pendiente");
  let list = D.restock.slice();
  if (tab !== "todas") list = list.filter((r) => (done[r.id] ? "atendida" : r.status) === tab);
  if (query) { const q = query.toLowerCase(); list = list.filter((r) => r.title.toLowerCase().includes(q)); }
  const tm = { agotado: ["red", "Agotado"], stock_bajo: ["amber", "Stock bajo"], titulo_nuevo: ["blue", "Título nuevo"] };
  return (
    <div className="cfade maxw">
      <div className="metrics">
        <div className="metric"><div className="k">Por reabastecer</div><div className="v">{D.restock.filter((r) => r.status === "pendiente").length}</div></div>
        <div className="metric flag"><div className="k">Agotados</div><div className="v">{D.restock.filter((r) => r.type === "agotado").length}</div></div>
        <div className="metric"><div className="k">Títulos solicitados</div><div className="v">{D.derived.newTitleRequests}</div><div className="d">aún no tenemos</div></div>
      </div>
      <div className="block">
        <div className="block-h"><h2>Cola de reabastecimiento</h2>
          <div className="seg more">{[["pendiente", "Pendientes"], ["atendida", "Atendidas"], ["todas", "Todas"]].map(([k, l]) => <button key={k} className={tab === k ? "on" : ""} onClick={() => setTab(k)}>{l}</button>)}</div>
        </div>
        <div className="list" style={{ borderTop: "1px solid var(--line)" }}>
          {list.map((r) => {
            const atend = done[r.id] || r.status === "atendida";
            const [col, lbl] = tm[r.type];
            return (
              <div key={r.id} className={"li" + (sel === "restock-" + r.id ? " sel" : "")} style={atend ? { opacity: .55 } : null} onClick={() => onOpen("restock", r)}>
                <Pf title={r.title} />
                <div className="li-main">
                  <div className="li-t">{r.title} <span className={"tag " + col}>{lbl}</span></div>
                  <div className="li-s">{r.requests} solicitudes · sugerido +{r.suggested_qty} · {timeAgo(r.created_at)}</div>
                </div>
                {atend ? <span className="tag green"><Icon name="check" /> Pedido hecho</span> :
                  <button className="btn sm pri" onClick={(e) => { e.stopPropagation(); setDone((m) => ({ ...m, [r.id]: 1 })); }}>Pedir</button>}
              </div>
            );
          })}
          {list.length === 0 && <div className="empty"><Icon name="check" /><div>Nada en esta cola.</div></div>}
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { CleanCatalogo, CleanClientes, CleanDescuentos, CleanHistorial, CleanRestock, CleanBar: Bar, CleanPf: Pf });
