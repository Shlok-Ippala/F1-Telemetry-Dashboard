# In pages/lap_comparison.py

from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc  # Import dbc
import fastf1
from fastf1 import plotting
import plotly.graph_objects as go
import pandas as pd

from app_instance import app

# --- Reusable Navbar Component ---
# You can move this to a separate file and import it on every page
navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Lap Comparison", href="/lap-comparison")),
        dbc.NavItem(dbc.NavLink("Race Comparison", href="/race-comparison")),
    ],
    brand="🏎️ F1 Analytics Dashboard",
    brand_href="/",
    color="primary",
    dark=True,
    className="mb-4" # Margin bottom 4
)


# --- Dropdown options ---
years = [2021, 2022, 2023, 2024]
metrics = ['Speed', 'Throttle', 'Brake', 'RPM', 'nGear']

# --- Define the Controls Panel ---
controls = dbc.Card(
    [
        dbc.Row([
            dbc.Col(dbc.Label("Select Year"), width=12),
            dbc.Col(dcc.Dropdown(years, 2024, id='year-dropdown'), width=12),
        ], className="mb-3"), # Margin bottom 3

        dbc.Row([
            dbc.Col(dbc.Label("Select Race"), width=12),
            dbc.Col(dcc.Dropdown(id='race-dropdown', placeholder="Select a Grand Prix"), width=12),
        ], className="mb-3"),

        dbc.Row([
            dbc.Col(dbc.Label("Select Driver(s)"), width=12),
            dbc.Col(dcc.Dropdown(id='driver-dropdown', multi=True, placeholder="Select driver(s)"), width=12),
        ], className="mb-3"),

        dbc.Row([
            dbc.Col(dbc.Label("Select Metric"), width=12),
            dbc.Col(dcc.Dropdown(metrics, 'Speed', id='metric-dropdown'), width=12),
        ], className="mb-3"),

        dbc.Button('Sketch Graph', id='sketch-button', n_clicks=0, color="primary", className="w-100")
    ],
    body=True,
)

# --- Define the main layout for this page using dbc grid system ---
layout = html.Div([
    navbar,
    dbc.Container([
        dbc.Row([
            # Column for the controls
            dbc.Col([
                html.H3("Telemetry Controls"),
                controls
            ], md=4), # On medium screens and up, this column takes 4/12 of the width

            # Column for the graph
            dbc.Col([
                dcc.Loading(
                    id="loading-graph",
                    type="default",
                    children=dcc.Graph(id='telemetry-graph', style={'height': '80vh'})
                )
            ], md=8) # On medium screens and up, this takes the remaining 8/12
        ])
    ], fluid=True)
])

# --- ALL YOUR CALLBACKS GO HERE, UNCHANGED ---
# Note: The @app.callback decorator now refers to the 'app' we imported.

@app.callback(
    Output('race-dropdown', 'options'),
    Input('year-dropdown', 'value')
)
def update_race_options(selected_year):
    if not selected_year:
        return []
    schedule = fastf1.get_event_schedule(selected_year)
    races = schedule['EventName'].tolist()
    return [{'label': r, 'value': r} for r in races]

@app.callback(
    Output('driver-dropdown', 'options'),
    Input('race-dropdown', 'value'),
    Input('year-dropdown', 'value')
)
def update_driver_options(selected_race, selected_year):
    if not selected_race or not selected_year:
        return []
    try:
        session = fastf1.get_session(selected_year, selected_race, 'R')
        session.load(laps=True, telemetry=False, weather=False, messages=False)
        drivers = session.drivers
        driver_abbreviations = [session.get_driver(d)['Abbreviation'] for d in drivers]
        return [{'label': d, 'value': d} for d in driver_abbreviations]
    except Exception as e:
        print(f"Error loading session for driver options: {e}")
        return []

@app.callback(
    Output('telemetry-graph', 'figure'),
    Input('sketch-button', 'n_clicks'),
    State('driver-dropdown', 'value'),
    State('year-dropdown', 'value'),
    State('race-dropdown', 'value'),
    State('metric-dropdown', 'value')
)
def update_graph(n_clicks, drivers, year, race, metric):
    if n_clicks is None or n_clicks == 0:
        fig = go.Figure()
        fig.update_layout(title="Select filters and click 'Sketch Graph' to display telemetry data")
        return fig
    if not drivers or not race or not year:
        fig = go.Figure()
        fig.update_layout(title="Please select Year, Race, and at least one Driver to sketch the graph.")
        return fig
    plotting.setup_mpl()
    try:
        session = fastf1.get_session(year, race, 'R')
        session.load(laps=True, telemetry=True, weather=True, messages=True)
        fig = go.Figure()
        team_color_used_solid = {}
        for d_abbr in drivers:
            driver_data = session.get_driver(d_abbr)
            if driver_data is None: continue
            team = driver_data['TeamName']
            color = plotting.get_team_color(team, session)
            laps = session.laps.pick_drivers(d_abbr)
            if laps.empty: continue
            fastest = laps.pick_fastest()
            if fastest.empty: continue
            telemetry = fastest.get_telemetry()
            if metric not in telemetry.columns: continue
            line_dash = 'solid'
            if team in team_color_used_solid: line_dash = 'dash'
            else: team_color_used_solid[team] = True
            fig.add_trace(go.Scatter(
                x=telemetry['Distance'],
                y=telemetry[metric],
                mode='lines',
                name=f"{d_abbr} ({team})",
                line=dict(color=color, dash=line_dash, width=2)
            ))
        fig.update_layout(
            title=f"{metric} Comparison - {race} {year}",
            xaxis_title='Distance (m)',
            yaxis_title=metric,
            legend_title="Driver (Team)",
            showlegend=True
        )
        return fig
    except Exception as e:
        print(f"Error generating graph: {e}")
        fig = go.Figure()
        fig.update_layout(title=f"Error sketching graph: {e}")
        return fig