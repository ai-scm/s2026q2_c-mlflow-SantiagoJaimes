# 1. Guía del taller paso a paso (2 horas)

## Agenda

| Tiempo | Bloque | Etapa del ciclo de vida |
|---|---|---|
| 0:00 - 0:10 | Contexto: del ciclo de datos al ciclo del modelo | - |
| 0:10 - 0:25 | Exploración local de los datos | Ingestión y entendimiento del dato |
| 0:25 - 0:45 | Modelo sin registry | Entrenamiento, despliegue, inferencia |
| 0:45 - 1:20 | Modelo con registry | Validación, registro, despliegue, inferencia |
| 1:20 - 1:40 | Segunda versión del modelo | Versionado |
| 1:40 - 1:55 | Discusión y puente a AWS | - |
| 1:55 - 2:00 | Cierre y limpieza | - |

## 0:00 - 0:10 Contexto

Un modelo es un producto de datos: pasa por ingestión, transformación y consumo como cualquier dato, pero además se evalúa, se versiona y se despliega como un servicio. Ver [02-ciclo-de-vida.md](02-ciclo-de-vida.md).

## 0:10 - 0:25 Exploración local de los datos

Es el único paso que corre fuera de Docker.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-explore.txt
python explore_data.py
```

Qué observar:

- 569 registros, 30 variables numéricas y ningún valor faltante.
- La clase objetivo está desbalanceada (63 % benigno, 37 % maligno). Por eso el modelo usa `class_weight='balanced'`.
- Las variables tienen escalas muy distintas (áreas en miles, otras en milésimas). Por eso el pipeline incluye `StandardScaler`.

## 0:25 - 0:45 Modelo sin registry

```bash
docker compose -f docker-compose-no-registry.yml up --build
```

Qué pasa:

1. El servicio `trainmodel` ejecuta `clf-train.py`: carga el dataset, lo divide 80/20, escribe las filas de prueba en `test.csv`, entrena el pipeline (escalado + Random Forest de 100 árboles) y lo guarda en formato MLflow en la carpeta `clf-model/`.
2. Cuando `trainmodel` termina bien, el servicio `servemodel` ejecuta `serveModel.sh clf-model` y expone el modelo en el puerto 1234.

En otra terminal:

```bash
./predict.sh test.csv
```

Qué observar:

- La carpeta `clf-model/`. El archivo `MLmodel` describe el modelo: sus flavors (`python_function` y `sklearn`), la versión de MLflow y las dependencias (`requirements.txt`, `python_env.yaml`).
- La respuesta: una probabilidad por fila de `test.csv`. El script sobrescribe `predict` para que devuelva la probabilidad de la clase 1 (benigno) en lugar de 0 o 1.
- La limitación: no hay historial. Si se vuelve a entrenar, no queda registro de las métricas ni de la versión anterior. Esa es la motivación del registry.

Cerrar con `Ctrl+C` y:

```bash
docker compose -f docker-compose-no-registry.yml down
```

## 0:45 - 1:20 Modelo con registry

```bash
docker compose -f docker-compose.yml up --build
```

Compose levanta tres servicios en orden:

1. `server` (`runServer.sh`): servidor MLflow con base de datos SQLite (`mlflow.db`) y carpeta de artefactos (`mlflow-artifact-root/`). Está en el puerto 5000 del contenedor, publicado como 8000 en tu máquina.
2. `trainmodel` espera a que el healthcheck del servidor responda y ejecuta `clf-train-registry.py`: entrena, registra las métricas `accuracy_train` y `accuracy_test` en el experimento `my-experiment`, guarda el modelo, lo registra como una versión de `clf-model` y le asigna el alias `Staging`.
3. `servemodel` espera a que `trainmodel` termine bien y sirve `models:/clf-model@Staging` en el puerto 1234.

Recorrido por la interfaz en http://localhost:8000:

1. **Experiments > my-experiment**: un run por entrenamiento. Al abrirlo se ven las métricas y, en **Artifacts**, la carpeta del modelo con su `MLmodel`.
2. **Models > clf-model**: las versiones registradas, la descripción y el alias `Staging`.

Probar la API en otra terminal:

```bash
./predict.sh test.csv
```

El servidor de predicción no conoce el número de versión: pide "la versión con alias `Staging`". Para desplegar otra versión basta con mover el alias.

## 1:20 - 1:40 Segunda versión del modelo

Detener y volver a levantar el flujo completo:

```bash
docker compose -f docker-compose.yml down
docker compose -f docker-compose.yml up
```

Como `mlflow.db` y `mlflow-artifact-root/` quedaron en la carpeta del proyecto, el servidor conserva lo anterior. El entrenamiento crea la versión 2 de `clf-model` y mueve `Staging` hacia ella. En la interfaz se ven los dos runs y las dos versiones; se pueden seleccionar los runs y pulsar **Compare** para comparar métricas.

## 1:40 - 1:55 Discusión

- ¿Qué parte del código corresponde a la ingestión, cuál a la transformación y cuál al consumo?
- ¿Por qué el escalado va dentro del pipeline del modelo y no como un paso aparte?
- ¿Qué diferencia hay entre registrar una versión y desplegarla?
- ¿Qué pasaría si los datos de producción cambian con el tiempo? ¿Qué parte de este proyecto lo detectaría?
- ¿Qué servicio de AWS reemplazaría cada componente? Ver [03-conceptos-mlflow-y-aws.md](03-conceptos-mlflow-y-aws.md).

## 1:55 - 2:00 Cierre y limpieza

```bash
docker compose -f docker-compose.yml down
sudo rm -rf clf-model mlflow.db mlflow-artifact-root test.csv
```

En Linux los archivos que crean los contenedores quedan con dueño `root`, por eso se borran con `sudo`.
