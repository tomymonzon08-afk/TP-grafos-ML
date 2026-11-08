import { useEffect, useState } from "react";
import { ReactFlow, type Node, type Edge } from "@xyflow/react";
import "@xyflow/react/dist/style.css";

const API = "http://localhost:8000";

type Materia = { id: number; nombre: string; anio: number; correlativas: number[] };
type Resultado = { probabilidades: Record<string, number>; secuencia: number[]; aprobadas: number[] };

// rojo = riesgoso, verde = seguro
const color = (p: number) => `hsl(${Math.round(p * 120)}, 70%, 70%)`;

export default function App() {
  const [plan, setPlan] = useState<Materia[]>([]);
  const [aprobadas, setAprobadas] = useState<Record<number, number>>({});
  const [nMaterias, setNMaterias] = useState(3);
  const [res, setRes] = useState<Resultado | null>(null);

  useEffect(() => {
    fetch(`${API}/plan`).then(r => r.json()).then(setPlan);
  }, []);

  useEffect(() => {
    fetch(`${API}/sugerencia`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ aprobadas, desaprobadas: [], n_materias: nMaterias }),
    }).then(r => r.json()).then(setRes);
  }, [aprobadas, nMaterias]);

  const porAnio: Record<number, number> = {};
  const nodes: Node[] = plan.map(m => {
    const fila = (porAnio[m.anio] = (porAnio[m.anio] ?? -1) + 1);
    const p = res?.probabilidades[m.id] ?? 0.5;
    const aprobada = m.id in aprobadas;
    return {
      id: String(m.id),
      position: { x: (m.anio - 1) * 230, y: fila * 70 },
      data: { label: `${m.id}. ${m.nombre}` },
      style: { background: aprobada ? "#ccc" : color(p), fontSize: 11, width: 200 },
    };
  });
  const edges: Edge[] = plan.flatMap(m =>
    m.correlativas.map(c => ({ id: `${c}-${m.id}`, source: String(c), target: String(m.id) }))
  );

  const toggle = (id: number) =>
    setAprobadas(a => {
      const n = { ...a };
      if (id in n) delete n[id]; else n[id] = 7;   // nota por defecto
      return n;
    });

  return (
    <div style={{ display: "flex", height: "100vh" }}>
      <div style={{ flex: 1 }}>
        <ReactFlow nodes={nodes} edges={edges} fitView
          onNodeClick={(_, n) => toggle(Number(n.id))} />
      </div>
      <aside style={{ width: 300, padding: 12, overflow: "auto" }}>
        <label>Materias por cuatrimestre: {nMaterias}
          <input type="range" min={1} max={4} value={nMaterias}
                 onChange={e => setNMaterias(Number(e.target.value))} />
        </label>
        <h3>Secuencia sugerida</h3>
        <ol>
          {res?.secuencia.map(id => (
            <li key={id}>{plan.find(m => m.id === id)?.nombre}
              {" "}({Math.round((res.probabilidades[id] ?? 0) * 100)}%)</li>
          ))}
        </ol>
      </aside>
    </div>
  );
}
