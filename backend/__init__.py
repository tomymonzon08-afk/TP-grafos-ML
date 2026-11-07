from backend import planDeEstudios as pe
from backend.perfilEstudiante import Estudiante, APROBADA
from backend.reglas import habilitadas
from backend.grafo import armarGrafo, mostrarGrafo
import networkx as nx

est = Estudiante(list(pe.plan.index))
print(habilitadas(pe.plan, est))        # esperado: [1, 2, 3, 4, 5, 6, 44]

est.registrar(5, APROBADA, 8)
print(habilitadas(pe.plan, est))        # ahora aparece el 7 y no el 5

dag = nx.DiGraph()
armarGrafo(dag, pe.plan)
mostrarGrafo(dag)