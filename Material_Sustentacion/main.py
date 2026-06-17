import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from pymongo import MongoClient
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

# ==========================================
# 1. CARGA Y PREPROCESAMIENTO DE DATOS
# ==========================================

# Cargar el dataset (ajusta la ruta según corresponda)
df = pd.read_excel('siniestros_viales_victimas.xlsx', sheet_name='VICTIMAS')
# Convertir la fecha a formato datetime
df['fecha_siniestro'] = pd.to_datetime(df['fecha_siniestro'], errors='coerce')

# Agrupar los datos por día para contar la cantidad de víctimas (nuestro target continuo)
df_diario = df.groupby('fecha_siniestro').size().reset_index(name='cantidad_victimas')

# Ingeniería de características temporales
df_diario['año'] = df_diario['fecha_siniestro'].dt.year
df_diario['mes'] = df_diario['fecha_siniestro'].dt.month
df_diario['dia'] = df_diario['fecha_siniestro'].dt.day
df_diario['dia_semana'] = df_diario['fecha_siniestro'].dt.dayofweek

# Separar características (X) y variable objetivo (y)
X = df_diario[['año', 'mes', 'dia', 'dia_semana']]
y = df_diario['cantidad_victimas']

# División en conjuntos de entrenamiento y prueba (80/20)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# ==========================================
# 2. CONSTRUCCIÓN DE MODELOS CON PIPELINES
# ==========================================

# Definir algoritmos a comparar
pipelines = {
    'RandomForest': Pipeline([
        ('scaler', StandardScaler()),
        ('regressor', RandomForestRegressor(n_estimators=100, random_state=42))
    ]),
    'GradientBoosting': Pipeline([
        ('scaler', StandardScaler()),
        ('regressor', GradientBoostingRegressor(n_estimators=100, learning_rate=0.1, random_state=42))
    ])
}

# ==========================================
# 3. ENTRENAMIENTO MÚLTIPLE Y EVALUACIÓN
# ==========================================

resultados_metricas = {}
predicciones_guardar = []

# Definimos 3 semillas aleatorias para entrenar los modelos 3 veces
semillas = [42, 100, 999] 

for nombre_modelo, pipeline in pipelines.items():
    print(f"\n--- Evaluando {nombre_modelo} ---")
    
    rmse_scores = []
    mae_scores = []
    r2_scores = []
    
    # Entrenamos el mismo modelo 3 veces, cambiando la semilla
    for semilla in semillas:
        # 1. Cambiamos la semilla del modelo dentro del pipeline
        pipeline.named_steps['regressor'].set_params(random_state=semilla)
        
        # 2. Entrenamos
        pipeline.fit(X_train, y_train)
        
        # 3. Predecimos
        y_pred = pipeline.predict(X_test)
        
        # 4. Calculamos métricas de esta iteración
        rmse_scores.append(np.sqrt(mean_squared_error(y_test, y_pred)))
        mae_scores.append(mean_absolute_error(y_test, y_pred))
        r2_scores.append(r2_score(y_test, y_pred))
        
        # Imprimimos el resultado de cada "vuelta"
        print(f"Vuelta con semilla {semilla}: R2 = {r2_scores[-1]:.4f}")
        
        # Guardamos las predicciones de la ÚLTIMA vuelta para la base de datos
        if semilla == semillas[-1]: 
            pred_df = X_test.copy()
            pred_df['valor_real'] = y_test.values
            pred_df['valor_predicho'] = y_pred
            pred_df['modelo'] = nombre_modelo
            predicciones_guardar.extend(pred_df.to_dict('records'))

    # Calculamos el PROMEDIO de las 3 corridas
    rmse_promedio = np.mean(rmse_scores)
    mae_promedio = np.mean(mae_scores)
    r2_promedio = np.mean(r2_scores)
    
    resultados_metricas[nombre_modelo] = {
        'RMSE': rmse_promedio,
        'MAE': mae_promedio,
        'R2': r2_promedio
    }
    
    print(f">> RESULTADO PROMEDIO (3 iteraciones): RMSE: {rmse_promedio:.4f} | MAE: {mae_promedio:.4f} | R2: {r2_promedio:.4f}")

# ==========================================
# 4. ALMACENAMIENTO EN BASE DE DATOS NOSQL (MONGODB)
# ==========================================

URI = "mongodb+srv://usuario:contraseña@cluster0.knsflmx.mongodb.net/?appName=Cluster0"

try:
    # 1. Creamos la conexión (El Cliente)
    client = MongoClient(URI)
    
    # 2. Apuntamos a la Base de Datos (Database)
    db = client['siniestros_viales_arg']
    
    # 3. Apuntamos a las Colecciones (Tablas NoSQL)
    col_entrada = db['datos_entrada']
    col_resultados = db['resultados_modelo']
    col_config = db['configuracion_modelo']
    
    # Limpiamos solo las colecciones para evitar duplicados al correr pruebas
    col_entrada.drop()
    col_resultados.drop()
    col_config.drop()
    
    # 4.1 Insertar Tabla de Datos de Entrada (Preprocesados)
    df_diario_str = df_diario.copy()
    df_diario_str['fecha_siniestro'] = df_diario_str['fecha_siniestro'].dt.strftime('%Y-%m-%d')
    col_entrada.insert_many(df_diario_str.to_dict('records'))
    
    # 4.2 Insertar Tabla de Resultados del Modelo (Métricas y Predicciones)
    col_resultados.insert_one({
        "metricas_comparativas": resultados_metricas,
        "detalle_predicciones": predicciones_guardar
    })
    
    # 4.3 Insertar Tabla de Configuración/Parametrización
    config_docs = []
    for nombre_modelo, pipeline in pipelines.items():
        config_docs.append({
            "modelo": nombre_modelo,
            "etapas_pipeline": list(pipeline.named_steps.keys()),
            "parametros": pipeline.named_steps['regressor'].get_params()
        })
    col_config.insert_many(config_docs)
    
    print("¡Exito! Los datos de entrada, los resultados predictivos y la configuración han sido guardados en MongoDB.")

