# In pages/race_comparison.py

from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash_iconify import DashIconify
import fastf1
from fastf1 import plotting
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from app_instance import app


# --- Flag icon mapping for Grand Prix (using Iconify flag icons) ---
RACE_FLAG_ICONS = {
    'bahrain': 'circle-flags:bh',
    'saudi': 'circle-flags:sa',
    'jeddah': 'circle-flags:sa',
    'australia': 'circle-flags:au',
    'melbourne': 'circle-flags:au',
    'japan': 'circle-flags:jp',
    'suzuka': 'circle-flags:jp',
    'china': 'circle-flags:cn',
    'shanghai': 'circle-flags:cn',
    'miami': 'circle-flags:us',
    'emilia': 'circle-flags:it',
    'imola': 'circle-flags:it',
    'monaco': 'circle-flags:mc',
    'canada': 'circle-flags:ca',
    'montreal': 'circle-flags:ca',
    'spain': 'circle-flags:es',
    'barcelona': 'circle-flags:es',
    'austria': 'circle-flags:at',
    'spielberg': 'circle-flags:at',
    'britain': 'circle-flags:gb',
    'british': 'circle-flags:gb',
    'silverstone': 'circle-flags:gb',
    'hungary': 'circle-flags:hu',
    'budapest': 'circle-flags:hu',
    'hungaroring': 'circle-flags:hu',
    'belgium': 'circle-flags:be',
    'spa': 'circle-flags:be',
    'netherlands': 'circle-flags:nl',
    'dutch': 'circle-flags:nl',
    'zandvoort': 'circle-flags:nl',
    'italy': 'circle-flags:it',
    'monza': 'circle-flags:it',
    'italian': 'circle-flags:it',
    'azerbaijan': 'circle-flags:az',
    'baku': 'circle-flags:az',
    'singapore': 'circle-flags:sg',
    'marina bay': 'circle-flags:sg',
    'united states': 'circle-flags:us',
    'austin': 'circle-flags:us',
    'cota': 'circle-flags:us',
    'americas': 'circle-flags:us',
    'mexico': 'circle-flags:mx',
    'brazilian': 'circle-flags:br',
    'brazil': 'circle-flags:br',
    'sao paulo': 'circle-flags:br',
    'são paulo': 'circle-flags:br',
    'paulo': 'circle-flags:br',
    'interlagos': 'circle-flags:br',
    'las vegas': 'circle-flags:us',
    'vegas': 'circle-flags:us',
    'qatar': 'circle-flags:qa',
    'losail': 'circle-flags:qa',
    'abu dhabi': 'circle-flags:ae',
    'yas marina': 'circle-flags:ae',
    'portugal': 'circle-flags:pt',
    'portimao': 'circle-flags:pt',
    'turkey': 'circle-flags:tr',
    'istanbul': 'circle-flags:tr',
    'styria': 'circle-flags:at',
    'eifel': 'circle-flags:de',
    'nurburgring': 'circle-flags:de',
    'russia': 'circle-flags:ru',
    'sochi': 'circle-flags:ru',
    'tuscany': 'circle-flags:it',
    'mugello': 'circle-flags:it',
    'sakhir': 'circle-flags:bh',
    'france': 'circle-flags:fr',
    'french': 'circle-flags:fr',
    'paul ricard': 'circle-flags:fr',
    'korean': 'circle-flags:kr',
    'korea': 'circle-flags:kr',
    'indian': 'circle-flags:in',
    'india': 'circle-flags:in',
    'german': 'circle-flags:de',
    'germany': 'circle-flags:de',
    'hockenheim': 'circle-flags:de',
    'malaysian': 'circle-flags:my',
    'malaysia': 'circle-flags:my',
    'sepang': 'circle-flags:my',
    'pre-season': 'circle-flags:bh',
    'testing': 'circle-flags:bh',
}

def get_race_flag_icon(race_name):
    """Get the flag icon identifier for a race based on its name."""
    race_lower = race_name.lower()
    for keyword, icon in RACE_FLAG_ICONS.items():
        if keyword in race_lower:
            return icon
    return 'circle-flags:xx'


# --- Reusable Navbar Component ---
navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Qualifying Analysis", href="/lap-comparison")),
        dbc.NavItem(dbc.NavLink("Weekend Analysis", href="/race-comparison")),
        dbc.NavItem(dbc.NavLink("Year Analysis", href="/year-analysis")),
    ],
    brand="F1 Analytics Dashboard",
    brand_href="/",
    color="primary",
    dark=True,
    className="mb-4"
)

# --- Dropdown options ---
years = [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]
chart_types = ['Lap Times', 'Box Plot', 'Violin Plot', 'Aero Performance']


# --- Page Header ---
page_header = html.Div([
    html.H2("Weekend Analysis", className="page-title"),
    html.P("Analyze race lap times, tire strategies, and team aero performance", className="page-subtitle")
], className="page-header")

# --- Empty State for Graph ---
empty_state = html.Div([
    html.H4("No Data Selected", className="empty-state-title"),
    html.P("Select a year, race, session, and drivers, then click 'Sketch Graph' to visualize", className="empty-state-text")
], className="graph-empty-state", id="race-graph-empty-state")

