
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import Flowable
from reportlab.pdfgen import canvas as pdfcanvas
import os

# ── Colors ──────────────────────────────────────────────────────────────────
INK        = colors.HexColor("#1A1A18")
MUTED      = colors.HexColor("#555550")
HINT       = colors.HexColor("#888780")
SURFACE    = colors.HexColor("#F8F7F3")
SURFACE2   = colors.HexColor("#EFEFEA")
BORDER     = colors.HexColor("#DDDDD8")

RED        = colors.HexColor("#E24B4A")
RED_LIGHT  = colors.HexColor("#FCEBEB")
RED_DARK   = colors.HexColor("#791F1F")

BLUE       = colors.HexColor("#185FA5")
BLUE_LIGHT = colors.HexColor("#E6F1FB")
BLUE_DARK  = colors.HexColor("#0C447C")

GREEN      = colors.HexColor("#0F6E56")
GREEN_LIGHT= colors.HexColor("#E1F5EE")
GREEN_DARK = colors.HexColor("#085041")

AMBER      = colors.HexColor("#BA7517")
AMBER_LIGHT= colors.HexColor("#FAEEDA")
AMBER_DARK = colors.HexColor("#633806")

PURPLE     = colors.HexColor("#534AB7")
PURPLE_LIGHT=colors.HexColor("#EEEDFE")
PURPLE_DARK= colors.HexColor("#3C3489")

PINK       = colors.HexColor("#993556")
PINK_LIGHT = colors.HexColor("#FBEAF0")
PINK_DARK  = colors.HexColor("#72243E")

WHITE      = colors.white
BLACK      = colors.black
CODE_BG    = colors.HexColor("#2C2C2A")
CODE_FG    = colors.HexColor("#D3D1C7")
CODE_TAG   = colors.HexColor("#EF9F27")
CODE_CMD   = colors.HexColor("#5DCAA5")
CODE_CMT   = colors.HexColor("#888780")
CODE_HL    = colors.HexColor("#AFA9EC")

W, H = A4

# ── Custom Flowables ─────────────────────────────────────────────────────────

class ColorRect(Flowable):
    def __init__(self, width, height, fill, radius=4):
        self.width = width
        self.height = height
        self.fill = fill
        self.radius = radius
    def draw(self):
        self.canv.setFillColor(self.fill)
        self.canv.roundRect(0, 0, self.width, self.height, self.radius, fill=1, stroke=0)

class TagBadge(Flowable):
    def __init__(self, text, bg, fg, width=None):
        self.text = text
        self.bg = bg
        self.fg = fg
        self._width = width or (len(text)*5.5 + 16)
        self.height = 16
        self.width = self._width
    def draw(self):
        c = self.canv
        c.setFillColor(self.bg)
        c.roundRect(0, 0, self._width, self.height, 4, fill=1, stroke=0)
        c.setFillColor(self.fg)
        c.setFont("Helvetica-Bold", 7)
        c.drawCentredString(self._width/2, 4.5, self.text.upper())

class SectionDivider(Flowable):
    def __init__(self, color=RED, width=None):
        self.color = color
        self._w = width
        self.height = 3
        self.width = width or 500
    def draw(self):
        self.canv.setFillColor(self.color)
        self.canv.rect(0, 0, self.width or 500, 3, fill=1, stroke=0)

class LeftBorderBox(Flowable):
    def __init__(self, text, border_color, bg_color, text_color=None, label=None, label_color=None, available_width=500):
        self.text = text
        self.border_color = border_color
        self.bg_color = bg_color
        self.text_color = text_color or MUTED
        self.label = label
        self.label_color = label_color or border_color
        self.available_width = available_width
        self.height = None
        self.width = available_width

    def wrap(self, availW, availH):
        self.width = availW
        # estimate height
        chars_per_line = (availW - 30) / 5.5
        lines = max(1, len(self.text) / chars_per_line)
        label_h = 14 if self.label else 0
        self.height = label_h + lines * 13 + 16
        return availW, self.height

    def draw(self):
        c = self.canv
        h = self.height
        w = self.width
        # background
        c.setFillColor(self.bg_color)
        c.roundRect(0, 0, w, h, 4, fill=1, stroke=0)
        # left border
        c.setFillColor(self.border_color)
        c.rect(0, 0, 3, h, fill=1, stroke=0)
        # label
        y = h - 10
        if self.label:
            c.setFillColor(self.label_color)
            c.setFont("Helvetica-Bold", 7)
            c.drawString(12, y, self.label.upper())
            y -= 14
        # text
        c.setFillColor(self.text_color)
        c.setFont("Helvetica", 8.5)
        # simple word wrap
        words = self.text.split()
        line = ""
        max_w = w - 24
        for word in words:
            test = (line + " " + word).strip()
            if c.stringWidth(test, "Helvetica", 8.5) < max_w:
                line = test
            else:
                c.drawString(12, y, line)
                y -= 13
                line = word
        if line:
            c.drawString(12, y, line)


class CodeBlock(Flowable):
    def __init__(self, lines, available_width=500):
        self.lines = lines
        self.available_width = available_width
        self.height = len(lines) * 13 + 20
        self.width = available_width

    def wrap(self, availW, availH):
        self.width = availW
        self.height = len(self.lines) * 13 + 20
        return availW, self.height

    def draw(self):
        c = self.canv
        h = self.height
        w = self.width
        c.setFillColor(CODE_BG)
        c.roundRect(0, 0, w, h, 5, fill=1, stroke=0)
        y = h - 16
        for text, color in self.lines:
            c.setFillColor(color)
            c.setFont("Courier", 7.5)
            max_chars = int((w - 20) / 4.6)
            display = text[:max_chars] if len(text) > max_chars else text
            left_pad = 14 if color == CODE_TAG else 10
            c.drawString(left_pad, y, display)
            y -= 13

# ── Page templates ────────────────────────────────────────────────────────────

class CoverPage:
    def __call__(self, canvas, doc):
        canvas.saveState()
        # full bleed background
        canvas.setFillColor(INK)
        canvas.rect(0, 0, W, H, fill=1, stroke=0)
        # red accent top stripe
        canvas.setFillColor(RED)
        canvas.rect(0, H-6, W, 6, fill=1, stroke=0)
        # top label
        canvas.setFillColor(RED)
        canvas.roundRect(40*mm, H-40*mm, 60*mm, 8*mm, 3, fill=1, stroke=0)
        canvas.setFillColor(WHITE)
        canvas.setFont("Helvetica-Bold", 8)
        canvas.drawCentredString(70*mm, H-36.5*mm, "PACK DE PROMPTS — CRIADORES DE CONTEÚDO")
        # big title
        canvas.setFillColor(WHITE)
        canvas.setFont("Helvetica-Bold", 38)
        canvas.drawString(40*mm, H-78*mm, "Prompt")
        canvas.setFillColor(RED)
        canvas.setFont("Helvetica-Bold", 38)
        canvas.drawString(40*mm, H-96*mm, "Engine")
        canvas.setFillColor(WHITE)
        canvas.setFont("Helvetica-Bold", 38)
        canvas.drawString(40*mm, H-114*mm, "Para Criadores")
        # subtitle
        canvas.setFillColor(HINT)
        canvas.setFont("Helvetica", 11)
        canvas.drawString(40*mm, H-128*mm, "Guia técnico de engenharia de prompt para")
        canvas.drawString(40*mm, H-140*mm, "escalar Instagram e TikTok com copy de")
        canvas.drawString(40*mm, H-152*mm, "alta conversão — sem tempo perdido.")
        # divider
        canvas.setFillColor(colors.HexColor("#333330"))
        canvas.rect(40*mm, H-162*mm, W-80*mm, 0.5, fill=1, stroke=0)
        # stats row
        stats = [("5", "Prompts Mestres"), ("20", "Ganchos de Retenção"), ("8", "VSLs para Stories"), ("10", "Legendas Magnéticas")]
        x = 40*mm
        for num, lbl in stats:
            canvas.setFillColor(WHITE)
            canvas.setFont("Helvetica-Bold", 20)
            canvas.drawString(x, H-177*mm, num)
            canvas.setFillColor(HINT)
            canvas.setFont("Helvetica", 8)
            canvas.drawString(x, H-186*mm, lbl)
            x += 37*mm
        # bottom label
        canvas.setFillColor(colors.HexColor("#3A3A38"))
        canvas.roundRect(40*mm, 18*mm, 52*mm, 8*mm, 3, fill=1, stroke=0)
        canvas.setFillColor(HINT)
        canvas.setFont("Helvetica", 8)
        canvas.drawCentredString(66*mm, 21*mm, "Método ROLES • Gatilhos Mentais")
        # version
        canvas.setFillColor(HINT)
        canvas.setFont("Helvetica", 8)
        canvas.drawRightString(W-40*mm, 21*mm, "v1.0 — 2025")
        canvas.restoreState()


class ContentPage:
    def __call__(self, canvas, doc):
        canvas.saveState()
        # top bar
        canvas.setFillColor(SURFACE2)
        canvas.rect(0, H-10*mm, W, 10*mm, fill=1, stroke=0)
        canvas.setFillColor(RED)
        canvas.rect(0, H-1, W, 1, fill=1, stroke=0)
        # header text
        canvas.setFillColor(HINT)
        canvas.setFont("Helvetica", 7.5)
        canvas.drawString(15*mm, H-6.5*mm, "PROMPT ENGINE PARA CRIADORES")
        canvas.drawRightString(W-15*mm, H-6.5*mm, "promptengine.digital")
        # bottom bar
        canvas.setFillColor(SURFACE2)
        canvas.rect(0, 0, W, 10*mm, fill=1, stroke=0)
        canvas.setFillColor(BORDER)
        canvas.rect(0, 10*mm, W, 0.5, fill=1, stroke=0)
        # page number
        canvas.setFillColor(MUTED)
        canvas.setFont("Helvetica", 8)
        canvas.drawCentredString(W/2, 3.5*mm, str(doc.page))
        canvas.restoreState()


def make_styles():
    s = {}

    s['h1'] = ParagraphStyle('h1',
        fontName='Helvetica-Bold', fontSize=22, textColor=INK,
        spaceAfter=4, spaceBefore=14, leading=26)

    s['h1_accent'] = ParagraphStyle('h1_accent',
        fontName='Helvetica-Bold', fontSize=22, textColor=RED,
        spaceAfter=4, spaceBefore=2, leading=26)

    s['h2'] = ParagraphStyle('h2',
        fontName='Helvetica-Bold', fontSize=14, textColor=INK,
        spaceAfter=4, spaceBefore=12, leading=18)

    s['h3'] = ParagraphStyle('h3',
        fontName='Helvetica-Bold', fontSize=11, textColor=INK,
        spaceAfter=3, spaceBefore=8, leading=15)

    s['label'] = ParagraphStyle('label',
        fontName='Helvetica-Bold', fontSize=7, textColor=HINT,
        spaceAfter=6, spaceBefore=0, leading=10, letterSpacing=1.2)

    s['body'] = ParagraphStyle('body',
        fontName='Helvetica', fontSize=9, textColor=MUTED,
        spaceAfter=6, spaceBefore=0, leading=14, alignment=TA_JUSTIFY)

    s['body_left'] = ParagraphStyle('body_left',
        fontName='Helvetica', fontSize=9, textColor=MUTED,
        spaceAfter=5, spaceBefore=0, leading=14)

    s['small'] = ParagraphStyle('small',
        fontName='Helvetica', fontSize=8, textColor=HINT,
        spaceAfter=4, leading=12)

    s['mono'] = ParagraphStyle('mono',
        fontName='Courier', fontSize=8, textColor=CODE_FG,
        spaceAfter=3, leading=12)

    s['section_tag'] = ParagraphStyle('section_tag',
        fontName='Helvetica-Bold', fontSize=8, textColor=RED,
        spaceAfter=2, leading=11, letterSpacing=1.0)

    s['toc_item'] = ParagraphStyle('toc_item',
        fontName='Helvetica', fontSize=10, textColor=MUTED,
        spaceAfter=5, leading=14, leftIndent=0)

    s['toc_num'] = ParagraphStyle('toc_num',
        fontName='Helvetica-Bold', fontSize=10, textColor=INK,
        spaceAfter=5, leading=14)

    s['bullet'] = ParagraphStyle('bullet',
        fontName='Helvetica', fontSize=8.5, textColor=MUTED,
        spaceAfter=3, leading=13, leftIndent=12, firstLineIndent=-12)

    s['roles_label'] = ParagraphStyle('roles_label',
        fontName='Helvetica-Bold', fontSize=7, textColor=HINT,
        spaceAfter=1, leading=10, letterSpacing=0.8)

    s['roles_val'] = ParagraphStyle('roles_val',
        fontName='Helvetica', fontSize=8, textColor=MUTED,
        spaceAfter=0, leading=11)

    return s


def roles_table(items, color):
    rows = []
    for letter, val in items:
        rows.append([
            Paragraph(f'<b>&nbsp;&nbsp;{letter}</b>', ParagraphStyle('r', fontName='Helvetica-Bold', fontSize=8, textColor=WHITE)),
            Paragraph(val, ParagraphStyle('rv', fontName='Helvetica', fontSize=8, textColor=MUTED, leading=11))
        ])
    t = Table(rows, colWidths=[18*mm, None])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), color),
        ('BACKGROUND', (1,0), (1,-1), SURFACE2),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0, 0), (0, -1), 15),
        ('LEFTPADDING', (1,0), (1,-1), 10),
        ('ROWBACKGROUNDS', (1,0), (1,-1), [SURFACE2, WHITE]),
        ('LINEBELOW', (0,0), (-1,-2), 0.5, BORDER),
        ('ROUNDEDCORNERS', [4,4,4,4]),
    ]))
    return t


def prompt_box(lines):
    color_map = {
        'tag': CODE_TAG, 'cmd': CODE_CMD, 'cmt': CODE_CMT,
        'hl': CODE_HL, 'normal': CODE_FG
    }
    code_lines = [(text, color_map.get(kind, CODE_FG)) for text, kind in lines]
    return CodeBlock(code_lines)


def section_header(title, subtitle, color, tag_text, s):
    items = []
    items.append(Spacer(1, 6*mm))
    items.append(Paragraph(tag_text.upper(), ParagraphStyle('st',
        fontName='Helvetica-Bold', fontSize=7.5, textColor=color,
        letterSpacing=1.2, leading=10, spaceAfter=4)))
    items.append(Paragraph(title, ParagraphStyle('sh',
        fontName='Helvetica-Bold', fontSize=20, textColor=INK,
        spaceAfter=2, leading=24)))
    items.append(Paragraph(subtitle, s['body']))
    items.append(SectionDivider(color=color))
    items.append(Spacer(1, 5*mm))
    return items


