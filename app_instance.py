# In app_instance.py
#print("--- PYTHON IS EXECUTING THE app_instance.py FILE ---")
import dash
import dash_bootstrap_components as dbc

# This is the central app object that other modules will import
app = dash.Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.CYBORG])
app.title = "F1 Analytics Dashboard"
server = app.server