import { useEffect, useMemo, useState } from "react";
import { ReactFlow, Background, Controls, type Node, type Edge } from "@xyflow/react";
import "@xyflow/react/dist/style.css";

const API = "http://localhost:8000";

type Materia = { id: number; nombre: string; anio: number; correlativas: number[] };
type Registro = { aprobada: boolean; nota: number | null; veces: number };
type Historial = Record<number, Registro>;
type Resultado = {
  probabilidades: Record<string, number>;
  secuencia: number[];
  aprobadas: number[];
};
type Simulacion = { id: number; tipo: "aprueba" | "desaprueba"; nota: number };

const color = (p: number) => `hsl(${Math.round(p * 120)}, 70%, 75%)`;

const pedir = (historial: Historial, n: number): Promise<Resultado> =>
  fetch(`${API}/sugerencia`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ historial, n_materias: n }),
  }).then(r => (r.ok ? r.json() : Promise.reject(r.status)));

export default function App() {
  const [plan, setPlan] = useState<Materia[]>([]);
  const [historial, setHistorial] = useState<Historial>({});
  const [seleccionada, setSeleccionada] = useState<number | null>(null);
  const [nMaterias, setNMaterias] = useState(3);
  const [res, setRes] = useState<Resultado | null>(null);
  const [resSim, setResSim] = useState<Resultado | null>(null);
  const [verCamino, setVerCamino] = useState(false);
  const [aviso, setAviso] = useState("");
  const [sim, setSim] = useState<Simulacion | null>(null);
  const [notaSim, setNotaSim] = useState(8);

  const porId = useMemo(() => new Map(plan.map(m => [m.id, m])), [plan]);

  const idsAprobadas = (h: Historial) => {
    const a: Record<number, number> = {};
    for (const [id, r] of Object.entries(h)) if (r.aprobada) a[Number(id)] = r.nota ?? 7;
    return a;
  };

  // Historial real
  const aprobadas = useMemo(() => idsAprobadas(historial), [historial]);

  // Historial simulado: copia del real + el cambio hipotético
  const historialSim = useMemo<Historial | null>(() => {
    if (!sim) return null;
    const veces = (historial[sim.id]?.veces ?? 0) + 1;
    return {
      ...historial,
      [sim.id]:
        sim.tipo === "aprueba"
          ? { aprobada: true, nota: sim.nota, veces }
          : { aprobada: false, nota: null, veces },
    };
  }, [sim, historial]);

  // Lo que se dibuja: el escenario simulado si hay simulación, si no el real
  const hVista = historialSim ?? historial;
  const aprobadasVista = useMemo(() => idsAprobadas(hVista), [hVista]);
  const vista = sim && resSim ? resSim : res;

  useEffect(() => {
    fetch(`${API}/plan`).then(r => r.json()).then(setPlan);
  }, []);

  // Pedido con el historial real
  useEffect(() => {
    let vivo = true;
    pedir(historial, nMaterias)
      .then(r => vivo && setRes(r))
      .catch(() => {});
    return () => { vivo = false; };
  }, [historial, nMaterias]);

  // Pedido con el historial simulado
  useEffect(() => {
    if (!historialSim) { setResSim(null); return; }
    let vivo = true;
    pedir(historialSim, nMaterias)
      .then(r => vivo && setResSim(r))
      .catch(() => {});
    return () => { vivo = false; };
  }, [historialSim, nMaterias]);

  const orden = useMemo(() => {
    const o: Record<number, number> = {};
    vista?.secuencia.forEach((id, i) => (o[id] = i + 1));
    return o;
  }, [vista]);

  // Guarda (o borra) el registro de una materia; si deja de estar aprobada,
  // borra también el historial de lo que dependa de ella.
  const guardar = (id: number, reg: Registro | null) => {
    setHistorial(h => {
      const n = { ...h };
      if (reg === null) delete n[id];
      else n[id] = reg;

      if (!reg?.aprobada) {
        const quitar = new Set<number>([id]);
        let cambio = true;
        while (cambio) {
          cambio = false;
          for (const x of plan) {
            if (!quitar.has(x.id) && x.correlativas.some(c => quitar.has(c))) {
              quitar.add(x.id);
              cambio = true;
            }
          }
        }
        let borradas = 0;
        quitar.forEach(q => {
          if (q !== id && q in n) { delete n[q]; borradas++; }
        });
        setAviso(borradas > 0 ? `Se quitó el historial de ${borradas} materia(s) que dependían de esta.` : "");
      } else {
        setAviso("");
      }
      return n;
    });
  };

  const abrir = (id: number) => {
    const m = porId.get(id);
    if (!m) return;
    const faltan = m.correlativas.filter(c => !(c in aprobadas));
    if (faltan.length > 0) {
      const nombres = faltan.map(c => porId.get(c)?.nombre).join(", ");
      setAviso(`No podés cargar "${m.nombre}": falta aprobar ${nombres}.`);
      return;
    }
    setAviso("");
    if (id !== seleccionada) setSim(null); // cambiar de materia descarta la simulación
    setSeleccionada(id);
  };

  const aplicarSimulacion = () => {
    if (!sim || !historialSim) return;
    guardar(sim.id, historialSim[sim.id]);
    setSim(null);
  };

  // ---- Comparación antes / después ----
  const comparacion = useMemo(() => {
    if (!sim || !res || !resSim) return null;
    const cambios = Object.keys(res.probabilidades)
      .map(Number)
      .filter(id => id !== sim.id && !(id in aprobadas) && !(id in aprobadasVista))
      .map(id => ({
        id,
        antes: res.probabilidades[id],
        despues: resSim.probabilidades[id],
        delta: resSim.probabilidades[id] - res.probabilidades[id],
      }));
    const promedio = cambios.length
      ? cambios.reduce((s, c) => s + c.delta, 0) / cambios.length
      : 0;
    const top = [...cambios].sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta)).slice(0, 8);
    return {
      promedio,
      top,
      antes: res.secuencia.filter(id => id !== sim.id),
      despues: resSim.secuencia.filter(id => id !== sim.id),
    };
  }, [sim, res, resSim, aprobadas, aprobadasVista]);

  const nodes: Node[] = useMemo(() => {
    const fila: Record<number, number> = {};
    return plan.map(m => {
      fila[m.anio] = (fila[m.anio] ?? -1) + 1;
      const p = vista?.probabilidades[m.id];
      const reg = hVista[m.id];
      const aprobada = !!reg?.aprobada;
      const enCamino = verCamino && m.id in orden;
      const apagada = verCamino && !enCamino;
      const bloqueada = !aprobada && !m.correlativas.every(c => c in aprobadasVista);
      const esSim = sim?.id === m.id;

      return {
        id: String(m.id),
        position: { x: (m.anio - 1) * 240, y: fila[m.anio] * 90 },
        data: {
          label: (
            <div>
              {enCamino && <strong style={{ color: "#1d4ed8" }}>#{orden[m.id]} </strong>}
              {bloqueada && "🔒 "}
              {esSim && "🧪 "}
              {m.id}. {m.nombre}
              {aprobada && <div>✔ Nota {reg.nota} · cursada {reg.veces}x</div>}
              {!aprobada && reg && <div>✖ Sin aprobar · cursada {reg.veces}x</div>}
              {p !== undefined && !aprobada && (
                <div style={{ opacity: 0.7 }}>{Math.round(p * 100)}% de aprobar</div>
              )}
            </div>
          ),
        },
        style: {
          background: aprobada ? "#d4d4d4" : p === undefined ? "#fff" : color(p),
          width: 210,
          fontSize: 11,
          cursor: bloqueada ? "not-allowed" : "pointer",
          border:
            esSim ? "3px solid #7c3aed"
            : seleccionada === m.id ? "3px solid #000"
            : enCamino ? "3px solid #1d4ed8"
            : bloqueada ? "1px dashed #999"
            : "1px solid #888",
          opacity: apagada ? 0.35 : 1,
        },
      };
    });
  }, [plan, vista, hVista, aprobadasVista, verCamino, orden, seleccionada, sim]);

  const edges: Edge[] = useMemo(
    () =>
      plan.flatMap(m =>
        m.correlativas.map(c => ({
          id: `${c}-${m.id}`,
          source: String(c),
          target: String(m.id),
          style: { stroke: verCamino && c in orden && m.id in orden ? "#1d4ed8" : "#bbb" },
        }))
      ),
    [plan, verCamino, orden]
  );

  // ---- Panel de edición de la materia seleccionada ----
  const editor = (() => {
    if (seleccionada === null) return null;
    const m = porId.get(seleccionada);
    if (!m) return null;
    const reg = historial[seleccionada];
    const estado = reg ? (reg.aprobada ? "aprobada" : "cursada") : "sin";
    const habilitada = m.correlativas.every(c => c in aprobadas);
    const puedeSimular = habilitada && !reg?.aprobada;
    const vecesActuales = reg?.veces ?? 0;

    const cambiarEstado = (e: string) => {
      setSim(null);
      if (e === "sin") guardar(seleccionada, null);
      else if (e === "cursada")
        guardar(seleccionada, {
          aprobada: false, nota: null,
          veces: reg && !reg.aprobada ? reg.veces : 1,
        });
      else
        guardar(seleccionada, {
          aprobada: true, nota: reg?.nota ?? 7,
          veces: Math.max(1, reg?.veces ?? 1),
        });
    };

    return (
      <div style={{ borderBottom: "1px solid #ddd", paddingBottom: 12, marginBottom: 12 }}>
        <h3 style={{ marginTop: 0 }}>{m.id}. {m.nombre}</h3>

        <label style={{ display: "block", marginBottom: 8 }}>
          Estado:{" "}
          <select value={estado} onChange={e => cambiarEstado(e.target.value)}>
            <option value="sin">Sin cursar</option>
            <option value="cursada">La cursé y no la aprobé</option>
            <option value="aprobada">Aprobada</option>
          </select>
        </label>

        {reg?.aprobada && (
          <label style={{ display: "block", marginBottom: 8 }}>
            Nota (6 a 10):{" "}
            <input
              type="number" min={6} max={10} step={0.5} value={reg.nota ?? 7}
              onChange={e => {
                const v = Math.min(10, Math.max(6, Number(e.target.value) || 6));
                guardar(seleccionada, { ...reg, nota: v });
              }}
            />
          </label>
        )}

        {reg && (
          <label style={{ display: "block", marginBottom: 8 }}>
            {reg.aprobada ? "Veces que la cursó (contando la que aprobó)" : "Veces que la cursó sin aprobar"}:{" "}
            <input
              type="number" min={1} max={reg.aprobada ? 6 : 5} value={reg.veces}
              onChange={e => {
                const max = reg.aprobada ? 6 : 5;
                const v = Math.min(max, Math.max(1, Math.round(Number(e.target.value)) || 1));
                guardar(seleccionada, { ...reg, veces: v });
              }}
            />
          </label>
        )}

        {puedeSimular && (
          <div style={{ background: "#f5f3ff", padding: 8, borderRadius: 6, marginBottom: 8 }}>
            <strong>🧪 ¿Y si...?</strong>
            <div style={{ margin: "6px 0" }}>
              <label>
                Nota si aprueba:{" "}
                <input
                  type="number" min={6} max={10} step={0.5} value={notaSim} style={{ width: 60 }}
                  onChange={e => setNotaSim(Math.min(10, Math.max(6, Number(e.target.value) || 6)))}
                />
              </label>
            </div>
            <button onClick={() => setSim({ id: seleccionada, tipo: "aprueba", nota: notaSim })}>
              Simular que la apruebo
            </button>{" "}
            <button
              disabled={vecesActuales >= 5}
              title={vecesActuales >= 5 ? "Máximo 5 intentos" : ""}
              onClick={() => setSim({ id: seleccionada, tipo: "desaprueba", nota: 0 })}
            >
              Simular que no la apruebo
            </button>
          </div>
        )}

        <button onClick={() => { setSeleccionada(null); setSim(null); }}>Cerrar</button>
      </div>
    );
  })();

  // ---- Panel de comparación ----
  const panelComparacion =
    sim && comparacion && (
      <div style={{ marginBottom: 12 }}>
        <h3 style={{ marginTop: 0 }}>
          🧪 Simulación: {sim.tipo === "aprueba" ? `apruebo con ${sim.nota}` : "no la apruebo"} (
          {porId.get(sim.id)?.nombre})
        </h3>
        <p style={{ margin: "4px 0" }}>
          Cambio promedio de P(aprobar) en lo que falta:{" "}
          <strong style={{ color: comparacion.promedio >= 0 ? "#15803d" : "#b91c1c" }}>
            {comparacion.promedio >= 0 ? "+" : ""}
            {(comparacion.promedio * 100).toFixed(1)} puntos
          </strong>
        </p>

        <h4 style={{ marginBottom: 4 }}>Materias que más cambian</h4>
        <table style={{ fontSize: 11, width: "100%" }}>
          <tbody>
            {comparacion.top.map(c => (
              <tr key={c.id}>
                <td>{porId.get(c.id)?.nombre}</td>
                <td>{Math.round(c.antes * 100)}% → {Math.round(c.despues * 100)}%</td>
                <td style={{ color: c.delta >= 0 ? "#15803d" : "#b91c1c" }}>
                  {c.delta >= 0 ? "+" : ""}{(c.delta * 100).toFixed(1)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        <h4 style={{ marginBottom: 4 }}>Secuencia sugerida</h4>
        <div style={{ display: "flex", gap: 8, fontSize: 11 }}>
          {[["Antes", comparacion.antes], ["Después", comparacion.despues]].map(([titulo, lista]) => (
            <div key={titulo as string} style={{ flex: 1 }}>
              <strong>{titulo as string}</strong>
              <ol style={{ paddingLeft: 18, margin: "4px 0" }}>
                {(lista as number[]).map(id => (
                  <li key={id}>{porId.get(id)?.nombre}</li>
                ))}
              </ol>
            </div>
          ))}
        </div>

        <button onClick={aplicarSimulacion}>Aplicar al historial</button>{" "}
        <button onClick={() => setSim(null)}>Salir de la simulación</button>
      </div>
    );

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh" }}>
      <header
        style={{
          display: "flex", alignItems: "center", gap: 24, flexWrap: "wrap",
          padding: "10px 16px", borderBottom: "1px solid #ddd",
        }}
      >
        <h2 style={{ margin: 0 }}>Planificador curricular · Abogacía</h2>

        <button
          onClick={() => setVerCamino(v => !v)}
          style={{
            padding: "8px 16px", borderRadius: 6, border: "none", cursor: "pointer",
            background: verCamino ? "#1d4ed8" : "#e5e7eb",
            color: verCamino ? "#fff" : "#000",
          }}
        >
          {verCamino ? "Ocultar camino sugerido" : "Ver camino sugerido"}
        </button>

        <label>
          Materias por cuatrimestre: {nMaterias}{" "}
          <input
            type="range" min={1} max={4} value={nMaterias}
            onChange={e => setNMaterias(Number(e.target.value))}
          />
        </label>

        <button onClick={() => { setHistorial({}); setSeleccionada(null); setSim(null); setAviso(""); }}>
          Borrar historial
        </button>

        <span style={{ fontSize: 12 }}>
          🟥 riesgosa → 🟩 segura · gris = aprobada · 🔒 = faltan correlativas · click para cargar historial
        </span>

        {sim && (
          <span style={{ background: "#7c3aed", color: "#fff", padding: "4px 10px", borderRadius: 6, fontSize: 12 }}>
            MODO SIMULACIÓN
          </span>
        )}
        {aviso && <span style={{ color: "#b91c1c", fontSize: 12 }}>{aviso}</span>}
      </header>

      <div style={{ display: "flex", flex: 1, minHeight: 0 }}>
        <div style={{ flex: 1 }}>
          <ReactFlow
            nodes={nodes} edges={edges} fitView
            nodesDraggable={false}
            onNodeClick={(_, n) => abrir(Number(n.id))}
          >
            <Background />
            <Controls />
          </ReactFlow>
        </div>

        {(seleccionada !== null || verCamino || sim) && (
          <aside style={{ width: 380, padding: 12, overflow: "auto", borderLeft: "1px solid #ddd" }}>
            {editor}
            {panelComparacion}
            {verCamino && (
              <>
                <h3 style={{ marginTop: 0 }}>Camino sugerido{sim ? " (simulado)" : ""}</h3>
                <p style={{ fontSize: 12, opacity: 0.7 }}>
                  Orden de cursada que respeta las correlatividades y prioriza las materias de menor riesgo.
                </p>
                <ol>
                  {vista?.secuencia.map(id => (
                    <li key={id}>
                      {porId.get(id)?.nombre}{" "}
                      ({Math.round((vista.probabilidades[id] ?? 0) * 100)}%)
                    </li>
                  ))}
                </ol>
              </>
            )}
          </aside>
        )}
      </div>
    </div>
  );
}