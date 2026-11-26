"""
Dashboard: Delitos sexuales reportados en Colombia (Policía Nacional)
Ejecutar localmente:  streamlit run app.py
"""
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ----------------------------------------------------------------------------
# Configuración general
# ----------------------------------------------------------------------------
st.set_page_config(page_title="Delitos sexuales en Colombia", page_icon="📊", layout="wide")

ARCHIVO = Path(__file__).parent / "data" / "delitos_sexuales_analisis.csv"
FUENTE = ("Fuente: Policía Nacional de Colombia, «Reporte Delitos sexuales Policía Nacional» "
          "(fpe5-yrmw), Datos Abiertos Colombia. Muestra estratificada de 10.000 registros.")

# Paleta (validada para daltonismo): azul, naranja, aguamarina + gris para "sin dato"
AZUL, NARANJA, AGUA, GRIS = "#257de0", "#f47230", "#00b894", "#9c9c9c"
TEXTO_SEC = "#666666"
COLOR_GENERO = {"FEMENINO": AZUL, "MASCULINO": NARANJA, "NO REPORTADO": GRIS}
COLOR_EDAD = {"MENORES": AZUL, "ADOLESCENTES": NARANJA, "ADULTOS": AGUA}
ORDEN_EDAD = ["MENORES", "ADOLESCENTES", "ADULTOS"]
ESCALA_SECUENCIAL = ["#cce3fd", "#84b9f3", "#338ced", "#1b64be", "#0e3d7e"]

st.markdown("""
<style>
  .block-container {padding-top: 1.6rem; padding-bottom: 2rem;}
  div[data-testid="stMetric"] {background: #f6f8fb; border: 1px solid #e3e8ef;
      border-radius: 10px; padding: 12px 16px;}
  div[data-testid="stMetricLabel"] p {font-size: 0.85rem; color: #555;}
  .seccion {font-size: 1.25rem; font-weight: 700; color: #1F3864; margin: 1.2rem 0 0.2rem 0;
      border-bottom: 2px solid #e3e8ef; padding-bottom: 4px;}
  .nota {font-size: 0.8rem; color: #666;}
</style>
""", unsafe_allow_html=True)


