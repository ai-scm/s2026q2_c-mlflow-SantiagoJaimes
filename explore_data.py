#!/usr/bin/env python
"""Exploracion local del dataset (unico paso que corre fuera de Docker).

Responde las preguntas que conviene hacerse antes de entrenar:
cuantos registros hay, que columnas, si faltan datos, como esta
balanceada la variable objetivo y que variables se relacionan mas con ella.

Uso:
    python -m venv .venv && source .venv/bin/activate
    pip install -r requirements-explore.txt
    python explore_data.py
"""

import pandas as pd
from sklearn.datasets import load_breast_cancer


def main():
    # Ingestion: el dataset viene incluido en scikit-learn, no requiere descarga.
    raw = load_breast_cancer(as_frame=True)
    df = raw.frame

    print("== Forma del dataset ==")
    print(f"{df.shape[0]} filas x {df.shape[1]} columnas "
          f"({df.shape[1] - 1} variables + 'target')\n")

    print("== Calidad: valores faltantes ==")
    missing = int(df.isna().sum().sum())
    print(f"Total de valores faltantes: {missing}\n")

    print("== Variable objetivo ==")
    counts = df["target"].value_counts().sort_index()
    for value, n in counts.items():
        name = raw.target_names[value]
        print(f"  {value} = {name:<9} {n:>4} registros ({n / len(df):.1%})")
    print("  Hay desbalance moderado: por eso el modelo usa class_weight='balanced'\n")

    print("== Escalas de las variables (motivo del StandardScaler) ==")
    desc = df.drop(columns="target").describe().T[["mean", "min", "max"]]
    print(desc.sort_values("max", ascending=False).head(5).round(2).to_string())
    print("  ...")
    print(desc.sort_values("max").head(3).round(4).to_string(), "\n")

    print("== Variables mas correlacionadas con el target ==")
    corr = df.corr(numeric_only=True)["target"].drop("target")
    top = corr.abs().sort_values(ascending=False).head(8)
    for col in top.index:
        print(f"  {col:<25} {corr[col]:+.3f}")


if __name__ == "__main__":
    main()
