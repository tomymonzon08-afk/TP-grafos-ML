import json
import numpy as np
import pandas as pd
from collections import deque
from pathlib import Path

# ---------- Configuración ----------
RNG = np.random.default_rng(42)
N_ESTUDIANTES = 1500
MAX_CUATRIMESTRES = 12
N_CURSAR_MIN, N_CURSAR_MAX = 1, 4
SIGMA_RUIDO = 0.85

DATA = Path(__file__).parent

# ---------- Carga ----------
plan = json.load(open(DATA / "plan_estudios.json"))
dificultades = json.load(open(DATA / "dificultades_generador.json"))
features_cfg = json.load(open(DATA / "features_estudiante.json"))

MATERIAS = plan["materias"]
MAT = {str(m["id"]): m for m in MATERIAS}  # Forzamos que las claves del dict sean texto
N_MATERIAS = len(MATERIAS)

COLS_FEATURES = [f["nombre"] for f in features_cfg["features_modelo"]["features"]]

# ---------- Validaciones ----------
def validar():
    ids_plan = set(MAT.keys())
    for mid in dificultades["por_materia"]:
        if str(mid) not in ids_plan:
            raise ValueError(f"dificultades_generador.json: '{mid}' no existe en el plan")

    esperadas = {
        "promedio_general", "promedio_correlativas", "peor_nota_correlativa",
        "veces_recursada", "n_materias_cuatrimestre", "tasa_aprobacion_materia",
        "avance_carrera",
    }
    faltan = esperadas - set(COLS_FEATURES)
    sobran = set(COLS_FEATURES) - esperadas
    if faltan or sobran:
        raise ValueError(f"features_estudiante.json desalineado. Faltan: {faltan}. Sobran: {sobran}")

def verificar_dag():
    indeg = {str(m["id"]): 0 for m in MATERIAS}
    adj = {str(m["id"]): [] for m in MATERIAS}
    for m in MATERIAS:
        m_id = str(m["id"])
        for c in m["correlativas"]:
            c_str = str(c)
            if c_str not in MAT:
                raise ValueError(f"Correlativa '{c}' de '{m_id}' no existe en el plan")
            adj[c_str].append(m_id)
            indeg[m_id] += 1
    q = deque([n for n, d in indeg.items() if d == 0])
    orden = []
    while q:
        u = q.popleft(); orden.append(u)
        for v in adj[u]:
            indeg[v] -= 1
            if indeg[v] == 0: q.append(v)
    if len(orden) != N_MATERIAS:
        raise ValueError(f"DAG con ciclos: {len(orden)}/{N_MATERIAS} procesadas")
    return orden

def dificultad_de(mid):
    mid_str = str(mid)
    if mid_str in dificultades["por_materia"]:
        return dificultades["por_materia"][mid_str]
    return dificultades["por_anio"][str(MAT[mid_str]["anio"])]

# ---------- Simulación ----------
def sigmoid(x):
    return 1 / (1 + np.exp(-x))

def nota_desde(habilidad, dificultad, ruido):
    base = 6.5 + 1.8 * habilidad - 2.0 * (dificultad - 0.55)
    return float(np.clip(base + RNG.normal(0, 0.9 + ruido), 6, 10))