# --- Define the Controls Panel ---
controls = dbc.Card(
    [
        # Session Selection Section
        html.Div([
            dbc.Row([
                dbc.Col(html.Label("Year", className="control-label"), width=12),
                dbc.Col(dcc.Dropdown(years, 2025, id='race-year-dropdown', clearable=False), width=12),
            ], className="mb-3"),

            dbc.Row([
                dbc.Col(html.Label("Grand Prix", className="control-label"), width=12),
                dbc.Col(
                    html.Div([
                        dcc.Store(id='race-event-options-store', data=[]),
                        dmc.Select(
                            id='race-event-dropdown',
                            placeholder="Select a Grand Prix",
                            searchable=True,
                            nothingFoundMessage="No races found",
                            leftSection=html.Img(
                                id="race-event-flag-icon",
                                src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='20' height='15' viewBox='0 0 20 15'%3E%3Crect fill='%23fff' width='20' height='15'/%3E%3Cg fill='%23000'%3E%3Crect x='0' y='0' width='4' height='3'/%3E%3Crect x='8' y='0' width='4' height='3'/%3E%3Crect x='16' y='0' width='4' height='3'/%3E%3Crect x='4' y='3' width='4' height='3'/%3E%3Crect x='12' y='3' width='4' height='3'/%3E%3Crect x='0' y='6' width='4' height='3'/%3E%3Crect x='8' y='6' width='4' height='3'/%3E%3Crect x='16' y='6' width='4' height='3'/%3E%3Crect x='4' y='9' width='4' height='3'/%3E%3Crect x='12' y='9' width='4' height='3'/%3E%3Crect x='0' y='12' width='4' height='3'/%3E%3Crect x='8' y='12' width='4' height='3'/%3E%3Crect x='16' y='12' width='4' height='3'/%3E%3C/g%3E%3C/svg%3E",
                                width=20,
                                height=15,
                                style={"borderRadius": "2px"}
                            ),
                            styles={
                                "input": {"backgroundColor": "#000", "borderColor": "rgba(255,255,255,0.2)", "color": "white"},
                                "dropdown": {"backgroundColor": "#000", "borderColor": "rgba(255,255,255,0.2)"},
                            },
                            className="mantine-select-dark"
                        ),
                    ]),
                    width=12
                ),
            ], className="mb-3"),

            dbc.Row([
                dbc.Col(html.Label("Session", className="control-label"), width=12),
                dbc.Col(
                    dcc.Loading(
                        id="loading-session",
                        type="default",
                        children=dcc.Dropdown(id='race-session-dropdown', placeholder="Select a session"),
                        fullscreen=False,
                        style={'minHeight': '38px'}
                    ), width=12
                ),
            ]),
        ], className="control-section"),

        # Chart Type Section
        html.Div([
            dbc.Row([
                dbc.Col(html.Label("Chart Type", className="control-label"), width=12),
                dbc.Col(dcc.Dropdown(chart_types, 'Lap Times', id='race-chart-dropdown', clearable=False), width=12),
            ]),
        ], className="control-section"),

        # Dynamic driver/team selection section
        html.Div([
            html.Div(id='driver-team-selection-container', children=[
                dbc.Row([
                    dbc.Col(html.Label("Drivers", className="control-label", id='driver-team-label'), width=12),
                    dbc.Col(
                        dcc.Loading(
                            id="loading-race-drivers",
                            type="default",
                            children=dcc.Dropdown(id='race-driver-dropdown', multi=True, placeholder="Select driver(s)"),
                            fullscreen=False,
                            style={'minHeight': '38px'}
                        ), width=12
                    ),
                    dbc.Col(html.Div(id='race-driver-tags-display', style={'marginTop': '8px'}), width=12),
                ]),
            ]),

            # Hidden team dropdown (shown when Aero Performance is selected)
            html.Div(id='team-selection-container', children=[
                dbc.Row([
                    dbc.Col(html.Label("Teams", className="control-label"), width=12),
                    dbc.Col(
                        dcc.Loading(
                            id="loading-race-teams",
                            type="default",
                            children=dcc.Dropdown(id='race-team-dropdown', multi=True, placeholder="Select team(s)"),
                            fullscreen=False,
                            style={'minHeight': '38px'}
                        ), width=12
                    ),
                    dbc.Col(html.Div(id='race-team-tags-display', style={'marginTop': '8px'}), width=12),
                ]),
            ], style={'display': 'none'}),
        ], className="control-section"),

        dbc.Button('Sketch Graph', id='race-sketch-button', n_clicks=0, color="primary", className="w-100 mt-2"),
        
        # Store for driver-team color mapping
        dcc.Store(id='race-driver-colors-store', data={}),
        dcc.Store(id='race-team-colors-store', data={})
    ],
    body=True,
    className="transparent-card"
)

# --- Define the main layout for this page ---
layout = html.Div([
    navbar,
    dbc.Container([
        dbc.Row([
            # Column for the controls
            dbc.Col([
                page_header,
                controls
            ], md=4),

            # Column for the graph
            dbc.Col([
                html.Div(id='race-graph-container', children=[
                    empty_state,
                    dcc.Loading(
                        id="race-loading-graph",
                        type="default",
                        children=dcc.Graph(id='race-graph', style={'height': '80vh', 'display': 'none'})
                    )
                ])
            ], md=8)
        ])
    ], fluid=True)
])

# --- CALLBACKS ---

@app.callback(
    Output('race-event-dropdown', 'data'),
    Output('race-event-options-store', 'data'),
    Input('race-year-dropdown', 'value')
)
def update_race_options(selected_year):
    if not selected_year:
        return [], []
    schedule = fastf1.get_event_schedule(selected_year)
    races = schedule['EventName'].tolist()
    options = [{'label': r, 'value': r} for r in races]
    return options, options


