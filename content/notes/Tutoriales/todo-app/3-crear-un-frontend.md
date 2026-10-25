---
title: 3. Crear un frontend desde cero
tags:
  - frontend
  - react
  - typescript
  - vite
  - tutorial
---

La presente nota es un tutorial sencillo de cómo crear la pantalla de una lista
TODO en React, con las funcionalidades CRUD completas para una tarea (`task`).

Se arranca de una lista que solo muestra las tareas, y cada funcionalidad se
construye sobre esa base. Las tareas viven en memoria, así que la pantalla se
arma y se prueba sin backend, la conexión con la API tiene su propia nota.

El contenido se distribuye entonces de la siguiente manera:

1. [Requisitos](#1-requisitos)
2. [Análisis y diseño del frontend](#2-análisis-y-diseño-del-frontend)
3. [Setup del proyecto](#3-setup-del-proyecto)
4. [Modelo y datos de ejemplo](#4-modelo-y-datos-de-ejemplo)
5. [Mostrar las tareas en una lista](#5-mostrar-las-tareas-en-una-lista)
6. [Funcionalidad de filtro por estado](#6-funcionalidad-de-filtro-por-estado)
7. [Funcionalidad de creación de tareas](#7-funcionalidad-de-creación-de-tareas)
8. [Funcionalidad de actualización parcial](#8-funcionalidad-de-actualización-parcial)
9. [Funcionalidad de borrado](#9-funcionalidad-de-borrado)
10. [Validar el flujo completo en el navegador](#10-validar-el-flujo-completo-en-el-navegador)
11. [Preguntas de entrevista](#11-preguntas-de-entrevista)

## 1. Requisitos

A continuación se propone el conjunto mínimo de características que debe
satisfacer la página:

1. Ver las tareas en una lista.
2. Filtrar la lista por estado.
3. Crear una tarea escribiendo un nombre.
4. Cambiar el estado de una tarea.
5. Borrar una tarea.

## 2. Análisis y diseño del frontend

Cada acción se traduce en una pieza de la pantalla:

| Acción               | Pieza                               |
| -------------------- | ----------------------------------- |
| Ver las tareas       | La lista                            |
| Filtrar por estado   | El selector sobre la lista          |
| Crear una tarea      | El formulario de una sola caja      |
| Actualizar una tarea | El selector de estado de cada tarea |
| Borrar una tarea     | El botón de borrar de cada tarea    |

Y el estado que sostiene la pantalla es el siguiente:

| Estado   | Para qué                           |
| -------- | ---------------------------------- |
| `tasks`  | El arreglo completo de tareas      |
| `status` | El filtro aplicado a la lista      |
| `name`   | Lo que se escribe en el formulario |

Las decisiones del diseño que conviene fijar en esta etapa son:

- El estado nunca se muta, cada acción arma un arreglo nuevo con `map`, `filter`
  o el spread
- Lo que se puede calcular no se guarda, la lista filtrada, la página y la tarea
  abierta se derivan de `tasks` en cada render
- Todo el estado vive en `App`

## 3. Setup del proyecto

El proyecto se crea con Vite, que trae el servidor de desarrollo y la plantilla
de React con TypeScript ya configurada.

```bash
# creando el proyecto con la plantilla de react y typescript
bun create vite tasks-web --template react-ts
cd tasks-web

# instalando las dependencias
bun install

# levantando el servidor de desarrollo
bun dev
```

```text
  VITE v8.3.4  ready in 172 ms

  ➜  Local:   http://localhost:5173/
```

La estructura del proyecto es la siguiente:

```text
tasks-web/
├── index.html
├── package.json
├── bun.lock
├── tsconfig.json
├── vite.config.ts
└── src/
    ├── main.tsx     # monta App en el DOM
    ├── tasks.ts     # el tipo Task y las tareas de ejemplo
    └── App.tsx      # toda la pantalla
```

## 4. Modelo y datos de ejemplo

`Status` es una unión de literales, así el compilador rechaza un estado que no
existe.

Agregue el siguiente código en `src/tasks.ts`.

```tsx
// src/tasks.ts
export type Status = "todo" | "doing" | "done"

export type Task = {
  id: string
  name: string
  status: Status
  created_at: string
}

export const INITIAL_TASKS: Task[] = [
  { id: "1", name: "Comprar leche", status: "todo", created_at: "2026-10-01" },
  {
    id: "2",
    name: "Escribir la nota",
    status: "doing",
    created_at: "2026-10-02",
  },
  {
    id: "3",
    name: "Pagar el internet",
    status: "done",
    created_at: "2026-10-03",
  },
  {
    id: "4",
    name: "Llamar al dentista",
    status: "todo",
    created_at: "2026-10-04",
  },
  {
    id: "5",
    name: "Renovar el dominio",
    status: "todo",
    created_at: "2026-10-05",
  },
  {
    id: "6",
    name: "Revisar el backup",
    status: "doing",
    created_at: "2026-10-06",
  },
]
```

## 5. Mostrar las tareas en una lista

Agregue el siguiente código en `src/App.tsx`.

```tsx
// src/App.tsx
import { useState } from "react"
import { INITIAL_TASKS, type Task } from "./tasks"

export default function App() {
  const [tasks, setTasks] = useState<Task[]>(INITIAL_TASKS)

  return (
    <main>
      <h1>Tareas ({tasks.length})</h1>

      <ul>
        {tasks.map((task) => (
          <li key={task.id}>
            {task.name} — {task.status}
          </li>
        ))}
      </ul>
    </main>
  )
}
```

Con `bun dev` encendido, abra `http://localhost:5173` y valide que la lista trae
las seis tareas de ejemplo.

## 6. Funcionalidad de filtro por estado

Agregue en `src/App.tsx` las líneas que se muestran en verde.

```diff
@@ -4,13 +4,25 @@

 export default function App() {
   const [tasks, setTasks] = useState<Task[]>(INITIAL_TASKS);
+  const [status, setStatus] = useState("");
+
+  // la lista filtrada se calcula en cada render, no es estado
+  const filtered =
+    status === "" ? tasks : tasks.filter((task) => task.status === status);

   return (
     <main>
-      <h1>Tareas ({tasks.length})</h1>
+      <h1>Tareas ({filtered.length})</h1>
+
+      <select value={status} onChange={(event) => setStatus(event.target.value)}>
+        <option value="">todos</option>
+        <option value="todo">todo</option>
+        <option value="doing">doing</option>
+        <option value="done">done</option>
+      </select>

       <ul>
-        {tasks.map((task) => (
+        {filtered.map((task) => (
           <li key={task.id}>
             {task.name} — {task.status}
           </li>
```

Elija `done` en el selector y valide que la lista deja una sola tarea.

## 7. Funcionalidad de creación de tareas

Agregue en `src/App.tsx` las líneas que se muestran en verde.

```diff
@@ -5,15 +5,35 @@
 export default function App() {
   const [tasks, setTasks] = useState<Task[]>(INITIAL_TASKS);
   const [status, setStatus] = useState("");
+  const [name, setName] = useState("");

   // la lista filtrada se calcula en cada render, no es estado
   const filtered =
     status === "" ? tasks : tasks.filter((task) => task.status === status);

+  function handleCreate() {
+    const task: Task = {
+      id: crypto.randomUUID(),
+      name,
+      status: "todo",
+      created_at: new Date().toISOString(),
+    };
+    // arma un arreglo nuevo en lugar de empujar sobre el anterior
+    setTasks([task, ...tasks]);
+    setName("");
+  }
+
   return (
     <main>
       <h1>Tareas ({filtered.length})</h1>

+      <input
+        value={name}
+        onChange={(event) => setName(event.target.value)}
+        placeholder="nombre"
+      />
+      <button onClick={handleCreate}>crear</button>
+
       <select value={status} onChange={(event) => setStatus(event.target.value)}>
         <option value="">todos</option>
         <option value="todo">todo</option>
```

El `value` del input viene del estado y el `onChange` lo escribe, por eso se le
llama un componente controlado.

Escriba un nombre, pulse `crear` y valide que la tarea aparece primera en la
lista con estado `todo`.

## 8. Funcionalidad de actualización parcial

Agregue en `src/App.tsx` las líneas que se muestran en verde.

```diff
@@ -1,6 +1,6 @@
 // src/App.tsx
 import { useState } from "react";
-import { INITIAL_TASKS, type Task } from "./tasks";
+import { INITIAL_TASKS, type Status, type Task } from "./tasks";

 export default function App() {
   const [tasks, setTasks] = useState<Task[]>(INITIAL_TASKS);
@@ -23,6 +23,14 @@
     setName("");
   }

+  function handleStatus(id: string, next: Status) {
+    // devuelve la tarea con el estado nuevo, o la misma si no es la que cambia
+    const updateTask = (task: Task) =>
+      task.id === id ? { ...task, status: next } : task;
+
+    setTasks(tasks.map(updateTask));
+  }
+
   return (
     <main>
       <h1>Tareas ({filtered.length})</h1>
@@ -44,7 +52,17 @@
       <ul>
         {filtered.map((task) => (
           <li key={task.id}>
-            {task.name} — {task.status}
+            {task.name}
+            <select
+              value={task.status}
+              onChange={(event) =>
+                handleStatus(task.id, event.target.value as Status)
+              }
+            >
+              <option value="todo">todo</option>
+              <option value="doing">doing</option>
+              <option value="done">done</option>
+            </select>
           </li>
         ))}
       </ul>
```

Cambie el estado de una tarea y valide que la lista lo muestra. Con el filtro en
`todo`, la tarea que pasa a `done` desaparece de la lista, porque la lista se
deriva del filtro.

## 9. Funcionalidad de borrado

Agregue en `src/App.tsx` las líneas que se muestran en verde.

```diff
@@ -31,6 +31,10 @@
     setTasks(tasks.map(updateTask));
   }

+  function handleDelete(id: string) {
+    setTasks(tasks.filter((task) => task.id !== id));
+  }
+
   return (
     <main>
       <h1>Tareas ({filtered.length})</h1>
@@ -63,6 +67,7 @@
               <option value="doing">doing</option>
               <option value="done">done</option>
             </select>
+            <button onClick={() => handleDelete(task.id)}>borrar</button>
           </li>
         ))}
       </ul>
```

Pulse `borrar` en una tarea y valide que sale de la lista.

## 10. Validar el flujo completo en el navegador

Con las cinco acciones cubiertas, `src/App.tsx` queda así.

```tsx
// src/App.tsx
import { useState } from "react"
import { INITIAL_TASKS, type Status, type Task } from "./tasks"

export default function App() {
  const [tasks, setTasks] = useState<Task[]>(INITIAL_TASKS)
  const [status, setStatus] = useState("")
  const [name, setName] = useState("")

  // la lista filtrada se calcula en cada render, no es estado
  const filtered =
    status === "" ? tasks : tasks.filter((task) => task.status === status)

  function handleCreate() {
    const task: Task = {
      id: crypto.randomUUID(),
      name,
      status: "todo",
      created_at: new Date().toISOString(),
    }
    // arma un arreglo nuevo en lugar de empujar sobre el anterior
    setTasks([task, ...tasks])
    setName("")
  }

  function handleStatus(id: string, next: Status) {
    // devuelve la tarea con el estado nuevo, o la misma si no es la que cambia
    const updateTask = (task: Task) =>
      task.id === id ? { ...task, status: next } : task

    setTasks(tasks.map(updateTask))
  }

  function handleDelete(id: string) {
    setTasks(tasks.filter((task) => task.id !== id))
  }

  return (
    <main>
      <h1>Tareas ({filtered.length})</h1>

      <input
        value={name}
        onChange={(event) => setName(event.target.value)}
        placeholder="nombre"
      />
      <button onClick={handleCreate}>crear</button>

      <select
        value={status}
        onChange={(event) => setStatus(event.target.value)}
      >
        <option value="">todos</option>
        <option value="todo">todo</option>
        <option value="doing">doing</option>
        <option value="done">done</option>
      </select>

      <ul>
        {filtered.map((task) => (
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
  )
}
```

## 11. Preguntas de entrevista

Las siguientes preguntas son las que un entrevistador puede hacer sobre lo que
se construyó en esta nota.

#### 11.1. Estado y renderizado

1. ¿Para qué sirve el `useState` que guarda `tasks` en `App`?

   Guarda la lista de tareas entre renders, una variable normal se volvería a
   crear en cada render y React no se enteraría de que cambió

2. ¿Qué función vuelve a dibujar la lista de tareas en la pantalla?

   `setTasks`, la que devuelve el `useState`, y `setStatus` cuando cambia el
   filtro. Al llamarlas React vuelve a ejecutar el cuerpo de la función `App`,
   arma el JSX nuevo, lo compara con el del render anterior y cambia en el DOM
   solo lo que difiere

3. ¿Por qué `handleCreate` arma un arreglo nuevo con `[task, ...tasks]` en
   lugar de hacer `tasks.push(task)`?

   `push` muta el mismo arreglo, la referencia no cambia y React no vuelve a
   dibujar

4. ¿Por qué `filtered` es una constante y no otro `useState`?

   Se calcula de `tasks` y de `status` en cada render, guardarlo obliga a
   actualizarlo en cada alta, cambio y borrado, y tarde o temprano queda
   desfasado

5. ¿Para qué sirve el `key` del `li` en el `map` de la lista de tareas?

   React identifica cada `li` entre renders y no rehace el DOM de todos

6. ¿Qué pasa si al `input` del nombre se le quita el `value` y queda solo el
   `onChange`?

   Deja de ser un componente controlado, el texto pasa a vivir en el DOM y el
   `setName("")` de `handleCreate` ya no vacía la caja

7. ¿Por qué `handleStatus` recibe el `id` de la tarea y no su posición en la
   lista?

   La posición en `filtered` no es la misma que en `tasks` cuando hay un filtro
   puesto, y `handleStatus` recorre `tasks`

#### 11.2. Tipos y datos

1. ¿Qué aporta declarar `Status` como unión de literales en vez de tipar el
   estado como `string`?

   El compilador rechaza un estado que no existe, como `"terminado"`, y el
   editor autocompleta los tres válidos

2. ¿Por qué hace falta el `as Status` en el `onChange` del selector de cada
   tarea?

   `event.target.value` está tipado como `string`, y un `string` cualquiera no
   entra donde se espera la unión `"todo" | "doing" | "done"`. El `as Status`
   apaga esa verificación, y vale solo mientras los tres `<option>` lleven
   exactamente esos valores, porque si alguien agrega otro el compilador no
   avisa

3. ¿Por qué el `id` de una tarea nueva sale de `crypto.randomUUID()` y no de
   `tasks.length + 1`?

   Al borrar, `length` vuelve a dar un número ya usado y dos tareas terminarían
   con el mismo `key`

4. ¿Qué pasa con las tareas creadas al recargar la página?

   Se pierden, el estado vive en memoria y la página vuelve a arrancar con las
   seis tareas de `INITIAL_TASKS`
