---
title: Permitir localhost en el CORS de un bucket S3 con URLs prefirmadas
tags:
  - aws
  - s3
  - cors
  - cdk
---

Cuando una app sube archivos a S3 con URLs prefirmadas, el `PUT` lo hace el
navegador, no el servidor. Es una petición cross-origin, así que el origen de la
página tiene que estar en el CORS del bucket. En local ese origen es
`http://localhost:3000`, que normalmente no está permitido, y la subida falla.

## 1. El síntoma

En la consola del navegador, o en la UI de la app:

```
TypeError: NetworkError when attempting to fetch resource.
```

El mensaje no menciona CORS en ningún lado. Es a propósito: el navegador oculta
el detalle de una respuesta que la política de origen cruzado bloqueó, para no
filtrar información de otro dominio. Por eso un fallo de CORS y una caída real
de red se ven idénticos desde JavaScript.

Dos señales de que es CORS y no la red:

| Señal | Dónde mirar |
| ----- | ----------- |
| La pestaña Network muestra el `PUT` o un `OPTIONS` en estado `(blocked)` o CORS error | DevTools → Network |
| La petición al propio backend funciona y solo falla la que va a `*.s3.amazonaws.com` | DevTools → Network |

## 2. Confirmarlo desde la terminal

```bash
aws s3api get-bucket-cors --bucket <bucket> --region <region>
```

```json
{
  "CORSRules": [
    {
      "AllowedMethods": ["GET", "HEAD", "PUT"],
      "AllowedOrigins": ["https://miapp.example.com"],
      "AllowedHeaders": ["*"],
      "MaxAgeSeconds": 3000
    }
  ]
}
```

Si `AllowedOrigins` no incluye tu origen local, ese es el problema. Un
`NoSuchCORSConfiguration` significa que el bucket no tiene CORS y entonces
**ninguna** subida desde el navegador funciona.

## 3. Arreglo en el CDK

Es el que conviene: queda versionado y le sirve a cualquiera que levante el
proyecto en local.

Si el bucket se define con `aws_s3.Bucket`, va directo en el constructor:

```python
from aws_cdk import aws_s3 as s3

allowed_origins = ["https://miapp.example.com"]
if environment != "prd":
    allowed_origins += ["http://localhost:3000", "http://127.0.0.1:3000"]

bucket = s3.Bucket(
    self,
    "Uploads",
    cors=[
        s3.CorsRule(
            allowed_methods=[s3.HttpMethods.GET, s3.HttpMethods.HEAD, s3.HttpMethods.PUT],
            allowed_origins=allowed_origins,
            allowed_headers=["*"],
            max_age=3000,
        )
    ],
)
```

Si el CORS se aplica después del despliegue con un custom resource —típico
cuando el origen depende de un recurso que todavía no existe, como el dominio de
una distribución de CloudFront— la regla se arma igual y se pasa a las dos
llamadas:

```python
cf_origin = Fn.join("", ["https://", distribution.distribution_domain_name])
allowed_origins = [cf_origin]
if environment != "prd":
    allowed_origins += ["http://localhost:3000", "http://127.0.0.1:3000"]

cors_rules = [
    {
        "AllowedMethods": ["GET", "HEAD", "PUT"],
        "AllowedOrigins": allowed_origins,
        "AllowedHeaders": ["*"],
        "MaxAgeSeconds": 3000,
    }
]

cr.AwsCustomResource(
    self,
    "SetUploadsBucketCors",
    on_create=cr.AwsSdkCall(
        service="S3",
        action="putBucketCors",
        parameters={
            "Bucket": bucket.bucket_name,
            "CORSConfiguration": {"CORSRules": cors_rules},
        },
        physical_resource_id=cr.PhysicalResourceId.of("SetUploadsBucketCors"),
    ),
    on_update=cr.AwsSdkCall(...),  # mismos parámetros que on_create
    policy=cr.AwsCustomResourcePolicy.from_statements(
        [iam.PolicyStatement(actions=["s3:PutBucketCORS"], resources=[bucket.bucket_arn])]
    ),
)
```

Dos detalles que importan:

- **`on_create` y `on_update` tienen que llevar la misma regla.** Si solo
  cambiás una, el despliegue siguiente revierte la otra y el bug vuelve sin que
  haya cambiado nada visible.
- **`putBucketCors` reemplaza la configuración entera**, no la mezcla. La lista
  tiene que incluir siempre los orígenes de producción, no solo el nuevo.

## 4. Arreglo temporal, sin desplegar

Sirve para probar en el momento. **El siguiente `cdk deploy` lo pisa**, porque
el stack vuelve a aplicar su propia configuración.

```bash
aws s3api put-bucket-cors --bucket <bucket> --region <region> \
  --cors-configuration '{
    "CORSRules": [{
      "AllowedMethods": ["GET", "HEAD", "PUT"],
      "AllowedOrigins": ["https://miapp.example.com", "http://localhost:3000"],
      "AllowedHeaders": ["*"],
      "MaxAgeSeconds": 3000
    }]
  }'
```

## 5. Verificar

Sin abrir el navegador, simulando el preflight que manda:

```bash
curl -s -o /dev/null -D - -X OPTIONS "https://<bucket>.s3.<region>.amazonaws.com/" \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: PUT"
```

Tiene que volver `200` con la cabecera:

```
Access-Control-Allow-Origin: http://localhost:3000
```

Si vuelve `403` con `AccessForbidden`, el origen sigue sin estar permitido.

## Por qué no poner localhost en producción

El CORS no protege el bucket —para eso están las políticas de IAM y la firma de
la URL—, pero sí define qué páginas pueden leer la respuesta. Permitir
`http://localhost:3000` en producción deja que cualquier página servida desde el
localhost de cualquier persona hable con tu bucket de producción usando las
credenciales que ya tenga en el navegador. No hace falta y el condicional por
entorno sale gratis.

## Cuando CORS no es el culpable

Si el preflight pasa y la subida igual falla, revisá en este orden:

| Causa | Cómo se ve |
| ----- | ---------- |
| URL prefirmada vencida | `403` con `Request has expired` |
| Cabecera firmada que el navegador no manda igual (p. ej. `Content-Type`) | `403` con `SignatureDoesNotMatch` |
| El rol que firma no tiene `s3:PutObject` | `403` desde el endpoint que genera la URL, no desde S3 |

Relacionado: [[Backend/crear-una-api]]