# Checkered flag SVG data URI for default/unselected state
CHECKERED_FLAG_SVG = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='20' height='15' viewBox='0 0 20 15'%3E%3Crect fill='%23fff' width='20' height='15'/%3E%3Cg fill='%23000'%3E%3Crect x='0' y='0' width='4' height='3'/%3E%3Crect x='8' y='0' width='4' height='3'/%3E%3Crect x='16' y='0' width='4' height='3'/%3E%3Crect x='4' y='3' width='4' height='3'/%3E%3Crect x='12' y='3' width='4' height='3'/%3E%3Crect x='0' y='6' width='4' height='3'/%3E%3Crect x='8' y='6' width='4' height='3'/%3E%3Crect x='16' y='6' width='4' height='3'/%3E%3Crect x='4' y='9' width='4' height='3'/%3E%3Crect x='12' y='9' width='4' height='3'/%3E%3Crect x='0' y='12' width='4' height='3'/%3E%3Crect x='8' y='12' width='4' height='3'/%3E%3Crect x='16' y='12' width='4' height='3'/%3E%3C/g%3E%3C/svg%3E"

@app.callback(
    Output('race-event-flag-icon', 'src'),
    Input('race-event-dropdown', 'value')
)
def update_race_event_flag(selected_race):
    """Update the flag image when a race is selected."""
    if not selected_race:
        return CHECKERED_FLAG_SVG
    
    # Get the country code from the race name
    country_code = get_flag_country_code(selected_race)
    return f"https://flagcdn.com/w20/{country_code}.png"


# Country code mapping for FlagCDN
FLAG_COUNTRY_CODES = {
    'bahrain': 'bh',
    'saudi': 'sa',
    'jeddah': 'sa',
    'australia': 'au',
    'australian': 'au',
    'japan': 'jp',
    'japanese': 'jp',
    'china': 'cn',
    'chinese': 'cn',
    'miami': 'us',
    'emilia': 'it',
    'imola': 'it',
    'monaco': 'mc',
    'canada': 'ca',
    'canadian': 'ca',
    'spain': 'es',
    'spanish': 'es',
    'austria': 'at',
    'austrian': 'at',
    'britain': 'gb',
    'british': 'gb',
    'hungary': 'hu',
    'hungarian': 'hu',
    'belgium': 'be',
    'belgian': 'be',
    'spa': 'be',
    'netherlands': 'nl',
    'dutch': 'nl',
    'italy': 'it',
    'italian': 'it',
    'monza': 'it',
    'azerbaijan': 'az',
    'baku': 'az',
    'singapore': 'sg',
    'united states': 'us',
    'americas': 'us',
    'mexico': 'mx',
    'mexican': 'mx',
    'brazil': 'br',
    'brazilian': 'br',
    'paulo': 'br',
    'las vegas': 'us',
    'vegas': 'us',
    'qatar': 'qa',
    'abu dhabi': 'ae',
    'portugal': 'pt',
    'turkish': 'tr',
    'turkey': 'tr',
    'styria': 'at',
    'eifel': 'de',
    'russia': 'ru',
    'russian': 'ru',
    'sochi': 'ru',
    'tuscany': 'it',
    'tuscan': 'it',
    'sakhir': 'bh',
    'france': 'fr',
    'french': 'fr',
    'german': 'de',
    'germany': 'de',
    'malaysia': 'my',
    'malaysian': 'my',
    'korea': 'kr',
    'korean': 'kr',
    'india': 'in',
    'indian': 'in',
    'pre-season': 'bh',
    'testing': 'bh',
}

def get_flag_country_code(race_name):
    """Get the 2-letter country code for FlagCDN."""
    race_lower = race_name.lower()
    for keyword, code in FLAG_COUNTRY_CODES.items():
        if keyword in race_lower:
            return code
    return 'xx'  # Unknown flag


@app.callback(
    Output('race-session-dropdown', 'options'),
    Output('race-session-dropdown', 'value'),
    Input('race-event-dropdown', 'value'),
    Input('race-year-dropdown', 'value')
)
def update_session_options(selected_race, selected_year):
    if not selected_race or not selected_year:
        return [], None
    try:
        # Get the event schedule to check if it's a sprint weekend
        schedule = fastf1.get_event_schedule(selected_year)
        event = schedule[schedule['EventName'] == selected_race]
        
        if event.empty:
            return [], None
        
        # Check if it's a sprint weekend by looking at EventFormat
        event_format = event['EventFormat'].values[0]
        is_sprint = 'sprint' in str(event_format).lower()
        
        if is_sprint:
            # Sprint weekend: FP1, Sprint, Race
            options = [
                {'label': 'Free Practice 1', 'value': 'FP1'},
                {'label': 'Sprint', 'value': 'S'},
                {'label': 'Race', 'value': 'R'},
            ]
        else:
            # Normal weekend: FP1, FP2, FP3, Race
            options = [
                {'label': 'Free Practice 1', 'value': 'FP1'},
                {'label': 'Free Practice 2', 'value': 'FP2'},
                {'label': 'Free Practice 3', 'value': 'FP3'},
                {'label': 'Race', 'value': 'R'},
            ]
        
        # Default to Race
        return options, 'R'
    except Exception as e:
        print(f"Error getting session options: {e}")
        # Fallback to standard options
        return [
            {'label': 'Free Practice 1', 'value': 'FP1'},
            {'label': 'Free Practice 2', 'value': 'FP2'},
            {'label': 'Free Practice 3', 'value': 'FP3'},
            {'label': 'Race', 'value': 'R'},
        ], 'R'


@app.callback(
    Output('driver-team-selection-container', 'style'),
    Output('team-selection-container', 'style'),
    Input('race-chart-dropdown', 'value')
)
def toggle_driver_team_selection(chart_type):
    """Toggle between driver and team selection based on chart type."""
    if chart_type == 'Aero Performance':
        # Hide both selections - Aero Performance uses all teams automatically
        return {'display': 'none'}, {'display': 'none'}
    else:
        # Show driver selection, hide team selection
        return {'display': 'block'}, {'display': 'none'}


