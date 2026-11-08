from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import networkx as nx

from backend import planDeEstudios as pe
from backend.perfilEstudiante import Estudiante, APROBADA, DESAPROBADA
from backend.grafo import armarGrafo, dijkstra_correlativas, INICIO, RECIBIDO
from backend.manejoPredicciones import predecir_probabilidades
from backend.prob2weig import asignar_pesos

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174"],   # el puerto de Vite
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE = nx.DiGraph()
armarGrafo(BASE, pe.plan)


class Perfil(BaseModel):
    aprobadas: dict[int, float] = {}   # {id_materia: nota}
    desaprobadas: list[int] = []
    n_materias: int = 3


@app.get("/plan")
def plan():
    return [
        {"id": int(i), "nombre": f["nombre"], "anio": int(f["anio"]),
         "correlativas": [int(c) for c in f["correlativas"]]}
        for i, f in pe.plan.iterrows()
    ]


@app.post("/sugerencia")
def sugerencia(p: Perfil):
    n = max(1, min(4, p.n_materias))       # el generador solo vio 1 a 4
    est = Estudiante(list(pe.plan.index))
    for m, nota in p.aprobadas.items():
        est.registrar(m, APROBADA, nota)
    for m in p.desaprobadas:
        est.registrar(m, DESAPROBADA)

    g = BASE.copy()
    probs = predecir_probabilidades(pe.plan, g, est, n)
    asignar_pesos(g, probs)
    _, _, orden = dijkstra_correlativas(g)

    aprobadas = est.aprobadas_ids()
    secuencia = [int(m) for m in orden
                 if m not in (INICIO, RECIBIDO) and m not in aprobadas]
    return {
        "probabilidades": {int(m): float(v) for m, v in probs.items() if m != RECIBIDO},
        "secuencia": secuencia,
        "aprobadas": [int(m) for m in aprobadas],
    }