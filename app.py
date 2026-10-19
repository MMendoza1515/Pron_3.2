import math
import sqlite3
import pandas as pd
import streamlit as st

# Configuración inicial de la página
st.set_page_config(
    page_title="pron v3.2 Pro - Centro Táctico Integral", 
    page_icon="⚽", 
    layout="centered"
)

DB_NAME = "pron_v32_limpio.db"

# --- PROTOCOLO OBLIGATORIO DE RESETEO Y LIMPIEZA DE VARIABLES ---
def resetear_variables_sesion():
    """Elimina cualquier estado residual previo en la memoria de la sesión."""
    keys_a_limpiar = [
        'p_local_pct', 'p_empate_pct', 'p_visitante_pct', 
        'estado_governance', 'saques_local', 'saques_visitante', 
        'prob_no_corners', 'tarjetas_proyectadas'
    ]
    for key in keys_a_limpiar:
        if key in st.session_state:
            del st.session_state[key]
    # Limpia la caché de Streamlit para forzar un cálculo fresco
    st.cache_data.clear()

# Inicialización segura de la base de datos SQLite
def inicializar_db():
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    cursor.execute("DROP TABLE IF EXISTS governance_log_v32")
    cursor.execute("""
        CREATE TABLE governance_log_v32 (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_date TEXT, home_team TEXT, away_team TEXT,
            p_local REAL, p_empate REAL, p_visitante REAL, governance_status TEXT
        )
    """)
    conexion.commit()
    conexion.close()

inicializar_db()

# --- DICCIONARIO AMPLIADO MUNDIAL DE LIGAS Y TORNEOS ---
EQUIPOS_POR_LIGA = {
    "La Liga (España)": [
        "Real Madrid", "Barcelona", "Atlético de Madrid", 
        "Getafe", "Rayo Vallecano", "Real Sociedad", "Villarreal", "Athletic Club", "Sevilla", "Valencia"
    ],
    "Premier League (Inglaterra)": [
        "Manchester City", "Arsenal", "Liverpool", 
        "Manchester United", "Chelsea", "Tottenham", "Aston Villa", "Newcastle United", "Brighton", "West Ham"
    ],
    "Serie A (Italia)": [
        "Inter de Milán", "AC Milan", "Juventus", 
        "Napoli", "Atalanta", "Roma", "Lazio", "Fiorentina", "Bologna", "Torino"
    ],
    "Bundesliga (Alemania)": [
        "Bayer Leverkusen", "Bayern Múnich", "Borussia Dortmund", 
        "RB Leipzig", "Stuttgart", "Eintracht Frankfurt", "Wolfsburg", "Union Berlin"
    ],
    "Süper Lig (Turquía)": [
        "Trabzonspor", "Besiktas", "Galatasaray", 
        "Fenerbahce", "Basaksehir", "Adana Demirspor", "Sivasspor", "Antalyaspor"
    ],
    "Liga Profesional (Argentina)": [
        "River Plate", "Boca Juniors", "Racing Club", 
        "Independiente", "San Lorenzo", "Estudiantes de La Plata", "Vélez Sarsfield", "Talleres"
    ],
    "Brasileirão (Brasil)": [
        "Flamengo", "Palmeiras", "Atlético Mineiro", 
        "São Paulo", "Fluminense", "Botafogo", "Internacional", "Corinthians"
    ],
    "Liga MX (México)": [
        "América", "Cruz Azul", "Monterrey", 
        "Tigres UANL", "Chivas de Guadalajara", "Toluca", "Pachuca", "Pumas UNAM"
    ],
    "MLS (Estados Unidos / Canadá)": [
        "Inter Miami", "LAFC", "LA Galaxy", 
        "Columbus Crew", "Seattle Sounders", "FC Cincinnati", "New York City FC"
    ],
    "Primera División (El Salvador)": [
        "Alianza FC", "CD FAS", "CD Águila", 
        "Isidro Metapán", "Municipal Limeño", "11 Deportivo", "Fuerte San Francisco", "Dragón"
    ],
    "UEFA Champions League": [
        "Real Madrid", "Manchester City", "Bayern Múnich", "Paris Saint-Germain",
        "Inter de Milán", "Arsenal", "Barcelona", "Leverkusen", "Atlético de Madrid", "Liverpool"
    ],
    "Copa Libertadores": [
        "Flamengo", "Palmeiras", "River Plate", "Boca Juniors",
        "Fluminense", "São Paulo", "Atlético Mineiro", "Colo-Colo", "Peñarol", "Liga de Quito"
    ],
    "Eliminatorias / Amistosos (Selecciones)": [
        "Argentina", "Brasil", "España", "Francia", 
        "Inglaterra", "Alemania", "Portugal", "México", 
        "Estados Unidos", "Uruguay", "Colombia", "El Salvador"
    ],
    "Copa Mundial de la FIFA": [
        "Argentina", "Francia", "Brasil", "Inglaterra", 
        "España", "Alemania", "Países Bajos", "Portugal", 
        "Bélgica", "Croacia", "Uruguay", "Estados Unidos", "México", "El Salvador"
    ],
    "Copa América / Eurocopa": [
        "Argentina", "Brasil", "Uruguay", "Colombia",
        "España", "Francia", "Inglaterra", "Alemania", "Italia", "Portugal"
    ]
}