except Exception as e:
    print(f"Error al conectar o guardar en MongoDB: {e}")

# ==========================================
# 5. VISUALIZACIÓN DE RESULTADOS CON PLOTLY
# ==========================================

# --- Gráfico 1: Comparativa de Métricas (Bar Chart) ---
# Convertimos el diccionario 'resultados_metricas' (del paso 3) a un DataFrame
df_metricas = pd.DataFrame(resultados_metricas).T.reset_index()
df_metricas.rename(columns={'index': 'Modelo'}, inplace=True)

# Reestructuramos la tabla para el gráfico agrupado
df_metricas_melt = df_metricas.melt(id_vars='Modelo', var_name='Métrica', value_name='Valor')

fig_metricas = px.bar(df_metricas_melt, x='Métrica', y='Valor', color='Modelo', 
                      barmode='group', text_auto='.2f',
                      title='Comparación de Rendimiento: Random Forest vs Gradient Boosting',
                      labels={'Valor': 'Puntuación', 'Métrica': 'Métrica'})

fig_metricas.update_layout(plot_bgcolor='rgba(0,0,0,0)')
fig_metricas.show()

# --- Gráfico 2: Valores Reales vs Predichos (Line/Scatter Chart) ---
# Levantamos la lista de predicciones que armamos en el paso 3
df_pred = pd.DataFrame(predicciones_guardar)

# Filtramos solo los resultados de un modelo (ej: RandomForest) para no saturar visualmente
df_pred_rf = df_pred[df_pred['modelo'] == 'RandomForest'].copy()

# Como el train_test_split mezcló los datos, los volvemos a ordenar cronológicamente
df_pred_rf = df_pred_rf.sort_values(by=['año', 'mes', 'dia'])

# Creamos una columna de fecha en formato string para el eje X
df_pred_rf['fecha_str'] = df_pred_rf['año'].astype(str) + '-' + \
                          df_pred_rf['mes'].astype(str).str.zfill(2) + '-' + \
                          df_pred_rf['dia'].astype(str).str.zfill(2)

fig_pred = go.Figure()

# Línea de valores reales
fig_pred.add_trace(go.Scatter(x=df_pred_rf['fecha_str'], y=df_pred_rf['valor_real'], 
                              mode='lines+markers', name='Víctimas Reales',
                              line=dict(color='crimson', width=2)))

# Línea de predicción del algoritmo
fig_pred.add_trace(go.Scatter(x=df_pred_rf['fecha_str'], y=df_pred_rf['valor_predicho'], 
                              mode='lines+markers', name='Predicción (RF)',
                              line=dict(color='royalblue', width=2, dash='dot')))

fig_pred.update_layout(title='Accidentes Diarios (Datos de Prueba): Realidad vs Modelo Predictivo',
                       xaxis_title='Fecha del Siniestro',
                       yaxis_title='Volumen de Víctimas',
                       hovermode="x unified",
                       plot_bgcolor='rgba(0,0,0,0)')
fig_pred.show()

# --- Gráfico 3: Importancia de Variables (Feature Importance) ---
# Extraemos el modelo entrenado del pipeline de Random Forest
modelo_rf = pipelines['RandomForest'].named_steps['regressor']
importancias = modelo_rf.feature_importances_
nombres_variables = ['Año', 'Mes', 'Día', 'Día de la Semana']

df_importancia = pd.DataFrame({
    'Variable': nombres_variables,
    'Importancia': importancias
}).sort_values(by='Importancia', ascending=True) # Ordenado para gráfico de barras horizontal

fig_importancia = px.bar(df_importancia, x='Importancia', y='Variable', orientation='h',
                         title='¿Qué factores impactan más en los siniestros viales? (Importancia de Variables)',
                         text_auto='.2%', color='Importancia', color_continuous_scale='Blues')

fig_importancia.update_layout(plot_bgcolor='rgba(0,0,0,0)', showlegend=False)
fig_importancia.show()

# --- Gráfico 4: Dispersión de Errores (Real vs Predicho) ---
fig_dispersion = go.Figure()

# Puntos de dispersión
fig_dispersion.add_trace(go.Scatter(
    x=df_pred_rf['valor_real'], 
    y=df_pred_rf['valor_predicho'], 
    mode='markers',
    marker=dict(color='purple', size=8, opacity=0.6),
    name='Predicciones'
))

# Línea diagonal de "Predicción Perfecta" (donde el real es exactamente igual al predicho)
val_max = max(df_pred_rf['valor_real'].max(), df_pred_rf['valor_predicho'].max())
fig_dispersion.add_trace(go.Scatter(
    x=[0, val_max], y=[0, val_max],
    mode='lines',
    line=dict(color='gray', dash='dash'),
    name='Modelo Ideal (Error Cero)'
))

fig_dispersion.update_layout(
    title='Rendimiento del Modelo: Dispersión de Errores',
    xaxis_title='Cantidad REAL de Víctimas',
    yaxis_title='Cantidad PREDICHA por el Modelo',
    plot_bgcolor='rgba(0,0,0,0)'
)
fig_dispersion.show()