# ----------------------------------------------------------------------------
# Datos
# ----------------------------------------------------------------------------
@st.cache_data
def preparar(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["fecha_hecho"] = pd.to_datetime(df["fecha_hecho"], errors="coerce")
    df = df.dropna(subset=["fecha_hecho"])
    df["anio"] = df["fecha_hecho"].dt.year
    df["anio_mes"] = df["fecha_hecho"].dt.to_period("M")
    if "delito_corto" not in df.columns:
        df["delito_corto"] = df["delito"].str.replace(
            r"^ART[ÍI]CULO\s+\d+\s*[A-Z]?\.\s*", "", regex=True).str.strip()
    if "cantidad" not in df.columns:
        df["cantidad"] = 1
    for col in ["departamento", "genero", "grupo_etario", "armas_medios", "delito_corto"]:
        df[col] = df[col].fillna("NO REPORTADO").astype(str)
    return df


@st.cache_data
def cargar_archivo(ruta: str) -> pd.DataFrame:
    return preparar(pd.read_csv(ruta, dtype={"cod_depto": str, "cod_mpio": str, "codigo_dane": str}))


if ARCHIVO.exists():
    df = cargar_archivo(str(ARCHIVO))
else:
    st.warning("No se encontró `data/delitos_sexuales_analisis.csv`. Sube el archivo generado "
               "por el notebook de limpieza para ver el dashboard.")
    subido = st.file_uploader("Archivo delitos_sexuales_analisis.csv", type="csv")
    if subido is None:
        st.stop()
    df = preparar(pd.read_csv(subido, dtype={"cod_depto": str, "cod_mpio": str, "codigo_dane": str}))

MESES_TODOS = pd.period_range(df["anio_mes"].min(), df["anio_mes"].max(), freq="M")


def estilo(fig, alto=360, leyenda=True):
    fig.update_layout(
        template="plotly_white", height=alto, margin=dict(l=10, r=10, t=40, b=10),
        font=dict(family="Arial", size=13, color="#191919"),
        title=dict(font=dict(size=15), x=0, xanchor="left"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title_text=""),
        showlegend=leyenda, hoverlabel=dict(font_size=13), separators=",.",
    )
    fig.update_xaxes(gridcolor="#eeeeee", zeroline=False)
    fig.update_yaxes(gridcolor="#eeeeee", zeroline=False)
    return fig


def fechas(fig):
    fig.update_xaxes(tickformat="%m/%Y")
    return fig


def barras(fig):
    fig.update_traces(marker_line_width=0, marker_cornerradius=4)
    return fig


def fmt(n):
    return f"{n:,.0f}".replace(",", ".")


def pct(x, dec=1):
    return f"{x:.{dec}f}".replace(".", ",") + " %"


def num(x, dec=1):
    return f"{x:.{dec}f}".replace(".", ",")


# ----------------------------------------------------------------------------
# Encabezado
# ----------------------------------------------------------------------------
st.title("Delitos sexuales reportados en Colombia")
st.markdown(
    f"**Pregunta de investigación:** ¿cómo se distribuyen los casos reportados según el grupo etario, "
    f"el género, el tipo de delito y el medio empleado, y cómo cambian entre departamentos y a lo largo "
    f"del tiempo?  \n<span class='nota'>Periodo analizado: {MESES_TODOS[0].strftime('%m/%Y')} a "
    f"{MESES_TODOS[-1].strftime('%m/%Y')}. Unidad: número de víctimas (cada registro es una víctima). "
    f"{FUENTE}</span>", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# Filtros
# ----------------------------------------------------------------------------
f1, f2, f3, f4, f5 = st.columns([1, 2, 1.3, 1.5, 2])
anios = sorted(df["anio"].unique())
sel_anio = f1.multiselect("Año", anios, placeholder="Todos")
sel_depto = f2.multiselect("Departamento", sorted(df["departamento"].unique()), placeholder="Todos")
sel_genero = f3.multiselect("Género", sorted(df["genero"].unique()), placeholder="Todos")
sel_edad = f4.multiselect("Grupo etario", [g for g in ORDEN_EDAD if g in df["grupo_etario"].unique()],
                          placeholder="Todos")
sel_delito = f5.multiselect("Tipo de delito", sorted(df["delito_corto"].unique()), placeholder="Todos")

d = df
for col, sel in [("anio", sel_anio), ("departamento", sel_depto), ("genero", sel_genero),
                 ("grupo_etario", sel_edad), ("delito_corto", sel_delito)]:
    if sel:
        d = d[d[col].isin(sel)]

if d.empty:
    st.info("No hay registros con la combinación de filtros seleccionada.")
    st.stop()

total = d["cantidad"].sum()
meses_sel = [m for m in MESES_TODOS if not sel_anio or m.year in sel_anio]
serie = (d.groupby("anio_mes")["cantidad"].sum().reindex(meses_sel, fill_value=0)
         .rename("victimas").reset_index().rename(columns={"index": "anio_mes"}))
serie["mes"] = serie["anio_mes"].dt.to_timestamp()
serie["anio"] = serie["anio_mes"].dt.year

# ----------------------------------------------------------------------------
# Indicadores clave
# ----------------------------------------------------------------------------
pct_muj = d.loc[d["genero"] == "FEMENINO", "cantidad"].sum() / total * 100
pct_nna = d.loc[d["grupo_etario"].isin(["MENORES", "ADOLESCENTES"]), "cantidad"].sum() / total * 100
por_depto = d.groupby("departamento")["cantidad"].sum().sort_values(ascending=False)
top_delito = d.groupby("delito_corto")["cantidad"].sum().sort_values(ascending=False)

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Víctimas en la muestra", fmt(total))
k2.metric("Mujeres", pct(pct_muj))
k3.metric("Menores de 18 años", pct(pct_nna), help="Grupos MENORES y ADOLESCENTES.")
k4.metric("Promedio mensual", f"{serie['victimas'].mean():.0f} víctimas",
          help=f"Mediana: {serie['victimas'].median():.0f} víctimas por mes.")
try:
    k5.metric("Departamento con más casos", por_depto.index[0].title(),
              f"{pct(por_depto.iloc[0] / total * 100)} del total", delta_color="off", delta_arrow="off")
except TypeError:  # versiones de Streamlit sin delta_arrow
    k5.metric("Departamento con más casos", por_depto.index[0].title(),
              help=f"{pct(por_depto.iloc[0] / total * 100)} del total de víctimas.")

# ----------------------------------------------------------------------------
# 1. Perfil de la víctima
# ----------------------------------------------------------------------------
st.markdown("<div class='seccion'>1. Perfil de la víctima</div>", unsafe_allow_html=True)
c1, c2 = st.columns([1.4, 1])

edad_gen = (d.groupby(["grupo_etario", "genero"])["cantidad"].sum().reset_index(name="victimas"))
edad_gen["pct"] = edad_gen["victimas"] / total * 100
fig = px.bar(edad_gen, x="grupo_etario", y="victimas", color="genero", barmode="group",
             category_orders={"grupo_etario": ORDEN_EDAD,
                              "genero": ["FEMENINO", "MASCULINO", "NO REPORTADO"]},
             color_discrete_map=COLOR_GENERO, custom_data=["genero", "pct"],
             title="Víctimas por grupo etario y género",
             labels={"grupo_etario": "Grupo etario", "victimas": "Víctimas (número)"})
fig.update_traces(hovertemplate="<b>%{x}</b> · %{customdata[0]}<br>%{y:,} víctimas "
                                "(%{customdata[1]:.1f} % del total)<extra></extra>")
fig.update_layout(bargap=0.25, bargroupgap=0.08)
c1.plotly_chart(estilo(barras(fig)), width="stretch")

edad = (d.groupby("grupo_etario")["cantidad"].sum().reindex(ORDEN_EDAD).dropna()
        .reset_index(name="victimas"))
edad["pct"] = edad["victimas"] / total * 100
fig = px.bar(edad, x="pct", y="grupo_etario", orientation="h", text=edad["pct"].map(pct),
             color="grupo_etario", color_discrete_map=COLOR_EDAD,
             category_orders={"grupo_etario": ORDEN_EDAD[::-1]}, custom_data=["victimas"],
             title="Distribución por grupo etario (%)",
             labels={"pct": "% de las víctimas", "grupo_etario": ""})
fig.update_traces(textposition="outside", cliponaxis=False,
                  hovertemplate="<b>%{y}</b><br>%{customdata[0]:,} víctimas (%{x:.1f} %)<extra></extra>")
fig.update_xaxes(range=[0, edad["pct"].max() * 1.25])
c2.plotly_chart(estilo(barras(fig), leyenda=False), width="stretch")

# ----------------------------------------------------------------------------
# 2. Tipo de delito y medio empleado
# ----------------------------------------------------------------------------
st.markdown("<div class='seccion'>2. Tipo de delito y medio empleado</div>", unsafe_allow_html=True)
c1, c2 = st.columns([1.4, 1])

top10 = top_delito.head(10).reset_index(name="victimas")
top10["pct"] = top10["victimas"] / total * 100
top10["etiqueta"] = top10["delito_corto"].str.slice(0, 60).str.capitalize()
fig = px.bar(top10, x="victimas", y="etiqueta", orientation="h", custom_data=["pct", "delito_corto"],
             text=top10["pct"].map(pct), title="Diez tipos de delito con más víctimas",
             labels={"victimas": "Víctimas (número)", "etiqueta": ""})
fig.update_traces(marker_color=AZUL, textposition="outside", cliponaxis=False,
                  hovertemplate="<b>%{customdata[1]}</b><br>%{x:,} víctimas (%{customdata[0]:.1f} %)<extra></extra>")
fig.update_yaxes(categoryorder="total ascending")
fig.update_xaxes(range=[0, top10["victimas"].max() * 1.18])
c1.plotly_chart(estilo(barras(fig), alto=420, leyenda=False), width="stretch")

medio = d.groupby("armas_medios")["cantidad"].sum().sort_values(ascending=False).reset_index(name="victimas")
medio["pct"] = medio["victimas"] / total * 100
medio["etiqueta"] = medio["armas_medios"].str.slice(0, 35).str.capitalize()
medio["color"] = np.where(medio["armas_medios"] == "NO REPORTADO", GRIS, AZUL)
fig = go.Figure(go.Bar(x=medio["victimas"], y=medio["etiqueta"], orientation="h",
                       marker_color=medio["color"], text=medio["pct"].map(pct),
                       textposition="outside", cliponaxis=False, customdata=medio[["pct"]],
                       hovertemplate="<b>%{y}</b><br>%{x:,} víctimas (%{customdata[0]:.1f} %)<extra></extra>"))
fig.update_layout(title="Víctimas por medio empleado", xaxis_title="Víctimas (número)")
fig.update_yaxes(categoryorder="total ascending")
fig.update_xaxes(range=[0, medio["victimas"].max() * 1.22])
c2.plotly_chart(estilo(barras(fig), alto=420, leyenda=False), width="stretch")
pct_nr = medio.loc[medio["armas_medios"] == "NO REPORTADO", "pct"].sum()
if pct_nr > 0:
    c2.caption(f"En gris: registros sin medio reportado ({pct(pct_nr)}). "
               "Interpretar esta variable con cautela.")

# ----------------------------------------------------------------------------
# 3. Territorio
# ----------------------------------------------------------------------------
st.markdown("<div class='seccion'>3. Distribución territorial</div>", unsafe_allow_html=True)
c1, c2 = st.columns([1, 1])

top15 = por_depto.head(15).reset_index(name="victimas")
top15["pct"] = top15["victimas"] / total * 100
fig = px.bar(top15, x="victimas", y="departamento", orientation="h", custom_data=["pct"],
             text=top15["pct"].map(pct), title="Departamentos con más víctimas (top 15)",
             labels={"victimas": "Víctimas (número)", "departamento": ""})
fig.update_traces(marker_color=AZUL, textposition="outside", cliponaxis=False,
                  hovertemplate="<b>%{y}</b><br>%{x:,} víctimas (%{customdata[0]:.1f} %)<extra></extra>")
fig.update_yaxes(categoryorder="total ascending")
fig.update_xaxes(range=[0, top15["victimas"].max() * 1.18])
c1.plotly_chart(estilo(barras(fig), alto=480, leyenda=False), width="stretch")

top10_dep = por_depto.head(10).index
calor = (d[d["departamento"].isin(top10_dep)]
         .pivot_table(index="departamento", columns="anio", values="cantidad", aggfunc="sum", fill_value=0)
         .reindex(top10_dep))
fig = px.imshow(calor, text_auto=True, aspect="auto", color_continuous_scale=ESCALA_SECUENCIAL,
                labels=dict(x="Año", y="", color="Víctimas"),
                title="Víctimas por departamento y año (top 10)")
fig.update_xaxes(type="category", side="bottom")
fig.update_traces(xgap=2, ygap=2,
                  hovertemplate="<b>%{y}</b> · %{x}<br>%{z:,} víctimas<extra></extra>")
c2.plotly_chart(estilo(fig, alto=480, leyenda=False), width="stretch")
c2.caption("Los totales dependen del tamaño de la población de cada departamento; "
           "no son tasas por habitante.")

# ----------------------------------------------------------------------------
# 4. Evolución en el tiempo
# ----------------------------------------------------------------------------
st.markdown("<div class='seccion'>4. Evolución en el tiempo</div>", unsafe_allow_html=True)
desglose = st.radio("Ver la serie mensual:", ["Total", "Por grupo etario", "Por género"],
                    horizontal=True, label_visibility="collapsed")
c1, c2 = st.columns([1.6, 1])

if desglose == "Total":
    fig = px.line(serie, x="mes", y="victimas", markers=True, title="Víctimas por mes",
                  labels={"mes": "Mes", "victimas": "Víctimas por mes"})
    fig.update_traces(line=dict(color=AZUL, width=2), marker=dict(size=8),
                      hovertemplate="%{x|%m/%Y}<br>%{y:,} víctimas<extra></extra>")
    fig.add_hline(y=serie["victimas"].mean(), line_dash="dot", line_color=TEXTO_SEC,
                  annotation_text=f"Promedio: {serie['victimas'].mean():.0f}",
                  annotation_position="bottom right", annotation_font_color=TEXTO_SEC)
    leyenda = False
else:
    col, colores, orden = (("grupo_etario", COLOR_EDAD, ORDEN_EDAD) if desglose == "Por grupo etario"
                           else ("genero", COLOR_GENERO, ["FEMENINO", "MASCULINO", "NO REPORTADO"]))
    cats = [c for c in orden if c in d[col].unique()]
    idx = pd.MultiIndex.from_product([cats, meses_sel], names=[col, "anio_mes"])
    s2 = (d.groupby([col, "anio_mes"])["cantidad"].sum().reindex(idx, fill_value=0)
          .rename("victimas").reset_index())
    s2["mes"] = s2["anio_mes"].dt.to_timestamp()
    fig = px.line(s2, x="mes", y="victimas", color=col, markers=True, color_discrete_map=colores,
                  category_orders={col: cats}, title=f"Víctimas por mes, {desglose.lower()}",
                  labels={"mes": "Mes", "victimas": "Víctimas por mes"})
    fig.update_traces(line=dict(width=2), marker=dict(size=7),
                      hovertemplate="%{x|%m/%Y}<br>%{y:,} víctimas<extra></extra>")
    leyenda = True
fig.update_layout(hovermode="x unified")
c1.plotly_chart(fechas(estilo(fig, alto=400, leyenda=leyenda)), width="stretch")

fig = go.Figure()
for i, a in enumerate(sorted(serie["anio"].unique())):
    vals = serie.loc[serie["anio"] == a, "victimas"]
    fig.add_trace(go.Box(y=vals, name=str(a), boxpoints="all", jitter=0.35, pointpos=0,
                         marker=dict(color=AZUL, size=7, opacity=0.7), line=dict(color="#1b64be", width=1.5),
                         fillcolor="rgba(37,125,224,0.12)",
                         hovertemplate=f"{a}<br>%{{y:,}} víctimas<extra></extra>"))
fig.update_layout(title="Dispersión de las víctimas mensuales por año",
                  yaxis_title="Víctimas por mes", xaxis_title="Año")
c2.plotly_chart(estilo(fig, alto=400, leyenda=False), width="stretch")
c2.caption("Cada punto es un mes. La caja va del primer al tercer cuartil; la línea central es la mediana.")

# ----------------------------------------------------------------------------
# 5. Componente predictivo
# ----------------------------------------------------------------------------
st.markdown("<div class='seccion'>5. Componente predictivo: víctimas por mes</div>", unsafe_allow_html=True)
MESES_PRUEBA = 6
if len(serie) < 18:
    st.info("Se necesitan al menos 18 meses para entrenar y probar los modelos. "
            "Quita el filtro de año para ver esta sección.")
else:
    t = np.arange(1, len(serie) + 1)
    y = serie["victimas"].to_numpy(dtype=float)
    t_ent, y_ent = t[:-MESES_PRUEBA], y[:-MESES_PRUEBA]
    t_pru, y_pru = t[-MESES_PRUEBA:], y[-MESES_PRUEBA:]

    coef_lin = np.polyfit(t_ent, y_ent, 1)
    coef_cua = np.polyfit(t_ent, y_ent, 2)
    base = y_ent[-12:].mean()
    preds = {"Base (promedio 12 meses)": np.full(MESES_PRUEBA, base),
             "Lineal": np.polyval(coef_lin, t_pru),
             "Cuadrático": np.polyval(coef_cua, t_pru)}
    filas = []
    for nombre, p in preds.items():
        mae = np.mean(np.abs(y_pru - p))
        rmse = np.sqrt(np.mean((y_pru - p) ** 2))
        filas.append({"Modelo": nombre, "MAE": mae, "RMSE": rmse,
                      "Error relativo (%)": mae / y_pru.mean() * 100})
    res = pd.DataFrame(filas)
    mejor = res.loc[res["MAE"].idxmin()]

    c1, c2 = st.columns([1.6, 1])
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=serie["mes"], y=y, mode="lines+markers", name="Real",
                             line=dict(color="#191919", width=2), marker=dict(size=7),
                             hovertemplate="%{x|%m/%Y}<br>Real: %{y:,.0f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=serie["mes"], y=np.polyval(coef_lin, t), mode="lines", name="Lineal",
                             line=dict(color=AZUL, width=2, dash="dash"),
                             hovertemplate="Lineal: %{y:,.0f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=serie["mes"], y=np.polyval(coef_cua, t), mode="lines", name="Cuadrático",
                             line=dict(color=NARANJA, width=2, dash="dash"),
                             hovertemplate="Cuadrático: %{y:,.0f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=serie["mes"].iloc[-MESES_PRUEBA:], y=preds["Base (promedio 12 meses)"],
                             mode="lines", name="Base", line=dict(color=GRIS, width=2, dash="dot"),
                             hovertemplate="Base: %{y:,.0f}<extra></extra>"))
    inicio_prueba = serie["mes"].iloc[-MESES_PRUEBA] - pd.Timedelta(days=15)
    fig.add_vrect(x0=inicio_prueba, x1=serie["mes"].iloc[-1] + pd.Timedelta(days=15),
                  fillcolor="#f2f2f2", line_width=0, layer="below",
                  annotation_text="Prueba", annotation_position="top left",
                  annotation_font_color=TEXTO_SEC)
    fig.update_layout(title="Valores reales frente a los modelos (entrenados sin los meses de prueba)",
                      xaxis_title="Mes", yaxis_title="Víctimas por mes", hovermode="x unified")
    c1.plotly_chart(fechas(estilo(fig, alto=400)), width="stretch")

    c2.markdown(f"**Separación temporal:** {len(t_ent)} meses de entrenamiento y "
                f"{MESES_PRUEBA} de prueba ({serie['anio_mes'].iloc[-MESES_PRUEBA].strftime('%m/%Y')} a "
                f"{serie['anio_mes'].iloc[-1].strftime('%m/%Y')}).")
    c2.dataframe(res.style.format({"MAE": num, "RMSE": num, "Error relativo (%)": pct})
                 .highlight_min(subset=["MAE"], color="#dbeafe"),
                 hide_index=True, width="stretch")
    c2.markdown(f"El modelo con menor error es **{mejor['Modelo']}**: en promedio se equivoca en "
                f"**{mejor['MAE']:.0f} víctimas por mes** ({pct(mejor['Error relativo (%)'])}).")
    c2.caption("MAE: error absoluto medio. RMSE: raíz del error cuadrático medio. Con solo 36 meses y una "
               "variable (el tiempo), estas predicciones son aproximadas y no deben tomarse como certezas.")