# --- ENCABEZADO ---
st.title("⚽ Protocolo pron v3.2 Pro")
st.caption("Centro Táctico de Decisiones y Auditoría Integral")

st.divider()

# --- SECCIÓN 1: CONFIGURACIÓN DEL ENCUENTRO ---
st.subheader("1. Configuración del Partido")

liga_seleccionada = st.selectbox(
    "Selecciona la Liga / Torneo:", 
    options=list(EQUIPOS_POR_LIGA.keys()),
    on_change=resetear_variables_sesion
)

equipos_disponibles = EQUIPOS_POR_LIGA[liga_seleccionada]

col_eq1, col_eq2 = st.columns(2)
with col_eq1:
    equipo_local = st.selectbox("Equipo Local", options=equipos_disponibles, index=0, on_change=resetear_variables_sesion)
with col_eq2:
    equipos_visitantes_disponibles = [eq for eq in equipos_disponibles if eq != equipo_local]
    equipo_visitante = st.selectbox("Equipo Visitante", options=equipos_visitantes_disponibles, index=0 if len(equipos_visitantes_disponibles) > 0 else 0, on_change=resetear_variables_sesion)

st.divider()

# --- SECCIÓN 2: PARÁMETROS TÁCTICOS Y DE MODELADO ---
st.subheader("2. Variables y Parámetros Tácticos")

col_m1, col_m2 = st.columns(2)
with col_m1:
    lambda_local = st.number_input(f"xG Esperados [{equipo_local}]", value=1.65, step=0.05)
    remates_local = st.number_input(f"Remates Proyectados [{equipo_local}]", value=14.0, step=0.5)
    lambda_corners = st.number_input("λ Córneres Totales", value=9.5, step=0.5)
with col_m2:
    lambda_visitante = st.number_input(f"xG Esperados [{equipo_visitante}]", value=1.45, step=0.05)
    remates_visitante = st.number_input(f"Remates Proyectados [{equipo_visitante}]", value=12.5, step=0.5)
    friccion_arbitral = st.slider("Índice de Fricción Arbitral / Tarjetas", min_value=0.80, max_value=2.00, value=1.25, step=0.05)

# Protagonistas Clave (Player Props)
st.markdown("#### 🏃‍♂️ Protagonistas Clave (Player Props)")
col_j1, col_j2 = st.columns(2)
with col_j1:
    jugador_1 = st.text_input(f"Estrella [{equipo_local}]", value="Ousmane Dembélé")
    j1_remates = st.number_input(f"Remates P/G ({equipo_local})", value=3.4, step=0.1)
with col_j2:
    jugador_2 = st.text_input(f"Estrella [{equipo_visitante}]", value="Lamine Yamal")
    j2_remates = st.number_input(f"Remates P/G ({equipo_visitante})", value=2.9, step=0.1)

st.divider()

