# In pages/year_analysis.py

from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import fastf1
from fastf1 import plotting
from fastf1.ergast import Ergast
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from app_instance import app

# --- Reusable Navbar Component ---
navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Qualifying Analysis", href="/lap-comparison")),
        dbc.NavItem(dbc.NavLink("Weekend Analysis", href="/race-comparison")),
        dbc.NavItem(dbc.NavLink("Year Analysis", href="/year-analysis")),
    ],
    brand="🏎️ F1 Analytics Dashboard",
    brand_href="/",
    color="primary",
    dark=True,
    className="mb-4"
)

# --- Dropdown options ---
years = list(range(1950, 2026))  # Ergast has data back to 1950
chart_types = ['Points Graph']

# --- Define the Controls Panel ---
controls = dbc.Card(
    [
        dbc.Row([
            dbc.Col(dbc.Label("Select Year"), width=12),
            dbc.Col(dcc.Dropdown(years, 2025, id='year-analysis-year-dropdown', clearable=False), width=12),
        ], className="mb-3"),

        dbc.Row([
            dbc.Col(dbc.Label("Select Driver(s)"), width=12),
            dbc.Col(
                dcc.Loading(
                    id="loading-year-drivers",
                    type="default",
                    children=dcc.Dropdown(id='year-analysis-driver-dropdown', multi=True, placeholder="Select driver(s)"),
                    fullscreen=False,
                    style={'minHeight': '38px'}
                ), width=12
            ),
            dbc.Col(html.Div(id='year-analysis-driver-tags-display', style={'marginTop': '8px'}), width=12),
        ], className="mb-3"),

        dbc.Row([
            dbc.Col(dbc.Label("Select Chart Type"), width=12),
            dbc.Col(dcc.Dropdown(chart_types, 'Points Graph', id='year-analysis-chart-dropdown', clearable=False), width=12),
        ], className="mb-3"),

        dbc.Button('Sketch Graph', id='year-analysis-sketch-button', n_clicks=0, color="primary", className="w-100"),
        
        # Store for driver-team color mapping
        dcc.Store(id='year-analysis-driver-colors-store', data={})
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
                html.H3("Year Analysis", style={'color': 'white'}),
                controls
            ], md=4),

            # Column for the graph
            dbc.Col([
                dcc.Loading(
                    id="year-analysis-loading-graph",
                    type="default",
                    children=dcc.Graph(id='year-analysis-graph', style={'height': '80vh'})
                )
            ], md=8)
        ])
    ], fluid=True)
])

# --- CALLBACKS ---

@app.callback(
    Output('year-analysis-driver-dropdown', 'options'),
    Output('year-analysis-driver-colors-store', 'data'),
    Input('year-analysis-year-dropdown', 'value')
)
def update_driver_options(selected_year):
    if not selected_year:
        return [], {}
    try:
        # Get driver standings to get list of drivers for the year
        ergast = Ergast()
        standings = ergast.get_driver_standings(season=selected_year)
        
        # ErgastMultiResponse has content as list of DataFrames
        if hasattr(standings, 'content') and standings.content:
            drivers_df = standings.content[0] if isinstance(standings.content, list) else standings.content
        else:
            return [], {}
        
        if drivers_df is None or drivers_df.empty:
            return [], {}
        
        driver_colors = {}
        options = []
        
        for _, row in drivers_df.iterrows():
            driver_code = row['driverCode']
            # Try to get team color
            try:
                constructor = row.get('constructorNames', [])
                if isinstance(constructor, str):
                    team_name = constructor
                elif isinstance(constructor, list) and len(constructor) > 0:
                    team_name = constructor[0]
                else:
                    team_name = 'Unknown'
                
                # Get approximate team colors
                color = get_team_color_by_name(team_name)
                driver_colors[driver_code] = color
            except:
                driver_colors[driver_code] = '#FFFFFF'
            
            driver_name = f"{row['givenName']} {row['familyName']}"
            options.append({'label': f"{driver_code} - {driver_name}", 'value': driver_code})
        
        # Add "All Drivers" option at the top
        all_drivers_option = {'label': '⭐ All Drivers', 'value': 'ALL_DRIVERS'}
        options.insert(0, all_drivers_option)
        
        return options, driver_colors
        
    except Exception as e:
        print(f"Error loading drivers: {e}")
        import traceback
        traceback.print_exc()
        return [], {}


