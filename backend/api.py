from fastapi import FastAPI, HTTPException
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
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE = nx.DiGraph()
armarGrafo(BASE, pe.plan)


class Registro(BaseModel):
    aprobada: bool = False
    nota: float | None = None   # solo si aprobada (6 a 10)
    veces: int = 0              # veces que la cursó


class Perfil(BaseModel):
    historial: dict[int, Registro] = {}   # {id_materia: Registro}
    n_materias: int = 3


@app.get("/plan")
def plan():
    return [
        {"id": int(i), "nombre": f["nombre"], "anio": int(f["anio"]),
         "correlativas": [int(c) for c in f["correlativas"]]}
        for i, f in pe.plan.iterrows()
    ]


def validar(historial: dict[int, Registro]):
    aprobadas = {m for m, r in historial.items() if r.aprobada}
    for m, r in historial.items():
        if m not in pe.plan.index:
            raise HTTPException(400, f"La materia {m} no existe")
        if r.aprobada:
            if r.nota is None or not (6 <= r.nota <= 10):
                raise HTTPException(400, f"La materia {m} aprobada necesita nota entre 6 y 10")
            if r.veces < 1:
                raise HTTPException(400, f"La materia {m} aprobada debe tener al menos 1 cursada")
        elif r.veces < 1 or r.veces > 5:
            raise HTTPException(400, f"La materia {m}: veces debe estar entre 1 y 5")
        faltan = [c for c in pe.plan.loc[m, "correlativas"] if c not in aprobadas]
        if faltan:
            raise HTTPException(
                400, f"La materia {m} tiene registro pero faltan las correlativas {faltan}"
            )


@app.post("/sugerencia")
def sugerencia(p: Perfil):
    validar(p.historial)
    n = max(1, min(4, p.n_materias))     # el generador solo vio 1 a 4

    # Armamos el perfil del estudiante con el historial
    est = Estudiante(list(pe.plan.index))
    for m, r in p.historial.items():
        if r.aprobada:
            est.registrar(m, APROBADA, r.nota)
        else:
            est.registrar(m, DESAPROBADA)
        est.perfil.loc[m, "intentos"] = r.veces   # el modelo lo lee como veces_recursada

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