import streamlit as st

st.set_page_config(
    page_title="Flujo de potencia",
    layout="wide"
)

st.title("Flujo de potencia en una microrred")
st.write("Simulación mediante el método de Newton-Raphson")

factor_carga = st.slider(
    "Factor de carga",
    min_value=0.5,
    max_value=2.5,
    value=1.0,
    step=0.1
)

potencia_generador = st.number_input(
    "Potencia del generador (MW)",
    min_value=0.0,
    value=100.0
)

if st.button("Ejecutar simulación"):
    st.success("La simulación se ejecutó correctamente.")
    st.write("Factor de carga:", factor_carga)
    st.write("Potencia del generador:", potencia_generador, "MW")