def prompt_card(number, badge_text, title, why_text, roles, code_lines, badge_color, badge_bg, s, available_width=165*mm):
    items = []

    # Card header row
    header_data = [[
        Paragraph(f'<b>{number}</b>', ParagraphStyle('cn',
            fontName='Helvetica-Bold', fontSize=8, textColor=WHITE)),
        Paragraph(f'<b>{badge_text.upper()}</b>', ParagraphStyle('cb',
            fontName='Helvetica-Bold', fontSize=7, textColor=badge_color, letterSpacing=0.8)),
        Paragraph(f'<b>{title}</b>', ParagraphStyle('ct',
            fontName='Helvetica-Bold', fontSize=9.5, textColor=INK, leading=13))
    ]]
    header_table = Table(header_data, colWidths=[10*mm, 28*mm, available_width-38*mm])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,0), badge_color),
        ('BACKGROUND', (1,0), (1,0), badge_bg),
        ('BACKGROUND', (2,0), (2,0), SURFACE2),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        
        # Mude o 0 para 3 ou 4 aqui:
        ('LEFTPADDING', (0,0), (0,0), 3), 
        
        ('LEFTPADDING', (1,0), (1,0), 8),
        ('LEFTPADDING', (2,0), (2,0), 10),
        ('ROUNDEDCORNERS', [4,4,0,0]),
    ]))
    items.append(header_table)

    # Why it works box
    items.append(LeftBorderBox(
        why_text,
        border_color=badge_color,
        bg_color=badge_bg,
        text_color=MUTED,
        label="Por que funciona",
        label_color=badge_color,
        available_width=available_width
    ))

    # ROLES table
    items.append(Spacer(1, 2))
    items.append(Paragraph("MÉTODO ROLES", ParagraphStyle('rl',
        fontName='Helvetica-Bold', fontSize=6.5, textColor=HINT,
        letterSpacing=1, leading=9, spaceAfter=3)))
    items.append(roles_table(roles, badge_color))
    items.append(Spacer(1, 4))

    # Code block
    items.append(Paragraph("PROMPT COMPLETO", ParagraphStyle('pl',
        fontName='Helvetica-Bold', fontSize=6.5, textColor=HINT,
        letterSpacing=1, leading=9, spaceAfter=3)))
    items.append(prompt_box(code_lines))
    items.append(Spacer(1, 8*mm))

    return items


# ── Content Data ─────────────────────────────────────────────────────────────

PROMPTS_MESTRES = [
    {
        "num": "PM 01", "badge": "Fundacional", "color": RED, "bg": RED_LIGHT,
        "title": "Briefing de Marca — O Prompt Fundacional",
        "why": "Sem contexto de marca, a IA usa tom e vocabulário padrão. Este prompt cria uma 'memória de sessão' que alinha voz, público e posicionamento antes de qualquer produção de conteúdo.",
        "roles": [
            ("R", "Especialista em branding e copywriting"),
            ("O", "Memorizar identidade de marca"),
            ("L", "Não gerar conteúdo ainda"),
            ("E", "Tom, dores e diferenciais"),
            ("S", "Confirmação explícita ao final"),
        ],
        "code": [
            ("// Rode este prompt PRIMEIRO em toda sessão de trabalho", "cmt"),
            ("", "normal"),
            ("Atue como especialista em branding e copywriting para redes sociais.", "hl"),
            ("", "normal"),
            ("// Identidade", "cmt"),
            ("Meu nome/marca: [Nome ou @perfil]", "tag"),
            ("Meu nicho: [Ex: finanças pessoais para CLTs]", "tag"),
            ("Meu público-alvo: [Idade, gênero, situação, dor principal]", "tag"),
            ("", "normal"),
            ("// Tom de Voz", "cmt"),
            ("Meu tom é: [Ex: direto e provocador / acolhedor e didático]", "tag"),
            ("Palavras que uso muito: [Liste 3 a 5 expressões]", "tag"),
            ("O que NUNCA digo: [Palavras que quebram minha voz]", "tag"),
            ("", "normal"),
            ("// Posicionamento", "cmt"),
            ("Meu diferencial é: [O que me separa dos outros do nicho]", "tag"),
            ("Minha maior prova social: [Resultado real, número, depoimento]", "tag"),
            ("Meu produto/serviço principal: [O que você vende]", "tag"),
            ("", "normal"),
            ("Guarde essas informações. Não gere nenhum conteúdo agora.", "cmd"),
            ("Responda apenas: 'Briefing registrado. Pode solicitar os conteudos.'", "cmd"),
        ]
    },
    {
        "num": "PM 02", "badge": "Dores", "color": BLUE, "bg": BLUE_LIGHT,
        "title": "Mapeador de Dores — Munição para Ganchos",
        "why": "Ganchos que convertem falam sobre dores específicas. Este prompt usa a técnica de escavação de dor em 3 camadas — superficial, emocional e identitária — para gerar material que para o scroll.",
        "roles": [
            ("R", "Psicólogo comportamental e copywriter"),
            ("O", "Mapear dores em 3 níveis"),
            ("L", "Apenas dores, sem soluções"),
            ("E", "Linguagem do público, não técnica"),
            ("S", "Tabela estruturada de saída"),
        ],
        "code": [
            ("// Rode após o PM 01 — briefing deve estar ativo", "cmt"),
            ("", "normal"),
            ("Atue como psicólogo comportamental especializado em marketing.", "hl"),
            ("", "normal"),
            ("Com base no briefing, mapeie as dores do meu público em 3 camadas.", "normal"),
            ("Use a linguagem exata que eles usariam, nao a linguagem tecnica.", "normal"),
            ("", "normal"),
            ("CAMADA 1 — Dor Superficial (o que reclamam abertamente)", "tag"),
            ("Liste 5 frases na voz do público. Ex: 'Nao tenho tempo para...'", "normal"),
            ("", "normal"),
            ("CAMADA 2 — Dor Emocional (o que sentem mas raramente dizem)", "tag"),
            ("Liste 5 frases. Ex: 'Tenho vergonha quando...'", "normal"),
            ("", "normal"),
            ("CAMADA 3 — Dor de Identidade (quem eles nao querem ser)", "tag"),
            ("Liste 5 frases. Ex: 'Tenho medo de virar aquela pessoa que...'", "normal"),
            ("", "normal"),
            ("Ao final, destaque as 3 dores com maior potencial de gancho.", "cmd"),
        ]
    },
    {
        "num": "PM 03", "badge": "Ângulos", "color": RED, "bg": RED_LIGHT,
        "title": "Gerador de Ângulos — Anti-Conteúdo Genérico",
        "why": "O maior erro de criadores é falar do mesmo tema com o mesmo ângulo. Este prompt usa a matriz de 'ângulos de reframe' para transformar um tema saturado em perspectiva única.",
        "roles": [
            ("R", "Estrategista de conteúdo viral"),
            ("O", "10 ângulos únicos por tema"),
            ("L", "Sem ângulos já saturados"),
            ("E", "Contra-narrativa e provocação"),
            ("S", "Classificar por potencial viral"),
        ],
        "code": [
            ("Atue como estrategista de conteúdo especializado em viralização.", "hl"),
            ("", "normal"),
            ("Tema que quero abordar: [Ex: 'como poupar dinheiro']", "tag"),
            ("O angulo obvio/saturado seria: [Ex: '10 dicas para economizar']", "tag"),
            ("", "normal"),
            ("Gere 10 angulos nao-obvios usando estas lentes:", "normal"),
            ("-> Contra-narrativa: o oposto do que todos dizem", "cmd"),
            ("-> Confissao: algo que poucos admitem mas todos pensam", "cmd"),
            ("-> Erro comum: o que as pessoas fazem errado sem saber", "cmd"),
            ("-> Comparacao inusitada: analogia que ninguem usou ainda", "cmd"),
            ("-> Dado chocante: estatistica que contradiz o senso comum", "cmd"),
            ("-> Polemico mas verdadeiro: opiniao que gera debate saudavel", "cmd"),
            ("-> Resultado rapido: promessa em 24h/7 dias", "cmd"),
            ("", "normal"),
            ("Para cada angulo, escreva o titulo como o 1o frame do Reel.", "normal"),
            ("Ao final, classifique os 3 com maior potencial de salvar/compartilhar.", "cmd"),
        ]
    },
    {
        "num": "PM 04", "badge": "Tom", "color": AMBER, "bg": AMBER_LIGHT,
        "title": "Calibrador de Tom — Treine a IA na sua Voz",
        "why": "A IA tem um 'tom padrão' que soa como qualquer um. Este prompt usa exemplos positivos e negativos para calibrar a voz antes de gerar conteúdo em escala.",
        "roles": [
            ("R", "Editor de conteúdo pessoal"),
            ("O", "Clonar o tom de voz da marca"),
            ("L", "Não alterar informação, só tom"),
            ("E", "Exemplos positivos e negativos"),
            ("S", "Teste com 3 variações"),
        ],
        "code": [
            ("Atue como editor de conteudo que vai aprender meu estilo.", "hl"),
            ("", "normal"),
            ("Analise: ritmo das frases, palavras recorrentes, nível de", "normal"),
            ("formalidade, uso de pontuacao, jeito de abrir e fechar ideias.", "normal"),
            ("", "normal"),
            ("EXEMPLO POSITIVO — Assim escrevo:", "tag"),
            ("[Cole aqui 3 a 5 legendas suas que funcionaram bem]", "tag"),
            ("", "normal"),
            ("EXEMPLO NEGATIVO — Assim NAO escrevo:", "tag"),
            ("[Cole exemplos de textos genericos que voce odeia]", "tag"),
            ("", "normal"),
            ("Apos analisar, responda:", "cmd"),
            ("1. Descreva meu estilo em 5 caracteristicas objetivas", "normal"),
            ("2. Liste 10 palavras/expressoes do meu vocabulario", "normal"),
            ("3. Liste 10 palavras que nunca aparecem no meu conteudo", "normal"),
            ("", "normal"),
            ("Depois, reescreva este texto usando meu estilo:", "cmd"),
            ("[Cole qualquer paragrafo generico aqui para teste]", "tag"),
            ("Gere 3 versoes: direta, emocional, provocadora.", "cmd"),
        ]
    },
    {
        "num": "PM 05", "badge": "Editorial", "color": BLUE, "bg": BLUE_LIGHT,
        "title": "Calendário Editorial de 30 Dias — Estratégia Completa",
        "why": "Consistência bate talento no algoritmo. Este prompt usa o framework de 'pilares de conteúdo com progressão de consciência' para montar um mês estratégico, não aleatório.",
        "roles": [
            ("R", "Estrategista de marketing de conteúdo"),
            ("O", "30 dias de pauta estratégica"),
            ("L", "Máx 2 posts de venda direta/semana"),
            ("E", "Progressão de consciência do público"),
            ("S", "Formato, pilar e objetivo por post"),
        ],
        "code": [
            ("Atue como estrategista de marketing de conteudo.", "hl"),
            ("", "normal"),
            ("Monte um calendario editorial de 30 dias com 5 pilares:", "normal"),
            ("", "normal"),
            ("40% — Educacao (resolve uma dor, ensina algo util)", "cmd"),
            ("25% — Prova Social (resultados, depoimentos, bastidores)", "cmd"),
            ("20% — Conexao (historia pessoal, valores, opiniao)", "cmd"),
            ("10% — Entretenimento (trends, humor no nicho)", "cmd"),
            ("5%  — Oferta Direta (CTA para produto/servico)", "cmd"),
            ("", "normal"),
            ("Plataforma principal: [Instagram / TikTok / Ambos]", "tag"),
            ("Frequencia de posts: [X por semana]", "tag"),
            ("Formatos disponiveis: [Reel / Carrossel / Story / Feed]", "tag"),
            ("Objetivo do mes: [crescer seguidores / lancar produto]", "tag"),
            ("", "normal"),
            ("Para cada post: dia, formato, pilar, angulo, gancho e nivel", "normal"),
            ("de consciencia do publico: frio / morno / quente.", "normal"),
            ("Organize em tabela semanal. Destaque os 5 com maior potencial.", "cmd"),
        ]
    },
]

