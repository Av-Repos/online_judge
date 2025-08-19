import streamlit as st
import pandas as pd
from io import StringIO
import datetime
import os
from utils import *
from mutex import *
import time

# Cargar leaderboard existente
def load_leaderboard():
    if not os.path.exists(PATH_LEADERBOARD):
        return pd.DataFrame(columns=["Equipo", "Puntos", "Subido"])
    return pd.read_csv(PATH_LEADERBOARD)

# Guardar o actualizar el leaderboard
def save_to_leaderboard(team_name, points):
    df = load_leaderboard()
    now = datetime.datetime.now().strftime("%H:%M:%S")
    
    if team_name in df["Equipo"].values:  # Si el equipo ya existe
        current_points = df.loc[df["Equipo"] == team_name, "Puntos"].values[0]
        
        # Solo actualizamos si la nueva puntuación es mayor
        if points > current_points:
            df.loc[df["Equipo"] == team_name, ["Puntos", "Subido"]] = [points, now]
            df.to_csv(PATH_LEADERBOARD, index=False)
            return True
        else:
            return False  # No se actualiza porque la nueva puntuación es menor
    else:
        # Si no existe el equipo, lo añadimos como una nueva entrada
        new_row = pd.DataFrame([[team_name, points, now]], columns=df.columns)
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(PATH_LEADERBOARD, index=False)
        return True

# Actualiza el layout y la base de datos de acuerdo a la solución y equipo indicados
def update(file_content, team_name):
    try:
        #Evalua la solución y recoge toda la información necesaria para la creación del heatmap
        points, heatmap = evaluate(file_content)
        #Crea la imagen con el heatmap
        heatmap_plot(heatmap, team_name)
        #Actualiza el leaderboard
        save_to_leaderboard(team_name, points)
        return points
    except Exception as e:
        return f"❌ Error en la evaluación: {e}"

# Crea la imagen del heatmap asociado a la solución y equipo indicados
def heatmap_plot(heatmap, team_name):
    fig, axes = plt.subplots(
        nrows=HEAT_ROWS, ncols=HEAT_COLS, figsize=(4*HEAT_COLS, 4*HEAT_ROWS)
    )

    count = 1
    for i in range(HEAT_ROWS):
        for j in range(HEAT_COLS):
            hp = heatmap[heatmap["Cluster"] == count].pivot(
                index='Row', columns='Column', values='Points'
            )
            sns.heatmap(
                hp, annot=True, cmap='viridis', ax=axes[i][j],
                vmin=0, vmax=3+2*(MAX_RADIO-1), cbar=False
            )
            axes[i][j].set_title(f"Cluster Nº {count}")
            count += 1

    fig.tight_layout()

    fig.savefig(FOLDER_HEATMAP+f"{team_name}.png")
    plt.close(fig)   # 👈 CERRAR LA FIGURA PARA EVITAR QUE OTRO PROCESO PARALELO LA SOBRESCRIBA!

mutex = FileMutex()

st.set_page_config(layout="wide")

# CSS para mejorar la visualización
st.markdown("""
<style>
/* Añadir padding lateral para separar del borde de la pantalla */
.st-emotion-cache-18ni7ap {
    padding-left: 1rem !important;
    padding-right: 1rem !important;
}

/* También puedes ajustar max-width si necesitas */
.main .block-container {
    max-width: 100vw !important;
}

/* Aumentar el tamaño de los encabezados de la columna central */
.st-markdown h1 {
    font-size: 200% !important;
}

/* Cambiar el tamaño del texto en la tabla del leaderboard */
.st-dataframe {
    font-size: 1.25rem !important;
}

/* Ajustar el tamaño del título en la columna central */
.st-column .css-12oz5g7 {
    font-size: 1.5rem !important;
}
</style>
""", unsafe_allow_html=True)

col1, col_center, col3 = st.columns([1,3,1], gap="large")

with col1:
    st.markdown("<h1 style='text-align:center; width: 100%;'>🏅 TOPS 🏅</h1>", unsafe_allow_html=True)
    
    # Cargar leaderboard y filtrar las 4 mejores puntuaciones
    df = load_leaderboard()
    if not df.empty:
        # Obtener las 4 mejores puntuaciones, ordenadas por puntos y fecha
        top_df = df.sort_values(by=["Puntos", "Subido"], ascending=[False,True]).head(4)
        i = 1
        for _, row in top_df.iterrows():
            team_name = row["Equipo"]
            st.markdown(f"<h1 style='text-align:center; width: 100%; font-size: 150%;'>{i}. {team_name}: {row['Puntos']}</h1>", unsafe_allow_html=True)
            st.image(FOLDER_HEATMAP + f"{team_name}.png", use_container_width=True)
            i += 1
    else:
        st.info("Aún no hay envíos. ¡Sé el primero en subir tu solución!")

