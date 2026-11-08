from backend import planDeEstudios as pe
from backend.perfilEstudiante import Estudiante
from backend.grafo import armarGrafo, dijkstra_correlativas, camino, INICIO, RECIBIDO
from backend.manejoPredicciones import predecir_probabilidades
from backend.prob2weig import asignar_pesos
import networkx as nx

if __name__ == "__main__":
    est = Estudiante(list(pe.plan.index))
    dag = nx.DiGraph()
    armarGrafo(dag, pe.plan)
    probs = predecir_probabilidades(pe.plan, dag, est, n_materias=3)
    asignar_pesos(dag, probs)
    costos, pred, orden = dijkstra_correlativas(dag)
    print(len(orden))                    
    print(camino(pred, RECIBIDO))
    # 1. el orden respeta las correlatividades
    pos = {m: i for i, m in enumerate(orden)}
    for m in pe.plan.index:
        for c in pe.plan.loc[m, "correlativas"]:
            assert pos[c] < pos[m], f"{m} aparece antes que su correlativa {c}"

    # 2. las probabilidades son razonables
    print(probs[1], probs[30], probs[43])     # entre 0 y 1; las de años altos suelen ser menores

    # 3. camino de mayor riesgo
    print(nx.dag_longest_path(dag, weight="weight"))

    # 4. secuencia sugerida solo con pendientes
    sugerida = [m for m in orden if m not in (INICIO, RECIBIDO) and m not in est.aprobadas_ids()]
    print(sugerida)