GANCHOS = [
    {
        "num":"G01","badge":"Curiosidade","color":PURPLE,"bg":PURPLE_LIGHT,
        "title":"Loop Aberto — A pergunta que não pode ser ignorada",
        "why":"O cérebro odeia loops abertos. Uma pergunta sem resposta cria tensão cognitiva — o espectador precisa assistir até o final para 'fechar' o loop. Técnica derivada do Efeito Zeigarnik.",
        "roles":[("R","Roteirista de conteúdo viral"),("O","Abrir loop irresistível"),("L","Máx 10 palavras no gancho"),("E","Pergunta que implica revelação"),("S","5 variações por nicho")],
        "code":[("// Rode após PM 01 (briefing ativo)","cmt"),("","normal"),("Atue como roteirista dos primeiros 3 segundos de vídeos virais.","hl"),("","normal"),("Crie 5 ganchos de Loop Aberto para o início do Reel/TikTok.","normal"),("","normal"),("Regra: pergunta ou afirmacao incompleta que so faz sentido","normal"),("      se a pessoa assistir ate o final. Max 10 palavras.","normal"),("Proibido: 'Voce sabia que', 'Incrivel', 'Surpreendente'.","cmt"),("","normal"),("Tema do vídeo: [Descreva o conteudo em 1 frase]","tag"),("Nicho: [Seu nicho]","tag"),("Público: [Quem vai ver]","tag"),("","normal"),("Para cada gancho:","cmd"),("-> O texto do gancho em destaque","normal"),("-> Por que esse loop vai segurar esse público","normal"),("-> Sugestao de texto on-screen (legenda sobreposta)","normal")]
    },
    {
        "num":"G02","badge":"Contra-narrativa","color":AMBER,"bg":AMBER_LIGHT,
        "title":"O Mito Derrubado — Contradiz o que todos acreditam",
        "why":"Contradizer uma crença estabelecida ativa o reflexo de defesa — o espectador fica para provar que você está errado, e no processo absorve seu conteúdo. Gatilho de dissonância cognitiva.",
        "roles":[("R","Provocador estratégico de nicho"),("O","Contradizer crença dominante"),("L","Verdadeiro, não sensacionalismo"),("E","Especificidade do nicho"),("S","Afirmação + dado ou prova")],
        "code":[("Atue como criador que desafia o consenso do nicho.","hl"),("","normal"),("Crie 5 ganchos Contra-Narrativa que contradizem uma crença","normal"),("comum — mas que sao verdadeiros e defensaveis.","normal"),("","normal"),("Estrutura: '[Coisa que todos fazem] esta errado. [Revelacao]'","cmd"),("","normal"),("Crença dominante que quero contradizer:","normal"),("[Ex: 'Postar todo dia é obrigatorio para crescer']","tag"),("","normal"),("O que eu acredito de diferente (perspectiva real):","normal"),("[Sua visao contraria com base em experiencia ou dado]","tag"),("","normal"),("Para cada gancho:","cmd"),("-> Texto (max 12 palavras)","normal"),("-> Como desenvolver nos proximos 15 segundos","normal"),("-> Nivel de polemica: baixo / medio / alto","tag")]
    },
    {
        "num":"G03","badge":"Prova Social","color":GREEN,"bg":GREEN_LIGHT,
        "title":"O Resultado Específico — Número real, não promessa vaga",
        "why":"Números específicos são 3x mais críveis que afirmações genéricas. 'Perdi 8kg' retém mais do que 'Emagreci muito'. O cérebro trata especificidade como evidência de verdade.",
        "roles":[("R","Copywriter de prova social"),("O","Gancho com número específico"),("L","Apenas resultados reais seus"),("E","Especificidade e tempo"),("S","Antes/depois em 1 frase")],
        "code":[("Atue como copywriter especializado em prova social.","hl"),("","normal"),("Crie 5 ganchos de Resultado Especifico baseados em dados reais.","normal"),("","normal"),("Meu resultado real: [Ex: cresci 4.200 seguidores em 23 dias]","tag"),("O metodo/causa: [Ex: 3 Reels/semana com gancho testado]","tag"),("Periodo: [Ex: 23 dias / 1 mes / 6 semanas]","tag"),("Ponto de partida: [Ex: 800 seguidores, zero engajamento]","tag"),("","normal"),("Estruturas para variar:","cmd"),("-> '[Numero] em [tempo]. Sem [objecao comum].'","normal"),("-> 'De [antes] para [depois] em [tempo]. O que fiz:'","normal"),("-> 'Esse resultado levou [tempo]. Replica em [menos].'","normal"),("","normal"),("Para cada gancho:","cmd"),("-> Texto final (max 15 palavras)","normal"),("-> Por que esse angulo vai parar o scroll","normal"),("-> CTA sugerido para o final do vídeo","normal")]
    },
    {
        "num":"G04","badge":"Escassez","color":RED,"bg":RED_LIGHT,
        "title":"A Janela Fechando — Urgência sem mentira",
        "why":"FOMO ativa o sistema límbico antes do racional. Ganchos de escassez temporal criam urgência de assistir agora, não depois. Funciona mesmo sem produto para vender.",
        "roles":[("R","Especialista em urgência editorial"),("O","Criar FOMO legítimo"),("L","Sem fake urgency"),("E","Janela real de oportunidade"),("S","Consequência de não agir")],
        "code":[("Atue como roteirista de urgencia editorial etica.","hl"),("","normal"),("Crie 5 ganchos de Escassez Temporal. Proibido inventar urgencia falsa.","cmt"),("","normal"),("O tema/oportunidade real do video:","normal"),("[Ex: mudanca no algoritmo do Instagram em 2025]","tag"),("","normal"),("Por que a janela esta se fechando (razao real):","normal"),("[Ex: a atualizacao ja comecou a ser aplicada]","tag"),("","normal"),("Consequencia concreta de nao agir:","normal"),("[Ex: perder alcance organico nos proximos 30 dias]","tag"),("","normal"),("Estruturas:","cmd"),("-> 'Se voce ainda nao [acao], tem ate [prazo].'","normal"),("-> '[Mudanca] ja comecou. Quem nao souber vai [consequencia].'","normal"),("-> 'Essa janela fecha em [tempo]. Aproveite enquanto funciona.'","normal")]
    },
    {
        "num":"G05","badge":"Autoridade","color":BLUE,"bg":BLUE_LIGHT,
        "title":"A Credencial Implícita — Autoridade sem soar arrogante",
        "why":"Declarar autoridade diretamente gera ceticismo. Mostrar autoridade através de contexto ativa confiança automática — técnica da 'autoridade demonstrada' do copywriting direto.",
        "roles":[("R","Copywriter de posicionamento"),("O","Autoridade através de contexto"),("L","Nunca autodeclarado diretamente"),("E","Volume, tempo ou escala"),("S","Credencial em 1 frase de contexto")],
        "code":[("Atue como copywriter de posicionamento de autoridade.","hl"),("","normal"),("Crie 5 ganchos de Autoridade Implicita — minha credencial","normal"),("deve aparecer como contexto, nunca como autodeclaracao direta.","normal"),("","normal"),("Minha experiencia real:","normal"),("[Ex: 5 anos no nicho, 300 alunos, analisei 150 perfis]","tag"),("","normal"),("Resultado mais relevante que alcancei ou ajudei alguem:","normal"),("[Ex: 3 criadores a 100k em menos de 6 meses]","tag"),("","normal"),("Tema do video: [O que voce vai ensinar]","tag"),("","normal"),("Estruturas-modelo:","cmd"),("-> 'Depois de [volume de experiencia], descobri que [insight].'","normal"),("-> '[X pessoas] me perguntam sobre [tema]. A resposta e:'","normal"),("-> 'Analisei [numero] de [objeto]. O padrao que repete e:'","normal"),("","normal"),("Para cada gancho: texto + tom + nivel de autoridade (1-5).","cmd")]
    },
    {
        "num":"G06","badge":"Curiosidade","color":PURPLE,"bg":PURPLE_LIGHT,
        "title":"O Segredo Guardado — Informação que 'poucos sabem'",
        "why":"A percepção de acesso exclusivo ativa o desejo de pertencimento e o medo de exclusão. 'O que poucos sabem' não é apenas curiosidade — é gatilho de identidade.",
        "roles":[("R","Curador de informação exclusiva"),("O","Percepção de acesso especial"),("L","Informação deve ser real"),("E","Exclusividade sem elitismo"),("S","Quem 'não sabe' definido")],
        "code":[("Atue como roteirista que transforma conhecimento em revelacao.","hl"),("","normal"),("Crie 5 ganchos de Segredo Guardado. O segredo precisa ser real e util.","cmd"),("","normal"),("A informacao real que vou revelar:","normal"),("[Descreva o insight ou tecnica que vai ensinar]","tag"),("","normal"),("Por que a maioria ainda nao sabe isso:","normal"),("[Ex: contra-intuitivo / recente / ensinado so em cursos caros]","tag"),("","normal"),("Estruturas:","cmd"),("-> 'O que [grupo] nao quer que voce saiba sobre [tema]:'","normal"),("-> 'Ninguem no [nicho] fala isso. Mas e o que realmente [resultado].'","normal"),("-> 'Descobri por acidente depois de [contexto]. Mudou tudo.'","normal"),("","normal"),("Para cada gancho: texto + 'promessa implicita' + como honrar em 30s.","cmd")]
    },
    {
        "num":"G07","badge":"Contra-narrativa","color":AMBER,"bg":AMBER_LIGHT,
        "title":"A Confissão Calculada — Vulnerabilidade que constrói confiança",
        "why":"Admitir um erro real desativa a resistência do público. A confissão cria identificação e eleva a credibilidade da solução — quem errou e aprendeu é mais confiável.",
        "roles":[("R","Narrador de jornada pessoal"),("O","Identificação via vulnerabilidade"),("L","Erro real, não performático"),("E","Antes/depois emocional"),("S","Erro → aprendizado → convite")],
        "code":[("Atue como roteirista de storytelling de vulnerabilidade.","hl"),("","normal"),("Crie 5 ganchos de Confissao Calculada baseados num erro real","normal"),("que cometi — que meu publico provavelmente tambem comete.","normal"),("","normal"),("O erro real que quero confessar:","normal"),("[Ex: fiquei 2 anos postando todo dia sem resultado]","tag"),("","normal"),("O que aprendi (a virada):","normal"),("[Ex: frequencia sem estrategia e ruido, nao crescimento]","tag"),("","normal"),("Como meu publico se identifica com esse erro:","normal"),("[Ex: tambem postam sem estrategia achando que volume resolve]","tag"),("","normal"),("Estruturas:","cmd"),("-> 'Por [tempo], fiz [erro]. Ate que [virada].'","normal"),("-> 'Esse foi meu maior erro em [nicho]. E provavelmente e o seu.'","normal")]
    },
    {
        "num":"G08","badge":"Escassez","color":RED,"bg":RED_LIGHT,
        "title":"O Custo da Ignorância — O que você perde por não saber",
        "why":"A aversão à perda é 2x mais poderosa que o desejo de ganho (Kahneman). Mostrar o custo de não agir cria urgência mais forte do que qualquer promessa de benefício.",
        "roles":[("R","Copywriter de aversão à perda"),("O","Mostrar custo da inação"),("L","Custo real, não catastrofismo"),("E","Perda concreta e específica"),("S","Quantificar a perda se possível")],
        "code":[("Atue como copywriter especializado em aversao a perda.","hl"),("","normal"),("Crie 5 ganchos de Custo da Ignorancia — foco no que o publico","normal"),("perde por nao conhecer o que vou ensinar.","normal"),("","normal"),("O conhecimento que vou ensinar:","normal"),("[Ex: como usar SEO no TikTok para crescer sem ads]","tag"),("","normal"),("Custo real de nao saber isso:","normal"),("[Ex: R$500/mes em anuncios desnecessarios / 6 meses perdidos]","tag"),("","normal"),("Estruturas:","cmd"),("-> 'Cada dia que voce nao sabe isso, voce esta [perdendo X].'","normal"),("-> 'Fiz as contas: ignorar [tema] me custou [numero/tempo].'","normal"),("-> 'Enquanto voce le isso, [consequencia negativa] acontece.'","normal"),("","normal"),("Para cada gancho: texto + intensidade de urgencia (1-5).","cmd")]
    },
    {
        "num":"G09","badge":"Curiosidade","color":PURPLE,"bg":PURPLE_LIGHT,
        "title":"O Processo Revelado — Bastidor que educa e entretém",
        "why":"Conteúdo de bastidor ativa curiosidade sobre processo — como algo funciona por dentro. Alto índice de salvamentos porque o espectador quer 'guardar para aplicar'.",
        "roles":[("R","Documentarista de processo"),("O","Curiosidade + utilidade"),("L","Processo deve ser replicável"),("E","Detalhe inesperado do processo"),("S","Número de passos visíveis")],
        "code":[("Atue como roteirista de conteudo de processo e bastidor.","hl"),("","normal"),("Crie 5 ganchos de Processo Revelado que abram meu video","normal"),("mostrando o 'como fazer por dentro'.","normal"),("","normal"),("O processo que vou mostrar:","normal"),("[Ex: como crio um Reel do zero em 45 minutos]","tag"),("","normal"),("O detalhe mais inesperado do meu processo:","normal"),("[Ex: nao uso roteiro, gravo em 1 take]","tag"),("","normal"),("Resultado final desse processo:","normal"),("[Ex: Reel com media de 80k views]","tag"),("","normal"),("Estruturas:","cmd"),("-> 'Vou mostrar exatamente como [resultado] em [tempo real].'","normal"),("-> 'Esse e meu processo de [X] passos. Ninguem filma isso.'","normal"),("-> '[Tempo]. E tudo que leva para [resultado]. Cada detalhe:'","normal")]
    },
    {
        "num":"G10","badge":"Prova Social","color":GREEN,"bg":GREEN_LIGHT,
        "title":"A Transformação do Aluno — Resultado de terceiro como gancho",
        "why":"Resultado de aluno é mais persuasivo que o seu próprio — elimina a objeção 'você é diferente de mim'. O espectador se vê no aluno, não no professor.",
        "roles":[("R","Narrador de transformação"),("O","Espectador se vê no aluno"),("L","Perfil real e autorizado"),("E","Ponto de partida comum"),("S","Antes → depois → método")],
        "code":[("Atue como roteirista de narrativas de transformacao.","hl"),("","normal"),("Crie 5 ganchos de Transformacao de Aluno baseados num caso real.","normal"),("","normal"),("Perfil do aluno (sem nome se preferir):","normal"),("[Ex: mae de 2 filhos, 34 anos, trabalhava CLT]","tag"),("","normal"),("Situacao antes:","normal"),("[Ex: 200 seguidores, nunca tinha vendido nada online]","tag"),("","normal"),("Resultado depois:","normal"),("[Ex: 12k seguidores e primeira venda em 45 dias]","tag"),("","normal"),("O metodo/diferencial que usou:","normal"),("[Ex: estrategia de Reels com gancho + CTA direto]","tag"),("","normal"),("Estruturas:","cmd"),("-> '[Perfil] tinha [antes]. Em [tempo], [resultado].'","normal"),("-> 'Recebi uma mensagem ontem. [Detalhe]. Aqui o que mudou.'","normal"),("-> 'Esse resultado nao foi meu. Foi de [perfil]. Comecou com:'","normal")]
    },
    {
        "num":"G11","badge":"Contra-narrativa","color":AMBER,"bg":AMBER_LIGHT,
        "title":"A Opinião Impopular — Posicionamento que divide e une",
        "why":"Opiniões polarizadoras aumentam comentários — quem concorda valida, quem discorda rebate. O algoritmo não distingue: comentário é engajamento. Conteúdo neutro não viraliza.",
        "roles":[("R","Provocador de debate saudável"),("O","Polarizar para engajar"),("L","Opinião real sua, defensável"),("E","Declaração clara, sem rodeios"),("S","Quem vai discordar claramente")],
        "code":[("Atue como criador de conteudo polarizador — estrategico.","hl"),("","normal"),("Crie 5 ganchos de Opiniao Impopular — algo que realmente","normal"),("acredito e que vai contra o senso comum do meu nicho.","normal"),("","normal"),("Minha opiniao impopular real:","normal"),("[Ex: consistencia sem estrategia e a causa de nao crescer]","tag"),("","normal"),("Quem vai discordar:","normal"),("[Ex: coaches que ensinam 'poste todo dia']","tag"),("","normal"),("Por que eu tenho razao (argumento principal):","normal"),("[Ex: tenho dados de 3 anos comparando perfis]","tag"),("","normal"),("Estruturas:","cmd"),("-> 'Opiniao impopular: [afirmacao]. Discorda? Me explica.'","normal"),("-> 'Cansei de fingir que [pratica comum] funciona. Nao funciona.'","normal"),("-> 'Todo mundo ensina [conselho]. Vou contar por que e errado.'","normal")]
    },
    {
        "num":"G12","badge":"Autoridade","color":BLUE,"bg":BLUE_LIGHT,
        "title":"A Lista Numerada Específica — Promessa de completude",
        "why":"Números criam expectativa de completude — o espectador assiste para 'coletar' todos os itens. Números ímpares (3, 5, 7) retêm mais. Números pequenos têm mais retenção em vídeos curtos.",
        "roles":[("R","Curador de listas de alto impacto"),("O","Retenção pela promessa numérica"),("L","Máx 5 itens para vídeos curtos"),("E","Números ímpares e específicos"),("S","Cada item deve ser acionável")],
        "code":[("Atue como roteirista de conteudo de lista de alto valor.","hl"),("","normal"),("Crie 5 ganchos de Lista Numerada para o meu video.","normal"),("Deixe claro quantos itens e qual o resultado ao final.","normal"),("","normal"),("Tema do video: [Ex: habitos que dobram produtividade]","tag"),("Numero de itens: [Use 3 ou 5 para videos curtos]","tag"),("Resultado prometido: [O que muda na vida do espectador]","tag"),("Tempo do video: [Ex: 60s / 90s / 3 min]","tag"),("","normal"),("Estruturas:","cmd"),("-> '[Numero] [itens] que [resultado]. Ninguem fala do [X].'","normal"),("-> 'Os [numero] erros que destroem [objetivo]. O ultimo e o mais comum.'","normal"),("-> '[Numero] minutos. [Numero] tecnicas. [Resultado mensuravel].'","normal"),("","normal"),("Para cada gancho: texto + qual item serve como 'gancho interno'.","cmd")]
    },
    {
        "num":"G13","badge":"Curiosidade","color":PURPLE,"bg":PURPLE_LIGHT,
        "title":"A Analogia Estranha — Comparação que para o scroll",
        "why":"O cérebro para quando encontra algo que não consegue categorizar imediatamente. Uma analogia inesperada entre dois universos cria 'confusão produtiva' — o espectador precisa resolver.",
        "roles":[("R","Criador de analogias disruptivas"),("O","Confusão produtiva nos 3s"),("L","Analogia deve ser resolvida no vídeo"),("E","Distância entre os universos"),("S","Universo A → Universo B → Insight")],
        "code":[("Atue como criador de metaforas para conteudo educativo.","hl"),("","normal"),("Crie 5 ganchos de Analogia Estranha — conecte meu tema","normal"),("a algo completamente diferente e inesperado.","normal"),("","normal"),("Meu tema: [Ex: estrategia de conteudo no Instagram]","tag"),("Conceito central: [Ex: consistencia supera volume aleatorio]","tag"),("","normal"),("Universos para analogia:","cmd"),("[ ] Academia / treino fisico","normal"),("[ ] Culinaria / receita","normal"),("[ ] Esporte especifico","normal"),("[ ] Fenomeno da natureza","normal"),("[ ] Jogo / videogame","normal"),("","normal"),("Estrutura:","cmd"),("-> '[Coisa estranha] e [meu tema] tem mais em comum do que imagina.'","normal"),("-> 'Tratar [meu tema] como [analogia] mudou meus resultados.'","normal")]
    },
    {
        "num":"G14","badge":"Prova Social","color":GREEN,"bg":GREEN_LIGHT,
        "title":"O Teste ao Vivo — 'Fiz o experimento para você'",
        "why":"Conteúdo experimental elimina a objeção 'será que funciona?'. Quando você testou e mostra o resultado real — inclusive se deu errado — a credibilidade sobe e o espectador fica.",
        "roles":[("R","Cientista de conteúdo prático"),("O","Suspense com resultado real"),("L","Experimento 100% real"),("E","Hipótese + desfecho inesperado"),("S","Período e métricas do teste")],
        "code":[("Atue como roteirista de conteudo experimental.","hl"),("","normal"),("Crie 5 ganchos de Teste ao Vivo baseados num experimento real.","normal"),("","normal"),("O que testei: [Ex: postei Reels sem legenda por 30 dias]","tag"),("Hipotese inicial: [O que eu esperava que acontecesse]","tag"),("Resultado real (pode ser surpresa):","tag"),("[Ex: alcance caiu 40% mas tempo de visualizacao subiu 60%]","tag"),("Periodo do teste: [Ex: 30 dias / 3 semanas]","tag"),("Metrica principal: [Ex: alcance / engajamento / seguidores]","tag"),("","normal"),("Estruturas:","cmd"),("-> 'Passei [tempo] testando [experimento]. Me surpreendeu.'","normal"),("-> 'Todo mundo diz [hipotese]. Testei por [tempo]. Errado.'","normal"),("-> 'Fiz o experimento que voce nao tinha tempo. Resultado:'","normal")]
    },
    {
        "num":"G15","badge":"Escassez","color":RED,"bg":RED_LIGHT,
        "title":"O Ponto de Virada — 'Estava errado até descobrir isso'",
        "why":"A estrutura de 'ponto de virada' combina escassez (você estava perdendo tempo/dinheiro) com narrativa de transformação. O espectador quer a informação que causou a virada.",
        "roles":[("R","Narrador de virada estratégica"),("O","Urgência via custo já pago"),("L","Erro e virada reais"),("E","Custo do erro antes da virada"),("S","Momento exato da descoberta")],
        "code":[("Atue como roteirista de narrativas de virada.","hl"),("","normal"),("Crie 5 ganchos de Ponto de Virada baseados numa mudanca real.","normal"),("","normal"),("O que eu acreditava/fazia antes:","normal"),("[Ex: que quantidade de posts era mais importante que qualidade]","tag"),("Por quanto tempo fiz isso: [Ex: 2 anos]","tag"),("O custo desse erro: [Ex: 730 posts sem gerar 1 real de venda]","tag"),("O que mudei: [Ex: 3 Reels estrategicos por semana]","tag"),("Resultado apos a mudanca: [Ex: primeiros R$3.000 em 45 dias]","tag"),("","normal"),("Estruturas:","cmd"),("-> 'Por [tempo], fiz [erro]. Desperdicei [custo]. Ate que [virada].'","normal"),("-> 'Esse insight me custou [preco]. Voce vai ter de graca agora.'","normal"),("-> '[Data]. Foi quando parei de [erro] e comecei a [solucao].'","normal")]
    },
    {
        "num":"G16","badge":"Autoridade","color":BLUE,"bg":BLUE_LIGHT,
        "title":"A Comparação Direta — 'Testei X e Y. Venceu foi...'",
        "why":"Comparações geram engajamento porque ativam o viés de pertencimento — o espectador torce por um lado antes de ver o resultado. Quem usa o método A fica para confirmar.",
        "roles":[("R","Analista comparativo de métodos"),("O","Engajamento via tomada de lado"),("L","Comparação justa e real"),("E","Resultado inesperado vence"),("S","Métrica objetiva de comparação")],
        "code":[("Atue como analista de performance de conteudo.","hl"),("","normal"),("Crie 5 ganchos de Comparacao Direta — comparo duas abordagens.","normal"),("","normal"),("Elemento A (o mais famoso/recomendado):","normal"),("[Ex: postar Reels todo dia]","tag"),("Elemento B (a alternativa testada):","normal"),("[Ex: 3 Reels por semana com roteiro estrategico]","tag"),("Metrica de comparacao:","normal"),("[Ex: crescimento de seguidores em 60 dias]","tag"),("Vencedor (pode ser B para gerar surpresa):","normal"),("[Ex: B cresceu 3x mais com 1/3 do esforco]","tag"),("","normal"),("Estruturas:","cmd"),("-> '[A] vs [B]. Testei os dois por [tempo]. O vencedor surpreende.'","normal"),("-> 'Todo mundo escolhe [A]. Escolhi [B]. Veja a diferenca.'","normal"),("-> '[A] ou [B]? Fiz o teste. Resultado: [teaser].'","normal")]
    },
    {
        "num":"G17","badge":"Curiosidade","color":PURPLE,"bg":PURPLE_LIGHT,
        "title":"O Diagnóstico Rápido — 'Descubra em 60s se você tem esse problema'",
        "why":"Conteúdo de autodiagnóstico ativa o narcisismo produtivo — o espectador assiste porque o conteúdo é sobre ele. Gera alto índice de comentários e salvamentos para rever.",
        "roles":[("R","Especialista em autodiagnóstico"),("O","Identificação imediata do espectador"),("L","Sinais reais e verificáveis"),("E","Perguntas que causam 'isso sou eu'"),("S","3 a 5 sinais diagnósticos")],
        "code":[("Atue como especialista em diagnostico de problemas do nicho.","hl"),("","normal"),("Crie 5 ganchos de Diagnostico Rapido — o espectador pensa","normal"),("'isso e exatamente o meu problema'.","normal"),("","normal"),("Problema central que meu publico tem:","normal"),("[Ex: falta de consistencia nas redes sociais]","tag"),("","normal"),("3 sinais visiveis desse problema (comportamentos reais):","normal"),("[Ex: posta 3 dias e some por 2 semanas]","tag"),("[Ex: tem rascunhos que nunca publica]","tag"),("[Ex: compara engajamento com perfis maiores]","tag"),("","normal"),("Estruturas:","cmd"),("-> 'Se voce faz [sinal 1] e [sinal 2], voce tem [problema].'","normal"),("-> '3 sinais de que [problema te impede de resultado].'","normal"),("-> 'Responde com sinceridade: [pergunta diagnostica].'","normal")]
    },
    {
        "num":"G18","badge":"Prova Social","color":GREEN,"bg":GREEN_LIGHT,
        "title":"A Pergunta Frequente — 'Todo mundo me pergunta sobre isso'",
        "why":"'Todo mundo pergunta' é prova social de relevância — valida que o tema é importante. O espectador pensa 'se muitos perguntam, eu provavelmente precisava saber'.",
        "roles":[("R","Curador de demanda real"),("O","Prova social de relevância"),("L","Pergunta realmente frequente"),("E","Volume e especificidade"),("S","Canal e perfil de quem pergunta")],
        "code":[("Atue como criador que responde demandas reais da audiencia.","hl"),("","normal"),("Crie 5 ganchos de Pergunta Frequente baseados em duvidas reais.","normal"),("","normal"),("A pergunta mais frequente que recebo:","normal"),("[Ex: 'Como voce decide o que postar?']","tag"),("Onde essa pergunta aparece mais:","normal"),("[Ex: DM do Instagram / comentarios / Stories]","tag"),("Volume aproximado:","normal"),("[Ex: 3 a 5 vezes por semana / toda vez que posto sobre X]","tag"),("","normal"),("Estruturas:","cmd"),("-> '[Numero] pessoas me perguntaram isso essa semana.'","normal"),("-> 'A pergunta que aparece no meu DM toda semana: [pergunta].'","normal"),("-> 'Essa duvida apareceu [numero] vezes nos comentarios.'","normal"),("","normal"),("Para cada gancho: texto + variacao para Story (max 5 palavras).","cmd")]
    },
    {
        "num":"G19","badge":"Autoridade","color":BLUE,"bg":BLUE_LIGHT,
        "title":"O Erro dos Outros — Análise de estratégia alheia",
        "why":"Análise crítica de erros alheios posiciona você como especialista sem precisar falar de si. Ver o erro de outro é mais memorável do que ouvir uma regra abstrata.",
        "roles":[("R","Analista crítico de estratégias"),("O","Autoridade via diagnóstico externo"),("L","Sem atacar pessoas, só estratégias"),("E","Erro específico e visível"),("S","Erro + diagnóstico + correção")],
        "code":[("Atue como consultor estrategico que analisa erros do nicho.","hl"),("","normal"),("Crie 5 ganchos de Analise de Erro Externo — analiso erros","normal"),("comuns que vejo nos perfis/estrategias do meu nicho.","normal"),("","normal"),("Erro mais comum que observo:","normal"),("[Ex: criar conteudo sem CTA claro nos primeiros 10 segundos]","tag"),("Perfil de quem comete:","normal"),("[Ex: criadores com 1k a 10k seguidores]","tag"),("Por que esse erro parece certo (o engano):","normal"),("[Ex: parece mais 'natural' nao pedir nada logo de cara]","tag"),("A correcao simples:","normal"),("[Ex: um CTA implicito nos primeiros 5s sobe retencao em 30%]","tag"),("","normal"),("Estruturas:","cmd"),("-> 'Analisei [numero] perfis essa semana. O mesmo erro em [X]%.'","normal"),("-> 'Voce provavelmente faz isso tambem. Te custa [resultado].'","normal")]
    },
    {
        "num":"G20","badge":"Contra-narrativa","color":AMBER,"bg":AMBER_LIGHT,
        "title":"O Conselho Não Pedido — 'Ninguém vai te dizer isso'",
        "why":"A percepção de que alguém está dando informação que 'o sistema' esconde ativa confiança e lealdade. Posiciona o criador como aliado contra um inimigo comum.",
        "roles":[("R","Aliado que quebra o silêncio"),("O","Lealdade via informação exclusiva"),("L","Inimigo deve ser estrutural, não pessoal"),("E","Por que outros calam esse assunto"),("S","Benefício claro de saber isso")],
        "code":[("Atue como criador posicionado como aliado e conselheiro honesto.","hl"),("","normal"),("Crie 5 ganchos de Conselho Nao Pedido — informacao que meu","normal"),("publico precisava mas ninguem do nicho costuma dar abertamente.","normal"),("","normal"),("A verdade que vou dizer:","normal"),("[Ex: a maioria dos cursos ensina taticas de 2020]","tag"),("Por que outros nao falam isso:","normal"),("[Ex: porque vendem esses mesmos cursos]","tag"),("O beneficio de saber isso:","normal"),("[Ex: parar de investir em estrategias sem resultado atual]","tag"),("Inimigo estrutural (nunca pessoal):","normal"),("[Ex: mercado de infoprodutos desatualizado]","tag"),("","normal"),("Estruturas:","cmd"),("-> 'Ninguem no [nicho] vai te falar isso. Mas voce precisa saber.'","normal"),("-> 'Isso vai contrariar o que [grupo] te ensinou. Os numeros nao mentem.'","normal")]
    },
]

