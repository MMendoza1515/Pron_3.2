import math
import sqlite3
import pandas as pd
import streamlit as st

# Configuración inicial de la página
st.set_page_config(
    page_title="pron v3.2 Pro - Centro Táctico", 
    page_icon="⚽", 
    layout="centered"
)

DB_NAME = "pron_v32_limpio.db"

# Inicialización de la base de datos SQLite
def inicializar_db():
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS matches_v32 (
            match_id INTEGER PRIMARY KEY AUTOINCREMENT,
            league TEXT, match_date TEXT, home_team TEXT, away_team TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS player_stats_v32 (
            player_stat_id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_name TEXT, team_name TEXT, league TEXT,
            goals_ranking INTEGER, shots_per_game REAL,
            yellow_red_cards INTEGER, fouls_drawn REAL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS governance_log_v32 (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_id INTEGER, market_category TEXT, market_selected TEXT,
            model_probability REAL, implied_probability REAL, delta_p REAL,
            governance_status TEXT
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
st.caption("Centro de Mando Táctico y Auditoría de Apuestas")

st.divider()

# --- SECCIÓN 1: SELECTBOX DE CONFIGURACIÓN ---
st.subheader("1. Configuración del Encuentro")

liga_seleccionada = st.selectbox(
    "Selecciona la Liga / Torneo:", 
    options=list(EQUIPOS_POR_LIGA.keys())
)

equipos_disponibles = EQUIPOS_POR_LIGA[liga_seleccionada]

col_eq1, col_eq2 = st.columns(2)
with col_eq1:
    equipo_local = st.selectbox("Equipo Local", options=equipos_disponibles, index=0)
with col_eq2:
    equipos_visitantes_disponibles = [eq for eq in equipos_disponibles if eq != equipo_local]
    equipo_visitante = st.selectbox("Equipo Visitante", options=equipos_visitantes_disponibles, index=0 if len(equipos_visitantes_disponibles) > 0 else 0)

st.divider()

# --- SECCIÓN 2: PARÁMETROS MATEMÁTICOS Y ESTADÍSTICOS ---
st.subheader("2. Variables de Modelado")

col_m1, col_m2 = st.columns(2)
with col_m1:
    lambda_goles = st.number_input("λ Goles Totales (xG)", value=2.6, step=0.1)
    remates_local = st.number_input(f"Remates Proyectados [{equipo_local}]", value=13.0, step=0.5)
with col_m2:
    lambda_corners = st.number_input("λ Córneres Totales", value=9.5, step=0.1)
    remates_visitante = st.number_input(f"Remates Proyectados [{equipo_visitante}]", value=11.5, step=0.5)

friccion_arbitral = st.slider(
    "Índice de Fricción Arbitral / Tarjetas", 
    min_value=0.80, max_value=2.00, value=1.20, step=0.05,
    help="1.00 = Promedio normal, >1.20 = Partido cerrado o friccionado"
)

# Protagonistas Clave
col_j1, col_j2 = st.columns(2)
with col_j1:
    jugador_1 = st.text_input(f"Estrella [{equipo_local}]", value="Delantero Local")
    j1_remates = st.number_input(f"Remates P/G ({equipo_local})", value=3.2, step=0.1)
with col_j2:
    jugador_2 = st.text_input(f"Estrella [{equipo_visitante}]", value="Delantero Visitante")
    j2_remates = st.number_input(f"Remates P/G ({equipo_visitante})", value=2.8, step=0.1)

st.divider()

# --- BOTÓN DE EJECUCIÓN ---
if st.button("🚀 Ejecutar Auditoría Integral Pro", type="primary", use_container_width=True):
    
    # --- CÁLCULOS CUANTITATIVOS ---
    lambda_10min = lambda_corners * (10 / 90)
    prob_no_corners = (math.exp(-lambda_10min) * (lambda_10min ** 0)) / math.factorial(0)
    p_modelo = prob_no_corners * 100  # En porcentaje

    # Estimación de mercado implícita de referencia (ej. cuota simétrica del 50%)
    p_implicita = 50.0 
    delta_p = p_modelo - p_implicita

    # Lógica de Gobernanza y Clasificación (Estelar vs Base)
    if p_modelo >= 40.0:
        estado_governance = "⭐ APROBADO ESTELAR"
        color_badge = "success"
    elif p_modelo >= 25.0:
        estado_governance = "✅ APROBADO BASE"
        color_badge = "info"
    else:
        estado_governance = "⚠️ REVISAR RIESGO"
        color_badge = "warning"

    # Dinámica de Saques de Puerta y Remates
    t_puerta_local = round(remates_local * 0.38, 1)
    t_puerta_visitante = round(remates_visitante * 0.38, 1)
    saques_visitante = round(remates_local - t_puerta_local, 1)
    saques_local = round(remates_visitante - t_puerta_visitante, 1)
    remates_totales = remates_local + remates_visitante
    tarjetas_proyectadas = round(4.2 * friccion_arbitral, 1)

    # --- BLOQUE UNIFICADO DE RESULTADOS (DE UN SOLO VISTAZO) ---
    st.success(f"📋 Auditoría Completa: {equipo_local} vs {equipo_visitante} ({liga_seleccionada})")

    # Tarjetas de Indicadores Principales (KPIs)
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Prob. No Córners <10'", f"{p_modelo:.1f}%", f"Δ {delta_p:+.1f}%")
    kpi2.metric("Tarjetas Amarillas Est.", f"{tarjetas_proyectadas}")
    kpi3.metric("Remates Totales", f"{remates_totales}")

    # Panel de Gobernanza Estructurado
    st.markdown("### 🏛️ Matriz de Gobernanza & Decisión")
    st.markdown(
        f"""
        | Componente Táctico | Detalle de Auditoría |
        | :--- | :--- |
        | **Estado de Validación** | **{estado_governance}** |
        | **Probabilidad del Modelo ($P_m$)** | `{p_modelo:.2f}%` |
        | **Probabilidad Implícita de Mercado** | `{p_implicita:.2f}%` |
        | **Margen de Valor ($\Delta p$)** | `{delta_p:+.2f}%` *(Indicador de Valor Matemático)* |
        | **Volumen de Saques de Puerta** | `{equipo_visitante}: {saques_visitante}` \| `{equipo_local}: {saques_local}` |
        | **Fricción & Disciplina** | Coeficiente arbitral de `{friccion_arbitral}` con `{tarjetas_proyectadas}` amonestaciones estimadas. |
        """
    )

    # Tabla Interactiva de Protagonistas (Player Props)
    st.markdown("### 🏃‍♂️ Rendimiento de Protagonistas Clave")
    df_jugadores = pd.DataFrame([
        {"Jugador": jugador_1, "Equipo": equipo_local, "Liga / Torneo": liga_seleccionada, "Remates P/G": j1_remates},
        {"Jugador": jugador_2, "Equipo": equipo_visitante, "Liga / Torneo": liga_seleccionada, "Remates P/G": j2_remates}
    ])
    st.dataframe(df_jugadores, use_container_width=True)

    # PERSISTENCIA EN SQLITE
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    cursor.execute("""
        INSERT INTO governance_log_v32 (match_id, market_category, market_selected, model_probability, implied_probability, delta_p, governance_status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (202, f"Auditoría Unificada - {liga_seleccionada}", f"{equipo_local} vs {equipo_visitante}", round(p_modelo/100, 4), 0.50, round(delta_p/100, 4), estado_governance))
    conexion.commit()
    conexion.close()

    st.toast("Datos de gobernanza guardados en SQLite con éxito.", icon="💾")
