---
title: Crear una API desde cero
tags:
  - backend
  - api
  - fastapi
  - python
  - tutorial
  - diseño
---

La presente nota es un tutorial sencillo de cómo crear una API para una lista
TODO, con las funcionalidades CRUD completas para una tarea (`task`).

El énfasis está en el diseño agregando características, no en una implementación
prolija ni en proponer una solución escalable.

El recorrido va de los requisitos al modelo de datos, y del modelo a una API que
lo soporte; el código es el mínimo necesario para que esa cadena se vea.

El contenido se distribuye entonces de la siguiente manera:

1. [Requisitos](#1-requisitos)
2. [Análisis y diseño de la API](#2-análisis-y-diseño-de-la-api)
3. [Setup del proyecto](#3-setup-del-proyecto)
4. [Creación de la app con FastAPI](#4-creación-de-la-app-con-fastapi)
5. [Funcionalidad de creación de tareas](#5-funcionalidad-de-creación-de-tareas)
6. [Funcionalidad de lectura de una tarea](#6-funcionalidad-de-lectura-de-una-tarea)
7. [Funcionalidad de listado con filtro y paginación](#7-funcionalidad-de-listado-con-filtro-y-paginación)
8. [Funcionalidad de actualización parcial](#8-funcionalidad-de-actualización-parcial)
9. [Funcionalidad de borrado](#9-funcionalidad-de-borrado)
10. [Documentación automática con OpenAPI](#10-documentación-automática-con-openapi)
11. [Capas pendientes para una API en producción](#11-capas-pendientes-para-una-api-en-producción)
12. [Preguntas de entrevista](#12-preguntas-de-entrevista)

## 1. Requisitos

A continuación se propone un conjunto mínimo de características que debe
satisfacer la API, las propiedades y operaciones son las siguientes:

1. Crear una tarea con un nombre y, opcionalmente, descripción y fecha límite.
2. Obtener una tarea por su identificador.
3. Listar las tareas, con paginación y filtro por estado.
4. Actualizar una tarea, cambiando solo algunos de sus campos.
5. Borrar una tarea.

## 2. Análisis y diseño de la API

Con los requisitos definidos, se modela la `task` con las siguientes
propiedades:

- `id` : identificador unico
- `name` : nombre de la tarea, obligatorio
- `description`: texto libre, opcional
- `status`: estado actual
- `due_date`: fecha limite
- `created_at`: fecha de creacion
- `updated_at`: fecha de ultima modificación

Cada acción ahora pasa a traducirse en un endpoint simple, según la convención
REST:

| Endpoint             | Acción               | Éxito | Errores      |
| -------------------- | -------------------- | ----- | ------------ |
| `POST /tasks`        | Crear una tarea      | `201` | `422`        |
| `GET /tasks/{id}`    | Leer una tarea       | `200` | `404`        |
| `GET /tasks`         | Listar las tareas    | `200` | `422`        |
| `PATCH /tasks/{id}`  | Actualizar una tarea | `200` | `404`, `422` |
| `DELETE /tasks/{id}` | Borrar una tarea     | `204` | `404`        |

Los cinco status codes de esta tabla cubren la mayoría de los casos de cualquier
CRUD:

- `200` : Operación exitosa, se responde el resultado
- `201` : Creación de nuevo recurso exitoso
- `204` : Operación exitosa, no hay nada que devolver
- `404` : El recurso no existe
- `422` : El body es correcto pero es invalido para el endpoint

Una decisión del contrato que conviene fijar en esta etapa son:

- el `id`, el `created_at` y el `status` inicial los asigna el servidor y no el
  cliente (si el cliente pudiera enviarlos, dos clientes podrían elegir el mismo
  `id`)

## 3. Setup del proyecto

El proyecto se crea con `uv`, que resuelve las dependencias y administra el
entorno virtual sin pasos manuales.

```bash
# Creando el proyecto y entrando a la carpeta
uv init tasks-api
cd tasks-api

# Agregando las dependencias
uv add fastapi "uvicorn[standard]"
```

La aplicación necesita dos paquetes, cuyo aporte resume la tabla que sigue al
comando de instalación:

- `fastapi` : Permite crear la API
- `uvicorn` : Servidor ASGI, traduce HTTP a JSON

Una vez creado el proyecto tendrá que eliminar y crear archivos/carpetas de
acuerdo a la siguiente estructura:

```text
tasks-api/
├── .python-version
├── README.md
├── pyproject.toml
├── uv.lock
└── app/
    ├── __init__.py
    ├── main.py             # crea la instancia FastAPI y registra los routers
    ├── schemas.py          # declara los modelos IO
    ├── store.py            # declara la db (en este caso sera un diccionario)
    └── routers/
        ├── __init__.py
        └── tasks.py        # declara e implementa los endpoints junto a las acciones
```

## 4. Creación de la app con FastAPI

En el archivo `app/main.py`:

1. Crea la instancia de `FastAPI`
2. Luego crea la ruta `/health` con la respuesta `{"status" : "ok"}`

```python
# app/main.py
from fastapi import FastAPI

app = FastAPI(title="Tasks API")

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

La ruta `health` permite verificar de que el servidor está vivo, se usa siempre
por balanceadores de carga y orquestadores como Kubernetes para decidir si una
instancia recibe tráfico, así que casi toda API en producción tiene una.

Ejecute el siguiente comando en su terminal para iniciar el servidor, el flag
`reload` permite que reiniciar el servidor con cada cambio de codigo:

```bash
uv run uvicorn app.main:app --reload
```

```text
INFO:     Will watch for changes in these directories: ['/home/pqbas/tasks-api']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [109468] using WatchFiles
INFO:     Started server process [109485]
INFO:     Application startup complete.
```

Para validar que el servidor está encendido ejecute la siguiente consulta:

```bash
curl -i http://127.0.0.1:8000/health
```

```text
HTTP/1.1 200 OK
content-type: application/json

{"status":"ok"}
```

## 5. Funcionalidad de creación de tareas

Ahora va a implementar la acción de `crear tareas`, para ello va a necesitar:

1. Declarar los esquemas `TaskCreate` y `Task`
2. Implementar el endpoint `POST /tasks`
3. Validar el endpoint `POST /tasks`

#### 5.1. Declarar los esquemas `TaskCreate` y `Task`

La razón por la que se requiere dos esquemas `TaskCreate` y `Task`, es porque el
cliente no manda el mismo `json` que el servidor devuelve.

- `TaskCreate` lleva tres campos, los que manda el cliente
- `Task` lleva esos tres campos más los cuatro que decide el servidor

Agregue el siguiente código en `app/schemas.py`.

```python
# app/schemas.py
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

Status = Literal["todo", "doing", "done"]


class TaskCreate(BaseModel):
    name: str = Field(min_length=1)
    description: str | None = None
    due_date: datetime | None = None


class Task(BaseModel):
    id: str
    name: str
    description: str | None
    status: Status
    created_at: datetime
    updated_at: datetime | None
    due_date: datetime | None
```

#### 5.2. Implementar el endpoint `POST /tasks`

Cree el diccionario que almacena todas las tareas en `app/store.py`.

```python
# app/store.py
from app.schemas import Task

db: dict[str, Task] = {}
```

Agregue el siguiente código en `app/routers/tasks.py`.

```python
# app/routers/tasks.py
from datetime import datetime, timezone
from uuid import uuid4
from fastapi import APIRouter
from app.schemas import Task, TaskCreate
from app.store import db

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.post("", status_code=201)
def create_task(body: TaskCreate) -> Task:
    task = Task(
        id=str(uuid4()),
        name=body.name,
        description=body.description,
        status="todo",
        created_at=datetime.now(timezone.utc),
        updated_at=None,
        due_date=body.due_date,
    )
    db[task.id] = task
    return task
```

#### 5.3. Validar el endpoint `POST /tasks`

Ejecute los siguientes comandos para validar que la creación responde `201` con
la tarea completa, y `422` cuando falta el nombre.

```bash
curl -i -X POST http://127.0.0.1:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"name": "Comprar leche"}'
```

```http
HTTP/1.1 201 Created
content-type: application/json

{
  "id": "a211f5b3-a524-4b20-8d79-c305cab17ce7",
  "name": "Comprar leche",
  "description": null,
  "status": "todo",
  "created_at": "2026-09-22T18:08:32.632592Z",
  "updated_at": null,
  "due_date": null
}
```

```bash
curl -X POST http://127.0.0.1:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"name": "Escribir la nota", "description": "Tutorial de API"}'
```

```json
{
  "id": "10a79592-0c2f-4ab6-8c0d-f1d79d5173e3",
  "name": "Escribir la nota",
  "description": "Tutorial de API",
  "status": "todo",
  "created_at": "2026-09-22T18:08:32.637555Z",
  "updated_at": null,
  "due_date": null
}
```

```bash
curl -X POST http://127.0.0.1:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"description": "sin nombre"}'
```

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "name"],
      "msg": "Field required",
      "input": { "description": "sin nombre" }
    }
  ]
}
```

## 6. Funcionalidad de lectura de una tarea

Ahora va a implementar la acción de `leer una tarea`, para ello va a necesitar:

1. Implementar el endpoint `GET /tasks/{id}`
2. Validar el endpoint `GET /tasks/{id}`

No hay esquema nuevo que declarar, la respuesta reutiliza `Task`.

#### 6.1. Implementar el endpoint `GET /tasks/{id}`

Agregue el siguiente código en `app/routers/tasks.py`.

```python
# app/routers/tasks.py
from fastapi import APIRouter, HTTPException

...

@router.get("/{task_id}")
def read_task(task_id: str) -> Task:
    task = db.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="task not found")
    return task
```

#### 6.2. Validar el endpoint `GET /tasks/{id}`

Ejecute los siguientes comandos para validar que la lectura devuelve la tarea
con `200`, y `404` cuando el id no existe.

```bash
curl -i http://127.0.0.1:8000/tasks/10a79592-0c2f-4ab6-8c0d-f1d79d5173e3
```

```http
HTTP/1.1 200 OK
content-type: application/json

{
  "id": "10a79592-0c2f-4ab6-8c0d-f1d79d5173e3",
  "name": "Escribir la nota",
  "description": "Tutorial de API",
  "status": "todo",
  "created_at": "2026-09-22T18:08:32.637555Z",
  "updated_at": null,
  "due_date": null
}
```

```bash
curl -i http://127.0.0.1:8000/tasks/no-existe
```

```text
HTTP/1.1 404 Not Found
content-type: application/json

{"detail":"task not found"}
```

## 7. Funcionalidad de listado con filtro y paginación

Ahora va a implementar la acción de `listar las tareas`, para ello va a
necesitar:

1. Declarar el esquema `TaskPage`
2. Implementar el endpoint `GET /tasks`
3. Validar el endpoint `GET /tasks`

#### 7.1. Declarar el esquema `TaskPage`

`TaskPage` envuelve el resultado, las tareas de la página en `items` y el total
sin paginar en `total`.

Agregue el siguiente código al final de `app/schemas.py`.

```python
# app/schemas.py, al final del archivo
class TaskPage(BaseModel):
    items: list[Task]
    total: int
```

#### 7.2. Implementar el endpoint `GET /tasks`

Agregue el siguiente código en `app/routers/tasks.py`.

```python
# app/routers/tasks.py
from app.schemas import Status, Task, TaskCreate, TaskPage

...

@router.get("")
def list_tasks(
    status: Status | None = None,
    limit: int = 20,
    offset: int = 0,
) -> TaskPage:
    items = list(db.values())
    if status is not None:
        items = [task for task in items if task.status == status]
    return TaskPage(items=items[offset : offset + limit], total=len(items))
```

| Parámetro | Por defecto | Efecto                                 |
| --------- | ----------- | -------------------------------------- |
| `status`  | sin filtro  | Devuelve solo las tareas en ese estado |
| `limit`   | `20`        | Cuántos elementos trae la página       |
| `offset`  | `0`         | Desde qué posición empieza la página   |

#### 7.3. Validar el endpoint `GET /tasks`

Ejecute los siguientes comandos para validar que el listado pagina con `limit` y
rechaza con `422` un estado fuera del conjunto.

```bash
curl "http://127.0.0.1:8000/tasks?limit=1"
```

```json
{
  "items": [
    {
      "id": "a211f5b3-a524-4b20-8d79-c305cab17ce7",
      "name": "Comprar leche",
      "description": null,
      "status": "todo",
      "created_at": "2026-09-22T18:08:32.632592Z",
      "updated_at": null,
      "due_date": null
    }
  ],
  "total": 2
}
```

```bash
curl "http://127.0.0.1:8000/tasks?status=pendiente"
```

```json
{
  "detail": [
    {
      "type": "literal_error",
      "loc": ["query", "status"],
      "msg": "Input should be 'todo', 'doing' or 'done'",
      "input": "pendiente",
      "ctx": { "expected": "'todo', 'doing' or 'done'" }
    }
  ]
}
```

## 8. Funcionalidad de actualización parcial

Ahora va a implementar la acción de `actualizar una tarea`, para ello va a
necesitar:

1. Declarar el esquema `TaskUpdate`
2. Implementar el endpoint `PATCH /tasks/{id}`
3. Validar el endpoint `PATCH /tasks/{id}`

#### 8.1. Declarar el esquema `TaskUpdate`

`TaskUpdate` repite los campos que el cliente puede cambiar, todos opcionales,
porque el `PATCH` modifica solo los que llegan.

Agregue el siguiente código al final de `app/schemas.py`.

```python
# app/schemas.py, al final del archivo
class TaskUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    description: str | None = None
    status: Status | None = None
    due_date: datetime | None = None
```

#### 8.2. Implementar el endpoint `PATCH /tasks/{id}`

Agregue el siguiente código en `app/routers/tasks.py`.

```python
# app/routers/tasks.py
from app.schemas import Status, Task, TaskCreate, TaskPage, TaskUpdate

...

@router.patch("/{task_id}")
def update_task(task_id: str, body: TaskUpdate) -> Task:
    task = db.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="task not found")

    changes = body.model_dump(exclude_unset=True)
    changes["updated_at"] = datetime.now(timezone.utc)

    updated = task.model_copy(update=changes)
    db[task_id] = updated
    return updated
```

| Body enviado            | Qué pasa con `description`    |
| ----------------------- | ----------------------------- |
| `{"status": "done"}`    | Se conserva el valor anterior |
| `{"description": null}` | Se borra y queda en nulo      |

#### 8.3. Validar el endpoint `PATCH /tasks/{id}`

Ejecute los siguientes comandos para validar que la actualización parcial cambia
solo los campos enviados, y rechaza con `422` un estado inválido.

```bash
curl -X PATCH http://127.0.0.1:8000/tasks/10a79592-0c2f-4ab6-8c0d-f1d79d5173e3 \
  -H "Content-Type: application/json" \
  -d '{"status": "doing"}'
```

```json
{
  "id": "10a79592-0c2f-4ab6-8c0d-f1d79d5173e3",
  "name": "Escribir la nota",
  "description": "Tutorial de API",
  "status": "doing",
  "created_at": "2026-09-22T18:08:32.637555Z",
  "updated_at": "2026-09-22T18:08:32.684988Z",
  "due_date": null
}
```

```bash
curl -X PATCH http://127.0.0.1:8000/tasks/10a79592-0c2f-4ab6-8c0d-f1d79d5173e3 \
  -H "Content-Type: application/json" \
  -d '{"status": "terminado"}'
```

```json
{
  "detail": [
    {
      "type": "literal_error",
      "loc": ["body", "status"],
      "msg": "Input should be 'todo', 'doing' or 'done'",
      "input": "terminado",
      "ctx": { "expected": "'todo', 'doing' or 'done'" }
    }
  ]
}
```

## 9. Funcionalidad de borrado

Ahora va a implementar la acción de `borrar una tarea`, para ello va a
necesitar:

1. Implementar el endpoint `DELETE /tasks/{id}`
2. Validar el endpoint `DELETE /tasks/{id}`

No hay esquema nuevo que declarar, el borrado responde `204` sin cuerpo.

#### 9.1. Implementar el endpoint `DELETE /tasks/{id}`

Agregue el siguiente código al final de `app/routers/tasks.py`.

```python
# app/routers/tasks.py, al final del archivo
@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: str) -> None:
    if task_id not in db:
        raise HTTPException(status_code=404, detail="task not found")
    del db[task_id]
```

#### 9.2. Validar el endpoint `DELETE /tasks/{id}`

Ejecute los siguientes comandos para validar que el borrado responde `204`, y
`404` al repetirlo sobre el mismo id.

```bash
curl -i -X DELETE http://127.0.0.1:8000/tasks/10a79592-0c2f-4ab6-8c0d-f1d79d5173e3
```

```text
HTTP/1.1 204 No Content
```

```bash
curl -i -X DELETE http://127.0.0.1:8000/tasks/10a79592-0c2f-4ab6-8c0d-f1d79d5173e3
```

```text
HTTP/1.1 404 Not Found
content-type: application/json

{"detail":"task not found"}
```

## 10. Documentación automática con OpenAPI

| Ruta            | Qué contiene                                    |
| --------------- | ----------------------------------------------- |
| `/docs`         | Interfaz web para leer y probar los endpoints   |
| `/openapi.json` | El esquema OpenAPI crudo, para generar clientes |

## 11. Capas pendientes para una API en producción

## 12. Preguntas de entrevista

Las siguientes preguntas son las que un entrevistador puede hacer sobre lo que
se construyó en esta nota.

#### 12.1. Diseño de la API y HTTP

| Pregunta                                                                     | Respuesta corta                                                                                          |
| ---------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| ¿Por qué `POST /tasks` responde `201` y `DELETE /tasks/{id}` responde `204`? | `201` dice que se creó un recurso, `204` que la operación salió bien y no hay cuerpo que devolver         |
| ¿Qué diferencia hay entre `PUT` y `PATCH`?                                   | `PUT` reemplaza el recurso completo, `PATCH` solo los campos que llegan                                  |
| ¿Cuáles de los cinco endpoints son idempotentes?                             | `GET`, `PATCH` y `DELETE`, porque repetirlos deja la misma fila; `POST` no, cada llamada crea otra tarea  |
| ¿Por qué `DELETE` repetido responde `404` si es idempotente?                  | La idempotencia es sobre el estado final, no sobre el status de la respuesta                             |
| ¿Por qué `GET /tasks/{id}` devuelve `404` y no `200` con `null`?             | El status es parte del contrato, y pedir algo que no existe no es una respuesta exitosa                  |
| ¿Por qué el listado devuelve `total` además de `items`?                      | Con `limit` el cliente no puede saber cuántas tareas hay, y lo necesita para paginar                     |

#### 12.2. Esquemas y validación

| Pregunta                                                            | Respuesta corta                                                                             |
| ------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| ¿Por qué se necesitan dos esquemas, `TaskCreate` y `Task`?          | El cliente no manda `id`, `status` ni `created_at`, esos los genera el servidor              |
| ¿Qué status responde FastAPI si el cuerpo no cumple el esquema?     | `422`, que Pydantic levanta antes de entrar a la función del endpoint                        |
| ¿Cuándo usarías `400` en vez de `422`?                              | `422` es validación de forma, `400` es la que eliges para una regla de negocio               |
| ¿Cómo se distingue un campo ausente de un campo en `null` en el `PATCH`? | Con `model_dump(exclude_unset=True)`, que solo incluye los campos que el cliente mandó  |
| ¿Por qué `Status` es un `Literal` y no un `str`?                    | Restringe los tres valores válidos en la validación y además los publica en el OpenAPI       |
| ¿Dónde se valida que el nombre no llegue vacío?                     | En `Field(min_length=1)` del esquema `TaskCreate`                                            |

#### 12.3. Implementación con FastAPI

| Pregunta                                                            | Respuesta corta                                                                           |
| ------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| ¿Qué aporta un `APIRouter` frente a colgar los endpoints de `app`?  | Agrupa las rutas con un prefijo y unos tags, y deja montar el módulo con `include_router`  |
| ¿De dónde sale `/docs` sin escribir documentación?                  | Del esquema OpenAPI que FastAPI genera leyendo los tipos de cada endpoint                 |
| ¿Qué hace el tipo de retorno `-> Task` además de documentar?        | FastAPI valida y serializa la respuesta con ese esquema                                   |
| ¿Para qué sirve la ruta `/health`?                                  | Los balanceadores y orquestadores deciden con ella si la instancia recibe tráfico         |
| ¿Por qué `uvicorn --reload` no se usa en producción?                | Vigila los archivos en disco, en producción se levantan varios workers sin recarga        |
| ¿Qué problema tiene guardar las tareas en un diccionario?           | Se pierden al reiniciar y cada worker tendría el suyo, que es lo que resuelve la nota siguiente |
