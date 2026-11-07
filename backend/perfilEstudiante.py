import numpy as np
import pandas as pd

NO_CURSADA = "No cursada"
CURSANDO = "Cursando"
APROBADA = "Aprobada"
DESAPROBADA = "Desaprobada"


class Estudiante:

    def __init__(self, ids_materias):
        self.perfil = pd.DataFrame({
            "id_materia": ids_materias,
            "nota": np.nan,
            "intentos": 0,
            "estado": NO_CURSADA,
        }).set_index("id_materia")

    def registrar(self, id_materia, estado, nota=np.nan):
        self.perfil.loc[id_materia, "estado"] = estado
        self.perfil.loc[id_materia, "nota"] = nota
        if estado in (APROBADA, DESAPROBADA):
            self.perfil.loc[id_materia, "intentos"] += 1

    def materias_cursando(self):
        return (self.perfil["estado"] == CURSANDO).sum()

    def materias_aprobadas(self):
        return (self.perfil["estado"] == APROBADA).sum()

    def aprobadas_ids(self):
        return set(self.perfil.index[self.perfil["estado"] == APROBADA])

    def promedio(self):
        notas = self.perfil.loc[self.perfil["estado"] == APROBADA, "nota"]
        return notas.mean()  # NaN si todavía no aprobó nada

    def promedio_correlativas(self, correlativas):
        if not correlativas:        # lista vacía: sin correlativas
            return np.nan
        return self.perfil.loc[correlativas, "nota"].mean()

    def es_recursada(self, id_materia):
        return self.perfil.loc[id_materia, "intentos"] > 0

    def copiar(self):
        nuevo = Estudiante([])
        nuevo.perfil = self.perfil.copy()
        return nuevo

    def chequear_corr_aprob(self, correlativas):
        if not correlativas:
            return True
        
        chequeadas = (self.perfil.loc[correlativas, "estado"] == APROBADA).sum()

        if chequeadas == len(correlativas):
            return True
        else:
            return False

    def mostrar_perfil(self):
        print(self.perfil)

    def veces_recursada(self, id_materia):
        return int(self.perfil.loc[id_materia, "intentos"])
