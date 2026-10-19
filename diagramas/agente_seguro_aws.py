"""Genera content/AI/agente-seguro-aws.{excalidraw,svg,png}, arquitectura AWS con las capas de secure by design."""
import json, random, subprocess
from pathlib import Path
from awsicons import ITEMS, _el

OUT = Path(__file__).resolve().parent.parent / "content" / "AI"
els = []
GATE, PINK, VPC, SUB, GREEN, GRAY = "#ffc9c9", "#e7157b", "#8c4fff", "#147eba", "#2b8a3e", "#495057"


def base(t, x, y, w, h, **k):
    e = dict(type=t, id=f"e{len(els)}", x=x, y=y, width=w, height=h, angle=0,
             strokeColor=k.get("stroke", "#1e1e1e"), backgroundColor=k.get("bg", "transparent"),
             fillStyle="solid", strokeWidth=k.get("sw", 2), strokeStyle=k.get("style", "solid"), roughness=1,
             opacity=100, groupIds=[], roundness={"type": 3} if t == "rectangle" and k.get("round", True) else None,
             seed=random.randint(1, 10**9), version=1, versionNonce=random.randint(1, 10**9),
             isDeleted=False, boundElements=[], updated=1, link=None, locked=False)
    els.append(e); return e


def text(x, y, s, size=16, w=None, align="left", cid=None, color="#1e1e1e"):
    lines = s.split("\n")
    w = w or max(len(l) for l in lines) * size * 0.55
    e = base("text", x, y, w, len(lines) * size * 1.25, stroke=color)
    e.update(text=s, originalText=s, fontSize=size, fontFamily=1, textAlign=align,
             verticalAlign="middle", containerId=cid, lineHeight=1.25, autoResize=True)
    return e


def box(x, y, w, h, label, bg, size=20, **k):
    r = base("rectangle", x, y, w, h, bg=bg, **k)
    n = len(label.split("\n"))
    t = text(x, y + h/2 - n*size*1.25/2, label, size, w, "center", r["id"])
    r["boundElements"].append({"type": "text", "id": t["id"]})
    return r


def zone(x, y, w, h, color, label, bg="transparent", style="solid"):
    base("rectangle", x, y, w, h, stroke=color, bg=bg, style=style, round=False)
    text(x + 12, y + 8, label, 16, color=color)


def arrow(x1, y1, x2, y2, label=None, color="#1e1e1e", lx=0, ly=-22):
    a = base("arrow", x1, y1, x2-x1, y2-y1, stroke=color)
    a.update(points=[[0, 0], [x2-x1, y2-y1]], startBinding=None, endBinding=None,
             startArrowhead=None, endArrowhead="arrow", roundness={"type": 2})
    if label:
        text((x1+x2)/2 + lx, (y1+y2)/2 + ly, label, 15, color=GRAY)


def icon(name, x, y, h):
    """Copia el ícono de la librería como elementos editables, sin su texto, escalado a alto h."""
    src = [e for e in ITEMS[name] if not e.get("isDeleted") and e["type"] != "text"]
    rects = [e for e in src if e["type"] == "rectangle"]
    f = max(rects, key=lambda e: e["width"] * e["height"]) if rects else None
    if f:  # descarta decoraciones fuera del marco
        src = [e for e in src if f["x"] - 2 <= e["x"] + e["width"]/2 <= f["x"] + f["width"] + 2
               and f["y"] - 2 <= e["y"] + e["height"]/2 <= f["y"] + f["height"] + 2]
        x0, y0, fw, fh = f["x"], f["y"], f["width"], f["height"]
    else:
        x0 = min(e["x"] for e in src); y0 = min(e["y"] for e in src)
        fw = max(e["x"] + e["width"] for e in src) - x0; fh = max(e["y"] + e["height"] for e in src) - y0
    s, g = h / fh, f"g{len(els)}"
    for e in src:
        c = json.loads(json.dumps(e))
        c.update(id=f"e{len(els)}", x=x + (e["x"] - x0) * s, y=y + (e["y"] - y0) * s,
                 width=e["width"] * s, height=e["height"] * s, groupIds=[g], boundElements=[],
                 strokeWidth=max(0.5, e.get("strokeWidth", 1) * s), seed=random.randint(1, 10**9))
        if "points" in c:
            c["points"] = [[px * s, py * s] for px, py in e["points"]]
        els.append(c)
    return fw * s


# --- título y cuenta
text(170, 8, "Agente seguro en AWS: secure by design aplicado a la arquitectura", 26)
zone(160, 60, 1640, 840, PINK, "cuenta AWS del banco · us-east-1 (los datos no salen de la región)")

# --- usuario
box(20, 250, 100, 260, "usuario", "#a5d8ff")