# ----------------------------------------------------------------------------
# Lectura rápida y pie
# ----------------------------------------------------------------------------
st.markdown("<div class='seccion'>Lectura rápida (según los filtros aplicados)</div>", unsafe_allow_html=True)
edad_top = edad.sort_values("victimas", ascending=False).iloc[0]
anual = serie.groupby("anio")["victimas"].sum()
obs = [
    f"El **{pct(pct_muj)}** de las víctimas son mujeres y el **{pct(pct_nna)}** son menores de 18 años; "
    f"el grupo con más víctimas es **{edad_top['grupo_etario'].lower()}** ({pct(edad_top['pct'])}).",
    f"El delito más frecuente es **{top_delito.index[0].lower()}** "
    f"({pct(top_delito.iloc[0] / total * 100)} de las víctimas), y **{por_depto.index[0].title()}** "
    f"concentra el {pct(por_depto.iloc[0] / total * 100)} de los casos.",
]
if len(anual) > 1:
    cambio = (anual.iloc[-1] / anual.iloc[0] - 1) * 100
    obs.append(f"Entre {anual.index[0]} y {anual.index[-1]} las víctimas registradas "
               f"{'aumentaron' if cambio >= 0 else 'disminuyeron'} un **{pct(abs(cambio))}** "
               f"({fmt(anual.iloc[0])} → {fmt(anual.iloc[-1])}).")
for o in obs:
    st.markdown(f"- {o}")
st.caption("Son observaciones descriptivas sobre denuncias registradas: no establecen relaciones causales "
           "ni equivalen al total de hechos ocurridos (existe subregistro).")

st.divider()
p1, p2 = st.columns([3, 1])
p1.markdown(f"<span class='nota'>{FUENTE} Datos: https://www.datos.gov.co/resource/fpe5-yrmw.json. "
            "Limpieza y análisis en Python (pandas, Plotly, Streamlit). Datos públicos y anonimizados: "
            "no contienen información que identifique a las víctimas.</span>", unsafe_allow_html=True)
p2.download_button("Descargar datos filtrados (CSV)", d.drop(columns=["anio_mes"]).to_csv(index=False)
                   .encode("utf-8"), "delitos_sexuales_filtrado.csv", "text/csv", width="stretch")
