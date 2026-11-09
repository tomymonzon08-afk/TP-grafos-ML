import math

P_MIN = 1e-6

def asignar_pesos(grafo, probabilidades):
    for origen, destino in grafo.edges:
        p = probabilidades.get(destino)   
        p = max(p, P_MIN)                      # evita log(0)
        grafo[origen][destino]["weight"] = -math.log(p)