VSL_DATA = [
    {
        "num":"V01","badge":"Lançamento","color":PINK,"bg":PINK_LIGHT,
        "title":"AIDA Clássico — Do problema à oferta em 4 blocos",
        "why":"O framework mais testado do copywriting direto, adaptado ao formato Story. Cada bloco tem uma função. O erro mais comum é pular o bloco de Desejo e ir direto para o CTA — isso mata a conversão.",
        "framework":"AIDA: Atenção → Interesse → Desejo → Ação",
        "frames":[
            ("A","Atenção (0–5s)","Gancho que para o dedo. Sem introdução, sem 'oi gente'.","Curiosidade / dor"),
            ("I","Interesse (15–30s)","Aprofunda o problema. Você entende o espectador melhor que ele.","Identificação / empatia"),
            ("D","Desejo (30–60s)","Solução com resultado específico. É aqui que a venda acontece.","Prova social / autoridade"),
            ("A","Ação (60–75s)","CTA único, claro e com fricção zero.","Escassez / urgência"),
        ],
        "roles":[("R","Copywriter de resposta direta"),("O","VSL 4 blocos AIDA em 75s"),("L","1 ideia por frame de Story"),("E","Transição Desejo → CTA fluida"),("S","Script + legenda + CTA por bloco")],
        "code":[("// PM 01 deve estar ativo antes de rodar este prompt","cmt"),("","normal"),("Atue como copywriter de VSL curta para Instagram Stories.","hl"),("","normal"),("Escreva um roteiro AIDA para Story de venda. Duracao: 75s.","normal"),("","normal"),("O que estou vendendo: [Nome + preco]","tag"),("Para quem: [Perfil exato do comprador ideal]","tag"),("Dor principal resolvida: [O problema central]","tag"),("Resultado principal entregue: [O que muda na vida]","tag"),("Prova social disponivel: [Numero de alunos / resultado]","tag"),("CTA desejado: [link na bio / DM palavra X / arrasta pra cima]","tag"),("Urgencia real (se houver): [vagas / desconto ate X]","tag"),("","normal"),("Para cada bloco (A-I-D-A) entregue:","cmd"),("-> Script completo em linguagem falada","normal"),("-> Texto on-screen sugerido (max 6 palavras)","normal"),("-> Gatilho mental ativo nesse bloco","normal"),("-> Duracao exata em segundos","normal"),("","normal"),("// Regra de ouro: 1 ideia por frame. 1 CTA no video inteiro.","cmt")]
    },
    {
        "num":"V02","badge":"Aquecimento","color":GREEN,"bg":GREEN_LIGHT,
        "title":"PAS Emocional — Problema, Agitação e Solução com história",
        "why":"PAS é o framework mais eficaz para público frio. A fase de Agitação é onde a maioria falha: sem aprofundar a dor emocionalmente, a solução soa genérica.",
        "framework":"PAS: Problema → Agitação → Solução",
        "frames":[
            ("P","Problema (0–20s)","Nomeia o problema com a linguagem exata do público.","Reconhecimento / espelho"),
            ("A","Agitação (20–55s)","Aprofunda as consequências. O bloco mais longo.","Dor de identidade / FOMO"),
            ("S","Solução (55–90s)","Apresenta a solução como alívio natural — não como venda.","Esperança / autoridade"),
        ],
        "roles":[("R","Roteirista de storytelling emocional"),("O","Criar urgência via dor amplificada"),("L","Agitação real, não manipulação"),("E","Dor emocional, não racional"),("S","História de 1 personagem real")],
        "code":[("Atue como roteirista de VSL com storytelling emocional.","hl"),("","normal"),("Escreva um roteiro PAS para Stories. Duracao: 90s. Publico frio.","normal"),("","normal"),("Personagem da historia:","normal"),("[Ex: 'eu mesmo, ha 2 anos' / 'minha aluna Carla, mae de 2 filhos']","tag"),("O problema exato desse personagem:","normal"),("[Descreva em detalhe — o mais especifico possivel]","tag"),("Consequencias emocionais de NAO resolver (liste 3):","normal"),("[Ex: vergonha social / sensacao de estagnacao / medo]","tag"),("A virada: [O momento em que a solucao entrou na historia]","tag"),("O produto/servico que resolve: [Nome + o que entrega]","tag"),("CTA final: [Acao unica desejada]","tag"),("","normal"),("Para cada bloco (P-A-S):","cmd"),("-> Script em linguagem falada, primeira pessoa","normal"),("-> Texto on-screen (max 5 palavras por frame)","normal"),("-> Emocao dominante a ser transmitida","normal"),("","normal"),("// O bloco A (Agitacao) deve ser o mais longo. Nao mencione o","cmt"),("// produto ate o bloco S.","cmt")]
    },
    {
        "num":"V03","badge":"Oferta direta","color":RED,"bg":RED_LIGHT,
        "title":"FAB Invertido — Benefício antes de feature, CTA no meio",
        "why":"A versão clássica do FAB começa pela Feature — erro fatal em vídeo curto. Neste formato invertido, o CTA aparece antes do fim — técnica do 'CTA precoce' que aumenta cliques em até 40% em Stories.",
        "framework":"FAB Invertido: Benefício → Feature → CTA Precoce → Prova + CTA Final",
        "frames":[
            ("B","Benefício (0–15s)","Abre com o resultado final. Sem contexto, sem apresentação.","Desejo / resultado imediato"),
            ("F","Feature (15–35s)","O mecanismo único — o 'como' que torna o benefício crível.","Autoridade / credibilidade"),
            ("A","CTA Precoce (35–45s)","CTA no meio do vídeo — captura quem já estava pronto.","Escassez / urgência"),
            ("+","Prova + CTA Final (45–60s)","Depoimento rápido + repetição do CTA com variação.","Prova social / reciprocidade"),
        ],
        "roles":[("R","Copywriter de oferta direta"),("O","Conversão rápida em público quente"),("L","Máx 3 benefícios por script"),("E","CTA no frame 3, repetido no 5"),("S","Benefício mensurável e específico")],
        "code":[("Atue como copywriter de oferta direta para Stories de 60s.","hl"),("","normal"),("Escreva um roteiro FAB Invertido para publico quente.","normal"),("","normal"),("Produto/servico: [Nome + o que entrega + preco]","tag"),("Beneficio 1 (mais desejado): [Resultado especifico mensuravel]","tag"),("Beneficio 2: [Segundo resultado mais importante]","tag"),("Beneficio 3: [Beneficio bonus ou diferencial]","tag"),("","normal"),("O mecanismo unico (feature):","normal"),("[O que torna minha solucao diferente de qualquer outra]","tag"),("","normal"),("Prova social: [depoimento OU numero OU print de mensagem]","tag"),("Urgencia/escassez real: [O que limita ou tem prazo]","tag"),("CTA: [Acao unica — link, DM, palavra-chave]","tag"),("","normal"),("Entregue:","cmd"),("-> Script por frame em linguagem falada","normal"),("-> Texto on-screen por frame","normal"),("-> Variacao do CTA para frame 3 e frame final","normal"),("// Inclua o CTA duas vezes: no frame 3 e no frame 5.","cmt")]
    },
    {
        "num":"V04","badge":"Autoridade","color":PURPLE,"bg":PURPLE_LIGHT,
        "title":"Before/After/Bridge — Transformação em 3 atos",
        "why":"O BAB é o framework mais intuitivo para criadores com resultados reais. O 'Before' cria identificação, o 'After' cria desejo, a 'Bridge' revela o produto como o único caminho lógico.",
        "framework":"BAB: Before → After → Bridge",
        "frames":[
            ("B","Before (0–20s)","Pinta o passado com detalhes sensoriais. Dor concreta.","Identificação / espelho"),
            ("A","After (20–50s)","Estado transformado com riqueza sensorial. Números e emoções.","Desejo / visão de futuro"),
            ("B","Bridge (50–75s)","Revela o mecanismo que conecta os dois estados.","Autoridade / reciprocidade"),
        ],
        "roles":[("R","Narrador de transformação BAB"),("O","Posicionar produto como ponte óbvia"),("L","Before e After devem ser reais"),("E","Contraste emocional forte"),("S","Bridge revela mecanismo, não produto")],
        "code":[("Atue como copywriter especializado no framework BAB.","hl"),("","normal"),("Escreva um roteiro Before/After/Bridge em 75s.","normal"),("","normal"),("Estado BEFORE (como era antes):","normal"),("[Detalhe: rotina, emocao, resultado, frustracao]","tag"),("Estado AFTER (como ficou depois):","normal"),("[Detalhe: o que mudou na rotina, nos numeros, na emocao]","tag"),("A Bridge — o mecanismo da transformacao:","normal"),("[O insight, metodo ou sistema — NAO o nome do produto ainda]","tag"),("O produto que ensina esse mecanismo:","normal"),("[Nome + formato + preco]","tag"),("","normal"),("Tom do Before: [Confessional / empatico / provocador]","tag"),("Tom do After: [Inspiracional / factual / emocional]","tag"),("CTA: [Acao + onde + urgencia se houver]","tag"),("","normal"),("Entregue:","cmd"),("-> Script por bloco em linguagem falada","normal"),("-> Contraste visual sugerido para on-screen (Before vs After)","normal"),("-> Frase de transicao entre cada bloco","normal"),("-> Onde inserir pausa dramatica para aumentar tensao","normal")]
    },
    {
        "num":"V05","badge":"Reativação","color":BLUE,"bg":BLUE_LIGHT,
        "title":"Objeção Frontal — Derruba a resistência antes de vender",
        "why":"Ideal para reativar quem já viu sua oferta e não comprou. Em vez de repetir o argumento de venda, este framework abre com a objeção principal — o que desativa a resistência imediatamente.",
        "framework":"Objection-First: Objeção → Reframe → Prova → CTA",
        "frames":[
            ("O","Objeção (0–15s)","Abre com a objeção exata na voz do espectador.","Empatia / validação"),
            ("R","Reframe (15–45s)","Não refuta — ressignifica. A objeção é baseada em premissa errada.","Curiosidade / autoridade"),
            ("P","Prova (45–75s)","Prova que confirma o reframe. Alguém que tinha a mesma objeção.","Prova social / similaridade"),
            ("C","CTA (75–90s)","CTA com referência à objeção quebrada.","Comprometimento / escassez"),
        ],
        "roles":[("R","Especialista em quebra de objeções"),("O","Reativar indecisos com empatia"),("L","Máx 2 objeções por roteiro"),("E","Reframe que ressignifica, não convence"),("S","Prova específica por objeção")],
        "code":[("Atue como especialista em quebra de objecoes para reativacao.","hl"),("","normal"),("Escreva um roteiro Objecao Frontal para reativar quem","normal"),("ja viu minha oferta mas nao comprou. Duracao: 90s.","normal"),("","normal"),("Oferta que quero reativar: [Nome + preco + o que entrega]","tag"),("Objecao mais comum: [Ex: 'e caro' / 'nao tenho tempo']","tag"),("Por que essa objecao esta errada (reframe):","normal"),("[Sua perspectiva que muda o enquadramento]","tag"),("Prova que confirma o reframe:","normal"),("[Depoimento de aluno que tinha essa objecao + resultado]","tag"),("Urgencia para esse CTA: [Ex: 'ultimas vagas' / 'desconto ate X']","tag"),("CTA: [Acao especifica]","tag"),("","normal"),("Entregue:","cmd"),("-> Script por frame em linguagem falada","normal"),("-> Frase de abertura que nomeia a objecao sem acusar","normal"),("-> Frase de CTA que referencia a objecao quebrada","normal"),("-> Variacao para repetir como story de texto (sem video)","normal")]
    },
    {
        "num":"V06","badge":"Lançamento","color":PINK,"bg":PINK_LIGHT,
        "title":"Prova Social em Cascata — Depoimentos que vendem sozinhos",
        "why":"Empilhar 3 depoimentos de perfis diferentes cobre o espectro completo de identificação. Quem está no início se vê no primeiro, quem está avançado se vê no terceiro.",
        "framework":"Social Proof Stack: Abertura → 3 Provas em Cascata → CTA",
        "frames":[
            ("1","Abertura (0–10s)","Promessa de prova: 'Vou mostrar o que aconteceu com 3 pessoas...'","Curiosidade / antecipação"),
            ("2","Prova 1 (10–25s)","Iniciante. Perfil com ponto de partida baixo e resultado visível.","Similaridade / esperança"),
            ("3","Prova 2 (25–40s)","Perfil intermediário. Mostra que o método funciona em variados contextos.","Consistência / credibilidade"),
            ("4","Prova 3 + CTA (40–60s)","Resultado mais expressivo + CTA. A escada termina no pico.","Prova máxima / escassez"),
        ],
        "roles":[("R","Curador de prova social estratégica"),("O","Quebrar resistência por volume"),("L","Depoimentos reais e autorizados"),("E","Diversidade de perfis"),("S","1 resultado específico por depoimento")],
        "code":[("Atue como roteirista de prova social estrategica para Stories.","hl"),("","normal"),("Escreva um roteiro Prova Social em Cascata com 3 depoimentos.","normal"),("Duracao: 60 segundos.","normal"),("","normal"),("Produto/servico: [Nome + o que resolve]","tag"),("","normal"),("// Para cada depoimento, forneça:","cmt"),("","normal"),("Depoimento 1 — Perfil iniciante:","cmd"),("Contexto antes: [situacao de partida]","tag"),("Resultado obtido: [resultado especifico]","tag"),("","normal"),("Depoimento 2 — Perfil intermediario:","cmd"),("Contexto antes: [situacao diferente do primeiro]","tag"),("Resultado obtido: [resultado diferente]","tag"),("","normal"),("Depoimento 3 — Resultado mais expressivo:","cmd"),("Contexto antes: [situacao]","tag"),("Resultado obtido: [o maior resultado que tenho]","tag"),("","normal"),("CTA final: [Acao + urgencia]","tag"),("","normal"),("Entregue: script da abertura + transicao entre provas + CTA","cmd")]
    },
    {
        "num":"V07","badge":"Aquecimento","color":GREEN,"bg":GREEN_LIGHT,
        "title":"Micro-Aula de 60s — Entrega valor real e planta a oferta",
        "why":"Entregar valor real antes de vender ativa o gatilho de reciprocidade. A 'lacuna de conhecimento' no final torna a oferta a continuação natural do conteúdo, não uma interrupção.",
        "framework":"Value-First: Gancho → Ensino → Lacuna → Oferta",
        "frames":[
            ("G","Gancho (0–10s)","Promete ensinar algo específico e útil em 60 segundos.","Curiosidade / promessa"),
            ("E","Ensino (10–40s)","Ensina de verdade — 1 técnica com passo a passo executável.","Reciprocidade / autoridade"),
            ("L","Lacuna (40–52s)","Mostra o que mais existe além do que foi ensinado.","Curiosidade / incompletude"),
            ("O","Oferta (52–60s)","CTA que posiciona o produto como o lugar onde a lacuna é preenchida.","Completude / reciprocidade"),
        ],
        "roles":[("R","Professor que converte via valor"),("O","Reciprocidade + lacuna de conhecimento"),("L","Ensino real, não teaser vago"),("E","Lacuna deve ser honesta"),("S","1 técnica completa ensinada")],
        "code":[("Atue como professor e copywriter de conteudo que converte.","hl"),("","normal"),("Escreva um roteiro Value-First VSL onde ensino algo real","normal"),("e planto minha oferta como continuacao natural. Duracao: 60s.","normal"),("","normal"),("O que vou ensinar (1 tecnica completa e acionavel):","normal"),("[Descreva a tecnica em detalhes — vou realmente ensina-la]","tag"),("Por que essa tecnica sozinha nao e suficiente (a lacuna honesta):","normal"),("[O que falta para ter o resultado completo]","tag"),("O que meu produto entrega alem dessa tecnica:","normal"),("[As outras pecas do metodo completo]","tag"),("Produto: [Nome + formato + preco + CTA]","tag"),("","normal"),("Entregue:","cmd"),("-> Script por frame em linguagem falada","normal"),("-> A frase exata da lacuna (deve soar honesta, nao manipuladora)","normal"),("-> Transicao natural entre Lacuna e Oferta","normal"),("","normal"),("// Ensine de verdade. Conteudo real retém mais do que teaser.","cmt")]
    },
    {
        "num":"V08","badge":"Oferta direta","color":RED,"bg":RED_LIGHT,
        "title":"Urgência Real — O Story do prazo que fecha",
        "why":"O Story de prazo só funciona quando a urgência é real e explicada. Dizer 'últimas horas' sem contexto gera ceticismo. Explicar por que o prazo existe transforma urgência artificial em legítima.",
        "framework":"Deadline VSL: Aviso → Razão → Consequência → CTA",
        "frames":[
            ("1","Aviso (0–10s)","Alerta claro do prazo com data/hora específica. Sem rodeio.","Escassez / urgência"),
            ("2","Razão (10–25s)","Explica por que o prazo existe. A razão torna a urgência crível.","Lógica / transparência"),
            ("3","Consequência (25–35s)","O que acontece depois do prazo: preço maior, vagas fechadas.","Aversão à perda"),
            ("4","CTA (35–45s)","O CTA mais direto do pack. 'Link na bio. Agora.'","Urgência máxima / ação"),
        ],
        "roles":[("R","Especialista em urgência legítima"),("O","CTA imediato via prazo real"),("L","Prazo 100% real e verificável"),("E","Razão do prazo explicada"),("S","Consequência concreta de perder")],
        "code":[("Atue como copywriter de deadline e urgencia legitima.","hl"),("","normal"),("Escreva um roteiro Deadline VSL de 45 segundos.","normal"),("Este e o Story mais direto — o publico ja conhece a oferta.","normal"),("","normal"),("Oferta: [Nome + o que resolve]","tag"),("Prazo exato (data e hora): [Ex: domingo as 23h59]","tag"),("","normal"),("Razao real do prazo (escolha):","cmd"),("[ ] Preco sobe apos o lancamento (de X para Y)","normal"),("[ ] Vagas limitadas pela capacidade de atendimento","normal"),("[ ] Bonus exclusivo removido apos prazo","normal"),("[ ] Desconto de lancamento encerra","normal"),("","normal"),("Consequencia especifica apos o prazo:","normal"),("[O que muda exatamente]","tag"),("CTA: [Acao + onde + friccao zero]","tag"),("","normal"),("// Regra absoluta: o prazo deve ser 100% real.","cmt"),("// Urgencia falsa queima confianca — e confianca nao se recupera.","cmt")]
    },
]

