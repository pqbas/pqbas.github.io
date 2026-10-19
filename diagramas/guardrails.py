import sys
o = []
def rect(x, y, w, h, bg, dash=False):
    d = ' stroke-dasharray="10 8"' if dash else ''
    o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{bg}" stroke="#1e1e1e" stroke-width="2"{d}/>')
def text(x, y, s, size=16, anchor="start", color="#1e1e1e", bold=False):
    b = ' font-weight="bold"' if bold else ''
    for i, l in enumerate(s.split("\n")):
        o.append(f'<text x="{x}" y="{y + i*size*1.3}" font-size="{size}" text-anchor="{anchor}" fill="{color}"{b} xml:space="preserve">{l}</text>')
def box(x, y, w, h, label, bg, size=22):
    rect(x, y, w, h, bg); n = len(label.split("\n"))
    text(x + w/2, y + h/2 - (n-1)*size*1.3/2 + size*0.35, label, size, "middle", bold=True)
def arrow(x1, y1, x2, y2, label=None):
    o.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#1e1e1e" stroke-width="2.5" marker-end="url(#a)"/>')
    if label: text((x1+x2)/2 + 10, (y1+y2)/2 + 5, label, 15, color="#868e96")
G, L = "#ffc9c9", "#e9ecef"
text(650, 35, "Guardrails: el LLM queda encerrado, todo pasa por tus puertas", 26, "middle", bold=True)
rect(200, 60, 900, 480, "#ebfbee", True)
text(215, 88, "tu código (determinista, fuera del LLM)", 17, color="#2f9e44", bold=True)
box(20, 200, 140, 60, "usuario", "#a5d8ff"); box(1140, 200, 140, 60, "usuario", "#a5d8ff")
box(240, 190, 180, 80, "G1\nENTRADA", G); box(500, 170, 200, 120, "LLM\n(no se confía)", L)
box(780, 190, 180, 80, "G3\nSALIDA", G); box(510, 370, 180, 80, "G2\nACCIONES", G)
box(510, 600, 180, 60, "tool / API\ndel banco", "#ffec99", 18)
arrow(160, 230, 236, 230); arrow(420, 230, 496, 230); arrow(700, 230, 776, 230)
arrow(960, 230, 1136, 230); arrow(600, 290, 600, 366, "pide tool"); arrow(600, 450, 600, 596)
text(240, 300, "· prompt injection\n· fuera de alcance\n· PII → bloquear o\n   enmascarar", 16)
text(785, 300, "· grounding / citas válidas\n· formato (schema)\n· sin PII ni contenido\n   dañino", 16)
text(710, 390, "· ¿tool permitida?\n· ¿args válidos?\n· user_id de la sesión, no del LLM\n· HITL si hay impacto", 16)
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1300" height="690" font-family="Segoe Print, Comic Sans MS, sans-serif">
<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#1e1e1e"/></marker></defs>
<rect width="1300" height="690" fill="#fff"/>{"".join(o)}</svg>'''
open(sys.argv[1], "w").write(svg)
