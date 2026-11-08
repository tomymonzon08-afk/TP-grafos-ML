import networkx as nx
import matplotlib.pyplot as plt
from math import inf

INICIO = "Recibido"
RECIBIDO = "Recibido"

def armarGrafo(grafo, plan):
    grafo.add_node(INICIO)
    grafo.add_node(RECIBIDO)
    for id_materia in plan.index:
        grafo.add_node(id_materia)

    for id_materia, fila in plan.iterrows():
        if not fila["correlativas"]:
            grafo.add_edge(INICIO, id_materia, weight=0)
        else:
            for c in fila["correlativas"]:
                grafo.add_edge(c, id_materia, weight=0)

    for id_materia, fila in plan.iterrows():
        if grafo.out_degree(id_materia) == 0:
                grafo.add_edge(id_materia,RECIBIDO,weigth=0)



def camino_critico(grafo, destino=RECIBIDO):
    return nx.dijkstra_path(grafo, INICIO, destino, weight="weight")


def mostrarGrafo(grafo, mostrar_pesos=True):
    # Layout por capas: la "generación" de cada nodo en el DAG
    for capa, nodos in enumerate(nx.topological_generations(grafo)):
        for n in nodos:
            grafo.nodes[n]["capa"] = capa

    pos = nx.multipartite_layout(grafo, subset_key="capa")

    plt.figure(figsize=(16, 9))
    nx.draw(
        grafo,
        pos,
        with_labels=True,
        node_color="skyblue",
        node_size=700,
        font_size=10,
        font_weight="bold",
        edge_color="gray",
        arrows=True,
    )

    if mostrar_pesos:
        etiquetas = {
            (u, v): f"{d['weight']:.2f}"
            for u, v, d in grafo.edges(data=True)
        }
        nx.draw_networkx_edge_labels(
            grafo,
            pos,
            edge_labels=etiquetas,
            font_size=7,
            label_pos=0.3,          # más cerca del origen, evita que se pisen
            bbox=dict(alpha=0),     # sin fondo blanco que tape las flechas
        )

    plt.title("Grafo de correlatividades - Abogacía")
    plt.show()


def dijkstra_correlativas(grafo, a=INICIO, dest=None):
    # correlativas de cada nodo = sus predecesores en el grafo (sin contar INICIO)
    correlativas = {
        n: [p for p in grafo.predecessors(n) if p != a]
        for n in grafo.nodes
    }

    costos = {x: inf for x in grafo}
    costos[a] = 0
    pred = {a: None} #pred[x] es el nodo v desde el que se llegó a x con menor costo
    pendientes = set(grafo)          # nodos pendientes
    tomados = set()         # nodos ya fijados
    orden = []

    while pendientes and (dest is None or dest in pendientes):
        # candidatos: alcanzables y con todas sus correlativas ya tomadas
        candidatos = [
            x for x in pendientes
            if costos[x] < inf and all(c in tomados for c in correlativas[x])
        ]
        if not candidatos:
            break

        v = min(candidatos, key=lambda x: costos[x])   # el de menor peso que cumple
        pendientes.remove(v)
        tomados.add(v)
        orden.append(v)

        for x, datos in grafo[v].items():
            w = datos["weight"]
            if x in pendientes and costos[v] + w < costos[x]:
                costos[x] = costos[v] + w
                pred[x] = v

    return costos, pred, orden



def camino(pred, a, z):
    if z not in pred:
        return None
    ruta = []
    while z is not None:
        ruta.append(z)
        z = pred[z]
    return ruta[::-1]