@app.callback(
    Output('race-team-dropdown', 'options'),
    Output('race-team-colors-store', 'data'),
    Input('race-session-dropdown', 'value'),
    Input('race-event-dropdown', 'value'),
    Input('race-year-dropdown', 'value')
)
def update_team_options(selected_session, selected_race, selected_year):
    """Populate team options for Aero Performance chart."""
    if not selected_race or not selected_year or not selected_session:
        return [], {}
    try:
        session = fastf1.get_session(selected_year, selected_race, selected_session)
        session.load(laps=True, telemetry=False, weather=False, messages=False)
        plotting.setup_mpl()
        
        teams = set()
        team_colors = {}
        
        for d in session.drivers:
            driver_info = session.get_driver(d)
            team = driver_info['TeamName']
            if team not in teams:
                teams.add(team)
                color = plotting.get_team_color(team, session)
                team_colors[team] = color
        
        options = [{'label': t, 'value': t} for t in sorted(teams)]
        return options, team_colors
    except Exception as e:
        print(f"Error loading teams: {e}")
        return [], {}


@app.callback(
    Output('race-team-tags-display', 'children'),
    Input('race-team-dropdown', 'value'),
    State('race-team-colors-store', 'data')
)
def display_team_tags(selected_teams, team_colors):
    """Display team tags with team colors."""
    if not selected_teams or not team_colors:
        return []
    
    tags = []
    for team in selected_teams:
        color = team_colors.get(team, '#ffffff')
        tags.append(
            html.Span(
                team,
                className='driver-tag',
                style={
                    'backgroundColor': '#000000',
                    'color': color,
                    'fontWeight': 'bold'
                }
            )
        )
    return tags


@app.callback(
    Output('race-driver-dropdown', 'options'),
    Output('race-driver-colors-store', 'data'),
    Input('race-session-dropdown', 'value'),
    Input('race-event-dropdown', 'value'),
    Input('race-year-dropdown', 'value')
)
def update_driver_options(selected_session, selected_race, selected_year):
    if not selected_race or not selected_year or not selected_session:
        return [], {}
    try:
        session = fastf1.get_session(selected_year, selected_race, selected_session)
        session.load(laps=True, telemetry=False, weather=False, messages=False)
        plotting.setup_mpl()
        
        drivers = session.drivers
        driver_colors = {}
        options = []
        
        for d in drivers:
            driver_info = session.get_driver(d)
            abbr = driver_info['Abbreviation']
            full_name = driver_info['FullName']
            team = driver_info['TeamName']
            color = plotting.get_team_color(team, session)
            driver_colors[abbr] = color
            options.append({'label': full_name, 'value': abbr})
        
        # Add "All Drivers" option at the top
        all_drivers_option = {'label': '⭐ All Drivers', 'value': 'ALL_DRIVERS'}
        options.insert(0, all_drivers_option)
        
        return options, driver_colors
    except Exception as e:
        print(f"Error loading session for driver options: {e}")
        return [], {}


@app.callback(
    Output('race-driver-dropdown', 'value'),
    Input('race-driver-dropdown', 'value'),
    State('race-driver-dropdown', 'options'),
    prevent_initial_call=True
)
def handle_all_drivers_selection(selected_drivers, options):
    """When 'All Drivers' is selected, expand to all individual drivers."""
    if not selected_drivers or not options:
        return selected_drivers
    
    if 'ALL_DRIVERS' in selected_drivers:
        # Get all driver values except ALL_DRIVERS
        all_driver_values = [opt['value'] for opt in options if opt['value'] != 'ALL_DRIVERS']
        return all_driver_values
    
    return selected_drivers


@app.callback(
    Output('race-driver-tags-display', 'children'),
    Input('race-driver-dropdown', 'value'),
    State('race-driver-colors-store', 'data')
)
def display_driver_tags(selected_drivers, driver_colors):
    if not selected_drivers or not driver_colors:
        return []
    
    tags = []
    for driver in selected_drivers:
        color = driver_colors.get(driver, '#ffffff')
        tags.append(
            html.Span(
                driver,
                className='driver-tag',
                style={
                    'backgroundColor': '#000000',
                    'color': color,
                    'fontWeight': 'bold'
                }
            )
        )
    return tags


