"""Genera content/AI/infra-privada.{svg,png} con íconos de AWS."""
import subprocess
from pathlib import Path
from awsicons import icon

OUT = Path(__file__).resolve().parent.parent / "content" / "AI"
o = []
def rect(x, y, w, h, bg, stroke="#1e1e1e", dash=False, rx=12):
    d = ' stroke-dasharray="10 8"' if dash else ''
    o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{bg}" stroke="{stroke}" stroke-width="2"{d}/>')
def text(x, y, s, size=15, anchor="start", color="#1e1e1e", bold=False, italic=False):
    b = (' font-weight="bold"' if bold else '') + (' font-style="italic"' if italic else '')
    for i, l in enumerate(s.split("\n")):
        o.append(f'<text x="{x}" y="{y + i*size*1.35}" font-size="{size}" text-anchor="{anchor}" fill="{color}"{b} xml:space="preserve">{l}</text>')
def ic(name, x, y, h):
    s, w = icon(name, x, y, h, label=False); o.append(s); return w
def arrow(x1, y1, x2, y2, color="#1e1e1e", m="a"):
    o.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="2.5" marker-end="url(#{m})"/>')

text(750, 38, "Infraestructura: el agente vive en una red privada y habla con AWS sin pasar por internet", 24, "middle", bold=True)
# cuenta AWS
rect(150, 70, 1330, 600, "#fff", "#e7157b", rx=4)
ic("AWS account", 150, 70, 0.1) if False else None
text(170, 97, "cuenta AWS del banco  ·  región us-east-1 (los datos no salen de la región)", 16, color="#e7157b", bold=True)
# usuario
o.append('<circle cx="75" cy="300" r="16" fill="#a5d8ff" stroke="#1e1e1e" stroke-width="2"/>'
         '<path d="M45,350 Q45,320 75,320 Q105,320 105,350 Z" fill="#a5d8ff" stroke="#1e1e1e" stroke-width="2"/>')
text(75, 375, "usuario", 16, "middle", bold=True)
# API Gateway + WAF + Cognito
ic("API Gateway", 245, 230, 65); text(278, 318, "API Gateway", 16, "middle", bold=True)
text(278, 338, "puerta pública única", 13, "middle", color="#495057")
ic("WAF", 190, 370, 42); text(211, 430, "WAF", 14, "middle", bold=True); text(211, 447, "filtra ataques", 12, "middle", color="#495057")
ic("Cognito", 305, 370, 42); text(326, 430, "Cognito", 14, "middle", bold=True); text(326, 447, "¿quién es?", 12, "middle", color="#495057")
arrow(110, 300, 238, 262)
# VPC
rect(410, 115, 700, 455, "#f4f0ff", "#8c4fff", rx=4)
ic("VPC", 410, 115, 30)
text(450, 137, "VPC  =  tu red privada dentro de AWS", 17, color="#8c4fff", bold=True)
# subred privada
rect(430, 160, 400, 390, "#e6f2f8", "#147eba", rx=4)
text(445, 185, "subred privada", 16, color="#147eba", bold=True)
text(445, 207, "✕ sin ruta a internet (sin NAT): aunque\n   engañen al agente, no puede sacar datos", 13, color="#c92a2a")
ic("Lambda", 598, 240, 65); text(630, 328, "Lambda / ECS  (el agente)", 16, "middle", bold=True)
text(630, 347, "security group: solo habla con los endpoints", 13, "middle", color="#495057")
arrow(312, 262, 592, 270)
ic("IAM", 445, 385, 45)
text(500, 400, "rol IAM del agente (qué puede hacer):", 14, color="#147eba", bold=True)
text(500, 422, "· bedrock:InvokeModel  solo ese modelo\n· secretsmanager:GetSecretValue  solo su secreto\n· s3:GetObject  solo su bucket\n✕ nada de borrar ni de otros servicios", 13)
# endpoints y servicios
svc = [("Amazon Bedrock", "Amazon Bedrock", "el LLM, no entrena\ncon tus datos"),
       ("Secrets Manager", "Secrets Manager", "API keys, cifradas\ncon KMS"),
       ("S3", "S3", "documentos del RAG,\ncifrados con KMS"),
       ("CloudWatch", "CloudWatch Logs", "logs sin PII,\ncifrados con KMS")]
for i, (ico, name, desc) in enumerate(svc):
    y = 160 + i*100
    ic("Interface Endpoint", 955, y, 45)
    text(978, y+62, "VPC endpoint", 13, "middle", bold=True, color="#8c4fff")
    arrow(665, 272, 948, y+22, "#2b8a3e", "v")
    w = ic(ico, 1200, y, 45)
    arrow(1003, y+22, 1194, y+22, "#2b8a3e", "v")
    text(1258, y+16, name, 15, bold=True); text(1258, y+35, desc, 12, color="#495057")
text(1300, 560, "verde = red interna de AWS (PrivateLink)", 13, "middle", color="#2b8a3e", bold=True)
# CloudTrail
rect(430, 590, 1020, 62, "#fff8e6", "#e7157b", rx=8)
ic("CloudTrail", 445, 597, 48)
text(505, 628, "CloudTrail: registra cada llamada a AWS (quién invocó qué modelo, qué secreto leyó, cuándo)  →  auditoría", 15, color="#a61e4d", bold=True)
# leyenda
text(20, 705, "VPC = red privada propia  ·  subred privada = sin internet  ·  VPC endpoint = puerta privada a un servicio AWS  ·  rol IAM = permisos mínimos  ·  KMS = cifrado con llaves del banco", 14, color="#495057", italic=True)
text(20, 730, "Por qué importa en banca: ningún dato del cliente viaja por internet, el agente no puede filtrar datos afuera, y todo queda registrado.", 14, color="#495057", italic=True)

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1500" height="750" font-family="Helvetica, Arial, sans-serif">
<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#1e1e1e"/></marker>
<marker id="v" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#2b8a3e"/></marker></defs>
<rect width="1500" height="750" fill="#fff"/>{"".join(o)}</svg>'''
(OUT / "infra-privada.svg").write_text(svg)
subprocess.run(["google-chrome", "--headless", "--disable-gpu", f"--screenshot={OUT / 'infra-privada.png'}",
                "--window-size=1500,750", f"file://{OUT / 'infra-privada.svg'}"], capture_output=True)
