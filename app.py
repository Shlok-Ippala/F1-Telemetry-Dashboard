# In app.py

import os
from dash import dcc, html, Input, Output
import dash_mantine_components as dmc
import fastf1

from app_instance import app, server
from pages import home, lap_comparison, race_comparison, year_analysis

# Enable FastF1 cache - use /tmp for cloud deployments, local folder otherwise
cache_dir = '/tmp/f1_cache' if os.environ.get('RENDER') else 'data/cache'
os.makedirs(cache_dir, exist_ok=True)
fastf1.Cache.enable_cache(cache_dir)

# Define the main layout of the app wrapped in MantineProvider
app.layout = dmc.MantineProvider(
    children=[
        dcc.Location(id='url', refresh=False),
        html.Div(id='page-content')
    ],
    forceColorScheme="dark"
)

# This callback changes the 'page-content' based on the URL
@app.callback(Output('page-content', 'children'),
              Input('url', 'pathname'))
def display_page(pathname):
    if pathname == '/lap-comparison':
        return lap_comparison.layout
    elif pathname == '/race-comparison':
        return race_comparison.layout
    elif pathname == '/year-analysis':
        return year_analysis.layout
    else:
        # The default page is the home page
        return home.layout

# Run the app
if __name__ == '__main__':
    # Get port from environment variable (for Render) or default to 8050
    port = int(os.environ.get('PORT', 8050))
    debug = os.environ.get('RENDER') is None  # Debug only in local dev
    
    app.run(host='0.0.0.0', port=port, debug=debug)