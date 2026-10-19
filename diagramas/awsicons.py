"""Convierte íconos de aws-architecture-icons.excalidrawlib a fragmentos SVG."""
import json
from html import escape
from pathlib import Path

LIB = json.loads((Path(__file__).with_name("aws-architecture-icons.excalidrawlib")).read_text())
ITEMS = {i["name"]: i["elements"] for i in LIB["libraryItems"]}
FONTS = {1: "Virgil, 'Comic Sans MS', sans-serif", 2: "Helvetica, Arial, sans-serif", 3: "monospace"}


def _el(e, dx, dy):
    svg = _shape(e, dx, dy)
    if e.get("angle"):
        import math
        cx, cy = e["x"] - dx + e["width"]/2, e["y"] - dy + e["height"]/2
        svg = f'<g transform="rotate({math.degrees(e["angle"])} {cx} {cy})">{svg}</g>'
    return svg


def _shape(e, dx, dy):
    x, y = e["x"] - dx, e["y"] - dy
    st = e.get("strokeColor", "#1e1e1e")
    bg = e.get("backgroundColor", "transparent")
    bg = "none" if bg == "transparent" else bg
    sw = e.get("strokeWidth", 1)
    op = e.get("opacity", 100) / 100
    common = f'stroke="{st}" stroke-width="{sw}" fill="{bg}" opacity="{op}"'
    if e.get("strokeStyle") == "dashed":
        common += ' stroke-dasharray="8 6"'
    t = e["type"]
    if t == "rectangle":
        r = min(e["width"], e["height"]) * 0.15 if e.get("roundness") else 0
        return f'<rect x="{x}" y="{y}" width="{e["width"]}" height="{e["height"]}" rx="{r}" {common}/>'
    if t == "ellipse":
        return (f'<ellipse cx="{x + e["width"]/2}" cy="{y + e["height"]/2}" rx="{e["width"]/2}" '
                f'ry="{e["height"]/2}" {common}/>')
    if t == "diamond":
        w, h = e["width"], e["height"]
        return f'<polygon points="{x+w/2},{y} {x+w},{y+h/2} {x+w/2},{y+h} {x},{y+h/2}" {common}/>'
    if t in ("line", "arrow"):
        pts = " ".join(f"{x + px},{y + py}" for px, py in e["points"])
        closed = len(e["points"]) > 2 and e["points"][0] == e["points"][-1]
        tag = "polygon" if closed and bg != "none" else "polyline"
        if tag == "polyline":
            common = common.replace(f'fill="{bg}"', 'fill="none"')
        return f'<{tag} points="{pts}" stroke-linejoin="round" stroke-linecap="round" {common}/>'
    if t == "text":
        fs = e.get("fontSize", 20)
        anchor = {"left": "start", "center": "middle", "right": "end"}[e.get("textAlign", "left")]
        tx = {"start": x, "middle": x + e["width"]/2, "end": x + e["width"]}[anchor]
        lines = e["text"].split("\n")
        lh = e.get("lineHeight", 1.25) * fs
        return "".join(
            f'<text x="{tx}" y="{y + lh*i + fs*0.95}" font-size="{fs}" text-anchor="{anchor}" '
            f'font-family="{FONTS.get(e.get("fontFamily", 1), FONTS[2])}" fill="{st}">{escape(l)}</text>'
            for i, l in enumerate(lines))
    return ""


def icon(name, x, y, height=80, label=True):
    """Ícono escalado a `height`, con su esquina superior izquierda en (x, y). Devuelve (svg, ancho)."""
    els = [e for e in ITEMS[name] if not e.get("isDeleted") and (label or e["type"] != "text")]
    # sin etiqueta, el marco del ícono es su rectángulo más grande (las decoraciones pueden salirse)
    rects = [e for e in els if e["type"] == "rectangle"]
    ref = [max(rects, key=lambda e: e["width"] * e["height"])] if rects and not label else els
    x0 = min(e["x"] for e in ref); y0 = min(e["y"] for e in ref)
    x1 = max(e["x"] + e["width"] for e in ref); y1 = max(e["y"] + e["height"] for e in ref)
    s = height / (y1 - y0)
    body = "".join(_el(e, x0, y0) for e in els)
    if rects and not label:
        # recorta las decoraciones que se salen del marco
        global _N
        _N += 1
        clip = f'<clipPath id="c{_N}"><rect x="-2" y="-2" width="{x1 - x0 + 4}" height="{y1 - y0 + 4}"/></clipPath>'
        body = f'{clip}<g clip-path="url(#c{_N})">{body}</g>'
    return f'<g transform="translate({x},{y}) scale({s})">{body}</g>', (x1 - x0) * s


_N = 0
