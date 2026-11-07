import networkx as nx
import matplotlib.pyplot as plt

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



