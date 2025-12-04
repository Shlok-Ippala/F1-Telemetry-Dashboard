# In pages/home.py

print("--- Python is EXECUTING pages/home.py ---")

from dash import html, dcc

layout = html.Div([
    html.H1("🏎️ F1 Analytics Dashboard", style={'textAlign': 'center', 'marginTop': '50px'}),
    html.H3("Choose an analysis mode:", style={'textAlign': 'center', 'marginTop': '20px'}),
    html.Div([
        dcc.Link(
            html.Button('Qualifying Analysis', style={'width': '200px', 'height': '50px', 'fontSize': '18px'}),
            href='/lap-comparison'
        ),
        html.Br(),
        html.Br(),
        dcc.Link(
            html.Button('Weekend Analysis', style={'width': '200px', 'height': '50px', 'fontSize': '18px'}),
            href='/race-comparison'
        ),
        html.Br(),
        html.Br(),
        dcc.Link(
            html.Button('Year Analysis', style={'width': '200px', 'height': '50px', 'fontSize': '18px'}),
            href='/year-analysis'
        ),
    ], style={'textAlign': 'center', 'marginTop': '30px'})
])