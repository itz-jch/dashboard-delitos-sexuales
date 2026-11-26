# Dashboard: Delitos sexuales reportados en Colombia

Dashboard interactivo en Python (Streamlit + Plotly) sobre el dataset público
«Reporte Delitos sexuales Policía Nacional» (fpe5-yrmw) de Datos Abiertos Colombia.

## Estructura
- `app.py`: código del dashboard.
- `requirements.txt`: librerías necesarias.
- `.streamlit/config.toml`: tema visual (claro).
- `data/delitos_sexuales_analisis.csv`: base de análisis generada por el notebook de limpieza.

## Ejecutar en el computador
```
pip install -r requirements.txt
streamlit run app.py
```

## Publicar con un enlace (Streamlit Community Cloud, gratis)
1. Sube esta carpeta a un repositorio público de GitHub.
2. Entra a https://share.streamlit.io con tu cuenta de GitHub.
3. Elige "Create app", selecciona el repositorio, la rama `main` y el archivo `app.py`, y pulsa "Deploy".
