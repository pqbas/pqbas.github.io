---
title: Pipeline de procesamiento de documentos con Step Functions y Lambda
tags:
  - aws
  - step-functions
  - lambda
  - arquitectura
---

Patrón para convertir archivos que suben los usuarios —CVs, facturas,
contratos— en datos estructurados: el navegador sube a S3, una máquina de
estados orquesta, y una Lambda por archivo hace el trabajo. Abajo, la forma
general y los tres errores de diseño que aparecen siempre.

## 1. La forma

```
Navegador ──PUT prefirmado──> S3
    │
    └──inicia──> Step Functions
                     │
                     ├── Preparar      (una Lambda: arma la lista de items)
                     │
                     ├── Map           (una ejecución hija por archivo)
                     │     ├── Extraer     (archivo -> texto -> datos)
                     │     └── Indexar     (datos -> embeddings / búsqueda)
                     │
                     └── ¿Qué sigue?   (Choice: encadena o termina)
```

El navegador no manda el archivo al backend: pide una URL prefirmada y sube
directo a S3. Así el archivo no pasa por el servidor ni cuenta contra el límite
de tamaño de petición. A cambio, el bucket necesita CORS —ver
[[AWS/cors-s3-para-desarrollo-local]].

El frontend no espera: arranca la ejecución, recibe un ARN y consulta el estado
cada pocos segundos.

## 2. Por qué un Map y no un bucle

El `Map` distribuido lanza una ejecución hija por archivo, con concurrencia
configurable. Dos límites marcan su diseño:

| Límite | Valor | Consecuencia |
| ------ | ----- | ------------ |
| Datos de estado entre pasos | 256 KB | La salida agregada del Map no entra con cientos de ítems |
| Historial de ejecución | 25 000 eventos | Un Map inline con muchos ítems lo agota |

Por eso, a escala, el patrón es:

- `ExecutionType: EXPRESS` en el iterador — más barato y sin historial detallado.
- `ResultPath: DISCARD` — la salida del Map no vuelve al estado.
- `ResultWriter` a S3 — cada iteración escribe su resultado, éxito o fallo, en
  un prefijo propio.

Ese último punto importa: **si descartás la salida y no la escribís a S3, los
errores por ítem desaparecen**. No quedan en el historial de la ejecución
padre, que solo ve "el Map terminó".

## 3. Los tres errores de diseño

### Confundir "no pude empezar" con "fallé"

Una invocación de Lambda puede fallar **antes** de que tu código corra:

| Error | Cuándo |
| ----- | ------ |
| `Lambda.CodeArtifactUserPendingException` | La función de imagen estaba inactiva y se está reactivando (HTTP 409) |
| `Lambda.TooManyRequestsException` | Límite de concurrencia |
| `Lambda.ServiceException` | Fallo interno del servicio |
| `Lambda.SdkClientException` | Problema de red del cliente |

Los cuatro son temporales y el reintento es gratis: la función no se ejecutó,
no hubo cobro ni efectos. Sin un `Retry`, cualquiera de ellos manda el ítem al
camino de fallo.

El caso más molesto es el primero. Una Lambda de imagen de contenedor que lleva
tiempo sin invocarse pasa a `Inactive`; AWS la reactiva en segundos, pero
mientras tanto rechaza las invocaciones. En un entorno de pruebas poco usado,
la primera tanda del día falla entera y la segunda funciona — un patrón que
parece aleatorio hasta que se entiende.

```python
# Lista explícita, nunca States.ALL
task.add_retry(
    errors=[
        "Lambda.CodeArtifactUserPendingException",
        "Lambda.TooManyRequestsException",
        "Lambda.ServiceException",
        "Lambda.SdkClientException",
    ],
    interval=Duration.seconds(2),
    max_attempts=4,
    backoff_rate=2,
)
```

**Por qué no `States.ALL`:** un fallo ocurrido a mitad de la ejecución ya
consumió lo caro —tokens de un modelo, una escritura parcial— y reintentarlo lo
vuelve a pagar. Para esos errores el lugar del reintento es *dentro* de la
Lambda, acotado a la llamada que falló.

### Tolerar fallos y llamarlo éxito

Un `Map` suele configurarse con `ToleratedFailurePercentage: 100` para que una
tanda grande no se caiga entera por un archivo corrupto. Razonable, pero se
combina mal con otra práctica habitual: capturar el error con un `Catch` que
apunta a un estado `Pass`.

Un `Pass` **termina bien**. Entonces:

1. El ítem falla.
2. El `Catch` lo manda al `Pass`, que registra el fallo y termina con éxito.
3. La ejecución hija cuenta como exitosa.
4. El Map reporta 100% de éxito.
5. La ejecución padre termina en `SUCCEEDED`.

Resultado: **la consola dice verde y no se procesó nada**. El frontend, que
solo mira el estado de la ejecución, no tiene forma de saberlo; lo máximo que
puede decir es "terminó pero no encuentro el resultado".

No es un bug: es la combinación de dos decisiones sensatas por separado. Pero
hay que saberlo, porque cambia dónde se diagnostica.

### Que el frontend infiera el fallo

Si la UI deduce "no hay resultado, entonces algo falló", muestra un síntoma en
vez de una causa. Conviene que el estado del trabajo sea un dato explícito —una
fila por archivo con `status`, `error_type` y `error_cause`— y que la UI lo lea
en lugar de adivinarlo.

## 4. Dónde se diagnostica

En orden, del dato más agregado al más específico:

```bash
# 1. ¿Terminó la ejecución padre? (puede decir SUCCEEDED y aun así no haber hecho nada)
aws stepfunctions describe-execution --execution-arn <arn> --region <region>

# 2. ¿Cuántos ítems del Map fallaron de verdad?
aws stepfunctions list-map-runs --execution-arn <arn> --region <region>
aws stepfunctions describe-map-run --map-run-arn <arn> --region <region>

# 3. El resultado por ítem: aquí está la causa real
aws s3 ls s3://<bucket-de-resultados>/<prefijo>/<MapRunId>/ --recursive
```

El JSON por ítem trae el archivo de origen, el tipo de error y la causa. Es el
único lugar donde el fallo aparece como fallo.

Los logs de la Lambda sirven para confirmar: **si no hay ninguna línea en la
ventana de tiempo, la función nunca se ejecutó**, y el problema es de
invocación, no del código.

## 5. Lista de verificación

Al montar un pipeline así:

- [ ] `Retry` con lista explícita de errores de invocación en cada tarea Lambda
- [ ] `ResultWriter` a S3 si el Map descarta su salida
- [ ] Reintentos dentro de la Lambda para lo que falla durante la ejecución
- [ ] Un identificador estable por documento —un hash del contenido— para que
      reprocesar actualice en vez de duplicar
- [ ] Estado por ítem legible desde la UI, no inferido
- [ ] CORS en el bucket para cada origen que suba archivos
