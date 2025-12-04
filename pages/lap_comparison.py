# In pages/lap_comparison.py

from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc  # Import dbc
import fastf1
from fastf1 import plotting
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
years = [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]
metrics = ['Speed', 'Throttle', 'Brake', 'RPM', 'nGear', 'Delta', 'Track Dominance']

# --- Define the Controls Panel ---
controls = dbc.Card(
    [
        dbc.Row([
            dbc.Col(dbc.Label("Select Year"), width=12),
            dbc.Col(dcc.Dropdown(years, 2025, id='year-dropdown', clearable=False), width=12),
        ], className="mb-3"),

        dbc.Row([
            dbc.Col(dbc.Label("Select Race"), width=12),
            dbc.Col(dcc.Dropdown(id='race-dropdown', placeholder="Select a Grand Prix"), width=12),
        ], className="mb-3"),

        dbc.Row([
            dbc.Col(dbc.Label("Select Driver(s)"), width=12),
            dbc.Col(
                dcc.Loading(
                    id="loading-drivers",
                    type="default",
                    children=dcc.Dropdown(id='driver-dropdown', multi=True, placeholder="Select driver(s)"),
                    fullscreen=False,
                    style={'minHeight': '38px'}
                ), width=12
            ),
            dbc.Col(html.Div(id='driver-tags-display', style={'marginTop': '8px'}), width=12),
        ], className="mb-3"),

        dbc.Row([
            dbc.Col(dbc.Label("Select Metric"), width=12),
            dbc.Col(dcc.Dropdown(metrics, 'Speed', id='metric-dropdown', clearable=False), width=12),
        ], className="mb-3"),

        dbc.Button('Sketch Graph', id='sketch-button', n_clicks=0, color="primary", className="w-100"),
        
        # Store for driver-team color mapping
        dcc.Store(id='driver-colors-store', data={})
    ],
    body=True,
    className="transparent-card"
)

# --- Modal for Delta warning ---
delta_modal = dbc.Modal(
    [
        dbc.ModalHeader(dbc.ModalTitle("More Drivers Needed"), close_button=True),
        dbc.ModalBody("Please select two or more drivers to compare Delta times."),
        dbc.ModalFooter(
            dbc.Button("OK", id="close-delta-modal", className="ms-auto", n_clicks=0)
        ),
    ],
    id="delta-modal",
    is_open=False,
    centered=True,
)

