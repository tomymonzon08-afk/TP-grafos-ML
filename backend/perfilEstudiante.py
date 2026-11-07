import numpy as np
import pandas as pd

perfil = pd.DataFrame({
    "id_materia": [ 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28],
    "nombre": ["Laboratorio de Datos I",
                "Estadística I",
                "Programación I", 
                "Álgebra y Geometría Analítica I", 
                "Estadística II", 
                "Programación II",
                "Análisis Matematico I",
                "Prácticas Sociales Educativas: Módulo Introductorio",
                "Aprendizaje Estadístico I",
                "Análisis Exploratorio de datos",
                "Análisis Matematico II",
                "Álgebra Lineal",
                "Bases de datos",
                "Aprendizaje Estadístico II",
                "Probabilidad e Inferencia Estadística",
                "Laboratorio de Datos",
                "Prácticas sociales Educativas: Módulo de Intervención Sociocomunitaria",
                "Aprendizaje Profundo",
                "Métodos Númericos y Simulación",
                "Procesamiento del Lenguaje Natural",
                "Procesamiento de Grandes Volúmenes de Datos",
                "Procesamiento de Datos Espaciales",
                "Organización Empresarial y Gestión de Proyectos",
                "Visión por computadora",
                "Inteligencia de Negocios",
                "Gestión de datos No Estructurados",
                "Integración y Despliegue Continuo de Modelos",
                "Seminario de Integración y Aplicación Profesional"
                ],
    "correlativas": [np.nan,
                     np.nan,
                     np.nan,
                     np.nan,
                     [2],
                     [3],
                     np.nan,
                     np.nan,
                     [5],
                     [1,3],
                     [7],
                     [4],
                     [6],
                     [9],
                     [5,11],
                     [1,6],
                     [8],
                     [11,14],
                     [6,11],
                     [18],
                     [6,13],
                     [10],
                     [13],
                     [18],
                     [13],
                     [21],
                     [18,21],
                     [20,21,22,23] 
                     ],
    "año": [1,1,1,1,1,1,1,1,2,2,2,2,2,2,2,3,3,3,3,3,3,3,3,4,4,4,4,4], 
    "cuatrimestre": [1,1,1,1,2,2,2,2,1,1,1,1,2,2,2,1,1,1,1,2,2,2,2,1,1,1,2,2],
    "nota": [np.nan] * 28,
})


promedio = perfil["nota"].mean()
materias_aprobadas = (perfil["nota"] >= 6).sum()
materias_cursando = 0

def prom_correlativas(correlativas, notas):
    #Promedio de las notas de las correlativas de una materia.
    #Devuelve NaN si no tiene correlativas o si ninguna tiene nota
    if not isinstance(correlativas, list):  # NaN (sin correlativas)
        return np.nan
    return notas.reindex(correlativas).mean()  # mean ignora NaN

def actualizar_promedio_corr():
    notas = perfil.set_index("id_materia")["nota"]
    perfil["promedio_corr"] = perfil["correlativas"].apply(
        lambda c: prom_correlativas(c, notas)
    )

def agregar_nota(id_materia, nota):
    perfil.loc[perfil["id_materia"] == id_materia, "nota"] = nota
    actualizar_promedio_corr()

#Elegimos el plan de estudios de la carrera Ciencia de Datos de la FCEyE. Dejamos de lado las materias optativas para este diseño