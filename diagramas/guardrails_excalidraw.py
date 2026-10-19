import json, random, sys
els = []
def base(t, x, y, w, h, **k):
    e = dict(type=t, id=f"e{len(els)}", x=x, y=y, width=w, height=h, angle=0,
             strokeColor=k.get("stroke", "#1e1e1e"), backgroundColor=k.get("bg", "transparent"),
             fillStyle="solid", strokeWidth=2, strokeStyle=k.get("style", "solid"), roughness=1,
             opacity=100, groupIds=[], roundness={"type": 3} if t == "rectangle" else None,
             seed=random.randint(1, 10**9), version=1, versionNonce=random.randint(1, 10**9),
             isDeleted=False, boundElements=[], updated=1, link=None, locked=False)
    els.append(e); return e
def text(x, y, s, size=20, w=None, align="left", cid=None, color="#1e1e1e"):
    lines = s.split("\n")
    w = w or max(len(l) for l in lines) * size * 0.55
    e = base("text", x, y, w, len(lines) * size * 1.25, stroke=color)
    e.update(text=s, originalText=s, fontSize=size, fontFamily=1, textAlign=align,
             verticalAlign="middle", containerId=cid, lineHeight=1.25, autoResize=True)
    return e
def box(x, y, w, h, label, bg, size=22, style="solid"):
    r = base("rectangle", x, y, w, h, bg=bg, style=style)
    n = len(label.split("\n"))
    t = text(x, y + h/2 - n*size*1.25/2, label, size, w, "center", r["id"])
    r["boundElements"].append({"type": "text", "id": t["id"]})
    return r
def arrow(x1, y1, x2, y2, label=None):
    a = base("arrow", x1, y1, x2-x1, y2-y1)
    a.update(points=[[0, 0], [x2-x1, y2-y1]], startBinding=None, endBinding=None,
             startArrowhead=None, endArrowhead="arrow", roundness={"type": 2})
    if label: text((x1+x2)/2 + 10, (y1+y2)/2 - 12, label, 16, color="#868e96")

GATE, LLM = "#ffc9c9", "#e9ecef"
text(220, 0, "Guardrails: el LLM queda encerrado, todo pasa por tus puertas", 26)
base("rectangle", 200, 60, 900, 470, bg="#ebfbee", style="dashed")
text(215, 70, "tu código (determinista, fuera del LLM)", 18, color="#2f9e44")
box(20, 200, 140, 60, "usuario", "#a5d8ff")
box(240, 190, 180, 80, "G1\nENTRADA", GATE)
box(500, 170, 200, 120, "LLM\n(no se confía)", LLM)
box(780, 190, 180, 80, "G3\nSALIDA", GATE)
box(1140, 200, 140, 60, "usuario", "#a5d8ff")
box(510, 370, 180, 80, "G2\nACCIONES", GATE)
box(510, 600, 180, 60, "tool / API\ndel banco", "#ffec99", 18)
arrow(160, 230, 240, 230); arrow(420, 230, 500, 230)
arrow(700, 230, 780, 230); arrow(960, 230, 1140, 230)
arrow(600, 290, 600, 370, "pide tool"); arrow(600, 450, 600, 600)
text(225, 285, "· prompt injection\n· fuera de alcance\n· PII → bloquear o\n  enmascarar", 16)
text(785, 285, "· grounding / citas\n  válidas\n· formato (schema)\n· sin PII ni\n  contenido dañino", 16)
text(710, 400, "· ¿tool permitida?\n· ¿args válidos?\n· user_id de la sesión,\n  no del LLM\n· HITL si hay impacto", 16)
json.dump(dict(type="excalidraw", version=2, source="https://excalidraw.com", elements=els,
               appState=dict(viewBackgroundColor="#ffffff", gridSize=None), files={}),
          open(sys.argv[1], "w"), ensure_ascii=False, indent=1)