LEGENDAS = [
    {
        "num":"L01","badge":"Comentário","color":AMBER,"bg":AMBER_LIGHT,
        "title":"A Pergunta Divisora — Força o posicionamento público",
        "why":"Perguntas de escolha binária ativam o instinto de posicionamento público. O leitor não quer apenas ler — quer ser visto opinando. Isso gera comentários longos que o algoritmo interpreta como alto engajamento.",
        "signal":"Sinal primário: Comentário",
        "roles":[("R","Facilitador de debate estratégico"),("O","Legenda que exige posicionamento"),("L","Debate saudável, não polêmica vazia"),("E","Pergunta final irresistível"),("S","3 variações de pergunta por legenda")],
        "code":[("// Rode após PM 01 — briefing de marca ativo","cmt"),("","normal"),("Atue como copywriter especializado em legendas de alto engajamento.","hl"),("","normal"),("Escreva 3 variacoes de legenda com o framework Pergunta Divisora.","normal"),("Objetivo principal: gerar comentarios via posicionamento binario.","normal"),("","normal"),("Tema do post: [Assunto do Reel/carrossel/post]","tag"),("Minha posicao sobre o tema: [O que voce defende]","tag"),("A posicao oposta legitima: [O que alguem razoavel defenderia]","tag"),("O perfil que vai discordar: [Quem vai rebater nos comentarios]","tag"),("","normal"),("Estrutura obrigatoria:","cmd"),("-> Linha 1: afirmacao que ja divide (sem pergunta ainda)","normal"),("-> Linhas 2-5: argumento que fundamenta sem fechar o debate","normal"),("-> Ultima linha: pergunta binaria de posicionamento","tag"),("","normal"),("Para cada variacao:","cmd"),("-> Legenda formatada para Instagram (com quebras de linha)","normal"),("-> Pergunta de CTA em 3 formulacoes (escolha a melhor)","normal"),("-> Estimativa de polarizacao: baixa / media / alta","tag"),("-> Primeiro comentario sugerido para 'plantar' o debate","normal"),("","normal"),("// Regra: 1 pergunta por legenda. A pergunta vai na ultima linha.","cmt")]
    },
    {
        "num":"L02","badge":"Salvamento","color":BLUE,"bg":BLUE_LIGHT,
        "title":"O Guia Denso — Mais valor por linha do que qualquer post",
        "why":"Pessoas salvam o que não podem absorver de uma vez. Uma legenda densa com múltiplas técnicas ativa o comportamento de arquivo. O Instagram prioriza posts com alto índice de salvamento.",
        "signal":"Sinal primário: Salvamento",
        "roles":[("R","Curador de conhecimento comprimido"),("O","Legenda que precisa ser salva"),("L","Cada item deve ser acionável"),("E","Densidade sem perder clareza"),("S","CTA explícito de salvamento")],
        "code":[("Atue como curador de conhecimento em legendas de alta densidade.","hl"),("","normal"),("Escreva 2 variacoes de legenda do tipo Guia Denso.","normal"),("Objetivo: maximo de salvamentos — mais valiosa que a maioria","normal"),("dos posts completos do nicho.","normal"),("","normal"),("Tema/conhecimento que vou condensar:","normal"),("[Descreva o assunto — quanto mais especifico, melhor]","tag"),("Numero de itens da lista: [Entre 5 e 10 — impar e melhor]","tag"),("","normal"),("Nivel de profundidade:","cmd"),("[ ] Iniciante — linguagem simples, exemplos do dia a dia","normal"),("[ ] Intermediario — assume conhecimento basico do nicho","normal"),("[ ] Avancado — para quem ja pratica, vai alem do obvio","normal"),("","normal"),("Item contra-intuitivo obrigatorio:","normal"),("[Um ponto que contradiz o senso comum — inclua no item 3 ou 4]","tag"),("","normal"),("Estrutura obrigatoria:","cmd"),("-> Linha 1: promessa de valor comprimido","normal"),("-> Lista numerada com cada item em max 2 linhas","normal"),("-> Ultima linha: CTA explicito de salvamento","normal"),("","normal"),("// Nao termine com pergunta — o objetivo e salvar, nao comentar.","cmt")]
    },
    {
        "num":"L03","badge":"Compartilhamento","color":GREEN,"bg":GREEN_LIGHT,
        "title":"A Dedicatória — 'Marca alguém que precisa ver isso'",
        "why":"Pessoas compartilham conteúdo que serve como 'presente' para alguém específico. O CTA 'marca alguém que...' ativa o instinto social de presentear com conhecimento.",
        "signal":"Sinal primário: Compartilhamento",
        "roles":[("R","Escritor de conteúdo presenteável"),("O","Ativar instinto de presentear"),("L","Conteúdo fala de alguém, não ao alguém"),("E","Identificação com terceiro"),("S","Perfil de quem vai ser marcado")],
        "code":[("Atue como copywriter de legendas que geram marcacoes.","hl"),("","normal"),("Escreva 3 variacoes de legenda Dedicatoria.","normal"),("Objetivo: maximo de compartilhamentos via instinto de presentear.","normal"),("","normal"),("Tema do post: [O que o post ensina ou comunica]","tag"),("","normal"),("Perfil da pessoa que vai ser marcada (seja ultra-especifico):","normal"),("[Ex: 'amigo que reclama do chefe mas nao faz nada'","tag"),(" Ex: 'irma que quer empreender mas tem medo de comecar']","tag"),("","normal"),("O que essa pessoa esta vivendo agora:","normal"),("[Situacao especifica e emocao predominante]","tag"),("O que esse conteudo vai mudar ou confirmar para ela:","normal"),("[O insight ou validacao que ela vai receber ao ler]","tag"),("","normal"),("Para cada variacao:","cmd"),("-> Legenda completa formatada","normal"),("-> CTA de marcacao com 3 formulacoes da descricao da pessoa","normal"),("-> Por que esse perfil vai ter alta taxa de marcacao","normal"),("","normal"),("// 'Marca alguem' e fraco. 'Marca aquela pessoa que...' e magnetico.","cmt")]
    },
    {
        "num":"L04","badge":"Múltiplos sinais","color":PURPLE,"bg":PURPLE_LIGHT,
        "title":"A Confissão Ressonante — Vulnerabilidade que viraliza",
        "why":"Confissões reais criam identificação profunda: comentários de 'eu também', compartilhamentos e salvamentos. É o formato de maior ROI emocional — mas só funciona com vulnerabilidade genuína.",
        "signal":"Sinais: Comentário + Compartilhamento",
        "roles":[("R","Ghostwriter de vulnerabilidade estratégica"),("O","Identificação coletiva via confissão"),("L","Confissão real, não inventada"),("E","Sentimento que ninguém articula"),("S","Virada ou aprendizado ao final")],
        "code":[("Atue como ghostwriter de vulnerabilidade estrategica.","hl"),("","normal"),("Escreva 2 variacoes de Confissao Ressonante.","normal"),("Sinal primario: comentario. Secundario: compartilhamento.","cmd"),("","normal"),("A confissao real que quero fazer:","normal"),("[Descreva o sentimento ou situacao honesta — especifico]","tag"),("O contexto em que esse sentimento apareceu:","normal"),("[Quando, em que situacao, o que estava acontecendo]","tag"),("O que isso custou (emocionalmente ou praticamente):","normal"),("[A consequencia real de ter guardado ou vivido assim]","tag"),("A virada ou o aprendizado:","normal"),("[O que mudou — pode ser sutil, nao precisa ser epico]","tag"),("Quem no seu publico vai se identificar:","normal"),("[Perfil especifico — para calibrar linguagem e tom]","tag"),("","normal"),("Nivel de vulnerabilidade:","cmd"),("[ ] Leve — algo que muitos passam mas ninguem fala","normal"),("[ ] Medio — algo pessoal que exige coragem para publicar","normal"),("[ ] Intenso — revelacao que vai mudar como te veem","normal"),("","normal"),("// Vulnerabilidade sem virada = lamento. Com virada = autoridade.","cmt")]
    },
    {
        "num":"L05","badge":"Salvamento","color":BLUE,"bg":BLUE_LIGHT,
        "title":"O Checklist Executável — Lista que se torna ferramenta",
        "why":"Um checklist não é apenas conteúdo — é uma ferramenta. Pessoas salvam ferramentas para usar depois. Quanto mais parecer uma lista de verificação real, mais o leitor salva.",
        "signal":"Sinal primário: Salvamento",
        "roles":[("R","Designer de ferramentas de ação"),("O","Legenda que vira rotina de uso"),("L","Itens acionáveis, não teóricos"),("E","Formato visual de checklist real"),("S","Contexto de uso explícito")],
        "code":[("Atue como especialista em ferramentas de produtividade.","hl"),("","normal"),("Escreva 2 variacoes de legenda Checklist Executavel.","normal"),("Objetivo: maximo de salvamentos — deve parecer ferramenta.","normal"),("","normal"),("Situacao de uso do checklist:","normal"),("[Quando o publico vai precisar dessa lista?]","tag"),("[Ex: 'antes de gravar um Reel' / 'toda segunda-feira']","tag"),("Tema do checklist: [O processo ou tarefa que cobre]","tag"),("Numero de itens: [Entre 5 e 8]","tag"),("","normal"),("Os itens reais (rascunho — vou refinar):","normal"),("[Liste os itens que voce quer incluir]","tag"),("","normal"),("Nivel do publico:","cmd"),("[ ] Iniciante — itens basicos que ninguem lembra","normal"),("[ ] Avancado — itens que so quem pratica vai valorizar","normal"),("","normal"),("Para cada variacao:","cmd"),("-> Legenda com marcadores visuais de checklist","normal"),("-> Contexto de uso na primeira linha","normal"),("-> Pelo menos 1 item 'nunca tinha pensado nisso'","normal"),("-> CTA de salvamento com razao especifica","normal"),("","normal"),("// Cada item: verbo imperativo. 'Verifique', 'Defina', 'Revise'.","cmt")]
    },
    {
        "num":"L06","badge":"Comentário","color":AMBER,"bg":AMBER_LIGHT,
        "title":"A Polêmica Técnica — Debate entre especialistas",
        "why":"Debates técnicos geram comentários longos e de alta qualidade. Pessoas que sabem sobre o assunto precisam corrigir, complementar ou validar. O ego técnico é poderoso.",
        "signal":"Sinal primário: Comentário",
        "roles":[("R","Especialista que instiga debate técnico"),("O","Comentários longos e qualificados"),("L","Posição técnica real e defensável"),("E","Afirmação que provoca o especialista"),("S","Pergunta para quem já pratica")],
        "code":[("Atue como especialista que instiga debates tecnicos produtivos.","hl"),("","normal"),("Escreva 2 variacoes de legenda Polemica Tecnica.","normal"),("Objetivo: comentarios longos e qualificados de quem conhece.","normal"),("","normal"),("A posicao tecnica que defendo:","normal"),("[Afirmacao sobre metodo, estrategia ou ferramenta do nicho]","tag"),("O que a maioria dos especialistas pensa diferente:","normal"),("[A posicao dominante que voce contesta]","tag"),("Meu argumento principal (dado ou experiencia real):","normal"),("[O que sustenta sua posicao — seja especifico]","tag"),("O contra-argumento mais forte que posso receber:","normal"),("[Para ja deixar a abertura certa no texto]","tag"),("","normal"),("Para cada variacao:","cmd"),("-> Legenda em tom tecnico mas acessivel","normal"),("-> Afirmacao-gatilho na primeira linha","normal"),("-> Argumento embasado no meio","normal"),("-> Abertura explicita para contra-argumento no final","normal"),("","normal"),("// A humildade tecnica no final ('talvez eu esteja errado')","cmt"),("// e o que transforma afirmacao em convite ao debate.","cmt")]
    },
    {
        "num":"L07","badge":"Múltiplos sinais","color":PURPLE,"bg":PURPLE_LIGHT,
        "title":"A Narrativa de Virada — Storytelling que retém e converte",
        "why":"Narrativas com arco completo ativam dois comportamentos: comentários de identificação e salvamentos para reler a virada quando em crise. É o formato mais próximo do storytelling literário.",
        "signal":"Sinais: Comentário + Salvamento",
        "roles":[("R","Ghostwriter de narrativa pessoal"),("O","Arco narrativo completo em legenda"),("L","História real, não parábola inventada"),("E","Conflito específico, não genérico"),("S","Detalhe sensorial no conflito")],
        "code":[("Atue como ghostwriter de storytelling pessoal.","hl"),("","normal"),("Escreva 2 variacoes de Narrativa de Virada.","normal"),("Sinais: comentario + salvamento via arco narrativo completo.","cmd"),("","normal"),("A cena de abertura (momento especifico no tempo):","normal"),("[Ex: 'era uma terca a noite, minha planilha aberta, R$0 no mes']","tag"),("O conflito central:","normal"),("[O que estava em jogo — emocao + situacao concreta]","tag"),("Detalhes sensoriais do conflito:","normal"),("[O que voce viu, sentiu, pensou — quanto mais especifico melhor]","tag"),("O momento exato da virada:","normal"),("[Uma frase, um dado, uma decisao, uma conversa — algo concreto]","tag"),("O aprendizado em 1 frase:","normal"),("[O que voce diria pra voce mesmo antes do conflito]","tag"),("","normal"),("Tom da narrativa:","cmd"),("[ ] Intimo e silencioso — como conversa de 2h da manha","normal"),("[ ] Direto e sem drama — os fatos e o que aprendi","normal"),("[ ] Inspiracional com peso — dificil mas valeu","normal"),("","normal"),("CTA duplo na ultima linha:","cmd"),("'Salva se esta vivendo. Comenta se ja superou.'","tag")]
    },
    {
        "num":"L08","badge":"Compartilhamento","color":GREEN,"bg":GREEN_LIGHT,
        "title":"A Afirmação Validadora — 'Alguém finalmente disse'",
        "why":"Pessoas compartilham conteúdo que valida algo que já acreditavam mas não sabiam expressar. 'Alguém finalmente disse' é o gatilho de compartilhamento mais poderoso.",
        "signal":"Sinal primário: Compartilhamento",
        "roles":[("R","Articulador de crenças não-ditas"),("O","Ser o porta-voz do que o público pensa"),("L","Crença que o público já tem, não nova"),("E","Articulação perfeita, não originalidade"),("S","Quem vai se sentir representado")],
        "code":[("Atue como copywriter que articula crencas nao-ditas.","hl"),("","normal"),("Escreva 3 variacoes de Afirmacao Validadora.","normal"),("Objetivo: maximo de compartilhamentos — o leitor vai usar o","normal"),("post para representar algo que ja acredita.","normal"),("","normal"),("A crenca que meu publico ja tem mas raramente articula:","normal"),("[A conviccao coletiva nao-dita do seu nicho]","tag"),("[Ex: 'consistencia forcada e toxica' / 'descanso e produtividade']","tag"),("","normal"),("Quem vai se sentir representado:","normal"),("[Perfil especifico — quanto mais preciso, mais compartilhamento]","tag"),("O que essa crenca contraria (o senso comum oposto):","normal"),("[Para dar contraste a afirmacao]","tag"),("Para quem o leitor vai enviar esse post:","normal"),("[Ex: 'para o chefe' / 'para o amigo que duvida']","tag"),("","normal"),("Tom:","cmd"),("[ ] Manifesto — declaracao de principio","normal"),("[ ] Carta — como escrever para uma pessoa especifica","normal"),("[ ] Sentenca — curto, denso, definitivo","normal"),("","normal"),("// Escreva 1 linha que funcione fora de contexto (para prints).","cmt")]
    },
    {
        "num":"L09","badge":"Comentário","color":AMBER,"bg":AMBER_LIGHT,
        "title":"A Escada de Identificação — Quem você era vs quem você é",
        "why":"Listar comportamentos de 'quem era' vs 'quem virei' convida o leitor a se posicionar em qual degrau ele está. O CTA 'em qual ponto você está?' gera comentários numerados de alta retenção.",
        "signal":"Sinal primário: Comentário",
        "roles":[("R","Mapeador de jornada de evolução"),("O","Comentários de autoposicionamento"),("L","Degraus reais da jornada do nicho"),("E","Progressão clara e sem julgamento"),("S","5–7 degraus específicos")],
        "code":[("Atue como especialista em jornada de desenvolvimento do nicho.","hl"),("","normal"),("Escreva 2 variacoes de Escada de Identificacao.","normal"),("Objetivo: comentarios de autoposicionamento em serie.","normal"),("","normal"),("O tema da evolucao:","normal"),("[Ex: 'a jornada de quem comeca a criar conteudo']","tag"),("O ponto de partida (degrau 1 — mais iniciante):","normal"),("[Comportamento ou crenca de quem esta comecando]","tag"),("O ponto de chegada (degrau 7 — mais avancado):","normal"),("[Comportamento ou mentalidade de quem domina]","tag"),("Os degraus intermediarios:","normal"),("[Liste comportamentos/crencas de cada fase — pode ser rascunho]","tag"),("","normal"),("Tom da escada:","cmd"),("[ ] Sem julgamento — todas as fases sao validas","normal"),("[ ] Com humor — ri de si mesmo em cada fase","normal"),("[ ] Direto — nomeia os erros sem suavizar","normal"),("","normal"),("CTA de autoposicionamento:","cmd"),("'Comenta em qual degrau voce esta agora.'","tag"),("","normal"),("// Proibido usar 'errado' ou 'certo' para os degraus.","cmt"),("// Sao fases, nao falhas — isso elimina resistencia do iniciante.","cmt")]
    },
    {
        "num":"L10","badge":"Múltiplos sinais","color":PURPLE,"bg":PURPLE_LIGHT,
        "title":"O Manifesto de Nicho — Declaração que une a tribo",
        "why":"Um manifesto bem escrito ativa os três sinais ao mesmo tempo. É o formato de maior vida útil no feed — posts de manifesto continuam recebendo engajamento orgânico meses depois.",
        "signal":"Sinais: Comentário + Compartilhamento + Salvamento",
        "roles":[("R","Redator de manifesto de comunidade"),("O","Identidade coletiva em texto"),("L","Crenças reais, não aspiracionais vazias"),("E","Contraste: não somos X, somos Y"),("S","5–8 crenças do grupo")],
        "code":[("Atue como redator de manifesto de comunidade.","hl"),("","normal"),("Escreva 2 variacoes de Manifesto de Nicho.","normal"),("Sinais: comentario + compartilhamento + salvamento simultaneos.","cmd"),("","normal"),("Para quem e esse manifesto (perfil especifico):","normal"),("[Ex: 'criadores que recusam crescer com conteudo vazio']","tag"),("A crenca central que une esse grupo:","normal"),("[O valor principal compartilhado — o que define quem pertence]","tag"),("O que esse grupo NAO e (o contraste):","normal"),("[O oposto — sem atacar pessoas, so comportamentos]","tag"),("","normal"),("5 a 8 crencas especificas desse grupo:","normal"),("[Liste — podem ser rascunhos]","tag"),("[Ex: 'nao postamos por postar — so quando temos algo real']","tag"),("","normal"),("Tom do manifesto:","cmd"),("[ ] Firme e declarativo — estilo constituicao","normal"),("[ ] Caloroso e acolhedor — estilo carta de boas-vindas","normal"),("[ ] Provocador e orgulhoso — estilo grito de guerra","normal"),("","normal"),("Para cada variacao:","cmd"),("-> Manifesto completo com quebras de linha","normal"),("-> A frase-ancora (a linha que vai para print)","normal"),("-> CTA triplo: 1 linha por sinal","normal"),("","normal"),("// Crencas especificas criam tribo. Crencas genericas nao unem ninguem.","cmt")]
    },
]

