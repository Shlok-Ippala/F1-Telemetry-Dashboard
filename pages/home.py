# In pages/home.py

print("--- Python is EXECUTING pages/home.py ---")

from dash import html, dcc

layout = html.Div([
    html.H1("🏎️ F1 Analytics Dashboard", style={'textAlign': 'center', 'marginTop': '50px'}),
    html.H3("Choose an analysis mode:", style={'textAlign': 'center', 'marginTop': '20px'}),
    html.Div([
        dcc.Link(
            html.Button('Lap Comparison', style={'width': '200px', 'height': '50px', 'fontSize': '18px'}),
            href='/lap-comparison'
        ),
        html.Br(),
        html.Br(),
        dcc.Link(
            html.Button('Race Comparison', style={'width': '200px', 'height': '50px', 'fontSize': '18px'}),
            href='/race-comparison'
        ),
    ], style={'textAlign': 'center', 'marginTop': '30px'})
])