---
title: Constantes para estimar sistemas
tags:
  - system-design
  - estimacion
  - rendimiento
  - entrevistas
---

Las cinco tablas que resuelven cualquier estimación de bolsillo. Los
multiplicadores dan los RPS, las latencias dan las conexiones, la capacidad dice
cuántas instancias y los tamaños dan el almacenamiento.

## 1. Latencias

| Operación                               | Tiempo      |
| --------------------------------------- | ----------- |
| Referencia a RAM                        | 100 ns      |
| Lectura aleatoria en SSD                | 100 µs      |
| Ida y vuelta dentro del datacenter      | 0.5 ms      |
| Consulta por índice con datos en RAM    | 1 ms        |
| Escritura con `commit`                  | 5 a 10 ms   |
| Búsqueda en disco magnético             | 10 ms       |
| Ida y vuelta entre regiones cercanas    | 10 ms       |
| Ida y vuelta cruzando el Atlántico      | 100 ms      |

## 2. Capacidad por instancia

| Pieza                            | Aguanta               |
| -------------------------------- | --------------------- |
| Postgres, lecturas por índice    | 3 000 a 5 000 /s      |
| Postgres, escrituras             | 500 a 1 000 /s        |
| Redis                            | 100 000 ops/s         |
| API en un contenedor chico       | 500 a 1 000 req/s     |
| Balanceador                      | decenas de miles /s   |
| Broker de Kafka                  | 100 000 mensajes/s    |

## 3. Tamaños

| Dato                             | Ocupa        |
| -------------------------------- | ------------ |
| Fila en Postgres, con índices    | 300 B        |
| `uuid`                           | 16 B         |
| `timestamptz`                    | 8 B          |
| Texto corto, un nombre o un tweet | 100 a 150 B |
| Foto                             | 1 MB         |
| Minuto de video                  | 50 MB        |
| Un millón de filas               | 300 MB       |

## 4. Multiplicadores de estimación

| Qué                              | Valor                                   |
| -------------------------------- | --------------------------------------- |
| DAU sobre MAU                    | 50%                                     |
| Escrituras por usuario al día    | 2 contenido, 5 productividad, 50 chat   |
| Lecturas sobre escrituras        | 1:1 chat, 10:1 acortador, 100:1 feed    |
| Pico sobre promedio              | 2×                                      |
| Horizonte de almacenamiento      | 5 años                                  |
| Segundos en un día               | 86 400, se redondea a 100 000           |
| Segundos en un año               | 30 millones                             |

## 5. Disponibilidad

| Nueves  | Caída al año |
| ------- | ------------ |
| 99%     | 3.7 días     |
| 99.9%   | 8.8 horas    |
| 99.99%  | 53 minutos   |
| 99.999% | 5 minutos    |

## 6. Las dos fórmulas

```text
RPS         = usuarios × acciones por día / 86 400
conexiones  = RPS × duración de la consulta
```

La segunda es la ley de Little, y despejada al revés da el techo de una
instancia. Con un pool de 20 y consultas de 10 ms, el máximo es 2 000 RPS.

## 7. De dónde salen

| Fuente                                      | Qué aporta                                                            |
| ------------------------------------------- | --------------------------------------------------------------------- |
| Alex Xu, *System Design Interview*, cap. 2  | Los multiplicadores, los nueves y el método de escribir los supuestos |
| Jeff Dean, *Latency numbers*                | La tabla de latencias                                                  |
| Martin Kleppmann, *DDIA*, cap. 1            | Los parámetros de carga y medir con percentiles, no con promedios      |

Ninguno de los dos libros da un número universal de escrituras por usuario,
porque depende del producto. El número lo propone quien diseña, lo dice en voz
alta como supuesto y sigue.

Aplicadas a un caso concreto, en
[[Tutoriales/todo-app/5-system-design|el system design de la todo-app]].