@app.callback(
    Output('race-graph', 'figure'),
    Output('race-graph', 'style'),
    Output('race-graph-empty-state', 'style'),
    Input('race-sketch-button', 'n_clicks'),
    State('race-driver-dropdown', 'value'),
    State('race-team-dropdown', 'value'),
    State('race-year-dropdown', 'value'),
    State('race-event-dropdown', 'value'),
    State('race-session-dropdown', 'value'),
    State('race-chart-dropdown', 'value'),
    State('race-driver-colors-store', 'data'),
    State('race-team-colors-store', 'data')
)
def update_graph(n_clicks, drivers, teams, year, race, session_type, chart_type, driver_colors, team_colors):
    empty_layout = dict(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(color='white', gridcolor='rgba(255,255,255,0.1)', linecolor='white', rangemode='tozero'),
        yaxis=dict(color='white', gridcolor='rgba(255,255,255,0.1)', linecolor='white', rangemode='tozero'),
        font=dict(color='white')
    )
    
    # Styles for showing/hiding
    graph_hidden = {'height': '80vh', 'display': 'none'}
    graph_visible = {'height': '80vh', 'display': 'block'}
    empty_hidden = {'display': 'none'}
    empty_visible = {}
    
    if n_clicks is None or n_clicks == 0:
        fig = go.Figure()
        fig.update_layout(title="", **empty_layout)
        return fig, graph_hidden, empty_visible
    
    # Handle Aero Performance - uses all teams automatically
    if chart_type == 'Aero Performance':
        if not race or not year or not session_type:
            fig = go.Figure()
            fig.update_layout(title="Please select Year, Race, and Session to sketch the graph.", **empty_layout)
            return fig, graph_visible, empty_hidden
        
        try:
            session = fastf1.get_session(year, race, session_type)
            session.load(laps=True, telemetry=True, weather=False, messages=False)
            plotting.setup_mpl()
            
            # Get all teams from the session
            all_teams = set()
            all_team_colors = {}
            for d in session.drivers:
                driver_info = session.get_driver(d)
                team = driver_info['TeamName']
                if team not in all_teams:
                    all_teams.add(team)
                    all_team_colors[team] = plotting.get_team_color(team, session)
            
            session_names = {'FP1': 'FP1', 'FP2': 'FP2', 'FP3': 'FP3', 'R': 'Race', 'S': 'Sprint'}
            session_name = session_names.get(session_type, session_type)
            
            result = create_aero_performance_graph(session, list(all_teams), race, year, all_team_colors, empty_layout, session_name)
            return result, graph_visible, empty_hidden
        except Exception as e:
            print(f"Error generating aero performance graph: {e}")
            fig = go.Figure()
            fig.update_layout(title=f"Error: {e}", **empty_layout)
            return fig, graph_visible, empty_hidden
    
    if not drivers or not race or not year or not session_type:
        fig = go.Figure()
        fig.update_layout(title="Please select Year, Race, Session, and at least one Driver to sketch the graph.", **empty_layout)
        return fig, graph_visible, empty_hidden
    
    # Get session name for title
    session_names = {'FP1': 'FP1', 'FP2': 'FP2', 'FP3': 'FP3', 'R': 'Race', 'S': 'Sprint'}
    session_name = session_names.get(session_type, session_type)
    
    try:
        session = fastf1.get_session(year, race, session_type)
        session.load(laps=True, telemetry=False, weather=False, messages=False)
        plotting.setup_mpl()
        
        if chart_type == 'Lap Times':
            result = create_laptime_graph(session, drivers, race, year, driver_colors, empty_layout, session_name)
            return result, graph_visible, empty_hidden
        elif chart_type == 'Box Plot':
            result = create_boxplot_graph(session, drivers, race, year, driver_colors, empty_layout, session_name)
            return result, graph_visible, empty_hidden
        elif chart_type == 'Violin Plot':
            result = create_violin_graph(session, drivers, race, year, driver_colors, empty_layout, session_name)
            return result, graph_visible, empty_hidden
        else:
            fig = go.Figure()
            fig.update_layout(title="Unknown chart type selected.", **empty_layout)
            return fig, graph_visible, empty_hidden
            
    except Exception as e:
        print(f"Error generating graph: {e}")
        fig = go.Figure()
        fig.update_layout(
            title=f"Error sketching graph: {e}",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white')
        )
        return fig, graph_visible, empty_hidden


def create_laptime_graph(session, drivers, race, year, driver_colors, empty_layout, session_name='Race'):
    """Create a lap times comparison graph across the session."""
    fig = go.Figure()
    team_color_used_solid = {}
    
    for d_abbr in drivers:
        driver_data = session.get_driver(d_abbr)
        if driver_data is None:
            continue
        
        team = driver_data['TeamName']
        color = driver_colors.get(d_abbr, plotting.get_team_color(team, session))
        
        # Get all laps for this driver
        driver_laps = session.laps.pick_drivers(d_abbr).pick_quicklaps()
        
        if driver_laps.empty:
            continue
        
        # Extract lap numbers and lap times
        lap_numbers = driver_laps['LapNumber'].values
        lap_times = driver_laps['LapTime'].dt.total_seconds().values
        
        # Filter out any NaN values
        valid_mask = ~np.isnan(lap_times)
        lap_numbers = lap_numbers[valid_mask]
        lap_times = lap_times[valid_mask]
        
        if len(lap_numbers) == 0:
            continue
        
        line_dash = 'solid'
        if team in team_color_used_solid:
            line_dash = 'dash'
        else:
            team_color_used_solid[team] = True
        
        fig.add_trace(go.Scatter(
            x=lap_numbers,
            y=lap_times,
            mode='lines+markers',
            name=f"{d_abbr} ({team})",
            line=dict(color=color, dash=line_dash, width=2),
            marker=dict(size=4)
        ))
    
    fig.update_layout(
        title=dict(
            text=f"Lap Times - {race} {year} ({session_name})",
            font=dict(color='white', size=20)
        ),
        xaxis_title='Lap Number',
        yaxis_title='Lap Time (s)',
        legend_title="Driver (Team)",
        showlegend=True,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            color='white',
            gridcolor='rgba(255,255,255,0.1)',
            linecolor='white',
            tickfont=dict(color='white'),
            title_font=dict(color='white')
        ),
        yaxis=dict(
            color='white',
            gridcolor='rgba(255,255,255,0.1)',
            linecolor='white',
            tickfont=dict(color='white'),
            title_font=dict(color='white')
        ),
        legend=dict(
            font=dict(color='white'),
            title_font=dict(color='white')
        )
    )
    
    return fig


