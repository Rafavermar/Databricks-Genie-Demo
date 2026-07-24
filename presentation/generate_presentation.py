"""Generate and validate the Spanish executive presentation."""

from __future__ import annotations

import json
from collections import defaultdict
from io import BytesIO
from itertools import pairwise
from pathlib import Path
from typing import Any

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.presentation import Presentation as PresentationType
from pptx.slide import Slide
from pptx.util import Inches, Pt

from renewable_operations.data_quality import assert_quality, validate_dataset
from renewable_operations.synthetic_data import generate_dataset
from renewable_operations.transformations import build_daily_kpis

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "presentation" / "renewable_operations_demo.pptx"
LOCAL_EVIDENCE = ROOT / "evidence" / "local_presentation_metrics.json"
REMOTE_EVIDENCE = ROOT / "evidence" / "remote_presentation_metrics.json"
DASHBOARD_SCREENSHOT = ROOT / "presentation" / "assets" / "dashboard_executive.png"
GENIE_SCREENSHOT = ROOT / "presentation" / "assets" / "genie_agent.png"

NAVY = RGBColor(0x1B, 0x25, 0x33)
RED = RGBColor(0xFF, 0x36, 0x21)
TEAL = RGBColor(0x00, 0xA9, 0x72)
GRAY = RGBColor(0xF5, 0xF7, 0xF9)
MID_GRAY = RGBColor(0x6B, 0x77, 0x85)
LIGHT_LINE = RGBColor(0xD9, 0xDF, 0xE5)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
ORANGE = RGBColor(0xF3, 0x9C, 0x4A)

SLIDE_WIDTH = Inches(13.333)
SLIDE_HEIGHT = Inches(7.5)
FOOTER = "Datos sintéticos | Demo Databricks Free Edition"


def _textbox(
    slide: Slide,
    text: str,
    x: float,
    y: float,
    width: float,
    height: float,
    *,
    size: float = 18,
    color: RGBColor = NAVY,
    bold: bool = False,
    align: PP_ALIGN = PP_ALIGN.LEFT,
    valign: MSO_ANCHOR = MSO_ANCHOR.MIDDLE,
) -> Any:
    shape = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(width), Inches(height))
    frame = shape.text_frame
    frame.clear()
    frame.word_wrap = True
    frame.vertical_anchor = valign
    paragraph = frame.paragraphs[0]
    paragraph.alignment = align
    run = paragraph.add_run()
    run.text = text
    run.font.name = "Aptos"
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    return shape


def _box(
    slide: Slide,
    x: float,
    y: float,
    width: float,
    height: float,
    *,
    fill: RGBColor = WHITE,
    line: RGBColor = LIGHT_LINE,
    radius: bool = True,
) -> Any:
    shape_type = MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE
    shape = slide.shapes.add_shape(shape_type, Inches(x), Inches(y), Inches(width), Inches(height))
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    shape.line.color.rgb = line
    shape.line.width = Pt(1)
    return shape


def _title(slide: Slide, title: str, subtitle: str | None = None) -> None:
    _textbox(slide, title, 0.65, 0.32, 11.9, 0.55, size=26, bold=True)
    line = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0.65), Inches(0.98), Inches(1.1), Inches(0.06)
    )
    line.fill.solid()
    line.fill.fore_color.rgb = RED
    line.line.fill.background()
    if subtitle:
        _textbox(slide, subtitle, 1.95, 0.86, 10.5, 0.3, size=11, color=MID_GRAY)


def _footer(slide: Slide, number: int) -> None:
    _textbox(slide, FOOTER, 0.65, 7.12, 6.5, 0.2, size=9, color=MID_GRAY)
    _textbox(
        slide, str(number), 12.1, 7.12, 0.55, 0.2, size=9, color=MID_GRAY, align=PP_ALIGN.RIGHT
    )


