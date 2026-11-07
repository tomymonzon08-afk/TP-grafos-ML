import networkx as nx
import matplotlib.pyplot as plt
import planDeEstudios as pe
import prob2weig as pw

INICIO = "INICIO"

def armarGrafo(grafo, plan):
    grafo.add_node(INICIO)
    for id_materia in plan.index:
        grafo.add_node(id_materia)

    for id_materia, fila in plan.iterrows():
        if not fila["correlativas"]:
            grafo.add_edge(INICIO, id_materia, weight=0)
        else:
            for c in fila["correlativas"]:
                grafo.add_edge(c, id_materia, weight=0)


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




dag = nx.DiGraph()
armarGrafo(dag, pe.plan)
pw.asignar_pesos(dag, {1:0.3,2:0.9,4:0.7, 9:0.99999999})
mostrarGrafo(dag)