def generar_estudiante(est_id):
    habilidad  = RNG.normal(0, 1)
    constancia = RNG.normal(0, 1)
    carga_ext  = RNG.normal(0, 1)

    aprobadas = {}   # mid -> nota
    intentos  = {}   # mid -> veces cursada
    filas = []

    for cuat in range(1, MAX_CUATRIMESTRES + 1):
        if len(aprobadas) == N_MATERIAS:
            break

        habilitadas = [
            m for m in MATERIAS
            if str(m["id"]) not in aprobadas
            and all(str(c) in aprobadas for c in m["correlativas"])
        ]
        if not habilitadas:
            break

        n_cursar = int(np.clip(
            round(2.5 + 1.2 * constancia - 0.8 * carga_ext + RNG.normal(0, 0.7)),
            N_CURSAR_MIN, min(N_CURSAR_MAX, len(habilitadas))
        ))
        
        # Si elegimos una sola, RNG.choice puede devolver un array de 1D.
        elegidas = RNG.choice(habilitadas, size=n_cursar, replace=False)

        for m in elegidas:
            mid = str(m["id"])
            dif = dificultad_de(mid)
            notas_corr = [aprobadas[str(c)] for c in m["correlativas"] if str(c) in aprobadas]
            prom_corr = float(np.mean(notas_corr)) if notas_corr else 6.0
            peor_corr = float(np.min(notas_corr)) if notas_corr else 6.0
            recursadas = intentos.get(mid, 0)

            logit = (
                +1.0
                + 0.8 * habilidad
                + 0.45 * (prom_corr - 6.0) / 1.5
                + 0.25 * (peor_corr - 5.5) / 2.0
                - 1.6 * (dif - 0.55)
                - 0.45 * (n_cursar - 2.5)
                - 0.4 * recursadas
                + 0.3 * constancia
                - 0.2 * carga_ext
                + RNG.normal(0, SIGMA_RUIDO)
            )
            p_aprobar = sigmoid(logit)
            aprobo = int(RNG.random() < p_aprobar)

            filas.append(dict(
                estudiante_id=est_id,
                cuatrimestre=cuat,
                materia=int(mid),   # Guardamos como entero para Tomás
                anio_materia=m["anio"],
                promedio_general=round(float(np.mean(list(aprobadas.values()))) if aprobadas else 6.0, 2),
                promedio_correlativas=round(prom_corr, 2),
                peor_nota_correlativa=round(peor_corr, 2),
                veces_recursada=recursadas,
                n_materias_cuatrimestre=n_cursar,
                avance_carrera=round(len(aprobadas) / N_MATERIAS, 3),
                aprobo=aprobo,
            ))

            intentos[mid] = recursadas + 1
            if aprobo:
                aprobadas[mid] = nota_desde(habilidad, dif, SIGMA_RUIDO)

    return filas, {int(mid): round(n, 2) for mid, n in aprobadas.items()}, intentos

# ---------- Main ----------
def main():
    validar()
    orden = verificar_dag()
    print(f"[OK] Plan válido: {N_MATERIAS} materias, DAG sin ciclos.")
    print(f"[OK] Features alineadas: {COLS_FEATURES}")

    todas, estados = [], {}
    for i in range(N_ESTUDIANTES):
        est_id = f"E{i:05d}"
        filas, aprobadas, intentos = generar_estudiante(est_id)
        todas.extend(filas)
        estados[est_id] = {"aprobadas": aprobadas, "intentos": intentos}

    df = pd.DataFrame(todas)

    antes = len(df)
    df = df[df["veces_recursada"] <= 5].reset_index(drop=True)
    print(f"[Limpieza] Eliminadas {antes - len(df)} filas con veces_recursada > 5. Quedan {len(df)}.")

    tasas = df.groupby("materia")["aprobo"].mean().round(3).to_dict()
    df["tasa_aprobacion_materia"] = df["materia"].map(tasas)

    df = df[["estudiante_id", "cuatrimestre", "materia", "anio_materia"]
            + COLS_FEATURES + ["aprobo"]]
    df.to_csv(DATA / "dataset.csv", index=False)

    json.dump(estados, open(DATA / "estudiantes.json", "w"), indent=1, ensure_ascii=False)
    json.dump(tasas, open(DATA / "tasa_aprobacion_observada.json", "w"), indent=1, ensure_ascii=False)

    print(f"\n[Dataset] {len(df)} filas, {N_ESTUDIANTES} estudiantes")
    print(f"[Target ] tasa aprobación global: {df['aprobo'].mean():.3f}")
    print(f"[Tasas  ] min {min(tasas.values()):.2f} / max {max(tasas.values()):.2f}")
    print("\nMaterias con menos datos (cola larga):")
    print(df.groupby("materia").size().sort_values().head(5).to_string())
    extremas = {k: v for k, v in tasas.items() if v < 0.35 or v > 0.90}
    print(f"\nTasas extremas: {extremas if extremas else '  (ninguna)'}")

if __name__ == "__main__":
    main()