# ── Build PDF ────────────────────────────────────────────────────────────────

OUTPUT = r"C:\Users\Public\projetos\ferramente excel\prompt_engine_para_criadores.pdf"
AW = 165*mm  # available width inside margins

doc = SimpleDocTemplate(
    OUTPUT,
    pagesize=A4,
    leftMargin=22*mm,
    rightMargin=22*mm,
    topMargin=16*mm,
    bottomMargin=14*mm,
    title="Prompt Engine Para Criadores",
    author="Prompt Engine",
    subject="Pack de Prompts para Criadores de Conteúdo",
)

s = make_styles()
story = []

# ── COVER (blank first page handled by onFirstPage) ──────────────────────────
story.append(PageBreak())

# ── TABLE OF CONTENTS ────────────────────────────────────────────────────────
story.append(Spacer(1, 8*mm))
story.append(Paragraph("SUMÁRIO", ParagraphStyle('toc_h',
    fontName='Helvetica-Bold', fontSize=7, textColor=HINT,
    letterSpacing=1.5, leading=10, spaceAfter=10)))

toc_items = [
    ("Introdução & Como Usar", "Pág 3"),
    ("Seção 01 — 5 Prompts Mestres", "Pág 4"),
    ("Seção 02 — 20 Ganchos de Retenção", "Pág 9"),
    ("Seção 03 — 8 Roteiros VSL para Stories", "Pág 19"),
    ("Seção 04 — 10 Legendas Magnéticas", "Pág 27"),
    ("Regras de Ouro para Legendas", "Pág 33"),
]

