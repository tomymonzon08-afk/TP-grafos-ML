import networkx as nx
import matplotlib.pyplot as plt
import planDeEstudios as pe

def armarGrafo(grafo, plan):
    grafo.add_node(0) 

    for id_materia in plan["id_materia"]:
        grafo.add_node(id_materia)

    for _, fila in plan.iterrows():
        id_materia = fila["id_materia"]
        correlativas = fila["correlativas"]

        # Sin correlativas: arista desde el nodo de inicio
        if not isinstance(correlativas, list):   # np.nan no es lista
            grafo.add_edge(0, id_materia, weight=0)
        # Con correlativas: una arista desde cada correlativa
        else:
            for correlativa in correlativas:
                grafo.add_edge(correlativa, id_materia, weight=0)


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
armarGrafo(dag, pe.perfil)
mostrarGrafo(dag)