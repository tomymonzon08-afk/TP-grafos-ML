import numpy as np
import pandas as pd

NO_CURSADA = "No cursada"
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

    def aprobadas_ids(self):
        return set(self.perfil.index[self.perfil["estado"] == APROBADA])