# --- BOTÓN DE EJECUCIÓN PRINCIPAL CON DIRECTRIZ DE PURGA ---
if st.button("🚀 Ejecutar Auditoría Integral Pro (Purga & Cálculo)", type="primary", use_container_width=True):
    
    # DIRECTRIZ FORMAL DE REINICIO DE VARIABLES
    resetear_variables_sesion()
    
    # --- CÁLCULO DE POISSON 1X2 (BARRIDO HASTA 6x6) ---
    max_goles = 6
    prob_local_win = 0.0
    prob_empate = 0.0
    prob_visitante_win = 0.0

    for i in range(max_goles + 1):
        for j in range(max_goles + 1):
            p_i = (math.exp(-lambda_local) * (lambda_local ** i)) / math.factorial(i)
            p_j = (math.exp(-lambda_visitante) * (lambda_visitante ** j)) / math.factorial(j)
            p_match = p_i * p_j
            
            if i > j:
                prob_local_win += p_match
            elif i == j:
                prob_empate += p_match
            else:
                prob_visitante_win += p_match

    # Normalización porcentual 1X2
    total_prob = prob_local_win + prob_empate + prob_visitante_win
    p_local_pct = (prob_local_win / total_prob) * 100
    p_empate_pct = (prob_empate / total_prob) * 100
    p_visitante_pct = (prob_visitante_win / total_prob) * 100

    # Lógica de Gobernanza y Clasificación
    max_p = max(p_local_pct, p_empate_pct, p_visitante_pct)
    if max_p >= 55.0:
        estado_governance = "⭐ APROBADO ESTELAR (Alta Certeza)"
    elif max_p >= 42.0:
        estado_governance = "✅ APROBADO BASE (Valor Moderado)"
    else:
        estado_governance = "⚠️ REVISAR RIESGO (Alta Incertidumbre)"

    # Dinámica Secundaria (Saques de puerta y tarjetas)
    t_puerta_local = round(remates_local * 0.38, 1)
    t_puerta_visitante = round(remates_visitante * 0.38, 1)
    saques_visitante = round(remates_local - t_puerta_local, 1)
    saques_local = round(remates_visitante - t_puerta_visitante, 1)
    
    lambda_10min = lambda_corners * (10 / 90)
    prob_no_corners = ((math.exp(-lambda_10min) * (lambda_10min ** 0)) / math.factorial(0)) * 100
    tarjetas_proyectadas = round(4.2 * friccion_arbitral, 1)

    # --- BLOQUE VISUAL UNIFICADO DE UN SOLO VISTAZO ---
    st.success(f"🎯 Dictamen Táctico [RESETEADO]: {equipo_local} vs {equipo_visitante} ({liga_seleccionada})")

    # 1. Tarjetas de Probabilidad 1X2 (KPIs)
    col_res1, col_res2, col_res3 = st.columns(3)
    col_res1.metric(f"Victoria {equipo_local}", f"{p_local_pct:.1f}%")
    col_res2.metric("Empate (X)", f"{p_empate_pct:.1f}%")
    col_res3.metric(f"Victoria {equipo_visitante}", f"{p_visitante_pct:.1f}%")

    # 2. Matriz de Gobernanza Consolidada
    st.markdown("### 🏛️ Matriz de Gobernanza & Categorías Tácticas")
    st.markdown(
        f"""
        | Módulo / Categoría Fija | Detalle del Análisis / Resultado |
        | :--- | :--- |
        | **Estado de Viabilidad** | **{estado_governance}** |
        | **Tendencia Matemática Principal** | `{'Local Favorecido' if p_local_pct > p_visitante_pct else 'Visitante Favorecido'}` ({max_p:.1f}%) |
        | **Volumen de Saques de Puerta** | **{equipo_local}:** `{saques_local}` \| **{equipo_visitante}:** `{saques_visitante}` |
        | **Dinámica de Córneres (<10')** | Probabilidad de que no haya córneres en los primeros 10': **{prob_no_corners:.1f}%** |
        | **Fricción Arbitral & Disciplina** | Coeficiente `{friccion_arbitral}` con **{tarjetas_proyectadas}** amarillas estimadas |
        """
    )

    # 3. Tabla de Protagonistas Clave
    st.markdown("### 🏃‍♂️ Rendimiento de Protagonistas Clave")
    df_jugadores = pd.DataFrame([
        {"Jugador": jugador_1, "Equipo": equipo_local, "Remates P/G": j1_remates, "Impacto": "Desborde / Transición"},
        {"Jugador": jugador_2, "Equipo": equipo_visitante, "Remates P/G": j2_remates, "Impacto": "Ruptura / Bloque Bajo"}
    ])
    st.dataframe(df_jugadores, use_container_width=True)

    # PERSISTENCIA EN SQLITE
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    cursor.execute("""
        INSERT INTO governance_log_v32 (match_date, home_team, away_team, p_local, p_empate, p_visitante, governance_status)
        VALUES (datetime('now'), ?, ?, ?, ?, ?, ?)
    """, (equipo_local, equipo_visitante, round(p_local_pct, 2), round(p_empate_pct, 2), round(p_visitante_pct, 2), estado_governance))
    conexion.commit()
    conexion.close()

    st.toast("Variables purgadas y auditoría registrada con éxito.", icon="🔄")
