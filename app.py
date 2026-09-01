import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(
    page_title="Microrred eléctrica",
    page_icon="⚡",
    layout="wide"
)

# Valores iniciales y persistentes de la simulación
valores_iniciales = {
    "numero_barras": 3,
    "factor_carga": 1.0,
    "generacion": 100
}

for clave, valor_inicial in valores_iniciales.items():
    if clave not in st.session_state:
        st.session_state[clave] = valor_inicial
    else:
        # Evita que Streamlit elimine el valor al cambiar de página
        st.session_state[clave] = st.session_state[clave]

        
# =========================================================
# ESTILO DE LA PÁGINA
# =========================================================

st.markdown(
    """
    <style>
        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
        }

        h1, h2, h3 {
            color: #12355b;
        }

        [data-testid="stMetric"] {
            background-color: #f4f7fb;
            border: 1px solid #dce4ef;
            border-radius: 12px;
            padding: 15px;
        }

        .tarjeta {
            background-color: #f4f7fb;
            border-left: 5px solid #1976d2;
            border-radius: 10px;
            padding: 18px;
            margin-bottom: 15px;
        }
    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# MODELO PROVISIONAL
# Luego debe sustituirse por Newton-Raphson
# =========================================================

def calcular_modelo_demostracion(numero_barras, factor_carga, generacion):
    barras = np.arange(1, numero_barras + 1)

    voltajes = (
        1.04
        - 0.022 * factor_carga * np.arange(numero_barras)
        + 0.00010 * (generacion - 100) * np.arange(numero_barras)
    )

    voltajes[0] = 1.04
    voltajes = np.clip(voltajes, 0.80, 1.10)

    angulos = (
        -2.3 * factor_carga * np.arange(numero_barras)
        + 0.004 * (generacion - 100) * np.arange(numero_barras)
    )

    angulos[0] = 0

    razon_convergencia = 0.18 + 0.18 * factor_carga
    errores = 0.20 * razon_convergencia ** np.arange(15)

    tolerancia = 1e-6
    posiciones = np.where(errores < tolerancia)[0]

    if len(posiciones) > 0:
        iteraciones = int(posiciones[0] + 1)
        convergio = True
    else:
        iteraciones = len(errores)
        convergio = False

    resultados = pd.DataFrame({
        "Barra": barras,
        "Voltaje (p.u.)": np.round(voltajes, 4),
        "Ángulo (°)": np.round(angulos, 3)
    })

    return resultados, errores, convergio, iteraciones


# =========================================================
# MEDIDOR DE VOLTAJE
# =========================================================

def crear_medidor(voltaje, barra):
    figura = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=voltaje,
            number={
                "suffix": " p.u.",
                "valueformat": ".3f"
            },
            title={"text": f"Voltaje de barra {barra}"},
            gauge={
                "axis": {"range": [0.80, 1.10]},
                "bar": {"color": "#1976d2"},
                "steps": [
                    {"range": [0.80, 0.95], "color": "#ffb3b3"},
                    {"range": [0.95, 1.05], "color": "#b8e6c1"},
                    {"range": [1.05, 1.10], "color": "#ffe0a3"}
                ],
                "threshold": {
                    "line": {"color": "#222222", "width": 4},
                    "value": 1.0
                }
            }
        )
    )

    figura.update_layout(
        height=240,
        margin={"l": 20, "r": 20, "t": 50, "b": 10}
    )

    return figura


# =========================================================
# ONDAS SENOIDales
# =========================================================

def crear_ondas(resultados):
    grados = np.linspace(0, 360, 500)
    figura = go.Figure()

    colores = ["#1565c0", "#e53935", "#43a047", "#fb8c00"]

    for indice, fila in resultados.iterrows():
        voltaje = fila["Voltaje (p.u.)"]
        angulo = fila["Ángulo (°)"]

        onda = voltaje * np.sin(
            np.radians(grados + angulo)
        )

        figura.add_trace(
            go.Scatter(
                x=grados,
                y=onda,
                mode="lines",
                name=f"Barra {int(fila['Barra'])}: {angulo:.2f}°",
                line={
                    "color": colores[indice],
                    "width": 3
                }
            )
        )

    figura.update_layout(
        title="Representación de magnitud y ángulo de fase",
        xaxis_title="Ángulo eléctrico (°)",
        yaxis_title="Voltaje instantáneo (p.u.)",
        template="plotly_white",
        hovermode="x unified",
        height=430
    )

    return figura


# =========================================================
# DIAGRAMA ANIMADO DE LA RED
# =========================================================

def crear_red_animada(numero_barras, resultados, factor_carga):
    if numero_barras == 3:
        posiciones = {
            1: (0, 1),
            2: (1.5, 2),
            3: (3, 1)
        }

        lineas = [(1, 2), (2, 3), (1, 3)]

    else:
        posiciones = {
            1: (0, 1.5),
            2: (1.5, 2.5),
            3: (1.5, 0.5),
            4: (3, 1.5)
        }

        lineas = [
            (1, 2),
            (1, 3),
            (2, 4),
            (3, 4),
            (2, 3)
        ]

    figura = go.Figure()

    # Líneas eléctricas
    for inicio, final in lineas:
        x1, y1 = posiciones[inicio]
        x2, y2 = posiciones[final]

        figura.add_trace(
            go.Scatter(
                x=[x1, x2],
                y=[y1, y2],
                mode="lines",
                line={
                    "color": "#8fa4b8",
                    "width": 3 + factor_carga
                },
                hoverinfo="skip",
                showlegend=False
            )
        )

    # Partículas que representan flujo
    particulas_x = []
    particulas_y = []

    for inicio, final in lineas:
        x1, y1 = posiciones[inicio]
        x2, y2 = posiciones[final]

        for desplazamiento in [0.0, 0.33, 0.66]:
            particulas_x.append(
                x1 + desplazamiento * (x2 - x1)
            )
            particulas_y.append(
                y1 + desplazamiento * (y2 - y1)
            )

    indice_particulas = len(figura.data)

    figura.add_trace(
        go.Scatter(
            x=particulas_x,
            y=particulas_y,
            mode="markers",
            marker={
                "size": 11,
                "color": "#ffd600"
            },
            name="Flujo de potencia",
            hoverinfo="skip"
        )
    )

    # Barras o nodos
    nodos_x = []
    nodos_y = []
    textos = []
    voltajes = []

    for barra in range(1, numero_barras + 1):
        x, y = posiciones[barra]
        voltaje = resultados.loc[
            resultados["Barra"] == barra,
            "Voltaje (p.u.)"
        ].iloc[0]

        nodos_x.append(x)
        nodos_y.append(y)
        voltajes.append(voltaje)

        tipo = "Slack" if barra == 1 else "PQ"

        textos.append(
            f"Barra {barra}<br>"
            f"{tipo}<br>"
            f"{voltaje:.3f} p.u."
        )

    figura.add_trace(
        go.Scatter(
            x=nodos_x,
            y=nodos_y,
            mode="markers+text",
            text=textos,
            textposition="bottom center",
            marker={
                "size": 48,
                "color": voltajes,
                "colorscale": [
                    [0.0, "#e53935"],
                    [0.5, "#43a047"],
                    [1.0, "#f9a825"]
                ],
                "cmin": 0.90,
                "cmax": 1.08,
                "line": {
                    "color": "white",
                    "width": 3
                },
                "colorbar": {
                    "title": "Voltaje<br>(p.u.)"
                }
            },
            hovertemplate="%{text}<extra></extra>",
            showlegend=False
        )
    )

    # Cuadros de la animación
    cuadros = []

    for progreso in np.linspace(0, 1, 30):
        puntos_x = []
        puntos_y = []

        for inicio, final in lineas:
            x1, y1 = posiciones[inicio]
            x2, y2 = posiciones[final]

            for desplazamiento in [0.0, 0.33, 0.66]:
                avance = (progreso + desplazamiento) % 1

                puntos_x.append(
                    x1 + avance * (x2 - x1)
                )
                puntos_y.append(
                    y1 + avance * (y2 - y1)
                )

        cuadros.append(
            go.Frame(
                data=[
                    go.Scatter(
                        x=puntos_x,
                        y=puntos_y,
                        mode="markers",
                        marker={
                            "size": 11,
                            "color": "#ffd600"
                        }
                    )
                ],
                traces=[indice_particulas]
            )
        )

    figura.frames = cuadros

    figura.update_layout(
        title=f"Diagrama animado de una red de {numero_barras} barras",
        template="plotly_white",
        height=500,
        xaxis={
            "visible": False,
            "range": [-0.5, 3.5]
        },
        yaxis={
            "visible": False,
            "range": [0, 3]
        },
        showlegend=False,
        updatemenus=[
            {
                "type": "buttons",
                "direction": "left",
                "buttons": [
                    {
                        "label": "▶ Animar flujo",
                        "method": "animate",
                        "args": [
                            None,
                            {
                                "frame": {
                                    "duration": 80,
                                    "redraw": False
                                },
                                "fromcurrent": True
                            }
                        ]
                    },
                    {
                        "label": "⏸ Pausar",
                        "method": "animate",
                        "args": [
                            [None],
                            {
                                "frame": {
                                    "duration": 0,
                                    "redraw": False
                                },
                                "mode": "immediate"
                            }
                        ]
                    }
                ]
            }
        ]
    )

    return figura


# =========================================================
# PÁGINAS
# =========================================================

def pagina_inicio():
    st.title("⚡ Flujo de potencia en una microrred")
    st.subheader("Método numérico de Newton–Raphson")

    st.markdown(
        """
        <div class="tarjeta">
            Esta aplicación permite modificar las condiciones de una
            microrred y observar los cambios de voltaje, ángulo de fase
            y convergencia.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.write(
        """
        En la página **Simulación** podrás:

        - Elegir entre una red de tres o cuatro barras.
        - Variar la demanda eléctrica.
        - Modificar la generación.
        - Observar el flujo de potencia mediante una animación.
        - Ver los voltajes mediante medidores.
        - Comparar los ángulos mediante ondas senoidales.
        """
    )

    st.warning(
        "Esta primera versión utiliza resultados demostrativos. "
        "Después deben conectarse los cálculos reales de Newton–Raphson."
    )


def pagina_simulacion():
    st.title("🎛️ Simulación interactiva")

    columna1, columna2, columna3 = st.columns(3)

    with columna1:
        numero_barras = st.radio(
            "Configuración de la red",
            options=[3, 4],
            horizontal=True,
            key="numero_barras"
        )

    with columna2:
        factor_carga = st.slider(
            "Factor de demanda",
            min_value=0.50,
            max_value=2.50,
            step=0.05,
            key="factor_carga"
        )

    with columna3:
        generacion = st.slider(
            "Generación (MW)",
            min_value=20,
            max_value=200,
            step=5,
            key="generacion"
        )

    resultados, errores, convergio, iteraciones = (
        calcular_modelo_demostracion(
            numero_barras,
            factor_carga,
            generacion
        )
    )

    st.session_state["resultados"] = resultados
    st.session_state["errores"] = errores
    st.session_state["convergio"] = convergio
    st.session_state["iteraciones"] = iteraciones

    metrica1, metrica2, metrica3 = st.columns(3)

    metrica1.metric(
        "Voltaje mínimo",
        f"{resultados['Voltaje (p.u.)'].min():.3f} p.u."
    )

    metrica2.metric(
        "Iteraciones",
        iteraciones
    )

    metrica3.metric(
        "Estado",
        "Convergió" if convergio else "No convergió"
    )

    if convergio:
        st.success("El método alcanzó la tolerancia establecida.")
    else:
        st.error("El método no alcanzó la tolerancia establecida.")

    tab_red, tab_voltajes, tab_fases = st.tabs([
        "Red animada",
        "Medidores de voltaje",
        "Ángulos de fase"
    ])

    with tab_red:
        figura_red = crear_red_animada(
            numero_barras,
            resultados,
            factor_carga
        )

        st.plotly_chart(
            figura_red,
            use_container_width=True
        )

    with tab_voltajes:
        columnas = st.columns(numero_barras)

        for indice, fila in resultados.iterrows():
            with columnas[indice]:
                medidor = crear_medidor(
                    fila["Voltaje (p.u.)"],
                    int(fila["Barra"])
                )

                st.plotly_chart(
                    medidor,
                    use_container_width=True
                )

    with tab_fases:
        st.plotly_chart(
            crear_ondas(resultados),
            use_container_width=True
        )


def pagina_resultados():
    st.title("📊 Resultados y convergencia")

    if "resultados" not in st.session_state:
        st.info(
            "Primero debes ingresar a Simulación y modificar "
            "las condiciones de la red."
        )
        return

    resultados = st.session_state["resultados"]
    errores = st.session_state["errores"]

    st.subheader("Resultados por barra")
    st.dataframe(
        resultados,
        use_container_width=True,
        hide_index=True
    )

    figura = go.Figure()

    figura.add_trace(
        go.Scatter(
            x=np.arange(1, len(errores) + 1),
            y=errores,
            mode="lines+markers",
            line={
                "color": "#1976d2",
                "width": 3
            },
            marker={"size": 8}
        )
    )

    figura.update_layout(
        title="Error por iteración",
        xaxis_title="Iteración",
        yaxis_title="Error",
        yaxis_type="log",
        template="plotly_white",
        height=420
    )

    st.plotly_chart(
        figura,
        use_container_width=True
    )


# =========================================================
# NAVEGACIÓN
# =========================================================

paginas = [
    st.Page(
        pagina_inicio,
        title="Inicio",
        default=True
    ),
    st.Page(
        pagina_simulacion,
        title="Simulación"
    ),
    st.Page(
        pagina_resultados,
        title="Resultados"
    )
]

navegacion = st.navigation(paginas)
navegacion.run()