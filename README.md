# Predicción de Siniestros Viales en Argentina 🚗📊

Este repositorio contiene el proyecto final para la asignatura **Programación Avanzada para Ciencias de Datos** (Licenciatura en Ciencias de Datos - Universidad de la Ciudad de Buenos Aires). 

El objetivo principal de este proyecto es construir un pipeline de Machine Learning capaz de predecir el volumen diario de víctimas de siniestros viales en Argentina, transformando un dataset de registros individuales en un modelo de regresión de series temporales.

## 👥 Integrantes del Equipo
* Damián Jorge Cordero
* Luis Eduardo Santillán Cruz
* Ricardo Alberto Ureña

## 🛠️ Tecnologías y Herramientas Utilizadas
* **Python 3.13.7**
* **Pandas & NumPy:** Limpieza, agrupación temporal (GroupBy) y Feature Engineering.
* **Scikit-Learn:** Creación de Pipelines, escalado (StandardScaler) y entrenamiento de modelos (Random Forest y Gradient Boosting).
* **Plotly:** Visualización interactiva de métricas y evaluación de modelos.
* **MongoDB Atlas:** Base de datos NoSQL en la nube para persistencia de datos procesados, configuración del pipeline y resultados.

## 📂 Estructura del Repositorio
* `TP_Final_Siniestros.ipynb`: Cuaderno interactivo (Jupyter/Colab) con la exploración de datos, explicaciones paso a paso y visualización de gráficos.
* `main.py`: Script de producción puro con el pipeline de machine learning para ejecución en consola o automatización.
* `siniestros_viales_victimas.xlsx`: Dataset original utilizado para el preprocesamiento.
* `requirements.txt`: Dependencias y librerías necesarias.

## ⚙️ Estructura del Script
El archivo principal (`main.py`) ejecuta el flujo completo de forma secuencial:
1. **Extracción y Transformación:** Carga el archivo `.xlsx`, maneja valores nulos y agrupa los datos temporalmente por día.
2. **Feature Engineering:** Extrae variables numéricas (Año, Mes, Día, Día de la Semana).
3. **Modelado:** Entrena y evalúa los algoritmos utilizando Pipelines para evitar el *Data Leakage*.
4. **Carga en Base de Datos:** Exporta el dataset preprocesado, las configuraciones y las predicciones a un cluster de MongoDB Atlas.
5. **Visualización:** Despliega gráficos interactivos para el análisis de los resultados (R², MAE, RMSE).

## 🚀 Cómo ejecutar el proyecto

1. **Clonar el repositorio:**
   ```bash
   git clone <URL_DEL_REPOSITORIO>
   cd <NOMBRE_DE_LA_CARPETA>
   ```

2. **Instalar las dependencias:**
   Se recomienda utilizar un entorno virtual.

   ```bash
   pip install -r requirements.txt
   ```

3. **Ejecutar el pipeline:**
   Asegúrese de tener el archivo siniestros_viales_victimas.xlsx en el mismo directorio.

   ```bash
   python main.py
   ```

Nota: Si se evalúa el proyecto utilizando el botón 'Open in Colab', recuerde subir manualmente el archivo siniestros_viales_victimas.xlsx al entorno de ejecución antes de correr las celdas.
