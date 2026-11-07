import json
from pathlib import Path
import pandas as pd

_RUTA = Path(__file__).parent / "data" / "plan_estudios.json"

def cargar_plan():
    materias = json.load(open(_RUTA, encoding="utf-8"))["materias"]
    df = pd.DataFrame(materias).rename(columns={"id": "id_materia"})
    return df.set_index("id_materia")

plan = cargar_plan()