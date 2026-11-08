from pathlib import Path
import joblib
import pandas as pd
import networkx as nx
from backend.perfilEstudiante import APROBADA

INICIO = "INICIO"
RECIBIDO = "RECIBIDO"
DEFECTO = 6.0   # misma regla que el generador

_modelo = joblib.load(Path(__file__).parent / "modelo_aprobacion.joblib")

def features_materia(plan, estudiante, id_materia, n_materias, grafo):
    perfil = estudiante.perfil
    aprobadas = perfil[perfil["estado"] == APROBADA]
    prom_general = aprobadas["nota"].mean() if len(aprobadas) else DEFECTO

    # nota real si está aprobada, si no la proyectada
    notas_corr = [
        aprobadas.loc[c, "nota"] if c in aprobadas.index else prom_general
        for c in plan.loc[id_materia, "correlativas"]
    ]
    prom_corr = sum(notas_corr) / len(notas_corr) if notas_corr else DEFECTO
    peor_corr = min(notas_corr) if notas_corr else DEFECTO

    previas = (nx.ancestors(grafo, id_materia) - {INICIO}) | set(aprobadas.index)

    return {
        "promedio_general": prom_general,
        "promedio_correlativas": prom_corr,
        "peor_nota_correlativa": peor_corr,
        "veces_recursada": int(perfil.loc[id_materia, "intentos"]),
        "n_materias_cuatrimestre": n_materias,
        "avance_carrera": len(previas) / len(plan),
        "materia": id_materia,
    }


def predecir_probabilidades(plan, grafo, estudiante, n_materias=3):
    aprobadas = estudiante.aprobadas_ids()
    pendientes = [m for m in plan.index if m not in aprobadas]

    filas = [features_materia(plan, estudiante, m, n_materias, grafo) for m in pendientes]
    X = pd.DataFrame(filas)
    if hasattr(_modelo, "feature_names_in_"):
        X = X[list(_modelo.feature_names_in_)]   # mismo orden que en el entrenamiento

    p = _modelo.predict_proba(X)[:, 1]

    probs = dict(zip(pendientes, p))
    probs.update({m: 1.0 for m in aprobadas})    # aprobadas cuestan 0
    probs[RECIBIDO] = 1.0
    return probs