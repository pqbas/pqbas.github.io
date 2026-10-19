import sys
o = []
def rect(x, y, w, h, bg, stroke="#1e1e1e", dash=False):
    d = ' stroke-dasharray="10 8"' if dash else ''
    o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{bg}" stroke="{stroke}" stroke-width="2"{d}/>')
def text(x, y, s, size=15, anchor="start", color="#1e1e1e", bold=False, italic=False):
    b = (' font-weight="bold"' if bold else '') + (' font-style="italic"' if italic else '')
    for i, l in enumerate(s.split("\n")):
        o.append(f'<text x="{x}" y="{y + i*size*1.35}" font-size="{size}" text-anchor="{anchor}" fill="{color}"{b} xml:space="preserve">{l}</text>')
def arrow(x1, y1, x2, y2, color="#1e1e1e", dash=False):
    d = ' stroke-dasharray="6 6"' if dash else ''
    m = "g" if dash else "a"
    o.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="2.5" marker-end="url(#{m})"{d}/>')

text(750, 38, "Secure by Design: recorre el request capa por capa", 28, "middle", bold=True)
text(750, 70, "las decisiones de seguridad se toman al diseñar la arquitectura, no se parchan al final", 17, "middle", color="#495057", italic=True)
# 6 infraestructura (contenedor)
rect(170, 95, 1170, 395, "#f3f0ff", "#7048e8", True)
text(190, 125, "6  INFRAESTRUCTURA  ·  ¿dónde corre?", 18, color="#7048e8", bold=True)
text(190, 150, "VPC privada + VPC endpoints  ·  IAM: un rol por servicio  ·  KMS + TLS  ·  Secrets Manager  ·  Bedrock en tu cuenta y región", 15, color="#5f3dc4")
capas = [
    ("1  IDENTIDAD", "¿quién es?", "· Cognito / OAuth / JWT\n· user_id de la sesión,\n   nunca del LLM"),
    ("2  ENTRADA", "¿qué entra?", "· guardrail G1\n· injection, alcance\n· input del usuario\n   como dato, no orden"),
    ("3  DATOS", "¿qué ve el modelo?", "· lo mínimo necesario\n· PII enmascarada\n· RAG filtra por los\n   permisos del usuario"),
    ("4  ACCIONES", "¿qué puede hacer?", "· mínimo privilegio\n· lectura antes que\n   escritura\n· args validados (G2)\n· HITL si hay impacto"),
    ("5  SALIDA", "¿qué responde?", "· grounding / citas (G3)\n· valida el schema\n· sin PII ni contenido\n   dañino"),
]
rect(20, 185, 120, 70, "#a5d8ff"); text(80, 226, "usuario", 20, "middle", bold=True)
rect(1365, 185, 115, 70, "#a5d8ff"); text(1422, 226, "usuario", 20, "middle", bold=True)
arrow(140, 220, 186, 220)
for i, (t, q, b) in enumerate(capas):
    x = 190 + i*230
    rect(x, 175, 190, 90, "#ffc9c9" if i in (1, 3, 4) else "#d3f9d8")
    text(x+95, 212, t, 19, "middle", bold=True)
    text(x+95, 240, q, 15, "middle", color="#495057", italic=True)
    text(x+5, 292, b, 15)
    arrow(x+190, 220, x+226, 220) if i < 4 else arrow(x+190, 220, 1361, 220)
    arrow(x+95, 400, x+95, 526, "#e67700", True)
# 7 auditoría
rect(170, 530, 1170, 85, "#fff3bf", "#e67700")
text(190, 560, "7  AUDITORÍA  ·  ¿qué queda registrado?", 18, color="#e67700", bold=True)
text(190, 590, "quién pidió  ·  qué datos se usaron  ·  qué respondió el modelo  ·  qué acción se ejecutó  ·  sin PII en claro  ·  CloudTrail + logs", 15, color="#a85d00")
text(750, 655, "rojo = donde actúan los guardrails (G1, G2, G3)   ·   detecto, pero asumo que falla: limito el daño y todo queda auditado", 15, "middle", color="#495057", italic=True)
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1500" height="680" font-family="sans-serif">
<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#1e1e1e"/></marker>
<marker id="g" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#e67700"/></marker></defs>
<rect width="1500" height="680" fill="#fff"/>{"".join(o)}</svg>'''
open(sys.argv[1], "w").write(svg)