def _base_slide(presentation: PresentationType, title: str, subtitle: str | None = None) -> Slide:
    slide = presentation.slides.add_slide(presentation.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = WHITE
    _title(slide, title, subtitle)
    _footer(slide, len(presentation.slides))
    return slide


def _notes(slide: Slide, message: str, transition: str, duration: str, demo: str = "N/A") -> None:
    slide.notes_slide.notes_text_frame.text = (
        f"Mensaje principal: {message}\n"
        f"Transición: {transition}\n"
        f"Duración aproximada: {duration}\n"
        f"Demostración: {demo}"
    )


def _card(
    slide: Slide,
    title: str,
    body: str,
    x: float,
    y: float,
    width: float,
    height: float,
    *,
    accent: RGBColor = RED,
) -> None:
    _box(slide, x, y, width, height, fill=GRAY)
    accent_shape = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(0.08), Inches(height)
    )
    accent_shape.fill.solid()
    accent_shape.fill.fore_color.rgb = accent
    accent_shape.line.fill.background()
    _textbox(slide, title, x + 0.22, y + 0.12, width - 0.35, 0.38, size=15, bold=True)
    _textbox(
        slide,
        body,
        x + 0.22,
        y + 0.55,
        width - 0.35,
        height - 0.68,
        size=12,
        color=MID_GRAY,
        valign=MSO_ANCHOR.TOP,
    )


def _real_screenshot(
    slide: Slide,
    path: Path,
    x: float,
    y: float,
    width: float,
    height: float,
    *,
    crop_top_pixels: int = 158,
) -> None:
    """Insert a real browser capture after removing browser chrome."""
    if not path.exists():
        raise FileNotFoundError(f"Required screenshot not found: {path}")

    with Image.open(path) as source:
        if source.width < 800 or source.height < 600:
            raise ValueError(f"Screenshot dimensions are too small: {path}")
        crop_top = min(crop_top_pixels, source.height - 1)
        cropped = source.crop((0, crop_top, source.width, source.height))
        image_stream = BytesIO()
        cropped.save(image_stream, format="PNG")
        image_stream.seek(0)

    _box(slide, x - 0.03, y - 0.03, width + 0.06, height + 0.06, fill=WHITE)
    slide.shapes.add_picture(
        image_stream,
        Inches(x),
        Inches(y),
        width=Inches(width),
        height=Inches(height),
    )


def _metric_summary() -> dict[str, Any]:
    dataset = generate_dataset()
    assert_quality(validate_dataset(dataset))
    kpis = build_daily_kpis(dataset.assets, dataset.generation, dataset.incidents)
    monthly: dict[str, dict[str, float]] = defaultdict(lambda: {"actual": 0.0, "forecast": 0.0})
    for row in kpis:
        key = row["generation_date"].strftime("%Y-%m")
        monthly[key]["actual"] += float(row["actual_generation_mwh"])
        monthly[key]["forecast"] += float(row["forecast_generation_mwh"])
    actual = sum(float(row["actual_generation_mwh"]) for row in kpis)
    forecast = sum(float(row["forecast_generation_mwh"]) for row in kpis)
    local_metrics = {
        "asset_rows": len(dataset.assets),
        "generation_rows": len(dataset.generation),
        "incident_rows": len(dataset.incidents),
        "kpi_rows": len(kpis),
        "total_generation_mwh": actual,
        "total_forecast_mwh": forecast,
        "variance_mwh": actual - forecast,
        "availability_pct": sum(float(row["availability_pct"]) for row in kpis) / len(kpis),
        "avoided_co2_tonnes": sum(float(row["avoided_co2_tonnes"]) for row in kpis),
        "monthly": dict(sorted(monthly.items())),
        "source": "Resultados locales deterministas validados",
    }
    if not REMOTE_EVIDENCE.exists():
        return local_metrics
    remote_metrics = json.loads(REMOTE_EVIDENCE.read_text(encoding="utf-8"))
    for key in ("asset_rows", "generation_rows", "incident_rows", "kpi_rows"):
        if remote_metrics[key] != local_metrics[key]:
            raise ValueError(
                f"Remote evidence mismatch for {key}: {remote_metrics[key]} != {local_metrics[key]}"
            )
    return remote_metrics


