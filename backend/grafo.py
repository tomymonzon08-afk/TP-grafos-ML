import networkx as nx
import matplotlib.pyplot as plt
from planDeEstudios import planDeEstudios as pe


def armarGrafo(grafo, plan):
    grafo.add_node(0)  # nodo de inicio

    for id_materia in plan["id_materia"]:
        grafo.add_node(id_materia)

    # Iteramos por fila, usando directamente el id_materia (no el índice)
    for _, fila in plan.iterrows():
        id_materia = fila["id_materia"]
        correlativas = fila["correlativas"]

        # Sin correlativas: arista desde el nodo de inicio
        if not isinstance(correlativas, list):   # np.nan no es lista
            grafo.add_edge(0, id_materia, weight=0, active=True)
        # Con correlativas: una arista desde cada correlativa
        else:
            for correlativa in correlativas:
                grafo.add_edge(correlativa, id_materia, weight=0, active=False)


def mostrarGrafo(grafo):
    # Layout por capas: calcula la "generación" de cada nodo en el DAG
    for capa, nodos in enumerate(nx.topological_generations(grafo)):
        for n in nodos:
            grafo.nodes[n]["capa"] = capa

    pos = nx.multipartite_layout(grafo, subset_key="capa")

    plt.figure(figsize=(14, 8))
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
    plt.title("Grafo de correlatividades - Ciencia de Datos")
    plt.show()


dag = nx.DiGraph()
armarGrafo(dag, pe)

mostrarGrafo(dag)