for title, pg in toc_items:
    row = [[
        Paragraph(title, ParagraphStyle('ti', fontName='Helvetica', fontSize=10, textColor=MUTED, leading=14)),
        Paragraph(pg, ParagraphStyle('tp', fontName='Helvetica-Bold', fontSize=10, textColor=INK, leading=14, alignment=TA_LEFT))
    ]]
    t = Table(row, colWidths=[AW-20*mm, 20*mm])
    t.setStyle(TableStyle([
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LINEBELOW', (0,0), (-1,0), 0.5, BORDER),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t)

story.append(PageBreak())

# ── INTRO ────────────────────────────────────────────────────────────────────
story.append(Spacer(1, 4*mm))
story.append(Paragraph("INTRODUÇÃO", ParagraphStyle('it',
    fontName='Helvetica-Bold', fontSize=7, textColor=RED,
    letterSpacing=1.5, leading=10, spaceAfter=6)))
story.append(Paragraph("Como usar este guia", ParagraphStyle('ih',
    fontName='Helvetica-Bold', fontSize=18, textColor=INK,
    spaceAfter=6, leading=22)))
story.append(Paragraph(
    "A maioria dos packs de prompts gera conteúdo genérico porque não ensina a IA sobre você. "
    "Antes de pedir qualquer post, Reel ou roteiro, você precisa criar um contexto de marca — "
    "uma base que transforma a IA de assistente genérico em parceiro estratégico.",
    s['body']))
story.append(Spacer(1, 3*mm))
story.append(Paragraph(
    "Cada prompt neste guia usa a técnica ROLES (Role → Objective → Limits → Emphasis → Specifics). "
    "Os campos entre [colchetes] são onde você insere suas informações. "
    "Comece sempre pelo PM 01 antes de usar qualquer outro prompt.",
    s['body']))

story.append(Spacer(1, 4*mm))
story.append(Paragraph("O MÉTODO ROLES", ParagraphStyle('ml',
    fontName='Helvetica-Bold', fontSize=7, textColor=HINT,
    letterSpacing=1.2, leading=10, spaceAfter=6)))

roles_intro = [
    ("R", "Role", "Define quem a IA deve ser para responder seu comando"),
    ("O", "Objective", "O objetivo claro e mensurável da resposta"),
    ("L", "Limits", "O que a IA não deve fazer ou ultrapassar"),
    ("E", "Emphasis", "O ponto mais importante a priorizar"),
    ("S", "Specifics", "Detalhes técnicos que definem o formato da saída"),
]
for letter, name, desc in roles_intro:
    row = [[
        Paragraph(f'<b>&nbsp;&nbsp;{letter}</b>', ParagraphStyle('rl', fontName='Helvetica-Bold', fontSize=10, textColor=WHITE, leading=13)),
        Paragraph(f'<b>{name}</b>', ParagraphStyle('rn', fontName='Helvetica-Bold', fontSize=9, textColor=INK, leading=13, spaceAfter=1)),
        Paragraph(desc, ParagraphStyle('rd', fontName='Helvetica', fontSize=8.5, textColor=MUTED, leading=12)),
    ]]
    t = Table(row, colWidths=[8*mm, 28*mm, AW-36*mm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,0), RED),
        ('BACKGROUND', (1,0), (-1,0), SURFACE2),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (0,0), 0),
        ('LEFTPADDING', (1,0), (1,0), 8),
        ('LEFTPADDING', (2,0), (2,0), 8),
        ('LINEBELOW', (0,0), (-1,0), 0.5, BORDER),
    ]))
    story.append(t)

story.append(Spacer(1, 4*mm))
story.append(LeftBorderBox(
    "IMPORTANTE: Rode sempre o PM 01 (Briefing de Marca) no início de cada sessão. Esse prompt cria o contexto que todos os outros precisam para funcionar. Sem ele, as respostas serão genéricas.",
    border_color=RED, bg_color=RED_LIGHT, text_color=RED_DARK,
    label="Regra de ouro",
    label_color=RED,
    available_width=AW
))
story.append(PageBreak())

# ── SEÇÃO 01: PROMPTS MESTRES ────────────────────────────────────────────────
for item in section_header(
    "5 Prompts Mestres",
    "Execute nessa ordem. Cada prompt constrói sobre o anterior — do contexto de marca ao calendário estratégico completo.",
    RED, "SEÇÃO 01 — PROMPTS MESTRES", s
):
    story.append(item)

for pm in PROMPTS_MESTRES:
    for item in prompt_card(
        pm["num"], pm["badge"], pm["title"], pm["why"],
        pm["roles"], pm["code"], pm["color"], pm["bg"], s, AW
    ):
        story.append(item)

story.append(PageBreak())

# ── SEÇÃO 02: GANCHOS ─────────────────────────────────────────────────────────
for item in section_header(
    "20 Ganchos de Retenção",
    "Para Reels e TikTok. Cada gancho é estruturado para os primeiros 3 segundos — a única janela que decide se a pessoa continua ou vai embora.",
    PURPLE, "SEÇÃO 02 — GANCHOS DE RETENÇÃO", s
):
    story.append(item)