# --- Define the main layout for this page using dbc grid system ---
layout = html.Div([
    navbar,
    delta_modal,
    dbc.Container([
        dbc.Row([
            # Column for the controls
            dbc.Col([
                html.H3("Qualifying Analysis", style={'color': 'white'}),
                controls
            ], md=4),

            # Column for the graph
            dbc.Col([
                dcc.Loading(
                    id="loading-graph",
                    type="default",
                    children=dcc.Graph(id='telemetry-graph', style={'height': '80vh'})
                )
            ], md=8)
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
    Output('driver-colors-store', 'data'),
    Input('race-dropdown', 'value'),
    Input('year-dropdown', 'value')
)
def update_driver_options(selected_race, selected_year):
    if not selected_race or not selected_year:
        return [], {}
    try:
        session = fastf1.get_session(selected_year, selected_race, 'Q')
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
        
        # Add "All Drivers" option at the top
        all_drivers_option = {'label': '⭐ All Drivers', 'value': 'ALL_DRIVERS'}
        options.insert(0, all_drivers_option)
        
        return options, driver_colors
    except Exception as e:
        print(f"Error loading session for driver options: {e}")
        return [], {}


@app.callback(
    Output('driver-dropdown', 'value'),
    Input('driver-dropdown', 'value'),
    State('driver-dropdown', 'options'),
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
    Output('driver-tags-display', 'children'),
    Input('driver-dropdown', 'value'),
    State('driver-colors-store', 'data')
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
    Output('delta-modal', 'is_open'),
    Input('sketch-button', 'n_clicks'),
    Input('close-delta-modal', 'n_clicks'),
    State('driver-dropdown', 'value'),
    State('metric-dropdown', 'value'),
    State('delta-modal', 'is_open'),
)
def toggle_delta_modal(sketch_clicks, close_clicks, drivers, metric, is_open):
    from dash import ctx
    if ctx.triggered_id == 'close-delta-modal':
        return False
    if ctx.triggered_id == 'sketch-button':
        # Only Delta requires 2+ drivers; Track Dominance works with any number (including 0)
        if metric == 'Delta' and (not drivers or len(drivers) < 2):
            return True
    return False


@app.callback(
    Output('telemetry-graph', 'figure'),
    Input('sketch-button', 'n_clicks'),
    State('driver-dropdown', 'value'),
    State('year-dropdown', 'value'),
    State('race-dropdown', 'value'),
    State('metric-dropdown', 'value')
)
def update_graph(n_clicks, drivers, year, race, metric):
    empty_layout = dict(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(color='white', gridcolor='rgba(255,255,255,0.1)', linecolor='white', rangemode='tozero'),
        yaxis=dict(color='white', gridcolor='rgba(255,255,255,0.1)', linecolor='white', rangemode='tozero'),
        font=dict(color='white')
    )
    if n_clicks is None or n_clicks == 0:
        fig = go.Figure()
        fig.update_layout(title="Select filters and click 'Sketch Graph' to display telemetry data", **empty_layout)
        return fig
    if not race or not year:
        fig = go.Figure()
        fig.update_layout(title="Please select Year and Race to sketch the graph.", **empty_layout)
        return fig
    
    # For non-Track Dominance metrics, require at least one driver
    if metric != 'Track Dominance' and (not drivers or len(drivers) == 0):
        fig = go.Figure()
        fig.update_layout(title="Please select at least one Driver to sketch the graph.", **empty_layout)
        return fig
    
    # Check for Delta with insufficient drivers
    if metric == 'Delta' and len(drivers) < 2:
        fig = go.Figure()
        fig.update_layout(title="Please select two or more drivers for Delta comparison.", **empty_layout)
        return fig
    
    # Track Dominance can work with no selection (uses all drivers)
    
    try:
        session = fastf1.get_session(year, race, 'Q')
        session.load(laps=True, telemetry=True, weather=True, messages=True)
        plotting.setup_mpl()
        fig = go.Figure()
        
        # Handle Delta metric separately
        if metric == 'Delta':
            return create_delta_graph(session, drivers, race, year, empty_layout)
        
        # Handle Track Dominance separately
        if metric == 'Track Dominance':
            return create_track_dominance(session, drivers, race, year, empty_layout)
        
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
            title=dict(
                text=f"{metric} Comparison - {race} {year}",
                font=dict(color='white', size=20)
            ),
            xaxis_title='Distance (m)',
            yaxis_title=metric,
            legend_title="Driver (Team)",
            showlegend=True,
            # Transparent background
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            # White axes
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
            # White legend text
            legend=dict(
                font=dict(color='white'),
                title_font=dict(color='white')
            )
        )
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


def create_delta_graph(session, drivers, race, year, empty_layout):
    """Create a delta time comparison graph with sector-based corrections."""
    fig = go.Figure()
    
    # Collect telemetry data and sector times for all drivers
    driver_telemetry = {}
    driver_laptimes = {}
    driver_sector_times = {}  # Cumulative sector times
    driver_laps = {}  # Store the lap object for sector info
    team_color_used_solid = {}
    
    for d_abbr in drivers:
        driver_data = session.get_driver(d_abbr)
        if driver_data is None:
            continue
        laps = session.laps.pick_drivers(d_abbr)
        if laps.empty:
            continue
        fastest = laps.pick_fastest()
        if fastest.empty:
            continue
        
        telemetry = fastest.get_telemetry()
        if telemetry.empty:
            continue
        
        # Store telemetry and lap time
        driver_telemetry[d_abbr] = telemetry
        driver_laptimes[d_abbr] = fastest['LapTime'].total_seconds()
        driver_laps[d_abbr] = fastest
        
        # Get sector times (cumulative)
        try:
            s1 = fastest['Sector1Time'].total_seconds() if pd.notna(fastest['Sector1Time']) else None
            s2 = fastest['Sector2Time'].total_seconds() if pd.notna(fastest['Sector2Time']) else None
            s3 = fastest['Sector3Time'].total_seconds() if pd.notna(fastest['Sector3Time']) else None
            
            if s1 and s2 and s3:
                driver_sector_times[d_abbr] = {
                    'S1': s1,           # Cumulative time at end of S1
                    'S2': s1 + s2,      # Cumulative time at end of S2
                    'S3': s1 + s2 + s3  # Cumulative time at end of S3 (lap time)
                }
            else:
                driver_sector_times[d_abbr] = None
        except:
            driver_sector_times[d_abbr] = None
    
    if len(driver_telemetry) < 2:
        fig.update_layout(title="Not enough valid telemetry data for Delta comparison.", **empty_layout)
        return fig
    
    # Find the fastest driver (reference)
    fastest_driver = min(driver_laptimes, key=driver_laptimes.get)
    ref_telemetry = driver_telemetry[fastest_driver]
    ref_sectors = driver_sector_times.get(fastest_driver)
    
    # Create common distance array for interpolation
    max_distance = min(tel['Distance'].max() for tel in driver_telemetry.values())
    common_distance = np.linspace(0, max_distance, 500)
    
    # Calculate reference time at each distance point
    ref_time = np.interp(common_distance, ref_telemetry['Distance'], ref_telemetry['Time'].dt.total_seconds())
    
    # Find sector boundary distances from reference telemetry
    sector_distances = {}
    if ref_sectors:
        ref_times_array = ref_telemetry['Time'].dt.total_seconds().values
        ref_dist_array = ref_telemetry['Distance'].values
        
        for sector_name, sector_time in ref_sectors.items():
            # Find the distance where cumulative time equals sector time
            idx = np.searchsorted(ref_times_array, sector_time)
            if idx < len(ref_dist_array):
                sector_distances[sector_name] = ref_dist_array[min(idx, len(ref_dist_array)-1)]
    
    # Plot delta for each driver
    for d_abbr in drivers:
        if d_abbr not in driver_telemetry:
            continue
            
        driver_data = session.get_driver(d_abbr)
        team = driver_data['TeamName']
        color = plotting.get_team_color(team, session)
        
        tel = driver_telemetry[d_abbr]
        driver_time = np.interp(common_distance, tel['Distance'], tel['Time'].dt.total_seconds())
        
        # Calculate raw delta from telemetry
        raw_delta = ref_time - driver_time
        
        # Get driver's sector times for correction
        drv_sectors = driver_sector_times.get(d_abbr)
        
        # Apply sector-based corrections if we have sector data for both drivers
        if ref_sectors and drv_sectors and sector_distances:
            delta = apply_sector_corrections(
                raw_delta, common_distance, 
                ref_sectors, drv_sectors, sector_distances,
                driver_laptimes[d_abbr], driver_laptimes[fastest_driver]
            )
        else:
            # Fallback to simple linear correction
            expected_final_delta = driver_laptimes[d_abbr] - driver_laptimes[fastest_driver]
            current_final_delta = raw_delta[-1] if len(raw_delta) > 0 else 0
            correction_needed = expected_final_delta - current_final_delta
            correction = np.linspace(0, correction_needed, len(common_distance))
            delta = raw_delta + correction
        
        line_dash = 'solid'
        if team in team_color_used_solid:
            line_dash = 'dash'
        else:
            team_color_used_solid[team] = True
        
        fig.add_trace(go.Scatter(
            x=common_distance,
            y=delta,
            mode='lines',
            name=f"{d_abbr} ({team})",
            line=dict(color=color, dash=line_dash, width=2)
        ))
    
    # Add vertical lines for sector boundaries
    if sector_distances:
        if 'S1' in sector_distances:
            fig.add_vline(
                x=sector_distances['S1'],
                line=dict(color='rgba(255,255,255,0.4)', width=1, dash='dash'),
                annotation_text="S1",
                annotation_position="top",
                annotation_font=dict(color='white', size=12)
            )
        if 'S2' in sector_distances:
            fig.add_vline(
                x=sector_distances['S2'],
                line=dict(color='rgba(255,255,255,0.4)', width=1, dash='dash'),
                annotation_text="S2",
                annotation_position="top",
                annotation_font=dict(color='white', size=12)
            )
    
    fig.update_layout(
        title=dict(
            text=f"Delta Comparison - {race} {year} (Reference: {fastest_driver})",
            font=dict(color='white', size=20)
        ),
        xaxis_title='Distance (m)',
        yaxis_title='Delta Time (s)',
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
            title_font=dict(color='white'),
            zeroline=True,
            zerolinecolor='rgba(255,255,255,0.5)',
            zerolinewidth=2
        ),
        legend=dict(
            font=dict(color='white'),
            title_font=dict(color='white')
        )
    )
    
    return fig


def apply_sector_corrections(raw_delta, common_distance, ref_sectors, drv_sectors, sector_distances, drv_laptime, ref_laptime):
    """
    Apply piecewise linear corrections based on sector times.
    Corrects delta at each sector boundary to match official sector time differences.
    """
    delta = raw_delta.copy()
    n_points = len(common_distance)
    max_dist = common_distance[-1]
    
    # Define correction points: start, S1 end, S2 end, S3 end (lap end)
    # Expected delta at each point based on official times
    correction_points = [
        (0, 0),  # Start of lap: delta = 0
    ]
    
    # S1 boundary
    if 'S1' in sector_distances and 'S1' in drv_sectors and 'S1' in ref_sectors:
        s1_dist = sector_distances['S1']
        expected_s1_delta = drv_sectors['S1'] - ref_sectors['S1']
        correction_points.append((s1_dist, expected_s1_delta))
    
    # S2 boundary
    if 'S2' in sector_distances and 'S2' in drv_sectors and 'S2' in ref_sectors:
        s2_dist = sector_distances['S2']
        expected_s2_delta = drv_sectors['S2'] - ref_sectors['S2']
        correction_points.append((s2_dist, expected_s2_delta))
    
    # End of lap (S3)
    expected_final_delta = drv_laptime - ref_laptime
    correction_points.append((max_dist, expected_final_delta))
    
    # Sort by distance
    correction_points.sort(key=lambda x: x[0])
    
    # Find raw delta values at correction points
    raw_at_points = []
    for dist, _ in correction_points:
        idx = np.searchsorted(common_distance, dist)
        idx = min(idx, n_points - 1)
        raw_at_points.append(raw_delta[idx])
    
    # Calculate corrections needed at each point
    corrections_at_points = []
    for i, (dist, expected) in enumerate(correction_points):
        correction = expected - raw_at_points[i]
        corrections_at_points.append((dist, correction))
    
    # Apply piecewise linear correction
    correction_array = np.zeros(n_points)
    for i in range(len(corrections_at_points) - 1):
        dist_start, corr_start = corrections_at_points[i]
        dist_end, corr_end = corrections_at_points[i + 1]
        
        # Find indices for this segment
        idx_start = np.searchsorted(common_distance, dist_start)
        idx_end = np.searchsorted(common_distance, dist_end)
        
        if idx_end > idx_start:
            # Linear interpolation of correction within this segment
            segment_correction = np.linspace(corr_start, corr_end, idx_end - idx_start)
            correction_array[idx_start:idx_end] = segment_correction
    
    # Handle the last point
    if len(corrections_at_points) > 0:
        correction_array[-1] = corrections_at_points[-1][1]
    
    delta = raw_delta + correction_array
    return delta


def create_track_dominance(session, drivers, race, year, empty_layout):
    """Create a track dominance visualization showing which driver was fastest in each mini-sector."""
    fig = go.Figure()
    
    NUM_SECTORS = 10  # Number of mini-sectors
    
    # If no drivers selected, use all drivers from the session
    if not drivers or len(drivers) == 0:
        all_driver_nums = session.drivers
        drivers = [session.get_driver(d)['Abbreviation'] for d in all_driver_nums]
    
    # Collect data for all drivers
    driver_data = {}
    
    for d_abbr in drivers:
        drv_info = session.get_driver(d_abbr)
        if drv_info is None:
            continue
        
        laps = session.laps.pick_drivers(d_abbr)
        if laps.empty:
            continue
        
        fastest = laps.pick_fastest()
        if fastest.empty:
            continue
        
        telemetry = fastest.get_telemetry()
        if telemetry.empty or 'X' not in telemetry.columns or 'Y' not in telemetry.columns:
            continue
        
        team = drv_info['TeamName']
        color = plotting.get_team_color(team, session)
        
        driver_data[d_abbr] = {
            'telemetry': telemetry,
            'color': color,
            'team': team,
            'fastest': fastest,
            'laptime': fastest['LapTime'].total_seconds()
        }
    
    if len(driver_data) < 2:
        fig.update_layout(title="Not enough valid data for Track Dominance.", **empty_layout)
        return fig
    
    # Use the first driver's telemetry as reference for track shape
    ref_driver = list(driver_data.keys())[0]
    ref_tel = driver_data[ref_driver]['telemetry']
    
    # Get X, Y coordinates and distance
    x_coords = ref_tel['X'].values
    y_coords = ref_tel['Y'].values
    distances = ref_tel['Distance'].values
    ref_times = ref_tel['Time'].dt.total_seconds().values
    
    max_distance = distances[-1]
    
    # Create mini-sector boundaries based on distance
    sector_boundaries = np.linspace(0, max_distance, NUM_SECTORS + 1)
    
    # Find index for each sector boundary
    sector_indices = []
    for dist in sector_boundaries:
        idx = np.searchsorted(distances, dist)
        idx = min(idx, len(x_coords) - 1)
        sector_indices.append(idx)
    
    # Calculate time at each sector boundary for each driver
    driver_sector_times = {}
    for d_abbr, data in driver_data.items():
        tel = data['telemetry']
        tel_distances = tel['Distance'].values
        tel_times = tel['Time'].dt.total_seconds().values
        
        # Interpolate time at each sector boundary
        times_at_boundaries = np.interp(sector_boundaries, tel_distances, tel_times)
        driver_sector_times[d_abbr] = times_at_boundaries
    
    # Determine winner for each mini-sector
    sector_winners = []
    for i in range(NUM_SECTORS):
        best_time = float('inf')
        winner = None
        for d_abbr, times in driver_sector_times.items():
            sector_time = times[i + 1] - times[i]  # Time for this sector
            if sector_time < best_time:
                best_time = sector_time
                winner = d_abbr
        sector_winners.append({'winner': winner, 'time': best_time})
    
    # First, add a dark background outline for the entire track (shadow effect)
    fig.add_trace(go.Scatter(
        x=x_coords,
        y=y_coords,
        mode='lines',
        name='Track Outline',
        line=dict(color='rgba(0,0,0,0.8)', width=18),
        hoverinfo='skip',
        showlegend=False
    ))
    
    # Add a subtle grey outline for depth
    fig.add_trace(go.Scatter(
        x=x_coords,
        y=y_coords,
        mode='lines',
        name='Track Border',
        line=dict(color='rgba(60,60,60,1)', width=14),
        hoverinfo='skip',
        showlegend=False
    ))
    
    # Track which drivers have been added to legend
    legend_added = set()
    
    # Determine which drivers need stripes (second driver from same team)
    team_drivers = {}
    for d_abbr, data in driver_data.items():
        team = data['team']
        if team not in team_drivers:
            team_drivers[team] = []
        team_drivers[team].append(d_abbr)
    
    # Mark drivers who need alternate color (not the first one from their team)
    drivers_with_alt_color = {}
    for team, team_driver_list in team_drivers.items():
        if len(team_driver_list) > 1:
            # All except the first driver get alternate color
            for d in team_driver_list[1:]:
                drivers_with_alt_color[d] = team
    
    # Secondary team colors - distinct colors that don't clash with other teams
    secondary_team_colors = {
        'Red Bull Racing': '#FFD700',       # Gold
        'Red Bull': '#FFD700',              # Gold
        'Ferrari': '#FFF200',               # Yellow
        'Mercedes': '#00A19C',              # Petronas Teal variant
        'McLaren': '#47C7FC',               # Cyan/Light Blue
        'Aston Martin': '#00594F',          # Dark Teal
        'Alpine': '#FF87BC',                # Pink
        'Williams': '#64C4FF',              # Light Blue
        'Haas F1 Team': '#B6BABD',          # Silver
        'MoneyGram Haas F1 Team': '#B6BABD',
        'RB': '#1E5BC6',                    # Different Blue
        'Kick Sauber': '#00E701',           # Bright Green
        'Sauber': '#00E701',
        'Alfa Romeo': '#4CBB17',            # Kelly Green
        'AlphaTauri': '#4E7C9B',            # Steel Blue
    }
    
    def get_secondary_color(team_name):
        """Get secondary color for a team."""
        for team_key, sec_color in secondary_team_colors.items():
            if team_key.lower() in team_name.lower() or team_name.lower() in team_key.lower():
                return sec_color
        return '#FFFF00'  # Yellow as fallback
    
    # Plot each mini-sector with the winning driver's color
    for i in range(NUM_SECTORS):
        start_idx = sector_indices[i]
        end_idx = sector_indices[i + 1]
        winner = sector_winners[i]['winner']
        
        if winner and winner in driver_data:
            # Use secondary color for second teammate
            if winner in drivers_with_alt_color:
                team = drivers_with_alt_color[winner]
                color = get_secondary_color(team)
            else:
                color = driver_data[winner]['color']
            
            # Get segment coordinates
            seg_x = x_coords[start_idx:end_idx+1]
            seg_y = y_coords[start_idx:end_idx+1]
            
            # Add glow layer (wider, semi-transparent)
            fig.add_trace(go.Scatter(
                x=seg_x,
                y=seg_y,
                mode='lines',
                line=dict(color=color, width=14),
                opacity=0.3,
                hoverinfo='skip',
                showlegend=False
            ))
            
            # Only add to legend once per driver
            show_legend = winner not in legend_added
            if show_legend:
                legend_added.add(winner)
            
            # Add main colored track
            fig.add_trace(go.Scatter(
                x=seg_x,
                y=seg_y,
                mode='lines',
                name=winner,
                line=dict(color=color, width=10),
                hovertemplate=f"Sector {i+1}: {winner}<extra></extra>",
                showlegend=show_legend,
                legendgroup=winner
            ))
    
    # Add start/finish marker
    if len(x_coords) > 1:
        dx = x_coords[1] - x_coords[0]
        dy = y_coords[1] - y_coords[0]
        length = np.sqrt(dx**2 + dy**2)
        if length > 0:
            perp_x = -dy / length
            perp_y = dx / length
            # Keep line within track width
            line_length = 350
            
            fig.add_trace(go.Scatter(
                x=[x_coords[0] - perp_x * line_length, x_coords[0] + perp_x * line_length],
                y=[y_coords[0] - perp_y * line_length, y_coords[0] + perp_y * line_length],
                mode='lines',
                name='Start/Finish',
                line=dict(color='white', width=4),
                showlegend=True
            ))
    
    # Add mini-sector boundary markers (white lines within track width)
    for i in range(1, NUM_SECTORS):
        idx = sector_indices[i]
        if idx > 0 and idx < len(x_coords) - 1:
            dx = x_coords[idx + 1] - x_coords[idx - 1]
            dy = y_coords[idx + 1] - y_coords[idx - 1]
            length = np.sqrt(dx**2 + dy**2)
            if length > 0:
                perp_x = -dy / length
                perp_y = dx / length
                # Short line that stays within track borders
                line_length = 300
                
                fig.add_trace(go.Scatter(
                    x=[x_coords[idx] - perp_x * line_length, x_coords[idx] + perp_x * line_length],
                    y=[y_coords[idx] - perp_y * line_length, y_coords[idx] + perp_y * line_length],
                    mode='lines',
                    line=dict(color='white', width=2),
                    hoverinfo='skip',
                    showlegend=False
                ))
    
    # Create summary of sectors won by each driver
    driver_sectors_won = {}
    for sw in sector_winners:
        winner = sw['winner']
        if winner:
            driver_sectors_won[winner] = driver_sectors_won.get(winner, 0) + 1
    
    legend_text = "<b>Mini-Sectors Won:</b><br>"
    for d_abbr in sorted(driver_sectors_won.keys(), key=lambda x: driver_sectors_won[x], reverse=True):
        count = driver_sectors_won[d_abbr]
        legend_text += f"{d_abbr}: {count}/{NUM_SECTORS}<br>"
    
    fig.update_layout(
        title=dict(
            text=f"Track Dominance - {race} {year}",
            font=dict(color='white', size=20)
        ),
        showlegend=True,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            visible=False,
            scaleanchor='y',
            scaleratio=1
        ),
        yaxis=dict(
            visible=False
        ),
        legend=dict(
            font=dict(color='white'),
            bgcolor='rgba(0,0,0,0.5)',
            bordercolor='rgba(255,255,255,0.3)',
            borderwidth=1
        ),
        annotations=[
            dict(
                x=0.02,
                y=0.98,
                xref='paper',
                yref='paper',
                text=legend_text,
                showarrow=False,
                font=dict(color='white', size=12),
                align='left',
                bgcolor='rgba(0,0,0,0.7)',
                bordercolor='rgba(255,255,255,0.3)',
                borderwidth=1,
                borderpad=8
            )
        ]
    )
    
    return fig