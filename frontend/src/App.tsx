import { useEffect, useMemo, useState } from "react";
import { ReactFlow, Background, Controls, type Node, type Edge } from "@xyflow/react";
import "@xyflow/react/dist/style.css";

const API = "http://localhost:8000";

type Materia = { id: number; nombre: string; anio: number; correlativas: number[] };
type Registro = { aprobada: boolean; nota: number | null; veces: number };
type Resultado = {
  probabilidades: Record<string, number>;
  secuencia: number[];
  aprobadas: number[];
};

const color = (p: number) => `hsl(${Math.round(p * 120)}, 70%, 75%)`;

export default function App() {
  const [plan, setPlan] = useState<Materia[]>([]);
  const [historial, setHistorial] = useState<Record<number, Registro>>({});
  const [seleccionada, setSeleccionada] = useState<number | null>(null);
  const [nMaterias, setNMaterias] = useState(3);
  const [res, setRes] = useState<Resultado | null>(null);
  const [verCamino, setVerCamino] = useState(false);
  const [aviso, setAviso] = useState("");

  const porId = useMemo(() => new Map(plan.map(m => [m.id, m])), [plan]);

  // ids aprobados, derivados del historial
  const aprobadas = useMemo(() => {
    const a: Record<number, number> = {};
    for (const [id, r] of Object.entries(historial))
      if (r.aprobada) a[Number(id)] = r.nota ?? 7;
    return a;
  }, [historial]);

  useEffect(() => {
    fetch(`${API}/plan`).then(r => r.json()).then(setPlan);
  }, []);

  // cada cambio del historial recalcula las probabilidades en el backend
  useEffect(() => {
    fetch(`${API}/sugerencia`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ historial, n_materias: nMaterias }),
    })
      .then(r => (r.ok ? r.json() : Promise.reject(r.status)))
      .then(setRes)
      .catch(() => {});
  }, [historial, nMaterias]);

  const orden = useMemo(() => {
    const o: Record<number, number> = {};
    res?.secuencia.forEach((id, i) => (o[id] = i + 1));
    return o;
  }, [res]);

  // Guarda (o borra) el registro de una materia. Si deja de estar aprobada,
  // se borra también el registro de todo lo que dependa de ella.
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
          if (q !== id && q in n) {
            delete n[q];
            borradas++;
          }
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
    setSeleccionada(id);
  };

  const nodes: Node[] = useMemo(() => {
    const fila: Record<number, number> = {};
    return plan.map(m => {
      fila[m.anio] = (fila[m.anio] ?? -1) + 1;
      const p = res?.probabilidades[m.id];
      const reg = historial[m.id];
      const aprobada = !!reg?.aprobada;
      const enCamino = verCamino && m.id in orden;
      const apagada = verCamino && !enCamino;
      const bloqueada = !aprobada && !m.correlativas.every(c => c in aprobadas);

      return {
        id: String(m.id),
        position: { x: (m.anio - 1) * 240, y: fila[m.anio] * 90 },
        data: {
          label: (
            <div>
              {enCamino && <strong style={{ color: "#1d4ed8" }}>#{orden[m.id]} </strong>}
              {bloqueada && "🔒 "}
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
            seleccionada === m.id ? "3px solid #000"
            : enCamino ? "3px solid #1d4ed8"
            : bloqueada ? "1px dashed #999"
            : "1px solid #888",
          opacity: apagada ? 0.35 : 1,
        },
      };
    });
  }, [plan, res, historial, aprobadas, verCamino, orden, seleccionada]);

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

    const cambiarEstado = (e: string) => {
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

        <button onClick={() => setSeleccionada(null)}>Cerrar</button>
      </div>
    );
  })();

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

        <button onClick={() => { setHistorial({}); setSeleccionada(null); setAviso(""); }}>
          Borrar historial
        </button>

        <span style={{ fontSize: 12 }}>
          🟥 riesgosa → 🟩 segura · gris = aprobada · 🔒 = faltan correlativas · click para cargar historial
        </span>

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

        {(seleccionada !== null || verCamino) && (
          <aside style={{ width: 320, padding: 12, overflow: "auto", borderLeft: "1px solid #ddd" }}>
            {editor}
            {verCamino && (
              <>
                <h3 style={{ marginTop: 0 }}>Camino sugerido</h3>
                <p style={{ fontSize: 12, opacity: 0.7 }}>
                  Orden de cursada que respeta las correlatividades y prioriza las materias de menor riesgo.
                </p>
                <ol>
                  {res?.secuencia.map(id => (
                    <li key={id}>
                      {porId.get(id)?.nombre}{" "}
                      ({Math.round((res.probabilidades[id] ?? 0) * 100)}%)
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