def _native_line_chart(slide: Slide, monthly: dict[str, dict[str, float]]) -> None:
    x, y, width, height = 0.95, 3.72, 7.4, 2.45
    axis = slide.shapes.add_connector(
        MSO_CONNECTOR.STRAIGHT,
        Inches(x),
        Inches(y + height),
        Inches(x + width),
        Inches(y + height),
    )
    axis.line.color.rgb = LIGHT_LINE
    values = [series["actual"] for series in monthly.values()] + [
        series["forecast"] for series in monthly.values()
    ]
    minimum, maximum = min(values), max(values)
    months = list(monthly)
    for series_name, color in (("actual", TEAL), ("forecast", NAVY)):
        points: list[tuple[float, float]] = []
        for index, month in enumerate(months):
            px = x + index * width / (len(months) - 1)
            normalized = (monthly[month][series_name] - minimum) / (maximum - minimum)
            py = y + height - normalized * (height - 0.15)
            points.append((px, py))
        for start, end in pairwise(points):
            connector = slide.shapes.add_connector(
                MSO_CONNECTOR.STRAIGHT,
                Inches(start[0]),
                Inches(start[1]),
                Inches(end[0]),
                Inches(end[1]),
            )
            connector.line.color.rgb = color
            connector.line.width = Pt(2)
    _textbox(slide, "Real", 6.45, 3.45, 0.6, 0.2, size=10, color=TEAL, bold=True)
    _textbox(slide, "Prevista", 7.15, 3.45, 0.8, 0.2, size=10, color=NAVY, bold=True)
    _textbox(slide, months[0], x, y + height + 0.08, 0.9, 0.2, size=9, color=MID_GRAY)
    _textbox(
        slide,
        months[-1],
        x + width - 0.9,
        y + height + 0.08,
        0.9,
        0.2,
        size=9,
        color=MID_GRAY,
        align=PP_ALIGN.RIGHT,
    )


def _architecture_slide(presentation: PresentationType) -> None:
    slide = _base_slide(
        presentation,
        "Arquitectura",
        "Un flujo gobernado desde datos sintéticos hasta decisiones",
    )
    labels = [
        ("Datos\nsintéticos", RED),
        ("Tablas\nDelta", NAVY),
        ("Proceso\nserverless", NAVY),
        ("Metric View /\nsemantic view", TEAL),
        ("AI/BI\nDashboard", NAVY),
        ("Genie", ORANGE),
        ("Usuarios\nde negocio", NAVY),
    ]
    start_x = 0.55
    box_width = 1.55
    gap = 0.28
    for index, (label, color) in enumerate(labels):
        x = start_x + index * (box_width + gap)
        _box(slide, x, 2.65, box_width, 1.35, fill=GRAY, line=color)
        _textbox(
            slide,
            label,
            x + 0.08,
            2.82,
            box_width - 0.16,
            0.95,
            size=13,
            bold=True,
            align=PP_ALIGN.CENTER,
        )
        if index < len(labels) - 1:
            arrow = slide.shapes.add_shape(
                MSO_SHAPE.CHEVRON,
                Inches(x + box_width + 0.04),
                Inches(3.1),
                Inches(0.2),
                Inches(0.42),
            )
            arrow.fill.solid()
            arrow.fill.fore_color.rgb = RED
            arrow.line.fill.background()
    _textbox(
        slide,
        "Unity Catalog · definiciones reutilizables · infraestructura como código",
        2.15,
        4.7,
        9.0,
        0.5,
        size=17,
        color=TEAL,
        bold=True,
        align=PP_ALIGN.CENTER,
    )
    _notes(
        slide,
        "La misma definición gobernada alimenta dashboard y conversación.",
        "Pasemos de la arquitectura al modelo de datos.",
        "1:15",
    )


