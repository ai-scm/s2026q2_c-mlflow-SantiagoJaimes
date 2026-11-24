# Taller hands-on: MLflow + Docker, del dato al modelo desplegado

Material del micro-assignment del semillero. Sigue el tutorial [Machine Learning Model Serving for Newbies with MLflow](https://towardsdatascience.com/machine-learning-model-serving-for-newbies-with-mlflow-76f9f0ac3cb2/) y su repositorio [mtpatter/mlflow-tutorial](https://github.com/mtpatter/mlflow-tutorial): se entrena un clasificador Random Forest sobre el dataset de cáncer de mama de scikit-learn, se registra y versiona en MLflow y se despliega como una API de predicción.

El modelo es solo el vehículo pedagógico. El objetivo es ver cómo los datos se convierten en un modelo, cómo se versiona y cómo se despliega, y relacionarlo con el ciclo de vida de los datos visto antes.

## Lineamientos

- **Local**: solo se instalan dependencias para explorar los datos (`explore_data.py`).
- **Docker**: el servidor MLflow, el entrenamiento, el tracking, el registro del modelo y el serving corren en contenedores.

## Requisitos

- Linux con Docker Engine y el plugin Docker Compose v2 (`docker compose version`).
- Python 3.11 o superior, solo para la exploración de datos.

## Paso a paso (Linux)

### 1. Explorar los datos (local)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-explore.txt
python explore_data.py
```

### 2. Modelo sin registry

Entrena el modelo, lo guarda en la carpeta `clf-model/` y lo sirve en el puerto 1234.

```bash
docker compose -f docker-compose-no-registry.yml up --build
```

Cuando aparezca `Uvicorn running on http://0.0.0.0:1234`, en otra terminal:

```bash
./predict.sh test.csv
```

Para terminar: `Ctrl+C` en la primera terminal y luego:

```bash
docker compose -f docker-compose-no-registry.yml down
```

### 3. Modelo con registry (flujo completo)

Levanta el servidor MLflow, entrena y registra el modelo con el alias `Staging` y lo sirve.

```bash
docker compose -f docker-compose.yml up --build
```

- Interfaz de MLflow: http://localhost:8000 (experimento `my-experiment` y modelo `clf-model` en la pestaña **Models**).
- API del modelo: http://localhost:1234/invocations

En otra terminal:

```bash
./predict.sh test.csv
```

Cada vez que se vuelve a levantar este flujo se registra una versión nueva del modelo y el alias `Staging` pasa a apuntar a ella.

Para terminar:

```bash
docker compose -f docker-compose.yml down
```

### 4. Solo el servidor MLflow (opcional)

```bash
docker compose -f compose-server.yml up --build
```

## Predicciones

```bash
./predict.sh test.csv
```

equivale a:

```bash
curl http://localhost:1234/invocations -H 'Content-Type: text/csv' --data-binary @test.csv
```

La respuesta es una lista con la probabilidad de que cada fila de `test.csv` sea benigna (clase 1). Valores cercanos a 0 indican maligno.

```json
{"predictions": [0.5074, 0.0, 0.9837, 0.986, 0.9913, 0.0, 1.0, ...]}
```

La API no tiene página de inicio: abrir http://localhost:1234 en el navegador responde `404`. Para comprobar que está viva: http://localhost:1234/ping

## Empezar de cero

Los contenedores escriben en la carpeta del proyecto (`clf-model/`, `mlflow.db`, `mlflow-artifact-root/`, `test.csv`). En Linux esos archivos quedan con dueño `root`, por eso se borran con `sudo`:

```bash
docker compose -f docker-compose.yml down
docker compose -f docker-compose-no-registry.yml down
sudo rm -rf clf-model mlflow.db mlflow-artifact-root test.csv
```

Si no se borra `clf-model/`, el flujo sin registry no la sobrescribe: muestra `Error saving model at path clf-model ... Does it already exist?` y sirve el modelo anterior.

## Archivos

| Archivo | Qué hace |
|---|---|
| `explore_data.py` | Exploración local del dataset |
| `requirements-explore.txt` | Dependencias locales para la exploración |
| `clf-train.py` | Entrena y guarda el modelo en una carpeta (sin registry) |
| `clf-train-registry.py` | Entrena, registra métricas y modelo en MLflow y asigna el alias `Staging` |
| `runServer.sh` | Arranca el servidor MLflow (SQLite + carpeta de artefactos) |
| `serveModel.sh` | Sirve un modelo en el puerto 1234 |
| `predict.sh` | Envía un CSV a la API |
| `Dockerfile` | Imagen con Python 3.12 y las dependencias de `requirements.txt` |
| `docker-compose.yml` | Servidor + entrenamiento con registry + serving |
| `docker-compose-no-registry.yml` | Entrenamiento + serving sin servidor |
| `compose-server.yml` | Solo el servidor MLflow |
| `requirements.txt` | Dependencias de la imagen (MLflow 2.16.2) |

## Documentación

1. [Guía del taller paso a paso](docs/01-guia-del-taller.md): agenda de 2 horas y qué observar en cada paso.
2. [Ciclo de vida de los datos frente al del modelo](docs/02-ciclo-de-vida.md): qué se mantiene, qué cambia y qué se amplía.
3. [Conceptos de MLflow y puente a AWS](docs/03-conceptos-mlflow-y-aws.md).

## Lecturas complementarias

- [Introducción práctica a MLflow](https://medium.com/@kevinnjagi83/mlflow-tutorial-63a9ab1a220d)
- [Flujo MLOps en entornos empresariales (AWS + Azure)](https://docs.aws.amazon.com/es_es/prescriptive-guidance/latest/patterns/build-an-mlops-workflow-by-using-amazon-sagemaker-and-azure-devops.html)
- [Repositorio con ejemplo completo MLflow + Docker](https://github.com/mtpatter/mlflow-tutorial)
