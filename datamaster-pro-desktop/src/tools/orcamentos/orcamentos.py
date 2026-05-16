"""
Orçamentos - Gera orçamentos em PDF em massa a partir de Excel/CSV
"""
import io
import logging
import os
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

try:
    from pypdf import PdfReader, PdfWriter
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False

try:
    import qrcode
    QRCODE_AVAILABLE = True
except ImportError:
    QRCODE_AVAILABLE = False

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Mapeamento centralizado de colunas (único lugar para manter)
# ---------------------------------------------------------------------------
COLUMN_MAP: Dict[str, List[str]] = {
    "id":        ["id", "numero", "cod", "codigo", "n_orcamento", "n_pedido", "order_id", "sequencial"],
    "nome":      ["nome", "cliente", "nome_cliente", "razao_social", "entidade", "destinatario", "buyer", "pagador", "contato"],
    "data":      ["data", "emissao", "data_pedido", "created_at", "dt_emissao"],
    "cpf_cnpj":  ["cpf", "cnpj", "cpf_cnpj", "documento", "identificacao", "id_fiscal", "tax_id", "registro", "inscricao"],
    "endereco":  ["endereco", "endereço", "rua", "logradouro", "localidade", "bairro", "cidade", "address", "entrega"],
    "telefone":  ["telefone", "fone", "whatsapp", "celular", "phone", "tel", "cel", "wpp", "mobile", "contact_no"],
    "email":     ["email", "email_envio", "mail", "correio", "contato_email", "user_email"],
    "validade":  ["validade", "valido", "vencimento", "valid", "expira", "periodo"],
    "pagamento": ["pagamento", "forma", "condicoes", "parcelas", "payment", "terms"],
    "item":      ["item", "servico", "produto", "descricao", "assinatura", "licenca", "plano", "pacote",
                  "descr", "detalhe", "especificacao", "sku", "artigo", "task", "atividade", "material", "referencia", "ref"],
    "qtd":       ["qtd", "quantidade", "qtde", "qtdade", "unidades", "unids", "un", "vol", "volume", "count", "amount", "qty"],
    "preco":     ["preco", "valor", "price", "valor_unitario", "preco_unitario", "vlr", "unit", "vlr_unit", "p_unit", "custo", "fee", "monto", "valor_item"],
    "desconto":  ["desc", "desconto", "abatimento", "discount", "off", "vlr_desc"],
    "categoria": ["categoria", "grupo", "tipo", "category", "group"],
    "prazo":     ["prazo", "entrega", "lead_time", "dias_entrega", "dias"],
    "obs_item":  ["obs", "nota", "comentario", "informacao_adicional", "observacao"],
}


def _find_col(columns: List[str], row: pd.Series, key: str):
    """Localiza valor na row usando a lista de sinônimos do COLUMN_MAP."""
    keywords = COLUMN_MAP.get(key, [key])
    col_lower_map = {str(c).lower(): c for c in columns}
    for kw in keywords:
        for col_l, col_orig in col_lower_map.items():
            if kw in col_l:
                return row.get(col_orig)
    return None


def _is_valid(v) -> bool:
    if v is None:
        return False
    return str(v).strip().lower() not in ("", "nan", "none", "null")


# ---------------------------------------------------------------------------
# QR Code PIX — payload EMV com CRC-16/CCITT correto
# ---------------------------------------------------------------------------
def _crc16_ccitt(data: str) -> str:
    crc = 0xFFFF
    for ch in data.encode("utf-8"):
        crc ^= ch << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) if crc & 0x8000 else (crc << 1)
            crc &= 0xFFFF
    return format(crc, "04X")


