# 3. Conceptos de MLflow y puente a AWS

## Servidor de tracking

`runServer.sh` arranca el servidor con dos almacenes:

| Almacén | Qué guarda | En este proyecto |
|---|---|---|
| Backend store | Experimentos, runs, métricas y Model Registry | `mlflow.db` (SQLite) |
| Artifact store | Modelos y archivos | `mlflow-artifact-root/` |

## Experimentos y runs

- **Experimento**: agrupa los intentos sobre un mismo problema (`my-experiment`).
- **Run**: una ejecución de entrenamiento. Guarda métricas (`accuracy_train`, `accuracy_test`) y artefactos (el modelo).

## Formato de modelo MLflow

Un modelo MLflow es una carpeta (`clf-model/` en el flujo sin registry) con:

- `MLmodel`: describe el modelo y sus **flavors**: `sklearn` para cargarlo como objeto de scikit-learn y `python_function` para servirlo de forma genérica.
- `model.pkl`: el modelo serializado.
- `requirements.txt`, `python_env.yaml` y `conda.yaml`: las dependencias.

En `clf-train-registry.py`, `input_example` permite que MLflow infiera la **firma** del modelo: las columnas y tipos que espera recibir.

## Model Registry

- **Modelo registrado**: un nombre (`clf-model`).
- **Versión**: cada `mlflow.register_model(...)` crea una versión nueva.
- **Alias**: un nombre que apunta a una versión (`Staging`). El servidor de predicción usa `models:/clf-model@Staging`, así que para desplegar otra versión basta con mover el alias.

| URI | Qué carga |
|---|---|
| `clf-model` | La carpeta local del flujo sin registry |
| `runs:/<run_id>/clf-model` | El modelo guardado en un run |
| `models:/clf-model/2` | La versión 2 |
| `models:/clf-model@Staging` | La versión a la que apunta el alias |

## Serving

```bash
mlflow models serve -m models:/clf-model@Staging -p 1234 -h 0.0.0.0 --env-manager local
```

- `GET /ping`: comprueba que el servicio está vivo.
- `POST /invocations`: recibe CSV (`text/csv`) o JSON (`application/json`) y devuelve `{"predictions": [...]}`.
- `--env-manager local`: usa las librerías ya instaladas en la imagen Docker.
- El alias se resuelve al arrancar el servicio.

## Puente a AWS

| En el taller | En AWS |
|---|---|
| `docker compose` | Amazon SageMaker Pipelines, AWS Step Functions o CodePipeline |
| Imagen construida con el `Dockerfile` | Imagen en Amazon ECR |
| Servidor MLflow (`server`) | MLflow administrado en Amazon SageMaker AI |
| `mlflow-artifact-root/` | Bucket de Amazon S3 |
| Entrenamiento (`trainmodel`) | SageMaker Training Jobs |
| Alias `Staging` | MLflow Model Registry sincronizado con SageMaker Model Registry |
| Serving (`servemodel`) | Endpoint de SageMaker AI, o contenedor en Amazon ECS con Fargate |
| Logs y healthcheck | Amazon CloudWatch |

En MLflow administrado de SageMaker AI, AWS hospeda el servidor y la base de metadatos; los artefactos quedan en un bucket de S3 de tu cuenta; el acceso se controla con IAM; y los modelos registrados pueden sincronizarse con SageMaker Model Registry y desplegarse en endpoints de SageMaker AI.

Referencia: [Managed MLflow on Amazon SageMaker AI](https://docs.aws.amazon.com/sagemaker/latest/dg/mlflow.html)