@app.callback(
    Output('year-analysis-driver-dropdown', 'value'),
    Input('year-analysis-driver-dropdown', 'value'),
    State('year-analysis-driver-dropdown', 'options'),
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


def get_team_color_by_name(team_name):
    """Get team color by constructor name."""
    team_colors = {
        'red bull': '#3671C6',
        'ferrari': '#E8002D',
        'mercedes': '#27F4D2',
        'mclaren': '#FF8000',
        'aston martin': '#229971',
        'alpine': '#FF87BC',
        'williams': '#64C4FF',
        'haas': '#B6BABD',
        'alphatauri': '#5E8FAA',
        'alfa romeo': '#C92D4B',
        'rb': '#6692FF',
        'sauber': '#52E252',
        'kick sauber': '#52E252',
    }
    
    team_lower = team_name.lower()
    for key, color in team_colors.items():
        if key in team_lower:
            return color
    return '#FFFFFF'


@app.callback(
    Output('year-analysis-driver-tags-display', 'children'),
    Input('year-analysis-driver-dropdown', 'value'),
    State('year-analysis-driver-colors-store', 'data')
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
    Output('year-analysis-graph', 'figure'),
    Input('year-analysis-sketch-button', 'n_clicks'),
    State('year-analysis-driver-dropdown', 'value'),
    State('year-analysis-year-dropdown', 'value'),
    State('year-analysis-chart-dropdown', 'value'),
    State('year-analysis-driver-colors-store', 'data')
)
def update_graph(n_clicks, drivers, year, chart_type, driver_colors):
    empty_layout = dict(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(color='white', gridcolor='rgba(255,255,255,0.1)', linecolor='white', rangemode='tozero'),
        yaxis=dict(color='white', gridcolor='rgba(255,255,255,0.1)', linecolor='white', rangemode='tozero'),
        font=dict(color='white')
    )
    
    if n_clicks is None or n_clicks == 0:
        fig = go.Figure()
        fig.update_layout(title="Select filters and click 'Sketch Graph' to display data", **empty_layout)
        return fig
    
    if not drivers or not year:
        fig = go.Figure()
        fig.update_layout(title="Please select Year and at least one Driver to sketch the graph.", **empty_layout)
        return fig
    
    try:
        if chart_type == 'Points Graph':
            return create_points_graph(year, drivers, driver_colors, empty_layout)
        else:
            fig = go.Figure()
            fig.update_layout(title="Unknown chart type selected.", **empty_layout)
            return fig
            
    except Exception as e:
        print(f"Error generating graph: {e}")
        fig = go.Figure()
        fig.update_layout(
            title=f"Error sketching graph: {e}",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white')
        )
        return fig


def create_points_graph(year, drivers, driver_colors, empty_layout):
    """Create a cumulative points graph across the season."""
    fig = go.Figure()
    
    try:
        ergast = Ergast()
        
        # Get race schedule for the year
        schedule = ergast.get_race_schedule(season=year)
        
        # ErgastSimpleResponse has content as DataFrame directly
        if hasattr(schedule, 'content'):
            races_df = schedule.content
        else:
            races_df = schedule
        
        if races_df is None or races_df.empty:
            fig.update_layout(title="Could not load race schedule.", **empty_layout)
            return fig
        
        race_names = races_df['raceName'].tolist()
        race_rounds = races_df['round'].tolist()
        
        # Track which team colors have been used (for dashed lines for teammates)
        team_color_used = {}
        
        # Get results for each driver
        for driver_code in drivers:
            cumulative_points = []
            total_points = 0
            races_with_data = []
            
            # Get race results for each round
            for i, round_num in enumerate(race_rounds):
                try:
                    race_results = ergast.get_race_results(season=year, round=round_num)
                    
                    # ErgastMultiResponse has content as list of DataFrames
                    if hasattr(race_results, 'content') and race_results.content:
                        results_df = race_results.content[0] if isinstance(race_results.content, list) else race_results.content
                    else:
                        continue
                    
                    if results_df is not None and not results_df.empty:
                        # Find this driver's points
                        driver_result = results_df[results_df['driverCode'] == driver_code]
                        if not driver_result.empty:
                            points = driver_result['points'].values[0]
                            total_points += float(points)
                        
                        cumulative_points.append(total_points)
                        races_with_data.append(race_names[i])
                except Exception as e:
                    # If no data for this race yet (future race), continue checking
                    print(f"No results for round {round_num}: {e}")
                    continue
            
            if cumulative_points:
                color = driver_colors.get(driver_code, '#FFFFFF')
                
                # Differentiate teammates with dashed lines
                line_dash = 'solid'
                if color in team_color_used:
                    line_dash = 'dash'
                else:
                    team_color_used[color] = True
                
                fig.add_trace(go.Scatter(
                    x=races_with_data,
                    y=cumulative_points,
                    mode='lines+markers',
                    name=driver_code,
                    line=dict(color=color, width=3, dash=line_dash),
                    marker=dict(size=8, color=color)
                ))
        
        fig.update_layout(
            title=dict(
                text=f"Championship Points - {year}",
                font=dict(color='white', size=20)
            ),
            xaxis_title='Race',
            yaxis_title='Cumulative Points',
            legend_title="Driver",
            showlegend=True,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(
                color='white',
                gridcolor='rgba(255,255,255,0.1)',
                linecolor='white',
                tickfont=dict(color='white'),
                title_font=dict(color='white'),
                tickangle=45
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
        
    except Exception as e:
        print(f"Error creating points graph: {e}")
        import traceback
        traceback.print_exc()
        fig.update_layout(title=f"Error: {e}", **empty_layout)
        return fig

