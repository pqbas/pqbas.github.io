# diagramas

Generadores de los diagramas de `content/AI/`. Los SVG se pasan a PNG con Chrome headless.

- `awsicons.py`, convierte íconos de `aws-architecture-icons.excalidrawlib` a SVG con `icon(nombre, x, y, alto)`
- `infra_privada.py`, escribe `content/AI/infra-privada.{svg,png}` directamente
- `guardrails.py` y `secure_by_design.py`, reciben la ruta del SVG de salida, por ejemplo
  `python3 guardrails.py ../content/AI/guardrails.svg`, y luego
  `google-chrome --headless --screenshot=<png> --window-size=<w>,<h> file://<svg>`
- `guardrails_excalidraw.py`, escribe la versión editable `.excalidraw`
- `agente_seguro_aws.py`, arquitectura AWS con las capas de secure by design, escribe `content/AI/agente-seguro-aws.{excalidraw,svg,png}`
