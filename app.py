import math
import sqlite3
import pandas as pd
import streamlit as st

# Configuración inicial de la página
st.set_page_config(
    page_title="pron v3.2 Pro - Dashboard", 
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
    # --- LIGAS TOP EUROPA ---
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

    # --- AMÉRICA Y LATINOAMÉRICA ---
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

    # --- TORNEOS INTERNACIONALES DE CLUBES ---
    "UEFA Champions League": [
        "Real Madrid", "Manchester City", "Bayern Múnich", "Paris Saint-Germain",
        "Inter de Milán", "Arsenal", "Barcelona", "Leverkusen", "Atlético de Madrid", "Liverpool"
    ],
    "Copa Libertadores": [
        "Flamengo", "Palmeiras", "River Plate", "Boca Juniors",
        "Fluminense", "São Paulo", "Atlético Mineiro", "Colo-Colo", "Peñarol", "Liga de Quito"
    ],

    # --- TORNEOS DE SELECCIONES ---
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
st.caption("Dashboard Analítico y Auditoría Móvil de Partidos")

st.divider()

# --- SECCIÓN 1: SELECCIÓN DE LIGA Y EQUIPOS ---
st.subheader("1. Selección del Encuentro")

liga_seleccionada = st.selectbox(
    "Selecciona la Liga / Torneo Mundial:", 
    options=list(EQUIPOS_POR_LIGA.keys())
)

equipos_disponibles = EQUIPOS_POR_LIGA[liga_seleccionada]

col_eq1, col_eq2 = st.columns(2)
with col_eq1:
    equipo_local = st.selectbox(
        "Equipo Local", 
        options=equipos_disponibles,
        index=0
    )
with col_eq2:
    equipos_visitantes_disponibles = [eq for eq in equipos_disponibles if eq != equipo_local]
    equipo_visitante = st.selectbox(
        "Equipo Visitante", 
        options=equipos_visitantes_disponibles,
        index=0 if len(equipos_visitantes_disponibles) > 0 else 0
    )

st.divider()

# --- SECCIÓN 2: PARÁMETROS ESTADÍSTICOS ---
st.subheader("2. Métrica Base del Partido")

col_m1, col_m2 = st.columns(2)
with col_m1:
    lambda_goles = st.number_input("λ Goles Totales (xG)", value=2.6, step=0.1)
    remates_local = st.number_input(f"Remates Proyectados [{equipo_local}]", value=12.5, step=0.5)
with col_m2:
    lambda_corners = st.number_input("λ Córneres Totales", value=9.5, step=0.1)
    remates_visitante = st.number_input(f"Remates Proyectados [{equipo_visitante}]", value=11.0, step=0.5)

friccion_arbitral = st.slider(
    "Índice de Fricción Arbitral / Tarjetas", 
    min_value=0.80, max_value=2.00, value=1.20, step=0.05,
    help="1.00 = Promedio normal, >1.20 = Partido cerrado/frictivo"
)

# --- SECCIÓN 3: PROTAGONISTAS CLAVE ---
st.subheader("3. Protagonistas Clave")

col_j1, col_j2 = st.columns(2)
with col_j1:
    jugador_1 = st.text_input(f"Estrella [{equipo_local}]", value="Delantero Local")
    j1_remates = st.number_input(f"Remates P/G ({equipo_local})", value=3.2, step=0.1)
with col_j2:
    jugador_2 = st.text_input(f"Estrella [{equipo_visitante}]", value="Delantero Visitante")
    j2_remates = st.number_input(f"Remates P/G ({equipo_visitante})", value=2.9, step=0.1)

st.divider()

# --- BOTÓN PRINCIPAL DE EJECUCIÓN ---
if st.button("🚀 Ejecutar Auditoría pron v3.2 Pro", type="primary", use_container_width=True):
    # CÁLCULOS MATEMÁTICOS (POISSON)
    lambda_10min = lambda_corners * (10 / 90)
    prob_no_corners = (math.exp(-lambda_10min) * (lambda_10min ** 0)) / math.factorial(0)
    porcentaje_no_corners = prob_no_corners * 100

    # Remates y Saques de Puerta
    t_puerta_local = round(remates_local * 0.38, 1)
    t_puerta_visitante = round(remates_visitante * 0.38, 1)
    saques_visitante = round(remates_local - t_puerta_local, 1)
    saques_local = round(remates_visitante - t_puerta_visitante, 1)
    remates_totales = remates_local + remates_visitante

    # Disciplina
    tarjetas_proyectadas = round(4.2 * friccion_arbitral, 1)

    # REPORTE VISUAL EN TARJETAS
    st.success(f"¡Auditoría Exitosa: {equipo_local} vs {equipo_visitante} ({liga_seleccionada})!")

    st.subheader("📊 Resultados de la Auditoría")

    m_col1, m_col2 = st.columns(2)
    m_col1.metric("Prob. No Córners <10'", f"{porcentaje_no_corners:.1f}%")
    m_col2.metric("Tarjetas Amarillas Est.", f"{tarjetas_proyectadas}")

    st.markdown("#### 🎯 Remates & Saques de Puerta")
    st.info(
        f"• **Remates Totales:** {remates_totales} ({equipo_local}: {remates_local} | {equipo_visitante}: {remates_visitante})\n"
        f"• **Saques de Puerta para {equipo_visitante}:** {saques_visitante} *(por desvíos de {equipo_local})*\n"
        f"• **Saques de Puerta para {equipo_local}:** {saques_local} *(por desvíos de {equipo_visitante})*"
    )

    st.markdown("#### 🏃‍♂️ Jugadores Registrados")
    df_jugadores = pd.DataFrame([
        {"Jugador": jugador_1, "Equipo": equipo_local, "Remates P/G": j1_remates},
        {"Jugador": jugador_2, "Equipo": equipo_visitante, "Remates P/G": j2_remates}
    ])
    st.dataframe(df_jugadores, use_container_width=True)

    # PERSISTENCIA EN SQLITE
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    cursor.execute("""
        INSERT INTO governance_log_v32 (match_id, market_category, market_selected, model_probability, implied_probability, delta_p, governance_status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (101, f"Auditoría Pro - {liga_seleccionada}", f"{equipo_local} vs {equipo_visitante}", round(prob_no_corners, 4), 0.50, round(prob_no_corners - 0.50, 4), "APROBADO_MUNDIAL"))
    conexion.commit()
    conexion.close()

    st.toast("Gobernanza guardada con éxito en SQLite.", icon="💾")
