"""ARS Quant · Simulador y explorador de inversiones (Argentina).

Estructura: 1) configuración visual  2) modelo financiero  3) componentes de UI  4) secciones (tabs).
"""
import html
from dataclasses import dataclass

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st
import yfinance as yf

st.set_page_config(page_title="ARS Quant · Simulador de inversiones", page_icon="📈", layout="wide",
                   initial_sidebar_state="collapsed")

# ============================================================ 1) CONFIGURACIÓN VISUAL
ACCENT, INK, MUTED, LINE = "#0B5FFF", "#0F172A", "#64748B", "#E5E9F0"
POS, NEG, WARN = "#15803D", "#B91C1C", "#B45309"
CELESTE, SOL, OK, BAD = ACCENT, WARN, POS, NEG  # alias usados por el bloque de mercado
PALETA = [ACCENT, INK, "#64748B", "#7DA7FF", "#94A3B8", "#1E3A8A"]
FONT = "DM Sans, sans-serif"

pio.templates["pro"] = go.layout.Template(pio.templates["plotly_white"])
pio.templates["pro"].layout.update(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", colorway=PALETA,
    font=dict(family=FONT, color=INK, size=13), margin=dict(l=8, r=8, t=48, b=8),
    xaxis=dict(gridcolor=LINE, linecolor=LINE, zeroline=False),
    yaxis=dict(gridcolor=LINE, linecolor=LINE, zeroline=False),
    hoverlabel=dict(bgcolor="#fff", bordercolor=LINE, font=dict(family=FONT, color=INK)),
    title=dict(font=dict(size=15)), legend=dict(orientation="h", y=-0.2))

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&display=swap');
html, body, [class*="css"], .stApp { font-family: 'DM Sans', sans-serif; color: #0F172A; }
.stApp { background: #F5F7FA; }
[data-testid="stHeader"] { background: transparent; }
.block-container { max-width: 1120px; padding-top: 1.4rem; }
.brand { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px; }
.brand h1 { margin: 0; font-size: 1.9rem; font-weight: 700; letter-spacing: -.02em; }
.brand h1 span { color: #0B5FFF; }
.sub { color: #0F172A; font-weight: 500; margin: 2px 0 0; }
.desc { color: #64748B; margin: 2px 0 14px; max-width: 680px; }
.pill { font-size: .8rem; padding: 4px 12px; border: 1px solid #E5E9F0; border-radius: 99px; background: #fff; color: #334155; }
.pill i { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 7px; background: #15803D; }
.pill.off i { background: #94A3B8; }
.paso { display: flex; align-items: center; gap: 10px; margin: 2px 0 8px; font-weight: 700; font-size: 1.05rem; }
.paso b { width: 26px; height: 26px; border-radius: 50%; background: #0B5FFF; color: #fff; display: inline-flex;
          align-items: center; justify-content: center; font-size: .85rem; }
.paso small { font-weight: 400; color: #64748B; font-size: .85rem; }
.h2 { font-size: 1.15rem; font-weight: 700; margin: 26px 0 4px; }
.help { color: #64748B; font-size: .88rem; margin-bottom: 8px; }
[data-testid="stVerticalBlockBorderWrapper"] { background: #fff; border-radius: 14px; border-color: #E5E9F0; }
.stTabs [data-baseweb="tab-list"] { gap: 6px; border-bottom: 1px solid #E5E9F0; overflow-x: auto; }
.stTabs [data-baseweb="tab"] { font-weight: 600; padding: 10px 16px; white-space: nowrap; }
.sum { display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; margin: 8px 0; }
.sum div { background: #fff; border: 1px solid #E5E9F0; border-radius: 12px; padding: 12px 14px; }
.sum small { color: #64748B; font-size: .78rem; display: block; }
.sum b { font-size: 1.15rem; font-variant-numeric: tabular-nums; }
.note { color: #334155; background: #EEF3FF; border-radius: 10px; padding: 10px 14px; margin: 8px 0 14px; font-size: .92rem; }
.rank { display: flex; flex-direction: column; gap: 8px; }
.row { background: #fff; border: 1px solid #E5E9F0; border-radius: 12px; padding: 12px 16px; }
.row .top { display: grid; grid-template-columns: 30px minmax(0,2.4fr) 1.1fr 1.2fr 1.2fr; gap: 12px; align-items: center; }
.row .rk { color: #94A3B8; font-weight: 700; }
.row .nm b { display: block; font-size: 1rem; }
.row small, .row .lab { color: #64748B; font-size: .78rem; display: block; }
.row .big { font-size: 1.2rem; font-weight: 700; font-variant-numeric: tabular-nums; }
.row .rd { font-weight: 700; font-variant-numeric: tabular-nums; }
.pos { color: #15803D; } .neg { color: #B91C1C; }
.tag { background: #FEF3C7; color: #92400E; border-radius: 6px; padding: 1px 7px; font-size: .72rem; font-weight: 700; margin-left: 6px; }
details { margin-top: 8px; } summary { cursor: pointer; color: #0B5FFF; font-size: .85rem; font-weight: 600; }
.det { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 8px 18px; margin-top: 8px;
       font-size: .86rem; color: #334155; }
.esc { border: 1px solid #E5E9F0; background: #fff; border-radius: 12px; padding: 12px 14px; }
.esc.sel { border-color: #0B5FFF; box-shadow: 0 0 0 1px #0B5FFF inset; }
.esc b { display: block; } .esc span { color: #64748B; font-size: .86rem; }
.legal { color: #64748B; font-size: .78rem; margin-top: 18px; }
@media (max-width: 720px) {
  .block-container { padding: .8rem .8rem 3rem; }
  .brand h1 { font-size: 1.5rem; }
  .sum { grid-template-columns: repeat(2, 1fr); }
  .row .top { grid-template-columns: 1fr 1fr; }
  .row .rk { display: none; } .row .nm { grid-column: 1 / -1; }
  .stTabs [data-baseweb="tab"] { padding: 8px 10px; font-size: .88rem; }
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ============================================================ helpers de formato
def money(v: float) -> str:
    return "$" + f"{v:,.0f}".replace(",", ".")


def usd(v: float) -> str:
    return "USD " + f"{v:,.0f}".replace(",", ".")


def pct(v: float, signed: bool = True) -> str:
    return (f"{v:+.1%}" if signed else f"{v:.1%}").replace(".", ",")


def dots(r: int) -> str:
    return "●" * r + "○" * (5 - r)


# ------------------------------------------------------------------ MODELO
FIJA, CER, DLINK, USD = "Tasa fija en pesos", "Ajusta por inflación (CER)", "Atado al dólar", "En dólares"


@dataclass
class Escenario:
    inflacion: float
    devaluacion: float


def tem(tea):
    return (1 + tea) ** (1 / 12) - 1


def resultado(tipo, tea, esc, monto, tc0, meses):
    t = tem(tea)
    if tipo == FIJA:
        m = 1 + t
    elif tipo == CER:
        m = (1 + esc.inflacion) * (1 + t)
    else:
        m = (1 + esc.devaluacion) * (1 + t)
    pesos = monto * m ** meses
    poder = pesos / (1 + esc.inflacion) ** meses
    dolares = pesos / (tc0 * (1 + esc.devaluacion) ** meses)
    return pesos, poder, dolares


ESCENARIOS = {
    "Todo sigue parecido": (2.0, 2.0, "Inflación y dólar suben 2% por mes."),
    "Se dispara el dólar": (4.0, 8.0, "El dólar sube 8% por mes y la inflación 4%."),
    "Se calma la economía": (1.0, 0.5, "La inflación baja a 1% por mes y el dólar casi no se mueve."),
    "Lo defino yo": (2.0, 2.0, "Elegís vos los porcentajes mensuales."),
}


# ------------------------------------------------------------------ CATÁLOGO DE OPCIONES
# (nombre, categoría, tipo en el simulador o None, tasa anual de ejemplo %, riesgo 1-5, moneda, plazo,
#  cómo se gana, dónde se compra, ¿rendimiento supuesto/variable?)
B, F, T, E, R, A, D, C, H = ("Bancos y billeteras", "Fondos comunes (FCI)", "Títulos públicos", "Empresas",
                            "Renta variable", "Avanzado", "Dólar y refugios de valor", "Cripto", "Bienes reales")
CATALOGO = [
    ("Caja de ahorro en pesos", B, FIJA, 20.0, 1, "Pesos", "Inmediato", "Interés bajo sobre el saldo", "Tu banco", False),
    ("Plazo fijo tradicional", B, FIJA, 35.0, 1, "Pesos", "30 días o más", "Tasa fija acordada de antemano", "Banco / home banking", False),
    ("Plazo fijo UVA", B, CER, 2.0, 1, "Pesos ajustados por inflación", "90 días o más", "Tu capital sube con la inflación y sumás una tasa extra", "Banco", False),
    ("Plazo fijo en dólares", B, USD, 1.0, 1, "Dólares", "30 días o más", "Interés bajo en dólares", "Banco", False),
    ("Billetera virtual remunerada", B, FIJA, 30.0, 1, "Pesos", "Inmediato", "Rendimiento diario con tasa variable", "Apps de billetera", False),
    ("FCI money market", F, FIJA, 32.0, 1, "Pesos", "Rescate en 24 hs", "Fondo que invierte en plazos fijos y cauciones", "Banco o broker", False),
    ("FCI renta fija en pesos", F, FIJA, 38.0, 2, "Pesos", "24 a 72 hs", "Cartera de letras y bonos en pesos", "Banco o broker", False),
    ("FCI ajustable por inflación (CER)", F, CER, 3.0, 2, "Pesos ajustados por inflación", "24 a 72 hs", "Cartera de bonos que ajustan por inflación", "Banco o broker", False),
    ("FCI dólar linked", F, DLINK, 2.0, 2, "Pesos atados al dólar", "24 a 72 hs", "Cartera de bonos atados al dólar", "Banco o broker", False),
    ("FCI renta fija en dólares", F, USD, 6.0, 2, "Dólares", "24 a 72 hs", "Cartera de bonos y ON en dólares", "Banco o broker", False),
    ("FCI renta variable", F, FIJA, 40.0, 4, "Pesos", "24 a 72 hs", "Cartera de acciones. Puede subir o bajar", "Banco o broker", True),
    ("Letra a tasa fija (LECAP / BONCAP)", T, FIJA, 42.0, 2, "Pesos", "Hasta el vencimiento", "Pagás menos hoy y cobrás más al vencimiento", "Broker (ALyC)", False),
    ("Bono que ajusta por inflación (CER)", T, CER, 6.0, 3, "Pesos ajustados por inflación", "Meses a años", "Capital ajustado por inflación más una tasa extra", "Broker (ALyC)", False),
    ("Bono atado al dólar (dólar linked)", T, DLINK, 4.0, 3, "Pesos atados al dólar", "Meses a años", "Capital que sigue al dólar oficial más una tasa extra", "Broker (ALyC)", False),
    ("Bono en dólares (AL30, GD30 y similares)", T, USD, 10.0, 4, "Dólares", "Años", "Cupones en dólares. El precio varía con el riesgo país", "Broker (ALyC)", False),
    ("Obligación negociable en dólares", E, USD, 8.0, 3, "Dólares", "1 a 10 años", "Prestás a una empresa que te paga intereses", "Broker (ALyC)", False),
    ("Obligación negociable en pesos", E, FIJA, 40.0, 3, "Pesos", "Meses a años", "Prestás a una empresa a tasa en pesos", "Broker (ALyC)", False),
    ("Obligación negociable dólar linked", E, DLINK, 5.0, 3, "Pesos atados al dólar", "Meses a años", "Deuda de empresa que sigue al dólar", "Broker (ALyC)", False),
    ("Cheques de pago diferido y pagarés", E, FIJA, 45.0, 3, "Pesos", "Hasta 360 días", "Financiás a empresas descontando cheques o pagarés", "Broker o plataformas", False),
    ("Caución bursátil (colocadora)", E, FIJA, 32.0, 1, "Pesos", "1 a 30 días", "Prestás a muy corto plazo con garantía", "Broker (ALyC)", False),
    ("Acciones argentinas (panel líder)", R, FIJA, 45.0, 4, "Pesos", "Inmediato en mercado", "Suba de precio más dividendos. Puede bajar", "Broker (ALyC)", True),
    ("CEDEARs", R, USD, 10.0, 4, "Pesos ligados al dólar CCL", "Inmediato en mercado", "Acciones del exterior compradas en pesos", "Broker (ALyC)", True),
    ("ETFs vía CEDEAR (S&P 500, Nasdaq)", R, USD, 9.0, 3, "Pesos ligados al dólar CCL", "Inmediato en mercado", "Canasta de cientos de empresas en un solo papel", "Broker (ALyC)", True),
    ("Acciones y ADRs del exterior", R, USD, 10.0, 4, "Dólares", "Inmediato en mercado", "Acciones extranjeras con cuenta en el exterior", "Broker con cuenta afuera", True),
    ("Opciones", A, None, 0.0, 5, "Pesos o dólares", "Corto plazo", "Contratos apalancados. Podés perder todo lo invertido", "Broker habilitado", True),
    ("Futuros (dólar, índices)", A, None, 0.0, 5, "Pesos", "Hasta el vencimiento", "Apuesta a hacia dónde va un precio. Con apalancamiento", "Broker / Matba-Rofex", True),
    ("Dólar billete", D, USD, 0.0, 2, "Dólares", "Inmediato", "No paga interés. Gana o pierde según el dólar", "Banco / casa de cambio", False),
    ("Dólar MEP / CCL (en cuenta)", D, USD, 0.0, 2, "Dólares", "24 hs", "Comprás dólares con bonos o acciones", "Broker (ALyC)", False),
    ("Oro (CEDEAR o físico)", D, USD, 3.0, 3, "Dólares", "Inmediato", "Sigue el precio internacional del oro", "Broker / joyerías", True),
    ("Bitcoin y criptomonedas", C, USD, 15.0, 5, "Dólares", "Inmediato", "Precio muy volátil, sin garantía", "Exchanges", True),
    ("Stablecoins (USDT, USDC)", C, USD, 0.0, 3, "Dólares", "Inmediato", "Buscan valer 1 dólar. No rinden por sí solas", "Exchanges", False),
    ("Inmuebles para alquilar", H, USD, 4.0, 3, "Dólares (habitualmente)", "Largo plazo", "Renta del alquiler más valorización", "Inmobiliaria", True),
    ("Fideicomisos y crowdfunding inmobiliario", H, USD, 8.0, 4, "Dólares", "1 a 5 años", "Invertís en obras junto a otros inversores", "Plataformas y desarrolladoras", True),
    ("Préstamos entre personas (crowdlending)", H, FIJA, 50.0, 4, "Pesos", "Meses", "Prestás a personas o pymes a tasa alta. Hay riesgo de impago", "Plataformas", True),
]
SIM = {c[0]: c for c in CATALOGO if c[2]}
DEFAULT = ["Plazo fijo tradicional", "Letra a tasa fija (LECAP / BONCAP)", "Bono que ajusta por inflación (CER)",
           "Bono atado al dólar (dólar linked)", "Bono en dólares (AL30, GD30 y similares)", "Dólar billete"]





def total(tipo: str, tea: float, esc: Escenario, monto: float, aporte: float, tc0: float, n: int) -> dict:
    """Capital inicial + aporte mensual (en pesos de hoy, ajustado por inflación cada mes)."""
    f = lambda k: resultado(tipo, tea, esc, 1, tc0, k)[0]
    pesos, inv_n, inv_u = monto * f(n), monto, monto / tc0
    for k in range(1, n + 1):
        ap = aporte * (1 + esc.inflacion) ** k
        pesos += ap * f(n - k)
        inv_n += ap
        inv_u += ap / (tc0 * (1 + esc.devaluacion) ** k)
    poder = pesos / (1 + esc.inflacion) ** n
    dol = pesos / (tc0 * (1 + esc.devaluacion) ** n)
    return {"pesos": pesos, "poder": poder, "usd": dol, "invertido": inv_n, "g_pesos": pesos / inv_n - 1,
            "g_real": poder / (monto + aporte * n) - 1, "g_usd": dol / inv_u - 1}


# ============================================================ 3) COMPONENTES DE UI
PRESETS = {"Escenario base": (2.0, 2.0), "Dólar alto": (4.0, 8.0), "Desinflación": (1.0, 0.5)}
MEDIDAS = {
    "Poder de compra": ("poder", "g_real", "vs. inflación", "Cuánto podrías comprar con ese dinero, descontando la suba de precios."),
    "Pesos": ("pesos", "g_pesos", "en pesos", "Cuántos pesos tendrías al final, sin descontar la inflación."),
    "Dólares": ("usd", "g_usd", "en dólares", "Cuántos dólares equivaldría tu dinero al final."),
}
AJUSTES = {"Todos": None, "Tasa fija en pesos": (FIJA,), "Sigue la inflación": (CER,), "Sigue el dólar": (DLINK, USD)}


def paso(n: int, titulo: str, sub: str = "") -> None:
    st.markdown(f'<div class="paso"><b>{n}</b>{html.escape(titulo)} <small>{html.escape(sub)}</small></div>',
                unsafe_allow_html=True)


def h2(titulo: str, ayuda: str = "") -> None:
    st.markdown(f'<div class="h2">{html.escape(titulo)}</div><div class="help">{html.escape(ayuda)}</div>',
                unsafe_allow_html=True)


def fila_ranking(pos: int, r: dict, medida: str, meses: int, tasa: float) -> str:
    c, (kv, kg, lab, _) = r["c"], MEDIDAS[medida]
    g = r[kg]
    cls, flecha, verbo = ("pos", "▲", "Gana") if g >= 0 else ("neg", "▼", "Pierde")
    final = usd(r["usd"]) if kv == "usd" else money(r[kv])
    tag = '<span class="tag">Supuesto</span>' if c[9] else ""
    det = (f"<div><b>Cómo se gana:</b> {html.escape(c[7])}</div><div><b>Dónde:</b> {html.escape(c[8])}</div>"
           f"<div><b>Tasa anual supuesta:</b> {tasa:.1f}%</div><div><b>En pesos:</b> {pct(r['g_pesos'])}</div>"
           f"<div><b>Contra inflación:</b> {pct(r['g_real'])}</div><div><b>En dólares:</b> {pct(r['g_usd'])}</div>")
    return (f'<div class="row"><div class="top"><div class="rk">{pos}</div>'
            f'<div class="nm"><b>{html.escape(r["n"])}{tag}</b><small>{html.escape(c[1])} · {html.escape(c[5])} · {html.escape(c[6])}</small></div>'
            f'<div><span class="lab">Riesgo</span>{dots(c[4])}</div>'
            f'<div><span class="lab">Capital final</span><span class="big">{final}</span></div>'
            f'<div class="rd {cls}">{flecha} {pct(g)}<span class="lab">{verbo} {lab}</span></div></div>'
            f'<details><summary>Ver detalles</summary><div class="det">{det}</div></details></div>')


@st.cache_data(ttl=900, show_spinner=False)
def mercado_disponible() -> bool:
    try:
        return not yf.Ticker("SPY").history(period="5d", timeout=4).empty
    except Exception:
        return False


@st.cache_data(ttl=600, show_spinner=False)
def bajar(ticker: str, periodo: str) -> pd.DataFrame:
    return yf.Ticker(ticker).history(period=periodo)


# ============================================================ 4) SECCIONES
ok_mercado = mercado_disponible()
estado = ('<span class="pill"><i></i>Datos de mercado disponibles</span>' if ok_mercado
          else '<span class="pill off"><i></i>Datos de mercado no disponibles ahora</span>')
st.markdown(f"""<div class="brand"><h1>ARS <span>Quant</span></h1>{estado}</div>
<p class="sub">Simulador y explorador de inversiones</p>
<p class="desc">Compará más de 30 formas de invertir en Argentina y mirá cuánto podrían rendir en pesos, en dólares y
frente a la inflación, según el escenario que definas.</p>""", unsafe_allow_html=True)

tasas_base = pd.DataFrame({"Opción": list(SIM), "Tipo": [SIM[n][2] for n in SIM],
                           "Tasa anual %": [SIM[n][3] for n in SIM]})
tasas_df = st.session_state.get("tasas_df", tasas_base)
tasa_de = dict(zip(tasas_df["Opción"], tasas_df["Tasa anual %"]))

tab_sim, tab_esc, tab_cmp, tab_meta, tab_mercado = st.tabs(["Simulador", "Escenarios", "Comparar", "Objetivo", "Mercado"])

# ------------------------------------------------------------ SIMULADOR
with tab_sim:
    with st.container(border=True):
        paso(1, "Tu situación", "Cuánto tenés y por cuánto tiempo")
        c1, c2, c3, c4 = st.columns(4)
        monto = c1.number_input("Capital inicial ($)", value=1_000_000, step=50_000, min_value=0)
        aporte = c2.number_input("Aporte mensual ($)", value=0, step=10_000, min_value=0,
                                 help="En pesos de hoy. Se ajusta por inflación cada mes.")
        meses = c3.select_slider("Plazo", options=[1, 3, 6, 9, 12, 18, 24, 36], value=12,
                                 format_func=lambda m: f"{m} {'mes' if m == 1 else 'meses'}")
        tc0 = c4.number_input("Dólar de referencia ($)", value=1200, step=10, min_value=1,
                              help="Dólar MEP de hoy. Sirve para calcular el resultado en dólares.")
    if monto + aporte == 0:
        st.info("Ingresá un capital inicial o un aporte mensual para simular.")
        st.stop()

    with st.container(border=True):
        paso(2, "Tu escenario", "Definí qué pasa con los precios y el dólar")
        st.session_state.setdefault("esc_sel", "Escenario base")
        cols = st.columns(4)
        for col, nombre in zip(cols, list(PRESETS) + ["Personalizado"]):
            sel = st.session_state["esc_sel"] == nombre
            if col.button(nombre, key=f"b_{nombre}", type="primary" if sel else "secondary", use_container_width=True):
                st.session_state["esc_sel"] = nombre
                st.rerun()
            col.caption("Elegís los valores" if nombre == "Personalizado" else
                        f"Inflación {PRESETS[nombre][0]:g}% · Dólar +{PRESETS[nombre][1]:g}% por mes")
        if st.session_state["esc_sel"] == "Personalizado":
            s1, s2 = st.columns(2)
            inf_m = s1.slider("Inflación mensual (%)", 0.0, 15.0, 2.0, 0.1)
            dev_m = s2.slider("Variación mensual del dólar (%)", 0.0, 15.0, 2.0, 0.1)
        else:
            inf_m, dev_m = PRESETS[st.session_state["esc_sel"]]
        esc = Escenario(inf_m / 100, dev_m / 100)
        st.markdown(f'<div class="note">Supuestos: los precios suben <b>{inf_m:g}%</b> por mes y el dólar '
                    f'<b>{dev_m:g}%</b> por mes. En {meses} meses serían <b>{pct((1 + esc.inflacion) ** meses - 1, False)}</b> '
                    f'y <b>{pct((1 + esc.devaluacion) ** meses - 1, False)}</b>.</div>', unsafe_allow_html=True)

    with st.container(border=True):
        paso(3, "¿Cómo querés medir el resultado?")
        medida = st.radio("Medición", list(MEDIDAS), horizontal=True, label_visibility="collapsed")
        st.caption(MEDIDAS[medida][3])

    kv, kg, lab, _ = MEDIDAS[medida]
    todas = [{"n": n, "c": c, **total(c[2], tasa_de[n] / 100, esc, monto, aporte, tc0, meses)}
             for n, c in SIM.items()]

    paso(4, "Resultados")
    fa, fb, fc, fd = st.columns([1.2, 1.2, 1.1, 1])
    cat = fa.selectbox("Categoría", ["Todas"] + sorted({c[1] for c in CATALOGO}))
    ajuste = fb.selectbox("Cómo se ajusta", list(AJUSTES))
    rmax = fc.select_slider("Riesgo máximo", options=[1, 2, 3, 4, 5], value=5, format_func=dots)
    solo_pos = fd.toggle("Solo resultado positivo", value=False)

    filas = [r for r in todas if r["c"][4] <= rmax and (cat == "Todas" or r["c"][1] == cat)
             and (AJUSTES[ajuste] is None or r["c"][2] in AJUSTES[ajuste]) and (not solo_pos or r[kg] > 0)]
    filas.sort(key=lambda r: r[kg], reverse=True)

    if not filas:
        st.info("Ninguna opción cumple estos filtros. Probá con otro riesgo o categoría.")
    else:
        base_r = filas[0]
        aportes_tot = base_r["invertido"] - monto
        finales = [r[kv] for r in filas]
        rango = (usd(min(finales)) + " a " + usd(max(finales))) if kv == "usd" else (money(min(finales)) + " a " + money(max(finales)))
        gan = sum(r["g_real"] > 0 for r in filas)
        st.markdown('<div class="h2">Resumen de tu simulación</div>', unsafe_allow_html=True)
        st.markdown(f"""<div class="sum">
<div><small>Capital inicial</small><b>{money(monto)}</b></div>
<div><small>Aportes</small><b>{money(aportes_tot)}</b></div>
<div><small>Total invertido</small><b>{money(base_r['invertido'])}</b></div>
<div><small>Valor final ({medida.lower()})</small><b style="font-size:.95rem">{rango}</b></div>
<div><small>Ganancia real</small><b>{pct(min(r['g_real'] for r in filas))} a {pct(max(r['g_real'] for r in filas))}</b></div>
</div>
<div class="note">Con estos supuestos, <b>{gan} de {len(filas)}</b> opciones mantienen o aumentan su poder de compra en
{meses} meses. Es una simulación informativa: los resultados dependen de los supuestos y no son una recomendación.</div>""",
                    unsafe_allow_html=True)

        ver_todas = st.toggle(f"Ver las {len(filas)} opciones", value=len(filas) <= 10)
        vis = filas if ver_todas else filas[:10]
        st.markdown('<div class="rank">' + "".join(fila_ranking(i + 1, r, medida, meses, tasa_de[r["n"]])
                                                   for i, r in enumerate(vis)) + "</div>", unsafe_allow_html=True)
        st.caption(f"Ordenadas de mayor a menor {lab}. 'Supuesto' indica que el rendimiento de esa opción es un valor de ejemplo.")

        exp = pd.DataFrame([{"Opción": r["n"], "Categoría": r["c"][1], "Riesgo (1-5)": r["c"][4],
                             "Invertido ($)": round(r["invertido"]), "Pesos finales": round(r["pesos"]),
                             "Poder de compra ($ de hoy)": round(r["poder"]), "Dólares finales": round(r["usd"], 2),
                             "Rend. pesos": r["g_pesos"], "Rend. real": r["g_real"], "Rend. USD": r["g_usd"]}
                            for r in filas])
        st.download_button("Descargar resultados (CSV)", exp.to_csv(index=False).encode("utf-8-sig"),
                           "simulacion.csv", "text/csv")

        with st.expander("Evolución mes a mes (primeras 6 opciones)"):
            x = list(range(1, meses + 1))
            fl = go.Figure()
            for i, r in enumerate(filas[:6]):
                y = [total(r["c"][2], tasa_de[r["n"]] / 100, esc, monto, aporte, tc0, m)["poder"] for m in x]
                fl.add_trace(go.Scatter(x=x, y=y, name=r["n"], line=dict(width=2.5, color=PALETA[i]),
                                        hovertemplate="%{y:$,.0f}<extra>" + r["n"] + "</extra>"))
            fl.add_trace(go.Scatter(x=x, y=[monto + aporte * m for m in x], name="Lo que aportás",
                                    line=dict(width=2, dash="dot", color=MUTED)))
            fl.update_layout(template="pro", height=380, title="Poder de compra en pesos de hoy",
                             xaxis_title="Meses", hovermode="x unified")
            st.plotly_chart(fl, use_container_width=True)
            st.caption("Si una línea está por encima de la punteada, esa opción supera la inflación.")

    with st.expander("Ajustes: cambiar las tasas"):
        st.caption("Las tasas son valores de ejemplo. Cargá las vigentes para resultados más realistas.")
        edit = st.data_editor(tasas_base, hide_index=True, use_container_width=True, height=300,
                              column_config={"Opción": st.column_config.TextColumn(disabled=True),
                                             "Tipo": st.column_config.TextColumn(disabled=True),
                                             "Tasa anual %": st.column_config.NumberColumn(
                                                 min_value=-100.0, max_value=300.0, step=0.5)})
        st.session_state["tasas_df"] = edit
    with st.expander("Glosario"):
        st.markdown("""
- **Poder de compra:** cuánto podés comprar con tu dinero. Si tenés más pesos pero los precios subieron más, comprás menos.
- **Dólar MEP:** dólar financiero que se compra con bonos o acciones. **CEDEAR:** certificado de acciones del exterior que se compra en pesos.
- **CER / UVA:** el capital sube con la inflación y suma una tasa extra. **Atado al dólar:** igual, pero con el dólar oficial.
- **Riesgo:** de 1 (muy bajo) a 5 (muy alto).
""")
    st.markdown('<p class="legal">Los rendimientos son supuestos y las simulaciones no predicen el futuro. Los activos variables '
                '(acciones, cripto, inmuebles) pueden perder valor. No incluye comisiones ni impuestos. Herramienta informativa: '
                'no es asesoramiento financiero. Consultá la oferta vigente en tu broker, BYMA, BCRA y CNV.</p>',
                unsafe_allow_html=True)

# ------------------------------------------------------------ ESCENARIOS
with tab_esc:
    h2("Escenarios", "Cada escenario es una combinación de inflación y dólar. Compará cómo cambia el resultado en cada uno.")
    cols = st.columns(len(PRESETS) + 1)
    for col, (nm, (i_, d_)) in zip(cols, list(PRESETS.items()) + [("Tu escenario", (inf_m, dev_m))]):
        col.markdown(f'<div class="esc {"sel" if nm == "Tu escenario" else ""}"><b>{nm}</b>'
                     f'<span>Inflación: {i_:g}%<br>Dólar: +{d_:g}%<br>por mes</span></div>', unsafe_allow_html=True)
    lista = [Escenario(i_ / 100, d_ / 100) for i_, d_ in PRESETS.values()] + [esc]
    nombres = list(PRESETS) + ["Tu escenario"]
    sel = [n for n in SIM if SIM[n][4] <= 3]
    z = [[total(SIM[n][2], tasa_de[n] / 100, e, 1_000_000, 0, tc0, meses)["g_real"] for e in lista] for n in sel]
    lim = max(0.05, float(np.max(np.abs(z))))
    hm = go.Figure(go.Heatmap(z=z, x=nombres, y=sel, zmin=-lim, zmax=lim, showscale=False, xgap=3, ygap=3,
                              colorscale=[[0, "#F4B4B4"], [0.5, "#FFFFFF"], [1, "#9AD4AE"]],
                              text=[[pct(v) for v in row] for row in z], texttemplate="%{text}",
                              hovertemplate="%{y}<br>%{x}: %{text}<extra></extra>"))
    hm.update_layout(template="pro", height=max(380, 28 * len(sel)), yaxis_autorange="reversed",
                     xaxis=dict(side="top"), title=f"Resultado contra la inflación a {meses} meses")
    st.plotly_chart(hm, use_container_width=True)
    st.markdown('<div class="note"><b>Cómo leerlo:</b> cada fila es una inversión y cada columna un escenario. Verde: mantiene '
                'o aumenta su poder de compra. Rojo: lo pierde. Los signos + y − también indican el resultado. Se muestran '
                'las opciones de riesgo 3 o menos.</div>', unsafe_allow_html=True)

# ------------------------------------------------------------ COMPARAR
with tab_cmp:
    h2("Comparar", "Elegí las inversiones y mirá sus resultados lado a lado, con los datos y el escenario del Simulador.")
    ele = st.multiselect("Elegí hasta 5 inversiones", list(SIM), default=DEFAULT[:3], max_selections=5)
    if len(ele) < 2:
        st.info("Elegí al menos dos inversiones para compararlas.")
    else:
        rows = {n: total(SIM[n][2], tasa_de[n] / 100, esc, monto, aporte, tc0, meses) for n in ele}
        tabla = pd.DataFrame({
            "Inversión": ele, "Riesgo": [dots(SIM[n][4]) for n in ele],
            "Rendimiento en pesos": [pct(rows[n]["g_pesos"]) for n in ele],
            "Rendimiento real": [pct(rows[n]["g_real"]) for n in ele],
            "Rendimiento en dólares": [pct(rows[n]["g_usd"]) for n in ele],
            "Capital final": [money(rows[n]["pesos"]) for n in ele],
            "Dólares finales": [usd(rows[n]["usd"]) for n in ele]})
        st.dataframe(tabla, hide_index=True, use_container_width=True)
        bar = go.Figure()
        for nm, k, col in [("En pesos", "g_pesos", "#94A3B8"), ("Real (vs. inflación)", "g_real", ACCENT),
                           ("En dólares", "g_usd", INK)]:
            bar.add_trace(go.Bar(x=ele, y=[rows[n][k] for n in ele], name=nm, marker_color=col,
                                 text=[pct(rows[n][k]) for n in ele], textposition="outside"))
        bar.update_layout(template="pro", barmode="group", height=400, yaxis_tickformat=".0%",
                          title=f"Rendimiento a {meses} meses")
        st.plotly_chart(bar, use_container_width=True)

# ------------------------------------------------------------ OBJETIVO
with tab_meta:
    h2("Objetivo", "Calculá cuánto necesitarías invertir hoy para llegar a una cantidad en el futuro.")
    g1, g2 = st.columns(2)
    meta = g1.number_input("¿Cuánto querés tener? ($ de hoy)", value=5_000_000, step=250_000, min_value=1000)
    plazo_meta = g2.select_slider("¿En cuánto tiempo?", options=[1, 3, 6, 9, 12, 18, 24, 36], value=12,
                                  format_func=lambda m: f"{m} {'mes' if m == 1 else 'meses'}")
    req = sorted(({"Inversión": n, "Necesitás hoy": meta / resultado(SIM[n][2], tasa_de[n] / 100, esc, 1, tc0, plazo_meta)[1],
                   "Riesgo": dots(SIM[n][4])} for n in SIM if SIM[n][4] <= 3), key=lambda r: r["Necesitás hoy"])
    st.markdown(f'<div class="note">Según tus supuestos (inflación {inf_m:g}% y dólar +{dev_m:g}% por mes), esto es lo que '
                f'necesitarías invertir hoy para poder comprar el equivalente a <b>{money(meta)}</b> en {plazo_meta} meses.</div>',
                unsafe_allow_html=True)
    m1, m2 = st.columns(2)
    m1.metric("Menor monto necesario", money(req[0]["Necesitás hoy"]), req[0]["Inversión"], delta_color="off")
    m2.metric("Mayor monto necesario", money(req[-1]["Necesitás hoy"]), req[-1]["Inversión"], delta_color="off")
    dfm = pd.DataFrame(req)
    dfm["Necesitás hoy"] = dfm["Necesitás hoy"].map(money)
    st.dataframe(dfm, hide_index=True, use_container_width=True)
    st.caption("Un monto menor no significa una opción más conveniente: revisá también el riesgo. Se muestran opciones de riesgo 3 o menos.")

ACTIVOS = {
    "Galicia": "GGAL.BA", "YPF": "YPFD.BA", "Pampa Energía": "PAMP.BA", "Banco Macro": "BMA.BA",
    "TGS": "TGSU2.BA", "Aluar": "ALUA.BA", "Ternium Argentina": "TXAR.BA", "BYMA": "BYMA.BA",
    "Apple (CEDEAR)": "AAPL.BA", "Microsoft (CEDEAR)": "MSFT.BA", "Amazon (CEDEAR)": "AMZN.BA",
    "Mercado Libre (CEDEAR)": "MELI.BA", "Tesla (CEDEAR)": "TSLA.BA", "Coca-Cola (CEDEAR)": "KO.BA",
    "Bono AL30": "AL30.BA", "Bono GD30": "GD30.BA", "Banco BBVA": "BBAR.BA", "Banco Supervielle": "SUPV.BA",
    "Central Puerto": "CEPU.BA", "Edenor": "EDN.BA", "Loma Negra": "LOMA.BA", "Telecom": "TECO2.BA",
    "Cresud": "CRES.BA", "Transener": "TRAN.BA", "Vista Energy": "VIST.BA", "S&P 500 (CEDEAR SPY)": "SPY.BA",
    "Nasdaq 100 (CEDEAR QQQ)": "QQQ.BA", "Nvidia (CEDEAR)": "NVDA.BA", "Google (CEDEAR)": "GOOGL.BA",
    "Meta (CEDEAR)": "META.BA", "Oro (CEDEAR GLD)": "GLD.BA",
}

# ------------------------------------------------------------ MERCADO
with tab_mercado:

    h2("Mercado", "Cotizaciones de acciones, CEDEARs y bonos, con datos de Yahoo Finance (pueden tener demora).")
    if not ok_mercado:
        st.warning("No pudimos conectar con los datos de mercado en este momento. Probá de nuevo en unos minutos.")
    k1, k2, k3 = st.columns([2, 1, 2])
    nombre = k1.selectbox("Activo", list(ACTIVOS))
    periodo = k2.selectbox("Período", ["1mo", "3mo", "6mo", "1y", "2y"], index=3,
                           format_func=lambda p: {"1mo": "1 mes", "3mo": "3 meses", "6mo": "6 meses", "1y": "1 año", "2y": "2 años"}[p])
    otro = k3.text_input("¿No está? Escribí un ticker", placeholder="Ej: BBAR.BA o NVDA").strip().upper()
    ticker, nombre = (otro or ACTIVOS[nombre]), (otro or nombre)
    try:
        with st.spinner("Cargando datos de mercado..."):
            df = bajar(ticker, periodo)
    except Exception:
        df = pd.DataFrame()
    if df.empty:
        st.info("No encontramos datos para este activo. Revisá el ticker o probá con otro.")
    else:
        cierre = df["Close"]
        rets = cierre.pct_change().dropna()
        cambio_dia = cierre.iloc[-1] / cierre.iloc[-2] - 1 if len(cierre) > 1 else 0.0
        a1, a2, a3, a4, a5 = st.columns(5)
        a1.metric("Activo", ticker)
        a2.metric("Precio", money(cierre.iloc[-1]), pct(cambio_dia))
        a3.metric(f"Variación ({periodo})", pct(cierre.iloc[-1] / cierre.iloc[0] - 1), delta_color="off")
        a4.metric("Volatilidad anual", pct(rets.std() * np.sqrt(252), False), help="Cuánto suele moverse el precio. Más alto, más incertidumbre.")
        a5.metric("Máxima caída", pct((cierre / cierre.cummax() - 1).min(), False), help="Mayor pérdida desde un máximo dentro del período.")

        fp = go.Figure()
        fp.add_trace(go.Scatter(x=df.index, y=cierre, name="Precio", line=dict(color=ACCENT, width=2.5),
                                fill="tozeroy", fillcolor="rgba(11,95,255,.07)", hovertemplate="%{y:$,.2f}<extra></extra>"))
        if len(cierre) >= 20:
            fp.add_trace(go.Scatter(x=df.index, y=cierre.rolling(20).mean(), name="Promedio 20 días",
                                    line=dict(color=MUTED, width=1.6, dash="dot")))
        fp.update_layout(template="pro", height=380, title=f"{nombre}: precio de cierre", hovermode="x unified",
                         yaxis=dict(range=[cierre.min() * 0.95, cierre.max() * 1.03], gridcolor=LINE))
        st.plotly_chart(fp, use_container_width=True)

        if len(rets) > 30:
            h2("Rango de precios posibles", "Simulamos 2.000 recorridos a partir de cómo se movió el precio. La banda cubre el 90% de los casos. No es una predicción.")
            mm = st.slider("Horizonte (meses)", 1, 24, 6, key="mc")
            dias = mm * 21
            mu, sig = rets.mean(), rets.std()
            sims = np.exp(np.cumsum(np.random.default_rng(42).normal(mu - sig ** 2 / 2, sig, (2000, dias)), axis=1))
            sims = np.hstack([np.ones((2000, 1)), sims]) * cierre.iloc[-1]
            p5, p50, p95 = np.percentile(sims, [5, 50, 95], axis=0)
            xs = list(range(dias + 1))
            mc = go.Figure()
            mc.add_trace(go.Scatter(x=xs, y=p95, line=dict(width=0), showlegend=False, hoverinfo="skip"))
            mc.add_trace(go.Scatter(x=xs, y=p5, fill="tonexty", fillcolor="rgba(11,95,255,.15)", line=dict(width=0), name="Rango 90%"))
            mc.add_trace(go.Scatter(x=xs, y=p50, line=dict(color=INK, width=2.5), name="Caso central"))
            mc.update_layout(template="pro", height=340, xaxis_title="Días hábiles", yaxis_title="Precio ($)")
            st.plotly_chart(mc, use_container_width=True)
            q1, q2, q3 = st.columns(3)
            for col, lb, v in [(q1, "Escenario bajo (p5)", p5[-1]), (q2, "Caso central", p50[-1]), (q3, "Escenario alto (p95)", p95[-1])]:
                col.metric(lb, money(v), pct(v / cierre.iloc[-1] - 1), delta_color="off")

    h2("Comparador de activos", "Todos parten de 100 para ver cuál creció más en el mismo período.")
    cmp_sel = st.multiselect("Elegí hasta 5 activos", list(ACTIVOS), default=["Galicia", "YPF", "S&P 500 (CEDEAR SPY)"], max_selections=5)
    cmp_per = st.selectbox("Período", ["3mo", "6mo", "1y", "2y"], index=2, key="cp",
                           format_func=lambda p: {"3mo": "3 meses", "6mo": "6 meses", "1y": "1 año", "2y": "2 años"}[p])
    fc, cargados = go.Figure(), 0
    for i, nm in enumerate(cmp_sel):
        try:
            ser = bajar(ACTIVOS[nm], cmp_per)["Close"]
            if not ser.empty:
                fc.add_trace(go.Scatter(x=ser.index, y=ser / ser.iloc[0] * 100, name=nm, line=dict(width=2.2, color=PALETA[i])))
                cargados += 1
        except Exception:
            pass
    if cargados:
        fc.add_hline(y=100, line_dash="dot", line_color=MUTED)
        fc.update_layout(template="pro", height=360, hovermode="x unified", yaxis_title="Base 100")
        st.plotly_chart(fc, use_container_width=True)
    elif cmp_sel:
        st.info("No hay datos disponibles para los activos elegidos en este momento.")

st.markdown('<p class="legal">ARS Quant es una herramienta informativa y de simulación. No constituye asesoramiento financiero '
            'ni una recomendación de inversión. Los datos pueden tener demora o errores.</p>', unsafe_allow_html=True)





            
