---
title: 4. Conectar un frontend a una API
tags:
  - frontend
  - react
  - typescript
  - api
  - fetch
  - tutorial
---

La presente nota continúa el tutorial de
[[Tutoriales/todo-app/3-crear-un-frontend|crear un frontend desde cero]] reemplazando las
tareas en memoria por las de la API de
[[Tutoriales/todo-app/2-conectar-una-base-de-datos|conectar una API a una base de datos]], sin
cambiar la pantalla.

Cada acción pasa a ser una petición, y la pantalla deja de ser la dueña de los
datos para mostrar lo que el servidor responde.

El contenido se distribuye entonces de la siguiente manera:

1. [Requisitos](#1-requisitos)
2. [Análisis y diseño de la conexión](#2-análisis-y-diseño-de-la-conexión)
3. [Habilitar CORS en la API](#3-habilitar-cors-en-la-api)
4. [Cliente de la API](#4-cliente-de-la-api)
5. [Cargar las tareas al abrir la página](#5-cargar-las-tareas-al-abrir-la-página)
6. [Funcionalidad de creación de tareas](#6-funcionalidad-de-creación-de-tareas)
7. [Funcionalidad de actualización parcial](#7-funcionalidad-de-actualización-parcial)
8. [Funcionalidad de borrado](#8-funcionalidad-de-borrado)
9. [Mostrar la carga y los errores](#9-mostrar-la-carga-y-los-errores)
10. [Validar el flujo completo en el navegador](#10-validar-el-flujo-completo-en-el-navegador)
11. [Preguntas de entrevista](#11-preguntas-de-entrevista)

## 1. Requisitos

A continuación se propone el conjunto mínimo de características que debe
satisfacer la conexión:

1. Las tareas que muestra la pantalla salen de la API.
2. Las tareas creadas siguen ahí después de recargar la página.
3. El filtro por estado lo resuelve el servidor.
4. La pantalla avisa mientras carga y cuando la API no responde.
5. La API no cambia su contrato.

## 2. Análisis y diseño de la conexión

Cada acción se traduce en una petición:

| Acción               | Petición             |
| -------------------- | -------------------- |
| Cargar las tareas    | `GET /tasks`         |
| Crear una tarea      | `POST /tasks`        |
| Cambiar el estado    | `PATCH /tasks/{id}`  |
| Borrar una tarea     | `DELETE /tasks/{id}` |

Las decisiones del diseño que conviene fijar en esta etapa son:

- El servidor es la única fuente de verdad, después de cada escritura se vuelve
  a pedir el listado en lugar de editar el arreglo local
- `src/api.ts` es el único archivo que conoce las URLs
- El `id`, el `status` inicial y el `created_at` los sigue poniendo el servidor,
  como en el tutorial de la API

## 3. Habilitar CORS en la API

La página corre en `http://localhost:5173` y la API en `http://127.0.0.1:8000`,
dos orígenes distintos, así que el navegador bloquea la respuesta hasta que la
API declare que acepta ese origen. Con `curl` el problema no aparecía, porque la
restricción la aplica el navegador y no el servidor.

Agregue el siguiente código en `app/main.py`.

```python
# app/main.py
from fastapi.middleware.cors import CORSMiddleware

...

app.add_middleware(
    CORSMiddleware,
    # el origen tiene que coincidir exacto, localhost y 127.0.0.1 son distintos
    allow_origins=["http://localhost:5173"],
    # permite el PATCH y el DELETE además del GET y el POST
    allow_methods=["*"],
    # permite el Content-Type: application/json que manda el cliente
    allow_headers=["*"],
)
```

Ejecute el siguiente comando para validar que la API responde los encabezados de
CORS ante el preflight que el navegador manda antes del `POST`.

```bash
curl -i -X OPTIONS http://127.0.0.1:8000/tasks \
  -H "Origin: http://localhost:5173" \
  -H "Access-Control-Request-Method: POST"
```

```text
HTTP/1.1 200 OK
access-control-allow-methods: DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT
access-control-allow-origin: http://localhost:5173
```

## 4. Cliente de la API

Una función por petición, todas en el mismo archivo.

Agregue el siguiente código en `src/api.ts`.

```tsx
// src/api.ts
import type { Status, Task } from "./tasks";

const API = "http://127.0.0.1:8000";
const HEADERS = { "Content-Type": "application/json" };

export async function listTasks(status: string) {
  // el filtro vacío no viaja, la API devolvería un 422
  const query = status === "" ? "" : `?status=${status}`;
  const response = await fetch(`${API}/tasks${query}`);
  const page = (await response.json()) as { items: Task[]; total: number };
  return page.items;
}

export async function createTask(name: string) {
  const response = await fetch(`${API}/tasks`, {
    method: "POST",
    headers: HEADERS,
    body: JSON.stringify({ name }),
  });
  return (await response.json()) as Task;
}

export async function updateTask(id: string, status: Status) {
  const response = await fetch(`${API}/tasks/${id}`, {
    method: "PATCH",
    headers: HEADERS,
    body: JSON.stringify({ status }),
  });
  return (await response.json()) as Task;
}

export async function deleteTask(id: string) {
  // el 204 no trae cuerpo que parsear
  await fetch(`${API}/tasks/${id}`, { method: "DELETE" });
}
```

El `as Task` no valida nada, solo le dice al compilador qué forma tiene el
`json`; si la API cambia un campo, el error aparece en tiempo de ejecución.

## 5. Cargar las tareas al abrir la página

`src/tasks.ts` se queda con los tipos, los datos de ejemplo salen de escena.

```diff
--- src/tasks.ts
+++ src/tasks.ts
@@
 export type Status = "todo" | "doing" | "done";

 export type Task = {
   id: string;
   name: string;
   status: Status;
   created_at: string;
 };
-
-export const INITIAL_TASKS: Task[] = [
-  { id: "1", name: "Comprar leche", status: "todo", created_at: "2026-10-01" },
-  ...
-];
```

Agregue en `src/App.tsx` las líneas que se muestran en verde.

```diff
@@ -1,15 +1,22 @@
 // src/App.tsx
-import { useState } from "react";
-import { INITIAL_TASKS, type Status, type Task } from "./tasks";
+import { useEffect, useState } from "react";
+import { listTasks } from "./api";
+import { type Status, type Task } from "./tasks";
 
 export default function App() {
-  const [tasks, setTasks] = useState<Task[]>(INITIAL_TASKS);
+  const [tasks, setTasks] = useState<Task[]>([]);
   const [status, setStatus] = useState("");
   const [name, setName] = useState("");
 
-  // la lista filtrada se calcula en cada render, no es estado
-  const filtered =
-    status === "" ? tasks : tasks.filter((task) => task.status === status);
+  // pide las tareas al servidor con el filtro puesto
+  async function reload() {
+    setTasks(await listTasks(status));
+  }
+
+  // corre al abrir la página y cada vez que cambia el filtro
+  useEffect(() => {
+    void reload();
+  }, [status]);
 
   function handleCreate() {
     const task: Task = {
@@ -37,7 +44,7 @@
 
   return (
     <main>
-      <h1>Tareas ({filtered.length})</h1>
+      <h1>Tareas ({tasks.length})</h1>
 
       <input
         value={name}
@@ -54,7 +61,7 @@
       </select>
 
       <ul>
-        {filtered.map((task) => (
+        {tasks.map((task) => (
           <li key={task.id}>
             {task.name}
             <select
```

El `useEffect` corre después de que la pantalla quedó pintada, y el arreglo
`[status]` decide cuándo vuelve a correr. Sin ese arreglo correría en cada
render, y como `reload` llama a `setTasks`, cada render dispararía el siguiente.

Con la API encendida, abra `http://localhost:5173` y valide en la pestaña de red
que aparece un `GET /tasks` al abrir, y otro con `?status=done` al elegir ese
filtro.

## 6. Funcionalidad de creación de tareas

Agregue en `src/App.tsx` las líneas que se muestran en verde.

```diff
@@ -1,6 +1,6 @@
 // src/App.tsx
 import { useEffect, useState } from "react";
-import { listTasks } from "./api";
+import { createTask, listTasks } from "./api";
 import { type Status, type Task } from "./tasks";
 
 export default function App() {
@@ -18,16 +18,11 @@
     void reload();
   }, [status]);
 
-  function handleCreate() {
-    const task: Task = {
-      id: crypto.randomUUID(),
-      name,
-      status: "todo",
-      created_at: new Date().toISOString(),
-    };
-    // arma un arreglo nuevo en lugar de empujar sobre el anterior
-    setTasks([task, ...tasks]);
+  // el id, el status y el created_at los pone el servidor
+  async function handleCreate() {
+    await createTask(name);
     setName("");
+    void reload();
   }
 
   function handleStatus(id: string, next: Status) {
```

Cree una tarea y valide que salen dos peticiones, el `POST /tasks` y el
`GET /tasks` del `reload`, y que la tarea sigue ahí al recargar la página con
`F5`.

## 7. Funcionalidad de actualización parcial

Agregue en `src/App.tsx` las líneas que se muestran en verde.

```diff
@@ -1,6 +1,6 @@
 // src/App.tsx
 import { useEffect, useState } from "react";
-import { createTask, listTasks } from "./api";
+import { createTask, listTasks, updateTask } from "./api";
 import { type Status, type Task } from "./tasks";
 
 export default function App() {
@@ -25,12 +25,10 @@
     void reload();
   }
 
-  function handleStatus(id: string, next: Status) {
-    // devuelve la tarea con el estado nuevo, o la misma si no es la que cambia
-    const updateTask = (task: Task) =>
-      task.id === id ? { ...task, status: next } : task;
-
-    setTasks(tasks.map(updateTask));
+  // el PATCH manda solo el campo que cambia
+  async function handleStatus(id: string, next: Status) {
+    await updateTask(id, next);
+    void reload();
   }
 
   function handleDelete(id: string) {
```

Cambie el estado de una tarea y valide que el cuerpo del `PATCH` lleva solo
`status`. Con el filtro en `todo`, la tarea que pasa a `done` desaparece de la
lista, porque el `reload` la vuelve a pedir con ese filtro.

## 8. Funcionalidad de borrado

Agregue en `src/App.tsx` las líneas que se muestran en verde.

```diff
@@ -1,6 +1,6 @@
 // src/App.tsx
 import { useEffect, useState } from "react";
-import { createTask, listTasks, updateTask } from "./api";
+import { createTask, deleteTask, listTasks, updateTask } from "./api";
 import { type Status, type Task } from "./tasks";
 
 export default function App() {
@@ -31,8 +31,9 @@
     void reload();
   }
 
-  function handleDelete(id: string) {
-    setTasks(tasks.filter((task) => task.id !== id));
+  async function handleDelete(id: string) {
+    await deleteTask(id);
+    void reload();
   }
 
   return (
```

Borre una tarea y valide que el `DELETE` responde `204` y que la tarea no vuelve
al recargar la página.

## 9. Mostrar la carga y los errores

Entre el click y la respuesta pasa un tiempo que la pantalla hasta ahora
ignoraba, y la API puede estar apagada.

Agregue en `src/App.tsx` las líneas que se muestran en verde.

```diff
@@ -7,10 +7,20 @@
   const [tasks, setTasks] = useState<Task[]>([]);
   const [status, setStatus] = useState("");
   const [name, setName] = useState("");
+  const [loading, setLoading] = useState(false);
+  const [error, setError] = useState<string | null>(null);
 
   // pide las tareas al servidor con el filtro puesto
   async function reload() {
-    setTasks(await listTasks(status));
+    setLoading(true);
+    try {
+      setTasks(await listTasks(status));
+      setError(null);
+    } catch {
+      setError("no se pudo hablar con la API");
+    } finally {
+      setLoading(false);
+    }
   }
 
   // corre al abrir la página y cada vez que cambia el filtro
@@ -40,6 +50,9 @@
     <main>
       <h1>Tareas ({tasks.length})</h1>
 
+      {loading && <p>cargando</p>}
+      {error !== null && <p>{error}</p>}
+
       <input
         value={name}
         onChange={(event) => setName(event.target.value)}
```

Apague la API, recargue la página y valide que aparece el mensaje de error en
lugar de una lista vacía.

## 10. Validar el flujo completo en el navegador

Con las cuatro peticiones cubiertas, `src/App.tsx` queda así.

```tsx
// src/App.tsx
import { useEffect, useState } from "react";
import { createTask, deleteTask, listTasks, updateTask } from "./api";
import { type Status, type Task } from "./tasks";

export default function App() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [status, setStatus] = useState("");
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // pide las tareas al servidor con el filtro puesto
  async function reload() {
    setLoading(true);
    try {
      setTasks(await listTasks(status));
      setError(null);
    } catch {
      setError("no se pudo hablar con la API");
    } finally {
      setLoading(false);
    }
  }

  // corre al abrir la página y cada vez que cambia el filtro
  useEffect(() => {
    void reload();
  }, [status]);

  // el id, el status y el created_at los pone el servidor
  async function handleCreate() {
    await createTask(name);
    setName("");
    void reload();
  }

  // el PATCH manda solo el campo que cambia
  async function handleStatus(id: string, next: Status) {
    await updateTask(id, next);
    void reload();
  }

  async function handleDelete(id: string) {
    await deleteTask(id);
    void reload();
  }

  return (
    <main>
      <h1>Tareas ({tasks.length})</h1>

      {loading && <p>cargando</p>}
      {error !== null && <p>{error}</p>}

      <input
        value={name}
        onChange={(event) => setName(event.target.value)}
        placeholder="nombre"
      />
      <button onClick={handleCreate}>crear</button>

      <select value={status} onChange={(event) => setStatus(event.target.value)}>
        <option value="">todos</option>
        <option value="todo">todo</option>
        <option value="doing">doing</option>
        <option value="done">done</option>
      </select>

      <ul>
        {tasks.map((task) => (
          <li key={task.id}>
            {task.name}
            <select
              value={task.status}
              onChange={(event) =>
                handleStatus(task.id, event.target.value as Status)
              }
            >
              <option value="todo">todo</option>
              <option value="doing">doing</option>
              <option value="done">done</option>
            </select>
            <button onClick={() => handleDelete(task.id)}>borrar</button>
          </li>
        ))}
      </ul>
    </main>
  );
}
```

## 11. Preguntas de entrevista

Las siguientes preguntas son las que un entrevistador puede hacer sobre lo que
se construyó en esta nota.

#### 11.1. El navegador y la API

1. ¿Por qué `curl` funcionaba y el navegador daba error de CORS?

   La restricción la aplica el navegador, la API respondía igual en los dos
   casos

2. ¿Qué es la petición `OPTIONS` que sale antes del `POST`?

   El preflight, con el que el navegador pregunta si ese método y esos
   encabezados están permitidos para ese origen

3. ¿Por qué el `GET` del listado no dispara preflight y el `POST` sí?

   El `Content-Type: application/json` saca a la petición del conjunto de
   peticiones simples

4. ¿Qué pasa si la API responde `500` y no se revisa `response.ok`?

   `fetch` no lo considera un fallo, el `json()` revienta o devuelve algo que no
   es una tarea, y el `catch` muestra un error que no explica nada

#### 11.2. React y los datos

1. ¿Por qué la carga va en un `useEffect` y no en el cuerpo de `App`?

   El cuerpo corre en cada render, el efecto corre después de pintar y solo
   cuando cambian sus dependencias

2. ¿Qué pasa si el `useEffect` se queda sin el arreglo `[status]`?

   Corre en cada render, y como `reload` llama a `setTasks`, cada render
   dispara el siguiente

3. ¿Por qué después de crear, cambiar o borrar se vuelve a pedir el listado?

   El servidor decide el orden y el filtro, el arreglo local no puede adivinar
   qué le toca mostrar a esta pantalla

4. ¿Por qué el filtro ahora viaja como `?status=` en vez de filtrar en el
   navegador?

   El navegador solo tiene la página que pidió, filtrar ahí escondería las
   tareas que el servidor todavía no mandó

5. ¿Qué pasa con los campos que la API devuelve y el tipo `Task` no declara?

   Llegan igual en el `json`, el tipo solo describe lo que la pantalla usa