def gerar_qrcode_pix(
    pix_key: str,
    amount: float = 0,
    name: str = "RECEBEDOR",
    city: str = "BRASIL",
) -> Optional[bytes]:
    """Retorna bytes PNG de um QR Code PIX com payload EMV/BR Code válido."""
    if not QRCODE_AVAILABLE:
        log.warning("qrcode não instalado. Execute: pip install qrcode[pil]")
        return None

    def tlv(tag: str, value: str) -> str:
        return f"{tag}{len(value):02d}{value}"

    pix_key = pix_key.strip()
    name = (name[:25] if name else "RECEBEDOR").upper()
    city = (city[:15] if city else "BRASIL").upper()

    merchant_account = tlv("00", "BR.GOV.BCB.PIX") + tlv("01", pix_key)
    payload = (
        tlv("00", "01")
        + tlv("26", merchant_account)
        + tlv("52", "0000")
        + tlv("53", "986")
        + (tlv("54", f"{amount:.2f}") if amount > 0 else "")
        + tlv("58", "BR")
        + tlv("59", name)
        + tlv("60", city)
        + tlv("62", tlv("05", "***"))
        + "6304"
    )
    payload += _crc16_ccitt(payload)

    try:
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(payload)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#000000", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except Exception as exc:
        log.error("Erro ao gerar QR Code PIX: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Watermark
# ---------------------------------------------------------------------------
def _add_watermark(pdf_path: str, text: str = "DataMaster Pro") -> bool:
    if not PYPDF_AVAILABLE:
        return False
    try:
        from reportlab.pdfgen import canvas as rl_canvas

        reader = PdfReader(pdf_path)
        writer = PdfWriter()

        for page in reader.pages:
            w = float(page.mediabox.width)
            h = float(page.mediabox.height)
            pkt = io.BytesIO()
            c = rl_canvas.Canvas(pkt, pagesize=(w, h))
            c.setFont("Helvetica-Bold", 38)
            c.setFillColorRGB(0.75, 0.75, 0.75, alpha=0.25)
            c.saveState()
            c.translate(w / 2, h / 2)
            c.rotate(45)
            c.drawCentredString(0, 0, text)
            c.restoreState()
            c.save()
            pkt.seek(0)
            wm_page = PdfReader(pkt).pages[0]
            page.merge_page(wm_page)
            writer.add_page(page)

        with open(pdf_path, "wb") as f:
            writer.write(f)
        return True
    except Exception as exc:
        log.error("Erro ao adicionar watermark: %s", exc)
        return False


# ---------------------------------------------------------------------------
# Gerador de PDF de orçamento
# ---------------------------------------------------------------------------
class GeradorOrcamentoPDF:
    """Renderiza um orçamento em PDF usando ReportLab Platypus."""

    MARGIN = 10 * mm

    def __init__(self, filename: str, config: Dict):
        self.filename = filename
        self.config = config

        cor_hex = self.config.get("pdf_cor", "#d48214") or "#d48214"
        self.cor_primaria   = colors.HexColor(cor_hex)
        self.cinza_escuro   = colors.HexColor("#1e293b")
        self.cinza_medio    = colors.HexColor("#64748b")
        self.cinza_claro    = colors.HexColor("#f1f5f9")
        self.cinza_borda    = colors.HexColor("#e2e8f0")
        self.branco         = colors.white

        self.styles = getSampleStyleSheet()
        self._definir_estilos()

    @staticmethod
    def _safe(v, fallback: str = "") -> str:
        if v is None or (isinstance(v, float) and v != v):
            return fallback
        s = str(v).strip()
        return s if s.lower() not in ("nan", "none", "null", "") else fallback

    @staticmethod
    def _fmt(value: float) -> str:
        return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def _definir_estilos(self):
        add = self.styles.add
        P = self.cor_primaria
        DE = self.cinza_escuro
        DM = self.cinza_medio

        add(ParagraphStyle("Titulo_Doc",      fontSize=22, fontName="Helvetica-Bold",  textColor=DE, leading=26))
        add(ParagraphStyle("Empresa_Nome",    fontSize=16, fontName="Helvetica-Bold",  textColor=P,  leading=18))
        add(ParagraphStyle("Empresa_Info",    fontSize=8.5,fontName="Helvetica",       textColor=DM, leading=12))
        add(ParagraphStyle("Secao",           fontSize=7.5,fontName="Helvetica-Bold",  textColor=P,  leading=10, spaceBefore=0, spaceAfter=3))
        add(ParagraphStyle("Num_Doc",         fontSize=9,  fontName="Helvetica",       textColor=DM, alignment=TA_RIGHT, leading=13))
        add(ParagraphStyle("Th",              fontSize=8.5,fontName="Helvetica-Bold",  textColor=colors.white, alignment=TA_LEFT))
        add(ParagraphStyle("Th_C",            fontSize=8.5,fontName="Helvetica-Bold",  textColor=colors.white, alignment=TA_CENTER))
        add(ParagraphStyle("Th_R",            fontSize=8.5,fontName="Helvetica-Bold",  textColor=colors.white, alignment=TA_RIGHT))
        add(ParagraphStyle("Td",              fontSize=8.5,fontName="Helvetica",       textColor=DE, leading=12))
        add(ParagraphStyle("Td_C",            fontSize=8.5,fontName="Helvetica",       textColor=DE, alignment=TA_CENTER, leading=12))
        add(ParagraphStyle("Td_R",            fontSize=8.5,fontName="Helvetica",       textColor=DE, alignment=TA_RIGHT,  leading=12))
        add(ParagraphStyle("Total_Label",     fontSize=9.5,fontName="Helvetica-Bold",  textColor=DE, alignment=TA_RIGHT))
        add(ParagraphStyle("Total_Valor",     fontSize=15, fontName="Helvetica-Bold",  textColor=P,  alignment=TA_RIGHT))
        add(ParagraphStyle("Obs",             fontSize=8,  fontName="Helvetica",       textColor=DM, leading=11))
        add(ParagraphStyle("QR_Caption",      fontSize=6.5,fontName="Helvetica",       textColor=DM, alignment=TA_CENTER))

    # ------------------------------------------------------------------ blocos

    def _bloco_header(self, story: list):
        cfg = self.config
        has_logo = cfg.get("logo_path") and os.path.exists(cfg["logo_path"])

        if has_logo:
            img = Image(cfg["logo_path"])
            aspect = img.drawHeight / img.drawWidth
            img.drawWidth = 32 * mm
            img.drawHeight = 32 * mm * aspect
            col_esq = img
        else:
            col_esq = Paragraph(
                self._safe(cfg.get("empresa_nome"), "Empresa").upper(),
                self.styles["Empresa_Nome"],
            )

        info = []
        if has_logo and cfg.get("empresa_nome"):
            info.append(Paragraph(self._safe(cfg["empresa_nome"]).upper(), self.styles["Empresa_Nome"]))
        if cfg.get("empresa_endereco"):
            info.append(Paragraph(self._safe(cfg["empresa_endereco"]), self.styles["Empresa_Info"]))

        contatos = []
        if cfg.get("empresa_telefone"):
            contatos.append(f"Tel: {self._safe(cfg['empresa_telefone'])}")
        if cfg.get("empresa_email"):
            contatos.append(f"E-mail: {self._safe(cfg['empresa_email'])}")
        if contatos:
            info.append(Paragraph("  |  ".join(contatos), self.styles["Empresa_Info"]))

        tbl = Table([[col_esq, info]], colWidths=[36 * mm, 144 * mm])
        tbl.setStyle(TableStyle([
            ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING",  (1, 0), (1, 0),   5 * mm),
        ]))
        story.append(tbl)
        story.append(Spacer(1, 4 * mm))

        # Linha separadora colorida
        sep = Table([[""]], colWidths=[180 * mm], rowHeights=[1.8])
        sep.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), self.cor_primaria)]))
        story.append(sep)
        story.append(Spacer(1, 0 * mm))

    def _bloco_titulo(self, story: list, dados_cliente: Dict):
        titulo = self._safe(self.config.get("pdf_titulo"), "ORÇAMENTO").upper()
        num    = self._safe(dados_cliente.get("ID"), "001")
        data   = self._safe(dados_cliente.get("Data"), datetime.now().strftime("%d/%m/%Y"))

        tbl = Table(
            [[
                Paragraph(titulo, self.styles["Titulo_Doc"]),
                Paragraph(f"N° <b>{num}</b><br/>Emissão: {data}", self.styles["Num_Doc"]),
            ]],
            colWidths=[120 * mm, 60 * mm],
        )
        tbl.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), self.cinza_claro),
            ("TOPPADDING",    (0, 0), (-1, -1), 5 * mm),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5 * mm),
            ("LEFTPADDING",   (0, 0), (0, 0),   5 * mm),
            ("RIGHTPADDING",  (-1, 0),(-1, 0),  5 * mm),
            ("LINEBELOW",     (0, 0), (-1, -1), 2.5, self.cor_primaria),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(tbl)
        story.append(Spacer(1, 6 * mm))

    def _bloco_destinatario(self, story: list, dados_cliente: Dict):
        s = self._safe
        campos = [
            Paragraph("DESTINATÁRIO", self.styles["Secao"]),
            Paragraph(
                f"<b>{s(dados_cliente.get('Nome'), 'N/A')}</b>",
                ParagraphStyle("_cn", fontSize=11, fontName="Helvetica-Bold",
                               textColor=self.cinza_escuro, leading=14),
            ),
        ]
        detalhes = []
        for chave, label in [("CPF_CNPJ", "Doc"), ("Telefone", "Tel"), ("Email", "E-mail"), ("Endereco", "End")]:
            if dados_cliente.get(chave):
                detalhes.append(f"{label}: {s(dados_cliente[chave])}")
        for d in detalhes:
            campos.append(Paragraph(d, self.styles["Empresa_Info"]))

        tbl = Table([[campos]], colWidths=[180 * mm])
        tbl.setStyle(TableStyle([
            ("TOPPADDING",    (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ]))
        story.append(tbl)
        story.append(Spacer(1, 7 * mm))

    def _bloco_itens(self, story: list, itens: List[Dict]) -> float:
        """Monta tabela de itens e retorna total geral."""
        header = [
            Paragraph("DESCRIÇÃO / SERVIÇO", self.styles["Th"]),
            Paragraph("QTD",                 self.styles["Th_C"]),
            Paragraph("UNITÁRIO",            self.styles["Th_C"]),
            Paragraph("TOTAL",               self.styles["Th_R"]),
        ]
        rows = [header]
        total_geral = 0.0

        for item in itens:
            sub = item.get("subtotal", 0.0)
            total_geral += sub
            rows.append([
                Paragraph(self._safe(item.get("desc")), self.styles["Td"]),
                Paragraph(str(item.get("qtd", 1)),       self.styles["Td_C"]),
                Paragraph(self._fmt(item.get("preco", 0)),self.styles["Td_C"]),
                Paragraph(self._fmt(sub),                 self.styles["Td_R"]),
            ])

        tbl = Table(rows, colWidths=[97 * mm, 18 * mm, 33 * mm, 32 * mm], repeatRows=1)

        style = [
            ("BACKGROUND",    (0, 0), (-1, 0),  self.cor_primaria),
            ("TOPPADDING",    (0, 0), (-1, 0),  5),
            ("BOTTOMPADDING", (0, 0), (-1, 0),  5),
            ("LEFTPADDING",   (0, 0), (0, 0),   5 * mm),
            ("RIGHTPADDING",  (-1, 0),(-1, 0),  4 * mm),
            ("TOPPADDING",    (0, 1), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
            ("LEFTPADDING",   (0, 1), (0, -1),  5 * mm),
            ("RIGHTPADDING",  (-1, 1),(-1, -1), 4 * mm),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("LINEBELOW",     (0, 0), (-1, -1), 0.4, self.cinza_borda),
        ]
        # zebra
        for i in range(1, len(rows)):
            if i % 2 == 0:
                style.append(("BACKGROUND", (0, i), (-1, i), self.cinza_claro))

        tbl.setStyle(TableStyle(style))
        story.append(tbl)
        return total_geral

    def _bloco_totais(self, story: list, total_geral: float, dados_cliente: Dict):
        story.append(Spacer(1, 3 * mm))

        tbl_total = Table(
            [["",
              Paragraph("TOTAL DO ORÇAMENTO", self.styles["Total_Label"]),
              Paragraph(self._fmt(total_geral),  self.styles["Total_Valor"])]],
            colWidths=[95 * mm, 52 * mm, 33 * mm],
        )
        tbl_total.setStyle(TableStyle([
            ("TOPPADDING",    (0, 0), (-1, -1), 4 * mm),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4 * mm),
            ("LINEABOVE",     (1, 0), (-1, 0),  1, self.cinza_borda),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("RIGHTPADDING",  (-1, 0),(-1, 0),  4 * mm),
        ]))
        story.append(tbl_total)

        # Validade / pagamento como badges simples
        badges = []
        if dados_cliente.get("Validade"):
            badges.append(f"Validade: <b>{self._safe(dados_cliente['Validade'])}</b>")
        if dados_cliente.get("Pagamento"):
            badges.append(f"Pagamento: <b>{self._safe(dados_cliente['Pagamento'])}</b>")

        if badges:
            story.append(Spacer(1, 5 * mm))
            for b in badges:
                story.append(Paragraph(
                    b,
                    ParagraphStyle("_badge", fontSize=8.5, fontName="Helvetica",
                                   textColor=self.cinza_escuro, leading=11,
                                   backColor=self.cinza_claro,
                                   borderPadding=(3, 6, 3, 6), spaceAfter=3),
                ))

    def _bloco_obs(self, story: list):

        obs = self._safe(self.config.get("observacoes_default"))

        if not obs:

            return

        story.append(Spacer(1, 10 * mm))

        story.append(Paragraph("NOTAS E CONDIÇÕES", self.styles["Secao"]))

        story.append(HRFlowable(width="25%", thickness=0.8, color=self.cor_primaria, hAlign="LEFT"))

        story.append(Spacer(1, 2 * mm))

        for linha in obs.split('\n'):
            if linha.strip():
                story.append(Paragraph(linha.strip(), self.styles["Obs"]))
                story.append(Spacer(1, 3))



    def _bloco_pagamento(self, story: list):

        pix     = self._safe(self.config.get("pix"))

        banco   = self._safe(self.config.get("banco"))

        agencia = self._safe(self.config.get("agencia"))

        conta   = self._safe(self.config.get("conta"))



        if not (pix or banco):

            return



        story.append(Spacer(1, 10 * mm))

        story.append(Paragraph("DADOS PARA PAGAMENTO", self.styles["Secao"]))

        story.append(HRFlowable(width="25%", thickness=0.8, color=self.cor_primaria, hAlign="LEFT"))

        story.append(Spacer(1, 3 * mm))



        linhas = []

        if pix:

            linhas.append(f"<b>Chave PIX:</b> {pix}")

        if banco:

            linhas.append(f"<b>Banco:</b> {banco}")

        partes_bancarias = []

        if agencia:

            partes_bancarias.append(f"<b>Agência:</b> {agencia}")

        if conta:

            partes_bancarias.append(f"<b>Conta:</b> {conta}")

        if partes_bancarias:

            linhas.append("  |  ".join(partes_bancarias))



        col_dados = Paragraph(

            "<br/>".join(linhas),

            ParagraphStyle("_banco", fontSize=9, fontName="Helvetica",

                           textColor=self.cinza_escuro, leading=15),

        )



        qr_cell = []

        if pix:

            qr_bytes = gerar_qrcode_pix(

                pix_key=pix,

                amount=0,

                name=self._safe(self.config.get("empresa_nome"), "Empresa"),

            )

            if qr_bytes:

                qr_img = Image(io.BytesIO(qr_bytes), width=27 * mm, height=27 * mm)

                qr_cell = [qr_img, Paragraph("Escaneie para pagar", self.styles["QR_Caption"])]



        if qr_cell:

            row_data  = [[col_dados, qr_cell]]

            col_widths = [133 * mm, 37 * mm]

        else:

            row_data  = [[col_dados]]

            col_widths = [170 * mm]



        tbl = Table(row_data, colWidths=col_widths)

        tbl.setStyle(TableStyle([

            ("BACKGROUND",    (0, 0), (-1, -1), self.cinza_claro),

            ("LINESTART",     (0, 0), (0, -1),  2.5, self.cor_primaria),

            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),

            ("TOPPADDING",    (0, 0), (-1, -1), 8),

            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),

            ("LEFTPADDING",   (0, 0), (0, 0),   8),

            ("ALIGN",         (1, 0), (1, 0),   "CENTER"),

        ]))

        story.append(tbl)

    # ------------------------------------------------------------------ gerar

    def gerar(self, dados_cliente: Dict, itens: List[Dict]):
        doc = SimpleDocTemplate(
            self.filename,
            pagesize=A4,
            rightMargin=self.MARGIN,
            leftMargin=self.MARGIN,
            topMargin=self.MARGIN,
            bottomMargin=self.MARGIN,
        )
        story: list = []

        self._bloco_header(story)
        self._bloco_titulo(story, dados_cliente)
        self._bloco_destinatario(story, dados_cliente)
        total = self._bloco_itens(story, itens)
        self._bloco_totais(story, total, dados_cliente)
        self._bloco_obs(story)
        self._bloco_pagamento(story)

        doc.build(story)
        log.info("PDF gerado: %s", self.filename)


