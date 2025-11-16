# In pages/race_comparison.py
from dash import html, dcc

layout = html.Div([
    html.H1("Race Comparison"),
    html.Hr(),
    html.P("This feature is under construction."),
    dcc.Link("Go back to Home", href="/")
])