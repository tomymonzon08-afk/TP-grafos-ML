# TP-grafos-ML
Trabajo práctico de Tomás Monzón y Morena Randisi sobre MAchine Learning y Teoría de grafos

Instrucciones de Instalación:

Desde la raíz del repositorio:

1)Instalar dependencias de Python: python -m pip install fastapi uvicorn pandas scikit-learn networkx joblib matplotlib.
Generar el dataset: python -m backend.data.generador.
Entrenar el modelo: python -m backend.prediccion.
Levantar la API: python -m uvicorn backend.api:app --reload (queda en http://localhost:8000).
En otra terminal: cd frontend, npm install, npm run dev (queda en http://localhost:5173).
Todos los comandos de Python se ejecutan desde la raíz del repositorio.
