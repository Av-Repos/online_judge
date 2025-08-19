import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import sys
#Paths de los ficheros de instancia (students.csv) y leaderboard actual (leaderboard.csv)
PATH_INSTANCE = "./data/students.csv"
PATH_LEADERBOARD = "./data/leaderboard.csv"

#Dimensiones del problema (la cantidad de estudiantes será N_CLUSTERS*N_ROWS*N_SEATS)
N_CLUSTERS = 4
N_ROWS = 8
N_SEATS = 6
#Máximo radio a considerar en las preferencias con respecto a otros estudiantes
MAX_RADIO = 4

#Paths a las carpetas donde se guardan las soluciones y las imágenes generadas
FOLDER_HEATMAP = "./data/images/"

#Variables que controlan la distribución de los heatmaps en la imágenes generadas
HEAT_ROWS = 2
HEAT_COLS = 2

#Evalua la solución en el fichero indicado
def evaluate(file_solution):

    n_students = N_CLUSTERS*N_ROWS*N_SEATS

    #Leemos el fichero de instancia para guardarlo como un Dataframe
    try:
        instance = pd.read_csv(PATH_INSTANCE)
        instance["ID"] = pd.to_numeric(instance["ID"],downcast="integer")
        instance = instance.set_index("ID")
    except:
        raise ValueError(f"No se ha podido leer la instancia, formato incorrecto.")
    
    #Leemos el fichero de la solución para guardarlo como un Dataframe
    try:
        solution = pd.read_csv(file_solution)
        solution["ID"] = pd.to_numeric(solution["ID"],downcast="integer")
        solution = solution.set_index("ID")
    except:
        raise ValueError(f"No se ha podido leer la solucion, formato incorrecto.")

    #Validar que no haya estudiantes duplicados
    if solution.index.duplicated().any():
        raise ValueError("Estudiantes repetidos en la solución.")
    
    #Validar que no haya localizaciones duplicadas
    if solution["Location"].duplicated().any():
        raise ValueError("Localizaciones repetidas en la solución.")

    #Accesos rápidos
    values = instance.to_numpy()
    student_ids = instance.index.to_numpy()

    #Hallar localizaciones de todos los estudiantes y guardarlos en cache
    try:
        seats = solution["Location"].str.extract(r'c(?P<c>\d+)r(?P<r>\d+)s(?P<s>\d+)').astype(int)
        seat_cache = dict(zip(solution.index, zip(seats["c"], seats["r"], seats["s"])))
    except:
        raise ValueError("Error al parsear las localizaciones en la solución.")

    #Crear heatmap vacío si es necesario
    heat_arr = np.empty((n_students, 4), dtype=np.int32)

    #Bucle principal
    total_points = 0
    for i in range(n_students):
        sid = student_ids[i]
        pc, pr, ps, other_id_1, other_id_2 = values[i]

        try:
            c, r, s = seat_cache[sid]
        except:
            raise ValueError(f"Estudiante {sid} no encontrado en la solución.")

        #Validación de las localizaciones
        if not (1 <= c <= N_CLUSTERS and 1 <= r <= N_ROWS and 1 <= s <= N_SEATS):
            raise ValueError(f"Asiento no válido para el estudiante {sid}.")

        #Preferencias de cluster, fila y asiento
        points = int((pc > 0 and c == pc) or (pc < 0 and c != -pc)) + \
                int((pr > 0 and r == pr) or (pr < 0 and r != -pr)) + \
                int((ps > 0 and s == ps) or (ps < 0 and s != -ps))

        #Preferencia con respecto a otros estudiantes
        try:
            c_o1, r_o1, s_o1 = seat_cache[abs(other_id_1)]
        except:
            raise ValueError(f"Estudiante {abs(other_id_1)} no encontrado en la solución.")
        
        try:
            c_o2, r_o2, s_o2 = seat_cache[abs(other_id_2)]
        except:
            raise ValueError(f"Estudiante {abs(other_id_2)} no encontrado en la solución.")
            
        #Calcular distancia de manhattan entre estudiantes (si están en un cluster distinto, se consideran a distancia máxima)
        dist1 = (abs(r - r_o1) + abs(s - s_o1)) if c == c_o1 else MAX_RADIO
        dist2 = (abs(r - r_o2) + abs(s - s_o2)) if c == c_o2 else MAX_RADIO

        #La puntuación se calcula de forma proporcional a la distancia con respecto a los otros estudiantes
        #Se limita la mayor puntuación posible a MAX_RADIO-1
        points += (MAX_RADIO - min(dist1, MAX_RADIO))*int(other_id_1>0) + \
                (min(dist1, MAX_RADIO) - 1)*int(other_id_1<0) + \
                (MAX_RADIO - min(dist2, MAX_RADIO))*int(other_id_2>0) + \
                (min(dist2, MAX_RADIO) - 1)*int(other_id_2<0)
        
        total_points += points

        #Añadir información del estudiante actual al heatmap
        heat_arr[i] = (c, r, s, points)

    return total_points, pd.DataFrame(heat_arr, columns=["Cluster", "Row", "Column", "Points"])
