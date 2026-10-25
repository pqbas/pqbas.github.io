---
title: Índices en bases de datos
tags:
  - databases
  - sql
  - sqlite
  - postgresql
  - snowflake
---

## 1. Qué es?

Un índice es una estructura que guarda una copia ordenada de los valores de una
o más columnas junto con la ubicación de la fila a la que pertenece cada valor

```
# Un índice sobre status
# donde la fila se identifica por su `rowid` en SQLite,

status   → indice
done     → 3
done     → 7
doing    → 1
todo     → 2
todo     → 5
```

De modo que la base puede encontrar un valor sin recorrer la tabla completa,
porque la base lo usa por su cuenta cuando una consulta filtra u ordena por esa
columna.

Funciona igual que el índice al final de un libro, donde para encontrar en qué
página aparece "SQLite" no se leen las 500 páginas, sino que se busca la palabra
en la lista alfabética y se salta a la página que indica.

## 2. Cómo funciona?

Sin índice, la siguiente consulta revisa las filas una por una, lo que se conoce
como _full scan_:

```sql
SELECT * FROM clientes WHERE email = 'x@y.com';
```

Con un índice sobre `email`, la base busca en una estructura ordenada, casi
siempre un B-tree, y llega directo a la fila. En una tabla de un millón de filas
la diferencia es revisar un millón de filas o dar unos 20 pasos.

```sql
CREATE INDEX clientes_email_idx ON clientes (email);
```

## 3. Costo

La copia ordenada ocupa espacio y se actualiza en cada `INSERT`, `UPDATE` y
`DELETE`, por lo que el índice acelera las lecturas a cambio de volver algo más
lentas las escrituras. Conviene crearlo solo sobre columnas que aparecen seguido
en `WHERE`, `JOIN` u `ORDER BY` y que tienen muchos valores distintos.

`PRIMARY KEY` y `UNIQUE` son restricciones que además crean un índice, mientras
que un índice común solo acelera la búsqueda.

## 4. Qué se puede indexar

Casi cualquier columna, aunque el tipo de índice depende del dato y del motor.

| Caso                            | Cómo se indexa                                        |
| ------------------------------- | ----------------------------------------------------- |
| Números, fechas, texto corto    | B-tree común                                          |
| Varias columnas                 | Índice compuesto, por ejemplo `(cliente_id, fecha)`   |
| Expresiones                     | Índice sobre la expresión, por ejemplo `lower(email)` |
| Solo una parte de las filas     | Índice parcial con `WHERE`                            |
| `jsonb`, arrays, texto completo | GIN en PostgreSQL                                     |
| Datos geográficos               | GiST en PostgreSQL                                    |
| `TEXT` o `BLOB` en MySQL        | Índice por prefijo, por ejemplo `email(50)`           |

## 5. Por motor

| Motor      | Índices                                                                                              |
| ---------- | ---------------------------------------------------------------------------------------------------- |
| SQLite     | Solo B-tree, admite expresiones y parciales, y el texto completo y lo espacial van en FTS5 y R\*Tree |
| PostgreSQL | B-tree por defecto, más GIN, GiST, BRIN y hash según el dato                                         |
| Snowflake  | Las tablas estándar no tienen índices, se usan _clustering keys_ o _search optimization_             |

En Snowflake solo las _hybrid tables_ aceptan índices (ver
[[Snowflake/fundamentos|fundamentos de Snowflake]]).

## 6. Dónde aparece

- [[Tutoriales/todo-app/2-conectar-una-base-de-datos|Conectar una API a una base de datos]]
  crea un índice sobre `status` porque el listado de tareas filtra por esa
  columna.