with col3:
    st.markdown("<h1 style='text-align:center; width: 100%;'>🔥 NEWS 🔥</h1>", unsafe_allow_html=True)
    
    # Cargar leaderboard y filtrar las más recientes
    if not df.empty:
        # Obtener las 4 entradas más recientes, ordenadas por fecha de subida
        recent_df = df.sort_values(by=["Subido"], ascending=False).head(4)
        for _, row in recent_df.iterrows():
            team_name = row["Equipo"]
            st.markdown(f"<h1 style='text-align:center; width: 100%; font-size: 150%;'>{team_name}: {row['Puntos']} ({row['Subido']})</h1>", unsafe_allow_html=True)
            st.image(FOLDER_HEATMAP + f"{team_name}.png", use_container_width=True)
    else:
        st.info("Aún no hay envíos. ¡Sé el primero en subir tu solución!")

with col_center:
    st.markdown("<h1 style='text-align:center; width: 100%;'>🏆 Leaderboard 🏆</h1>", unsafe_allow_html=True)

    st.markdown("Sube tu archivo `.csv` de resultados para recibir tu puntuación.")

    # Inicializar estado si no existe
    if "uploaded" not in st.session_state:
        st.session_state.uploaded = False
    if "points" not in st.session_state:
        st.session_state.points = None
    if "team_name" not in st.session_state:
        st.session_state.team_name = ""
    if "file" not in st.session_state:
        st.session_state.file = None

    # Inputs
    st.session_state.team_name = st.text_input("Nombre del participante", value=st.session_state.team_name)
    st.session_state.file = st.file_uploader("Archivo CSV", type="csv", key="file_uploader")

    # Botón de evaluación
    if st.button("Subir y evaluar") or ("button_clicked" in st.session_state and st.session_state.button_clicked):
        if st.session_state.team_name and st.session_state.file:
            content = StringIO(st.session_state.file.getvalue().decode("utf-8"))

            # Ejecutar en segundo plano
            st.info("🕐 Procesando archivo...")

            #Comprueba si alguien está usando los recursos compartidos. En caso afirmativo, recarga la página
            if not mutex.reserve():
                st.session_state.button_clicked = True
                st.rerun()
            else:
                st.session_state.button_clicked = False

            # Realiza el update y libera los recursos compartidos
            try:
                result = update(content, st.session_state.team_name)
            finally:
                mutex.release()

            if isinstance(result, str) and result.startswith("❌"):
                st.error(result)
            else:
                st.session_state.points = result
                st.session_state.uploaded = True
                st.rerun()
        else:
            st.warning("⚠️ Asegúrate de haber escrito tu nombre y seleccionado un archivo.")

        # Mostrar mensaje después de la recarga
        if st.session_state.uploaded:
            st.success(f"""✅ ¡Evaluación completada!
🎯 Puntuación: {st.session_state.points} puntos""")

        if st.button("Subir otro archivo"):
            st.session_state.uploaded = False
            st.session_state.points = None
            st.session_state.file = None
            st.session_state.team_name = ""
            st.rerun()

    # Mostrar leaderboard
    st.subheader("🏁 Leaderboard actual")
    df = load_leaderboard()
    row_height = 35  # altura estimada por fila
    num_rows = len(df)
    if not df.empty:
        df = df[["Equipo", "Puntos", "Subido"]]
        df = df.sort_values(by=["Puntos", "Subido"], ascending=[False,True]).reset_index(drop=True)
        
        if len(df.index) > 0:
            df.at[0, 'Equipo'] = f"{df.at[0, 'Equipo']} 👑"
        if len(df.index) > 1:
            df.at[1, 'Equipo'] = f"{df.at[1, 'Equipo']} 🥈"
        if len(df.index) > 2:
            df.at[2, 'Equipo'] = f"{df.at[2, 'Equipo']} 🥉"
        
        # Create custom styled HTML table
        styled_table = df.to_html(index=False)

        # Inject CSS to style table
        st.markdown("""
	    <style>
	    /* Make the table responsive and use full width */
	    table {
		width: 100%;
		border-collapse: collapse;
		font-size: 2rem;
		table-layout: fixed;
	    }

	    td {
		padding: 12px;
		text-align: center;
		border: 1px solid #ddd;
		word-wrap: break-word;
		font-weight: bold;
		color: black; 
	    }

	    th {
		padding: 12px;
		text-align: center;
		border: 1px solid #ddd;
		word-wrap: break-word;
		font-weight: bold;
		color: black; 
		background-color: #f0f0f0;
	    }
	    
	    /* Row backgrounds */
	    table tr:nth-child(1) {
		font-size: 2rem;
		background-color: #D4AF37;
	    }

	    table tr:nth-child(2) {
		font-size: 1.75rem;
		background-color: #c0c0c0;
	    }

	    table tr:nth-child(3) {
		font-size: 1.75rem;
		background-color: #CD7F32;
	    }

	    table tr:nth-child(n+4) {
		font-size: 1.5rem;
		background-color: white;
	    }
	    </style>
        """, unsafe_allow_html=True)

        # Display the HTML table
        st.markdown(styled_table, unsafe_allow_html=True)
    else:
        st.info("Aún no hay envíos. ¡Sé el primero en subir tu solución!")
