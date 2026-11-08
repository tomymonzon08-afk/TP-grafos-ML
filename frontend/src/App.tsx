import { useEffect, useMemo, useState } from "react";
import { ReactFlow, Background, Controls, type Node, type Edge } from "@xyflow/react";
import "@xyflow/react/dist/style.css";

const API = "http://localhost:8000";

type Materia = { id: number; nombre: string; anio: number; correlativas: number[] };
type Resultado = {
  probabilidades: Record<string, number>;
  secuencia: number[];
  aprobadas: number[];
};

// rojo = riesgosa, verde = segura
const color = (p: number) => `hsl(${Math.round(p * 120)}, 70%, 75%)`;

export default function App() {
  const [plan, setPlan] = useState<Materia[]>([]);
  const [aprobadas, setAprobadas] = useState<Record<number, number>>({});
  const [nMaterias, setNMaterias] = useState(3);
  const [res, setRes] = useState<Resultado | null>(null);
  const [verCamino, setVerCamino] = useState(false);
  const [aviso, setAviso] = useState(""); // NUEVO: mensaje de error

  // NUEVO: acceso rápido a una materia por su id
  const porId = useMemo(() => new Map(plan.map(m => [m.id, m])), [plan]);

  useEffect(() => {
    fetch(`${API}/plan`).then(r => r.json()).then(setPlan);
  }, []);

  useEffect(() => {
    fetch(`${API}/sugerencia`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ aprobadas, desaprobadas: [], n_materias: nMaterias }),
    })
      .then(r => (r.ok ? r.json() : Promise.reject(r.status)))
      .then(setRes)
      .catch(() => {});
  }, [aprobadas, nMaterias]);

  const orden = useMemo(() => {
    const o: Record<number, number> = {};
    res?.secuencia.forEach((id, i) => (o[id] = i + 1));
    return o;
  }, [res]);

  const nodes: Node[] = useMemo(() => {
    const fila: Record<number, number> = {};
    return plan.map(m => {
      fila[m.anio] = (fila[m.anio] ?? -1) + 1;
      const p = res?.probabilidades[m.id];
      const aprobada = m.id in aprobadas;
      const enCamino = verCamino && m.id in orden;
      const apagada = verCamino && !enCamino;
      // NUEVO: bloqueada = no está aprobada y le faltan correlativas
      const bloqueada = !aprobada && !m.correlativas.every(c => c in aprobadas);

      return {
        id: String(m.id),
        position: { x: (m.anio - 1) * 240, y: fila[m.anio] * 80 },
        data: {
          label: (
            <div>
              {enCamino && <strong style={{ color: "#1d4ed8" }}>#{orden[m.id]} </strong>}
              {bloqueada && "🔒 "}
              {m.id}. {m.nombre}
              {p !== undefined && !aprobada && (
                <div style={{ opacity: 0.7 }}>{Math.round(p * 100)}%</div>
              )}
            </div>
          ),
        },
        style: {
          background: aprobada ? "#d4d4d4" : p === undefined ? "#fff" : color(p),
          width: 210,
          fontSize: 11,
          cursor: bloqueada ? "not-allowed" : "pointer", // NUEVO
          border: enCamino
            ? "3px solid #1d4ed8"
            : bloqueada
            ? "1px dashed #999"
            : "1px solid #888", // NUEVO
          opacity: apagada ? 0.35 : 1,
        },
      };
    });
  }, [plan, res, aprobadas, verCamino, orden]);

  const edges: Edge[] = useMemo(
    () =>
      plan.flatMap(m =>
        m.correlativas.map(c => ({
          id: `${c}-${m.id}`,
          source: String(c),
          target: String(m.id),
          style: {
            stroke: verCamino && c in orden && m.id in orden ? "#1d4ed8" : "#bbb",
          },
        }))
      ),
    [plan, verCamino, orden]
  );

  // NUEVO: toggle con validación de correlativas
  const toggle = (id: number) => {
    const m = porId.get(id);
    if (!m) return;

    // Caso 1: ya está aprobada -> se desaprueba, junto con las que dependen de ella
    if (id in aprobadas) {
      const quitar = new Set<number>([id]);
      let cambio = true;
      while (cambio) {
        cambio = false;
        for (const x of plan) {
          if (
            !quitar.has(x.id) &&
            x.id in aprobadas &&
            x.correlativas.some(c => quitar.has(c))
          ) {
            quitar.add(x.id);
            cambio = true;
          }
        }
      }
      setAprobadas(a => {
        const n = { ...a };
        quitar.forEach(q => delete n[q]);
        return n;
      });
      setAviso(
        quitar.size > 1
          ? `Se quitaron también ${quitar.size - 1} materia(s) que dependían de "${m.nombre}".`
          : ""
      );
      return;
    }

    // Caso 2: no está aprobada -> solo se aprueba si todas sus correlativas lo están
    const faltan = m.correlativas.filter(c => !(c in aprobadas));
    if (faltan.length > 0) {
      const nombres = faltan.map(c => porId.get(c)?.nombre).join(", ");
      setAviso(`No podés aprobar "${m.nombre}": falta aprobar ${nombres}.`);
      return;
    }
    setAprobadas(a => ({ ...a, [id]: 7 }));
    setAviso("");
  };

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

        <span style={{ fontSize: 12 }}>
          🟥 riesgosa → 🟩 segura · gris = aprobada · 🔒 = faltan correlativas
        </span>

        {/* NUEVO: aviso de error */}
        {aviso && <span style={{ color: "#b91c1c", fontSize: 12 }}>{aviso}</span>}
      </header>

      <div style={{ display: "flex", flex: 1, minHeight: 0 }}>
        <div style={{ flex: 1 }}>
          <ReactFlow
            nodes={nodes} edges={edges} fitView
            nodesDraggable={false}
            onNodeClick={(_, n) => toggle(Number(n.id))}
          >
            <Background />
            <Controls />
          </ReactFlow>
        </div>

        {verCamino && (
          <aside style={{ width: 300, padding: 12, overflow: "auto", borderLeft: "1px solid #ddd" }}>
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
          </aside>
        )}
      </div>
    </div>
  );
}