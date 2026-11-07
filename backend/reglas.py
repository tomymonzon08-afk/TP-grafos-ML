from backend.perfilEstudiante import APROBADA, CURSANDO


def habilitadas(plan, estudiante):
    resultado = []

    for id_materia, fila in plan.iterrows():
        estado =estudiante.perfil.loc[id_materia,"estado"] 
        if estado != APROBADA and estado != CURSANDO :
            if estudiante.chequear_corr_aprob(fila["correlativas"]):
                resultado.append(id_materia)

    return resultado