---
title: Conectar una API a una base de datos
tags:
  - backend
  - api
  - fastapi
  - sqlite
  - postgresql
  - sql
  - python
  - tutorial
---

La presente nota continúa el tutorial de
[[Backend/crear-una-api|crear una API desde cero]] reemplazando el diccionario
en memoria por una base de datos SQLite, sin cambiar el contrato de los
endpoints.

El énfasis está en el recorrido completo, de los requisitos nuevos al diseño, y
del diseño a los cambios concretos en cada endpoint.

El contenido se distribuye entonces de la siguiente manera:

1. [Requisitos](#1-requisitos)
2. [Análisis y diseño de la base de datos](#2-análisis-y-diseño-de-la-base-de-datos)
3. [Setup de la base de datos](#3-setup-de-la-base-de-datos)
4. [Conexión a la base con sqlite3](#4-conexión-a-la-base-con-sqlite3)
5. [Creación de la tabla con SQL](#5-creación-de-la-tabla-con-sql)
6. [Funcionalidad de creación de tareas](#6-funcionalidad-de-creación-de-tareas)
7. [Funcionalidad de lectura de una tarea](#7-funcionalidad-de-lectura-de-una-tarea)
8. [Funcionalidad de listado con filtro y paginación](#8-funcionalidad-de-listado-con-filtro-y-paginación)
9. [Funcionalidad de actualización parcial](#9-funcionalidad-de-actualización-parcial)
10. [Funcionalidad de borrado](#10-funcionalidad-de-borrado)
11. [Validar que los datos sobreviven al reinicio](#11-validar-que-los-datos-sobreviven-al-reinicio)
12. [Migrar a PostgreSQL](#12-migrar-a-postgresql)
13. [Preguntas de entrevista](#13-preguntas-de-entrevista)

## 1. Requisitos

El diccionario `db` del tutorial anterior tiene dos límites:

- Los datos viven mientras el servidor se encuentra encendido
- No se pueden compartir con otros procesos ni con otros servidores

A continuación se propone el conjunto mínimo de características que debe
satisfacer el almacenamiento:

1. Las tareas creadas siguen ahí después de reiniciar el servidor.
2. Dos procesos del servidor leen y escriben las mismas tareas.
3. Las tareas se pueden leer sin pasar por la API.
4. La estructura del almacenamiento queda escrita en el repositorio.
5. El contrato de los endpoints no cambia.

## 2. Análisis y diseño de la base de datos

La `task` se modela como una tabla:

| Columna       | Tipo   | Obligatorio | Notas                                |
| ------------- | ------ | ----------- | ------------------------------------ |
| `id`          | `TEXT` | sí          | llave primaria (`PK`)                |
| `name`        | `TEXT` | sí          |                                      |
| `description` | `TEXT` | no          |                                      |
| `status`      | `TEXT` | sí          | con índice, el listado filtra por él |
| `created_at`  | `TEXT` | sí          | formato ISO 8601                     |
| `updated_at`  | `TEXT` | no          | formato ISO 8601                     |
| `due_date`    | `TEXT` | no          | formato ISO 8601                     |

Observaciones:

- sqlite solo usa NULL, INTEGER, TEXT, REAL, BLOB
- las fechas se guardan en formato TEXT en formato ISO
- La tarea tiene propiedades que la definen y que solo caracterízan:
  - `nombre`, `id`, `status`, `crated_at` definen la tarea
  - `due_date`, `updated_at`, `description` caracterizan pero no definen

## 3. Setup de la base de datos

Agregue el archivo que se muestra en verde:

```diff
 tasks-api/
 ├── .python-version
 ├── README.md
+├── schema.sql
 ├── pyproject.toml
 ├── uv.lock
 ├── app/
 │   ├── __init__.py
 │   ├── main.py
 │   ├── schemas.py
 │   ├── store.py
 │   └── routers/
 │       ├── __init__.py
 │       └── tasks.py
```

## 4. Creación de la tabla con SQL

Agregue el siguiente código en `schema.sql`.

```sql
-- schema.sql
CREATE TABLE IF NOT EXISTS tasks (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    description TEXT,
    status      TEXT NOT NULL CHECK (status IN ('todo', 'doing', 'done')),
    created_at  TEXT NOT NULL,
    updated_at  TEXT,
    due_date    TEXT
);

CREATE INDEX IF NOT EXISTS tasks_status_idx ON tasks (status);
```

Ejecute el siguientes comandos para crear la tabla:

```bash
### crear la db con el esquema `schema.sql`
sqlite3 tasks.db < schema.sql
```

Las consultas se escriben en archivos `.sql` dentro de una carpeta `queries/` y
se ejecutan con `sqlite3 -header -column tasks.db < archivo.sql`, igual que el
esquema. Así quedan guardadas en el repositorio, se pueden repetir y el editor
las revisa con el linter.

Los flags `-header` y `-column` muestran el resultado como tabla, con los
nombres de las columnas. Van en el comando y no dentro del archivo porque los
comandos de `sqlite3` que empiezan con punto, como `.headers on`, no son SQL y
`sqlfluff` los marca como error.

```diff
 tasks-api/
 ├── schema.sql
+├── queries/
+│   ├── inspect.sql
+│   ├── insert.sql
+│   ├── select.sql
+│   ├── update.sql
+│   ├── delete.sql
+│   └── check_constraints.sql
 ├── app/
```

#### 4.1. Inspeccionar la tabla

Agregue el siguiente código en `queries/inspect.sql`.

```sql
-- queries/inspect.sql

-- muestra las tablas e índices de la base
SELECT
    type,
    name
FROM sqlite_master;

-- muestra cada columna, nombre, tipo, etc
PRAGMA table_info (tasks);

-- muestra la cantidad de filas
SELECT COUNT(*) AS total FROM tasks;

-- muestra todas las filas
SELECT * FROM tasks;
```

Ejecute el archivo:

```bash
sqlite3 -header -column tasks.db < queries/inspect.sql
```

```text
type   name
-----  ------------------------
table  tasks
index  sqlite_autoindex_tasks_1
index  tasks_status_idx
cid  name         type  notnull  dflt_value  pk
---  -----------  ----  -------  ----------  --
0    id           TEXT  0                    1
1    name         TEXT  1                    0
2    description  TEXT  0                    0
3    status       TEXT  1                    0
4    created_at   TEXT  1                    0
5    updated_at   TEXT  0                    0
6    due_date     TEXT  0                    0
total
-----
0
```

`sqlite_autoindex_tasks_1` es el índice que SQLite crea solo para la llave
primaria `id`.

#### 4.2. Agregar, leer, modificar y borrar filas

##### Agregar filas

Agregue el siguiente código en `queries/insert.sql`.

```sql
-- queries/insert.sql
-- agrega dos tareas nuevas
INSERT INTO tasks (id, name, description, status, created_at)
VALUES (
    '1', 'comprar pan', 'en la panadería de la esquina', 'todo', datetime('now')
);

INSERT INTO tasks (id, name, status, created_at, due_date)
VALUES ('2', 'estudiar sql', 'doing', datetime('now'), '2026-10-20');

-- muestra cómo quedó la tabla
SELECT
    id,
    name,
    status,
    due_date
FROM tasks;
```

> [!NOTE] Las columnas que no aparecen en el `INSERT` quedan en `NULL`. Si
> ejecuta el archivo dos veces, falla con `UNIQUE constraint failed: tasks.id`:
> ya existe una tarea con ese `id`.

```bash
sqlite3 -header -column tasks.db < queries/insert.sql
```

```text
id  name          status  due_date
--  ------------  ------  ----------
1   comprar pan   todo
2   estudiar sql  doing   2026-10-20
```

##### Leer filas

Agregue el siguiente código en `queries/select.sql`.

```sql
-- queries/select.sql
-- lee una tarea por su id
SELECT * FROM tasks
WHERE id = '1';

-- lista las tareas filtrando por status
SELECT
    id,
    name,
    status
FROM tasks
WHERE status = 'todo';
```

> [!NOTE] El primer `SELECT` es lo que hará `GET /tasks/{id}` y el segundo lo
> que hará `GET /tasks?status=todo`.

```bash
sqlite3 -header -column tasks.db < queries/select.sql
```

```text
id  name         description                    status  created_at           updated_at  due_date
--  -----------  -----------------------------  ------  -------------------  ----------  --------
1   comprar pan  en la panadería de la esquina  todo    2026-10-11 16:39:13
id  name         status
--  -----------  ------
1   comprar pan  todo
```

##### Modificar filas

Agregue el siguiente código en `queries/update.sql`.

```sql
-- queries/update.sql
-- cambia el status de la tarea 1 y guarda cuándo se modificó
UPDATE tasks
SET status = 'done', updated_at = datetime('now')
WHERE id = '1';

-- muestra cómo quedó la tabla
SELECT
    id,
    name,
    status,
    updated_at
FROM tasks;
```

> [!NOTE] Sin el `WHERE`, el `UPDATE` cambia todas las filas de la tabla.

```bash
sqlite3 -header -column tasks.db < queries/update.sql
```

```text
id  name          status  updated_at
--  ------------  ------  -------------------
1   comprar pan   done    2026-10-11 16:39:13
2   estudiar sql  doing
```

##### Borrar filas

Agregue el siguiente código en `queries/delete.sql`.

```sql
-- queries/delete.sql
-- borra la tarea 2
DELETE FROM tasks
WHERE id = '2';

-- muestra cómo quedó la tabla
SELECT
    id,
    name,
    status
FROM tasks;
```

```bash
sqlite3 -header -column tasks.db < queries/delete.sql
```

```text
id  name         status
--  -----------  ------
1   comprar pan  done
```

Igual que en el `UPDATE`, sin el `WHERE` el `DELETE` borra todas las filas.

Para volver a empezar con la tabla vacía, borre la base y créela otra vez:

```bash
rm tasks.db
sqlite3 tasks.db < schema.sql
```

#### 4.3. Comprobar las restricciones

Agregue el siguiente código en `queries/check_constraints.sql`. Las inserciones
van dentro de una transacción que termina en `ROLLBACK`, por eso la prueba no
deja filas en la base.

```sql
-- queries/check_constraints.sql
BEGIN;

-- fila válida: se inserta
INSERT INTO tasks (id, name, status, created_at)
VALUES ('prueba-1', 'probar', 'todo', datetime('now'));

-- status fuera de la lista: falla con CHECK constraint failed
INSERT INTO tasks (id, name, status, created_at)
VALUES ('prueba-2', 'mal', 'pendiente', datetime('now'));

SELECT
    id,
    name,
    status
FROM tasks;

-- deshace las inserciones de prueba
ROLLBACK;
```

Ejecute el archivo:

```bash
sqlite3 -header -column tasks.db < queries/check_constraints.sql
```

```text
Runtime error near line 9: CHECK constraint failed: status IN ('todo', 'doing', 'done') (19)
id        name         status
--------  -----------  ------
1         comprar pan  done
prueba-1  probar       todo
```

El error confirma que el `CHECK` sobre `status` está activo, y el `SELECT`
muestra que, además de la tarea que ya existía, solo entró la fila válida.
`sqlite3` sigue ejecutando el archivo después del error, así que el `ROLLBACK`
final se aplica igual.

Qué es un índice y cuándo conviene está en
[[Databases/indices|índices en bases de datos]].

Cada cambio posterior del esquema se agrega como un `ALTER TABLE` en el mismo
archivo. Versionar esos cambios uno por uno es lo que resuelve
[[Alembic/migraciones|aplicar migraciones con Alembic]].

## 5. Conexión a la base con sqlite3

Una conexión es la sesión de trabajo con el archivo de la base mientras dura una
petición. El primer `insert`, `update` o `delete` abre una transacción y nada
queda escrito hasta llamar a `commit`, por eso una petición que falla a mitad no
deja datos a medias.

Reemplace el contenido de `app/store.py` por el siguiente código.

```python
# app/store.py
import sqlite3
from collections.abc import Generator
from datetime import datetime

# convierte los datetime a texto ISO 8601 al guardarlos
sqlite3.register_adapter(datetime, lambda value: value.isoformat())


# entrega una conexión por petición y la cierra al final
def get_connection() -> Generator[sqlite3.Connection, None, None]:
    # abre el archivo tasks.db y lo crea si no existe
    connection = sqlite3.connect("tasks.db")
    # devuelve filas que se pueden pasar a dict
    connection.row_factory = sqlite3.Row
    try:
        yield connection
    finally:
        connection.close()
```

## 6. Funcionalidad de creación de tareas

Ahora va a mover la acción de `crear tareas` a SQL, para ello va a necesitar:

1. Declarar los imports de `app/routers/tasks.py`
2. Implementar el endpoint `POST /tasks`
3. Validar el endpoint `POST /tasks`

#### 6.1. Declarar los imports de `app/routers/tasks.py`

Reemplace los imports de `app/routers/tasks.py` por los siguientes.

```python
# app/routers/tasks.py
import sqlite3
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException

from app.schemas import Status, Task, TaskCreate, TaskPage, TaskUpdate
from app.store import get_connection
```

`Depends` es lo que le pide a FastAPI que ejecute `get_connection` antes del
endpoint y le pase la conexión ya abierta.

#### 6.2. Implementar el endpoint `POST /tasks`

Reemplace `create_task` por el siguiente código.

```python
@router.post("", status_code=201)
def create_task(
    body: TaskCreate,
    connection: sqlite3.Connection = Depends(get_connection),
) -> Task:
    task = Task(
        id=str(uuid4()),
        name=body.name,
        description=body.description,
        status="todo",
        created_at=datetime.now(timezone.utc),
        updated_at=None,
        due_date=body.due_date,
    )
    row = connection.execute(
        """
        INSERT INTO tasks (id, name, description, status, created_at, updated_at, due_date)
        VALUES (:id, :name, :description, :status, :created_at, :updated_at, :due_date)
        RETURNING id, name, description, status, created_at, updated_at, due_date
        """,
        task.model_dump(),
    ).fetchone()
    connection.commit()
    return Task.model_validate(dict(row))
```

El `Task` se sigue armando igual, lo que cambia es dónde se guarda.
`task.model_dump()` entrega el diccionario que llena los parámetros `:nombre`,
el `RETURNING` devuelve la fila tal como quedó escrita, y nada se confirma hasta
el `commit`.

#### 6.3. Validar el endpoint `POST /tasks`

Ejecute los siguientes comandos para validar que la creación responde `201` y
que la fila queda en la tabla.

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
sqlite3 tasks.db "SELECT id, name, status FROM tasks;"
```

```text
a211f5b3-a524-4b20-8d79-c305cab17ce7|Comprar leche|todo
```

## 7. Funcionalidad de lectura de una tarea

Ahora va a mover la acción de `leer una tarea` a SQL, para ello va a necesitar:

1. Implementar el endpoint `GET /tasks/{id}`
2. Validar el endpoint `GET /tasks/{id}`

#### 7.1. Implementar el endpoint `GET /tasks/{id}`

Reemplace `read_task` por el siguiente código.

```python
@router.get("/{task_id}")
def read_task(
    task_id: str,
    connection: sqlite3.Connection = Depends(get_connection),
) -> Task:
    row = connection.execute(
        """
        SELECT id, name, description, status, created_at, updated_at, due_date
          FROM tasks
         WHERE id = :id
        """,
        {"id": task_id},
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="task not found")
    return Task.model_validate(dict(row))
```

La fila llega como `sqlite3.Row` gracias al `row_factory`, por eso `dict(row)`
alcanza para que Pydantic la valide, y el `created_at` que vuelve como texto ISO
8601 se convierte en `datetime` ahí mismo.

#### 7.2. Validar el endpoint `GET /tasks/{id}`

Ejecute los siguientes comandos para validar que la lectura devuelve la tarea
con `200`, y `404` cuando el id no existe.

```bash
curl -i http://127.0.0.1:8000/tasks/a211f5b3-a524-4b20-8d79-c305cab17ce7
```

```http
HTTP/1.1 200 OK
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
curl -i http://127.0.0.1:8000/tasks/no-existe
```

```text
HTTP/1.1 404 Not Found
content-type: application/json

{"detail":"task not found"}
```

## 8. Funcionalidad de listado con filtro y paginación

Ahora va a mover la acción de `listar las tareas` a SQL, para ello va a
necesitar:

1. Implementar el endpoint `GET /tasks`
2. Validar el endpoint `GET /tasks`

#### 8.1. Implementar el endpoint `GET /tasks`

Reemplace `list_tasks` por el siguiente código.

```python
@router.get("")
def list_tasks(
    status: Status | None = None,
    limit: int = 20,
    offset: int = 0,
    connection: sqlite3.Connection = Depends(get_connection),
) -> TaskPage:
    params = {"status": status, "limit": limit, "offset": offset}
    rows = connection.execute(
        """
        SELECT id, name, description, status, created_at, updated_at, due_date
          FROM tasks
         WHERE (:status IS NULL OR status = :status)
         ORDER BY created_at
         LIMIT :limit OFFSET :offset
        """,
        params,
    ).fetchall()
    total = connection.execute(
        """
        SELECT COUNT(*) AS total
          FROM tasks
         WHERE (:status IS NULL OR status = :status)
        """,
        params,
    ).fetchone()["total"]

    return TaskPage(
        items=[Task.model_validate(dict(row)) for row in rows],
        total=total,
    )
```

Las dos consultas son texto fijo, no se arman en Python. El filtro opcional se
expresa con `:status IS NULL`, que es verdadero cuando el parámetro no llegó, y
el conteo viaja aparte porque el `LIMIT` recorta la primera.

#### 8.2. Validar el endpoint `GET /tasks`

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

## 9. Funcionalidad de actualización parcial

Ahora va a mover la acción de `actualizar una tarea` a SQL, para ello va a
necesitar:

1. Implementar el endpoint `PATCH /tasks/{id}`
2. Validar el endpoint `PATCH /tasks/{id}`

#### 9.1. Implementar el endpoint `PATCH /tasks/{id}`

Reemplace `update_task` por el siguiente código.

```python
@router.patch("/{task_id}")
def update_task(
    task_id: str,
    body: TaskUpdate,
    connection: sqlite3.Connection = Depends(get_connection),
) -> Task:
    task = read_task(task_id, connection)
    changes = body.model_dump(exclude_unset=True)
    changes["updated_at"] = datetime.now(timezone.utc)
    updated = task.model_copy(update=changes)
    row = connection.execute(
        """
        UPDATE tasks
           SET name = :name,
               description = :description,
               status = :status,
               updated_at = :updated_at,
               due_date = :due_date
         WHERE id = :id
        RETURNING id, name, description, status, created_at, updated_at, due_date
        """,
        updated.model_dump(),
    ).fetchone()
    connection.commit()
    return Task.model_validate(dict(row))
```

`model_copy(update=changes)` se queda igual que en el tutorial 1, es lo que
aplica el cambio parcial. El `UPDATE` escribe siempre las cinco columnas que
pueden cambiar, con los valores ya resueltos, y el `404` lo levanta `read_task`,
la lectura de la sección anterior.

#### 9.2. Validar el endpoint `PATCH /tasks/{id}`

Ejecute los siguientes comandos para validar que la actualización parcial cambia
solo los campos enviados, y responde `404` cuando el id no existe.

```bash
curl -X PATCH http://127.0.0.1:8000/tasks/a211f5b3-a524-4b20-8d79-c305cab17ce7 \
  -H "Content-Type: application/json" \
  -d '{"status": "doing"}'
```

```json
{
  "id": "a211f5b3-a524-4b20-8d79-c305cab17ce7",
  "name": "Comprar leche",
  "description": null,
  "status": "doing",
  "created_at": "2026-09-22T18:08:32.632592Z",
  "updated_at": "2026-09-22T18:14:05.684988Z",
  "due_date": null
}
```

```bash
curl -i -X PATCH http://127.0.0.1:8000/tasks/no-existe \
  -H "Content-Type: application/json" \
  -d '{"status": "doing"}'
```

```text
HTTP/1.1 404 Not Found
content-type: application/json

{"detail":"task not found"}
```

## 10. Funcionalidad de borrado

Ahora va a mover la acción de `borrar una tarea` a SQL, para ello va a
necesitar:

1. Implementar el endpoint `DELETE /tasks/{id}`
2. Validar el endpoint `DELETE /tasks/{id}`

#### 10.1. Implementar el endpoint `DELETE /tasks/{id}`

Reemplace `delete_task` por el siguiente código.

```python
@router.delete("/{task_id}", status_code=204)
def delete_task(
    task_id: str,
    connection: sqlite3.Connection = Depends(get_connection),
) -> None:
    row = connection.execute(
        """
        DELETE FROM tasks
         WHERE id = :id
        RETURNING id
        """,
        {"id": task_id},
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="task not found")
    connection.commit()
```

La comprobación previa de existencia ya no hace falta, el `RETURNING` devuelve
el `id` borrado y no devuelve nada cuando no había fila, que es la señal del
`404`.

`RETURNING` existe en SQLite desde la versión 3.35, y es la misma cláusula que
usan PostgreSQL y MariaDB.

#### 10.2. Validar el endpoint `DELETE /tasks/{id}`

Ejecute los siguientes comandos para validar que el borrado responde `204`, y
`404` al repetirlo sobre el mismo id.

```bash
curl -i -X DELETE http://127.0.0.1:8000/tasks/a211f5b3-a524-4b20-8d79-c305cab17ce7
```

```text
HTTP/1.1 204 No Content
```

```bash
curl -i -X DELETE http://127.0.0.1:8000/tasks/a211f5b3-a524-4b20-8d79-c305cab17ce7
```

```text
HTTP/1.1 404 Not Found
content-type: application/json

{"detail":"task not found"}
```

## 11. Validar que los datos sobreviven al reinicio

Ejecute los siguientes comandos para validar que la tarea creada sigue ahí
después de reiniciar el servidor.

```bash
curl -X POST http://127.0.0.1:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"name": "Escribir la nota"}'
```

```json
{
  "id": "10a79592-0c2f-4ab6-8c0d-f1d79d5173e3",
  "name": "Escribir la nota",
  "description": null,
  "status": "todo",
  "created_at": "2026-09-22T18:20:11.637555Z",
  "updated_at": null,
  "due_date": null
}
```

Detenga `uvicorn` con `Ctrl+C`, vuelva a levantarlo y lea la misma tarea.

```bash
curl http://127.0.0.1:8000/tasks/10a79592-0c2f-4ab6-8c0d-f1d79d5173e3
```

```json
{
  "id": "10a79592-0c2f-4ab6-8c0d-f1d79d5173e3",
  "name": "Escribir la nota",
  "description": null,
  "status": "todo",
  "created_at": "2026-09-22T18:20:11.637555Z",
  "updated_at": null,
  "due_date": null
}
```

Con el diccionario en memoria esa segunda lectura respondía `404`.

## 12. Migrar a PostgreSQL

SQLite y PostgreSQL entienden el mismo SQL en todo lo que se escribió hasta
aquí, por eso ninguna consulta se rediseña, solo cambian el driver, los tipos de
fecha y la sintaxis de los parámetros.

| Pieza             | sqlite3                                | psycopg                               |
| ----------------- | -------------------------------------- | ------------------------------------- |
| Dependencia       | Biblioteca estándar de Python          | `psycopg[binary]`                     |
| Conexión          | `sqlite3.connect("tasks.db")`          | `psycopg.connect("postgresql://…")`   |
| Filas como `dict` | `connection.row_factory = sqlite3.Row` | `row_factory=dict_row`                |
| Parámetros        | `:id`                                  | `%(id)s`                              |
| Fechas            | `TEXT` en formato ISO 8601             | `TIMESTAMPTZ`                         |
| Cargar el esquema | `sqlite3 tasks.db < schema.sql`        | `psql "postgresql://…" -f schema.sql` |

Ahora va a mover el almacenamiento a PostgreSQL, para ello va a necesitar:

1. Levantar PostgreSQL e instalar `psycopg`
2. Cambiar los tipos de fecha en `schema.sql`
3. Reemplazar la conexión en `app/store.py`
4. Cambiar la sintaxis de los parámetros en las consultas
5. Validar que los endpoints responden igual

#### 12.1. Levantar PostgreSQL e instalar `psycopg`

Ejecute los siguientes comandos para levantar la base y agregar el driver.

```bash
docker run -d --name tasks-db \
  -e POSTGRES_PASSWORD=pg \
  -e POSTGRES_DB=tasks \
  -p 5432:5432 postgres:16
uv add "psycopg[binary]"
```

#### 12.2. Cambiar los tipos de fecha en `schema.sql`

Reemplace el contenido de `schema.sql` por el siguiente código.

```sql
-- schema.sql
CREATE TABLE IF NOT EXISTS tasks (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    description TEXT,
    status      TEXT NOT NULL CHECK (status IN ('todo', 'doing', 'done')),
    created_at  TIMESTAMPTZ NOT NULL,
    updated_at  TIMESTAMPTZ,
    due_date    TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS tasks_status_idx ON tasks (status);
```

`PRIMARY KEY`, `NOT NULL`, `CHECK`, `IF NOT EXISTS` y el índice se escriben
igual que en SQLite. El `id` se mantiene como `TEXT` porque `Task.id` es un
`str`, con una columna `UUID` la fila vuelve con un `uuid.UUID` y habría que
cambiar también el esquema de Pydantic.

Ejecute el siguiente comando para crear la tabla.

```bash
psql "postgresql://postgres:pg@127.0.0.1:5432/tasks" -f schema.sql
```

#### 12.3. Reemplazar la conexión en `app/store.py`

Reemplace el contenido de `app/store.py` por el siguiente código.

```python
# app/store.py
from collections.abc import Generator

import psycopg
from psycopg.rows import dict_row

DATABASE_URL = "postgresql://postgres:pg@127.0.0.1:5432/tasks"


def get_connection() -> Generator[psycopg.Connection, None, None]:
    connection = psycopg.connect(DATABASE_URL, row_factory=dict_row)
    try:
        yield connection
    finally:
        connection.close()
```

| Linea                  | Qué aporta                                                 |
| ---------------------- | ---------------------------------------------------------- |
| `psycopg.connect`      | Abre la sesión contra el servidor, ya no contra un archivo |
| `row_factory=dict_row` | Devuelve cada fila como `dict`                             |
| `get_connection`       | Entrega una conexión por petición y la cierra al final     |

Desaparece el `register_adapter`, psycopg manda los `datetime` tal cual y
`TIMESTAMPTZ` los devuelve como `datetime` con zona horaria. El `commit` sigue
siendo obligatorio, psycopg tampoco escribe sin él.

#### 12.4. Cambiar la sintaxis de los parámetros en las consultas

En `app/routers/tasks.py` cambie `import sqlite3` por `import psycopg`, las
anotaciones `sqlite3.Connection` por `psycopg.Connection`, y cada parámetro
`:nombre` por `%(nombre)s`. El resto de cada sentencia queda intacto, como se ve
en `read_task`.

```python
    row = connection.execute(
        """
        SELECT id, name, description, status, created_at, updated_at, due_date
          FROM tasks
         WHERE id = %(id)s
        """,
        {"id": task_id},
    ).fetchone()
```

El filtro opcional del listado necesita además un cast explícito, porque
PostgreSQL no deduce el tipo de un parámetro que llega en `NULL` y responde
`AmbiguousParameter`.

```sql
         WHERE (%(status)s::text IS NULL OR status = %(status)s)
```

Lo demás se mantiene, `dict(row)` sigue funcionando porque `dict_row` ya entrega
un `dict`, y las cinco sentencias conservan su `RETURNING`, su `LIMIT OFFSET` y
su `COUNT(*)`.

#### 12.5. Validar que los endpoints responden igual

Ejecute de nuevo las validaciones de la sección 11 para confirmar que el
contrato de los endpoints no cambió y que los datos sobreviven al reinicio, esta
vez porque viven en el servidor de la base y no en el archivo `tasks.db`.

## 13. Preguntas de entrevista

Las siguientes preguntas son las que un entrevistador puede hacer sobre lo que
se construyó en esta nota.

#### 13.1. SQL y modelo de datos

| Pregunta                                                         | Respuesta corta                                                                                        |
| ---------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| ¿Qué es una inyección SQL y qué la evita en este código?         | Los valores viajan como parámetros `:nombre`, el driver nunca los pega dentro del texto de la consulta |
| ¿Para qué sirve el índice sobre `status`?                        | El listado filtra por esa columna, sin índice la base recorre la tabla entera                          |
| ¿Qué garantiza el `CHECK` si Pydantic ya valida el estado?       | Que ningún otro programa escriba un estado inválido, la base es la última que puede rechazarlo         |
| ¿Por qué `RETURNING` en vez de un `SELECT` después del `INSERT`? | Una sola ida a la base, y devuelve la fila que realmente quedó escrita                                 |
| ¿Por qué el conteo del listado va en una segunda consulta?       | El `LIMIT` recorta la primera, así que de ahí no sale el total                                         |
| ¿Qué problema tiene `LIMIT OFFSET` en tablas grandes?            | El `OFFSET` recorre y descarta las filas anteriores, la paginación por cursor sobre `created_at` no    |
| ¿Por qué no se usa `COALESCE` para el `PATCH`?                   | No distingue un campo ausente de un `null` explícito, y `{"description": null}` debe limpiar el campo  |
| ¿Diferencia entre `PRIMARY KEY`, `UNIQUE` y un índice común?     | Las dos primeras son restricciones que además crean un índice, el índice solo acelera la búsqueda      |

#### 13.2. Transacciones y conexión

| Pregunta                                                       | Respuesta corta                                                                                                      |
| -------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| ¿Qué pasa si no se llama a `commit`?                           | La transacción se descarta al cerrar la conexión y nada queda escrito                                                |
| ¿Qué es una transacción y qué significan las propiedades ACID? | Un bloque de escrituras que se aplica entero o no se aplica, con atomicidad, consistencia, aislamiento y durabilidad |
| ¿Por qué una conexión por petición y no una global?            | Aísla la transacción de cada petición y libera el recurso al responder                                               |
| ¿Qué hace `Depends(get_connection)`?                           | FastAPI corre el generador al entrar la petición y su `finally` al terminarla                                        |
| ¿Qué es un pool de conexiones y por qué importa en PostgreSQL? | Reusa conexiones ya abiertas, y en PostgreSQL cada sesión nueva cuesta un proceso del servidor                       |

#### 13.3. SQLite y PostgreSQL

| Pregunta                                                          | Respuesta corta                                                                            |
| ----------------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| ¿Cuándo SQLite deja de alcanzar?                                  | Admite un escritor a la vez y vive en un archivo local, varios servidores no lo comparten  |
| ¿Qué cambia al migrar las consultas a PostgreSQL?                 | El driver, la sintaxis de los parámetros y los tipos de fecha, las sentencias quedan igual |
| ¿Por qué guardar las fechas en UTC?                               | La zona horaria es decisión de quien muestra el dato, no de quien lo guarda                |
| ¿Diferencia entre guardar una fecha en `TEXT` y en `TIMESTAMPTZ`? | En `TEXT` la base no sabe que es una fecha y no puede compararla ni operarla como tal      |
| ¿Qué es una migración y por qué no editar `schema.sql`?           | Es el cambio de esquema versionado y aplicable a una base que ya tiene datos               |
