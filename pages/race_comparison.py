# In pages/race_comparison.py

from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import fastf1
from fastf1 import plotting
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from app_instance import app

# --- Reusable Navbar Component ---
navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Lap Comparison", href="/lap-comparison")),
        dbc.NavItem(dbc.NavLink("Race Comparison", href="/race-comparison")),
    ],
    brand="🏎️ F1 Analytics Dashboard",
    brand_href="/",
    color="primary",
    dark=True,
    className="mb-4"
)

# --- Dropdown options ---
years = [2021, 2022, 2023, 2024, 2025]
chart_types = ['Lap Times', 'Box Plot', 'Violin Plot']

# --- Define the Controls Panel ---
controls = dbc.Card(
    [
        dbc.Row([
            dbc.Col(dbc.Label("Select Year"), width=12),
            dbc.Col(dcc.Dropdown(years, 2024, id='race-year-dropdown', clearable=False), width=12),
        ], className="mb-3"),

        dbc.Row([
            dbc.Col(dbc.Label("Select Race"), width=12),
            dbc.Col(dcc.Dropdown(id='race-event-dropdown', placeholder="Select a Grand Prix"), width=12),
        ], className="mb-3"),

        dbc.Row([
            dbc.Col(dbc.Label("Select Driver(s)"), width=12),
            dbc.Col(dcc.Dropdown(id='race-driver-dropdown', multi=True, placeholder="Select driver(s)"), width=12),
            dbc.Col(html.Div(id='race-driver-tags-display', style={'marginTop': '8px'}), width=12),
        ], className="mb-3"),

        dbc.Row([
            dbc.Col(dbc.Label("Select Chart Type"), width=12),
            dbc.Col(dcc.Dropdown(chart_types, 'Lap Times', id='race-chart-dropdown', clearable=False), width=12),
        ], className="mb-3"),

        dbc.Button('Sketch Graph', id='race-sketch-button', n_clicks=0, color="primary", className="w-100"),
        
        # Store for driver-team color mapping
        dcc.Store(id='race-driver-colors-store', data={})
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
                html.H3("Race Analysis Controls", style={'color': 'white'}),
                controls
            ], md=4),

            # Column for the graph
            dbc.Col([
                dcc.Loading(
                    id="race-loading-graph",
                    type="default",
                    children=dcc.Graph(id='race-graph', style={'height': '80vh'})
                )
            ], md=8)
        ])
    ], fluid=True)
])

# --- CALLBACKS ---

@app.callback(
    Output('race-event-dropdown', 'options'),
    Input('race-year-dropdown', 'value')
)
def update_race_options(selected_year):
    if not selected_year:
        return []
    schedule = fastf1.get_event_schedule(selected_year)
    races = schedule['EventName'].tolist()
    return [{'label': r, 'value': r} for r in races]


@app.callback(
    Output('race-driver-dropdown', 'options'),
    Output('race-driver-colors-store', 'data'),
    Input('race-event-dropdown', 'value'),
    Input('race-year-dropdown', 'value')
)
def update_driver_options(selected_race, selected_year):
    if not selected_race or not selected_year:
        return [], {}
    try:
        session = fastf1.get_session(selected_year, selected_race, 'R')
        session.load(laps=True, telemetry=False, weather=False, messages=False)
        plotting.setup_mpl()
        
        drivers = session.drivers
        driver_colors = {}
        options = []
        
        for d in drivers:
            driver_info = session.get_driver(d)
            abbr = driver_info['Abbreviation']
            team = driver_info['TeamName']
            color = plotting.get_team_color(team, session)
            driver_colors[abbr] = color
            options.append({'label': abbr, 'value': abbr})
        
        return options, driver_colors
    except Exception as e:
        print(f"Error loading session for driver options: {e}")
        return [], {}


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
    Input('race-sketch-button', 'n_clicks'),
    State('race-driver-dropdown', 'value'),
    State('race-year-dropdown', 'value'),
    State('race-event-dropdown', 'value'),
    State('race-chart-dropdown', 'value'),
    State('race-driver-colors-store', 'data')
)
def update_graph(n_clicks, drivers, year, race, chart_type, driver_colors):
    empty_layout = dict(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(color='white', gridcolor='rgba(255,255,255,0.1)', linecolor='white'),
        yaxis=dict(color='white', gridcolor='rgba(255,255,255,0.1)', linecolor='white'),
        font=dict(color='white')
    )
    
    if n_clicks is None or n_clicks == 0:
        fig = go.Figure()
        fig.update_layout(title="Select filters and click 'Sketch Graph' to display race data", **empty_layout)
        return fig
    
    if not drivers or not race or not year:
        fig = go.Figure()
        fig.update_layout(title="Please select Year, Race, and at least one Driver to sketch the graph.", **empty_layout)
        return fig
    
    try:
        session = fastf1.get_session(year, race, 'R')
        session.load(laps=True, telemetry=False, weather=False, messages=False)
        plotting.setup_mpl()
        
        if chart_type == 'Lap Times':
            return create_laptime_graph(session, drivers, race, year, driver_colors, empty_layout)
        elif chart_type == 'Box Plot':
            return create_boxplot_graph(session, drivers, race, year, driver_colors, empty_layout)
        elif chart_type == 'Violin Plot':
            return create_violin_graph(session, drivers, race, year, driver_colors, empty_layout)
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


def create_laptime_graph(session, drivers, race, year, driver_colors, empty_layout):
    """Create a lap times comparison graph across the race."""
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
            text=f"Lap Times - {race} {year}",
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


def create_boxplot_graph(session, drivers, race, year, driver_colors, empty_layout):
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
            text=f"Lap Time Distribution - {race} {year}",
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


def create_violin_graph(session, drivers, race, year, driver_colors, empty_layout):
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
            text=f"Lap Time Distribution (Violin) - {race} {year}",
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