def build_presentation(metrics: dict[str, Any]) -> PresentationType:
    """Build all 12 slides."""
    presentation = Presentation()
    presentation.slide_width = SLIDE_WIDTH
    presentation.slide_height = SLIDE_HEIGHT

    slide = presentation.slides.add_slide(presentation.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = WHITE
    red_block = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(0.22), SLIDE_HEIGHT
    )
    red_block.fill.solid()
    red_block.fill.fore_color.rgb = RED
    red_block.line.fill.background()
    _textbox(slide, "Renewable Operations\nIntelligence", 0.9, 1.35, 8.8, 1.45, size=32, bold=True)
    _textbox(
        slide,
        "De datos operativos a decisiones en lenguaje natural",
        0.93,
        3.0,
        8.5,
        0.55,
        size=19,
        color=MID_GRAY,
    )
    _textbox(
        slide, "Demo Databricks Free Edition", 0.93, 3.78, 5.8, 0.45, size=16, color=RED, bold=True
    )
    _box(slide, 10.05, 1.25, 2.25, 3.5, fill=GRAY, line=LIGHT_LINE)
    for index, (height, color) in enumerate(((1.35, NAVY), (2.05, TEAL), (2.7, RED))):
        bar = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            Inches(10.48 + index * 0.52),
            Inches(4.25 - height),
            Inches(0.3),
            Inches(height),
        )
        bar.fill.solid()
        bar.fill.fore_color.rgb = color
        bar.line.fill.background()
    _footer(slide, 1)
    _notes(
        slide,
        "Presentar la demo y recordar que todos los datos son sintéticos.",
        "Comencemos por el reto que resuelve.",
        "0:45",
    )

    slide = _base_slide(presentation, "Reto de negocio")
    challenges = [
        ("Información fragmentada", "Fuentes operativas aisladas y sin una lectura común."),
        ("KPIs inconsistentes", "La misma métrica puede calcularse de formas distintas."),
        ("Análisis manual", "Demasiado tiempo preparando consultas y reconciliando resultados."),
        (
            "Respuesta lenta",
            "Las desviaciones tardan en convertirse en una conversación accionable.",
        ),
    ]
    for index, (title, body) in enumerate(challenges):
        _card(slide, title, body, 0.75 + (index % 2) * 6.05, 1.5 + (index // 2) * 2.25, 5.75, 1.8)
    _notes(
        slide,
        "El problema no es solo acceder a datos, sino compartir definiciones.",
        "La propuesta combina gobierno, BI y conversación.",
        "1:00",
    )

    slide = _base_slide(presentation, "Propuesta de valor")
    values = [
        ("01", "Plataforma gobernada"),
        ("02", "Semantic layer reutilizable"),
        ("03", "Dashboard ejecutivo"),
        ("04", "Análisis conversacional con Genie"),
        ("05", "Despliegue como código"),
    ]
    for index, (number, label) in enumerate(values):
        y = 1.42 + index * 1.03
        _box(slide, 1.0, y, 11.0, 0.78, fill=GRAY)
        _textbox(slide, number, 1.22, y + 0.08, 0.65, 0.55, size=18, color=RED, bold=True)
        _textbox(slide, label, 2.28, y + 0.08, 8.65, 0.55, size=17, bold=True)
    _notes(
        slide,
        "Un único patrón sirve a operaciones, dirección y equipo de datos.",
        "Veamos cómo se conectan sus componentes.",
        "1:00",
    )

    _architecture_slide(presentation)

    slide = _base_slide(presentation, "Modelo de datos")
    model = [
        ("Assets", "10 instalaciones\ncapacidad · región · tecnología", 0.75, 1.6),
        ("Daily generation", "5.460 observaciones\nreal · prevista · disponibilidad", 6.95, 1.6),
        ("Incidents", "15 incidencias\nseveridad · downtime · estado", 0.75, 4.3),
        ("Daily KPIs", "variance · factor capacidad\ncoste/MWh · CO2 evitado", 6.95, 4.3),
    ]
    for title, body, x, y in model:
        _card(slide, title, body, x, y, 5.6, 1.6, accent=TEAL if title == "Daily KPIs" else RED)
    for start, end in (
        ((6.35, 2.4), (6.9, 2.4)),
        ((9.75, 3.2), (9.75, 4.25)),
        ((6.35, 5.1), (6.9, 5.1)),
    ):
        connector = slide.shapes.add_connector(
            MSO_CONNECTOR.STRAIGHT,
            Inches(start[0]),
            Inches(start[1]),
            Inches(end[0]),
            Inches(end[1]),
        )
        connector.line.color.rgb = MID_GRAY
        connector.line.width = Pt(1.5)
    _notes(
        slide,
        "El KPI diario concentra la semántica necesaria para consumo seguro.",
        "Sobre ese modelo se definen métricas gobernadas.",
        "1:00",
    )

    slide = _base_slide(presentation, "Métricas gobernadas")
    metric_names = [
        "Generación",
        "Previsión",
        "Desviación",
        "Disponibilidad",
        "Factor de capacidad",
        "Coste por MWh",
        "CO2 evitado",
    ]
    for index, name in enumerate(metric_names):
        row, column = divmod(index, 4)
        x, y = 0.7 + column * 3.15, 1.6 + row * 2.15
        _box(slide, x, y, 2.85, 1.55, fill=GRAY)
        _textbox(
            slide, name, x + 0.15, y + 0.22, 2.55, 0.4, size=15, bold=True, align=PP_ALIGN.CENTER
        )
        rule = "Definición única · unidad visible"
        if name == "Desviación":
            rule = "Real - prevista · negativa = desfavorable"
        elif name == "Coste por MWh":
            rule = "EUR / generación real · cero → NULL"
        _textbox(
            slide,
            rule,
            x + 0.18,
            y + 0.72,
            2.5,
            0.48,
            size=10,
            color=MID_GRAY,
            align=PP_ALIGN.CENTER,
        )
    _textbox(
        slide,
        "Calendario natural · periodo siempre explícito",
        3.55,
        6.05,
        6.2,
        0.45,
        size=16,
        color=TEAL,
        bold=True,
        align=PP_ALIGN.CENTER,
    )
    _notes(
        slide,
        "Las reglas evitan que dashboard y Genie respondan con lógicas distintas.",
        "Apliquemos esas métricas a una vista ejecutiva.",
        "1:00",
    )

    slide = _base_slide(
        presentation,
        "Dashboard ejecutivo",
        "Captura real del dashboard AI/BI publicado · paleta validada en tema oscuro",
    )
    _real_screenshot(slide, DASHBOARD_SCREENSHOT, 0.68, 1.25, 11.98, 5.35)
    _textbox(
        slide,
        "Pantalla real · ambas series y barras visibles · filtros globales activos",
        0.82,
        6.65,
        11.65,
        0.24,
        size=10,
        color=MID_GRAY,
        align=PP_ALIGN.CENTER,
    )
    _notes(
        slide,
        "Mostrar el dashboard real corregido y explicar las dos series y los filtros.",
        "La misma capa sirve a una conversación en lenguaje natural.",
        "1:45",
        "Abrir el dashboard real, filtrar el mes adverso y bajar a región.",
    )

    slide = _base_slide(
        presentation,
        "Conversación con Genie",
        "Captura real del agente desplegado · fuente semántica gobernada",
    )
    _real_screenshot(slide, GENIE_SCREENSHOT, 0.68, 1.25, 11.98, 5.35)
    _textbox(
        slide,
        "Fuente autorizada: workspace.renewable_operations_demo.gg_renewable_operations_metrics",
        0.82,
        6.65,
        11.65,
        0.24,
        size=10,
        color=TEAL,
        bold=True,
        align=PP_ALIGN.CENTER,
    )
    _notes(
        slide,
        "Genie acelera la exploración sin abandonar las definiciones acordadas.",
        "Convirtamos la conversación en un guion repetible.",
        "1:15",
        "Ejecutar pregunta inicial y follow-up de instalación e incidencias.",
    )

    slide = _base_slide(presentation, "Guion de demo")
    steps = [
        "Detectar\ndesviación",
        "Analizar\nregión",
        "Bajar a\ninstalación",
        "Relacionar\nincidencias",
        "Preguntar en\nlenguaje natural",
        "Convertir en\nacción",
    ]
    for index, step in enumerate(steps):
        x = 0.55 + index * 2.08
        circle = slide.shapes.add_shape(
            MSO_SHAPE.OVAL, Inches(x + 0.55), Inches(2.3), Inches(0.72), Inches(0.72)
        )
        circle.fill.solid()
        circle.fill.fore_color.rgb = RED if index in {0, 5} else NAVY
        circle.line.fill.background()
        _textbox(
            slide,
            str(index + 1),
            x + 0.67,
            2.44,
            0.48,
            0.38,
            size=15,
            color=WHITE,
            bold=True,
            align=PP_ALIGN.CENTER,
        )
        _textbox(slide, step, x, 3.28, 1.85, 0.85, size=13, bold=True, align=PP_ALIGN.CENTER)
        if index < len(steps) - 1:
            connector = slide.shapes.add_connector(
                MSO_CONNECTOR.STRAIGHT,
                Inches(x + 1.27),
                Inches(2.66),
                Inches(x + 2.63),
                Inches(2.66),
            )
            connector.line.color.rgb = LIGHT_LINE
            connector.line.width = Pt(2)
    _textbox(
        slide,
        "Una historia de 12-15 minutos: del síntoma a una decisión trazable",
        2.25,
        5.25,
        8.8,
        0.55,
        size=17,
        color=TEAL,
        bold=True,
        align=PP_ALIGN.CENTER,
    )
    _notes(
        slide,
        "El guion evita una sucesión de pantallas y mantiene una narrativa de decisión.",
        "Ahora resumamos el impacto esperado.",
        "0:50",
    )

    slide = _base_slide(presentation, "Valor para negocio")
    benefits = [
        "Menor tiempo hasta el insight",
        "Autoservicio guiado",
        "Coherencia métrica",
        "Trazabilidad",
        "Menor carga de consultas repetitivas",
        "Patrón escalable",
    ]
    for index, benefit in enumerate(benefits):
        row, column = divmod(index, 3)
        _card(
            slide,
            benefit,
            "Resultado esperable; sujeto a validación en el contexto corporativo.",
            0.7 + column * 4.15,
            1.5 + row * 2.45,
            3.85,
            1.85,
            accent=TEAL if index in {1, 2, 3} else RED,
        )
    _notes(
        slide,
        "Hablar de resultados esperables, no de ahorros garantizados.",
        "La confianza depende de controles técnicos visibles.",
        "1:00",
    )

    slide = _base_slide(presentation, "Controles y calidad")
    controls = [
        ("Infraestructura como código", "Bundle validable y reproducible"),
        ("Tests", "21 tests · 91,0 % cobertura"),
        ("Data quality", "Claves, rangos, conteos y coherencia"),
        ("Idempotencia", "Segunda ejecución sin duplicados"),
        ("Unity Catalog", "Namespace aislado y comentado"),
        ("Aislamiento Genie", "Solo semantic layer autorizada"),
    ]
    for index, (title, body) in enumerate(controls):
        row, column = divmod(index, 2)
        _card(slide, title, body, 0.75 + column * 6.1, 1.4 + row * 1.7, 5.8, 1.35, accent=TEAL)
    contract_source = "desplegado" if "remoto" in metrics["source"] else "local"
    _textbox(
        slide,
        (
            f"Contrato {contract_source}: {metrics['asset_rows']} assets · "
            f"{metrics['generation_rows']:,} días-activo · "
            f"{metrics['incident_rows']} incidencias"
        ),
        1.25,
        6.35,
        10.8,
        0.4,
        size=14,
        color=NAVY,
        bold=True,
        align=PP_ALIGN.CENTER,
    )
    _notes(
        slide,
        "La demo incluye evidencia técnica, no solo visualizaciones.",
        "Cerramos con el camino de industrialización.",
        "1:00",
        "Mostrar el run y el informe de calidad.",
    )

    slide = _base_slide(presentation, "Próximos pasos")
    next_steps = [
        "Incorporar datos corporativos gobernados",
        "Separar entornos y permisos",
        "Añadir dominios y acuerdos de calidad",
        "Validar seguridad de extremo a extremo",
        "Medir adopción y calidad de respuestas",
        "Industrializar CI/CD",
    ]
    for index, step in enumerate(next_steps):
        y = 1.35 + index * 0.82
        _textbox(slide, f"{index + 1:02d}", 1.0, y, 0.55, 0.45, size=15, color=RED, bold=True)
        _textbox(slide, step, 1.75, y, 8.6, 0.45, size=16, bold=True)
    _box(slide, 10.4, 1.55, 2.15, 3.6, fill=GRAY)
    _textbox(slide, "Estado", 10.75, 1.9, 1.45, 0.4, size=16, bold=True, align=PP_ALIGN.CENTER)
    remote_validated = "remoto" in metrics["source"]
    _textbox(
        slide,
        "Despliegue remoto\nvalidado" if remote_validated else "Validación local\ncompletada",
        10.7,
        2.65,
        1.55,
        0.85,
        size=15,
        color=TEAL,
        bold=True,
        align=PP_ALIGN.CENTER,
    )
    _textbox(
        slide,
        (
            "Dos ejecuciones\nidempotentes"
            if remote_validated
            else "Despliegue remoto\nse refleja en el\ninforme final"
        ),
        10.72,
        3.75,
        1.5,
        1.0,
        size=11,
        color=MID_GRAY,
        align=PP_ALIGN.CENTER,
    )
    _notes(
        slide,
        "La demo prueba el patrón; industrializar requiere gobierno y medición continua.",
        "Abrir preguntas.",
        "0:55",
    )
    return presentation


def validate_presentation(path: Path) -> dict[str, Any]:
    """Validate structure, notes, canvas bounds, and prohibited placeholders."""
    presentation = Presentation(path)
    failures: list[str] = []
    if len(presentation.slides) != 12:
        failures.append(f"expected 12 slides, found {len(presentation.slides)}")
    prohibited = ("TODO", "Iberdrola")
    for slide_number, slide in enumerate(presentation.slides, start=1):
        notes = slide.notes_slide.notes_text_frame.text.strip()
        if not notes:
            failures.append(f"slide {slide_number} has no notes")
        for shape in slide.shapes:
            if shape.left < 0 or shape.top < 0:
                failures.append(f"slide {slide_number} has a negative shape position")
            if shape.left + shape.width > presentation.slide_width:
                failures.append(f"slide {slide_number} shape exceeds width")
            if shape.top + shape.height > presentation.slide_height:
                failures.append(f"slide {slide_number} shape exceeds height")
            if hasattr(shape, "text"):
                for token in prohibited:
                    if token.lower() in shape.text.lower():
                        failures.append(f"slide {slide_number} contains prohibited token {token}")
    if failures:
        raise ValueError("Presentation validation failed: " + "; ".join(failures))
    return {"slides": len(presentation.slides), "notes": 12, "canvas_failures": 0}


def main() -> None:
    """Generate the presentation and local metric evidence."""
    metrics = _metric_summary()
    LOCAL_EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    serializable_metrics = {key: value for key, value in metrics.items() if key != "monthly"}
    LOCAL_EVIDENCE.write_text(
        json.dumps(serializable_metrics, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    presentation = build_presentation(metrics)
    presentation.save(OUTPUT)
    validation = validate_presentation(OUTPUT)
    print(json.dumps({"output": str(OUTPUT), "validation": validation}, indent=2))


if __name__ == "__main__":
    main()