# ---------------------------------------------------------------------------
# Classe principal: Orcamentos
# ---------------------------------------------------------------------------
class Orcamentos:
    """Orquestra a geração de orçamentos em massa a partir de Excel/CSV."""

    SUPPORTED_FORMATS = {".xlsx", ".xls", ".csv"}

    # ---------------------------------------------------------------- helpers

    @staticmethod
    def _ler_dataframe(data_file: str) -> pd.DataFrame:
        ext = Path(data_file).suffix.lower()
        if ext in (".xlsx", ".xls"):
            return pd.read_excel(data_file)
        return pd.read_csv(data_file, encoding="utf-8")

    @staticmethod
    def _match_column(field_name: str, columns) -> Optional[str]:
        """Correspondência fuzzy entre campo de formulário PDF e coluna do DataFrame."""
        fl = field_name.lower().replace("_", "").replace(" ", "")
        for col in columns:
            cl = str(col).lower().replace("_", "").replace(" ", "")
            if fl in cl or cl in fl:
                return col
        return None

    @staticmethod
    def _chave_cliente(row: pd.Series, columns: List[str]) -> str:
        parts = [
            _find_col(columns, row, "nome"),
            _find_col(columns, row, "cpf_cnpj"),
            _find_col(columns, row, "email"),
            _find_col(columns, row, "endereco"),
        ]
        if not any(_is_valid(p) for p in parts):
            return ""
        return "|".join(str(p) if _is_valid(p) else "" for p in parts)

    @staticmethod
    def _to_float(v) -> float:
        if v is None:
            return 0.0
        s = re.sub(r"[R$\s]", "", str(v)).strip()
        m = re.search(r"[\d.,]+", s)
        if not m:
            return 0.0
        try:
            return float(m.group().replace(",", "."))
        except ValueError:
            return 0.0

    @classmethod
    def _to_int(cls, v) -> int:
        f = cls._to_float(v)
        return max(1, int(f)) if f > 0 else 1

    # ---------------------------------------------------------------- generate (template PDF)

    def generate(
        self,
        template_pdf: str,
        data_file: str,
        output_dir: str,
        prefix: str = "orcamento",
        watermark: bool = True,
        watermark_text: str = "DataMaster Pro",
    ) -> Dict:
        """Preenche formulário PDF com dados de cada linha do arquivo."""
        if not PYPDF_AVAILABLE:
            return {"success": False, "error": "pypdf não instalado. Execute: pip install pypdf"}
        if not os.path.exists(template_pdf):
            return {"success": False, "error": "Template PDF não encontrado"}
        if not os.path.exists(data_file):
            return {"success": False, "error": "Arquivo de dados não encontrado"}

        try:
            df = self._ler_dataframe(data_file)
            os.makedirs(output_dir, exist_ok=True)
            reader = PdfReader(template_pdf)
            fields = reader.get_form_text_fields() or {}

            generated, errors = 0, []
            for idx, row in df.iterrows():
                try:
                    writer = PdfWriter()
                    for page in reader.pages:
                        writer.add_page(page)

                    data_dict = {
                        field_name: str(row[col])
                        for field_name in fields
                        if (col := self._match_column(field_name, df.columns))
                        and col in row
                        and pd.notna(row[col])
                    }
                    if data_dict:
                        writer.update_page_form_field_values(writer.pages[0], data_dict)

                    out = os.path.join(output_dir, f"{prefix}_{idx + 1}.pdf")
                    with open(out, "wb") as f:
                        writer.write(f)
                    if watermark:
                        _add_watermark(out, watermark_text)
                    generated += 1
                except Exception as exc:
                    errors.append(f"Linha {idx + 1}: {exc}")

            return {
                "success": True,
                "total_rows": len(df),
                "generated": generated,
                "output_dir": output_dir,
                "errors": errors or None,
            }
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def generate_single(self, template_pdf: str, data: Dict, output_path: str) -> Dict:
        """Preenche um único PDF de formulário."""
        if not PYPDF_AVAILABLE:
            return {"success": False, "error": "pypdf não instalado."}
        try:
            reader = PdfReader(template_pdf)
            writer = PdfWriter()
            for page in reader.pages:
                writer.add_page(page)
            writer.update_page_form_field_values(writer.pages[0], data)
            with open(output_path, "wb") as f:
                writer.write(f)
            return {"success": True, "output_path": output_path}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def get_template_fields(self, template_pdf: str) -> List[str]:
        if not PYPDF_AVAILABLE:
            return []
        try:
            reader = PdfReader(template_pdf)
            fields = reader.get_form_text_fields()
            return list(fields.keys()) if fields else []
        except Exception:
            return []

    # ---------------------------------------------------------------- generate_from_excel

    def generate_from_excel(
        self,
        data_file: str,
        output_dir: str,
        watermark: bool = True,
        watermark_text: str = "DataMaster Pro",
        config: Dict = None,
    ) -> Dict:
        """Lê planilha, agrupa por cliente e gera um PDF por cliente."""
        if not os.path.exists(data_file):
            return {"success": False, "error": "Arquivo de dados não encontrado"}

        config = config or {}
        limite = config.get("limite_docs")

        try:
            df = self._ler_dataframe(data_file)
            log.info("Arquivo lido: %d linhas | colunas: %s", len(df), list(df.columns))
            os.makedirs(output_dir, exist_ok=True)
            columns = list(df.columns)

            clientes: Dict[str, Dict] = defaultdict(lambda: {"dados": None, "itens": []})

            for idx, row in df.iterrows():
                if row.isna().all():
                    continue

                chave = self._chave_cliente(row, columns) or f"cliente_{idx}"
                if clientes[chave]["dados"] is None:
                    clientes[chave]["dados"] = row

                item_desc = _find_col(columns, row, "item")
                if not _is_valid(item_desc):
                    continue

                qtd   = self._to_int(_find_col(columns, row, "qtd"))
                preco = self._to_float(_find_col(columns, row, "preco"))
                sub   = qtd * preco

                desc_raw = _find_col(columns, row, "desconto")
                if _is_valid(desc_raw):
                    d = self._to_float(desc_raw)
                    sub = sub * (1 - d / 100) if d < 100 else sub - d

                clientes[chave]["itens"].append({
                    "desc":      str(item_desc),
                    "qtd":       qtd,
                    "preco":     preco,
                    "subtotal":  sub,
                    "categoria": str(_find_col(columns, row, "categoria")) if _is_valid(_find_col(columns, row, "categoria")) else None,
                    "prazo":     str(_find_col(columns, row, "prazo"))     if _is_valid(_find_col(columns, row, "prazo"))     else None,
                    "obs":       str(_find_col(columns, row, "obs_item"))  if _is_valid(_find_col(columns, row, "obs_item"))  else None,
                })

            log.info("Clientes agrupados: %d", len(clientes))

            empresa_cfg = {
                "nome":       config.get("empresa_nome", ""),
                "endereco":   config.get("empresa_endereco", ""),
                "telefone":   config.get("empresa_telefone", ""),
                "email":      config.get("empresa_email", ""),
                "pdf_titulo": config.get("pdf_titulo", "ORÇAMENTO"),
                "pdf_cor":    config.get("pdf_cor", "#1a56db"),
                "pix":        config.get("pix_chave", ""),
                "banco":      config.get("banco", ""),
                "agencia":    config.get("agencia", ""),
                "conta":      config.get("conta", ""),
            }
            logo_path   = config.get("logo_path", "")
            obs_default = config.get("observacoes_default", "")

            generated, errors, doc_count = 0, [], 0

            for chave, dados in clientes.items():
                if limite and doc_count >= limite:
                    log.info("Limite de %d documentos atingido.", limite)
                    break
                if not dados["itens"]:
                    continue
                try:
                    self._gerar_pdf_cliente(
                        chave, dados, empresa_cfg, logo_path, obs_default,
                        output_dir, watermark, watermark_text,
                    )
                    generated += 1
                    doc_count += 1
                except Exception as exc:
                    errors.append(f"Cliente {chave}: {exc}")
                    log.error("Erro ao gerar PDF para %s: %s", chave, exc)

            return {
                "success":    True,
                "total_rows": len(df),
                "generated":  generated,
                "output_dir": output_dir,
                "errors":     errors or None,
            }

        except Exception as exc:
            log.error("Falha geral: %s", exc)
            return {"success": False, "error": str(exc)}

    def _gerar_pdf_cliente(
        self,
        chave: str,
        dados: Dict,
        empresa_cfg: Dict,
        logo_path: str,
        obs_default: str,
        output_dir: str,
        watermark: bool,
        watermark_text: str,
    ):
        row     = dados["dados"]
        columns = list(row.index)

        def sv(key: str, fallback: str = "") -> str:
            v = _find_col(columns, row, key)
            return str(v).strip() if _is_valid(v) else fallback

        dados_cliente = {
            "ID":        sv("id", "001"),
            "Nome":      sv("nome", "Cliente"),
            "Data":      sv("data", datetime.now().strftime("%d/%m/%Y")),
            "CPF_CNPJ":  sv("cpf_cnpj"),
            "Endereco":  sv("endereco"),
            "Telefone":  sv("telefone"),
            "Email":     sv("email"),
            "Validade":  sv("validade"),
            "Pagamento": sv("pagamento"),
        }

        pdf_cfg = {
            "logo_path":           logo_path,
            "empresa_nome":        empresa_cfg.get("nome", ""),
            "empresa_endereco":    empresa_cfg.get("endereco", ""),
            "empresa_telefone":    empresa_cfg.get("telefone", ""),
            "empresa_email":       empresa_cfg.get("email", ""),
            "observacoes_default": obs_default,
            "pdf_titulo":          empresa_cfg.get("pdf_titulo", "ORÇAMENTO"),
            "pdf_cor":             empresa_cfg.get("pdf_cor", "#1a56db"),
            "pix":                 empresa_cfg.get("pix", ""),
            "banco":               empresa_cfg.get("banco", ""),
            "agencia":             empresa_cfg.get("agencia", ""),
            "conta":               empresa_cfg.get("conta", ""),
        }

        nome_safe     = re.sub(r"[^\w\s-]", "", dados_cliente["Nome"]).strip()
        empresa_safe  = re.sub(r"[^\w\s-]", "", empresa_cfg.get("nome", "Orcamento")).strip()
        base          = f"{empresa_safe}_{nome_safe}"
        out_path      = os.path.join(output_dir, f"{base}.pdf")
        counter       = 1
        while os.path.exists(out_path):
            out_path = os.path.join(output_dir, f"{base}_{counter}.pdf")
            counter += 1

        GeradorOrcamentoPDF(out_path, pdf_cfg).gerar(dados_cliente, dados["itens"])

        if watermark:
            _add_watermark(out_path, watermark_text)

        log.info("Gerado: %s", out_path)
