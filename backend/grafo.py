import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
from planDeEstudios import planDeEstudios as pe

def armarGrafo(grafo, planDeEstudios):
    for id_materia in planDeEstudios["id_materia"]:
        grafo.add_node(id_materia)

    for materia in range(28):
        #si no tiene correlativas, añade una arista dirigida desde el nodo de inicio hacia ella
        if pd.isna(planDeEstudios.at[materia+1,"correlativas"]) : 
            grafo.add_edge(0, materia, weight = 0, active = True)
        #si tiene correlativas, añade una arista dirgida desde cada correlativa a la materia
        else:
            for correlativa in planDeEstudios.at[materia, "correlativas"]:
                grafo.add_edge( correlativa, materia, weight = 0, active = False) 


def mostrarGrafo(grafo):
    plt.figure(figsize=(6, 4))
    nx.draw(
        grafo, 
        with_labels=True,       # Muestra el número/nombre de los nodos
        node_color='skyblue',   # Color de los nodos
        node_size=700,          # Tamaño de los nodos
        font_size=12,           # Tamaño del texto
        font_weight='bold',     # Negrita en las etiquetas
        edge_color='gray'       # Color de las aristas
    )

    # 4. Mostrar en pantalla
    plt.title("Ejemplo de Grafo con NetworkX")
    plt.show()


    


dag = nx.DiGraph()
dag.add_node(0)
armarGrafo(dag, pe)
mostrarGrafo(dag)