# --- 1 identidad
text(178, 200, "1 IDENTIDAD", 18, color=PINK)
icon("API Gateway", 205, 330, 60); text(185, 395, "API Gateway", 15)
icon("WAF", 178, 450, 40); text(178, 494, "WAF", 14)
icon("Cognito", 262, 450, 40); text(250, 494, "Cognito", 14)
text(175, 525, "· Cognito emite el JWT\n· API GW valida firma\n  y expiración\n· WAF: rate limit,\n  ataques web", 14, color=GRAY)

# --- 6 infraestructura: VPC y subred privada
zone(360, 100, 1090, 640, VPC, "6 INFRAESTRUCTURA · VPC (red privada)", bg="#f4f0ff")
zone(380, 140, 1050, 585, SUB, "subred privada · sin NAT, sin internet", bg="#e6f2f8")

# --- tu código: Lambda con las tres puertas
zone(400, 180, 700, 525, GREEN, "", bg="#ebfbee", style="dashed")
icon("Lambda", 412, 190, 34)
text(455, 195, "Lambda / ECS · tu código, fuera del LLM · rol IAM mínimo", 16, color=GREEN)

box(440, 245, 120, 60, "G3", GATE)
text(440, 312, "5 SALIDA\n· grounding y citas válidas\n· sin PII\n· sin contenido dañino", 15)
box(440, 430, 120, 60, "G1", GATE)
text(440, 500, "2 ENTRADA\n· enmascara PII\n· detecta prompt injection", 15)
box(820, 560, 120, 60, "G2", GATE)
text(820, 628, "4 ACCIONES\n· args válidos · user_id de la sesión\n· HITL si la operación es crítica", 15)

# --- VPC endpoints
icon("Interface Endpoint", 1200, 330, 45); text(1175, 380, "VPC endpoint", 14, color=VPC)
icon("Interface Endpoint", 1200, 568, 45); text(1175, 618, "VPC endpoint", 14, color=VPC)

# --- servicios AWS fuera de la VPC
icon("Amazon Bedrock", 1560, 320, 60)
text(1535, 388, "Bedrock (LLM)\nno se confía en él\nno entrena con tus datos", 15)
icon("DynamoDB", 1560, 560, 60)
text(1520, 628, "Tools / datos del cliente\n3 DATOS: cifrado KMS,\nfiltrado por user_id", 15)

# --- flujo
arrow(120, 470, 200, 375)
arrow(268, 380, 440, 455, "entrada + JWT", lx=-35, ly=25)
arrow(560, 455, 1195, 355, "entrada sanitizada", lx=40, ly=-55)
arrow(1250, 352, 1555, 350, color=GREEN)
arrow(1195, 340, 560, 270, "respuesta", lx=0, ly=-35)
arrow(1195, 365, 940, 575, "acción (tool call)", lx=30, ly=5)
arrow(940, 590, 1195, 590, "acción aprobada", lx=-110, ly=-28)
arrow(1250, 590, 1555, 590, color=GREEN)
arrow(440, 275, 268, 335, "respuesta verificada", lx=-130, ly=-75)
arrow(200, 345, 120, 300)
text(1460, 470, "verde = PrivateLink,\nno pasa por internet", 14, color=GREEN)

# --- 7 auditoría
zone(380, 760, 1400, 120, PINK, "", bg="#fff8e6")
icon("CloudWatch", 400, 785, 50); icon("CloudTrail", 470, 785, 50)
text(540, 778, "7 AUDITORÍA", 18, color=PINK)
text(540, 805, "CloudWatch Logs: prompt, decisión de cada guardrail, tools usadas y usuario, sin PII ni secretos\n"
              "CloudTrail: cada llamada a la API de AWS (quién invocó qué modelo, qué secreto leyó, cuándo)", 15)

W, H = 1820, 920
json.dump(dict(type="excalidraw", version=2, source="https://excalidraw.com", elements=els,
               appState=dict(viewBackgroundColor="#ffffff", gridSize=None), files={}),
          open(OUT / "agente-seguro-aws.excalidraw", "w"), ensure_ascii=False, indent=1)

# --- SVG/PNG con el mismo renderer de awsicons
body = []
for e in els:
    if e["type"] == "text" and e.get("containerId"):
        e = dict(e, fontFamily=2)
    elif e["type"] == "text":
        e = dict(e, fontFamily=2)
    s = _el(e, 0, 0)
    if e["type"] == "arrow":
        s = s.replace("<polyline", f'<polyline marker-end="url(#m{e["strokeColor"][1:]})"')
    body.append(s)
markers = "".join(f'<marker id="m{c[1:]}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
                  f'orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="{c}"/></marker>' for c in ("#1e1e1e", GREEN))
svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}"><defs>{markers}</defs>'
       f'<rect width="{W}" height="{H}" fill="#fff"/>{"".join(body)}</svg>')
(OUT / "agente-seguro-aws.svg").write_text(svg)
subprocess.run(["google-chrome", "--headless", "--disable-gpu", f"--screenshot={OUT / 'agente-seguro-aws.png'}",
                f"--window-size={W},{H}", f"file://{OUT / 'agente-seguro-aws.svg'}"], capture_output=True)