# Tags guide
tags_guide = [
    ("Curiosidade", PURPLE, PURPLE_LIGHT, "G01, G06, G09, G13, G17"),
    ("Contra-narrativa", AMBER, AMBER_LIGHT, "G02, G07, G11, G20"),
    ("Prova Social", GREEN, GREEN_LIGHT, "G03, G10, G14, G18"),
    ("Escassez", RED, RED_LIGHT, "G04, G08, G15"),
    ("Autoridade", BLUE, BLUE_LIGHT, "G05, G12, G16, G19"),
]
tag_rows = [[
    Paragraph(f'<b>&nbsp;&nbsp;{tag}</b>', ParagraphStyle('tg', fontName='Helvetica-Bold', fontSize=8, textColor=fg, leading=11)),
    Paragraph(ganchos, ParagraphStyle('tgn', fontName='Courier', fontSize=8, textColor=MUTED, leading=11)),
] for tag, fg, bg, ganchos in tags_guide]
tag_table = Table(tag_rows, colWidths=[40*mm, AW-40*mm])
tag_table.setStyle(TableStyle([
    ('TOPPADDING', (0,0), (-1,-1), 4),
    ('BOTTOMPADDING', (0,0), (-1,-1), 4),
   ('LEFTPADDING', (1, 0), (1, -1), 10),
    ('LINEBELOW', (0,0), (-1,-2), 0.5, BORDER),
    ('BACKGROUND', (0,0), (-1,-1), SURFACE2),
]))
story.append(tag_table)
story.append(Spacer(1, 6*mm))

for g in GANCHOS:
    for item in prompt_card(
        g["num"], g["badge"], g["title"], g["why"],
        g["roles"], g["code"], g["color"], g["bg"], s, AW
    ):
        story.append(item)

story.append(PageBreak())

# ── SEÇÃO 03: VSL ─────────────────────────────────────────────────────────────
for item in section_header(
    "8 Roteiros VSL para Stories",
    "Video Sales Letters adaptadas ao formato Story. Cada roteiro inclui framework, sequência de frames, gatilho por bloco e prompt ROLES completo.",
    PINK, "SEÇÃO 03 — ROTEIROS VSL PARA STORIES", s
):
    story.append(item)

for vsl in VSL_DATA:
    # Header card
    header_data = [[
        Paragraph(f'<b>{vsl["num"]}</b>', ParagraphStyle('vn', fontName='Helvetica-Bold', fontSize=8, textColor=WHITE)),
        Paragraph(f'<b>{vsl["badge"].upper()}</b>', ParagraphStyle('vb', fontName='Helvetica-Bold', fontSize=7, textColor=vsl["color"], letterSpacing=0.8)),
        Paragraph(f'<b>{vsl["title"]}</b>', ParagraphStyle('vt', fontName='Helvetica-Bold', fontSize=9.5, textColor=INK, leading=13))
    ]]
    # Header card
    header_data = [[
        Paragraph(f'<b>{vsl["num"]}</b>', ParagraphStyle('vn', fontName='Helvetica-Bold', fontSize=8, textColor=WHITE)),
        Paragraph(f'<b>{vsl["badge"].upper()}</b>', ParagraphStyle('vb', fontName='Helvetica-Bold', fontSize=7, textColor=vsl["color"], letterSpacing=0.8)),
        Paragraph(f'<b>{vsl["title"]}</b>', ParagraphStyle('vt', fontName='Helvetica-Bold', fontSize=9.5, textColor=INK, leading=13))
    ]]
    ht = Table(header_data, colWidths=[10*mm, 28*mm, AW-38*mm])
    ht.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,0), vsl["color"]),
        ('BACKGROUND', (1,0), (1,0), vsl["bg"]),
        ('BACKGROUND', (2,0), (2,0), SURFACE2),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        
        # Mude aqui para 3 para descolar o L05
        ('LEFTPADDING', (0,0), (0,0), 3), 
        
        ('LEFTPADDING', (1,0), (1,0), 8),
        ('LEFTPADDING', (2,0), (2,0), 10),
    ]))
    story.append(ht)

    story.append(LeftBorderBox(
        vsl["why"], border_color=vsl["color"], bg_color=vsl["bg"],
        text_color=MUTED, label="Por que funciona", label_color=vsl["color"],
        available_width=AW
    ))

    # Framework label
    story.append(Spacer(1, 2))
    story.append(Paragraph(f'FRAMEWORK: {vsl["framework"]}', ParagraphStyle('fw',
        fontName='Helvetica-Bold', fontSize=7, textColor=vsl["color"],
        letterSpacing=0.8, leading=10, spaceAfter=5)))

   # Frames table
    frame_rows = []
    for mark, step, desc, gate in vsl["frames"]:
        frame_rows.append([
            Paragraph(f'<b>{mark}</b>', ParagraphStyle('fm', fontName='Helvetica-Bold', fontSize=9, textColor=WHITE)),
            Paragraph(f'<b>{step}</b>', ParagraphStyle('fs', fontName='Helvetica-Bold', fontSize=8, textColor=INK, leading=11, spaceAfter=1)),
            Paragraph(desc, ParagraphStyle('fd', fontName='Helvetica', fontSize=7.5, textColor=MUTED, leading=11)),
            Paragraph(gate, ParagraphStyle('fg', fontName='Helvetica-Bold', fontSize=7, textColor=vsl["color"], leading=10)),
        ])
    
    ft = Table(frame_rows, colWidths=[8*mm, 32*mm, AW-68*mm, 28*mm])
    ft.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), vsl["color"]),
        ('BACKGROUND', (1,0), (-1,-1), SURFACE2),
        ('ROWBACKGROUNDS', (1,0), (-1,-1), [SURFACE2, WHITE]),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),

        # Ajuste aqui: 2.5 é o ideal para 8mm de largura
        ('LEFTPADDING', (0, 0), (0, -1), 6),
        ('LEFTPADDING', (1,0), (1,-1), 10),
        ('LINEBELOW', (0,0), (-1,-2), 0.5, BORDER),
    ]))
    story.append(ft)
    story.append(Spacer(1, 4))

    story.append(Paragraph("MÉTODO ROLES", ParagraphStyle('vrl', fontName='Helvetica-Bold', fontSize=6.5, textColor=HINT, letterSpacing=1, leading=9, spaceAfter=3)))
    story.append(roles_table(vsl["roles"], vsl["color"]))
    story.append(Spacer(1, 4))
    story.append(Paragraph("PROMPT COMPLETO", ParagraphStyle('vpl', fontName='Helvetica-Bold', fontSize=6.5, textColor=HINT, letterSpacing=1, leading=9, spaceAfter=3)))
    story.append(prompt_box(vsl["code"]))
    story.append(Spacer(1, 8*mm))

story.append(PageBreak())

# ── SEÇÃO 04: LEGENDAS ───────────────────────────────────────────────────────
for item in section_header(
    "10 Legendas Magnéticas",
    "Cada prompt gera legendas otimizadas para um sinal de engajamento específico. O algoritmo pesa os sinais de forma diferente — este guia cobre os três que mais importam.",
    AMBER, "SEÇÃO 04 — LEGENDAS MAGNÉTICAS", s
):
    story.append(item)

# Signals guide
signals_info = [
    ("Comentário", AMBER, AMBER_LIGHT, "Sinal mais forte — indica debate e tempo de tela. L01, L04, L06, L07, L09, L10"),
    ("Salvamento", BLUE, BLUE_LIGHT, "Indica intenção de retorno — melhor sinal de conteúdo útil. L02, L05, L07, L10"),
    ("Compartilhamento", GREEN, GREEN_LIGHT, "Alcance orgânico exponencial. L03, L04, L08, L10"),
]
for sig, fg, bg, desc in signals_info:
    row = [[
        Paragraph(f'<b>{sig}</b>', ParagraphStyle('sg', fontName='Helvetica-Bold', fontSize=8.5, textColor=fg, leading=12)),
        Paragraph(desc, ParagraphStyle('sd', fontName='Helvetica', fontSize=8, textColor=MUTED, leading=12)),
    ]]
    t = Table(row, colWidths=[38*mm, AW-38*mm])
    t.setStyle(TableStyle([
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('BACKGROUND', (0,0), (-1,-1), bg),
        ('LINEBELOW', (0,0), (-1,-1), 0.5, BORDER),
    ]))
    story.append(t)
story.append(Spacer(1, 6*mm))

for lg in LEGENDAS:
    header_data = [[
        Paragraph(f'<b>{lg["num"]}</b>', ParagraphStyle('ln', fontName='Helvetica-Bold', fontSize=8, textColor=WHITE)),
        Paragraph(f'<b>{lg["badge"].upper()}</b>', ParagraphStyle('lb', fontName='Helvetica-Bold', fontSize=7, textColor=lg["color"], letterSpacing=0.8)),
        Paragraph(f'<b>{lg["title"]}</b>', ParagraphStyle('lt', fontName='Helvetica-Bold', fontSize=9.5, textColor=INK, leading=13))
    ]]
    ht = Table(header_data, colWidths=[10*mm, 30*mm, AW-40*mm])
    ht.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,0), lg["color"]),
        ('BACKGROUND', (1,0), (1,0), lg["bg"]),
        ('BACKGROUND', (2,0), (2,0), SURFACE2),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        
        # AJUSTE AQUI: Mude de 0 para 3 para descolar o texto da borda
        ('LEFTPADDING', (0,0), (0,0), 3), 
        
        ('LEFTPADDING', (1,0), (1,0), 8),
        ('LEFTPADDING', (2,0), (2,0), 10),
    ]))
    story.append(ht)

    story.append(LeftBorderBox(
        lg["why"], border_color=lg["color"], bg_color=lg["bg"],
        text_color=MUTED, label="Por que funciona", label_color=lg["color"],
        available_width=AW
    ))

    story.append(Spacer(1, 2))
    story.append(Paragraph(lg["signal"].upper(), ParagraphStyle('ls',
        fontName='Helvetica-Bold', fontSize=7, textColor=lg["color"],
        letterSpacing=0.8, leading=10, spaceAfter=4)))

    story.append(Paragraph("MÉTODO ROLES", ParagraphStyle('lrl', fontName='Helvetica-Bold', fontSize=6.5, textColor=HINT, letterSpacing=1, leading=9, spaceAfter=3)))
    story.append(roles_table(lg["roles"], lg["color"]))
    story.append(Spacer(1, 4))
    story.append(Paragraph("PROMPT COMPLETO", ParagraphStyle('lpl', fontName='Helvetica-Bold', fontSize=6.5, textColor=HINT, letterSpacing=1, leading=9, spaceAfter=3)))
    story.append(prompt_box(lg["code"]))
    story.append(Spacer(1, 8*mm))

# ── REGRAS DE OURO ────────────────────────────────────────────────────────────
story.append(PageBreak())
story.append(Spacer(1, 4*mm))
story.append(Paragraph("REGRAS DE OURO", ParagraphStyle('rog',
    fontName='Helvetica-Bold', fontSize=7, textColor=AMBER,
    letterSpacing=1.5, leading=10, spaceAfter=6)))
story.append(Paragraph("Para qualquer legenda magnética", ParagraphStyle('roh',
    fontName='Helvetica-Bold', fontSize=18, textColor=INK,
    spaceAfter=8, leading=22)))

gold_rules = [
    ("Primeira linha", "É o único texto visível antes do 'ver mais'. Se não parar o dedo, o restante não existe. Trate como um gancho de Reel — não como introdução."),
    ("Um CTA por legenda", "Exceto os formatos Narrativa de Virada (L07) e Manifesto (L10), que têm CTAs duplo e triplo justificados. Em todos os outros: 1 ação, 1 instrução."),
    ("Quebra de linha estratégica", "Cada virada de assunto = linha em branco. Parágrafos longos matam a leitura no mobile. Máx 3 linhas seguidas antes de uma pausa visual."),
    ("Sinal primário definido", "Antes de escrever, decida: comentário, salvamento ou compartilhamento. Tentar os 3 sem estrutura planejada resulta em nenhum."),
    ("Primeiro comentário seu", "Sempre poste um comentário próprio logo após publicar. Abre o debate, planta o tom e sinaliza ao algoritmo que o post está ativo."),
    ("Teste A/B de CTA", "Mude apenas a última linha entre versões. 'Comenta aqui' vs 'qual a sua resposta?' pode dobrar a taxa de comentários no mesmo conteúdo."),
]

for i, (rule, desc) in enumerate(gold_rules):
    row = [[
        Paragraph(str(i+1).zfill(2), ParagraphStyle('grn', fontName='Helvetica-Bold', fontSize=14, textColor=AMBER, leading=17)),
        Paragraph(f'<b>{rule}</b>', ParagraphStyle('grr', fontName='Helvetica-Bold', fontSize=9.5, textColor=INK, leading=13, spaceAfter=2)),
        Paragraph(desc, ParagraphStyle('grd', fontName='Helvetica', fontSize=8.5, textColor=MUTED, leading=13)),
    ]]
    t = Table(row, colWidths=[12*mm, 38*mm, AW-50*mm])
    t.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 7),
        ('BOTTOMPADDING', (0,0), (-1,-1), 7),
        ('LEFTPADDING', (0,0), (0,0), 6),
        ('BACKGROUND', (0,0), (-1,-1), AMBER_LIGHT if i%2==0 else WHITE),
        ('LINEBELOW', (0,0), (-1,-1), 0.5, BORDER),
    ]))
    story.append(t)

story.append(Spacer(1, 8*mm))

# Final CTA box
final_data = [[
    Paragraph("PRÓXIMOS PASSOS", ParagraphStyle('fps', fontName='Helvetica-Bold', fontSize=7, textColor=RED, letterSpacing=1.2, leading=10, spaceAfter=4)),
],[
    Paragraph("Comece pelo PM 01. Sempre.", ParagraphStyle('fph', fontName='Helvetica-Bold', fontSize=14, textColor=INK, leading=18, spaceAfter=4)),
],[
    Paragraph(
        "Abra uma sessão nova, cole o PM 01 com seus dados de marca e aguarde a confirmação. "
        "A partir daí, qualquer prompt deste guia vai gerar conteúdo calibrado para a sua voz, "
        "o seu público e a sua proposta — não para qualquer criador genérico.",
        ParagraphStyle('fpb', fontName='Helvetica', fontSize=9, textColor=MUTED, leading=14)
    ),
]]
final_t = Table(final_data, colWidths=[AW])
final_t.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,-1), SURFACE2),
    ('TOPPADDING', (0,0), (-1,-1), 10),
    ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ('LEFTPADDING', (0,0), (-1,-1), 14),
    ('RIGHTPADDING', (0,0), (-1,-1), 14),
    ('LINEABOVE', (0,0), (-1,0), 2, RED),
]))
story.append(final_t)

# ── BUILD ─────────────────────────────────────────────────────────────────────
cover = CoverPage()
content = ContentPage()

doc.build(
    story,
    onFirstPage=cover,
    onLaterPages=content,
)

print(f"PDF gerado com sucesso: {OUTPUT}")