def create_boxplot_graph(session, drivers, race, year, driver_colors, empty_layout, session_name='Race'):
    """Create a box and whisker plot comparing lap time distributions."""
    fig = go.Figure()
    
    for d_abbr in drivers:
        driver_data = session.get_driver(d_abbr)
        if driver_data is None:
            continue
        
        team = driver_data['TeamName']
        color = driver_colors.get(d_abbr, plotting.get_team_color(team, session))
        
        # Get all laps for this driver (excluding pit laps and slow laps)
        driver_laps = session.laps.pick_drivers(d_abbr).pick_quicklaps()
        
        if driver_laps.empty:
            continue
        
        # Extract lap times
        lap_times = driver_laps['LapTime'].dt.total_seconds().values
        
        # Filter out any NaN values
        lap_times = lap_times[~np.isnan(lap_times)]
        
        if len(lap_times) == 0:
            continue
        
        fig.add_trace(go.Box(
            y=lap_times,
            name=d_abbr,
            marker_color=color,
            line_color=color,
            boxmean=True,  # Show mean as dashed line
            boxpoints='outliers'
        ))
    
    fig.update_layout(
        title=dict(
            text=f"Lap Time Distribution - {race} {year} ({session_name})",
            font=dict(color='white', size=20)
        ),
        xaxis_title='Driver',
        yaxis_title='Lap Time (s)',
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            color='white',
            gridcolor='rgba(255,255,255,0.1)',
            linecolor='white',
            tickfont=dict(color='white'),
            title_font=dict(color='white')
        ),
        yaxis=dict(
            color='white',
            gridcolor='rgba(255,255,255,0.1)',
            linecolor='white',
            tickfont=dict(color='white'),
            title_font=dict(color='white')
        )
    )
    
    return fig


def create_violin_graph(session, drivers, race, year, driver_colors, empty_layout, session_name='Race'):
    """Create a violin plot comparing lap time distributions with tire compound colors."""
    fig = go.Figure()
    
    # Tire compound colors
    compound_colors = {
        'SOFT': '#FF3333',      # Red
        'MEDIUM': '#FFD700',    # Yellow
        'HARD': '#FFFFFF',      # White
        'INTERMEDIATE': '#43B02A',  # Green
        'WET': '#0067AD'        # Blue
    }
    
    # Use numerical x positions for proper jitter
    driver_positions = {d: i for i, d in enumerate(drivers)}
    
    # First, collect all data and add violin traces
    driver_data_map = {}
    
    for d_abbr in drivers:
        driver_data = session.get_driver(d_abbr)
        if driver_data is None:
            continue
        
        team = driver_data['TeamName']
        color = driver_colors.get(d_abbr, plotting.get_team_color(team, session))
        
        # Get all laps for this driver (excluding pit laps and slow laps)
        driver_laps = session.laps.pick_drivers(d_abbr).pick_quicklaps()
        
        if driver_laps.empty:
            continue
        
        # Extract lap times and compounds
        lap_times = driver_laps['LapTime'].dt.total_seconds().values
        compounds = driver_laps['Compound'].values
        
        # Filter out any NaN values
        valid_mask = ~np.isnan(lap_times)
        lap_times_valid = lap_times[valid_mask]
        compounds_valid = compounds[valid_mask]
        
        if len(lap_times_valid) == 0:
            continue
        
        x_pos = driver_positions[d_abbr]
        
        driver_data_map[d_abbr] = {
            'lap_times': lap_times_valid,
            'compounds': compounds_valid,
            'color': color,
            'x_pos': x_pos
        }
        
        # Add violin trace using numerical x position
        fig.add_trace(go.Violin(
            x0=x_pos,
            y=lap_times_valid,
            name=d_abbr,
            line_color=color,
            fillcolor=color,
            opacity=0.6,
            meanline_visible=True,
            points=False,
            box_visible=False,
            showlegend=False,
            scalemode='width',
            width=0.8,
            side='both'
        ))
    
    # Add scatter points colored by tire compound using beeswarm positioning
    legend_added = set()
    
    for d_abbr in drivers:
        if d_abbr not in driver_data_map:
            continue
        
        data = driver_data_map[d_abbr]
        lap_times_valid = data['lap_times']
        compounds_valid = data['compounds']
        x_pos = data['x_pos']
        
        # Calculate beeswarm positions for all points of this driver
        all_times = lap_times_valid
        all_compounds = compounds_valid
        
        # Sort by lap time for beeswarm algorithm
        sort_idx = np.argsort(all_times)
        sorted_times = all_times[sort_idx]
        sorted_compounds = all_compounds[sort_idx]
        
        # Beeswarm positioning
        x_offsets = np.zeros(len(sorted_times))
        point_radius = 0.03  # Relative size of each point for collision detection
        y_range = np.ptp(sorted_times) if len(sorted_times) > 1 else 1
        y_tolerance = y_range * 0.015  # Points within this y-range are considered "neighbors"
        
        for i in range(len(sorted_times)):
            # Find nearby points that have already been placed
            nearby_offsets = []
            for j in range(i):
                if abs(sorted_times[i] - sorted_times[j]) < y_tolerance:
                    nearby_offsets.append(x_offsets[j])
            
            if not nearby_offsets:
                # No nearby points, place at center
                x_offsets[i] = 0
            else:
                # Find a position that doesn't overlap with nearby points
                # Try alternating left and right from center
                for offset in [0, -point_radius, point_radius, -2*point_radius, 2*point_radius, 
                              -3*point_radius, 3*point_radius, -4*point_radius, 4*point_radius,
                              -5*point_radius, 5*point_radius]:
                    collision = False
                    for existing in nearby_offsets:
                        if abs(offset - existing) < point_radius * 1.8:
                            collision = True
                            break
                    if not collision:
                        x_offsets[i] = offset
                        break
                else:
                    # If no non-colliding position found, use small random jitter
                    x_offsets[i] = np.random.uniform(-0.15, 0.15)
        
        # Unsort to get original order
        unsort_idx = np.argsort(sort_idx)
        x_offsets = x_offsets[unsort_idx]
        
        # Group by compound and add scatter points
        for compound in compound_colors.keys():
            compound_mask = compounds_valid == compound
            if not np.any(compound_mask):
                continue
            
            compound_times = lap_times_valid[compound_mask]
            compound_offsets = x_offsets[compound_mask]
            x_values = x_pos + compound_offsets
            
            # Only show legend for first occurrence of each compound
            show_legend = compound not in legend_added
            if show_legend:
                legend_added.add(compound)
            
            fig.add_trace(go.Scatter(
                x=x_values,
                y=compound_times,
                mode='markers',
                name=compound.capitalize(),
                marker=dict(
                    color=compound_colors[compound],
                    size=8,
                    opacity=0.95,
                    line=dict(color='rgba(0,0,0,0.8)', width=1)
                ),
                showlegend=show_legend,
                legendgroup=compound
            ))
    
    # Update layout with custom x-axis ticks
    fig.update_layout(
        title=dict(
            text=f"Lap Time Distribution (Violin) - {race} {year} ({session_name})",
            font=dict(color='white', size=20)
        ),
        xaxis_title='Driver',
        yaxis_title='Lap Time (s)',
        showlegend=True,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            color='white',
            gridcolor='rgba(255,255,255,0.1)',
            linecolor='white',
            tickfont=dict(color='white'),
            title_font=dict(color='white'),
            tickmode='array',
            tickvals=list(range(len(drivers))),
            ticktext=list(drivers),
            range=[-0.5, len(drivers) - 0.5]
        ),
        yaxis=dict(
            color='white',
            gridcolor='rgba(255,255,255,0.1)',
            linecolor='white',
            tickfont=dict(color='white'),
            title_font=dict(color='white')
        ),
        legend=dict(
            font=dict(color='white'),
            title=dict(text='Compound', font=dict(color='white'))
        )
    )
    
    return fig


