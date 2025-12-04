# In app.py

# (Remove all the temporary print statements)

from dash import dcc, html, Input, Output
import dash_mantine_components as dmc
import fastf1

from app_instance import app, server
from pages import home, lap_comparison, race_comparison, year_analysis

# fastf1.Cache.enable_cache('data/cache')  <-- DELETE THIS LINE FROM HERE

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
    # --- THIS IS THE FIX ---
    # Move the cache enabling here. It will now only run once
    # in the main process, not in the reloader's watcher.
    fastf1.Cache.enable_cache('data/cache')
    
    app.run(debug=True)