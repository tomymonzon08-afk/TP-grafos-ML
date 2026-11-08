import pandas as pd
import joblib
import numpy as np
from pathlib import Path
from sklearn.model_selection import GroupShuffleSplit, GridSearchCV, GroupKFold
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (confusion_matrix, precision_score, recall_score, f1_score, log_loss)


if __name__ == "__main__":

    df = pd.read_csv(Path(__file__).parent / "data" / "dataset.csv")

    #print (df.shape)

    #print (df["estudiante_id"].nunique())

    #print(df["aprobo"].mean())

    #print(df.isna().sum())

    #print(df.corr(numeric_only=True)["aprobo"])

    #print(df.groupby("materia").agg(
    #    tasa_columna=("tasa_aprobacion_materia", "first"),
    #    tasa_real=("aprobo", "mean"),
    #))
    #eleccion de variables
    NUMERICAS = ["promedio_general",
                "promedio_correlativas", "peor_nota_correlativa",
                "veces_recursada", "n_materias_cuatrimestre", "avance_carrera"]
    CATEGORICAS = ["materia"]

    X = df[NUMERICAS + CATEGORICAS]

    y = df["aprobo"]

    #División train test

    grupos = df["estudiante_id"] 

    gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)

    idx_train, idx_test = next(gss.split(X, y, groups=grupos))

    X_train = X.iloc[idx_train]
    X_test  = X.iloc[idx_test]
    y_train = y.iloc[idx_train]
    y_test  = y.iloc[idx_test]

    est_train = set(grupos.iloc[idx_train])
    est_test  = set(grupos.iloc[idx_test])

    #assert len(est_train & est_test) == 0, "hay estudiantes repetidos"

    #print(f"Train: {len(X_train)} filas, {len(est_train)} estudiantes")
    #print(f"Test:  {len(X_test)} filas, {len(est_test)} estudiantes")
    #print(f"% aprobó en train: {y_train.mean():.3f}")
    #print(f"% aprobó en test:  {y_test.mean():.3f}")

    #preparación y entrenamiento

    pre = ColumnTransformer([
        ("num", StandardScaler(), NUMERICAS),                                 
        ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAS),    
    ])

    pipe = Pipeline([
        ("pre", pre),
        ("clf", LogisticRegression(max_iter=2000)),
    ])

    pipe.fit(X_train, y_train)   

    #print(f"Accuracy train: {pipe.score(X_train, y_train):.3f}")
    #print(f"Accuracy test:  {pipe.score(X_test, y_test):.3f}")

    #medición de hiperparametros

    g_train = grupos.iloc[idx_train]          

    grilla = {"clf__C": [0.001, 0.01, 0.1, 1, 10, 100]}

    busqueda = GridSearchCV(
        pipe,
        grilla,
        cv=GroupKFold(n_splits=5),
        scoring="neg_log_loss",                        
    )

    busqueda.fit(X_train, y_train, groups=g_train)  

    #print(busqueda.best_params_)
    print(busqueda.best_score_)

    #res = pd.DataFrame(busqueda.cv_results_)
    #print(res[["param_clf__C", "mean_test_score", "std_test_score"]])

    #Evaluación de Test

    modelo = busqueda.best_estimator_
    proba = modelo.predict_proba(X_test)[:, 1]  

    def evaluar(modelo):

        umbrales = [0.3,0.4,0.5,0.6,0.7,0.8]

        for i in umbrales: 
            pred = (proba >= i).astype(int)             
            print(confusion_matrix(y_test, pred))
            print("precision:", precision_score(y_test, pred))
            print("recall:   ", recall_score(y_test, pred))
            print("f1:       ", f1_score(y_test, pred))


    #De esto asumo que el mejor umbral es 0.7
    #prefiero que haya más casos en los que el modelo predijo que iba a desaprobar
    #que casos en los que el modelo dijo que iba a aprobar y desaprobo. 
    #No elijo 0.8 porque ya son demasiado casos falsos negativos
    #Pero como a nosotros no nos importa acá si el alumno va a aprobar o no ,si no que las probabilidades, 
    #no damos mucho caso por ahora a esto
    #evaluar(modelo) 
    print("log loss: ", log_loss(y_test, proba))  

    #chequeo de probabilidades

    tramos = pd.cut(proba, bins=np.linspace(0, 1, 11))

    calib = pd.DataFrame({
        "tramo": tramos,
        "prob_predicha": proba,
        "real": y_test.values,
    }).groupby("tramo", observed=True).agg(
        n=("real", "size"),
        prob_predicha=("prob_predicha", "mean"),
        tasa_real=("real", "mean"),
    )
    #print(calib.round(3))

    #Interpretación del modelo con los coeficientes

    nombres = modelo.named_steps["pre"].get_feature_names_out()
    coefs = pd.Series(modelo.named_steps["clf"].coef_[0], index=nombres)
    print(coefs[[n for n in nombres if n.startswith("num__")]].sort_values())


    #num__veces_recursada           -0.349663
    #num__n_materias_cuatrimestre   -0.206508
    #num__anio_materia              -0.018181
    #num__avance_carrera             0.082631
    #num__peor_nota_correlativa      0.230395
    #num__promedio_correlativas      0.403291
    #num__promedio_general           0.477423

    joblib.dump(modelo, "modelo_aprobacion.joblib")