def create_aero_performance_graph(session, teams, race, year, team_colors, empty_layout, session_name='Race'):
    """Create an aero performance graph comparing teams' average speed vs top speed."""
    fig = go.Figure()
    
    team_data = []
    
    for team_name in teams:
        team_avg_speeds = []
        team_top_speeds = []
        
        # Get all drivers from this team
        for d in session.drivers:
            driver_info = session.get_driver(d)
            if driver_info['TeamName'] != team_name:
                continue
            
            abbr = driver_info['Abbreviation']
            
            # Get the 10 fastest laps for this driver
            driver_laps = session.laps.pick_drivers(abbr).pick_quicklaps()
            
            if driver_laps.empty:
                continue
            
            # Sort by lap time and take top 10
            driver_laps = driver_laps.sort_values('LapTime').head(10)
            
            # Get telemetry for each lap to calculate average and top speeds
            for _, lap in driver_laps.iterrows():
                try:
                    telemetry = lap.get_telemetry()
                    if telemetry is None or telemetry.empty:
                        continue
                    
                    if 'Speed' not in telemetry.columns:
                        continue
                    
                    speeds = telemetry['Speed'].dropna()
                    if len(speeds) == 0:
                        continue
                    
                    avg_speed = speeds.mean()
                    top_speed = speeds.max()
                    
                    if avg_speed > 0 and top_speed > 0:
                        team_avg_speeds.append(avg_speed)
                        team_top_speeds.append(top_speed)
                except Exception as e:
                    continue
        
        if len(team_avg_speeds) == 0:
            continue
        
        # Remove outliers using IQR method
        avg_speeds_arr = np.array(team_avg_speeds)
        top_speeds_arr = np.array(team_top_speeds)
        
        # Remove outliers for average speed
        q1_avg, q3_avg = np.percentile(avg_speeds_arr, [25, 75])
        iqr_avg = q3_avg - q1_avg
        avg_mask = (avg_speeds_arr >= q1_avg - 1.5 * iqr_avg) & (avg_speeds_arr <= q3_avg + 1.5 * iqr_avg)
        
        # Remove outliers for top speed
        q1_top, q3_top = np.percentile(top_speeds_arr, [25, 75])
        iqr_top = q3_top - q1_top
        top_mask = (top_speeds_arr >= q1_top - 1.5 * iqr_top) & (top_speeds_arr <= q3_top + 1.5 * iqr_top)
        
        # Combine masks
        valid_mask = avg_mask & top_mask
        
        if not np.any(valid_mask):
            continue
        
        # Calculate final averages after removing outliers
        final_avg_speed = np.mean(avg_speeds_arr[valid_mask])
        final_top_speed = np.mean(top_speeds_arr[valid_mask])
        
        team_data.append({
            'team': team_name,
            'avg_speed': final_avg_speed,
            'top_speed': final_top_speed,
            'color': team_colors.get(team_name, '#ffffff')
        })
    
    if not team_data:
        fig.update_layout(title="No telemetry data available for selected teams.", **empty_layout)
        return fig
    
    # Calculate center point (average of all teams)
    avg_speeds = [d['avg_speed'] for d in team_data]
    top_speeds = [d['top_speed'] for d in team_data]
    center_x = np.mean(avg_speeds)
    center_y = np.mean(top_speeds)
    
    # Calculate axis ranges with padding
    x_min, x_max = min(avg_speeds) - 2, max(avg_speeds) + 2
    y_min, y_max = min(top_speeds) - 2, max(top_speeds) + 2
    
    # Add diagonal lines from center (for quadrant effect)
    diag_length = max(x_max - x_min, y_max - y_min) * 1.5
    
    # Diagonal line 1 (top-left to bottom-right)
    fig.add_trace(go.Scatter(
        x=[center_x - diag_length, center_x + diag_length],
        y=[center_y + diag_length, center_y - diag_length],
        mode='lines',
        line=dict(color='rgba(255,255,255,0.3)', width=1),
        showlegend=False,
        hoverinfo='skip'
    ))
    
    # Diagonal line 2 (bottom-left to top-right)
    fig.add_trace(go.Scatter(
        x=[center_x - diag_length, center_x + diag_length],
        y=[center_y - diag_length, center_y + diag_length],
        mode='lines',
        line=dict(color='rgba(255,255,255,0.3)', width=1),
        showlegend=False,
        hoverinfo='skip'
    ))
    
    # Add vertical line at center
    fig.add_trace(go.Scatter(
        x=[center_x, center_x],
        y=[y_min - 5, y_max + 5],
        mode='lines',
        line=dict(color='rgba(255,255,255,0.5)', width=2),
        showlegend=False,
        hoverinfo='skip'
    ))
    
    # Add horizontal line at center
    fig.add_trace(go.Scatter(
        x=[x_min - 5, x_max + 5],
        y=[center_y, center_y],
        mode='lines',
        line=dict(color='rgba(255,255,255,0.5)', width=2),
        showlegend=False,
        hoverinfo='skip'
    ))
    
    # Add scatter points for each team
    for data in team_data:
        fig.add_trace(go.Scatter(
            x=[data['avg_speed']],
            y=[data['top_speed']],
            mode='markers+text',
            name=data['team'],
            text=[data['team']],
            textposition='top center',
            textfont=dict(color=data['color'], size=12),
            marker=dict(
                color=data['color'],
                size=15,
                line=dict(color='white', width=2)
            ),
            showlegend=True
        ))
    
    # Calculate label positions along the diagonal lines
    # Offset from center along each diagonal
    label_offset = min(x_max - center_x, y_max - center_y) * 0.6
    
    # Define base positions for quadrant labels
    quadrant_labels = [
        {'name': 'Low Downforce', 'base_x': center_x - label_offset * 0.7, 'base_y': center_y + label_offset * 0.7, 'yanchor': 'bottom', 'y_offset': 0.5},
        {'name': 'High Efficiency', 'base_x': center_x + label_offset * 0.7, 'base_y': center_y + label_offset * 0.7, 'yanchor': 'bottom', 'y_offset': 0.5},
        {'name': 'Low Efficiency', 'base_x': center_x - label_offset * 0.7, 'base_y': center_y - label_offset * 0.7, 'yanchor': 'top', 'y_offset': -0.5},
        {'name': 'High Downforce', 'base_x': center_x + label_offset * 0.7, 'base_y': center_y - label_offset * 0.7, 'yanchor': 'top', 'y_offset': -0.5},
    ]
    
    # Check for overlaps with team positions and adjust
    def check_overlap(label_x, label_y, teams_data, threshold_x=1.5, threshold_y=1.5):
        """Check if label position overlaps with any team marker."""
        for t in teams_data:
            if abs(t['avg_speed'] - label_x) < threshold_x and abs(t['top_speed'] - label_y) < threshold_y:
                return True
        return False
    
    # Adjust label positions to avoid overlaps
    annotations = []
    for label in quadrant_labels:
        x_pos = label['base_x']
        y_pos = label['base_y'] + label['y_offset']
        
        # If overlapping, move further along the diagonal
        attempts = 0
        while check_overlap(x_pos, y_pos, team_data) and attempts < 5:
            # Move further from center along the diagonal
            if 'Low Downforce' in label['name']:
                x_pos -= 0.5
                y_pos += 0.5
            elif 'High Efficiency' in label['name']:
                x_pos += 0.5
                y_pos += 0.5
            elif 'Low Efficiency' in label['name']:
                x_pos -= 0.5
                y_pos -= 0.5
            elif 'High Downforce' in label['name']:
                x_pos += 0.5
                y_pos -= 0.5
            attempts += 1
        
        annotations.append(
            dict(x=x_pos, y=y_pos, text=label['name'],
                 showarrow=False, font=dict(color='rgba(255,255,255,0.7)', size=10), 
                 xanchor='center', yanchor=label['yanchor'])
        )
    
    # Add axis labels
    annotations.extend([
        dict(x=x_min + 0.5, y=center_y, text="Slow", 
             showarrow=False, font=dict(color='rgba(255,255,255,0.7)', size=12), xanchor='left', yanchor='middle'),
        dict(x=x_max - 0.5, y=center_y, text="Quick", 
             showarrow=False, font=dict(color='rgba(255,255,255,0.7)', size=12), xanchor='right', yanchor='middle'),
        dict(x=center_x, y=y_max - 0.3, text="Low Drag", 
             showarrow=False, font=dict(color='rgba(255,255,255,0.7)', size=12), xanchor='center', yanchor='top'),
        dict(x=center_x, y=y_min + 0.3, text="High Drag", 
             showarrow=False, font=dict(color='rgba(255,255,255,0.7)', size=12), xanchor='center', yanchor='bottom'),
    ])
    
    fig.update_layout(
        title=dict(
            text=f"Aero Performance - {race} {year} ({session_name})",
            font=dict(color='white', size=20)
        ),
        xaxis_title='Mean Speed (km/h)',
        yaxis_title='Top Speed (km/h)',
        legend_title="Team",
        showlegend=True,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            color='white',
            gridcolor='rgba(255,255,255,0.05)',
            linecolor='white',
            tickfont=dict(color='white'),
            title_font=dict(color='white'),
            range=[x_min, x_max]
        ),
        yaxis=dict(
            color='white',
            gridcolor='rgba(255,255,255,0.05)',
            linecolor='white',
            tickfont=dict(color='white'),
            title_font=dict(color='white'),
            range=[y_min, y_max]
        ),
        legend=dict(
            font=dict(color='white'),
            title_font=dict(color='white')
        ),
        annotations=annotations
    )
    
    return fig
